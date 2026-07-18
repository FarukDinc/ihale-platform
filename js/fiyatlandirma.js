/**
 * Fiyatlandırma & Ödeme Sayfası
 * fiyatlandirma.html'e ekle:
 *   <script src="/js/fiyatlandirma.js"></script>
 */

document.addEventListener("DOMContentLoaded", async () => {

    const el = {
        standart_btn:  document.getElementById("standart-satin-al"),
        kurumsal_btn:  document.getElementById("kurumsal-satin-al"),
        odeme_modal:   document.getElementById("odeme-modal"),
        odeme_form:    document.getElementById("odeme-form"),
        modal_plan:    document.getElementById("modal-plan-adi"),
        modal_fiyat:   document.getElementById("modal-fiyat"),
        modal_kapat:   document.getElementById("modal-kapat"),
        kart_no:       document.getElementById("kart-no"),
        kart_ad:       document.getElementById("kart-ad"),
        kart_soyad:    document.getElementById("kart-soyad"),
        kart_ay:       document.getElementById("kart-ay"),
        kart_yil:      document.getElementById("kart-yil"),
        kart_cvc:      document.getElementById("kart-cvc"),
        taksit:        document.getElementById("taksit"),
        odeme_btn:     document.getElementById("odeme-btn"),
        kredi_goster:  document.getElementById("kalan-kredi-header")
    };

    let secili_plan = null;

    // ── Plan butonları ───────────────────────────────────
    function plan_sec(plan_kodu) {
        if (!API.auth.girisli_mi()) {
            UI.bildirim_goster("Satın almak için giriş yapmalısınız", "uyari");
            setTimeout(() => window.location.href = "/login", 1500);
            return;
        }

        secili_plan = plan_kodu;
        const planlar = {
            standart: { ad: "Standart Plan", fiyat: "1.490 TL/ay", kredi: "50 Kredi" },
            kurumsal: { ad: "Kurumsal Plan", fiyat: "3.990 TL/ay", kredi: "250 Kredi" }
        };

        const plan = planlar[plan_kodu];
        if (el.modal_plan)  el.modal_plan.textContent  = plan.ad;
        if (el.modal_fiyat) el.modal_fiyat.textContent = `${plan.fiyat} — ${plan.kredi}`;

        // Modal aç
        if (el.odeme_modal) {
            el.odeme_modal.style.display = "flex";
        }
    }

    el.standart_btn?.addEventListener("click", () => plan_sec("standart"));
    el.kurumsal_btn?.addEventListener("click", () => plan_sec("kurumsal"));

    // ── Modal kapat ─────────────────────────────────────
    el.modal_kapat?.addEventListener("click", () => {
        if (el.odeme_modal) el.odeme_modal.style.display = "none";
    });

    el.odeme_modal?.addEventListener("click", (e) => {
        if (e.target === el.odeme_modal) {
            el.odeme_modal.style.display = "none";
        }
    });

    // ── Kart no formatla ────────────────────────────────
    el.kart_no?.addEventListener("input", (e) => {
        let val = e.target.value.replace(/\D/g, "").slice(0, 16);
        e.target.value = val.replace(/(.{4})/g, "$1 ").trim();
    });

    // ── Ödeme formu ─────────────────────────────────────
    el.odeme_form?.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!secili_plan) return;

        const kart_no_temiz = el.kart_no?.value.replace(/\s/g, "") || "";

        if (kart_no_temiz.length !== 16) {
            UI.bildirim_goster("Geçerli kart numarası girin", "uyari");
            return;
        }

        if (el.odeme_btn) {
            el.odeme_btn.textContent = "İşlem yapılıyor...";
            el.odeme_btn.disabled = true;
        }

        try {
            const sonuc = await fetch(`${API.CONFIG.BASE_URL}/odeme/baslat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    // Bayat kopya DEĞİL canlı oturum token'ı: access_token ~1sa'de yenilenir,
                    // localStorage aynası o an eski olabilirdi → ödeme 401 alıyordu.
                    "Authorization": `Bearer ${await API.auth.token_canli()}`
                },
                body: JSON.stringify({
                    plan_kodu:        secili_plan,
                    kart_sahibi_ad:   el.kart_ad?.value || "",
                    kart_sahibi_soyad: el.kart_soyad?.value || "",
                    kart_no:          kart_no_temiz,
                    son_kullanma_ay:  el.kart_ay?.value || "",
                    son_kullanma_yil: el.kart_yil?.value || "",
                    cvc:              el.kart_cvc?.value || "",
                    taksit:           parseInt(el.taksit?.value || "1")
                })
            });

            const veri = await sonuc.json();

            if (sonuc.ok && veri.basari) {
                if (el.odeme_modal) el.odeme_modal.style.display = "none";
                UI.bildirim_goster(veri.mesaj || "Ödeme başarılı! Krediniz yüklendi.", "basari");

                // Kredi sayacını güncelle
                setTimeout(async () => {
                    const profil = await API.profil.getir();
                    if (el.kredi_goster && profil?.kredi) {
                        el.kredi_goster.textContent = profil.kredi.kalan_kredi;
                    }
                }, 1500);

            } else {
                const hata = veri.detail || veri.hata || "Ödeme başarısız";
                UI.bildirim_goster(hata, "hata");
            }

        } catch (err) {
            UI.bildirim_goster("Bağlantı hatası, tekrar deneyin", "hata");
        } finally {
            if (el.odeme_btn) {
                el.odeme_btn.textContent = "Ödemeyi Tamamla";
                el.odeme_btn.disabled = false;
            }
        }
    });

    // ── Giriş yapılmışsa krediyi göster ─────────────────
    if (API.auth.girisli_mi() && el.kredi_goster) {
        const profil = await API.profil.getir();
        if (profil?.kredi) {
            el.kredi_goster.textContent = profil.kredi.kalan_kredi;
        }
    }
});
