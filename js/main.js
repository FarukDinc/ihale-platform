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

/**
 * trAramaKalibi — PostgREST `ilike` için Türkçe-güvenli desen üretir.
 *
 * SORUN: ILIKE yalnız ASCII harflerde büyük/küçük katlaması yapar. Türkçe'de
 * İ(U+0130)↔i ve I↔ı(U+0131) çiftleri KATLANMAZ, ayrıca ü/ğ/ş/ç/ö gibi harfler
 * ASCII karşılıklarıyla eşleşmez. Sonuç: kullanıcı "istanbul" yazınca SIFIR kayıt
 * döner, hata da olmadığı için ekranda "kayıt bulunamadı" yazar ve veri yok sanılır.
 * 20 Tem canlı ölçümü (kik_kararlar, 97 satır): "istanbul" → 0 / "İSTANBUL" → 3;
 * "mudurlugu" → 0 iken gerçek evren 61 satır.
 *
 * ÇÖZÜM: çift varyantı olan her harfi tek-karakter joker `_` ile değiştir. Böylece
 * hangi varyant yazılırsa yazılsın hepsi eşleşir. Doğrulandı: "m_d_rl___" → 61
 * (gerçek evrenin tamamı), "_stanb_l" → 2.
 *
 * TAKAS: `_` herhangi bir karakteri tuttuğu için hafif fazla-eşleşme olabilir
 * (ör. "_stanb_l" teorik olarak "astanbol"u da tutar). Arama kutusunda birkaç fazla
 * sonuç, sıfır sonuçtan kıyaslanamayacak kadar iyidir.
 *
 * NOT: tr_fold()'lu bir kolon/RPC üzerinden arıyorsan buna GEREK YOKTUR — orada
 * katlama zaten sunucuda yapılıyor. Bu yardımcı, ham kolonda ilike yapmak zorunda
 * olan sayfalar içindir.
 */
function trAramaKalibi(metin) {
  if (!metin) return '';
  return String(metin)
    // or() gramerini bozan karakterler (virgül listeyi böler, parantez grubu kapatır → 400)
    .replace(/[,()*\%_]/g, ' ')
    .trim()
    // Türkçe'de ASCII karşılığıyla karışan harfler → tek karakter joker
    .replace(/[iıIİ]/g, '_')
    .replace(/[uüUÜ]/g, '_')
    .replace(/[gğGĞ]/g, '_')
    .replace(/[sşSŞ]/g, '_')
    .replace(/[cçCÇ]/g, '_')
    .replace(/[oöOÖ]/g, '_');
}
window.trAramaKalibi = trAramaKalibi;

/**
 * TR_ILLER_BUYUK — 81 il, DB'deki yazımla (Türkçe BÜYÜK HARF).
 *
 * NEDEN STATİK: il dropdown'larını `select('il')` ile DB'den distinct çıkarmak
 * D1 tuzağına düşüyor — PostgREST db-max-rows=1000 SUNUCUDA kesiyor ve `.limit(5000)`
 * bunu AŞMIYOR. 20 Tem ölçümü: dogrudan-temin yedek yolu 81 ilden 69'unu getiriyordu;
 * kaybolanlar tam da düşük hacimli iller (BAYBURT, ARTVİN, KİLİS, IĞDIR…) — kullanıcı
 * "bu ilde ihale yok" sanıyordu. 1,49M satırı sayfalayarak distinct çıkarmak ise
 * yüzlerce istek demek. İl listesi sabit bir gerçek; DB'ye sormaya gerek yok.
 *
 * ⚠️ Değerler DB ile BİREBİR aynı olmalı — filtreler `.eq('il', ...)` ile tam eşleşme
 * arıyor. DB'de "İSTANBUL"/"ADANA" gibi Türkçe büyük harf tutuluyor; küçük harf ya da
 * Title Case bir değer sessizce 0 sonuç döndürür.
 */
const TR_ILLER_BUYUK = ['ADANA','ADIYAMAN','AFYONKARAHİSAR','AĞRI','AKSARAY','AMASYA','ANKARA','ANTALYA','ARDAHAN','ARTVİN','AYDIN','BALIKESİR','BARTIN','BATMAN','BAYBURT','BİLECİK','BİNGÖL','BİTLİS','BOLU','BURDUR','BURSA','ÇANAKKALE','ÇANKIRI','ÇORUM','DENİZLİ','DİYARBAKIR','DÜZCE','EDİRNE','ELAZIĞ','ERZİNCAN','ERZURUM','ESKİŞEHİR','GAZİANTEP','GİRESUN','GÜMÜŞHANE','HAKKARİ','HATAY','IĞDIR','ISPARTA','İSTANBUL','İZMİR','KAHRAMANMARAŞ','KARABÜK','KARAMAN','KARS','KASTAMONU','KAYSERİ','KIRIKKALE','KIRKLARELİ','KIRŞEHİR','KİLİS','KOCAELİ','KONYA','KÜTAHYA','MALATYA','MANİSA','MARDİN','MERSİN','MUĞLA','MUŞ','NEVŞEHİR','NİĞDE','ORDU','OSMANİYE','RİZE','SAKARYA','SAMSUN','SİİRT','SİNOP','SİVAS','ŞANLIURFA','ŞIRNAK','TEKİRDAĞ','TOKAT','TRABZON','TUNCELİ','UŞAK','VAN','YALOVA','YOZGAT','ZONGULDAK'];
window.TR_ILLER_BUYUK = TR_ILLER_BUYUK;
