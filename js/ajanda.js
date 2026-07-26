/**
 * Ajanda / Takvim görünümü — İhaleGlobal (26 Tem 2026)
 * takipte.html'de Liste|Takvim toggle. Takip edilen ihalelerin son_teklif_tarihi +
 * ihale_tarihi'ni aylık ızgaraya yerleştirir. Self-contained CSS-grid (dış lib YOK).
 * Veri: window.__takipIlanlar (takipte.html doldurur). ICS: kendi jeneratörü.
 */
(() => {
  const AYLAR = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
  const GUNLER = ['Pzt','Sal','Çar','Per','Cum','Cmt','Paz'];
  let simdiAy, kuruldu = false;
  const bugun = new Date(); bugun.setHours(0,0,0,0);

  const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
  const tl = (v) => v == null || v === 0 ? '' : '₺' + Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 0 });

  const stil = `
    .gorunum-toggle{display:inline-flex;background:var(--navy);border:1px solid var(--border);border-radius:8px;overflow:hidden}
    .gt-btn{background:none;border:none;color:var(--muted);font-size:12.5px;font-weight:600;padding:6px 13px;cursor:pointer;font-family:var(--font-body)}
    .gt-btn.aktif{background:rgba(240,165,0,.14);color:var(--amber)}
    .aj-bas{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding:0 4px}
    .aj-ay{font-size:16px;font-weight:800;color:var(--white)}
    .aj-gez{background:var(--navy);border:1px solid var(--border);color:var(--white);width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:16px}
    .aj-gez:hover{border-color:var(--amber);color:var(--amber)}
    .aj-bugun-btn{background:none;border:1px solid var(--border);color:var(--muted);font-size:12px;padding:5px 12px;border-radius:7px;cursor:pointer;font-family:var(--font-body);margin-left:8px}
    .aj-izgara{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}
    .aj-gunbas{text-align:center;font-size:11px;font-weight:700;color:var(--muted);padding:4px 0;text-transform:uppercase}
    .aj-hucre{min-height:74px;background:var(--navy);border:1px solid var(--border);border-radius:8px;padding:5px 6px;cursor:default;position:relative;overflow:hidden}
    .aj-hucre.bos{background:transparent;border-color:transparent}
    .aj-hucre.dolu{cursor:pointer}
    .aj-hucre.dolu:hover{border-color:var(--amber)}
    .aj-hucre.bugun{box-shadow:0 0 0 2px var(--amber) inset}
    .aj-gunno{font-size:12px;font-weight:600;color:var(--muted)}
    .aj-hucre.bugun .aj-gunno{color:var(--amber)}
    .aj-nokta{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}
    .aj-dot{width:100%;font-size:9.5px;line-height:1.2;padding:2px 4px;border-radius:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .aj-dot.son{background:rgba(240,165,0,.16);color:var(--amber)}
    .aj-dot.ihale{background:rgba(96,165,250,.16);color:#93c5fd}
    .aj-dot.gecti{background:var(--card-bg);color:var(--muted)}
    .aj-dot-fazla{font-size:9px;color:var(--muted)}
    .aj-panel{margin-top:14px;background:var(--navy);border:1px solid var(--border);border-radius:10px;padding:14px}
    .aj-panel-bas{font-size:13px;font-weight:700;color:var(--white);margin-bottom:10px}
    .aj-kart{display:flex;align-items:center;gap:10px;padding:9px 11px;border-bottom:1px solid var(--border)}
    .aj-kart:last-child{border-bottom:none}
    .aj-kart-tip{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px;flex-shrink:0}
    .aj-kart-tip.son{background:rgba(240,165,0,.16);color:var(--amber)}
    .aj-kart-tip.ihale{background:rgba(96,165,250,.16);color:#93c5fd}
    .aj-kart-orta{flex:1;min-width:0}
    .aj-kart-ad{font-size:13px;color:var(--white);text-decoration:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .aj-kart-ad:hover{color:var(--amber)}
    .aj-kart-alt{font-size:11px;color:var(--muted)}
    .aj-kart-ics{background:none;border:1px solid var(--border);color:var(--muted);font-size:11px;padding:3px 9px;border-radius:6px;cursor:pointer;font-family:var(--font-body);flex-shrink:0}
    .aj-kart-ics:hover{color:var(--amber);border-color:var(--amber)}
    .aj-bosay{text-align:center;color:var(--muted);font-size:13px;padding:30px}
    @media(max-width:600px){.aj-hucre{min-height:54px}.aj-dot{font-size:8.5px}}
  `;

  function isaretler() {
    const out = [];
    (window.__takipIlanlar || []).forEach(i => {
      if (i.son_teklif_tarihi) out.push({ d: new Date(i.son_teklif_tarihi), tip: 'son', ilan: i });
      if (i.ihale_tarihi && i.ihale_tarihi !== i.son_teklif_tarihi) out.push({ d: new Date(i.ihale_tarihi), tip: 'ihale', ilan: i });
    });
    return out.filter(x => !isNaN(x.d));
  }

  function render() {
    const kap = document.getElementById('ajanda-takvim');
    if (!kap) return;
    if (!simdiAy) { simdiAy = new Date(bugun.getFullYear(), bugun.getMonth(), 1); }
    const yil = simdiAy.getFullYear(), ay = simdiAy.getMonth();
    const marklar = isaretler();
    // güne göre grupla (yerel gün)
    const gunMap = {};
    marklar.forEach(m => {
      if (m.d.getFullYear() === yil && m.d.getMonth() === ay) {
        const g = m.d.getDate(); (gunMap[g] = gunMap[g] || []).push(m);
      }
    });
    const ilkGun = new Date(yil, ay, 1);
    let bosOn = (ilkGun.getDay() + 6) % 7;   // Pzt=0
    const gunSayisi = new Date(yil, ay + 1, 0).getDate();
    const toplamIsaret = Object.values(gunMap).reduce((a, v) => a + v.length, 0);

    let hucreler = '';
    for (let i = 0; i < bosOn; i++) hucreler += '<div class="aj-hucre bos"></div>';
    for (let g = 1; g <= gunSayisi; g++) {
      const bu = new Date(yil, ay, g); bu.setHours(0,0,0,0);
      const mlar = gunMap[g] || [];
      const buBugun = bu.getTime() === bugun.getTime();
      const noktalar = mlar.slice(0, 2).map(m => {
        const gecti = m.d < bugun;
        const sinif = gecti ? 'gecti' : m.tip;
        const et = m.tip === 'son' ? 'Son teklif' : 'İhale';
        return `<span class="aj-dot ${sinif}" title="${esc(m.ilan.baslik||'')}">${et}: ${esc((m.ilan.baslik||'').slice(0,18))}</span>`;
      }).join('');
      const fazla = mlar.length > 2 ? `<span class="aj-dot-fazla">+${mlar.length - 2} daha</span>` : '';
      hucreler += `<div class="aj-hucre ${mlar.length ? 'dolu' : ''} ${buBugun ? 'bugun' : ''}" ${mlar.length ? `data-gun="${g}"` : ''}>
        <div class="aj-gunno">${g}</div><div class="aj-nokta">${noktalar}${fazla}</div></div>`;
    }

    kap.innerHTML = `
      <div class="aj-bas">
        <div style="display:flex;align-items:center;">
          <button class="aj-gez" id="aj-onceki">‹</button>
          <span class="aj-ay" style="margin:0 12px;">${AYLAR[ay]} ${yil}</span>
          <button class="aj-gez" id="aj-sonraki">›</button>
          <button class="aj-bugun-btn" id="aj-bugun">Bugün</button>
        </div>
        <span style="font-size:12px;color:var(--muted);">${toplamIsaret ? toplamIsaret + ' işaretli ihale' : ''}</span>
      </div>
      ${toplamIsaret === 0 ? '<div class="aj-bosay">Bu ay işaretli ihale yok. ‹ › ile gezin veya ihale takip edin.</div>' :
        `<div class="aj-izgara">${GUNLER.map(g => `<div class="aj-gunbas">${g}</div>`).join('')}${hucreler}</div>`}
      <div id="aj-panel"></div>`;

    document.getElementById('aj-onceki').onclick = () => { simdiAy = new Date(yil, ay - 1, 1); render(); };
    document.getElementById('aj-sonraki').onclick = () => { simdiAy = new Date(yil, ay + 1, 1); render(); };
    document.getElementById('aj-bugun').onclick = () => { simdiAy = new Date(bugun.getFullYear(), bugun.getMonth(), 1); render(); };
    kap.querySelectorAll('.aj-hucre.dolu').forEach(h => h.onclick = () => gunPanel(+h.dataset.gun, gunMap[+h.dataset.gun] || [], yil, ay));
  }

  function gunPanel(gun, mlar, yil, ay) {
    const p = document.getElementById('aj-panel');
    if (!p) return;
    p.innerHTML = `<div class="aj-panel">
      <div class="aj-panel-bas">${gun} ${AYLAR[ay]} ${yil} — ${mlar.length} ihale</div>
      ${mlar.map(m => {
        const i = m.ilan, et = m.tip === 'son' ? 'Son teklif' : 'İhale günü';
        const mal = i.yaklasik_maliyet_max || i.yaklasik_maliyet_min || i.tahmini_bedel;
        return `<div class="aj-kart">
          <span class="aj-kart-tip ${m.tip}">${et}</span>
          <div class="aj-kart-orta">
            <a class="aj-kart-ad" href="ihale-detay?id=${i.id}">${esc(i.baslik || '—')}</a>
            <div class="aj-kart-alt">${esc(i.idare || i.il || '')}${mal ? ' · ' + tl(mal) : ''}</div>
          </div>
          <button class="aj-kart-ics" data-id="${i.id}" data-tarih="${m.d.toISOString()}" data-baslik="${esc(i.baslik||'')}">📅 .ics</button>
        </div>`;
      }).join('')}
    </div>`;
    p.querySelectorAll('.aj-kart-ics').forEach(b => b.onclick = () => icsIndir(b.dataset.tarih, b.dataset.baslik, b.dataset.id));
    p.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function icsIndir(tarih, baslik, id) {
    const d = new Date(tarih), pad = (n) => String(n).padStart(2, '0');
    const dt = d.getUTCFullYear() + pad(d.getUTCMonth()+1) + pad(d.getUTCDate()) + 'T' + pad(d.getUTCHours()) + pad(d.getUTCMinutes()) + '00Z';
    const ics = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//ihaleglobal//TR','BEGIN:VEVENT','UID:' + id + '@ihaleglobal.com',
      'DTSTART:' + dt, 'SUMMARY:' + (baslik || 'İhale').replace(/[,;\\]/g,' ').slice(0,80),
      'DESCRIPTION:https://ihaleglobal.com/ihale-detay?id=' + id, 'END:VEVENT','END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = document.createElement('a'); a.href = url; a.download = 'ihale-' + String(id).slice(0,8) + '.ics';
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  window.gorunumSec = function (mod) {
    const liste = document.getElementById('gorunum-liste'), takvim = document.getElementById('ajanda-takvim');
    const bL = document.getElementById('gt-liste'), bT = document.getElementById('gt-takvim');
    if (!liste || !takvim) return;
    if (mod === 'takvim') {
      liste.style.display = 'none'; takvim.style.display = 'block';
      bL.classList.remove('aktif'); bT.classList.add('aktif');
      render();
    } else {
      liste.style.display = 'block'; takvim.style.display = 'none';
      bT.classList.remove('aktif'); bL.classList.add('aktif');
    }
  };

  const s = document.createElement('style'); s.textContent = stil;
  (document.readyState === 'loading') ? document.addEventListener('DOMContentLoaded', () => document.head.appendChild(s)) : document.head.appendChild(s);
  // Veri gelince, takvim görünümü açıksa tazele
  document.addEventListener('takip-veri-hazir', () => { const t = document.getElementById('ajanda-takvim'); if (t && t.style.display !== 'none') render(); });
})();
