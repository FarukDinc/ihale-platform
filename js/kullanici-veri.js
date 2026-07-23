/**
 * İhaleGlobal — Kayıtlı Aramalar + Okundu Takibi senkronu (rakip yol haritası #5, #6)
 *
 * NEDEN: her ikisi de yalnızca localStorage'daydı → cihaz değişince / tarayıcı
 * temizlenince kayboluyordu, telefon ile masaüstü birbirini görmüyordu.
 *
 * MİMARİ (js/takip.js ile birebir aynı, kasıtlı): localStorage BİRİNCİL kaynak
 * (anlık + senkron + misafirde de çalışır); giriş yapılmışsa Supabase arka planda
 * senkronlanır. Böylece mevcut senkron çağrı noktaları (Okundu.isle, KayitliArama.ekle…)
 * HİÇ DEĞİŞMEDEN cihazlar arası senkron kazanır.
 *
 * API:
 *   KullaniciVeri.aramaEkle(kayit)       // {id, ad, params, tarih}
 *   KullaniciVeri.aramaSil(yerelId)
 *   KullaniciVeri.okunduEkle(ilanId)
 *   KullaniciVeri.okunduSil(ilanId)
 *   KullaniciVeri.okunduTemizle()
 *   await KullaniciVeri.syncFromDB()     // DB ↔ localStorage birleştirme
 */
window.KullaniciVeri = (() => {
  const ARAMA_ANAHTAR  = 'ihale_kayitli_aramalar_v1';
  const OKUNDU_ANAHTAR = 'ihale_okundu_v1';

  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";

  let _istemci = null;
  function _sb() {
    if (!window.supabase) return null;
    if (!_istemci) _istemci = window.supabase.createClient(SB_URL, SB_KEY);
    return _istemci;
  }

  async function _getUser() {
    const sb = _sb();
    if (!sb) return null;
    try {
      const { data: { user } } = await sb.auth.getUser();
      return user || null;
    } catch { return null; }
  }

  const _oku = (k, varsayilan) => {
    try { return JSON.parse(localStorage.getItem(k)) || varsayilan; } catch { return varsayilan; }
  };
  const _yaz = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) {} };

  // ── Kayıtlı aramalar ──────────────────────────────────────
  function aramaEkle(kayit) {
    _getUser().then(user => {
      if (!user) return;
      _sb().from('kayitli_aramalar').upsert({
        user_id: user.id, yerel_id: kayit.id, ad: kayit.ad, params: kayit.params || {},
      }, { onConflict: 'user_id,yerel_id' }).then(() => {}, () => {});
    });
  }

  function aramaSil(yerelId) {
    _getUser().then(user => {
      if (!user) return;
      _sb().from('kayitli_aramalar').delete()
        .eq('user_id', user.id).eq('yerel_id', yerelId).then(() => {}, () => {});
    });
  }

  // ── Okundu ────────────────────────────────────────────────
  // UUID süzgeci: okundu listesine dış kaynak/DT anahtarı düşerse DB'de uuid kolonu
  // 22P02 verir ve sessizce senkron bozulur.
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  function okunduEkle(ilanId) {
    if (!UUID_RE.test(String(ilanId))) return;
    _getUser().then(user => {
      if (!user) return;
      _sb().from('ilan_okundu').upsert(
        { user_id: user.id, ilan_id: String(ilanId) },
        { onConflict: 'user_id,ilan_id', ignoreDuplicates: true }
      ).then(() => {}, () => {});
    });
  }

  function okunduSil(ilanId) {
    _getUser().then(user => {
      if (!user) return;
      _sb().from('ilan_okundu').delete()
        .eq('user_id', user.id).eq('ilan_id', String(ilanId)).then(() => {}, () => {});
    });
  }

  function okunduTemizle() {
    _getUser().then(user => {
      if (!user) return;
      _sb().from('ilan_okundu').delete().eq('user_id', user.id).then(() => {}, () => {});
    });
  }

  // ── DB → localStorage birleştirme (sayfa açılışında) ──────
  async function syncFromDB() {
    const user = await _getUser();
    if (!user) return;
    const sb = _sb();

    // Kayıtlı aramalar
    try {
      const { data } = await sb.from('kayitli_aramalar')
        .select('yerel_id, ad, params, olusturulma')
        .eq('user_id', user.id).order('olusturulma', { ascending: false });
      if (data) {
        const yerel = _oku(ARAMA_ANAHTAR, []);
        const dbIdler = new Set(data.map(r => Number(r.yerel_id)));
        const birlesik = [
          ...data.map(r => ({ id: Number(r.yerel_id), ad: r.ad, params: r.params || {}, tarih: r.olusturulma })),
          ...yerel.filter(y => !dbIdler.has(Number(y.id))),
        ];
        _yaz(ARAMA_ANAHTAR, birlesik);
        // Yalnız yerelde olanları DB'ye it (çevrimdışı/giriş öncesi eklenenler)
        yerel.filter(y => !dbIdler.has(Number(y.id))).forEach(aramaEkle);
      }
    } catch (_) {}

    // Okundu
    try {
      const { data } = await sb.from('ilan_okundu')
        .select('ilan_id').eq('user_id', user.id)
        .order('okundu_tarih', { ascending: true }).limit(2000);
      if (data) {
        const yerel = _oku(OKUNDU_ANAHTAR, []).map(String);
        const dbIdler = data.map(r => String(r.ilan_id));
        // Sıra korunur: DB (eskiden yeniye) + yalnız-yerel olanlar sona
        const sadeceYerel = yerel.filter(id => !dbIdler.includes(id));
        _yaz(OKUNDU_ANAHTAR, [...new Set([...dbIdler, ...sadeceYerel])]);
        sadeceYerel.forEach(okunduEkle);
      }
    } catch (_) {}
  }

  return { aramaEkle, aramaSil, okunduEkle, okunduSil, okunduTemizle, syncFromDB };
})();
