/**
 * Plan kontrolü modülü.
 * Supabase'deki kullanici_krediler tablosundan kullanıcı planını okur
 * (payment.py ödeme başarılı olunca plan'ı buraya yazar). Süresi dolan
 * abonelik free'ye düşer. Sonuç 30 saniyeliğine cache'lenir.
 */
window.Plan = (() => {
  // DB'deki gerçek geçerli değerler (planlar.kod FK): 'standart' | 'kurumsal'.
  // Diğerleri (pro/premium/enterprise) geriye dönük tolerans için tutuluyor.
  const PRO_PLANS = ['standart', 'kurumsal', 'pro', 'Pro', 'PRO', 'premium', 'enterprise'];

  let _cache = null;
  let _cacheTs = 0;
  const CACHE_MS = 30000;

  async function getUser() {
    if (!window.supabase) return null;
    const SB_URL = "https://ihaleglobal.com";
    const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs";
    const sb = window.supabase.createClient(SB_URL, SB_KEY);
    try {
      const { data: { user } } = await sb.auth.getUser();
      return { sb, user };
    } catch { return null; }
  }

  async function getPlan() {
    if (_cache && Date.now() - _cacheTs < CACHE_MS) return _cache;
    const res = await getUser();
    if (!res || !res.user) {
      _cache = 'free';
      _cacheTs = Date.now();
      return _cache;
    }
    try {
      const { data } = await res.sb.from('kullanici_krediler')
        .select('plan, plan_bitis')
        .eq('kullanici_id', res.user.id)
        .single();
      let planDeger = data?.plan;
      // Abonelik süresi dolmuşsa free'ye düş
      if (planDeger && data?.plan_bitis && new Date(data.plan_bitis) < new Date()) planDeger = 'free';
      _cache = PRO_PLANS.includes(planDeger) ? 'pro' : 'free';
    } catch {
      _cache = 'free';
    }
    _cacheTs = Date.now();
    return _cache;
  }

  function isPro() {
    return _cache === 'pro';
  }

  /**
   * Bir element üzerine Pro kilitli overlay koyar.
   * el: HTMLElement, mesaj: string (opsiyonel)
   */
  function lockElement(el, mesaj) {
    if (!el) return;
    el.style.position = 'relative';
    el.style.overflow = 'hidden';
    const overlay = document.createElement('div');
    overlay.className = 'pro-lock-overlay';
    overlay.innerHTML = `
      <div class="pro-lock-box">
        <div class="pro-lock-icon">🔒</div>
        <div class="pro-lock-title">Pro Özelliği</div>
        <div class="pro-lock-desc">${mesaj || 'Bu özellik Pro plana özeldir.'}</div>
        <a href="fiyatlandirma_odeme_bolumu" class="pro-lock-btn">Pro'ya Geç →</a>
      </div>
    `;
    el.appendChild(overlay);

    // Blur içeriği
    el.querySelectorAll(':scope > *:not(.pro-lock-overlay)').forEach(child => {
      child.style.filter = 'blur(4px)';
      child.style.pointerEvents = 'none';
      child.style.userSelect = 'none';
    });
  }

  /**
   * İçerik alanını Pro banner ile değiştir (sayfa düzeyinde kilit).
   * container: HTMLElement
   */
  function lockPage(container, baslik, mesaj) {
    if (!container) return;
    container.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:400px;text-align:center;gap:16px;">
        <div style="font-size:48px;">🔒</div>
        <h2 style="font-family:var(--font-display);font-size:22px;font-weight:700;">${baslik || 'Pro Özelliği'}</h2>
        <p style="font-size:14px;color:var(--muted);max-width:400px;">${mesaj || 'Bu sayfa Pro plana özeldir.'}</p>
        <a href="fiyatlandirma_odeme_bolumu" class="btn-pro-upgrade">Pro'ya Geç — İlk 30 Gün Ücretsiz →</a>
      </div>
    `;
  }

  function clearCache() {
    _cache = null;
    _cacheTs = 0;
  }

  return { getPlan, isPro, lockElement, lockPage, clearCache };
})();
