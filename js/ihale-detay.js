/**
 * İhale Detay Sayfası
 * ihale-detay.html'e ekle:
 *   <script src="/js/ihale-detay.js"></script>
 */

document.addEventListener("DOMContentLoaded", async () => {

    // URL'den ihale ID al
    const params = new URLSearchParams(window.location.search);
    const ihale_id = params.get("id");

    if (!ihale_id) {
        window.location.href = "/ihaleler";
        return;
    }

    // Elementler
    const el = {
        baslik:          document.getElementById("ihale-baslik"),
        ikn:             document.getElementById("ihale-ikn"),
        idare:           document.getElementById("ihale-idare"),
        il:              document.getElementById("ihale-il"),
        tarih:           document.getElementById("ihale-tarih"),
        kalan:           document.getElementById("ihale-kalan"),
        tur:             document.getElementById("ihale-tur"),
        durum:           document.getElementById("ihale-durum"),
        bedel:           document.getElementById("ihale-bedel"),
        analiz_btn:      document.getElementById("analiz-btn"),
        takip_btn:       document.getElementById("takip-btn"),
        analiz_bolum:    document.getElementById("analiz-bolum"),
        analiz_icerik:   document.getElementById("analiz-icerik"),
        kredi_uyari:     document.getElementById("kredi-uyari"),
        yukleniyor:      document.getElementById("yukleniyor")
    };

    // ── İhale bilgilerini yükle ─────────────────────────
    async function ihale_yukle() {
        UI.yukleniyor_goster(el.yukleniyor || document.body, "İhale yükleniyor...");

        const sonuc = await API.ihaleler.detay(ihale_id);
        if (!sonuc?.veri) {
            UI.bildirim_goster("İhale bulunamadı", "hata");
            setTimeout(() => window.location.href = "/ihaleler", 1500);
            return;
        }

        const ihale = sonuc.veri;

        // Temel bilgileri doldur
        if (el.baslik) el.baslik.textContent = ihale.baslik || "İsimsiz İhale";
        if (el.ikn)    el.ikn.textContent    = ihale.ikn || "—";
        if (el.idare)  el.idare.textContent  = ihale.idare || "—";
        if (el.il)     el.il.textContent     = ihale.il || "—";
        if (el.tarih)  el.tarih.textContent  = UI.tarih_formatla(ihale.ihale_tarihi);
        if (el.tur)    el.tur.textContent    = ihale.tur || "—";
        if (el.bedel)  el.bedel.textContent  = UI.para_formatla(ihale.tahmini_bedel);

        if (el.kalan) {
            el.kalan.innerHTML = UI.kalan_gun(ihale.ihale_tarihi) || "—";
        }

        if (el.durum) {
            const renk = ihale.durum?.includes("Açık") ? "#10b981" : "#94a3b8";
            el.durum.innerHTML = `
                <span style="color:${renk};font-weight:600">● ${ihale.durum || "—"}</span>
            `;
        }

        // Sayfa başlığını güncelle
        document.title = `${ihale.baslik} — İhalePlatform`;

        // Analiz varsa göster
        if (ihale.yapay_zeka_ozeti && el.analiz_bolum) {
            el.analiz_bolum.style.display = "block";
            if (el.analiz_btn) {
                el.analiz_btn.textContent = "🔄 Yeniden Analiz Et (1 Kredi)";
            }
            if (el.analiz_icerik) {
                UI.rapor_render({ rapor: ihale.yapay_zeka_ozeti }, el.analiz_icerik);
            }
        }

        if (el.yukleniyor) el.yukleniyor.style.display = "none";
    }

    // ── Analiz Et butonu ────────────────────────────────
    if (el.analiz_btn) {
        el.analiz_btn.addEventListener("click", async () => {

            if (!API.auth.girisli_mi()) {
                UI.bildirim_goster("Analiz için giriş yapmalısınız", "uyari");
                setTimeout(() => window.location.href = "/login", 1500);
                return;
            }

            // Kredi kontrolü
            const profil = await API.profil.getir();
            if (!profil) return;

            const kalan_kredi = profil.kredi.kalan_kredi;
            if (kalan_kredi < 1) {
                if (el.kredi_uyari) el.kredi_uyari.style.display = "block";
                UI.bildirim_goster(
                    "Krediniz yetersiz! Paket yükseltin.",
                    "uyari",
                    "/fiyatlandirma"
                );
                return;
            }

            // Analiz başlat
            el.analiz_btn.disabled = true;
            el.analiz_btn.innerHTML = `
                <span style="display:inline-flex;align-items:center;gap:8px">
                    <span style="width:16px;height:16px;border:2px solid #fff;
                        border-top-color:transparent;border-radius:50%;
                        animation:spin 0.8s linear infinite;display:inline-block"></span>
                    Analiz ediliyor...
                </span>
            `;

            if (el.analiz_bolum) {
                el.analiz_bolum.style.display = "block";
                UI.yukleniyor_goster(el.analiz_icerik, "Yapay zeka şartnameyi okuyor...");
            }

            const sonuc = await API.ihaleler.analiz_et(ihale_id);

            el.analiz_btn.disabled = false;
            el.analiz_btn.textContent = "🔄 Yeniden Analiz Et (1 Kredi)";

            if (sonuc?.basari && el.analiz_icerik) {
                UI.rapor_render(sonuc, el.analiz_icerik);
                UI.bildirim_goster(
                    sonuc.cache
                        ? "Analiz cache'den yüklendi (1 kredi)"
                        : `Analiz tamamlandı (${sonuc.harcanan_kredi} kredi)`,
                    "basari"
                );
            }
        });
    }

    // ── Takip butonu ────────────────────────────────────
    if (el.takip_btn) {
        // Mevcut takip durumunu kontrol et
        if (API.auth.girisli_mi()) {
            const takipler = await API.takipler.listele();
            const takipte = takipler?.veri?.some(t => t.ihale_id === ihale_id);
            if (takipte) {
                el.takip_btn.textContent = "✅ Takipte";
                el.takip_btn.style.background = "#10b981";
                el.takip_btn.dataset.takipte = "1";
            }
        }

        el.takip_btn.addEventListener("click", async () => {
            if (!API.auth.girisli_mi()) {
                UI.bildirim_goster("Takip için giriş yapmalısınız", "uyari");
                return;
            }

            if (el.takip_btn.dataset.takipte === "1") {
                await API.takipler.kaldir(ihale_id);
                el.takip_btn.textContent = "⭐ Takibe Al";
                el.takip_btn.style.background = "";
                el.takip_btn.dataset.takipte = "0";
                UI.bildirim_goster("Takipten çıkarıldı", "bilgi");
            } else {
                await API.takipler.ekle(ihale_id);
                el.takip_btn.textContent = "✅ Takipte";
                el.takip_btn.style.background = "#10b981";
                el.takip_btn.dataset.takipte = "1";
                UI.bildirim_goster("Takibe alındı!", "basari");
            }
        });
    }

    // Yükle
    await ihale_yukle();
});
