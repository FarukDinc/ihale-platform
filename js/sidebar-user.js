/* Sidebar kullanıcı bilgilerini Supabase auth'tan doldurur.
   Supabase JS CDN'den yüklü olmalı (main script'ten önce). */
(async () => {
  // www→apex kanonik yönlendirme: localStorage origin-bazlı olduğundan www'da
  // açılan oturum apex'te görünmez (kullanıcı "girişliyim ama *** görüyorum" sanır).
  // Tek origin'e sabitle. (Kalıcı çözüm: CF/nginx 301 — YAPILACAKLAR.)
  if (location.hostname.startsWith('www.')) {
    location.replace(location.protocol + '//' + location.hostname.slice(4)
      + location.pathname + location.search + location.hash);
    return;
  }

  const SUPABASE_URL = "https://ihaleglobal.com";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";

  // ── Sidebar hesap menüsü (Profil & Ayarlar / Abonelik / Çıkış Yap) ──────────────
  // ESKİDEN: kullanıcı bloğu tıklanınca doğrudan profil sayfasına gidiyordu ve hiçbir yerde
  // ÇIKIŞ YAP seçeneği YOKTU — kullanıcı oturumunu kapatamıyordu (17 Tem saha bulgusu).
  // ARTIK: blok bir menü açar. Menü body'ye FIXED konumla eklenir; sidebar'ın overflow-y:auto'su
  // absolute bir popover'ı kırpardı.
  let sbClient = null;                 // auth client (aşağıda kurulunca atanır) — çıkış için gerekli
  const menuler = [];

  if (!document.getElementById('sb-user-menu-stil')) {
    const st = document.createElement('style');
    st.id = 'sb-user-menu-stil';
    st.textContent = `
      .sb-user-menu { position:fixed; z-index:9999; min-width:210px; background:#0f1a2e;
        border:1px solid rgba(255,255,255,.13); border-radius:10px; padding:6px;
        box-shadow:0 12px 34px rgba(0,0,0,.6); display:none; }
      .sb-user-menu.acik { display:block; }
      .sb-user-menu button { display:flex; align-items:center; gap:9px; width:100%; text-align:left;
        background:none; border:none; color:#e2e8f0; font-family:inherit; font-size:13px;
        font-weight:600; padding:9px 11px; border-radius:7px; cursor:pointer; }
      .sb-user-menu button:hover { background:rgba(240,165,0,.12); color:#f0a500; }
      .sb-user-menu button.cikis { color:#f87171; }
      .sb-user-menu button.cikis:hover { background:rgba(239,68,68,.14); color:#f87171; }
      .sb-user-menu .ayrac { height:1px; background:rgba(255,255,255,.08); margin:4px 6px; }
      .sb-user-ok { margin-left:auto; color:#8a96a8; font-size:15px; line-height:1; }
    `;
    document.head.appendChild(st);
  }

  // ⚠️ .user-row SONRADAN gelebilir: kmenu'lü sayfalarda (benim-sayfam, v2 iç sayfalar)
  // kenar-menu.js rayı DOMContentLoaded'da monte eder; bu script ondan ÖNCE çalışırsa
  // querySelectorAll boş döner ve profil menüsü HİÇ kurulmazdı (menü yerine profil'e
  // zıplayan fallback devreye girerdi). Bu yüzden bağlama fonksiyona alınıp tekrar denenir.
  function satirlariBagla() {
  document.querySelectorAll('.sidebar-footer .user-row, .sidebar .user-row').forEach(el => {
    if (el.dataset.userMenu) return;   // iki kez bağlama
    el.dataset.userMenu = '1';
    el.style.cursor = 'pointer';
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-haspopup', 'menu');
    el.title = 'Hesap menüsü';
    if (!el.querySelector('.sb-user-ok')) {
      const ok = document.createElement('span');
      ok.className = 'sb-user-ok';
      ok.textContent = '⋮';
      el.appendChild(ok);
    }

    const menu = document.createElement('div');
    menu.className = 'sb-user-menu';
    menu.setAttribute('role', 'menu');
    document.body.appendChild(menu);
    menuler.push(menu);

    const ac = (e) => {
      if (e) e.stopPropagation();
      const zatenAcik = menu.classList.contains('acik');
      menuler.forEach(m => m.classList.remove('acik'));
      if (zatenAcik) return;
      const r = el.getBoundingClientRect();
      // Sidebar gizliyken (mobilde hamburger kapalı → display:none) rect 0×0 gelir ve menü
      // ekran dışına konumlanır. Görünmüyorsa hiç açma.
      if (!r.width && !r.height) return;
      menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 218)) + 'px';
      menu.style.width = Math.max(210, r.width) + 'px';
      menu.classList.add('acik');
      // Varsayılan bloğun ÜSTÜnde; yukarı sığmıyorsa (kısa ekran) ALTINA çevir — her hâlükârda
      // ekran içinde kalsın.
      const h = menu.offsetHeight || 120;
      if (r.top - h - 8 >= 0) {
        menu.style.top = '';
        menu.style.bottom = (window.innerHeight - r.top + 8) + 'px';
      } else {
        menu.style.bottom = '';
        menu.style.top = Math.max(8, Math.min(r.bottom + 8, window.innerHeight - h - 8)) + 'px';
      }
    };
    el.addEventListener('click', ac);
    el._sbBound = true;   // kenar-menu.js fallback'i bunu kontrol eder
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); ac(e); }
      if (e.key === 'Escape') menuler.forEach(m => m.classList.remove('acik'));
    });
  });
  }
  // Bağla + (yeni satır geldiyse) en son bilinen oturum durumuyla menüyü doldur.
  // ⚠️ menuDoldur bu noktada henüz TANIMLI DEĞİL (const, aşağıda) → ilk çağrıda ÇAĞIRMA (TDZ).
  //    DOMContentLoaded ve setTimeout'lar script gövdesi bittikten sonra çalışır, orada güvenli.
  const baglaVeDoldur = () => {
    const once = menuler.length;
    satirlariBagla();
    if (menuler.length > once) menuDoldur(sonMisafir);
  };
  satirlariBagla();                                             // hemen (satır HTML'de gömülüyse)
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', baglaVeDoldur);
  [150, 400, 900].forEach(ms => setTimeout(baglaVeDoldur, ms)); // geç monte edilen kmenu rayı için

  document.addEventListener('click', () => menuler.forEach(m => m.classList.remove('acik')));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') menuler.forEach(m => m.classList.remove('acik'));
  });

  // Tema satiri (Gunduz/Gece) — eski sol-alt sabit buton kmenu avatarinin ustune biniyordu (26 Tem);
  // tema artik BU MENUDEN secilir. theme.js global window.temaDegistir/temaSuAnki sunar.
  const temaEtiket = () => (window.temaSuAnki && window.temaSuAnki() === 'light')
    ? '🌙 <span>Gece Modu</span>' : '☀️ <span>Gündüz Modu</span>';

  // SÜRÜM GEÇİŞİ (v2 → v1). v1 tarafındaki karşılığı js/v1-kabuk.js profil menüsünde.
  const surumSatiri =
    '<div style="padding:8px 11px 3px;font-size:10.5px;font-weight:800;letter-spacing:.08em;' +
    'text-transform:uppercase;color:#8a96a8;">Sürüm</div>' +
    '<button type="button" data-surum="v1">🔵 <span>v1 — Kurumsal</span></button>' +
    '<button type="button" data-surum="v2" style="color:#f0a500;">🟡 <span>v2 — İhaleGlobal (aktif)</span></button>' +
    '<div class="ayrac"></div>';

  let sonMisafir = true;   // en son bilinen oturum durumu — geç bağlanan satırlar da dolsun
  const menuDoldur = (misafir) => {
    sonMisafir = misafir;
    const temaSatiri = `<button type="button" data-tema="1">${temaEtiket()}</button>`;
    const html = misafir
      ? `<button type="button" data-git="login">🔑 <span>Giriş Yap</span></button>
         <button type="button" data-git="login">✨ <span>Ücretsiz Kayıt Ol</span></button>
         <div class="ayrac"></div>
         ${temaSatiri}`
      : `${surumSatiri}
         <button type="button" data-git="profil">⚙️ <span>Profil &amp; Ayarlar</span></button>
         <button type="button" data-git="fiyatlandirma_odeme_bolumu">💳 <span>Abonelik</span></button>
         ${temaSatiri}
         <div class="ayrac"></div>
         <button type="button" class="cikis" data-cikis="1">🚪 <span>Çıkış Yap</span></button>`;
    menuler.forEach(m => {
      m.innerHTML = html;
      m.querySelectorAll('[data-surum]').forEach(b => b.addEventListener('click', (ev) => {
        ev.stopPropagation();
        const s = b.dataset.surum;
        try { localStorage.setItem('ihale_surum', s); } catch (_) {}
        if (s === 'v1') window.location.href = 'v1-benim-sayfam';
        else m.classList.remove('acik');
      }));
      m.querySelectorAll('[data-tema]').forEach(b => b.addEventListener('click', (ev) => {
        ev.stopPropagation();
        if (window.temaDegistir) window.temaDegistir();
        b.innerHTML = temaEtiket();   // etiket guncellenir, menu acik kalir
      }));
      m.querySelectorAll('[data-git]').forEach(b => b.addEventListener('click', (ev) => {
        ev.stopPropagation();
        window.location.href = b.dataset.git;
      }));
      m.querySelectorAll('[data-cikis]').forEach(b => b.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        b.innerHTML = '⏳ <span>Çıkış yapılıyor…</span>';
        try { if (sbClient) await sbClient.auth.signOut(); } catch (_) { /* yine de temizle */ }
        // Legacy token'ı DA temizle: kalırsa login sayfası kendini "girişli" sanıp dashboard'a
        // geri atar (iki-auth-sistemi bounce bug'ı, 17 Tem).
        try { localStorage.removeItem('ihale_token'); } catch (_) {}
        window.location.href = '/';
      }));
    });
  };
  menuDoldur(true);   // auth çözülene kadar güvenli varsayılan (misafir)

  // Misafir görünümü: oturum yoksa/düşmüşse sidebar BUNU söylemeli — eski statik
  // "Faruk D. / Ücretsiz Plan" yer tutucusu, oturumu düşen kullanıcıya "girişliyim
  // ama veriler ***" yanılgısı yaşatıyordu (maskeleme anon'a doğru çalışırken).
  const misafirGoster = () => {
    menuDoldur(true);   // menüde: Giriş Yap / Ücretsiz Kayıt Ol
    document.querySelectorAll('.sidebar .user-row, .sidebar-footer .user-row').forEach(el => {
      el.title = 'Giriş yapın';
    });
    document.querySelectorAll('.sidebar .user-avatar, .sidebar-footer .user-avatar, #avatar-text').forEach(el => {
      el.textContent = '👤';
    });
    document.querySelectorAll('.sidebar .user-name, .sidebar-footer .user-name, #sidebar-firma, #sidebar-isim').forEach(el => {
      el.textContent = 'Misafir';
    });
    document.querySelectorAll('.sidebar .user-plan, .sidebar-footer .user-plan').forEach(el => {
      el.textContent = 'Giriş yapın →';
    });
  };

  if (!window.supabase) return;
  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  sbClient = sb;   // menüdeki "Çıkış Yap" bu client ile signOut eder

  try {
    const { data: { user } } = await sb.auth.getUser();
    if (!user) { misafirGoster(); return; }
    menuDoldur(false);   // menüde: Profil & Ayarlar / Abonelik / Çıkış Yap

    // E-postadan baş harfler (fallback)
    const email = user.email || '';
    const initials = email.substring(0, 2).toUpperCase();

    // Firma adı — önce profil (tercih tablosu), yoksa kullanici_profiller (firma detay tablosu)
    const [{ data: profil }, { data: kProfil }, { data: kredi }] = await Promise.all([
      sb.from('profil').select('firma_adi').eq('user_id', user.id).maybeSingle(),
      sb.from('kullanici_profiller').select('firma_adi').eq('id', user.id).maybeSingle(),
      // Plan — kullanici_krediler tablosundan (payment.py buraya yazar)
      sb.from('kullanici_krediler').select('plan, plan_bitis').eq('kullanici_id', user.id).maybeSingle()
    ]);
    // DB'deki gerçek geçerli değerler (planlar.kod FK): 'standart' | 'kurumsal' — bkz. js/plan.js
    const PRO = ['standart', 'kurumsal', 'pro', 'Pro', 'PRO', 'premium', 'enterprise'];
    let planKodu = kredi?.plan;
    if (planKodu && kredi?.plan_bitis && new Date(kredi.plan_bitis) < new Date()) planKodu = null;

    const gosterilenAd = profil?.firma_adi || kProfil?.firma_adi || email.split('@')[0];
    const proMu = PRO.includes(planKodu);
    const plan = proMu ? 'Pro Plan' : 'Ücretsiz Plan';

    // Ödeme yapmış (Pro/Kurumsal) kullanıcıda sağ-üstteki "Pro'ya Geç" CTA'sını GİZLE — yükseltme
    // teklifi göstermenin anlamı yok. Yalnız TOPBAR'daki CTA hedeflenir (içerik-içi upsell'lere,
    // fiyatlandırma sayfasına dokunulmaz). Selektör hem doğrudan .topbar hem .topbar-actions'ı kapsar.
    if (proMu) {
      document.querySelectorAll('.topbar a[href="fiyatlandirma_odeme_bolumu"], .topbar-actions a[href="fiyatlandirma_odeme_bolumu"]').forEach(btn => {
        btn.style.display = 'none';
      });
    }

    // Tüm sidebar avatar + name elementlerini güncelle
    document.querySelectorAll('.sidebar .user-avatar, .sidebar-footer .user-avatar, #avatar-text').forEach(el => {
      el.textContent = initials;
    });
    document.querySelectorAll('.sidebar .user-name, .sidebar-footer .user-name, #sidebar-firma, #sidebar-isim').forEach(el => {
      el.textContent = gosterilenAd;
    });
    document.querySelectorAll('.sidebar .user-plan, .sidebar-footer .user-plan').forEach(el => {
      el.textContent = plan;
    });
  } catch (e) {
    // getUser ağ hatası vb. — yerelde oturum da yoksa misafir göster,
    // varsa statik yer tutucuya dokunma (geçici ağ sorunu olabilir).
    try {
      const { data } = await sb.auth.getSession();
      if (!data || !data.session) misafirGoster();
    } catch (_) { misafirGoster(); }
  }
})();
