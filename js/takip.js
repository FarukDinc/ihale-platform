/**
 * İhaleGlobal — Takip Listesi
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
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";

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

/**
 * İhaleGlobal — Doğrudan Temin Takip Listesi (18 Tem 2026)
 *
 * Takip ile AYNI şekil/API, AYRI depolama (localStorage anahtarı + Supabase tablosu
 * farklı) — dt_takipler'ın ilanlar(id) yerine dogrudan_temin_ilanlari.dt_no'ya
 * bağlanması gerektiği için (farklı birincil anahtar tipi/tablosu), mevcut Takip
 * nesnesinin tek-argümanlı imzasını bozmadan PARALEL bir nesne olarak eklendi.
 * Misafir: yalnız localStorage (DB'ye hiç yazmaz, Takip ile aynı davranış).
 *
 * API: TakipDT.toggle(dtNo) / .var(dtNo) / .liste() / .sayi() / await .syncFromDB()
 */
window.TakipDT = (() => {
  const ANAHTAR = 'dt_takip';
  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";

  function _sb() {
    if (!window.supabase) return null;
    return window.supabase.createClient(SB_URL, SB_KEY);
  }
  async function _getUser() {
    const sb = _sb();
    if (!sb) return null;
    try { const { data: { user } } = await sb.auth.getUser(); return user || null; } catch { return null; }
  }
  function liste() {
    try { return JSON.parse(localStorage.getItem(ANAHTAR)) || []; } catch { return []; }
  }
  function _kaydet(arr) {
    localStorage.setItem(ANAHTAR, JSON.stringify([...new Set(arr.map(String))]));
  }
  function varmi(dtNo) { return liste().includes(String(dtNo)); }

  async function _dbEkle(user, dtNo) {
    const sb = _sb();
    if (!sb) return;
    try {
      await sb.from('dt_takipler').upsert(
        { kullanici_id: user.id, dt_no: dtNo },
        { onConflict: 'kullanici_id,dt_no', ignoreDuplicates: true }
      );
    } catch { /* sessizce geç */ }
  }
  async function _dbCikar(user, dtNo) {
    const sb = _sb();
    if (!sb) return;
    try { await sb.from('dt_takipler').delete().eq('kullanici_id', user.id).eq('dt_no', dtNo); } catch { /* sessizce geç */ }
  }

  async function syncFromDB() {
    const user = await _getUser();
    if (!user) return;
    const sb = _sb();
    try {
      const { data } = await sb.from('dt_takipler').select('dt_no').eq('kullanici_id', user.id);
      if (!data) return;
      const dbIds = data.map(r => String(r.dt_no));
      const localIds = liste();
      _kaydet([...new Set([...dbIds, ...localIds])]);
      for (const id of localIds.filter(id => !dbIds.includes(id))) await _dbEkle(user, id);
    } catch { /* sessizce geç */ }
  }

  function toggle(dtNo) {
    dtNo = String(dtNo);
    const arr = liste();
    const idx = arr.indexOf(dtNo);
    let sonuc;
    if (idx >= 0) {
      arr.splice(idx, 1); _kaydet(arr); sonuc = false;
      _getUser().then(user => { if (user) _dbCikar(user, dtNo); });
    } else {
      arr.push(dtNo); _kaydet(arr); sonuc = true;
      _getUser().then(user => { if (user) _dbEkle(user, dtNo); });
    }
    return sonuc;
  }

  return { liste, var: varmi, toggle, sayi: () => liste().length, syncFromDB };
})();
