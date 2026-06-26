/* Sidebar kullanıcı bilgilerini Supabase auth'tan doldurur.
   Supabase JS CDN'den yüklü olmalı (main script'ten önce). */
(async () => {
  const SUPABASE_URL = "https://lpgelwfoarhouollhwur.supabase.co";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwZ2Vsd2ZvYXJob3VvbGxod3VyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIyMzI4MjAsImV4cCI6MjA5NzgwODgyMH0.GqTZkeoOAomuur4JSyW2pTR-8Zzg8OTv394JtP7DoXM";

  if (!window.supabase) return;
  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

  try {
    const { data: { user } } = await sb.auth.getUser();
    if (!user) return;

    // E-postadan baş harfler (fallback)
    const email = user.email || '';
    const initials = email.substring(0, 2).toUpperCase();

    // Profil tablosundan firma adı ve plan
    const { data: profil } = await sb.from('profil')
      .select('firma_adi, plan')
      .eq('user_id', user.id)
      .single();

    const gosterilenAd = profil?.firma_adi || email.split('@')[0];
    const plan = profil?.plan || 'Ücretsiz Plan';

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
