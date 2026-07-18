/* ============================================================================
 * harita.js — Türkiye il bazlı choropleth ısı haritası (Leaflet, yeniden kullanılabilir)
 * ----------------------------------------------------------------------------
 * Kullanım (sayfada):
 *   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
 *   <div id="turkiye-harita"></div>
 *   <div id="harita-yukleniyor">🗺️ Harita yükleniyor…</div>   (opsiyonel)
 *   <div id="harita-legend"></div>                              (opsiyonel)
 *   <div class="harita-mod-btn" data-mod="toplam" onclick="haritaModSec('toplam')">Tümü</div> (opsiyonel — mod seçici)
 *   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
 *   <script src="js/harita.js"></script>
 * Otomatik lazy-init (IntersectionObserver). Veri (ihale+DT sayımı) TEK SEFER çekilir;
 * 3 MOD arasında geçiş (window.haritaModSec(mod) — 'toplam'|'ihale'|'dt') sadece mevcut
 * Leaflet katmanını yeniden STİLLER/BAĞLAR, yeniden fetch YAPMAZ (18 Tem):
 *   - 'toplam' (öntanım): renk=İhale+DT toplamı; hover'da ikisi AYRI (dünya ticaret
 *     haritasındaki ihracat/ithalat ayrımıyla aynı fikir); tıklayınca popup açılır —
 *     kullanıcı "İhaleler" ya da "Doğrudan Temin"den birini seçer.
 *   - 'ihale' / 'dt': kullanıcı üstteki düğmeyle önceden niyetini belirtmiştir → renk
 *     yalnız o metriğe göre, tıklayınca DOĞRUDAN o sayfaya gider (popup yok, tek adım).
 * Popup/mod-düğmesi görseli için sayfanın kendi <style>'ında .il-popup* ve .harita-mod-btn
 * sınıfları tanımlı olmalı (bkz. dashboard.html — .il-tooltip ile aynı "sayfa CSS sağlar" kuralı).
 * NOT: index.html'de aynı mantığın satır-içi bir kopyası var; ileride index de bu
 *      modüle geçirilip tekilleştirilebilir (teknik borç — DT katmanı/mod seçici ORAYA henüz taşınmadı).
 * ========================================================================== */
(function () {
  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";
  const GEOJSON_URL = 'data/turkey-provinces.geojson';
  const RENKLER = ['#243b5e', '#7a5c1e', '#b07d08', '#e09600', '#f0a500', '#ef4444'];

  // İl bazlı sayım — önce tek istekli RPC (hızlı), yoksa sayfalı fallback. rpcAdi/tabloAdi
  // parametreli: aynı fonksiyon hem ilanlar/il_sayim hem dogrudan_temin_ilanlari/dt_il_sayim için.
  async function ilSayimGetir(sb, rpcAdi, tabloAdi, sayfaUst) {
    try {
      const { data, error } = await sb.rpc(rpcAdi);
      if (!error && Array.isArray(data) && data.length) {
        const sayim = {};
        data.forEach(r => { if (r.il) sayim[r.il] = Number(r.adet) || 0; });
        return sayim;
      }
    } catch (_) { /* RPC yoksa fallback */ }
    const istekler = [];
    for (let off = 0; off < sayfaUst; off += 1000) {
      istekler.push(sb.from(tabloAdi).select('il').not('il', 'is', null).range(off, off + 999));
    }
    const sonuc = await Promise.all(istekler);
    const sayim = {};
    for (const { data } of sonuc) (data || []).forEach(r => {
      if (r.il) sayim[r.il] = (sayim[r.il] || 0) + 1;
    });
    return sayim;
  }

  // GeoJSON Title-case ad → DB BÜYÜK HARF il anahtarı (örn. Afyon → AFYONKARAHİSAR).
  // toplamSayim (ihale+DT anahtar birleşimi) ile eşleştirilir — en geniş anahtar kümesi
  // budur, tüm modlarda AYNI k kullanılır (mod değişince eşleşme kaymasın diye).
  function ilAnahtar(ad, sayim) {
    const U = ad.toLocaleUpperCase('tr');
    if (sayim[U] != null) return U;
    for (const k of Object.keys(sayim)) if (k.startsWith(U) || U.startsWith(k)) return k;
    return U;
  }

  // Skewed dağılım için quantile bazlı eşikler (5 eşik → 6 kademe)
  function esikler(sayim) {
    const v = Object.values(sayim).filter(x => x > 0).sort((a, b) => a - b);
    if (!v.length) return [1, 2, 3, 4, 5];
    const q = p => v[Math.min(v.length - 1, Math.floor(v.length * p))];
    return [q(0.50), q(0.70), q(0.85), q(0.93), q(0.98)];
  }
  function renkSec(n, esik) {
    if (!n) return '#16233d';
    for (let i = 0; i < esik.length; i++) if (n <= esik[i]) return RENKLER[i];
    return RENKLER[RENKLER.length - 1];
  }

  const MOD_BASLIK = {
    toplam: 'Renkler ildeki İhale + Doğrudan Temin TOPLAMINI gösterir:',
    ihale:  'Renkler ildeki güncel İHALE sayısını gösterir:',
    dt:     'Renkler ildeki DOĞRUDAN TEMİN sayısını gösterir:',
  };
  const MOD_ALT = {
    toplam: 'Renk = İhale+Doğrudan Temin toplamı · bir ile tıklayın → seçim yapın',
    ihale:  'Renk = güncel ihale sayısı · bir ile tıklayın → o ilin ihaleleri',
    dt:     'Renk = doğrudan temin sayısı · bir ile tıklayın → o ilin doğrudan temin ilanları',
  };

  function legendCiz(esik, mod) {
    const lg = document.getElementById('harita-legend');
    if (!lg) return;
    const fmt = n => n >= 1000 ? (n / 1000).toFixed(1).replace('.0', '') + 'b' : String(n);
    // renkSec ile birebir eşleşir: 0 → #16233d, [1,e0] → RENKLER[0], (e0,e1] → RENKLER[1], … , e4+ → RENKLER[5]
    const kutular = [['#16233d', 'Kayıt yok']];
    for (let i = 0; i < RENKLER.length; i++) {
      const alt = i === 0 ? 1 : esik[i - 1] + 1;
      kutular.push([RENKLER[i], i < esik.length ? `${fmt(alt)}–${fmt(esik[i])}` : `${fmt(esik[esik.length - 1] + 1)}+`]);
    }
    lg.innerHTML =
      `<span style="margin-right:6px;font-size:11px;font-weight:600;color:var(--white,#e2e8f0);">${MOD_BASLIK[mod] || MOD_BASLIK.toplam}</span>` +
      kutular.map(([c, t]) => `<span class="lg-item"><span class="lg-box" style="background:${c}"></span>${t}</span>`).join('') +
      `<span class="lg-item" style="gap:5px;">Az <span style="width:56px;height:8px;border-radius:4px;display:inline-block;background:linear-gradient(90deg,${RENKLER.join(',')});"></span> Çok</span>`;
  }

  // İl adı için tıklama popup'ı ('toplam' modunda): kullanıcı "İhaleler" ya da "Doğrudan
  // Temin"den birini seçer (dünya ticaret haritasındaki ihracat/ithalat ayrımıyla aynı fikir).
  function popupHtml(ad, k, nIhale, nDt) {
    const btn = (aktif, href, etiket, sayi) =>
      `<a class="il-popup-btn${aktif ? '' : ' disabled'}" ${aktif ? `href="${href}"` : 'tabindex="-1" aria-disabled="true"'}>
         <span>${etiket}</span><b>${sayi.toLocaleString('tr')}</b>
       </a>`;
    return `<div class="il-popup">
      <b class="il-popup-ad">📍 ${ad}</b>
      <div class="il-popup-row">
        ${btn(nIhale > 0, 'ihaleler?il=' + encodeURIComponent(k), '📋 Güncel İhaleler', nIhale)}
        ${btn(nDt > 0, 'dogrudan-temin?il=' + encodeURIComponent(k), '⚡ Doğrudan Temin', nDt)}
      </div>
    </div>`;
  }

  // Modül durumu: veri bir kez çekilir, mod değişince yalnız bu değişkenlerden yeniden çizilir.
  let _katman = null, _ihaleSayim = {}, _dtSayim = {}, _toplamSayim = {};
  let _esikIhale = [], _esikDt = [], _esikToplam = [];
  let _aktifMod = 'toplam';

  // Mevcut Leaflet katmanını verilen moda göre yeniden stiller/bağlar — FETCH YAPMAZ.
  function uygula(mod) {
    if (!_katman) return;   // henüz çizilmediyse (veri yüklenmeden çağrılırsa) sessizce çık
    _aktifMod = mod;
    const sayim = mod === 'ihale' ? _ihaleSayim : mod === 'dt' ? _dtSayim : _toplamSayim;
    const esik  = mod === 'ihale' ? _esikIhale  : mod === 'dt' ? _esikDt  : _esikToplam;

    _katman.eachLayer(layer => {
      const k = layer.__ilKey, ad = layer.__ilAd;
      const n = sayim[k] || 0;
      layer.setStyle({ fillColor: renkSec(n, esik) });
      layer.off('click');   // önceki moddan kalan direkt-yönlendirme dinleyicisini temizle
      if (mod === 'toplam') {
        const nIhale = _ihaleSayim[k] || 0, nDt = _dtSayim[k] || 0;
        layer.bindTooltip(
          `<b>${ad}</b>` +
          `<br>📋 İhale: <span class="tt-sayi">${nIhale.toLocaleString('tr')}</span>` +
          `<br>⚡ Doğrudan Temin: <span class="tt-sayi">${nDt.toLocaleString('tr')}</span>` +
          `<br><span style="opacity:.75;">Toplam: ${(nIhale + nDt).toLocaleString('tr')}</span>`,
          { className: 'il-tooltip', sticky: true }
        );
        layer.bindPopup(popupHtml(ad, k, nIhale, nDt), { className: 'il-popup-wrap', maxWidth: 240 });
        // bindPopup zaten tıklamada açar — ayrı click dinleyicisine gerek yok.
      } else {
        layer.unbindPopup();
        const etiket = mod === 'ihale' ? '📋 İhale' : '⚡ Doğrudan Temin';
        layer.bindTooltip(`<b>${ad}</b> ${etiket}: <span class="tt-sayi">${n.toLocaleString('tr')}</span>`,
          { className: 'il-tooltip', sticky: true });
        const hedef = mod === 'ihale' ? 'ihaleler?il=' : 'dogrudan-temin?il=';
        layer.on('click', () => { window.location.href = hedef + encodeURIComponent(k); });
      }
    });

    legendCiz(esik, mod);
    document.querySelectorAll('.harita-mod-btn').forEach(b => b.classList.toggle('active', b.dataset.mod === mod));
    const alt = document.getElementById('harita-alt');
    if (alt) alt.textContent = MOD_ALT[mod] || MOD_ALT.toplam;
  }
  window.haritaModSec = uygula;

  async function ciz(haritaEl) {
    try {
      const sb = window.supabase.createClient(SB_URL, SB_KEY);
      const [geo, ihaleSayim, dtSayim] = await Promise.all([
        fetch(GEOJSON_URL).then(r => r.json()),
        ilSayimGetir(sb, 'il_sayim', 'ilanlar', 13000),
        ilSayimGetir(sb, 'dt_il_sayim', 'dogrudan_temin_ilanlari', 13000),
      ]);
      _ihaleSayim = ihaleSayim;
      _dtSayim = dtSayim;
      // Toplam = iki dict'in anahtar birleşiminden; en geniş anahtar kümesi olduğu için
      // her modda İL EŞLEŞTİRMESİ (k) hep BUNA göre yapılır (mod değişince kayma olmasın).
      _toplamSayim = {};
      new Set([...Object.keys(ihaleSayim), ...Object.keys(dtSayim)]).forEach(il => {
        _toplamSayim[il] = (ihaleSayim[il] || 0) + (dtSayim[il] || 0);
      });
      _esikIhale = esikler(_ihaleSayim);
      _esikDt = esikler(_dtSayim);
      _esikToplam = esikler(_toplamSayim);

      const map = L.map(haritaEl, { zoomControl: true, scrollWheelZoom: true, attributionControl: false });
      _katman = L.geoJSON(geo, {
        style: () => ({ weight: 1, color: '#334155', fillOpacity: 0.85 }),  // gerçek renk uygula() atar
        onEachFeature: (f, layer) => {
          layer.__ilKey = ilAnahtar(f.properties.name, _toplamSayim);
          layer.__ilAd = f.properties.name;
          layer.on({
            mouseover: e => e.target.setStyle({ weight: 2, color: '#fff', fillOpacity: 0.95 }),
            mouseout: e => _katman.resetStyle(e.target),
          });
        },
      }).addTo(map);
      map.fitBounds(_katman.getBounds(), { padding: [10, 10] });

      // İlk çizimde sayfanın GLOBAL modu varsa (dashboard.html'in aktifDashMod'u — kullanıcı
      // haritaya inmeden önce üstteki seçiciyle 'ihale'/'dt' seçmiş olabilir) onu kullan;
      // yoksa öntanım 'toplam'. window.aktifDashMod dashboard.html'de plain global (IIFE'siz).
      const ilkMod = window.aktifDashMod === 'ihale' ? 'ihale' : window.aktifDashMod === 'dt' ? 'dt' : 'toplam';
      uygula(ilkMod);
      const y = document.getElementById('harita-yukleniyor');
      if (y) y.style.display = 'none';
    } catch (e) {
      console.warn('Harita yüklenemedi:', e);
      const y = document.getElementById('harita-yukleniyor');
      if (y) y.textContent = '⚠ Harita yüklenemedi.';
    }
  }

  function init() {
    const haritaEl = document.getElementById('turkiye-harita');
    if (!haritaEl || !window.L) return;
    const io = new IntersectionObserver((entries) => {
      if (entries.some(e => e.isIntersecting)) { io.disconnect(); ciz(haritaEl); }
    }, { rootMargin: '200px' });
    io.observe(haritaEl);
  }

  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();
