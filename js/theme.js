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

  function uygula(tema) {
    if (tema === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem(KEY, tema);
    var btn = document.getElementById('tema-degistir-btn');
    if (btn) btn.textContent = tema === 'light' ? '🌙' : '☀️';
  }

  function ekle() {
    if (document.getElementById('tema-degistir-btn')) return;
    var btn = document.createElement('button');
    btn.id = 'tema-degistir-btn';
    btn.title = 'Açık/Koyu tema değiştir';
    btn.setAttribute('aria-label', 'Açık/Koyu tema değiştir');
    btn.textContent = (localStorage.getItem(KEY) === 'light') ? '🌙' : '☀️';
    btn.style.cssText = [
      'position:fixed', 'bottom:20px', 'right:20px', 'z-index:9999',
      'width:44px', 'height:44px', 'border-radius:50%',
      'border:1px solid var(--border, rgba(255,255,255,0.15))',
      'background:var(--navy-mid, #152340)', 'color:var(--white, #fff)',
      'font-size:18px', 'cursor:pointer', 'display:flex',
      'align-items:center', 'justify-content:center',
      'box-shadow:0 4px 12px rgba(0,0,0,0.3)', 'transition:transform .15s'
    ].join(';');
    btn.onmouseenter = function () { btn.style.transform = 'scale(1.08)'; };
    btn.onmouseleave = function () { btn.style.transform = 'scale(1)'; };
    btn.onclick = function () {
      var simdi = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      uygula(simdi);
    };
    document.body.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ekle);
  } else {
    ekle();
  }
})();
