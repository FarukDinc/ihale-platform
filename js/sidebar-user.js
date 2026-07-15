/* Sidebar kullanıcı bilgilerini Supabase auth'tan doldurur.
   Supabase JS CDN'den yüklü olmalı (main script'ten önce). */
(async () => {
  const SUPABASE_URL = "https://ihaleglobal.com";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs";

  // Sidebar alt-köşedeki kullanıcı bloğu tıklanınca profil sayfasına git
  // (giriş durumundan bağımsız — Supabase yüklenmese bile çalışmalı).
  document.querySelectorAll('.sidebar-footer .user-row, .sidebar .user-row').forEach(el => {
    if (el.dataset.profilLink) return; // iki kez bağlama
    el.dataset.profilLink = '1';
    el.style.cursor = 'pointer';
    el.setAttribute('role', 'link');
    el.setAttribute('tabindex', '0');
    el.title = 'Profil ve ayarlar';
    const git = () => { window.location.href = 'profil'; };
    el.addEventListener('click', git);
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); git(); }
    });
  });

  if (!window.supabase) return;
  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

  try {
    const { data: { user } } = await sb.auth.getUser();
    if (!user) return;

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

    // Pro kullanıcıda topbar "Pro'ya Geç" CTA'sını "Pro Plan" rozetine çevir (yükseltme değil, durum göster)
    if (proMu) {
      document.querySelectorAll('.topbar-actions a[href="fiyatlandirma_odeme_bolumu"]').forEach(btn => {
        btn.textContent = '⭐ Pro Plan';
        btn.classList.remove('btn-primary');
        btn.title = 'Pro plan aktif — abonelik detayları';
        btn.style.cssText = 'padding:7px 14px!important;font-size:13px!important;font-weight:700!important;background:rgba(240,165,0,0.12)!important;border:1px solid var(--amber)!important;color:var(--amber)!important;border-radius:8px!important;text-decoration:none!important;transition:none!important;';
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
    // Sessizce geç — giriş yapılmamış olabilir
  }
})();
