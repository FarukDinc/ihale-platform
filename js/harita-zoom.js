/**
 * SVG harita yakınlaştırma/kaydırma — viewBox tabanlı, bağımlılıksız.
 *
 *   haritaZoomKur(document.getElementById('t-harita'));   // sarmalayıcıyı ver, içindeki <svg> bulunur
 *
 * · fare tekerleği → imlecin durduğu noktaya doğru yakınlaş/uzaklaş (sayfa kaymaz)
 * · sürükle        → kaydır          · çift tık / ⟲ → sıfırla
 * · iki parmak     → mobilde pinch   · +/− düğmeleri → merkezden zoom
 *
 * ⚠️ İki tuzak:
 *  1) Haritadaki path'lerde zaten click handler'ı var (il/ülke seç). Sürükleme bitince
 *     tarayıcı yine de click üretir → 4px'ten büyük sürüklemede click CAPTURE aşamasında yutulur.
 *  2) Harita her yeniden çizildiğinde (katman/yıl değişimi) yeni bir <svg> doğar → kur() TEKRAR
 *     çağrılmalı. Sarmalayıcıda MutationObserver ile bu kendiliğinden yapılır, ama zoom sıfırlanır.
 */
(function () {
  'use strict';

  // Düğme + ipucu stilini bir kez enjekte et (her sayfada ayrı CSS bakımı olmasın)
  function stilEkle() {
    if (document.getElementById('harita-zoom-stil')) return;
    const s = document.createElement('style');
    s.id = 'harita-zoom-stil';
    s.textContent = `
      .hz-araclar { position:absolute; right:10px; top:10px; z-index:5; display:flex; flex-direction:column; gap:6px; }
      .hz-btn { width:30px; height:30px; border-radius:8px; border:1px solid #DCE5EF; background:#fff;
        color:#0C3E70; font:700 16px/1 "Open Sans",system-ui,sans-serif; cursor:pointer; display:flex;
        align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(12,62,112,.12); padding:0;
        transition:background .12s,border-color .12s; }
      .hz-btn:hover { background:#EDF3FA; border-color:#9CC4E8; }
      .hz-btn:disabled { opacity:.4; cursor:default; }
      .hz-ipucu { position:absolute; left:10px; bottom:8px; z-index:5; font:400 11px/1.3 "Open Sans",system-ui,sans-serif;
        color:#6C757D; background:rgba(255,255,255,.86); border-radius:6px; padding:3px 8px; pointer-events:none; }
      .hz-svg { cursor:grab; touch-action:pan-y; }
      .hz-svg.hz-tutuluyor { cursor:grabbing; }
      .hz-svg.hz-yakin path { transition:none; }
    `;
    document.head.appendChild(s);
  }

  function kur(sarmal, secenek) {
    if (!sarmal) return null;
    secenek = secenek || {};
    const svg = sarmal.querySelector('svg');
    if (!svg || svg._hzKurulu) return null;
    svg._hzKurulu = true;
    stilEkle();

    const ilk = (svg.getAttribute('viewBox') || '').trim().split(/[\s,]+/).map(Number);
    if (ilk.length !== 4 || ilk.some(isNaN)) return null;
    let vb = ilk.slice();
    const EN_AZ = 1, EN_COK = secenek.enCok || 16;   // 1 = tam görünüm

    svg.classList.add('hz-svg');
    if (getComputedStyle(sarmal).position === 'static') sarmal.style.position = 'relative';

    const uygula = () => {
      svg.setAttribute('viewBox', vb.map(n => +n.toFixed(3)).join(' '));
      const o = ilk[2] / vb[2];
      svg.classList.toggle('hz-yakin', o > 1.01);
      if (btnEksi) btnEksi.disabled = o <= 1.001;
      if (btnSifir) btnSifir.disabled = o <= 1.001;
    };
    const sinirla = () => {
      vb[0] = Math.max(ilk[0], Math.min(ilk[0] + ilk[2] - vb[2], vb[0]));
      vb[1] = Math.max(ilk[1], Math.min(ilk[1] + ilk[3] - vb[3], vb[1]));
    };
    // Ekran koordinatı → SVG kullanıcı koordinatı (viewBox oranı korunduğu için basit orantı yeter)
    const nokta = (cx, cy) => {
      const r = svg.getBoundingClientRect();
      return { x: vb[0] + (cx - r.left) / r.width * vb[2], y: vb[1] + (cy - r.top) / r.height * vb[3] };
    };
    function zoomla(cx, cy, k) {
      const olcek = ilk[2] / vb[2];
      const hedef = Math.max(EN_AZ, Math.min(EN_COK, olcek * k));
      const katsayi = (ilk[2] / hedef) / vb[2];        // viewBox'a uygulanacak gerçek oran
      if (Math.abs(katsayi - 1) < 1e-6) return;        // sınıra dayandı
      const p = nokta(cx, cy);
      vb[2] *= katsayi; vb[3] *= katsayi;
      vb[0] = p.x - (p.x - vb[0]) * katsayi;
      vb[1] = p.y - (p.y - vb[1]) * katsayi;
      sinirla(); uygula();
    }
    function merkezZoom(k) {
      const r = svg.getBoundingClientRect();
      zoomla(r.left + r.width / 2, r.top + r.height / 2, k);
    }
    function sifirla() { vb = ilk.slice(); uygula(); }

    // ── Araç düğmeleri ──
    let btnEksi = null, btnSifir = null;
    if (secenek.araclar !== false) {
      const kutu = document.createElement('div');
      kutu.className = 'hz-araclar';
      kutu.innerHTML = '<button class="hz-btn" type="button" title="Yakınlaştır">+</button>' +
        '<button class="hz-btn" type="button" title="Uzaklaştır">−</button>' +
        '<button class="hz-btn" type="button" title="Sıfırla" style="font-size:14px;">⟲</button>';
      const [b1, b2, b3] = kutu.querySelectorAll('button');
      b1.addEventListener('click', () => merkezZoom(1.45));
      b2.addEventListener('click', () => merkezZoom(1 / 1.45));
      b3.addEventListener('click', sifirla);
      btnEksi = b2; btnSifir = b3;
      sarmal.appendChild(kutu);

      if (secenek.ipucu !== false && !sarmal.querySelector('.hz-ipucu')) {
        const ip = document.createElement('div');
        ip.className = 'hz-ipucu';
        ip.textContent = 'Tekerlekle yakınlaştır · sürükleyerek gez · çift tıkla sıfırla';
        sarmal.appendChild(ip);
      }
    }

    // ── Tekerlek ──
    svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      zoomla(e.clientX, e.clientY, e.deltaY < 0 ? 1.22 : 1 / 1.22);
      if (secenek.gizle) secenek.gizle();
    }, { passive: false });

    // ── Sürükle ──
    let sur = null, sonPan = 0;
    svg.addEventListener('pointerdown', (e) => {
      if (e.button !== 0 || e.pointerType === 'touch') return;   // dokunmatik aşağıda ele alınır
      sur = { x: e.clientX, y: e.clientY, vb: vb.slice(), tasindi: false, id: e.pointerId };
    });
    svg.addEventListener('pointermove', (e) => {
      if (!sur || e.pointerId !== sur.id) return;
      const dx = e.clientX - sur.x, dy = e.clientY - sur.y;
      if (!sur.tasindi) {
        if (Math.abs(dx) + Math.abs(dy) < 4) return;
        sur.tasindi = true;
        svg.classList.add('hz-tutuluyor');
        try { svg.setPointerCapture(sur.id); } catch (_) {}
        if (secenek.gizle) secenek.gizle();
      }
      const r = svg.getBoundingClientRect();
      vb[0] = sur.vb[0] - dx / r.width * vb[2];
      vb[1] = sur.vb[1] - dy / r.height * vb[3];
      sinirla(); uygula();
    });
    const birak = () => {
      if (sur && sur.tasindi) sonPan = Date.now();
      if (sur) { try { svg.releasePointerCapture(sur.id); } catch (_) {} }
      sur = null; svg.classList.remove('hz-tutuluyor');
    };
    svg.addEventListener('pointerup', birak);
    svg.addEventListener('pointercancel', birak);
    svg.addEventListener('pointerleave', birak);
    // Sürükleme sonrası sahte tıklama path'in click handler'ına ULAŞMASIN
    svg.addEventListener('click', (e) => {
      if (Date.now() - sonPan < 250) { e.stopPropagation(); e.preventDefault(); }
    }, true);
    svg.addEventListener('dblclick', (e) => { e.preventDefault(); sifirla(); });

    // ── Dokunmatik: tek parmak kaydır, iki parmak pinch ──
    let dok = null;
    const uzaklik = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    svg.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        dok = { tip: 'pinch', d: uzaklik(e.touches), vb: vb.slice() };
      } else if (e.touches.length === 1 && ilk[2] / vb[2] > 1.01) {
        dok = { tip: 'pan', x: e.touches[0].clientX, y: e.touches[0].clientY, vb: vb.slice() };
      } else dok = null;
    }, { passive: true });
    svg.addEventListener('touchmove', (e) => {
      if (!dok) return;
      if (dok.tip === 'pinch' && e.touches.length === 2) {
        e.preventDefault();
        const d = uzaklik(e.touches);
        if (!dok.d) return;
        const orta = { x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
                       y: (e.touches[0].clientY + e.touches[1].clientY) / 2 };
        zoomla(orta.x, orta.y, d / dok.d);
        dok.d = d;
      } else if (dok.tip === 'pan' && e.touches.length === 1) {
        e.preventDefault();
        const r = svg.getBoundingClientRect();
        vb[0] = dok.vb[0] - (e.touches[0].clientX - dok.x) / r.width * vb[2];
        vb[1] = dok.vb[1] - (e.touches[0].clientY - dok.y) / r.height * vb[3];
        sinirla(); uygula();
      }
    }, { passive: false });
    svg.addEventListener('touchend', () => { dok = null; });

    uygula();
    return { sifirla: sifirla, zoom: merkezZoom };
  }

  /**
   * Sarmalayıcıyı izler: içindeki <svg> yeniden üretildiğinde zoom'u otomatik yeniden kurar.
   * (Katman/yıl değiştirince harita innerHTML ile baştan çiziliyor.)
   */
  window.haritaZoomKur = function (sarmal, secenek) {
    if (typeof sarmal === 'string') sarmal = document.getElementById(sarmal);
    if (!sarmal) return null;
    const sonuc = kur(sarmal, secenek);
    if (!sarmal._hzGozlem) {
      sarmal._hzGozlem = new MutationObserver(() => {
        const s = sarmal.querySelector('svg');
        if (s && !s._hzKurulu) kur(sarmal, secenek);
      });
      sarmal._hzGozlem.observe(sarmal, { childList: true, subtree: false });
    }
    return sonuc;
  };
})();
