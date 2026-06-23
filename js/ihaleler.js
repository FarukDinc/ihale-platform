/**
 * İhaleler Listesi Sayfası
 * ihaleler.html'e ekle:
 *   <script src="/js/ihaleler.js"></script>
 */

document.addEventListener("DOMContentLoaded", async () => {

    const el = {
        liste:        document.getElementById("ihale-listesi"),
        arama:        document.getElementById("arama-input"),
        il_filtre:    document.getElementById("il-filtre"),
        tur_filtre:   document.getElementById("tur-filtre"),
        filtrele_btn: document.getElementById("filtrele-btn"),
        temizle_btn:  document.getElementById("temizle-btn"),
        onceki_btn:   document.getElementById("onceki-sayfa"),
        sonraki_btn:  document.getElementById("sonraki-sayfa"),
        sayfa_no:     document.getElementById("sayfa-no"),
        toplam_text:  document.getElementById("toplam-ihale")
    };

    let mevcut_sayfa = 1;
    const BOYUT = 20;

    // ── İhale listesini yükle ────────────────────────────
    async function liste_yukle() {
        if (!el.liste) return;

        UI.yukleniyor_goster(el.liste, "İhaleler aranıyor...");

        const sonuc = await API.ihaleler.listele({
            il:    el.il_filtre?.value   || undefined,
            tur:   el.tur_filtre?.value  || undefined,
            arama: el.arama?.value       || undefined,
            sayfa: mevcut_sayfa,
            boyut: BOYUT
        });

        if (!sonuc?.veri?.length) {
            UI.bos_durum_goster(el.liste, "Arama kriterlerinize uygun ihale bulunamadı.", "🔍");
            return;
        }

        if (el.toplam_text) {
            el.toplam_text.textContent = `${sonuc.veri.length} ihale listeleniyor`;
        }
        if (el.sayfa_no) {
            el.sayfa_no.textContent = `Sayfa ${mevcut_sayfa}`;
        }

        el.liste.innerHTML = sonuc.veri.map(ihale => `
            <div class="ihale-satir" style="
                display:grid;
                grid-template-columns: 1fr auto;
                gap: 16px;
                padding: 18px;
                border-bottom: 1px solid #f1f5f9;
                align-items: center;
                transition: background 0.15s;
                cursor: pointer;
            "
            onmouseenter="this.style.background='#fafafa'"
            onmouseleave="this.style.background='white'"
            onclick="window.location.href='/ihale-detay.html?id=${ihale.id}'">

                <div>
                    <div style="font-weight:600;font-size:14px;color:#0A1628;margin-bottom:5px">
                        ${ihale.baslik || "İsimsiz"}
                    </div>
                    <div style="font-size:12px;color:#64748b;display:flex;gap:12px;flex-wrap:wrap">
                        <span>🏛️ ${ihale.idare || "—"}</span>
                        <span>📍 ${ihale.il || "—"}</span>
                        <span>📋 ${ihale.tur || "—"}</span>
                        <span>📅 ${UI.tarih_formatla(ihale.ihale_tarihi)}</span>
                    </div>
                </div>

                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
                    <span style="font-size:11px;color:#94a3b8;
                        background:#f8fafc;padding:3px 8px;border-radius:4px">
                        ${ihale.ikn || ""}
                    </span>
                    <div style="display:flex;align-items:center;gap:6px">
                        ${UI.kalan_gun(ihale.ihale_tarihi) || ""}
                        ${ihale.analiz_tarihi
                            ? '<span style="font-size:11px;color:#10b981">✅ Analiz</span>'
                            : ""
                        }
                    </div>
                    <button onclick="event.stopPropagation();takibe_al('${ihale.id}', this)"
                        style="font-size:11px;padding:4px 10px;border-radius:5px;
                            border:1px solid #e2e8f0;background:white;cursor:pointer;
                            color:#475569">
                        ⭐ Takip
                    </button>
                </div>
            </div>
        `).join("");
    }

    // ── Filtrele ────────────────────────────────────────
    el.filtrele_btn?.addEventListener("click", () => {
        mevcut_sayfa = 1;
        liste_yukle();
    });

    el.arama?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            mevcut_sayfa = 1;
            liste_yukle();
        }
    });

    // ── Temizle ─────────────────────────────────────────
    el.temizle_btn?.addEventListener("click", () => {
        if (el.arama)     el.arama.value = "";
        if (el.il_filtre) el.il_filtre.value = "";
        if (el.tur_filtre) el.tur_filtre.value = "";
        mevcut_sayfa = 1;
        liste_yukle();
    });

    // ── Sayfalama ────────────────────────────────────────
    el.onceki_btn?.addEventListener("click", () => {
        if (mevcut_sayfa > 1) {
            mevcut_sayfa--;
            liste_yukle();
            window.scrollTo(0, 0);
        }
    });

    el.sonraki_btn?.addEventListener("click", () => {
        mevcut_sayfa++;
        liste_yukle();
        window.scrollTo(0, 0);
    });

    // ── Global takip fonksiyonu ──────────────────────────
    window.takibe_al = async (ihale_id, btn) => {
        if (!API.auth.girisli_mi()) {
            UI.bildirim_goster("Takip için giriş yapın", "uyari");
            return;
        }
        btn.textContent = "⏳";
        const sonuc = await API.takipler.ekle(ihale_id);
        if (sonuc?.basari) {
            btn.textContent = "✅";
            btn.style.color = "#10b981";
            UI.bildirim_goster("Takibe alındı!", "basari");
        } else {
            btn.textContent = "⭐ Takip";
        }
    };

    // İlk yükleme
    liste_yukle();
});
