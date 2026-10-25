/*
 * cluster ショップ → 「フレンドの商品リスト」CSV 抽出スクリプト
 *
 * 使い方:
 *  1. Chrome でフレンドのショップ一覧ページを開く
 *       例) https://cluster.mu/u/su_min/accessories
 *           https://cluster.mu/u/usa_cluster/items
 *           https://cluster.mu/u/ushioka/avatars
 *  2. 下の「設定」の LIMIT を必要な件数に変える（0 なら全件）
 *  3. F12 → Console タブ に、このファイルの中身を丸ごと貼り付けて Enter
 *     (初回は「貼り付けを許可」の確認が出ることがあります)
 *  4. 終わると CSV がクリップボードにコピーされ、.csv もダウンロードされます
 *
 * 出力列: UID, 種別, 商品コード(url), 商品名   ← 既存の「フレンドの商品リスト」と同じ
 * 並び順: ショップの表示順（新しい順）。LIMIT=10 なら先頭（最新）の10件。
 */
(async () => {
  // ====== 設定 ======
  const LIMIT = 25;            // 取得する件数の上限。0 または null なら全件
  const UID_MAP = { ushioka: 'F1', su_min: 'F2', usa_cluster: 'F3'}; // ユーザID → UID
  const KIND_MAP = { avatars: 'アバター', accessories: 'アクセサリ', items: 'クラフトアイテム' };
  const FETCH_DETAIL = false;  // true: 各商品ページから正式名称を取得(遅いが確実) / false: 一覧の名前のみ(通常はこれで十分)
  const DETAIL_WAIT_MS = 400;  // 商品ページ取得の間隔(サーバーに優しく)
  const SCROLL_WAIT_MS = 1200; // スクロール後の待ち時間
  // ==================

  const limit = Number.isFinite(LIMIT) && LIMIT > 0 ? Math.floor(LIMIT) : Infinity;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const LINK_RE = /\/store\/(avatars|accessories|items)\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;

  const userId = (location.pathname.match(/^\/u\/([^/]+)/) || [])[1] || '';
  const uid = UID_MAP[userId] || '??';
  if (uid === '??') console.warn(`ユーザID "${userId}" が UID_MAP にありません。UID列は ?? になります。`);

  // 一覧上の商品リンクを、出現順・重複なしで集める。
  // 1商品につきリンクが2本(画像側=文字なし / 名前側=文字あり)あるので、文字のある方を名前にする。
  const collect = () => {
    const seen = new Map();
    document.querySelectorAll('a[href]').forEach((a) => {
      const m = a.href.match(LINK_RE);
      if (!m) return;
      const url = `https://cluster.mu/store/${m[1]}/${m[2]}`;
      const text = (a.innerText || a.getAttribute('aria-label') || a.querySelector('img')?.alt || '')
        .split('\n').map((s) => s.trim()).filter(Boolean)[0] || '';
      const cur = seen.get(url);
      if (!cur) seen.set(url, { kind: m[1], url, listText: text });
      else if (!cur.listText && text) cur.listText = text;
    });
    return [...seen.values()];
  };
  // 上限に達しているか(名前が空の商品が混ざっていれば、名前が出そろうまで待つ)
  const enough = () => {
    const c = collect();
    return c.length >= limit && c.slice(0, limit).every((it) => it.listText);
  };

  // 1) 読み込み: 上限があればその件数が出そろうまで、なければ全件が読み込まれるまで自動スクロール
  console.log(limit === Infinity ? '一覧を全件読み込み中…' : `一覧の先頭 ${limit} 件を読み込み中…`);
  let last = -1, stable = 0, tries = 0;
  while (true) {
    if (limit !== Infinity && enough()) break;
    window.scrollTo(0, document.body.scrollHeight);
    [...document.querySelectorAll('button, a')]
      .filter((b) => /もっと見る|さらに表示|もっと読み込む|load more/i.test(b.innerText || ''))
      .forEach((b) => b.click());
    await sleep(limit === Infinity ? SCROLL_WAIT_MS : 500);
    const n = collect().length;
    if (n === last) stable++; else { stable = 0; last = n; }
    tries++;
    // 全件モード: 件数が4回連続で変わらなければ終了。上限モード: 一覧が尽きた(8回変化なし)か、最大60回で打ち切り
    if (limit === Infinity ? stable >= 4 : (stable >= 8 || tries >= 60)) break;
  }
  window.scrollTo(0, 0);

  const all = collect();
  const items = limit === Infinity ? all : all.slice(0, limit);
  console.log(`商品リンクを ${all.length} 件検出 → 出力 ${items.length} 件` + (limit !== Infinity && items.length < limit ? `（上限 ${limit} 件に満たない: 出品がこれだけの可能性が高い）` : ''));
  if (items.length === 0) {
    console.error('商品リンクが見つかりません。ショップの一覧タブ(avatars / accessories / items)を開いているか確認してください。');
    return;
  }

  // 2) 名称: 通常は一覧の名前を使う。FETCH_DETAIL=true なら各商品ページから正式名称を取得
  const cleanTitle = (t) =>
    (t || '')
      .replace(/\s*[|｜\-–—]\s*(cluster|クラスター|Cluster ストア|cluster ストア).*$/i, '')
      .replace(/\s+/g, ' ')
      .trim();

  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    it.name = it.listText;
    if (FETCH_DETAIL || !it.name) { // 一覧で名前が取れなかったものだけでも詳細ページから補う
      try {
        const html = await (await fetch(it.url, { credentials: 'include' })).text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const og = doc.querySelector('meta[property="og:title"]')?.content;
        const h1 = doc.querySelector('h1')?.textContent;
        it.name = cleanTitle(og || h1 || doc.title) || it.listText;
      } catch (e) { /* 名前は空のまま警告に出る */ }
      if (i % 10 === 0) console.log(`  名称取得 ${i + 1}/${items.length}`);
      await sleep(DETAIL_WAIT_MS);
    }
  }

  // 3) CSV 化(列順は既存リストと同じ)
  const esc = (s) => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const header = ['UID(一意に特定するID)', '種別', '商品コード(urlもあり)', '商品名'];
  const rows = items.map((it) => [uid, KIND_MAP[it.kind], it.url, it.name]);
  const csv = [header, ...rows].map((r) => r.map(esc).join(',')).join('\r\n');

  // 4) 出力: クリップボード + ダウンロード + コンソール表示
  try { await navigator.clipboard.writeText(csv); console.log('CSV をクリップボードにコピーしました'); }
  catch (e) { console.warn('クリップボードへのコピーに失敗(ページにフォーカスがない場合など)。ダウンロードを使ってください。'); }

  const fname = `friend_items_${uid}_${userId}_${items[0].kind}${limit === Infinity ? '' : '_top' + limit}.csv`;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = fname;
  document.body.appendChild(a); a.click(); a.remove();

  console.table(rows.map((r) => ({ UID: r[0], 種別: r[1], 商品名: r[3], url: r[2].slice(-8) })));
  const empty = rows.filter((r) => !r[3]).length;
  if (empty) console.warn(`商品名が空の行が ${empty} 件あります。確認してください。`);
  console.log(`完了: ${rows.length} 件 → ${fname}`);
})();
