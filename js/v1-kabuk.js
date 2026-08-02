/**
 * İhaleGlobal v1 — KABUK (ihalepro düzeni: sol dar ray + topbar + breadcrumb)
 * Her v1 sayfası bunu yükler; sidebar/topbar tek yerden gelir.
 *
 * Kullanım (v1 sayfasında):
 *   <link rel="stylesheet" href="css/v1.css?v=1">
 *   <body class="v1" data-v1-aktif="ihaleler" data-v1-kirinti="Kamu > İhaleler">
 *     <div class="v1-app"><div class="v1-main"> ...sayfa... </div></div>
 *   <script src="js/v1-kabuk.js?v=1"></script>
 *
 * v1/v2: sürüm tercihi localStorage 'ihale_surum' ('v1'|'v2'). Profil menüsünden değişir.
 */
(() => {
  'use strict';

  /**
   * ── TÜRKÇE ARAMA YARDIMCISI (tüm v1 sayfaları buradan kullanır) ─────────
   * ⛔ PostgREST `ilike` Türkçe İ/ı'da SESSİZCE 0 döndürür: kullanıcı "insaat"
   *    yazınca "İnşaat" kayıtları hiç gelmez — hata da vermez, liste boş çıkar.
   *    Çözüm: karşılaştırmayı katlanmış (fold) kolon üzerinden yap.
   *
   *    v1Ara(sorgu, 'baslik_fold', kullaniciMetni)   →  düz ilike YERİNE bunu çağır
   *
   * ⚠️ Kolon seçimi maskelemeyi etkiler: `baslik_fold` misafire AÇIK (başlık zaten
   *    açık), `arama_fold` idare adını da içerdiği için anon'a KAPALI (401) —
   *    misafir dalında arama_fold KULLANMA.
   */
  const trFold = (s) => (s || '').toLocaleLowerCase('tr')
    .replace(/i̇/g, 'i').replace(/ı/g, 'i').replace(/İ/g, 'i')
    .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ö/g, 'o')
    .replace(/ş/g, 's').replace(/ü/g, 'u');
  window.trFold = trFold;
  // PostgREST kalıbı: * joker, virgül/parantez sorgu ayrıştırıcısını bozar → temizle
  window.v1AramaKalibi = (metin) => '*' + trFold(metin).replace(/[,()*]/g, ' ').trim() + '*';
  window.v1Ara = (sorgu, kolon, metin) => {
    const m = (metin || '').trim();
    return m ? sorgu.ilike(kolon, window.v1AramaKalibi(m)) : sorgu;
  };

  // ── İkonlar (dolu/filled — ihalepro kurumsal his) ──────────────────────
  const I = {
    home:   '<svg viewBox="0 0 24 24"><path d="M12 3 2.5 11.1h2.6V21h5.1v-5.9h3.6V21h5.1v-9.9h2.6L12 3Z"/></svg>',
    analiz: '<svg viewBox="0 0 24 24"><path d="M4 20h16v1.6H4V20Zm1.2-8.4h3v7h-3v-7Zm5.3-5.2h3v12.2h-3V6.4Zm5.3 8h3v4.2h-3v-4.2Z"/></svg>',
    dosya:  '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M8 2h6.2L21 8.8V20a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm5.6 8.4V3.9L20.1 10.4h-6.5Z"/></svg>',
    bayrak: '<svg viewBox="0 0 24 24"><path d="M5 2.5h1.8v19H5v-19Zm3.2 1.2h11.3l-2.6 4.2 2.6 4.2H8.2V3.7Z"/></svg>',
    para:   '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm.9 4.3v1.3c1.5.2 2.6 1 2.9 2.4h-1.9c-.2-.6-.8-1-1.7-1-1 0-1.6.4-1.6 1.1 0 .6.4.9 1.7 1.2l1 .2c2 .5 2.9 1.3 2.9 2.9 0 1.6-1.2 2.7-3.2 2.9v1.4h-1.7v-1.4c-1.7-.2-2.9-1.1-3.1-2.6h1.9c.2.7.9 1.1 1.9 1.1s1.7-.4 1.7-1.1c0-.6-.4-.9-1.6-1.2l-1.1-.3c-1.9-.4-2.8-1.3-2.8-2.8 0-1.6 1.2-2.6 3-2.9V6.3h1.7Z"/></svg>',
    tokmak: '<svg viewBox="0 0 24 24"><path d="m13.4 2.6 4.6 4.6-2.1 2.1-4.6-4.6 2.1-2.1ZM3.6 12.4l6.4-6.4 4.6 4.6-6.4 6.4-4.6-4.6ZM2 19.8h11.5v2.2H2v-2.2Z"/></svg>',
    firma:  '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M4.8 2h6.8a1.4 1.4 0 0 1 1.4 1.4v6.2h6.2a1.4 1.4 0 0 1 1.4 1.4V22H3.4V3.4A1.4 1.4 0 0 1 4.8 2Zm.6 3.1v2h2v-2h-2Zm3.6 0v2h2v-2h-2Zm-3.6 3.6v2h2v-2h-2Zm3.6 0v2h2v-2h-2Zm-3.6 3.6v2h2v-2h-2Zm3.6 0v2h2v-2h-2Zm6.8 0v2h2v-2h-2Zm0 3.6v2h2v-2h-2Z"/></svg>',
    kurum:  '<svg viewBox="0 0 24 24"><path d="M12 2.15a1.1 1.1 0 0 0-.49.11L2.28 6.9A1.4 1.4 0 0 0 1.5 8.16V9.3a.7.7 0 0 0 .7.7h19.6a.7.7 0 0 0 .7-.7V8.16a1.4 1.4 0 0 0-.78-1.26l-9.23-4.64a1.1 1.1 0 0 0-.49-.11Z"/><path d="M4.3 11.6h3v6.6h-3zM10.5 11.6h3v6.6h-3zM16.7 11.6h3v6.6h-3z"/><path d="M2.6 19.8h18.8a1.1 1.1 0 0 1 0 2.2H2.6a1.1 1.1 0 0 1 0-2.2Z"/></svg>',
    sektor: '<svg viewBox="0 0 24 24"><path d="M3 20.5V9.8l5.5-3.2v2.5l5.5-3.2v3.2L21 5.8v14.7H3Zm3-2.2h2.6v-3H6v3Zm5.5 0h2.6v-3h-2.6v3Zm5.5 0h2.6v-3H17v3Z"/></svg>',
    global: '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.9 6.5h-2.6a15 15 0 0 0-1.3-3.4 8.1 8.1 0 0 1 3.9 3.4ZM12 4.1c.7 1 1.3 2.2 1.7 3.4h-3.4c.4-1.2 1-2.4 1.7-3.4ZM4.2 13.5A8 8 0 0 1 4 12c0-.5.1-1 .2-1.5h3a16 16 0 0 0 0 3h-3Zm.9 2h2.6c.3 1.2.8 2.3 1.3 3.4a8.1 8.1 0 0 1-3.9-3.4Zm2.6-7H5.1a8.1 8.1 0 0 1 3.9-3.4c-.5 1.1-1 2.2-1.3 3.4ZM12 19.9c-.7-1-1.3-2.2-1.7-3.4h3.4c-.4 1.2-1 2.4-1.7 3.4Zm2.1-5.4H9.9a13.6 13.6 0 0 1 0-3h4.2a13.6 13.6 0 0 1 0 3Zm.8 4.4c.5-1.1 1-2.2 1.3-3.4h2.6a8.1 8.1 0 0 1-3.9 3.4Zm1.7-5.4a16 16 0 0 0 0-3h3c.1.5.2 1 .2 1.5s-.1 1-.2 1.5h-3Z"/></svg>',
    ara:    '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M10.5 3a7.5 7.5 0 1 0 4.55 13.46l4.24 4.25 1.42-1.42-4.25-4.24A7.5 7.5 0 0 0 10.5 3Zm0 2a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11Z"/></svg>',
    rapor:  '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M8 2h6.2L21 8.8V20a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm5.6 8.4V3.9L20.1 10.4h-6.5ZM9 15.4h1.6v3.2H9v-3.2Zm2.6-2.2h1.6v5.4h-1.6v-5.4Zm2.6 3h1.6v2.4h-1.6v-2.4Z"/></svg>',
    kisi:   '<svg viewBox="0 0 24 24"><path d="M12 12a4.6 4.6 0 1 0 0-9.2 4.6 4.6 0 0 0 0 9.2Zm0 2c-3.6 0-8 1.8-8 4.4V21h16v-2.6c0-2.6-4.4-4.4-8-4.4Z"/></svg>',
    takvim: '<svg viewBox="0 0 24 24"><path fill-rule="evenodd" d="M7 2v2H5.5A2.5 2.5 0 0 0 3 6.5v13A2.5 2.5 0 0 0 5.5 22h13a2.5 2.5 0 0 0 2.5-2.5v-13A2.5 2.5 0 0 0 18.5 4H17V2h-2v2H9V2H7Zm12 8H5v9.5c0 .28.22.5.5.5h13a.5.5 0 0 0 .5-.5V10Z"/></svg>',
    zil:    '<svg viewBox="0 0 24 24"><path d="M12 2a1.6 1.6 0 0 1 1.6 1.6v.62a6 6 0 0 1 4.4 5.78v3.2l1.42 2.46a1 1 0 0 1-.87 1.5H5.45a1 1 0 0 1-.87-1.5L6 13.2V10a6 6 0 0 1 4.4-5.78V3.6A1.6 1.6 0 0 1 12 2Z"/><path d="M9.6 18.5h4.8a2.4 2.4 0 0 1-4.8 0Z"/></svg>',
    ticaret:'<svg viewBox="0 0 24 24"><path d="M2.6 6.4 12 2.2l9.4 4.2-9.4 4.2L2.6 6.4Z"/><path d="M2.4 9.1 11 12.9v8.9L2.4 18V9.1ZM13 12.9l8.6-3.8V18L13 21.8v-8.9Z"/></svg>',
    sepet:  '<svg viewBox="0 0 24 24"><path d="M2 3h3.1l.9 3H21a1 1 0 0 1 .96 1.28l-2.2 7.4A2 2 0 0 1 17.84 16H9.1a2 2 0 0 1-1.93-1.47L4.4 5H2V3Z"/><path d="M9.5 18.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4ZM17.5 18.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z"/></svg>',
    harita: '<svg viewBox="0 0 24 24"><path d="M9 2.4 3.3 4.6A1.4 1.4 0 0 0 2.4 5.9v14.3a1 1 0 0 0 1.36.93L9 19.2V2.4ZM15 4.8 11 2.6v16.8l4 2.2V4.8ZM17 4.8v16.8l3.7-2.2a1.4 1.4 0 0 0 .9-1.3V3.8a1 1 0 0 0-1.36-.93L17 4.8Z"/></svg>',
    yildiz: '<svg viewBox="0 0 24 24"><path d="m12 2.6 2.9 5.9 6.5.95-4.7 4.58 1.11 6.47L12 17.44l-5.81 3.06 1.11-6.47-4.7-4.58 6.5-.95L12 2.6Z"/></svg>',
    klasor: '<svg viewBox="0 0 24 24"><path d="M2.4 5.6A2.2 2.2 0 0 1 4.6 3.4h4.3l2.2 2.6h8.3a2.2 2.2 0 0 1 2.2 2.2v10.2a2.2 2.2 0 0 1-2.2 2.2H4.6a2.2 2.2 0 0 1-2.2-2.2V5.6Z"/></svg>',
  };

  // ── Menü (ihalepro nav'ıyla birebir sıra) ──────────────────────────────
  // ⚠️ VERİ/SAYFA BÖLÜNMÜYOR — bu yalnızca GÖRSEL menü gruplaması. Çekirdek (kamu ihale işi)
  //    üstte; kamu-ihale-dışı komşu alanlar (Global/Dış Ticaret/e-Satınalma/Bank) altta
  //    "Keşfet" ayracının altında. Tüm sayfalar/RPC'ler/veriler aynen çalışır; sadece
  //    ihale arayan firmanın gözü çekirdeğe odaklansın diye komşular ayrık gösterilir.
  // ── DÜNYALAR (üst bar sekmeleri) — her dünyanın KENDİ sol menüsü ──────────
  // Kamu = çekirdek kamu ihale işi (varsayılan). Global İhaleler + E-Satınalma AYRI dünyalar;
  // üst bardan geçilir, sidebar o dünyaya göre değişir. (Eski sidebar "Keşfet" grubu kaldırıldı;
  // Global/Dış Ticaret/Bank → Global dünyasına, e-Satınalma → kendi dünyasına taşındı.)
  const MENU_KAMU = [
    { id: 'benim',      ad: 'Bana Özel',   ikon: I.home,   href: 'v1-benim-sayfam' },
    { id: 'takipte',    ad: 'Takibim',     ikon: I.yildiz, href: 'v1-takipte' },
    { id: 'analiz',     ad: 'Analiz',      ikon: I.analiz, href: 'v1-analiz' },
    { id: 'ihaleler',   ad: 'İhaleler',    ikon: I.dosya,  href: 'v1-ihaleler' },
    { id: 'sonuclar',   ad: 'Sonuçlar',    ikon: I.bayrak, href: 'v1-ihaleler?sekme=sonuc' },
    { id: 'sozlesme',   ad: 'Sözleşmeler', ikon: I.para,   href: 'v1-sozlesmeler' },
    { id: 'firmalar',   ad: 'Firmalar',    ikon: I.firma,  href: 'v1-firmalar' },
    { id: 'kurumlar',   ad: 'Kurumlar',    ikon: I.kurum,  href: 'v1-kurumlar' },
    { id: 'sektorler',  ad: 'Sektörler',   ikon: I.sektor, href: 'v1-sektorler' },
    { id: 'harita',     ad: 'Harita',      ikon: I.harita, href: 'v1-harita' },
    { id: 'kararlar',   ad: 'Kararlar',    ikon: I.tokmak, href: 'v1-kararlar' },
    { id: 'dokumanlar', ad: 'Dokümanlar',  ikon: I.klasor, href: 'v1-dokumanlar' },
  ];
  const MENU_GLOBAL = [
    { id: 'global',     ad: 'Global İhaleler', ikon: I.global,  href: 'v1-global' },
    { id: 'disticaret', ad: 'Dış Ticaret',     ikon: I.ticaret, href: 'v1-dis-ticaret' },
  ];
  const MENU_ESATINALMA = [
    { id: 'esatinalma', ad: 'Satınalma',  ikon: I.sepet, href: 'v1-esatinalma' },
    { id: 'ihalelerim', ad: 'İhalelerim', ikon: I.rapor, href: 'v1-ihalelerim' },
    { id: 'harita', ad: 'Harita', ikon: I.harita, href: 'v1-harita?dunya=esatinalma' },
    { id: 'bank',   ad: 'Bank',   ikon: I.para,   href: 'v1-bank' },
  ];
  const DUNYALAR = [
    { ws: 'kamu',       ad: 'Kamu',            ikon: I.kurum,  landing: 'v1-benim-sayfam', menu: MENU_KAMU },
    { ws: 'global',     ad: 'Global İhaleler', ikon: I.global, landing: 'v1-global',       menu: MENU_GLOBAL },
    { ws: 'esatinalma', ad: 'E-Satınalma',     ikon: I.sepet,  landing: 'v1-esatinalma',   menu: MENU_ESATINALMA },
  ];
  // Aktif sayfa (data-v1-aktif) hangi dünyaya ait — eşleşmezse 'kamu'
  const WS_OF = { global: 'global', disticaret: 'global', bank: 'esatinalma', esatinalma: 'esatinalma', ihalelerim: 'esatinalma' };

  const aktif = document.body.getAttribute('data-v1-aktif') || '';
  const kirinti = document.body.getAttribute('data-v1-kirinti') || '';
  // Aktif dünya + o dünyanın sol menüsü (üst bar sekmesi buna göre vurgulanır)
  // ?dunya= paramı workspace'i override eder → aynı sayfa (ör. v1-harita) birden çok dünyada
  // doğru sol menü + üst sekmeyle görünebilir. Yoksa aktif sayfanın WS_OF eşlemesi, o da yoksa Kamu.
  const _dunyaParam = new URLSearchParams(location.search).get('dunya');
  const suWs = (_dunyaParam && ['kamu','global','esatinalma'].includes(_dunyaParam)) ? _dunyaParam : (WS_OF[aktif] || 'kamu');
  const suDunya = DUNYALAR.find(d => d.ws === suWs) || DUNYALAR[0];
  const MENU = suDunya.menu;

  // ── Sol ray ────────────────────────────────────────────────────────────
  const ray = document.createElement('aside');
  ray.className = 'v1-ray';
  ray.innerHTML =
    // <a> menü öğeleri ZİYARET EDİLİNCE (:visited) soluyordu. Kök neden: alfa'lı renk
    // (rgba .82). Tarayıcı gizlilik modeli :visited'te alfa kanalını + fill:currentColor'ı
    // kısıtlar → tıklanan öğe soluk kalır. Çözüm: SOLID renk (alfa yok) + !important.
    '<style>.v1-ray-item,.v1-ray-item:link,.v1-ray-item:visited{color:#E8EEF4!important}'
    + '.v1-ray-item:hover,.v1-ray-item:visited:hover{color:#fff!important}'
    + '.v1-ray-item.aktif,.v1-ray-item.aktif:visited{color:var(--v1-lacivert)!important}'
    + '.v1-dunya-gecis{display:flex;gap:3px;background:#EAF1F8;border-radius:10px;padding:3px;margin-right:8px;}'
    + '.v1-dunya-sekme{display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border-radius:8px;font-family:var(--v1-font);font-size:12.5px;font-weight:700;color:var(--v1-muted);text-decoration:none;white-space:nowrap;}'
    + '.v1-dunya-sekme svg{width:15px;height:15px;fill:currentColor;flex-shrink:0;}'
    + '.v1-dunya-sekme:hover{color:var(--v1-lacivert);text-decoration:none;}'
    + '.v1-dunya-sekme.aktif{background:#fff;color:var(--v1-lacivert);box-shadow:0 1px 3px rgba(12,62,112,.14);}'
    + '@media(max-width:900px){.v1-dunya-sekme{padding:7px 9px;font-size:11.5px;}}'
    + '.v1-ara-btn-dolu{background:var(--v1-mavi);align-self:stretch;margin:0;border-radius:0;padding:0 18px;display:flex;align-items:center;gap:7px;}'
    + '.v1-ara-btn-dolu svg{fill:#fff;width:18px;height:18px;}'
    + '.v1-ara-btn-dolu .v1-ara-btn-yazi{color:#fff;font-family:var(--v1-font);font-size:13px;font-weight:700;}'
    + '.v1-ara-btn-dolu:hover{background:var(--v1-lacivert);}'
    + '@media(max-width:720px){.v1-ara-btn-dolu .v1-ara-btn-yazi{display:none;}}</style>' +
    '<a class="v1-ray-logo" href="v1-benim-sayfam" title="İhaleGlobal"><img src="/favicon-v1.svg?v=1" alt="İhaleGlobal"></a>' +
    '<nav class="v1-ray-nav">' +
    MENU.map((m) =>
      `<a class="v1-ray-item${m.id === aktif ? ' aktif' : ''}" href="${m.href}" title="${m.ad}" style="text-decoration:none;">${m.ikon}<span>${m.ad}</span></a>`
    ).join('') +
    '</nav>';

  // ── Topbar ─────────────────────────────────────────────────────────────
  const topbar = document.createElement('div');
  topbar.className = 'v1-topbar';
  topbar.innerHTML = `
    <div class="v1-ara-kutu">
      <select class="v1-ara-kapsam" id="v1-kapsam" title="Arama kapsamı">
        <option value="ihale">İhale</option>
        <option value="firma">Firma</option>
        <option value="idare">İdare</option>
        <option value="sonuc">Sonuç</option>
        <option value="dt">Doğrudan Temin</option>
      </select>
      <input type="text" id="v1-ara" placeholder="İhale, firma, kurum, sonuç ara..">
      <button class="v1-ara-btn v1-ara-btn-dolu" id="v1-ara-btn" aria-label="Ara" title="Ara">${I.ara}<span class="v1-ara-btn-yazi">Ara</span></button>
    </div>
    <div class="v1-top-sag">
      <div class="v1-dunya-gecis">${DUNYALAR.map(d => `<a class="v1-dunya-sekme${d.ws === suWs ? ' aktif' : ''}" href="${d.landing}" title="${d.ad}">${d.ikon}<span>${d.ad}</span></a>`).join('')}</div>
      <a class="v1-fasonda" href="https://fasonda.com" target="_blank" rel="noopener"
         title="Fasonda.com — üretim & tedarik pazar yeri">
        <span class="v1-fasonda-ikon">🏭</span>
        <span class="v1-fasonda-yazi">Fasonda.com'a<br><strong>Geçiş Yap →</strong></span>
      </a>
      <div class="v1-paket">
        <div class="v1-paket-ad">Mevcut Paket<strong id="v1-paket-ad">—</strong></div>
        <button class="v1-paket-btn" onclick="location.href='fiyatlandirma_odeme_bolumu'">Paket Yükselt</button>
      </div>
      <div class="v1-top-ikon" title="Raporlarım" onclick="location.href='v1-raporlar'">${I.rapor}</div>
      <div class="v1-top-ikon" title="Profilim" id="v1-profil-btn">${I.kisi}</div>
      <div class="v1-top-ikon" title="Ajandam" onclick="location.href='v1-ajanda'">${I.takvim}</div>
      <div class="v1-top-ikon" title="Bildirimler" onclick="location.href='v1-bildirimler'">${I.zil}</div>
    </div>`;

  // ── Breadcrumb ─────────────────────────────────────────────────────────
  let kirintiEl = null;
  if (kirinti) {
    kirintiEl = document.createElement('div');
    kirintiEl.className = 'v1-kirinti';
    const parcalar = kirinti.split('>').map(s => s.trim()).filter(Boolean);
    /**
     * ARA SEGMENTLER TIKLANABİLİR: "Analiz › Harita"da Analiz'e basınca üst sayfaya dönülür.
     * Hedef MENU dizisindeki ad↔href eşlemesinden bulunur; menüde karşılığı olmayan başlıklar
     * (Hesabım, Araçlar, Kamu…) KIRINTI_EK'ten çözülür. İkisinde de yoksa düz metin kalır —
     * kırık link üretmeyiz. SON segment her zaman düz metin (zaten bulunulan sayfa).
     */
    const KIRINTI_EK = {
      'hesabım': 'v1-benim-sayfam', 'ihaleglobal': 'v1-benim-sayfam', 'bana özel': 'v1-benim-sayfam',
      'global': 'v1-global', 'kamu': 'v1-ihaleler', 'araçlar': 'v1-ihaleler',
      'e-satınalma': 'v1-esatinalma', 'firmalar': 'v1-firmalar', 'kurumlar': 'v1-kurumlar',
    };
    const hedefBul = (ad) => {
      const k = ad.toLocaleLowerCase('tr');
      const m = MENU.find(x => x.ad.toLocaleLowerCase('tr') === k);
      return m ? m.href : (KIRINTI_EK[k] || null);
    };
    kirintiEl.innerHTML = '<a href="v1-benim-sayfam" title="Ana sayfa">🏠</a>' +
      parcalar.map((p, i) => {
        const son = i === parcalar.length - 1;
        const hedef = son ? null : hedefBul(p);
        const govde = hedef
          ? `<a href="${hedef}">${p}</a>`
          : `<span${son ? ' class="son"' : ''}>${p}</span>`;
        return ` <span>›</span> ${govde}`;
      }).join('');
  }

  // ── Monte et ───────────────────────────────────────────────────────────
  function mont() {
    const app = document.querySelector('.v1-app');
    const main = document.querySelector('.v1-main');
    if (!app || !main) return;
    app.insertBefore(ray, app.firstChild);
    main.insertBefore(topbar, main.firstChild);
    if (kirintiEl) main.insertBefore(kirintiEl, topbar.nextSibling);

    // Menü öğeleri artık <a href> → tıklama NATİF gezinir; orta/Ctrl/sağ tık "yeni sekmede
    // aç" da çalışır. Ayrı JS click handler'ı YOK (olursa yeni-sekme davranışını bozar).

    // Arama → kapsama göre v1 sayfasına yönlendir (?ara=)
    const inp = topbar.querySelector('#v1-ara');
    const sel = topbar.querySelector('#v1-kapsam');
    const git = () => {
      const q = inp.value.trim();
      // MADDE 21: 1-2 harflik arama hedef sayfada tam-tablo taraması yapar → boşa yük. En az 3 harf.
      if (q.length < 3) {
        if (q.length) { inp.placeholder = 'En az 3 harf yazın…'; inp.style.borderColor = '#c0392b';
          setTimeout(() => { inp.style.borderColor = ''; }, 1200); }
        return;
      }
      const e = encodeURIComponent(q);
      const rota = {
        ihale: 'v1-ihaleler?ara=' + e, firma: 'v1-firmalar?ara=' + e, idare: 'v1-kurumlar?ara=' + e,
        sonuc: 'v1-ihaleler?sekme=sonuc&ara=' + e, dt: 'v1-ihaleler?tur=dt&ara=' + e,
      };
      location.href = rota[sel.value] || rota.ihale;
    };
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') git(); });
    topbar.querySelector('#v1-ara-btn').addEventListener('click', git);
    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); inp.focus(); inp.select(); }
    });

    // Profil menüsü — SÜRÜM GEÇİŞİ burada (v1 ↔ v2)
    topbar.querySelector('#v1-profil-btn').addEventListener('click', profilMenu);
  }

  // ── Profil menüsü + v1/v2 sürüm geçişi ─────────────────────────────────
  function profilMenu(ev) {
    ev.stopPropagation();
    let m = document.getElementById('v1-profil-menu');
    if (m) { m.remove(); return; }
    m = document.createElement('div');
    m.id = 'v1-profil-menu';
    m.style.cssText = 'position:fixed;z-index:9999;min-width:230px;background:#fff;border:1px solid var(--v1-cizgi);' +
      'border-radius:12px;box-shadow:0 14px 34px rgba(12,62,112,.18);padding:6px;font-family:var(--v1-font);';
    const r = ev.currentTarget.getBoundingClientRect();
    m.style.top = (r.bottom + 8) + 'px';
    m.style.right = Math.max(8, window.innerWidth - r.right) + 'px';
    const btn = (metin, fn, renk) =>
      `<button style="display:flex;align-items:center;gap:9px;width:100%;text-align:left;background:none;border:none;` +
      `color:${renk || 'var(--v1-metin)'};font-family:inherit;font-size:13.5px;font-weight:600;padding:10px 12px;` +
      `border-radius:8px;cursor:pointer;" data-fn="${fn}">${metin}</button>`;
    m.innerHTML =
      '<div style="padding:8px 12px 4px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--v1-muted);">Sürüm</div>' +
      btn('🔵 <span>Standart (aktif)</span>', 'v1', 'var(--v1-mavi)') +
      btn('🔒 <span>Kurumsal (v2)</span>', 'v2') +
      '<div style="height:1px;background:var(--v1-cizgi);margin:5px 6px;"></div>' +
      btn('⚙️ <span>Profil &amp; Ayarlar</span>', 'profil') +
      btn('💳 <span>Abonelik</span>', 'abonelik') +
      btn('🚪 <span>Çıkış Yap</span>', 'cikis', 'var(--v1-kirmizi)');
    document.body.appendChild(m);
    m.querySelectorAll('[data-fn]').forEach(b => b.addEventListener('click', (e) => {
      e.stopPropagation();
      const f = b.dataset.fn;
      if (f === 'v2') {
        // Kurumsal (v2) ŞİFRE KİLİDİ — geçici soft-gate (client-side; kalıcısı server-side rol olacak).
        m.remove();
        v2SifreModal((dogru) => {
          if (!dogru) return;
          try { sessionStorage.setItem('kurumsal_v2', '1'); } catch (_) {}
          localStorage.setItem('ihale_surum', 'v2'); location.href = 'benim-sayfam';
        });
      }
      else if (f === 'v1') { localStorage.setItem('ihale_surum', 'v1'); m.remove(); }
      else if (f === 'profil') location.href = 'v1-profil';
      else if (f === 'abonelik') location.href = 'fiyatlandirma_odeme_bolumu';
      else if (f === 'cikis') { try { localStorage.removeItem('ihale_token'); } catch (_) {} location.href = '/'; }
    }));
    setTimeout(() => document.addEventListener('click', function kapat() { m.remove(); document.removeEventListener('click', kapat); }), 0);
  }

  // ── Kurumsal (v2) şifre modalı (native prompt yerine stilize) ──────────
  function v2SifreModal(cb) {
    const ov = document.createElement('div');
    ov.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(12,62,112,.32);display:flex;align-items:center;justify-content:center;font-family:var(--v1-font);padding:16px;';
    ov.innerHTML =
      '<div style="background:#fff;border-radius:16px;box-shadow:0 24px 60px rgba(12,62,112,.28);max-width:340px;width:100%;padding:22px;">' +
        '<div style="font-size:16px;font-weight:800;color:var(--v1-metin);display:flex;align-items:center;gap:8px;">🔒 Kurumsal (v2) Girişi</div>' +
        '<div style="font-size:12.5px;color:var(--v1-muted);margin:6px 0 14px;">Bu sürüm şifreyle korunmaktadır.</div>' +
        '<input id="v2-sifre-inp" type="password" placeholder="Şifre" autocomplete="off" ' +
          'style="width:100%;box-sizing:border-box;padding:11px 13px;border:1px solid var(--v1-cizgi);border-radius:10px;font-size:14px;font-family:inherit;outline:none;">' +
        '<div id="v2-sifre-hata" style="color:var(--v1-kirmizi);font-size:12px;font-weight:600;height:16px;margin:6px 2px 0;"></div>' +
        '<div style="display:flex;gap:8px;margin-top:12px;">' +
          '<button id="v2-sifre-iptal" style="flex:1;padding:10px;border:1px solid var(--v1-cizgi);background:#fff;border-radius:10px;font-family:inherit;font-weight:700;font-size:13.5px;cursor:pointer;color:var(--v1-metin);">Vazgeç</button>' +
          '<button id="v2-sifre-ok" style="flex:1;padding:10px;border:none;background:var(--v1-mavi);color:#fff;border-radius:10px;font-family:inherit;font-weight:700;font-size:13.5px;cursor:pointer;">Gir</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(ov);
    const inp = ov.querySelector('#v2-sifre-inp');
    const hata = ov.querySelector('#v2-sifre-hata');
    const kapat = (dogru) => { ov.remove(); cb(dogru); };
    const dene = () => {
      if (inp.value === 'Faruk.06!') { kapat(true); }
      else { hata.textContent = 'Şifre hatalı.'; inp.select(); }
    };
    ov.querySelector('#v2-sifre-ok').addEventListener('click', dene);
    ov.querySelector('#v2-sifre-iptal').addEventListener('click', () => kapat(false));
    ov.addEventListener('click', (e) => { if (e.target === ov) kapat(false); });
    inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') dene(); if (e.key === 'Escape') kapat(false); });
    setTimeout(() => inp.focus(), 30);
  }

  // ── Plan adını yaz (paket rozeti) ──────────────────────────────────────
  window.v1PaketYaz = (ad) => { const e = document.getElementById('v1-paket-ad'); if (e) e.textContent = ad || 'Ücretsiz'; };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mont);
  else mont();
})();
