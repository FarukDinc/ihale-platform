/**
 * Benim Firmam → Kişisel Eşleşme — İhaleGlobal (26 Tem 2026)
 * Kullanıcı firmasını seçer → geçmiş kazanımlarına benzer AKTİF ihaleleri getirir.
 * Backend: firmami_belirle / firmam_getir / firmam_acik_ihaleler (migration_firmam_eslesme.sql).
 * Yeniden kullanır: yukleniciler autocomplete, takvimeEkle (ICS), Takip (js/takip.js), TUFE (js/tufe.js).
 * Dashboard'da #firmam-blok içine render eder; login yoksa gizli kalır.
 */
(() => {
  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";
  let sb, blok, secili = null;

  const trFold = (s) => (s || '').toLocaleLowerCase('tr').replace(/[İ]/g,'i').replace(/[ı]/g,'i')
    .replace(/ç/g,'c').replace(/ğ/g,'g').replace(/ö/g,'o').replace(/ş/g,'s').replace(/ü/g,'u');
  const tl = (v) => v == null ? '—' : '₺' + Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 0 });
  const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const kalanGun = (t) => { if (!t) return null; const g = Math.ceil((new Date(t) - Date.now())/86400000); return g; };

  async function init() {
    blok = document.getElementById('firmam-blok');
    if (!blok || !window.supabase) return;
    sb = window.supabase.createClient(SB_URL, SB_KEY);
    const { data } = await sb.auth.getSession();
    if (!data || !data.session) { blok.style.display = 'none'; return; }   // yalnız üyeye
    blok.style.display = 'block';
    await durumYukle();
  }

  async function durumYukle() {
    // localStorage cache → hızlı ilk boya, sonra sunucudan teyit
    let f = null;
    try { const c = localStorage.getItem('firmam'); if (c) f = JSON.parse(c); } catch (_) {}
    if (f) renderEslesme(f);
    const { data, error } = await sb.rpc('firmam_getir');
    if (error) { if (!f) renderOnboarding(); return; }
    if (data && data.firma_id) {
      localStorage.setItem('firmam', JSON.stringify(data));
      if (!f || f.firma_id !== data.firma_id) renderEslesme(data);
    } else {
      localStorage.removeItem('firmam'); renderOnboarding();
    }
  }

  // ── Onboarding: firma seçilmemiş ──
  function renderOnboarding() {
    blok.innerHTML = `
      <div class="firmam-kart firmam-onboarding">
        <div class="firmam-ob-ikon">
          <svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4a1 1 0 011-1h8a1 1 0 011 1v17"/><path d="M15 9h3a1 1 0 011 1v11"/><path d="M8 7h1M12 7h1M8 11h1M12 11h1M8 15h1M12 15h1"/><path d="M3 21h18"/></svg>
        </div>
        <div class="firmam-ob-govde">
          <div class="firmam-ob-baslik">Firmanızı belirleyin, size özel ihaleleri getirelim</div>
          <div class="firmam-ob-alt">Firmanızı seçin; geçmiş kamu kazanımlarınıza benzeyen açık ihaleleri otomatik bulalım.</div>
          <div class="firmam-ac-wrap">
            <input type="text" id="firmam-ac-input" class="firmam-ac-input" placeholder="Firma adı ara…" autocomplete="off">
            <div id="firmam-ac-liste" class="firmam-ac-liste"></div>
          </div>
        </div>
      </div>`;
    acBagla();
  }

  // ── Firma autocomplete ──
  function acBagla() {
    const inp = document.getElementById('firmam-ac-input');
    const liste = document.getElementById('firmam-ac-liste');
    let t;
    inp.addEventListener('input', () => {
      clearTimeout(t); const q = inp.value.trim();
      if (q.length < 2) { liste.innerHTML = ''; return; }
      t = setTimeout(() => araGetir(q, liste), 280);
    });
    document.addEventListener('click', (e) => { if (!e.target.closest('.firmam-ac-wrap')) liste.innerHTML = ''; });
  }

  async function araGetir(q, liste) {
    const fold = trFold(q);
    let { data } = await sb.from('yukleniciler')
      .select('id,ad,il,toplam_sozlesme_sayisi,toplam_ciro')
      .ilike('arama_fold', '%' + fold + '%')
      .order('toplam_ciro', { ascending: false, nullsFirst: false }).limit(8);
    if (!data || !data.length) {
      ({ data } = await sb.from('yukleniciler').select('id,ad,il,toplam_sozlesme_sayisi,toplam_ciro')
        .ilike('ad', '%' + q + '%').limit(8));
    }
    if (!data || !data.length) { liste.innerHTML = '<div class="firmam-ac-bos">Firma bulunamadı</div>'; return; }
    liste.innerHTML = data.map(f => `
      <button class="firmam-ac-item" data-id="${f.id}" data-kad="${esc(f.ad)}" data-il="${esc(f.il||'')}"
        data-ciro="${f.toplam_ciro||0}" data-say="${f.toplam_sozlesme_sayisi||0}">
        <span class="firmam-ac-ad">${esc(f.ad)}</span>
        <span class="firmam-ac-meta">${esc(f.il||'—')} · ${(f.toplam_sozlesme_sayisi||0).toLocaleString('tr-TR')} sözleşme</span>
      </button>`).join('');
    liste.querySelectorAll('.firmam-ac-item').forEach(b => b.addEventListener('click', () => firmaSec(b.dataset)));
  }

  async function firmaSec(d) {
    const f = { firma_id: d.id, ad: d.ad, il: d.il, toplam_ciro: +d.ciro, toplam_sozlesme_sayisi: +d.say };
    blok.innerHTML = '<div class="firmam-kart" style="text-align:center;color:var(--muted);padding:30px;">Firmanız kaydediliyor…</div>';
    const { error } = await sb.rpc('firmami_belirle', { p_yuklenici_id: d.id });
    if (error) { blok.innerHTML = '<div class="firmam-kart" style="color:#e05260;padding:20px;">Kaydedilemedi. Tekrar deneyin.</div>'; setTimeout(renderOnboarding, 1800); return; }
    localStorage.setItem('firmam', JSON.stringify(f));
    renderEslesme(f);
  }

  // ── Eşleşme bloğu: firma seçili ──
  async function renderEslesme(f) {
    secili = f;
    blok.innerHTML = `
      <div class="firmam-kart">
        <div class="firmam-hero">
          <div>
            <div class="firmam-eyebrow">Sizin için</div>
            <div class="firmam-baslik">Katılabileceğiniz İhaleleri Bulduk</div>
            <div class="firmam-firma">
              <span class="firmam-rozet">${esc(f.ad)}</span>
              <span class="firmam-firma-meta">${esc(f.il||'')} · ${(f.toplam_sozlesme_sayisi||0).toLocaleString('tr-TR')} kazanım · ${tl(f.toplam_ciro)}</span>
              <button class="firmam-degistir" id="firmam-degistir">Firmayı değiştir</button>
            </div>
          </div>
        </div>
        <div id="firmam-sonuc" class="firmam-grid"><div class="firmam-yukleniyor">Firmanıza uygun açık ihaleler taranıyor…</div></div>
      </div>`;
    document.getElementById('firmam-degistir').addEventListener('click', firmaDegistir);
    const { data, error } = await sb.rpc('firmam_acik_ihaleler', { p_limit: 12 });
    const wrap = document.getElementById('firmam-sonuc');
    if (error) { wrap.innerHTML = '<div class="firmam-yukleniyor" style="color:#e05260;">Eşleşme alınamadı.</div>'; return; }
    if (!data || !data.length) {
      wrap.innerHTML = '<div class="firmam-bos">Firmanızın profiline uyan açık ihale şu an yok. Yeni ihale gelince bildireceğiz. 🔔</div>';
      return;
    }
    wrap.innerHTML = data.map(kart).join('');
    wrap.querySelectorAll('[data-takvim]').forEach(b => b.addEventListener('click', (e) => {
      e.preventDefault();
      takvimeEkleICS(b.dataset.tarih, b.dataset.baslik, b.dataset.takvim);
    }));
  }

  function kart(i) {
    const mal = i.yaklasik_maliyet_max || i.yaklasik_maliyet_min || i.tahmini_bedel;
    const bugunku = (window.TUFE && mal && i.son_teklif_tarihi) ? null : null; // aktif ihale → nominal yeterli
    const kg = kalanGun(i.son_teklif_tarihi);
    const kgMetin = kg == null ? '' : kg < 0 ? 'Süre doldu' : kg === 0 ? 'Bugün son' : kg + ' gün kaldı';
    const kgSinif = kg != null && kg <= 3 ? 'firmam-kalan-acil' : 'firmam-kalan';
    return `
      <a class="firmam-ihale" href="ihale-detay?id=${i.id}">
        <div class="firmam-ihale-ust">
          <span class="firmam-skor" title="Eşleşme skoru">%${Math.min(99, Math.round((i.skor||0)))}</span>
          ${kg != null ? `<span class="${kgSinif}">${kgMetin}</span>` : ''}
        </div>
        <div class="firmam-ihale-baslik">${esc(i.baslik || '—')}</div>
        <div class="firmam-ihale-idare">${esc(i.idare || '—')}</div>
        <div class="firmam-ihale-alt">
          ${i.kategori ? `<span class="firmam-cip">${esc(i.kategori)}</span>` : ''}
          ${i.il ? `<span class="firmam-il">${esc(i.il)}</span>` : ''}
          ${mal ? `<span class="firmam-mal">${tl(mal)}</span>` : ''}
        </div>
        <div class="firmam-neden">${esc(i.eslesme_nedeni || '')}</div>
        ${i.son_teklif_tarihi ? `<button class="firmam-takvim" data-takvim="${i.id}" data-tarih="${i.son_teklif_tarihi}" data-baslik="${esc(i.baslik||'')}" title="Takvime ekle">📅 Takvime Ekle</button>` : ''}
      </a>`;
  }

  // Kendi ICS jeneratörü (dashboard'da global takvimeEkle yok)
  function takvimeEkleICS(tarih, baslik, id) {
    if (!tarih) return;
    const d = new Date(tarih);
    const pad = (n) => String(n).padStart(2, '0');
    const dt = d.getUTCFullYear() + pad(d.getUTCMonth()+1) + pad(d.getUTCDate()) + 'T' + pad(d.getUTCHours()) + pad(d.getUTCMinutes()) + '00Z';
    const ics = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//ihaleglobal//TR','BEGIN:VEVENT',
      'UID:' + id + '@ihaleglobal.com', 'DTSTART:' + dt,
      'SUMMARY:Son teklif — ' + (baslik || 'İhale').replace(/[,;\\]/g,' ').slice(0,80),
      'DESCRIPTION:İhaleGlobal · https://ihaleglobal.com/ihale-detay?id=' + id,
      'END:VEVENT','END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = document.createElement('a'); a.href = url; a.download = 'ihale-' + id.slice(0,8) + '.ics';
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  async function firmaDegistir() {
    await sb.rpc('firmami_belirle', { p_yuklenici_id: null });
    localStorage.removeItem('firmam');
    renderOnboarding();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
