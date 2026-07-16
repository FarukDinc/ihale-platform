/* ============================================================================
 * harita.js — Türkiye il bazlı choropleth ısı haritası (Leaflet, yeniden kullanılabilir)
 * ----------------------------------------------------------------------------
 * Kullanım (sayfada):
 *   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
 *   <div id="turkiye-harita"></div>
 *   <div id="harita-yukleniyor">🗺️ Harita yükleniyor…</div>   (opsiyonel)
 *   <div id="harita-legend"></div>                              (opsiyonel)
 *   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
 *   <script src="js/harita.js"></script>
 * Otomatik lazy-init (IntersectionObserver). Bir ile tıklayınca ihaleler?il=X açar.
 * NOT: index.html'de aynı mantığın satır-içi bir kopyası var; ileride index de bu
 *      modüle geçirilip tekilleştirilebilir (teknik borç).
 * ========================================================================== */
(function () {
  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs";
  const GEOJSON_URL = 'data/turkey-provinces.geojson';
  const RENKLER = ['#243b5e', '#7a5c1e', '#b07d08', '#e09600', '#f0a500', '#ef4444'];

  // İl bazlı sayım — önce tek istekli RPC (hızlı), yoksa sayfalı fallback
  async function ilSayimGetir(sb) {
    try {
      const { data, error } = await sb.rpc('il_sayim');
      if (!error && Array.isArray(data) && data.length) {
        const sayim = {};
        data.forEach(r => { if (r.il) sayim[r.il] = Number(r.adet) || 0; });
        return sayim;
      }
    } catch (_) { /* RPC yoksa fallback */ }
    const istekler = [];
    for (let off = 0; off < 13000; off += 1000) {
      istekler.push(sb.from('ilanlar').select('il').not('il', 'is', null).range(off, off + 999));
    }
    const sonuc = await Promise.all(istekler);
    const sayim = {};
    for (const { data } of sonuc) (data || []).forEach(r => {
      if (r.il) sayim[r.il] = (sayim[r.il] || 0) + 1;
    });
    return sayim;
  }

  // GeoJSON Title-case ad → DB BÜYÜK HARF il anahtarı (örn. Afyon → AFYONKARAHİSAR)
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

  function legendCiz(esik) {
    const lg = document.getElementById('harita-legend');
    if (!lg) return;
    const fmt = n => n >= 1000 ? (n / 1000).toFixed(1).replace('.0', '') + 'b' : String(n);
    // renkSec ile birebir eşleşir: 0 → #16233d, [1,e0] → RENKLER[0], (e0,e1] → RENKLER[1], … , e4+ → RENKLER[5]
    const kutular = [['#16233d', 'İhale yok']];
    for (let i = 0; i < RENKLER.length; i++) {
      const alt = i === 0 ? 1 : esik[i - 1] + 1;
      kutular.push([RENKLER[i], i < esik.length ? `${fmt(alt)}–${fmt(esik[i])}` : `${fmt(esik[esik.length - 1] + 1)}+`]);
    }
    lg.innerHTML =
      '<span style="margin-right:6px;font-size:11px;font-weight:600;color:var(--white,#e2e8f0);">Renkler ildeki ihale yoğunluğunu gösterir:</span>' +
      kutular.map(([c, t]) => `<span class="lg-item"><span class="lg-box" style="background:${c}"></span>${t}</span>`).join('') +
      `<span class="lg-item" style="gap:5px;">Az <span style="width:56px;height:8px;border-radius:4px;display:inline-block;background:linear-gradient(90deg,${RENKLER.join(',')});"></span> Çok</span>`;
  }

  async function ciz(haritaEl) {
    try {
      const sb = window.supabase.createClient(SB_URL, SB_KEY);
      const [geo, sayim] = await Promise.all([
        fetch(GEOJSON_URL).then(r => r.json()),
        ilSayimGetir(sb),
      ]);
      const esik = esikler(sayim);

      const map = L.map(haritaEl, { zoomControl: true, scrollWheelZoom: false, attributionControl: false });
      const katman = L.geoJSON(geo, {
        style: f => {
          const k = ilAnahtar(f.properties.name, sayim);
          return { fillColor: renkSec(sayim[k] || 0, esik), weight: 1, color: '#334155', fillOpacity: 0.85 };
        },
        onEachFeature: (f, layer) => {
          const k = ilAnahtar(f.properties.name, sayim);
          const n = sayim[k] || 0;
          layer.bindTooltip(`${f.properties.name} <span class="tt-sayi">${n.toLocaleString('tr')}</span>`,
            { className: 'il-tooltip', sticky: true });
          layer.on({
            mouseover: e => e.target.setStyle({ weight: 2, color: '#fff', fillOpacity: 0.95 }),
            mouseout: e => katman.resetStyle(e.target),
            click: () => { window.location.href = 'ihaleler?il=' + encodeURIComponent(k); },
          });
        },
      }).addTo(map);
      map.fitBounds(katman.getBounds(), { padding: [10, 10] });

      legendCiz(esik);
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
