/**
 * Auth sayfaları — login.html ve kayit.html için
 */

document.addEventListener("DOMContentLoaded", () => {

    // ── Giriş formu ─────────────────────────────────────
    const giris_form = document.getElementById("giris-form");
    if (giris_form) {
        giris_form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = giris_form.querySelector("button[type=submit]");
            const email = document.getElementById("email").value;
            const sifre = document.getElementById("sifre").value;

            btn.textContent = "Giriş yapılıyor...";
            btn.disabled = true;

            try {
                await API.auth.giris(email, sifre);
                UI.bildirim_goster("Başarıyla giriş yapıldı!", "basari");
                setTimeout(() => window.location.href = "/dashboard", 800);
            } catch (err) {
                UI.bildirim_goster(err.message || "Giriş başarısız", "hata");
                btn.textContent = "Giriş Yap";
                btn.disabled = false;
            }
        });
    }

    // ── Kayıt formu ─────────────────────────────────────
    const kayit_form = document.getElementById("kayit-form");
    if (kayit_form) {
        kayit_form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const btn = kayit_form.querySelector("button[type=submit]");
            const email     = document.getElementById("email").value;
            const sifre     = document.getElementById("sifre").value;
            const firma_adi = document.getElementById("firma-adi").value;

            if (sifre.length < 6) {
                UI.bildirim_goster("Şifre en az 6 karakter olmalı", "uyari");
                return;
            }

            btn.textContent = "Kayıt oluşturuluyor...";
            btn.disabled = true;

            try {
                await API.auth.kayit(email, sifre, firma_adi);
                UI.bildirim_goster("Kayıt başarılı! E-postanızı onaylayın.", "basari");
                setTimeout(() => window.location.href = "/login", 2000);
            } catch (err) {
                UI.bildirim_goster(err.message || "Kayıt başarısız", "hata");
                btn.textContent = "Kayıt Ol";
                btn.disabled = false;
            }
        });
    }

    // Zaten giriş yapılmışsa dashboard'a yönlendir
    if (API.auth.girisli_mi()) {
        window.location.href = "/dashboard";
    }

});
