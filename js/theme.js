/* İhaleGlobal — Açık/Koyu Tema Değiştirici
   Sayfa yüklenir yüklenmez kayıtlı tercihi uygular (flaş önleme için en üstte,
   <head>'te css/style.css'ten hemen sonra çağrılmalı), ardından sol-alt SIDEBAR
   FOOTER'ına kompakt bir geçiş düğmesi gömer (yoksa sol-alt sabit fallback).
   Varsayılan: koyu tema (mevcut marka rengi). */
(function () {
  var KEY = 'ihale_tema';
  var kayitli = localStorage.getItem(KEY);
  if (kayitli === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  }

  // Buton, TIKLANINCA geçilecek modu gösterir (koyudayken "☀️ Gündüz Modu").
  function etiketle(tema) {
    var btn = document.getElementById('tema-degistir-btn');
    if (!btn) return;
    btn.innerHTML = tema === 'light'
      ? '<span style="font-size:13px;line-height:1">🌙</span><span>Gece Modu</span>'
      : '<span style="font-size:13px;line-height:1">☀️</span><span>Gündüz Modu</span>';
  }

  function uygula(tema) {
    if (tema === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem(KEY, tema);
    etiketle(tema);
    // Grafik sayfalari dinleyip renkleri tazeler (Chart.js CSS degiskenlerini otomatik okumaz).
    try { window.dispatchEvent(new CustomEvent('tema-degisti', { detail: tema })); } catch (_) {}
  }

  function ekle() {
    if (document.getElementById('tema-degistir-btn')) return;
    var suAn = (localStorage.getItem(KEY) === 'light') ? 'light' : 'dark';
    var btn = document.createElement('button');
    btn.id = 'tema-degistir-btn';
    btn.title = 'Gündüz / Gece modu değiştir';
    btn.setAttribute('aria-label', 'Gündüz / Gece modu değiştir');
    btn.onclick = function () {
      var simdi = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      uygula(simdi);
    };

    // Yüzen buton hep bir yere denk geliyordu (topbar/bildirim). Artık sol-alt SIDEBAR FOOTER'ına
    // (kullanıcı/Pro Plan bloğunun altına) KOMPAKT gömülür — hiçbir şeye engel olmaz.
    var footer = document.querySelector('.sidebar-footer');
    if (footer) {
      btn.style.cssText = [
        'display:flex', 'align-items:center', 'justify-content:center', 'gap:5px',
        'width:100%', 'margin-top:10px', 'padding:6px 8px', 'border-radius:8px',
        'border:1px solid var(--border, #22314f)', 'background:transparent',
        'color:var(--muted, #94a3b8)', 'font-family:var(--font-body, sans-serif)',
        'font-size:11px', 'font-weight:600', 'cursor:pointer',
        'transition:color .15s, border-color .15s'
      ].join(';');
      btn.onmouseenter = function () { btn.style.color = 'var(--amber, #F0A500)'; btn.style.borderColor = 'var(--amber, #F0A500)'; };
      btn.onmouseleave = function () { btn.style.color = 'var(--muted, #94a3b8)'; btn.style.borderColor = 'var(--border, #22314f)'; };
      footer.appendChild(btn);
    } else {
      // Sidebar'sız sayfalar (login/landing) için küçük sabit buton, sol-altta.
      btn.style.cssText = [
        'position:fixed', 'bottom:16px', 'left:16px', 'z-index:9999',
        'display:flex', 'align-items:center', 'gap:5px', 'padding:6px 12px', 'border-radius:20px',
        'border:1px solid var(--amber, #F0A500)', 'background:var(--navy-mid, #152340)',
        'color:var(--amber, #F0A500)', 'font-family:var(--font-body, sans-serif)',
        'font-size:12px', 'font-weight:700', 'cursor:pointer', 'box-shadow:0 4px 14px rgba(0,0,0,0.28)'
      ].join(';');
      document.body.appendChild(btn);
    }
    etiketle(suAn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ekle);
  } else {
    ekle();
  }
})();
