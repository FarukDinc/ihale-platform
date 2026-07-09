/**
 * İhalePlatform — Takip Listesi
 *
 * localStorage birincil kaynak (anlık, senkron).
 * Kullanıcı giriş yaptıysa Supabase `takip` tablosuyla senkronize olur:
 *   - toggle() → localStorage'ı anında günceller + Supabase'e async yazar
 *   - Sayfa yüklendiğinde syncFromDB() çağrılırsa DB → localStorage birleşimi yapılır
 *
 * API (değişmedi — geriye dönük uyumlu):
 *   Takip.toggle(id)         → bool (yeni durum)
 *   Takip.var(id)            → bool
 *   Takip.liste()            → string[]
 *   Takip.sayi()             → number
 *   await Takip.syncFromDB() → void (Supabase → localStorage merge)
 */
window.Takip = (() => {
  const ANAHTAR = 'ihale_takip';

  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs";

  function _sb() {
    if (!window.supabase) return null;
    return window.supabase.createClient(SB_URL, SB_KEY);
  }

  async function _getUser() {
    const sb = _sb();
    if (!sb) return null;
    try {
      const { data: { user } } = await sb.auth.getUser();
      return user || null;
    } catch { return null; }
  }

  // ── localStorage ─────────────────────────────────────────

  function liste() {
    try { return JSON.parse(localStorage.getItem(ANAHTAR)) || []; }
    catch { return []; }
  }

  function _kaydet(arr) {
    localStorage.setItem(ANAHTAR, JSON.stringify([...new Set(arr.map(String))]));
  }

  function varmi(id) {
    return liste().includes(String(id));
  }

  // ── Supabase yardımcıları ─────────────────────────────────

  async function _dbEkle(user, ilanId) {
    const sb = _sb();
    if (!sb) return;
    try {
      await sb.from('takipler').upsert(
        { kullanici_id: user.id, ilan_id: ilanId },
        { onConflict: 'kullanici_id,ilan_id', ignoreDuplicates: true }
      );
    } catch { /* sessizce geç */ }
  }

  async function _dbCikar(user, ilanId) {
    const sb = _sb();
    if (!sb) return;
    try {
      await sb.from('takipler')
        .delete()
        .eq('kullanici_id', user.id)
        .eq('ilan_id', ilanId);
    } catch { /* sessizce geç */ }
  }

  // ── Sync: DB → localStorage (sayfa yüklenince çağrılır) ──

  async function syncFromDB() {
    const user = await _getUser();
    if (!user) return;
    const sb = _sb();
    try {
      const { data } = await sb.from('takipler')
        .select('ilan_id')
        .eq('kullanici_id', user.id);
      if (!data) return;
      const dbIds = data.map(r => String(r.ilan_id));
      const localIds = liste();
      // Birleştir: DB + local (local'de olup DB'de olmayan → DB'ye yaz)
      const yeniIds = [...new Set([...dbIds, ...localIds])];
      _kaydet(yeniIds);
      // Local'de olup DB'de olmayanları DB'ye ekle (offline eklemeler)
      const sadecaLocal = localIds.filter(id => !dbIds.includes(id));
      for (const id of sadecaLocal) {
        await _dbEkle(user, id);
      }
    } catch { /* sessizce geç */ }
  }

  // ── Genel toggle ─────────────────────────────────────────

  function toggle(id) {
    id = String(id);
    const arr = liste();
    const idx = arr.indexOf(id);
    let sonuc;
    if (idx >= 0) {
      arr.splice(idx, 1);
      _kaydet(arr);
      sonuc = false;
      _getUser().then(user => { if (user) _dbCikar(user, id); });
    } else {
      arr.push(id);
      _kaydet(arr);
      sonuc = true;
      _getUser().then(user => { if (user) _dbEkle(user, id); });
    }
    return sonuc;
  }

  return { liste, var: varmi, toggle, sayi: () => liste().length, syncFromDB };
})();
