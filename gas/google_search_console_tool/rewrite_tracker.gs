// ========================================
// リライト効果測定ツール - Google Apps Script
// ========================================

// ========================================
// メイン実行関数
// ========================================
function runRewriteAnalysis() {
  Logger.log('=== 分析開始 ===');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  try {
    // 設定シートから設定を読み込み
    Logger.log('ステップ1: 設定読み込み');
    const config = loadConfig(ss);
    
    // 設定シートが作成された直後はnullが返る
    if (!config) {
      Logger.log('設定シート作成直後のため処理を中断');
      return;
    }
    
    Logger.log('設定読み込み完了: ' + JSON.stringify(config));
    
    // シートを準備
    Logger.log('ステップ2: シート準備');
    clearAndPrepareSheets(ss);
    Logger.log('シート準備完了');
    
    // 記事タイトルを取得
    Logger.log('ステップ3: タイトル取得開始');
    const pageTitle = getPageTitle(config.targetUrl);
    Logger.log('タイトル取得完了: ' + pageTitle);
    
    // リライト前後の期間を計算
    Logger.log('ステップ4: 期間計算');
    const periods = calculatePeriods(config.rewriteDate, config.beforeDays, config.afterDays);
    Logger.log('リライト前期間: ' + periods.before.start + ' 〜 ' + periods.before.end);
    Logger.log('リライト後期間: ' + periods.after.start + ' 〜 ' + periods.after.end);
    
    // データ取得
    Logger.log('ステップ5: リライト前データ取得');
    const beforeData = getSearchConsoleData(config.siteUrl, config.targetUrl, periods.before.start, periods.before.end);
    Logger.log('リライト前データ取得完了');
    
    Logger.log('ステップ6: リライト後データ取得');
    const afterData = getSearchConsoleData(config.siteUrl, config.targetUrl, periods.after.start, periods.after.end);
    Logger.log('リライト後データ取得完了');
    
    // サマリーシートに書き込み
    Logger.log('ステップ7: サマリーシート書き込み');
    writeSummarySheet(ss, beforeData, afterData, periods, config, pageTitle);
    Logger.log('サマリーシート書き込み完了');
    
    // キーワード別シートに書き込み
    Logger.log('ステップ8: キーワード別シート書き込み');
    writeKeywordSheet(ss, beforeData, afterData);
    Logger.log('キーワード別シート書き込み完了');
    
    Logger.log('=== 分析完了 ===');
    
    // トースト通知で完了を知らせる
    SpreadsheetApp.getActiveSpreadsheet().toast(
      'サマリーとキーワード別データを確認してください', 
      '✅ 分析完了！', 
      5
    );
    
  } catch (e) {
    Logger.log('エラー発生: ' + e.toString());
    Logger.log('スタックトレース: ' + e.stack);
    
    // エラー時もトースト通知
    SpreadsheetApp.getActiveSpreadsheet().toast(
      e.toString(), 
      '❌ エラーが発生しました', 
      10
    );
  }
}

// ========================================
// 設定シートから設定を読み込み
// ========================================
function loadConfig(ss) {
  let configSheet = ss.getSheetByName('設定');
  
  // 設定シートが存在しない場合は作成
  if (!configSheet) {
    configSheet = createConfigSheet(ss);
    ss.toast(
      '設定値を入力してから再度「リライト測定」→「分析実行」をクリックしてください', 
      '📋 設定シートを作成しました', 
      10
    );
    return null;  // nullを返して処理を中断
  }
  
  // 設定値を読み込み
  const config = {
    siteUrl: configSheet.getRange('B2').getValue(),
    targetUrl: configSheet.getRange('B3').getValue(),
    rewriteDate: formatDate(new Date(configSheet.getRange('B4').getValue())),
    beforeDays: configSheet.getRange('B5').getValue(),
    afterDays: configSheet.getRange('B6').getValue()
  };
  
  // 検証
  if (!config.siteUrl || !config.targetUrl || !config.rewriteDate) {
    ss.toast(
      'サイトURL、測定URL、リライト日を入力してください', 
      '⚠️ 設定値が不足しています', 
      10
    );
    return null;
  }
  
  return config;
}

// ========================================
// 設定シートを作成
// ========================================
function createConfigSheet(ss) {
  const configSheet = ss.insertSheet('設定', 0);
  
  // ヘッダー
  configSheet.getRange('A1:B1').setValues([['リライト測定ツール - 設定', '']])
    .setFontSize(14)
    .setFontWeight('bold')
    .setBackground('#4a86e8')
    .setFontColor('#ffffff');
  
  // 設定項目
  const settings = [
    ['サイトURL', 'https://life-simulation.dream-target.jp/'],
    ['測定URL', 'https://life-simulation.dream-target.jp/ecoflow-30'],
    ['リライト日', new Date('2025-11-07')],
    ['リライト前測定期間（日数）', 30],
    ['リライト後測定期間（日数）', 30]
  ];
  
  configSheet.getRange('A2:B6').setValues(settings);
  
  // A列のスタイル
  configSheet.getRange('A2:A6')
    .setFontWeight('bold')
    .setBackground('#f3f3f3');
  
  // 列幅調整
  configSheet.setColumnWidth(1, 200);
  configSheet.setColumnWidth(2, 400);
  
  // 日付のフォーマット
  configSheet.getRange('B4').setNumberFormat('yyyy-mm-dd');
  
  // 説明を追加
  configSheet.getRange('A8:B8').merge()
    .setValue('【使い方】')
    .setFontWeight('bold')
    .setBackground('#fff2cc');
  
  const instructions = [
    ['1. 上記の設定値を編集してください'],
    ['2. メニューから「リライト測定」→「分析実行」をクリック'],
    ['3. 「サマリー」と「キーワード別」シートに結果が出力されます'],
    [''],
    ['【注意事項】'],
    ['・サイトURLと測定URLは完全一致で入力してください'],
    ['・リライト日は「2025-11-07」のような形式で入力してください'],
    ['・測定期間は1〜90日程度を推奨します']
  ];
  
  configSheet.getRange(9, 1, instructions.length, 1).setValues(instructions);
  
  return configSheet;
}

// ========================================
// ページタイトルを取得
// ========================================
function getPageTitle(url) {
  try {
    const response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      followRedirects: true,
      timeout: 10  // 10秒でタイムアウト
    });
    
    if (response.getResponseCode() !== 200) {
      Logger.log('タイトル取得失敗: HTTP ' + response.getResponseCode());
      return '（タイトル取得失敗）';
    }
    
    const html = response.getContentText();
    const titleMatch = html.match(/<title[^>]*>(.*?)<\/title>/i);
    
    if (titleMatch && titleMatch[1]) {
      // HTMLエンティティをデコード
      const title = titleMatch[1]
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .trim();
      
      Logger.log('タイトル取得成功: ' + title);
      return title;
    }
    
    Logger.log('タイトルタグが見つかりませんでした');
    return '（タイトル未設定）';
    
  } catch (e) {
    Logger.log('タイトル取得エラー: ' + e.toString());
    return '（タイトル取得失敗）';
  }
}

// ========================================
// 期間計算
// ========================================
function calculatePeriods(rewriteDateStr, beforeDays, afterDays) {
  const rewriteDate = new Date(rewriteDateStr);
  
  // リライト前期間
  const beforeEnd = new Date(rewriteDate);
  beforeEnd.setDate(beforeEnd.getDate() - 1); // リライト日の前日
  const beforeStart = new Date(beforeEnd);
  beforeStart.setDate(beforeStart.getDate() - beforeDays + 1);
  
  // リライト後期間（今日まで or 指定日数）
  const afterStart = new Date(rewriteDate);
  const today = new Date();
  const afterEnd = new Date(Math.min(
    new Date(afterStart.getTime() + afterDays * 24 * 60 * 60 * 1000),
    today
  ));
  
  return {
    before: {
      start: formatDate(beforeStart),
      end: formatDate(beforeEnd)
    },
    after: {
      start: formatDate(afterStart),
      end: formatDate(afterEnd)
    }
  };
}

// ========================================
// Search Console APIからデータ取得（REST API使用）
// ========================================
function getSearchConsoleData(siteUrl, pageUrl, startDate, endDate) {
  const requestBody = {
    startDate: startDate,
    endDate: endDate,
    dimensions: ['query'],
    dimensionFilterGroups: [{
      filters: [{
        dimension: 'page',
        expression: pageUrl
      }]
    }],
    rowLimit: 1000
  };
  
  // サイトURLの形式を確認して適切にエンコード
  // URLプレフィックスの場合: https://example.com/ → sc-domain:example.com に変換が必要な場合がある
  let formattedSiteUrl = siteUrl;
  
  // URLプレフィックス形式の場合、そのまま1回だけエンコード
  const encodedSiteUrl = encodeURIComponent(formattedSiteUrl);
  const apiUrl = `https://www.googleapis.com/webmasters/v3/sites/${encodedSiteUrl}/searchAnalytics/query`;
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': 'Bearer ' + ScriptApp.getOAuthToken()
    },
    payload: JSON.stringify(requestBody),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(apiUrl, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      throw new Error('API呼び出しエラー (HTTP ' + responseCode + '): ' + response.getContentText());
    }
    
    const data = JSON.parse(response.getContentText());
    
    if (!data.rows || data.rows.length === 0) {
      return {
        summary: { clicks: 0, impressions: 0, ctr: 0, position: 0 },
        keywords: []
      };
    }
    
    // サマリー計算
    let totalClicks = 0;
    let totalImpressions = 0;
    let totalPosition = 0;
    
    data.rows.forEach(row => {
      totalClicks += row.clicks || 0;
      totalImpressions += row.impressions || 0;
      totalPosition += (row.position || 0) * (row.impressions || 0);
    });
    
    const avgPosition = totalImpressions > 0 ? totalPosition / totalImpressions : 0;
    const ctr = totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : 0;
    
    return {
      summary: {
        clicks: totalClicks,
        impressions: totalImpressions,
        ctr: ctr,
        position: avgPosition
      },
      keywords: data.rows.map(row => ({
        query: row.keys[0],
        clicks: row.clicks || 0,
        impressions: row.impressions || 0,
        ctr: row.ctr * 100 || 0,
        position: row.position || 0
      }))
    };
    
  } catch (e) {
    Logger.log('エラー詳細: ' + e.toString());
    throw new Error('Search Console APIの呼び出しに失敗しました: ' + e.toString());
  }
}

// ========================================
// シート準備
// ========================================
function clearAndPrepareSheets(ss) {
  // サマリーシート
  let summarySheet = ss.getSheetByName('サマリー');
  if (!summarySheet) {
    summarySheet = ss.insertSheet('サマリー');
  } else {
    summarySheet.clear();
  }
  
  // キーワード別シート
  let keywordSheet = ss.getSheetByName('キーワード別');
  if (!keywordSheet) {
    keywordSheet = ss.insertSheet('キーワード別');
  } else {
    keywordSheet.clear();
  }
}

// ========================================
// サマリーシート書き込み
// ========================================
function writeSummarySheet(ss, beforeData, afterData, periods, config, pageTitle) {
  const sheet = ss.getSheetByName('サマリー');
  
  // ヘッダー
  sheet.getRange('A1:F1').setValues([[
    '測定URL', config.targetUrl, '', '', '', ''
  ]]).setFontWeight('bold').setBackground('#e8f0fe');
  
  sheet.getRange('A2:F2').setValues([[
    'ページタイトル', pageTitle, '', '', '', ''
  ]]).setFontWeight('bold').setBackground('#e8f0fe');
  
  sheet.getRange('A3:F3').setValues([[
    'リライト日', config.rewriteDate, '', '', '', ''
  ]]).setFontWeight('bold');
  
  // テーブルヘッダー
  sheet.getRange('A5:F5').setValues([[
    '指標', 'リライト前', 'リライト後', '変化', '変化率', '判定'
  ]]).setFontWeight('bold').setBackground('#f3f3f3');
  
  // 期間情報
  sheet.getRange('A6').setValue('測定期間');
  sheet.getRange('B6').setValue(periods.before.start + ' 〜 ' + periods.before.end);
  sheet.getRange('C6').setValue(periods.after.start + ' 〜 ' + periods.after.end);
  
  // データ行
  const metrics = [
    {
      name: 'クリック数',
      before: beforeData.summary.clicks,
      after: afterData.summary.clicks
    },
    {
      name: '表示回数',
      before: beforeData.summary.impressions,
      after: afterData.summary.impressions
    },
    {
      name: 'CTR (%)',
      before: beforeData.summary.ctr,
      after: afterData.summary.ctr
    },
    {
      name: '平均掲載順位',
      before: beforeData.summary.position,
      after: afterData.summary.position,
      reverse: true // 順位は低い方が良い
    }
  ];
  
  let row = 7;
  metrics.forEach(metric => {
    const change = metric.after - metric.before;
    const changeRate = metric.before > 0 ? (change / metric.before) * 100 : 0;
    
    // 判定（順位は逆）
    let judgment = '';
    if (metric.reverse) {
      judgment = change < -1 ? '改善 ✓' : change > 1 ? '悪化 ✗' : '横ばい -';
    } else {
      judgment = change > 0 ? '改善 ✓' : change < 0 ? '悪化 ✗' : '横ばい -';
    }
    
    sheet.getRange(row, 1, 1, 6).setValues([[
      metric.name,
      metric.name.includes('順位') ? metric.before.toFixed(1) : metric.before,
      metric.name.includes('順位') ? metric.after.toFixed(1) : metric.after,
      metric.name.includes('順位') ? change.toFixed(1) : change,
      changeRate.toFixed(1) + '%',
      judgment
    ]]);
    
    row++;
  });
  
  // 書式設定
  sheet.setColumnWidth(1, 150);
  sheet.setColumnWidth(2, 120);
  sheet.setColumnWidth(3, 120);
  sheet.setColumnWidth(4, 100);
  sheet.setColumnWidth(5, 100);
  sheet.setColumnWidth(6, 100);
  
  // URLとタイトルのセル結合
  sheet.getRange('B1:F1').merge();
  sheet.getRange('B2:F2').merge();
  sheet.getRange('B3:F3').merge();
  
  // 判定列に色付け
  const judgmentRange = sheet.getRange('F7:F10');
  const judgmentValues = judgmentRange.getValues();
  const colors = judgmentValues.map(row => {
    if (row[0].includes('改善')) return ['#d9ead3'];
    if (row[0].includes('悪化')) return ['#f4cccc'];
    return ['#fff2cc'];
  });
  judgmentRange.setBackgrounds(colors);
}

// ========================================
// キーワード別シート書き込み
// ========================================
function writeKeywordSheet(ss, beforeData, afterData) {
  const sheet = ss.getSheetByName('キーワード別');
  
  // ヘッダー
  sheet.getRange('A1:K1').setValues([[
    'キーワード',
    'リライト前クリック',
    'リライト後クリック',
    'クリック変化',
    'リライト前表示',
    'リライト後表示',
    '表示変化',
    'リライト前順位',
    'リライト後順位',
    '順位変化',
    '重要度'
  ]]).setFontWeight('bold').setBackground('#f3f3f3');
  
  // キーワードをマージ
  const allKeywords = new Set();
  beforeData.keywords.forEach(k => allKeywords.add(k.query));
  afterData.keywords.forEach(k => allKeywords.add(k.query));
  
  const keywordMap = {};
  beforeData.keywords.forEach(k => {
    keywordMap[k.query] = { before: k, after: null };
  });
  afterData.keywords.forEach(k => {
    if (keywordMap[k.query]) {
      keywordMap[k.query].after = k;
    } else {
      keywordMap[k.query] = { before: null, after: k };
    }
  });
  
  // データ行作成
  const rows = [];
  Object.keys(keywordMap).forEach(query => {
    const data = keywordMap[query];
    const beforeClicks = data.before ? data.before.clicks : 0;
    const afterClicks = data.after ? data.after.clicks : 0;
    const beforeImpressions = data.before ? data.before.impressions : 0;
    const afterImpressions = data.after ? data.after.impressions : 0;
    const beforePosition = data.before ? data.before.position : 0;
    const afterPosition = data.after ? data.after.position : 0;
    
    // 重要度判定（クリック数で判断）
    const totalClicks = beforeClicks + afterClicks;
    let importance = '';
    if (totalClicks >= 10) importance = '★★★ メイン';
    else if (totalClicks >= 3) importance = '★★ 準メイン';
    else if (totalClicks >= 1) importance = '★ サブ';
    else importance = '- その他';
    
    rows.push([
      query,
      beforeClicks,
      afterClicks,
      afterClicks - beforeClicks,
      beforeImpressions,
      afterImpressions,
      afterImpressions - beforeImpressions,
      beforePosition.toFixed(1),
      afterPosition.toFixed(1),
      (afterPosition - beforePosition).toFixed(1),
      importance
    ]);
  });
  
  // クリック数でソート
  rows.sort((a, b) => (b[1] + b[2]) - (a[1] + a[2]));
  
  // シートに書き込み
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, 11).setValues(rows);
  }
  
  // 書式設定
  sheet.setColumnWidth(1, 250);
  for (let i = 2; i <= 11; i++) {
    sheet.setColumnWidth(i, 100);
  }
  
  // 重要度列に色付け
  if (rows.length > 0) {
    const importanceRange = sheet.getRange(2, 11, rows.length, 1);
    const importanceValues = importanceRange.getValues();
    const colors = importanceValues.map(row => {
      if (row[0].includes('メイン')) return ['#d9ead3'];
      if (row[0].includes('準メイン')) return ['#fff2cc'];
      if (row[0].includes('サブ')) return ['#fce5cd'];
      return ['#ffffff'];
    });
    importanceRange.setBackgrounds(colors);
  }
}

// ========================================
// ユーティリティ関数
// ========================================
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// ========================================
// メニュー追加
// ========================================
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('リライト測定')
    .addItem('分析実行', 'runRewriteAnalysis')
    .addToUi();
}
