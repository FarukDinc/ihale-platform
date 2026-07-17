/* İhaleGlobal — Sidebar'daki "Bildirimler" rozetini gerçek okunmamış sayısıyla günceller.
   Önceden her sayfada sabit "4" yazılıydı — bu script onu canlı sayıyla değiştirir.
   bildirimler.html kendi okunmamış sayısını zaten kendi mantığıyla hesaplıyor, bu script
   ona dokunmaz (id="sb-okunmamis" varsa atlar). */
(function () {
  const SUPABASE_URL = "https://ihaleglobal.com";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";

  if (!window.supabase) return;
  if (document.getElementById('sb-okunmamis')) return; // bildirimler.html kendi mantığını yürütüyor

  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

  (async () => {
    try {
      const { data: { user } } = await sb.auth.getUser();
      if (!user) return;

      const { count } = await sb.from('bildirimler')
        .select('id', { count: 'exact', head: true })
        .eq('kullanici_id', user.id)
        .eq('okundu', false);

      const link = document.querySelector('a[href="bildirimler"]');
      const badge = link ? link.querySelector('.nav-badge') : null;
      if (!badge) return;

      if (!count) {
        badge.style.display = 'none';
      } else {
        badge.textContent = count > 99 ? '99+' : String(count);
        badge.style.display = '';
      }
    } catch (e) {
      // Sessizce geç — sidebar'daki eski statik sayı kalır
    }
  })();
})();
