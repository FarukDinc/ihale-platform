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

  // Sidebar alt-köşedeki kullanıcı bloğu tıklanınca profil sayfasına git
  // (giriş yoksa login'e — hedef auth sonucuna göre aşağıda güncellenir).
  let tiklamaHedefi = 'profil';
  document.querySelectorAll('.sidebar-footer .user-row, .sidebar .user-row').forEach(el => {
    if (el.dataset.profilLink) return; // iki kez bağlama
    el.dataset.profilLink = '1';
    el.style.cursor = 'pointer';
    el.setAttribute('role', 'link');
    el.setAttribute('tabindex', '0');
    el.title = 'Profil ve ayarlar';
    const git = () => { window.location.href = tiklamaHedefi; };
    el.addEventListener('click', git);
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); git(); }
    });
  });

  // Misafir görünümü: oturum yoksa/düşmüşse sidebar BUNU söylemeli — eski statik
  // "Faruk D. / Ücretsiz Plan" yer tutucusu, oturumu düşen kullanıcıya "girişliyim
  // ama veriler ***" yanılgısı yaşatıyordu (maskeleme anon'a doğru çalışırken).
  const misafirGoster = () => {
    tiklamaHedefi = 'login';
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

  try {
    const { data: { user } } = await sb.auth.getUser();
    if (!user) { misafirGoster(); return; }

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
