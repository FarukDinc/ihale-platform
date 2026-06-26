/* ============================================
   IHALE PLATFORM — Interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ---- ANIMATED COUNT-UP on scroll ----
  const statEls = document.querySelectorAll('[data-countup]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseFloat(el.dataset.countup);
      const suffix = el.dataset.suffix || '';
      const decimal = el.dataset.decimal ? parseInt(el.dataset.decimal) : 0;
      const duration = 1200;
      const start = performance.now();

      function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const val = target * ease;
        el.textContent = decimal ? val.toFixed(decimal) + suffix : Math.round(val).toLocaleString('tr-TR') + suffix;
        if (progress < 1) requestAnimationFrame(step);
      }

      requestAnimationFrame(step);
      observer.unobserve(el);
    });
  }, { threshold: 0.3 });

  statEls.forEach(el => observer.observe(el));

  // ---- SMOOTH NAV HIGHLIGHT ----
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(a => a.classList.remove('active'));
        const active = document.querySelector(`.nav-links a[href="#${entry.target.id}"]`);
        if (active) active.classList.add('active');
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => sectionObserver.observe(s));

  // ---- PRICING TOGGLE (annual/monthly) ----
  const toggle = document.getElementById('billing-toggle');
  const priceEls = document.querySelectorAll('[data-monthly][data-annual]');
  const periodEls = document.querySelectorAll('.period');

  if (toggle) {
    toggle.addEventListener('change', () => {
      const isAnnual = toggle.checked;
      priceEls.forEach(el => {
        el.textContent = isAnnual ? el.dataset.annual : el.dataset.monthly;
      });
      periodEls.forEach(el => {
        el.textContent = isAnnual ? '/ay (yıllık)' : '/ay';
      });
    });
  }

  // ---- LANDING PAGE MOBILE NAV ----
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', mobileMenu.classList.contains('open'));
    });
  }

  // ---- APP SIDEBAR MOBILE TOGGLE ----
  // Applies to dashboard, ihaleler, takipte, etc. — injects hamburger into .topbar
  const sidebar = document.querySelector('.app > .sidebar, .app > aside.sidebar');
  const topbar  = document.querySelector('.topbar');
  if (sidebar && topbar) {
    // Inject hamburger button
    const hBtn = document.createElement('button');
    hBtn.id = 'sidebar-toggle';
    hBtn.setAttribute('aria-label', 'Menüyü Aç/Kapat');
    hBtn.style.cssText = [
      'display:none',
      'background:var(--card-bg)',
      'border:1px solid var(--border)',
      'border-radius:6px',
      'color:var(--white)',
      'font-size:18px',
      'width:36px',
      'height:36px',
      'cursor:pointer',
      'align-items:center',
      'justify-content:center',
      'flex-shrink:0',
    ].join(';');
    hBtn.textContent = '☰';
    topbar.insertBefore(hBtn, topbar.firstChild);

    // Backdrop overlay
    const backdrop = document.createElement('div');
    backdrop.id = 'sidebar-backdrop';
    backdrop.style.cssText = [
      'display:none',
      'position:fixed',
      'inset:0',
      'background:rgba(0,0,0,0.6)',
      'z-index:99',
    ].join(';');
    document.body.appendChild(backdrop);

    function sidebarAc() {
      sidebar.style.cssText = 'display:flex;position:fixed;top:0;left:0;z-index:100;height:100vh;';
      backdrop.style.display = 'block';
    }
    function sidebarKapat() {
      sidebar.style.cssText = '';
      backdrop.style.display = 'none';
    }

    hBtn.addEventListener('click', () => {
      sidebar.style.display === 'flex' && sidebar.style.position === 'fixed'
        ? sidebarKapat()
        : sidebarAc();
    });
    backdrop.addEventListener('click', sidebarKapat);

    // Show/hide button based on viewport
    const mq = window.matchMedia('(max-width: 900px)');
    function onResize(e) {
      hBtn.style.display = e.matches ? 'flex' : 'none';
      if (!e.matches) sidebarKapat();
    }
    mq.addEventListener('change', onResize);
    onResize(mq);
  }

});
