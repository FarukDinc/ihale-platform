/* İhaleGlobal — Açık/Koyu Tema Değiştirici
   Sayfa yüklenir yüklenmez kayıtlı tercihi uygular (flaş önleme için en üstte,
   <head>'te css/style.css'ten hemen sonra çağrılmalı), ardından sağ altta
   sabit bir geçiş düğmesi ekler. Varsayılan: koyu tema (mevcut marka rengi). */
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
      ? '<span style="font-size:16px;line-height:1">🌙</span><span>Gece Modu</span>'
      : '<span style="font-size:16px;line-height:1">☀️</span><span>Gündüz Modu</span>';
  }

  function uygula(tema) {
    if (tema === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem(KEY, tema);
    etiketle(tema);
  }

  function ekle() {
    if (document.getElementById('tema-degistir-btn')) return;
    var suAn = (localStorage.getItem(KEY) === 'light') ? 'light' : 'dark';
    var btn = document.createElement('button');
    btn.id = 'tema-degistir-btn';
    btn.title = 'Gündüz / Gece modu değiştir';
    btn.setAttribute('aria-label', 'Gündüz / Gece modu değiştir');
    btn.style.cssText = [
      'position:fixed', 'bottom:20px', 'right:20px', 'z-index:9999',
      'display:flex', 'align-items:center', 'gap:8px',
      'padding:9px 16px', 'border-radius:24px',
      'border:1px solid var(--amber, #F0A500)',
      'background:var(--navy-mid, #152340)', 'color:var(--amber, #F0A500)',
      'font-family:var(--font-body, sans-serif)', 'font-size:13px', 'font-weight:700',
      'cursor:pointer', 'box-shadow:0 6px 18px rgba(0,0,0,0.28)',
      'transition:transform .15s, box-shadow .15s'
    ].join(';');
    btn.onmouseenter = function () { btn.style.transform = 'translateY(-2px)'; btn.style.boxShadow = '0 8px 22px rgba(0,0,0,0.35)'; };
    btn.onmouseleave = function () { btn.style.transform = 'translateY(0)'; btn.style.boxShadow = '0 6px 18px rgba(0,0,0,0.28)'; };
    btn.onclick = function () {
      var simdi = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      uygula(simdi);
    };
    document.body.appendChild(btn);
    etiketle(suAn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ekle);
  } else {
    ekle();
  }
})();
