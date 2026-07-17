// ============================================================================
// svg-zoom.js — SVG haritalar için yeniden kullanılabilir yakınlaştırma/kaydırma
// ----------------------------------------------------------------------------
// Kullanım: svg'yi içeren wrapper hazır olduktan SONRA → window.svgZoomKur(wrapEl, {maxZoom: 8})
//   • tekerlek  : imleç noktasına yakınlaş/uzaklaş
//   • sürükleme : kaydırma (yalnızca yakınlaşmışken; pointer events, mobil dahil)
//   • pinch     : iki parmak yakınlaştırma
//   • butonlar  : + / − / ⟲ (wrapper'ın sağ üstüne eklenir)
// Sürükleme sonrası tıklama capture-phase'de yutulur → choropleth'lerdeki
// "ülkeye/ile tıkla-filtrele" davranışı yanlışlıkla tetiklenmez.
// NOT: çift-tık zoom bilerek YOK — haritalardaki tek-tık filtre ile çakışıyor.
// viewBox mutasyonu kullanılır; tooltip'ler clientX/Y ile konumlandığı için etkilenmez.
// ============================================================================
(function () {
  if (!document.getElementById('svg-zoom-stil')) {
    const st = document.createElement('style');
    st.id = 'svg-zoom-stil';
    st.textContent = `
      .svg-zoom-btns { position:absolute; top:10px; right:10px; display:flex; flex-direction:column; gap:4px; z-index:5; }
      .svg-zoom-btns button {
        width:32px; height:32px; border-radius:8px; border:1px solid rgba(255,255,255,.16);
        background:rgba(10,17,29,.88); color:#e2e8f0; font-size:17px; font-weight:700; cursor:pointer;
        line-height:1; display:flex; align-items:center; justify-content:center; padding:0;
        transition:border-color .15s, color .15s; touch-action:manipulation;
      }
      .svg-zoom-btns button:hover { border-color:#f0a500; color:#f0a500; }
    `;
    document.head.appendChild(st);
  }

  window.svgZoomKur = function (wrap, ayar) {
    ayar = ayar || {};
    const svg = wrap && wrap.querySelector('svg');
    if (!svg) return null;
    const vb0 = (svg.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
    if (vb0.length !== 4 || vb0.some(isNaN)) return null;
    const maxZoom = ayar.maxZoom || 8;
    let vb = vb0.slice();          // [x, y, w, h]
    let surukledi = false;         // sürükleme bitiminde tıklamayı yutmak için
    let btnSifirla = null;

    if (getComputedStyle(wrap).position === 'static') wrap.style.position = 'relative';
    svg.style.touchAction = 'none';   // pointer events'in mobilde çalışması için (Leaflet de böyle)

    const seviye = () => vb0[2] / vb[2];

    function uygula() {
      svg.setAttribute('viewBox', vb.map(n => +n.toFixed(3)).join(' '));
      svg.style.cursor = seviye() > 1.01 ? 'grab' : '';
      if (btnSifirla) btnSifirla.style.opacity = seviye() > 1.01 ? '1' : '.35';
    }

    function sinirla() {
      const w = Math.min(vb0[2], Math.max(vb0[2] / maxZoom, vb[2]));
      const h = w * vb0[3] / vb0[2];
      vb[2] = w; vb[3] = h;
      vb[0] = Math.min(vb0[0] + vb0[2] - w, Math.max(vb0[0], vb[0]));
      vb[1] = Math.min(vb0[1] + vb0[3] - h, Math.max(vb0[1], vb[1]));
    }

    // ekran koordinatı → mevcut viewBox koordinatı
    function svgNokta(cx, cy) {
      const r = svg.getBoundingClientRect();
      return [vb[0] + (cx - r.left) / r.width * vb[2], vb[1] + (cy - r.top) / r.height * vb[3]];
    }

    // f>1 yakınlaş; `sabit` (viewBox koordinatı) ekranda yerinde kalır
    function zoom(f, sabit) {
      const yeniW = Math.min(vb0[2], Math.max(vb0[2] / maxZoom, vb[2] / f));
      const oran = yeniW / vb[2];
      if (!sabit) sabit = [vb[0] + vb[2] / 2, vb[1] + vb[3] / 2];
      vb[0] = sabit[0] - (sabit[0] - vb[0]) * oran;
      vb[1] = sabit[1] - (sabit[1] - vb[1]) * oran;
      vb[2] = yeniW; vb[3] = vb[3] * oran;
      sinirla(); uygula();
    }

    function sifirla() { vb = vb0.slice(); uygula(); }

    // ── tekerlek ──
    wrap.addEventListener('wheel', e => {
      e.preventDefault();
      zoom(e.deltaY < 0 ? 1.3 : 1 / 1.3, svgNokta(e.clientX, e.clientY));
    }, { passive: false });

    // ── sürükleme + pinch ──
    const aktif = new Map();     // pointerId -> [x, y]
    let pinchBas = null;         // { mesafe, vb }
    svg.addEventListener('pointerdown', e => {
      aktif.set(e.pointerId, [e.clientX, e.clientY]);
      if (aktif.size === 2) {
        const p = [...aktif.values()];
        pinchBas = { mesafe: Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]) || 1, vb: vb.slice() };
      }
      surukledi = false;
      // DİKKAT: capture BURADA ALINMAZ. Capture aktifken tarayıcı click'i path yerine
      // svg'ye hedefler → il/ülke path'lerindeki click dinleyicileri HİÇ ateşlenmez
      // (haritada "ile tıkla" ölür — 17 Tem canlı bug'ı). Capture ancak gerçek
      // sürükleme/pinch BAŞLAYINCA alınır (aşağıda) — temiz tıklama serbest kalır.
    });
    svg.addEventListener('pointermove', e => {
      if (!aktif.has(e.pointerId)) return;
      const onceki = aktif.get(e.pointerId);
      aktif.set(e.pointerId, [e.clientX, e.clientY]);
      if (aktif.size === 1) {
        if (seviye() <= 1.01) return;   // tam görünümde kaydırılacak yer yok
        const r = svg.getBoundingClientRect();
        if (Math.abs(e.clientX - onceki[0]) + Math.abs(e.clientY - onceki[1]) > 1) {
          surukledi = true;
          try { svg.setPointerCapture(e.pointerId); } catch (_) {}   // sürükleme BAŞLADI → artık capture güvenli
        }
        vb[0] -= (e.clientX - onceki[0]) / r.width * vb[2];
        vb[1] -= (e.clientY - onceki[1]) / r.height * vb[3];
        sinirla(); uygula();
        svg.style.cursor = 'grabbing';
      } else if (aktif.size === 2 && pinchBas) {
        const p = [...aktif.values()];
        const m = Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]);
        if (m > 0) {
          surukledi = true;
          try { aktif.forEach((_, id) => svg.setPointerCapture(id)); } catch (_) {}   // pinch başladı → capture
          const orta = [(p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2];
          vb = pinchBas.vb.slice();
          zoom(m / pinchBas.mesafe, svgNokta(orta[0], orta[1]));
        }
      }
    });
    function birak(e) {
      aktif.delete(e.pointerId);
      if (aktif.size < 2) pinchBas = null;
      svg.style.cursor = seviye() > 1.01 ? 'grab' : '';
    }
    svg.addEventListener('pointerup', birak);
    svg.addEventListener('pointercancel', birak);

    // sürükleme bitişindeki tıklamayı yut (il/ülke seçimi yanlışlıkla tetiklenmesin)
    svg.addEventListener('click', e => {
      if (surukledi) { e.stopPropagation(); e.preventDefault(); surukledi = false; }
    }, true);

    // ── butonlar ──
    const kutu = document.createElement('div');
    kutu.className = 'svg-zoom-btns';
    kutu.innerHTML =
      '<button type="button" aria-label="Yakınlaştır" title="Yakınlaştır">+</button>' +
      '<button type="button" aria-label="Uzaklaştır" title="Uzaklaştır">−</button>' +
      '<button type="button" aria-label="Görünümü sıfırla" title="Görünümü sıfırla">⟲</button>';
    wrap.appendChild(kutu);
    const btnlar = kutu.querySelectorAll('button');
    btnlar[0].addEventListener('click', () => zoom(1.5));
    btnlar[1].addEventListener('click', () => zoom(1 / 1.5));
    btnSifirla = btnlar[2];
    btnSifirla.addEventListener('click', sifirla);

    uygula();
    return { zoom, sifirla };
  };
})();
