/**
 * Profil Sayfası
 * profil.html'e ekle:
 *   <script src="/js/profil.js"></script>
 */

document.addEventListener("DOMContentLoaded", async () => {

    if (!API.auth.girisli_mi()) {
        window.location.href = "/login";
        return;
    }

    const el = {
        form:             document.getElementById("profil-form"),
        firma_adi:        document.getElementById("firma-adi"),
        calisani:         document.getElementById("calisani"),
        ciro:             document.getElementById("yillik-ciro"),
        faaliyet:         document.getElementById("faaliyet-alanlari"),
        iller:            document.getElementById("calisma-illeri"),
        belgeler:         document.getElementById("belgeler"),
        referanslar:      document.getElementById("referanslar"),
        kacinilanlar:     document.getElementById("kacinilanlar"),
        kalan_kredi:      document.getElementById("kalan-kredi"),
        plan_adi:         document.getElementById("plan-adi"),
        analiz_sayisi:    document.getElementById("analiz-sayisi"),
        kaydet_btn:       document.getElementById("kaydet-btn"),
        cikis_btn:        document.getElementById("cikis-btn")
    };

    // ── Profil yükle ────────────────────────────────────
    async function profil_yukle() {
        const sonuc = await API.profil.getir();
        if (!sonuc) return;

        const { profil, kredi } = sonuc;

        // Formu doldur
        if (el.firma_adi)    el.firma_adi.value  = profil.firma_adi || "";
        if (el.calisani)     el.calisani.value   = profil.calisani_sayisi || "";
        if (el.ciro)         el.ciro.value       = profil.yillik_ciro_tl || "";

        // Array alanları — virgülle ayrılmış
        if (el.faaliyet)     el.faaliyet.value   = (profil.faaliyet_alanlari || []).join(", ");
        if (el.iller)        el.iller.value      = (profil.calisma_illeri || []).join(", ");
        if (el.belgeler)     el.belgeler.value   = (profil.belgeler || []).join(", ");
        if (el.referanslar)  el.referanslar.value = (profil.referanslar || []).join(", ");
        if (el.kacinilanlar) el.kacinilanlar.value = (profil.kacinilanlar || []).join(", ");

        // Kredi bilgisi
        if (el.kalan_kredi)  el.kalan_kredi.textContent = kredi.kalan_kredi;
        if (el.plan_adi)     el.plan_adi.textContent    = kredi.plan?.toUpperCase() || "FREE";
    }

    // ── Analiz geçmişi sayısı ───────────────────────────
    async function gecmis_yukle() {
        const sonuc = await API.gecmis.listele();
        if (el.analiz_sayisi && sonuc?.veri) {
            el.analiz_sayisi.textContent = sonuc.veri.length;
        }
    }

    // ── Kaydet ──────────────────────────────────────────
    el.form?.addEventListener("submit", async (e) => {
        e.preventDefault();

        const virgul_ayir = (str) =>
            str.split(",").map(s => s.trim()).filter(Boolean);

        const veri = {
            firma_adi:         el.firma_adi?.value || undefined,
            calisani_sayisi:   parseInt(el.calisani?.value) || undefined,
            yillik_ciro_tl:    parseInt(el.ciro?.value) || undefined,
            faaliyet_alanlari: el.faaliyet    ? virgul_ayir(el.faaliyet.value)    : undefined,
            calisma_illeri:    el.iller       ? virgul_ayir(el.iller.value)       : undefined,
            belgeler:          el.belgeler    ? virgul_ayir(el.belgeler.value)    : undefined,
            referanslar:       el.referanslar ? virgul_ayir(el.referanslar.value) : undefined,
            kacinilanlar:      el.kacinilanlar? virgul_ayir(el.kacinilanlar.value): undefined,
        };

        // Undefined olanları temizle
        Object.keys(veri).forEach(k => veri[k] === undefined && delete veri[k]);

        if (el.kaydet_btn) {
            el.kaydet_btn.textContent = "Kaydediliyor...";
            el.kaydet_btn.disabled = true;
        }

        const sonuc = await API.profil.guncelle(veri);

        if (el.kaydet_btn) {
            el.kaydet_btn.textContent = "Kaydet";
            el.kaydet_btn.disabled = false;
        }

        if (sonuc?.basari) {
            UI.bildirim_goster("Profil güncellendi!", "basari");
        }
    });

    // ── Çıkış ──────────────────────────────────────────
    el.cikis_btn?.addEventListener("click", () => API.auth.cikis());

    // Yükle
    await Promise.all([profil_yukle(), gecmis_yukle()]);
});
