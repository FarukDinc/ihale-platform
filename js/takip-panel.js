/**
 * Takip Listem paneli — İhaleGlobal (26 Tem 2026)
 * Dashboard'da: takip firma/kurum/sektör sayıları + Yeni Ekle modalı +
 * takip edilen firmaların son sözleşmeleri. Backend: takip_ozet / takip_firma_sozlesmeleri
 * + takip_firmalar/takip_idareler/takip_sektorler (migration_takip_sektorler.sql).
 */
(() => {
  const SB_URL = "https://ihaleglobal.com";
  const SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso";
  let sb, panel;

  const tl = (v) => v == null || v === 0 ? '—' : '₺' + Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 0 });
  const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const gunAy = (t) => t ? new Date(t).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
  const trFold = (s) => (s || '').toLocaleLowerCase('tr').replace(/i̇/g,'i').replace(/[ıi]/g,'i').replace(/ç/g,'c').replace(/ğ/g,'g').replace(/ö/g,'o').replace(/ş/g,'s').replace(/ü/g,'u');

  const stil = `
    .tp-kart{background:var(--navy-mid);border:1px solid var(--border);border-radius:14px;padding:18px 20px;margin-bottom:18px}
    .tp-bas{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px}
    .tp-bas-sol{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:800;color:var(--white)}
    .tp-bas-sol svg{color:var(--amber)}
    .tp-gor{font-size:12.5px;color:var(--muted);text-decoration:none}
    .tp-gor:hover{color:var(--amber)}
    .tp-sayaclar{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
    .tp-say{background:var(--navy);border:1px solid var(--border);border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:11px}
    .tp-say-ik{width:36px;height:36px;border-radius:9px;background:rgba(240,165,0,.12);color:var(--amber);display:flex;align-items:center;justify-content:center;flex-shrink:0}
    .tp-say-n{font-size:20px;font-weight:800;color:var(--white);line-height:1}
    .tp-say-l{font-size:11.5px;color:var(--muted);margin-top:2px}
    .tp-ekle{background:rgba(240,165,0,.12);border:1px solid var(--amber);color:var(--amber);font-size:12.5px;font-weight:700;padding:7px 14px;border-radius:8px;cursor:pointer;font-family:var(--font-body)}
    .tp-altbas{font-size:12.5px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
    .tp-soz{display:flex;flex-direction:column;gap:6px}
    .tp-soz-sat{display:flex;align-items:center;gap:10px;background:var(--navy);border:1px solid var(--border);border-radius:9px;padding:10px 13px;text-decoration:none;color:inherit;transition:border-color .15s}
    .tp-soz-sat:hover{border-color:var(--amber)}
    .tp-soz-ik{color:#4ade80;flex-shrink:0}
    .tp-soz-orta{flex:1;min-width:0}
    .tp-soz-firma{font-size:13px;font-weight:700;color:var(--white);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .tp-soz-is{font-size:11.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .tp-soz-sag{text-align:right;flex-shrink:0}
    .tp-soz-bedel{font-size:13px;font-weight:700;color:var(--amber)}
    .tp-soz-tarih{font-size:11px;color:var(--muted)}
    .tp-bos,.tp-yuk{text-align:center;color:var(--muted);font-size:12.5px;padding:18px}
    .tp-rozet-fesih{font-size:10px;background:rgba(239,68,68,.15);color:#fca5a5;padding:1px 6px;border-radius:8px;margin-left:6px}
    /* modal */
    .tp-modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px}
    .tp-modal{background:var(--navy-mid);border:1px solid var(--border);border-radius:14px;width:100%;max-width:460px;max-height:86vh;overflow:hidden;display:flex;flex-direction:column}
    .tp-modal-bas{display:flex;align-items:center;justify-content:space-between;padding:15px 18px;border-bottom:1px solid var(--border);font-weight:800;color:var(--white)}
    .tp-modal-kapat{background:none;border:none;color:var(--muted);font-size:20px;cursor:pointer;line-height:1}
    .tp-sekmeler{display:flex;gap:0;border-bottom:1px solid var(--border)}
    .tp-sekme{flex:1;background:none;border:none;border-bottom:2px solid transparent;color:var(--muted);font-size:13px;font-weight:600;padding:11px;cursor:pointer;font-family:var(--font-body)}
    .tp-sekme.aktif{color:var(--amber);border-bottom-color:var(--amber)}
    .tp-modal-govde{padding:16px 18px;overflow-y:auto}
    .tp-arama{width:100%;background:var(--navy);border:1px solid var(--border);border-radius:8px;padding:10px 13px;color:var(--white);font-size:14px;font-family:var(--font-body);outline:none;margin-bottom:10px}
    .tp-arama:focus{border-color:var(--amber)}
    .tp-secim{display:flex;flex-direction:column;gap:4px;max-height:300px;overflow-y:auto}
    .tp-oge{display:flex;align-items:center;justify-content:space-between;gap:8px;background:var(--navy);border:1px solid var(--border);border-radius:7px;padding:8px 11px;cursor:pointer;text-align:left;font-family:var(--font-body)}
    .tp-oge:hover{border-color:var(--muted)}
    .tp-oge-ad{font-size:12.5px;color:var(--white);flex:1;min-width:0}
    .tp-oge-ekli{color:#4ade80;font-size:11px;font-weight:700}
    .tp-oge-arti{color:var(--amber);font-size:16px}
    @media (max-width:640px){.tp-sayaclar{grid-template-columns:1fr}}
  `;

  async function init() {
    panel = document.getElementById('takip-panel');
    if (!panel || !window.supabase) return;
    sb = window.supabase.createClient(SB_URL, SB_KEY);
    const { data } = await sb.auth.getSession();
    if (!data || !data.session) { panel.style.display = 'none'; return; }
    panel.style.display = 'block';
    const s = document.createElement('style'); s.textContent = stil; document.head.appendChild(s);
    await render();
  }

  async function render() {
    panel.innerHTML = `
      <div class="tp-kart">
        <div class="tp-bas">
          <div class="tp-bas-sol">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10a1 1 0 011 1v15l-6-4-6 4V5a1 1 0 011-1z"/></svg>
            Takip Listem
          </div>
          <a class="tp-gor" href="takipte">Tümünü Gör →</a>
        </div>
        <div class="tp-sayaclar" id="tp-sayaclar"></div>
        <div style="display:flex;justify-content:flex-end;margin-bottom:14px;">
          <button class="tp-ekle" id="tp-ekle-btn">⊕ Yeni Ekle</button>
        </div>
        <div class="tp-altbas">Takip ettiğim firmaların son sözleşmeleri</div>
        <div class="tp-soz" id="tp-soz"><div class="tp-yuk">Yükleniyor…</div></div>
      </div>`;
    document.getElementById('tp-ekle-btn').addEventListener('click', modalAc);
    ozetYukle(); sozlesmeYukle();
  }

  async function ozetYukle() {
    const { data } = await sb.rpc('takip_ozet');
    const o = data || {};
    const kart = (n, l, ikon) => `<div class="tp-say"><span class="tp-say-ik">${ikon}</span><div><div class="tp-say-n">${(n||0).toLocaleString('tr-TR')}</div><div class="tp-say-l">${l}</div></div></div>`;
    document.getElementById('tp-sayaclar').innerHTML =
      kart(o.firma, 'Takip Firma', '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 21V4a1 1 0 011-1h8a1 1 0 011 1v17M15 9h3a1 1 0 011 1v11M3 21h18"/></svg>')
    + kart(o.idare, 'Takip Kurum', '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18M5 21V10M10 21V10M14 21V10M19 21V10M4 10l8-6 8 6"/></svg>')
    + kart(o.sektor, 'Takip Sektör', '<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/></svg>');
  }

  async function sozlesmeYukle() {
    const { data, error } = await sb.rpc('takip_firma_sozlesmeleri', { p_limit: 6 });
    const wrap = document.getElementById('tp-soz');
    if (error) { wrap.innerHTML = '<div class="tp-bos">Yüklenemedi.</div>'; return; }
    if (!data || !data.length) {
      wrap.innerHTML = '<div class="tp-bos">Takip ettiğiniz firmaların yeni sözleşmesi yok. Firma ekleyerek yeni işlerini burada görün.</div>'; return;
    }
    wrap.innerHTML = data.map(s => {
      const bedel = s.sozlesme_bedeli || s.kazanan_teklif;
      const risk = (s.fesih_var || s.tasfiye_var) ? `<span class="tp-rozet-fesih">${s.fesih_var ? 'fesih' : 'tasfiye'}</span>` : '';
      const href = s.ilan_id ? 'ihale-detay?id=' + s.ilan_id : 'firma-analiz?ara=' + encodeURIComponent(s.takip_firma || '');
      return `<a class="tp-soz-sat" href="${href}">
        <span class="tp-soz-ik"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v4a5 5 0 01-10 0z"/><path d="M9 16h6v4H9zM12 13v3"/></svg></span>
        <div class="tp-soz-orta">
          <div class="tp-soz-firma">${esc(s.kazanan_firma || s.takip_firma)}${risk}</div>
          <div class="tp-soz-is">${esc(s.baslik || s.kategori || '—')}${s.il ? ' · ' + esc(s.il) : ''}</div>
        </div>
        <div class="tp-soz-sag"><div class="tp-soz-bedel">${tl(bedel)}</div><div class="tp-soz-tarih">${gunAy(s.sonuc_tarihi)}</div></div>
      </a>`;
    }).join('');
  }

  // ── Yeni Ekle modalı ──
  let aktifSekme = 'firma';
  function modalAc() {
    const bg = document.createElement('div'); bg.className = 'tp-modal-bg'; bg.id = 'tp-modal-bg';
    bg.innerHTML = `
      <div class="tp-modal" onclick="event.stopPropagation()">
        <div class="tp-modal-bas">Takip Listeme Ekle <button class="tp-modal-kapat" id="tp-mk">×</button></div>
        <div class="tp-sekmeler">
          <button class="tp-sekme aktif" data-s="firma">Firma</button>
          <button class="tp-sekme" data-s="idare">Kurum</button>
          <button class="tp-sekme" data-s="sektor">Sektör</button>
        </div>
        <div class="tp-modal-govde" id="tp-modal-govde"></div>
      </div>`;
    bg.addEventListener('click', modalKapat);
    document.body.appendChild(bg);
    document.getElementById('tp-mk').addEventListener('click', modalKapat);
    bg.querySelectorAll('.tp-sekme').forEach(b => b.addEventListener('click', () => {
      bg.querySelectorAll('.tp-sekme').forEach(x => x.classList.remove('aktif')); b.classList.add('aktif');
      aktifSekme = b.dataset.s; sekmeGoster();
    }));
    aktifSekme = 'firma'; sekmeGoster();
  }
  function modalKapat() { const b = document.getElementById('tp-modal-bg'); if (b) b.remove(); render(); }

  function sekmeGoster() {
    const g = document.getElementById('tp-modal-govde');
    if (aktifSekme === 'sektor') {
      const kats = (window.KATEGORILER || []).map(k => k.kod);
      g.innerHTML = `<div class="tp-secim" id="tp-secim"></div>`;
      sektorListe(kats);
      return;
    }
    const ph = aktifSekme === 'firma' ? 'Firma adı ara…' : 'Kurum/idare ara…';
    g.innerHTML = `<input type="text" class="tp-arama" id="tp-arama" placeholder="${ph}" autocomplete="off"><div class="tp-secim" id="tp-secim"></div>`;
    const inp = document.getElementById('tp-arama'); let t;
    inp.addEventListener('input', () => { clearTimeout(t); const q = inp.value.trim(); if (q.length < 2) { document.getElementById('tp-secim').innerHTML = ''; return; } t = setTimeout(() => araGetir(q), 280); });
    inp.focus();
  }

  async function araGetir(q) {
    const secim = document.getElementById('tp-secim');
    const fold = trFold(q);
    if (aktifSekme === 'firma') {
      let { data } = await sb.from('yukleniciler').select('ad').ilike('arama_fold', '%' + fold + '%').order('toplam_ciro', { ascending: false, nullsFirst: false }).limit(10);
      if (!data || !data.length) ({ data } = await sb.from('yukleniciler').select('ad').ilike('ad', '%' + q + '%').limit(10));
      ogeListe(secim, (data || []).map(f => f.ad), 'firma');
    } else {
      // idare: ilanlar'dan benzersiz idare adları (kurum-analiz deseni yerine hafif)
      const { data } = await sb.from('ilanlar').select('idare').ilike('idare', '%' + q + '%').not('idare', 'is', null).limit(30);
      const uniq = [...new Set((data || []).map(r => r.idare))].slice(0, 10);
      ogeListe(secim, uniq, 'idare');
    }
  }

  async function ekliSet(tablo, kolon) {
    const { data } = await sb.from(tablo).select(kolon);
    return new Set((data || []).map(r => trFold(r[kolon])));
  }

  async function ogeListe(secim, adlar, tur) {
    const tablo = tur === 'firma' ? 'takip_firmalar' : 'takip_idareler';
    const kolon = tur === 'firma' ? 'firma_ad' : 'idare_ad';
    const ekli = await ekliSet(tablo, kolon);
    secim.innerHTML = adlar.length ? adlar.map(ad =>
      `<button class="tp-oge" data-kad="${esc(ad)}" data-tur="${tur}"><span class="tp-oge-ad">${esc(ad)}</span><span class="${ekli.has(trFold(ad)) ? 'tp-oge-ekli' : 'tp-oge-arti'}">${ekli.has(trFold(ad)) ? '✓ ekli' : '+'}</span></button>`
    ).join('') : '<div class="tp-bos">Sonuç yok</div>';
    secim.querySelectorAll('.tp-oge').forEach(b => b.addEventListener('click', () => ekleToggle(b, tur)));
  }

  async function sektorListe(kats) {
    const ekli = await ekliSet('takip_sektorler', 'sektor');
    const secim = document.getElementById('tp-secim');
    secim.innerHTML = kats.map(k =>
      `<button class="tp-oge" data-kad="${esc(k)}" data-tur="sektor"><span class="tp-oge-ad">${esc(k)}</span><span class="${ekli.has(trFold(k)) ? 'tp-oge-ekli' : 'tp-oge-arti'}">${ekli.has(trFold(k)) ? '✓ ekli' : '+'}</span></button>`
    ).join('');
    secim.querySelectorAll('.tp-oge').forEach(b => b.addEventListener('click', () => ekleToggle(b, 'sektor')));
  }

  async function ekleToggle(btn, tur) {
    const ad = btn.dataset.kad;
    const tablo = tur === 'firma' ? 'takip_firmalar' : tur === 'idare' ? 'takip_idareler' : 'takip_sektorler';
    const kolon = tur === 'firma' ? 'firma_ad' : tur === 'idare' ? 'idare_ad' : 'sektor';
    const rozet = btn.querySelector('span:last-child');
    const zatenEkli = rozet.textContent.includes('ekli');
    const { data: { session } } = await sb.auth.getSession();
    if (zatenEkli) {
      await sb.from(tablo).delete().eq(kolon, ad).eq('kullanici_id', session.user.id);
      rozet.className = 'tp-oge-arti'; rozet.textContent = '+';
    } else {
      await sb.from(tablo).insert({ [kolon]: ad, kullanici_id: session.user.id });
      rozet.className = 'tp-oge-ekli'; rozet.textContent = '✓ ekli';
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
