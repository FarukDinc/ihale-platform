/**
 * İhaleGlobal — Kenar Menü (İhalePro tarzı dar ikon rayı + flyout alt menü)
 *
 * NEDEN: 24 sayfada kopya, 240px düz sidebar vardı; alt kırılımlar (İhaleler→Aktif/DT,
 * Sonuçlar→Tümü/Bekleyen/İptal/Sonuçlanan, Sözleşmeler→Tümü/Biten/Devam) sayfa ÜSTÜNDE
 * sekme olarak duruyordu. Kullanıcı bunların SOL flyout'ta açılmasını istedi (rakip deseni).
 *
 * TASARIM: 68px dar ray (yalnız ikon) → gruba tıkla → sağında 230px flyout paneli açılır.
 * Alt öğesi olmayan grup doğrudan gider. Ray altında kullanıcı avatarı (mevcut sb-user menüsü).
 *
 * KULLANIM: sayfada <aside class="sidebar"> yerine bu script yüklenir; kendi rayını enjekte eder.
 * data-aktif özniteliğiyle veya URL'den aktif grubu işaretler. Mobil: main.js hamburger'ı
 * bu rayı da açıp kapatabilsin diye .sidebar sınıfı korunur.
 *
 * PİLOT: önce ihaleler.html'de dener; onaylanınca 24 sayfaya yayılır.
 */
(function () {
  // ── İkon seti (temiz çizgi ikonlar; stroke=currentColor → aktif/amber rengini miras alır) ──
  // 20 Tem'e dek emoji kullanılıyordu (◉⊞🚩…); platforma göre değişip amatör duruyordu.
  const _s = (p) => `<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
  const IK = {
    home:    _s('<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>'),
    dosya:   _s('<path d="M14 3H7a1 1 0 00-1 1v16a1 1 0 001 1h10a1 1 0 001-1V8z"/><path d="M14 3v5h4"/><path d="M9 13h6"/><path d="M9 17h4"/>'),
    kupa:    _s('<path d="M7 4h10v4a5 5 0 01-10 0z"/><path d="M7 6H4v1a3 3 0 003 3"/><path d="M17 6h3v1a3 3 0 01-3 3"/><path d="M9 16h6v4H9z"/><path d="M12 13v3"/>'),
    grafik:  _s('<path d="M4 20h16"/><path d="M6 20v-7"/><path d="M12 20V5"/><path d="M18 20v-10"/>'),
    bina:    _s('<path d="M5 21V4a1 1 0 011-1h8a1 1 0 011 1v17"/><path d="M15 9h3a1 1 0 011 1v11"/><path d="M8 7h1M12 7h1M8 11h1M12 11h1M8 15h1M12 15h1"/><path d="M3 21h18"/>'),
    kurum:   _s('<path d="M3 21h18"/><path d="M5 21V10M10 21V10M14 21V10M19 21V10"/><path d="M4 10l8-6 8 6"/>'),
    izgara:  _s('<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>'),
    terazi:  _s('<path d="M12 3v18"/><path d="M7 21h10"/><path d="M5 7h14"/><path d="M8 7l-3 6a3 3 0 006 0z" transform="translate(0,0)"/><path d="M16 7l3 6a3 3 0 01-6 0z" transform="translate(0,0)"/>'),
    kure:    _s('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.7 2.6 2.7 15.4 0 18M12 3c-2.7 2.6-2.7 15.4 0 18"/>'),
    sepet:   _s('<path d="M4 5h2l1.6 10h9L18 8H7"/><circle cx="9" cy="19" r="1.3"/><circle cx="17" cy="19" r="1.3"/>'),
    harita:  _s('<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>'),
    kullanici: _s('<circle cx="12" cy="8" r="4"/><path d="M5 21a7 7 0 0114 0"/>'),
  };

  // ── Menü ağacı (tek kaynak) ────────────────────────────────────────────────
  // alt: [{ad, href}] verilirse flyout açılır; yoksa gruba tıklanınca href'e gidilir.
  const MENU = [
    { id: 'anasayfa', ikon: IK.home, ad: 'Anasayfa', href: 'dashboard' },
    { id: 'ihaleler', ikon: IK.dosya, ad: 'İhaleler', alt: [
        { ad: 'Aktif İhaleler', href: 'ihaleler?sekme=guncel' },
        { ad: 'Geçmiş İhaleler', href: 'ihaleler?sekme=gecmis' },
        { ad: 'Doğrudan Temin', href: 'dogrudan-temin' },
        { ad: 'Detaylı Arama', href: 'ihaleler?sekme=detayli' },
      ] },
    { id: 'sonuclar', ikon: IK.kupa, ad: 'Sonuçlar', alt: [
        { ad: 'Sonuçlanan İhaleler', href: 'ihaleler?sekme=sonuc' },
        // "Sonuç Bekleyenler" = süresi geçmiş ama sonuç yayınlanmamış (durum=kapali, 1,6M).
        // "İptal Edilenler" EKAP'ta ayrı statü olarak GELMİYOR (durum yalnız aktif/kapali/sonuclandi)
        // → veri kaynağı olmadığı için menüye konmadı (ölü link yerine dürüst eksik).
        { ad: 'Sonuç Bekleyenler', href: 'ihaleler?sekme=gecmis&durum=kapali' },
      ] },
    { id: 'analiz', ikon: IK.grafik, ad: 'Analiz', alt: [
        { ad: 'Rekabet Analizi', href: 'rekabet-analizi' },
        { ad: 'Doğrudan Temin Analizi', href: 'dt-analiz' },
      ] },
    { id: 'firmalar', ikon: IK.bina, ad: 'Firmalar', href: 'firma-analiz' },
    { id: 'idareler', ikon: IK.kurum, ad: 'İdareler', href: 'kurum-analiz' },
    { id: 'sektorler', ikon: IK.izgara, ad: 'Sektörler', href: 'sektorler' },
    { id: 'kararlar', ikon: IK.terazi, ad: 'KİK Kararlar', href: 'kik-kararlar' },
    { id: 'uluslararasi', ikon: IK.kure, ad: 'Uluslararası', alt: [
        { ad: 'Uluslararası İhaleler', href: 'uluslararasi' },
        { ad: 'Ticaret Analizi', href: 'ticaret-analiz' },
      ] },
    { id: 'ozel', ikon: IK.sepet, ad: 'e-Satınalma', href: 'ozel-ihaleler' },
    { id: 'harita', ikon: IK.harita, ad: 'Harita', href: 'harita' },
    { id: 'firmam', ikon: IK.kullanici, ad: 'Firmam', alt: [
        { ad: 'İhalelerim', href: 'ihalelerim' },
        { ad: 'Takibim', href: 'takipte' },
        { ad: 'Bildirimler', href: 'bildirimler' },
        { ad: 'Uyumluluk', href: 'uyumluluk' },
        { ad: 'Dökümanlar', href: 'dokumanlar' },
        { ad: 'Profil & Filtreler', href: 'profil' },
        { ad: 'Abonelik', href: 'fiyatlandirma_odeme_bolumu' },
      ] },
  ];

  // Aktif grup: data-kenar-aktif özniteliği (sayfa gövdesinde) veya URL yolundan tahmin.
  const yol = (location.pathname.split('/').pop() || 'dashboard').replace('.html', '');
  const mevcutSekme = new URLSearchParams(location.search).get('sekme') || '';
  const govdeAktif = document.body.getAttribute('data-kenar-aktif');

  // Bir alt öğe aktif mi? Yol EŞLEŞMELİ; aynı sayfada farklı sekmeler varsa sekme de eşleşmeli
  // (yoksa "İhaleler" altında Aktif+Geçmiş+Detaylı hepsi birden aktif görünüyordu).
  function altAktifMi(href) {
    const [p, qs] = href.split('?');
    if (p !== yol) return false;
    const s = new URLSearchParams(qs || '').get('sekme') || '';
    return s === mevcutSekme;
  }
  function grupAktifMi(g) {
    if (govdeAktif) return g.id === govdeAktif;
    if (g.href && g.href.split('?')[0] === yol) return true;
    if (g.alt) return g.alt.some(s => s.href.split('?')[0] === yol);
    return false;
  }

  // ── Stil ───────────────────────────────────────────────────────────────────
  const st = document.createElement('style');
  st.textContent = `
    .kmenu { width:68px; flex-shrink:0; background:var(--navy-mid); border-right:1px solid var(--border);
      display:flex; flex-direction:column; align-items:center; position:sticky; top:0; height:100vh; z-index:60; }
    .kmenu-logo { width:40px; height:40px; margin:14px 0 8px; border-radius:11px; display:flex;
      align-items:center; justify-content:center; }
    .kmenu-logo img { width:40px; height:40px; }
    .kmenu-nav { flex:1; width:100%; overflow-y:auto; overflow-x:hidden; padding:6px 0;
      display:flex; flex-direction:column; align-items:center; gap:2px; }
    .kmenu-nav::-webkit-scrollbar { width:0; }
    .kmenu-item { width:52px; height:50px; border-radius:12px; display:flex; flex-direction:column;
      align-items:center; justify-content:center; gap:2px; cursor:pointer; color:var(--muted);
      font-size:19px; border:none; background:none; transition:background .15s,color .15s; position:relative; }
    .kmenu-item .etk { font-size:8.5px; font-weight:700; letter-spacing:.01em; line-height:1;
      max-width:60px; text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .kmenu-item:hover { background:var(--card-bg); color:var(--white); }
    .kmenu-item.aktif { background:rgba(240,165,0,0.14); color:var(--amber); }
    .kmenu-item.aktif::before { content:''; position:absolute; left:-8px; top:12px; bottom:12px;
      width:3px; border-radius:2px; background:var(--amber); }
    .kmenu-foot { width:100%; padding:10px 0; display:flex; justify-content:center;
      border-top:1px solid var(--border); }
    /* .user-row + .user-avatar → sidebar-user.js baş harfi yazar + çıkış menüsünü bağlar */
    .kmenu-foot .user-row { cursor:pointer; }
    .kmenu-foot .user-avatar { width:38px; height:38px; border-radius:50%; background:var(--amber); color:var(--navy);
      font-size:13px; font-weight:800; display:flex; align-items:center; justify-content:center; cursor:pointer; }

    .kmenu-flyout { position:fixed; left:68px; top:0; height:100vh; width:236px; background:var(--navy-mid);
      border-right:1px solid var(--border); box-shadow:12px 0 30px rgba(0,0,0,.35); z-index:59;
      transform:translateX(-12px); opacity:0; pointer-events:none; transition:transform .16s,opacity .16s;
      padding:18px 12px; display:flex; flex-direction:column; }
    .kmenu-flyout.acik { transform:translateX(0); opacity:1; pointer-events:auto; }
    .kmenu-flyout-baslik { font-size:11px; font-weight:800; letter-spacing:.09em; text-transform:uppercase;
      color:var(--muted); padding:4px 10px 12px; }
    .kmenu-flyout a { display:block; padding:10px 12px; border-radius:8px; color:var(--off-white);
      text-decoration:none; font-size:13.5px; font-weight:600; transition:background .12s,color .12s; }
    .kmenu-flyout a:hover { background:var(--card-bg); color:var(--white); }
    .kmenu-flyout a.aktif { background:rgba(240,165,0,0.12); color:var(--amber); }
    .kmenu-backdrop { position:fixed; inset:0; z-index:58; background:transparent; display:none; }
    .kmenu-backdrop.acik { display:block; }

    /* Eski geniş sidebar'ı gizle — AMA kendi rayımızı (.kmenu) DEĞİL (ikisi de .sidebar sınıflı) */
    .app > .sidebar:not(.kmenu) { display:none; }
    @media (max-width:900px){ .kmenu { display:none; } }  /* mobilde main.js hamburger devreye girer */
  `;
  document.head.appendChild(st);

  // ── Ray ──────────────────────────────────────────────────────────────────────
  const ray = document.createElement('aside');
  ray.className = 'kmenu sidebar';   // .sidebar → main.js hamburger uyumu
  ray.innerHTML = `
    <a class="kmenu-logo" href="/" title="İhaleGlobal"><img src="/favicon.svg" alt="İhaleGlobal"></a>
    <nav class="kmenu-nav" id="kmenu-nav"></nav>
    <div class="kmenu-foot"><div class="user-row" title="Hesap"><div class="user-avatar" id="kmenu-avatar">—</div></div></div>`;
  const nav = ray.querySelector('#kmenu-nav');

  const flyout = document.createElement('div');
  flyout.className = 'kmenu-flyout';
  const backdrop = document.createElement('div');
  backdrop.className = 'kmenu-backdrop';

  let acikGrup = null;
  function flyoutKapat() { flyout.classList.remove('acik'); backdrop.classList.remove('acik'); acikGrup = null; }
  function flyoutAc(g, btn) {
    if (acikGrup === g.id) { flyoutKapat(); return; }
    acikGrup = g.id;
    const bt = btn.getBoundingClientRect();
    flyout.style.top = '0px';
    flyout.innerHTML = `<div class="kmenu-flyout-baslik">${g.ad}</div>` +
      g.alt.map(s => `<a href="${s.href}"${altAktifMi(s.href) ? ' class="aktif"' : ''}>${s.ad}</a>`).join('');
    flyout.classList.add('acik'); backdrop.classList.add('acik');
  }

  MENU.forEach(g => {
    const btn = document.createElement('button');
    btn.className = 'kmenu-item' + (grupAktifMi(g) ? ' aktif' : '');
    btn.innerHTML = `<span>${g.ikon}</span><span class="etk">${g.ad}</span>`;
    btn.title = g.ad;
    btn.addEventListener('click', () => {
      if (g.alt) flyoutAc(g, btn);
      else { flyoutKapat(); location.href = g.href; }
    });
    // Hover ile aç (masaüstü kolaylığı)
    if (g.alt) btn.addEventListener('mouseenter', () => flyoutAc(g, btn));
    nav.appendChild(btn);
  });
  backdrop.addEventListener('click', flyoutKapat);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') flyoutKapat(); });

  // ── DOM'a ekle: eski inline .sidebar'ı KALDIR, rayı .app'in başına koy ──────────
  function mont() {
    const app = document.querySelector('.app');
    if (!app) return;
    const eski = app.querySelector('aside.sidebar:not(.kmenu)');
    if (eski) eski.remove();
    app.insertBefore(ray, app.firstChild);
    document.body.appendChild(flyout);
    document.body.appendChild(backdrop);
    // Avatar menüsü: sidebar-user.js `.sidebar .user-row`'a Profil/Abonelik/Çıkış menüsünü kendisi
    // bağlar ve baş harfi `.user-avatar`'a yazar (ray .sidebar sınıflı → seçici tutar).
    // Fallback: sidebar-user.js menüyü ~1sn içinde bağlamadıysa (o sayfada yüklü değilse) profile götür.
    const row = ray.querySelector('.kmenu-foot .user-row');
    setTimeout(() => {
      if (!row._sbBound && !document.querySelector('.sb-user-menu')) {
        row.addEventListener('click', () => location.href = 'profil');
      }
    }, 1200);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mont);
  else mont();

  // Avatar baş harfini doldur (Supabase oturumundan) — sidebar-user.js zaten .user-name doldururdu;
  // burada bağımsız küçük bir çağrı ile baş harfi yazalım.
  window.kmenuAvatarSet = (harf) => { const a = document.getElementById('kmenu-avatar'); if (a && harf) a.textContent = harf; };
})();
