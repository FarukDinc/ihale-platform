/**
 * İhalePlatform — API İstemcisi
 * Tüm backend iletişimi buradan geçer
 * 
 * Kullanım:
 *   <script src="/js/api.js"></script>
 *   const ihaleler = await API.ihaleleri_getir({ il: "Ankara" });
 */

const API = (() => {

    // ── Yapılandırma ────────────────────────────────────
    const CONFIG = {
        // Render.com API URL — deploy sonrası güncelle
        BASE_URL: "https://ihale-api.onrender.com",

        // Supabase — Auth için
        SUPABASE_URL: "https://xxxxxxxxxxxxx.supabase.co",
        SUPABASE_ANON_KEY: "xxxsupabseanonkeyxxx"
    };

    // ── Token yönetimi ──────────────────────────────────
    const token = {
        al:  () => localStorage.getItem("ihale_token"),
        yaz: (t) => localStorage.setItem("ihale_token", t),
        sil: () => localStorage.removeItem("ihale_token")
    };

    // ── Temel istek fonksiyonu ──────────────────────────
    async function istek(metot, yol, veri = null, auth = true) {
        const basliklar = { "Content-Type": "application/json" };

        if (auth) {
            const t = token.al();
            if (!t) {
                window.location.href = "/login.html";
                return null;
            }
            basliklar["Authorization"] = `Bearer ${t}`;
        }

        try {
            const yanit = await fetch(`${CONFIG.BASE_URL}${yol}`, {
                method: metot,
                headers: basliklar,
                body: veri ? JSON.stringify(veri) : null
            });

            // Token süresi dolduysa login'e yönlendir
            if (yanit.status === 401) {
                token.sil();
                window.location.href = "/login.html";
                return null;
            }

            // Kredi yetersiz
            if (yanit.status === 402) {
                const hata = await yanit.json();
                UI.bildirim_goster("Yetersiz kredi! Paket yükseltmek için tıklayın.", "uyari", "/fiyatlandirma.html");
                return null;
            }

            if (!yanit.ok) {
                const hata = await yanit.json();
                throw new Error(hata.detail || "Bir hata oluştu");
            }

            return await yanit.json();

        } catch (e) {
            console.error(`API hatası [${metot} ${yol}]:`, e);
            UI.bildirim_goster(e.message, "hata");
            return null;
        }
    }

    // ── Auth ────────────────────────────────────────────
    const auth = {
        async giris(email, sifre) {
            const supabase = window.supabase.createClient(
                CONFIG.SUPABASE_URL,
                CONFIG.SUPABASE_ANON_KEY
            );
            const { data, error } = await supabase.auth.signInWithPassword({
                email, password: sifre
            });
            if (error) throw new Error(error.message);
            token.yaz(data.session.access_token);
            return data;
        },

        async kayit(email, sifre, firma_adi) {
            const supabase = window.supabase.createClient(
                CONFIG.SUPABASE_URL,
                CONFIG.SUPABASE_ANON_KEY
            );
            const { data, error } = await supabase.auth.signUp({
                email,
                password: sifre,
                options: { data: { firma_adi } }
            });
            if (error) throw new Error(error.message);
            if (data.session) token.yaz(data.session.access_token);
            return data;
        },

        cikis() {
            token.sil();
            window.location.href = "/login.html";
        },

        girisli_mi() {
            return !!token.al();
        }
    };

    // ── İhaleler ────────────────────────────────────────
    const ihaleler = {
        async listele({ il, tur, arama, sayfa = 1, boyut = 20 } = {}) {
            const params = new URLSearchParams();
            if (il)    params.append("il", il);
            if (tur)   params.append("tur", tur);
            if (arama) params.append("arama", arama);
            params.append("sayfa", sayfa);
            params.append("boyut", boyut);

            return istek("GET", `/ihaleler?${params}`, null, false);
        },

        async detay(ihale_id) {
            return istek("GET", `/ihaleler/${ihale_id}`, null, false);
        },

        async analiz_et(ihale_id) {
            return istek("POST", "/analiz", { ihale_id });
        }
    };

    // ── Profil ──────────────────────────────────────────
    const profil = {
        async getir() {
            return istek("GET", "/profil");
        },

        async guncelle(veri) {
            return istek("PUT", "/profil", veri);
        }
    };

    // ── Takipler ────────────────────────────────────────
    const takipler = {
        async listele() {
            return istek("GET", "/takipler");
        },

        async ekle(ihale_id, notlar = null) {
            return istek("POST", "/takipler", { ihale_id, notlar });
        },

        async kaldir(ihale_id) {
            return istek("DELETE", `/takipler/${ihale_id}`);
        }
    };

    // ── Bildirimler ─────────────────────────────────────
    const bildirimler = {
        async listele() {
            return istek("GET", "/bildirimler");
        },

        async okundu_isaretle(bildirim_id) {
            return istek("PUT", `/bildirimler/${bildirim_id}/okundu`);
        }
    };

    // ── Analiz geçmişi ──────────────────────────────────
    const gecmis = {
        async listele() {
            return istek("GET", "/analiz-gecmisi");
        }
    };

    // Public API
    return { auth, ihaleler, profil, takipler, bildirimler, gecmis, CONFIG };

})();
