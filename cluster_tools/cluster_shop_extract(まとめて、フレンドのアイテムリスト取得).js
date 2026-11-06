/*
 * cluster ショップ → 3種別(アバター/アクセサリ/クラフトアイテム)まとめて 1つの CSV に抽出するスクリプト (v2)
 * 重要：ログアウト状態で使うこと（ログイン中だと何故かうまく動かない）
 * 
 * 使い方:
 *  1. Chrome で対象ユーザーのページを開く（どのタブでもOK）
 *       例) https://cluster.mu/u/yuki0410/
 *  2. 下の「設定」の LIMIT_PER_KIND を必要な件数に変える（種別ごとの先頭N件・新しい順）
 *  3. F12 → Console タブにこのファイルの中身を丸ごと貼り付けて Enter
 *
 * 種別ごとに次の順で取得を試みます（うまくいった方法を使う）:
 *   ① 今開いているタブがその種別ならそのまま読む
 *   ② 画面に見えない iframe で /u/<ユーザID>/<種別> を開いて読む
 *   ③ ページ内のタブ(リンク/ボタン)をクリックして読む
 * 3種別そろえば1つの CSV を出力します。
 * どうしても取れない種別がある場合は、取れた分をブラウザに一時保存して終了します。
 * その場合は、足りない種別のタブを開いてもう一度このスクリプトを貼り付けてください。
 * 保存分と合体して、3種別入りの1つの CSV が出ます（保存は1時間有効）。
 *
 * 出力列: UID, 種別, 商品名, 商品コード(url)
 */
(async () => {
  // ====== 設定 ======
  const BASE_URL = '';          // 空なら今開いているページのユーザーを対象にする。例: 'https://cluster.mu/u/yuki0410/'
  const LIMIT_PER_KIND = 30;    // 種別ごとの取得件数(先頭=最新から)。0 または null なら全件
  const KINDS = ['avatars', 'accessories', 'items']; // 取得する種別と出力順
  const UID_MAP = {             // ユーザID → UID。未登録ならユーザIDがそのままUID列に入る
    ushioka: 'F1', su_min: 'F2', usa_cluster: 'F3',
    cha_chako: 'F4', suika_tane: 'F5', '888kaze': 'F7',
  };
  const KIND_LABEL = { avatars: 'アバター', accessories: 'アクセサリ', items: 'クラフトアイテム' };
  const TAB_TEXTS = { // ③のクリック方式で、リンクが見つからないときに探すタブの文字
    avatars: ['アバター'], accessories: ['アクセサリ', 'アクセサリー'], items: ['クラフトアイテム', 'アイテム'],
  };
  const FETCH_DETAIL = false;   // true: 全商品の正式名称を商品ページから取得(遅い) / false: 一覧の名前のみ。名前が空のものだけは常に補完
  const DETAIL_WAIT_MS = 400*2;
  const SCROLL_WAIT_MS = 600*2;
  const INITIAL_WAIT_MS = 15000;     // 種別ページを開いてから、最初の商品が出るまで待つ最大時間
  const FRAME_LOAD_TIMEOUT_MS = 20000;
  const TAB_SWITCH_TIMEOUT_MS = 10000;
  const STABLE_LIMIT = 8;       // 件数が変わらない回数がこれに達したら「出そろった」と判断(×SCROLL_WAIT_MS)
  const MAX_SCROLL_TRIES = 120;
  const SAVE_TTL_MS = 60 * 60 * 1000; // 途中保存の有効期間
  // ==================

  const limit = Number.isFinite(LIMIT_PER_KIND) && LIMIT_PER_KIND > 0 ? Math.floor(LIMIT_PER_KIND) : Infinity;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const LINK_RE = /\/store\/(avatars|accessories|items)\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  const reEsc = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // --- 対象ユーザーの決定 ---
  const idFromPath = (p) => (String(p).match(/\/u\/([^/?#]+)/) || [])[1] || '';
  const currentUser = idFromPath(location.pathname);
  const userId = BASE_URL ? idFromPath(BASE_URL) : currentUser;
  if (!userId) { console.error('ユーザIDを特定できません。https://cluster.mu/u/<ユーザID>/ のページで実行してください。'); return; }
  if (currentUser !== userId) {
    console.error(`今開いているのは "${currentUser || '(ユーザページ以外)'}" のページですが、対象は "${userId}" です。https://cluster.mu/u/${userId}/ を開いてから実行してください。`);
    return;
  }
  const uid = UID_MAP[userId] || userId;
  console.log(`対象ユーザ: ${userId} (UID列: ${uid}) / 種別: ${KINDS.join(', ')} / 件数: ${limit === Infinity ? '全件' : '先頭' + limit + '件ずつ'}`);

  // --- 一覧から商品を集める(指定した種別だけ・出現順・重複なし) ---
  // 1商品につきリンクが2本(画像側=文字なし / 名前側=文字あり)あるので、文字のある方を名前にする
  const collect = (doc, kind) => {
    const seen = new Map();
    doc.querySelectorAll('a[href]').forEach((a) => {
      const m = a.href.match(LINK_RE);
      if (!m || m[1] !== kind) return;
      const url = `https://cluster.mu/store/${m[1]}/${m[2]}`;
      const text = (a.innerText || a.getAttribute('aria-label') || a.querySelector('img')?.alt || '')
        .split('\n').map((s) => s.trim()).filter(Boolean)[0] || '';
      const cur = seen.get(url);
      if (!cur) seen.set(url, { kind, url, listText: text });
      else if (!cur.listText && text) cur.listText = text;
    });
    return [...seen.values()];
  };
  const enough = (doc, kind) => {
    if (limit === Infinity) return false;
    const c = collect(doc, kind);
    return c.length >= limit && c.slice(0, limit).every((it) => it.listText);
  };
  const pageHeight = (doc) => Math.max(doc.body ? doc.body.scrollHeight : 0, doc.documentElement ? doc.documentElement.scrollHeight : 0);

  // --- 最初の商品が出るまで待つ(遅い読み込み対策) ---
  const waitFirst = async (doc, kind) => {
    const t0 = Date.now();
    while (Date.now() - t0 < INITIAL_WAIT_MS) {
      if (collect(doc, kind).length > 0) return true;
      await sleep(300);
    }
    return false;
  };

  // --- 先頭N件が出そろうまで(または一覧が尽きるまで)自動スクロール ---
  const loadKind = async (win, doc, kind) => {
    let last = -1, stable = 0, tries = 0;
    while (true) {
      if (enough(doc, kind)) break;
      try { win.scrollTo(0, pageHeight(doc)); } catch (e) { /* ignore */ }
      [...doc.querySelectorAll('button, a')]
        .filter((b) => /もっと見る|さらに表示|もっと読み込む|load more/i.test(b.innerText || ''))
        .forEach((b) => b.click());
      await sleep(SCROLL_WAIT_MS);
      const n = collect(doc, kind).length;
      if (n === last) stable++; else { stable = 0; last = n; }
      tries++;
      if (stable >= STABLE_LIMIT || tries >= MAX_SCROLL_TRIES) break;
    }
    try { win.scrollTo(0, 0); } catch (e) { /* ignore */ }
    const all = collect(doc, kind);
    return limit === Infinity ? all : all.slice(0, limit);
  };

  const kindPathRe = (kind) => new RegExp(`/u/${reEsc(userId)}/${kind}/?$`);

  // ① 今開いているタブがその種別
  const viaCurrent = async (kind) => {
    if (!kindPathRe(kind).test(location.pathname)) return null;
    if (!(await waitFirst(document, kind))) return [];
    return loadKind(window, document, kind);
  };

  // ② 見えない iframe で開いて読む
  const viaIframe = async (kind) => {
    let frame = null;
    try {
      frame = document.createElement('iframe');
      frame.setAttribute('aria-hidden', 'true');
      frame.style.cssText = 'position:fixed;left:0;top:0;width:1280px;height:900px;border:0;opacity:0;pointer-events:none;z-index:-1;';
      frame.src = `https://cluster.mu/u/${userId}/${kind}`;
      const loaded = new Promise((res) => frame.addEventListener('load', () => res(true), { once: true }));
      document.body.appendChild(frame);
      const ok = await Promise.race([loaded, sleep(FRAME_LOAD_TIMEOUT_MS).then(() => false)]);
      if (!ok) { console.warn(`[${kind}] iframe: 読み込みタイムアウト`); return null; }
      let win, doc;
      try { win = frame.contentWindow; doc = frame.contentDocument; void doc.body; void win.location.pathname; }
      catch (e) { console.warn(`[${kind}] iframe: 中身にアクセスできません(埋め込み禁止の可能性)`); return null; }
      if (!doc || !kindPathRe(kind).test(win.location.pathname)) {
        console.warn(`[${kind}] iframe: 想定と違うページが開きました (${win.location && win.location.pathname})`);
        return null;
      }
      if (!(await waitFirst(doc, kind))) return [];
      return await loadKind(win, doc, kind);
    } catch (e) {
      console.warn(`[${kind}] iframe: エラー`, e);
      return null;
    } finally {
      if (frame && frame.parentNode) frame.parentNode.removeChild(frame);
    }
  };

  // ③ ページ内のタブをクリックして読む
  const findTab = (kind) => {
    const byHref = [...document.querySelectorAll('a[href]')].find((a) => {
      try { return kindPathRe(kind).test(new URL(a.href, location.href).pathname); } catch (e) { return false; }
    });
    if (byHref) return byHref;
    const texts = TAB_TEXTS[kind] || [];
    return [...document.querySelectorAll('[role="tab"], a, button')]
      .find((el) => texts.includes((el.innerText || el.textContent || '').trim()));
  };
  const viaClick = async (kind) => {
    const tab = findTab(kind);
    if (!tab) { console.warn(`[${kind}] クリック: タブが見つかりません`); return null; }
    tab.click();
    const t0 = Date.now();
    while (!kindPathRe(kind).test(location.pathname)) {
      if (Date.now() - t0 > TAB_SWITCH_TIMEOUT_MS) { console.warn(`[${kind}] クリック: タブが切り替わりません`); return null; }
      await sleep(200);
    }
    await sleep(1000);
    if (!(await waitFirst(document, kind))) return [];
    return loadKind(window, document, kind);
  };

  // --- 名称補完 ---
  const cleanTitle = (t) =>
    (t || '').replace(/\s*[|｜\-–—]\s*(cluster|クラスター|Cluster ストア|cluster ストア).*$/i, '').replace(/\s+/g, ' ').trim();
  const fetchName = async (url) => {
    try {
      const html = await (await fetch(url, { credentials: 'include' })).text();
      const d = new DOMParser().parseFromString(html, 'text/html');
      const og = d.querySelector('meta[property="og:title"]')?.content;
      const h1 = d.querySelector('h1')?.textContent;
      return cleanTitle(og || h1 || d.title);
    } catch (e) { return ''; }
  };

  // --- 途中保存(ブラウザの localStorage) ---
  const SAVE_KEY = `cluster_shop_extract:${userId}:${limit === Infinity ? 'all' : limit}`;
  const loadSaved = () => {
    try {
      const o = JSON.parse(localStorage.getItem(SAVE_KEY) || 'null');
      return o && Date.now() - o.t < SAVE_TTL_MS ? o.kinds || {} : {};
    } catch (e) { return {}; }
  };
  const saveSaved = (kinds) => { try { localStorage.setItem(SAVE_KEY, JSON.stringify({ t: Date.now(), kinds })); } catch (e) { /* ignore */ } };
  const clearSaved = () => { try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ } };

  // --- メイン ---
  const got = {};     // kind -> rows[]  (今回取得できたもの)
  const how = {};     // kind -> 方法
  for (const kind of KINDS) {
    console.log(`--- ${KIND_LABEL[kind]} (${kind}) ---`);
    let items = null, method = '';
    items = await viaCurrent(kind);
    if (items !== null) method = '今のタブ';
    if (items === null) {
      items = await viaIframe(kind);
      if (items !== null) method = 'iframe';
    }
    if (items === null || items.length === 0) {
      // 取れなかった / 0件だったときは、クリック方式でも確認する(iframeで描画されなかった場合の保険)
      const second = await viaClick(kind);
      if (second !== null && (items === null || second.length > 0)) { items = second; method = 'タブクリック'; }
    }
    if (items === null) { console.warn(`[${kind}] どの方法でも取得できませんでした`); continue; }

    for (const it of items) {
      it.name = it.listText;
      if (FETCH_DETAIL || !it.name) { it.name = (await fetchName(it.url)) || it.listText; await sleep(DETAIL_WAIT_MS); }
    }
    got[kind] = items.map((it) => [uid, KIND_LABEL[kind], it.name, it.url]);
    how[kind] = method;
    console.log(`${KIND_LABEL[kind]}: ${items.length} 件 (${method})`);
  }

  // --- 保存分と合体 ---
  const saved = loadSaved();
  const merged = {};
  const summary = [];
  for (const kind of KINDS) {
    if (got[kind]) { merged[kind] = got[kind]; summary.push({ 種別: KIND_LABEL[kind], 件数: got[kind].length, 取得元: how[kind] }); }
    else if (saved[kind]) { merged[kind] = saved[kind]; summary.push({ 種別: KIND_LABEL[kind], 件数: saved[kind].length, 取得元: '前回の保存分' }); }
    else summary.push({ 種別: KIND_LABEL[kind], 件数: '-', 取得元: '未取得' });
  }
  console.table(summary);
  const missing = KINDS.filter((k) => !merged[k]);
  if (missing.length) {
    saveSaved(merged);
    console.warn(`未取得の種別: ${missing.map((k) => KIND_LABEL[k] + '(' + k + ')').join(', ')}\n` +
      `取れた分はブラウザに一時保存しました。次のページを開いて、このスクリプトをもう一度貼り付けてください:\n` +
      missing.map((k) => `  https://cluster.mu/u/${userId}/${k}`).join('\n'));
    return;
  }

  // --- CSV 化・出力(3種別を結合) ---
  const rows = KINDS.flatMap((k) => merged[k]);
  if (rows.length === 0) { console.error('3種別とも0件でした。ユーザページで実行しているか確認してください。'); return; }
  const badUrl = rows.filter((r) => !UUID_RE.test(r[3].split('/').pop())).length;
  const dupUrl = rows.length - new Set(rows.map((r) => r[3])).size;
  const emptyName = rows.filter((r) => !r[2]).length;

  const esc = (s) => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const header = ['UID(一意に特定するID)', '種別', '商品名', '商品コード(urlもあり)'];
  const csv = [header, ...rows].map((r) => r.map(esc).join(',')).join('\r\n');

  try { await navigator.clipboard.writeText(csv); console.log('CSV をクリップボードにコピーしました'); }
  catch (e) { console.warn('クリップボードへのコピーに失敗(ページにフォーカスがない場合など)。ダウンロードを使ってください。'); }

  const fname = `friend_items_${uid}_${userId}${limit === Infinity ? '' : '_top' + limit}.csv`;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = fname;
  document.body.appendChild(a); a.click(); a.remove();
  clearSaved();

  console.table(rows.map((r) => ({ UID: r[0], 種別: r[1], 商品名: r[2], url: r[3].slice(-8) })));
  if (badUrl) console.warn(`UUID形式でないURLが ${badUrl} 件あります。`);
  if (dupUrl) console.warn(`URLの重複が ${dupUrl} 件あります。`);
  if (emptyName) console.warn(`商品名が空の行が ${emptyName} 件あります。確認してください。`);
  console.log(`完了: 合計 ${rows.length} 件 → ${fname}`);
})();