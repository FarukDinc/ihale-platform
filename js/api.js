/**
 * İhaleGlobal — API İstemcisi
 * Tüm backend iletişimi buradan geçer
 * 
 * Kullanım:
 *   <script src="/js/api.js"></script>
 *   const ihaleler = await API.ihaleleri_getir({ il: "Ankara" });
 */

const API = (() => {

    // ── Yapılandırma ────────────────────────────────────
    const CONFIG = {
        // VDS'in kendi FastAPI'si — nginx /api/ proxy ile aynı origin
        BASE_URL: "https://ihaleglobal.com/api",

        // Supabase — Auth için
        SUPABASE_URL: "https://ihaleglobal.com",
        SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs"
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
                window.location.href = "/login";
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
                window.location.href = "/login";
                return null;
            }

            // Kredi yetersiz
            if (yanit.status === 402) {
                const hata = await yanit.json();
                UI.bildirim_goster("Yetersiz kredi! Paket yükseltmek için tıklayın.", "uyari", "/fiyatlandirma_odeme_bolumu");
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
            window.location.href = "/login";
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

    // ── Firma AI Yorumu (ÖNCELİK 10 Faz D1) ──────────────
    const firma = {
        async yorum_al(firma_adi) {
            return istek("POST", "/ai/firma-yorum", { firma: firma_adi });
        }
    };

    // Public API
    return { auth, ihaleler, profil, takipler, bildirimler, gecmis, firma, CONFIG };

})();
