/* ============================================
   IHALE PLATFORM — Interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ---- LIVE COUNTER ----
  const counters = [
    { id: 'cnt-active',  base: 2847, variance: 3,  label: '+3 son 1 saatte' },
    { id: 'cnt-today',   base: 124,  variance: 1,  label: '+1 yeni eklendi' },
    { id: 'cnt-budget',  base: 4.2,  variance: 0,  label: 'milyar TL toplam', decimal: 1 },
    { id: 'cnt-win',     base: 68,   variance: 0,  label: 'ortalama kazanma %' },
  ];

  function formatNumber(n, decimal) {
    if (decimal) return n.toFixed(decimal);
    return n.toLocaleString('tr-TR');
  }

  // Initial render
  counters.forEach(c => {
    const el = document.getElementById(c.id);
    if (el) el.textContent = formatNumber(c.base, c.decimal);
  });

  // Tick every ~4 seconds for active + today counters
  setInterval(() => {
    [counters[0], counters[1]].forEach(c => {
      if (c.variance === 0) return;
      const el = document.getElementById(c.id);
      if (!el) return;
      const shouldTick = Math.random() < 0.35;
      if (shouldTick) {
        c.base += 1;
        el.textContent = formatNumber(c.base, c.decimal);
        el.classList.add('tick');
        setTimeout(() => el.classList.remove('tick'), 300);
      }
    });
  }, 4000);

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

  // ---- MOBILE NAV ----
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', mobileMenu.classList.contains('open'));
    });
  }

});
