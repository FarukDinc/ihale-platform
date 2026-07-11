/* Sidebar kullanıcı bilgilerini Supabase auth'tan doldurur.
   Supabase JS CDN'den yüklü olmalı (main script'ten önce). */
(async () => {
  const SUPABASE_URL = "https://ihaleglobal.com";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs";

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
    const plan = PRO.includes(planKodu) ? 'Pro Plan' : 'Ücretsiz Plan';

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
