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
        SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzg0MzA3MTU4LCJleHAiOjE5NDE5ODcxNTh9.CjNKulvirotDD_y2oO2QKgo0kbqYvL0jUSV1RiDMoso"
    };

    // ── Supabase istemcisi (TEK örnek; çoklu GoTrueClient uyarı/çakışma üretir) ──
    let _sb = null;
    function sbClient() {
        if (!_sb && window.supabase) {
            _sb = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);
            // ihale_token AYNASI. Eskiden login anındaki access_token KOPYASI localStorage'da
            // kalıyordu; Supabase token'ı ~1sa'de yenilenince kopya bayatlıyor → istek 401 →
            // token.sil() + /login (oturum GEÇERLİYKEN bounce), ödeme çağrısı da 401 alıyordu.
            // Artık her oturum değişiminde ayna tazelenir. OAuth (Google) girişinde de bu olay
            // tetiklendiğinden ayna kendiliğinden dolar — sosyal giriş için de şart.
            _sb.auth.onAuthStateChange((_olay, oturum) => {
                try {
                    if (oturum && oturum.access_token) localStorage.setItem("ihale_token", oturum.access_token);
                    else localStorage.removeItem("ihale_token");
                } catch (_) {}
            });
        }
        return _sb;
    }

    // ── Token yönetimi ──────────────────────────────────
    // al()    : SENKRON ayna — girisli_mi() gibi senkron çağrılar için (8+ yerde kullanılıyor,
    //           async'e çevirmek `if (!girisli_mi())` guard'larını sessizce devre dışı bırakırdı)
    // canli() : ASENKRON gerçek kaynak — AĞ İSTEKLERİNDE DAİMA bu kullanılır (taze/yenilenmiş)
    const token = {
        al:  () => localStorage.getItem("ihale_token"),
        yaz: (t) => localStorage.setItem("ihale_token", t),
        sil: () => localStorage.removeItem("ihale_token"),
        async canli() {
            try {
                const sb = sbClient();
                if (!sb) return token.al();
                const { data } = await sb.auth.getSession();
                return (data && data.session && data.session.access_token) || null;
            } catch (_) { return token.al(); }
        }
    };

    // ── Temel istek fonksiyonu ──────────────────────────
    async function istek(metot, yol, veri = null, auth = true) {
        const basliklar = { "Content-Type": "application/json" };

        if (auth) {
            // DAİMA canlı oturumdan al — ayna bayat olabilir (yenilenme anı) ve OAuth
            // girişinde ayna henüz yazılmamış olabilir.
            const t = await token.canli();
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
            const supabase = sbClient();
            const { data, error } = await supabase.auth.signInWithPassword({
                email, password: sifre
            });
            if (error) throw new Error(error.message);
            token.yaz(data.session.access_token);
            return data;
        },

        async kayit(email, sifre, firma_adi) {
            const supabase = sbClient();
            const { data, error } = await supabase.auth.signUp({
                email,
                password: sifre,
                options: {
                    data: { firma_adi },
                    // E-posta onay linki buraya döner; login.html hash'teki token'ı
                    // işleyip oturumu kurar. Boş bırakılırsa SITE_URL'e (anasayfa) döner
                    // ve anasayfa hash'i işlemediği için kullanıcı "hiçbir şey olmadı" sanır.
                    emailRedirectTo: CONFIG.SUPABASE_URL + "/login"
                }
            });
            if (error) throw new Error(error.message);
            if (data.session) token.yaz(data.session.access_token);
            return data;
        },

        // ÖNEMLİ: eskiden yalnız aynayı siliyordu → Supabase oturumu AÇIK kalıyordu
        // (kullanıcı "çıkış yaptım" sanıyor ama oturum duruyor; aynı tarayıcıda geri
        // dönünce yeniden girişli oluyordu). Artık gerçekten signOut edilir.
        async cikis() {
            try { const sb = sbClient(); if (sb) await sb.auth.signOut(); } catch (_) {}
            token.sil();
            window.location.href = "/login";
        },

        // SENKRON kalmalı — 8+ çağrı yeri `if (!girisli_mi())` şeklinde guard yapıyor.
        // Ayna onAuthStateChange ile tazelendiği için bayatlamaz.
        girisli_mi() {
            return !!token.al();
        },

        // API dışı doğrudan fetch yapan yerler (örn. ödeme) canlı token'ı buradan alsın.
        async token_canli() {
            return await token.canli();
        }
    };

    // Aynayı besleyen dinleyici ancak istemci oluşturulunca bağlanır → erken kur.
    // (supabase-js henüz yüklenmediyse DOM hazır olduğunda tekrar dene.)
    try { sbClient(); } catch (_) {}
    if (!_sb && typeof document !== "undefined") {
        document.addEventListener("DOMContentLoaded", () => { try { sbClient(); } catch (_) {} });
    }

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
