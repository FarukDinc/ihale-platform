/**
 * Dashboard sayfası — gerçek data bağlantısı
 * dashboard.html'e ekle:
 *   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 *   <script src="/js/api.js"></script>
 *   <script src="/js/ui.js"></script>
 *   <script src="/js/dashboard.js"></script>
 */

document.addEventListener("DOMContentLoaded", async () => {

    // Auth kontrolü
    if (!API.auth.girisli_mi()) {
        window.location.href = "/login";
        return;
    }

    // Elementler
    const el = {
        firma_adi:      document.getElementById("firma-adi"),
        kalan_kredi:    document.getElementById("kalan-kredi"),
        plan_adi:       document.getElementById("plan-adi"),
        toplam_ihale:   document.getElementById("toplam-ihale"),
        takip_sayisi:   document.getElementById("takip-sayisi"),
        analiz_sayisi:  document.getElementById("analiz-sayisi"),
        ihale_listesi:  document.getElementById("ihale-listesi"),
        bildirim_liste: document.getElementById("bildirim-listesi"),
        bildirim_rozet: document.getElementById("bildirim-rozet"),
        cikis_btn:      document.getElementById("cikis-btn")
    };

    // ── Çıkış ──────────────────────────────────────────
    el.cikis_btn?.addEventListener("click", () => API.auth.cikis());

    // ── Profil + Kredi ──────────────────────────────────
    async function profil_yukle() {
        const sonuc = await API.profil.getir();
        if (!sonuc) return;

        const { profil, kredi } = sonuc;

        if (el.firma_adi)   el.firma_adi.textContent = profil.firma_adi || "Firma";
        if (el.kalan_kredi) el.kalan_kredi.textContent = kredi.kalan_kredi;
        if (el.plan_adi)    el.plan_adi.textContent = kredi.plan?.toUpperCase() || "FREE";
    }

    // ── Son ihaleler ────────────────────────────────────
    async function ihaleler_yukle() {
        if (!el.ihale_listesi) return;

        UI.yukleniyor_goster(el.ihale_listesi, "İhaleler yükleniyor...");

        const sonuc = await API.ihaleler.listele({ boyut: 10 });

        if (!sonuc || !sonuc.veri?.length) {
            UI.bos_durum_goster(el.ihale_listesi, "Henüz ihale bulunamadı.", "📭");
            return;
        }

        if (el.toplam_ihale) {
            el.toplam_ihale.textContent = sonuc.veri.length + "+";
        }

        el.ihale_listesi.innerHTML = sonuc.veri.map(ihale => `
            <div class="ihale-kart" data-id="${ihale.id}" style="
                padding: 16px; border: 1px solid #e2e8f0; border-radius: 10px;
                margin-bottom: 10px; cursor: pointer; transition: all 0.2s;
                background: white;
            " onmouseenter="this.style.borderColor='#F0A500'"
               onmouseleave="this.style.borderColor='#e2e8f0'">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="flex:1">
                        <div style="font-weight:600;font-size:14px;color:#0A1628;margin-bottom:4px">
                            ${ihale.baslik || "İsimsiz İhale"}
                        </div>
                        <div style="font-size:12px;color:#64748b">
                            🏛️ ${ihale.idare || "—"} &nbsp;|&nbsp;
                            📍 ${ihale.il || "—"} &nbsp;|&nbsp;
                            📅 ${UI.tarih_formatla(ihale.ihale_tarihi)}
                        </div>
                    </div>
                    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;margin-left:12px">
                        <span style="font-size:11px;background:#f1f5f9;padding:3px 8px;border-radius:4px;color:#475569">
                            ${ihale.ikn || ""}
                        </span>
                        ${ihale.analiz_tarihi
                            ? '<span style="font-size:11px;color:#10b981">✅ Analiz var</span>'
                            : '<span style="font-size:11px;color:#94a3b8">Analiz yok</span>'
                        }
                    </div>
                </div>
                <div style="margin-top:10px;display:flex;gap:8px">
                    <button onclick="ihale_detaya_git('${ihale.id}')" style="
                        font-size:12px;padding:5px 12px;border-radius:6px;
                        border:1px solid #e2e8f0;background:white;cursor:pointer;
                        color:#475569;
                    ">Detay →</button>
                    <button onclick="hizli_analiz('${ihale.id}', this)" style="
                        font-size:12px;padding:5px 12px;border-radius:6px;
                        border:none;background:#F0A500;cursor:pointer;
                        color:white;font-weight:600;
                    ">🤖 Analiz Et</button>
                    <button onclick="takibe_al('${ihale.id}', this)" style="
                        font-size:12px;padding:5px 12px;border-radius:6px;
                        border:1px solid #e2e8f0;background:white;cursor:pointer;
                        color:#475569;
                    ">⭐ Takip</button>
                </div>
            </div>
        `).join("");
    }

    // ── Takipler ────────────────────────────────────────
    async function takipler_yukle() {
        const sonuc = await API.takipler.listele();
        if (el.takip_sayisi && sonuc?.veri) {
            el.takip_sayisi.textContent = sonuc.veri.length;
        }
    }

    // ── Bildirimler ─────────────────────────────────────
    async function bildirimler_yukle() {
        if (!el.bildirim_liste) return;

        const sonuc = await API.bildirimler.listele();
        if (!sonuc?.veri?.length) {
            el.bildirim_liste.innerHTML = '<p style="color:#94a3b8;font-size:13px;padding:12px">Bildirim yok</p>';
            return;
        }

        const okunmamis = sonuc.veri.filter(b => !b.okundu).length;
        if (el.bildirim_rozet && okunmamis > 0) {
            el.bildirim_rozet.textContent = okunmamis;
            el.bildirim_rozet.style.display = "inline-flex";
        }

        el.bildirim_liste.innerHTML = sonuc.veri.slice(0, 5).map(b => `
            <div style="padding:10px;border-bottom:1px solid #f1f5f9;
                        opacity:${b.okundu ? 0.6 : 1};cursor:pointer"
                 onclick="bildirim_oku('${b.id}', this)">
                <div style="font-size:13px;font-weight:${b.okundu ? 400 : 600};color:#0A1628">
                    ${b.baslik}
                </div>
                <div style="font-size:12px;color:#94a3b8;margin-top:2px">
                    ${b.icerik || ""} &nbsp;·&nbsp; ${UI.tarih_formatla(b.olusturulma)}
                </div>
            </div>
        `).join("");
    }

    // ── Global fonksiyonlar (onclick'ler için) ──────────
    window.ihale_detaya_git = (id) => {
        window.location.href = `/ihale-detay?id=${id}`;
    };

    window.hizli_analiz = async (ihale_id, btn) => {
        const orijinal = btn.textContent;
        btn.textContent = "⏳ Analiz ediliyor...";
        btn.disabled = true;

        const sonuc = await API.ihaleler.analiz_et(ihale_id);

        btn.textContent = orijinal;
        btn.disabled = false;

        if (sonuc?.basari) {
            UI.bildirim_goster("Analiz tamamlandı! Detay sayfasında görüntüleyin.", "basari");
            setTimeout(() => ihale_detaya_git(ihale_id), 1500);
        }
    };

    window.takibe_al = async (ihale_id, btn) => {
        btn.textContent = "⏳";
        const sonuc = await API.takipler.ekle(ihale_id);
        if (sonuc?.basari) {
            btn.textContent = "✅ Takipte";
            btn.style.color = "#10b981";
            takipler_yukle();
        } else {
            btn.textContent = "⭐ Takip";
        }
    };

    window.bildirim_oku = async (id, el) => {
        await API.bildirimler.okundu_isaretle(id);
        el.style.opacity = "0.6";
    };

    // ── Hepsini yükle ───────────────────────────────────
    await Promise.all([
        profil_yukle(),
        ihaleler_yukle(),
        takipler_yukle(),
        bildirimler_yukle()
    ]);

});
