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

        // Google ile giriş bayrağı. VDS'te GoTrue'ya GOTRUE_EXTERNAL_GOOGLE_ENABLED/CLIENT_ID/
        // SECRET/REDIRECT_URI eklenip auth konteyneri yeniden başlatıldıktan SONRA true yap.
        // Kapalıyken buton hiç gösterilmez — yapılandırılmamış sağlayıcıya tıklayınca GoTrue
        // "Unsupported provider" hatası döndürür, kullanıcı bozuk akışa düşer.
        GOOGLE_GIRIS: true,

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

    // ── Bildirim ────────────────────────────────────────
    // Eskiden burada UI.bildirim_goster() çağrılıyordu ama UI yalnız js/ui.js'te
    // tanımlıydı ve api.js yükleyen 6 sayfanın HİÇBİRİ ui.js yüklemiyordu →
    // çağrılar çalışma anında ReferenceError veriyordu. Somut sonucu:
    // firma-analiz.html:748'de 402 (kredi bitti) uyarısı kullanıcıya HİÇ ulaşmıyor,
    // bunun yerine catch dalı yanıltıcı "Bu özellik yakında aktif olacak" gösteriyordu.
    // (js/ui.js 20 Tem'de silindi — hiçbir sayfa yüklemiyordu.)
    //
    // ⚠️ Sınıf adı bilinçli olarak 'toast' DEĞİL: teklif-olustur.html:410 ve
    // ihaleler.html:376 kendi `.toast { opacity: 0 }` kuralını taşıyor (görünürlüğü
    // `.toast.show` veriyor). 'toast' deseydik mesaj o iki sayfada GÖRÜNMEZ olurdu.
    // Stil inline: sayfa CSS'ine hiç bağlı değil, her sayfada aynı çalışır.
    function bildirimGoster(mesaj, tur = "bilgi", link = null) {
        try {
            const renk = { basari: "#16a34a", hata: "#dc2626", uyari: "#d97706", bilgi: "#2563eb" }[tur] || "#2563eb";
            document.querySelectorAll(".ig-api-toast").forEach(e => e.remove());
            const el = document.createElement("div");
            el.className = "ig-api-toast";
            el.textContent = mesaj || "Bir hata oluştu";   // textContent — innerHTML DEĞİL (XSS)
            el.style.cssText =
                "position:fixed;bottom:24px;right:24px;z-index:99999;max-width:340px;" +
                "padding:12px 20px;border-radius:8px;font-size:14px;font-weight:600;" +
                "font-family:inherit;color:#fff;background:" + renk + ";" +
                // GÖRÜNÜRLÜK BAŞTAN 1 — giriş animasyonu YOK. Bilinçli:
                // önce opacity:0 + rAF/reflow ile 1'e geçiş deneniyordu; sekme arka
                // plandayken rAF askıya alınıyor ve CSS geçişi ilerlemiyor → bildirim
                // opacity:0'da takılı kalıp HİÇ görünmüyordu (yerel testte yakalandı).
                // Artık görünürlük hiçbir animasyona bağlı değil; yalnız ÇIKIŞ animasyonlu
                // ve o başarısız olursa bildirim aniden kaybolur — zararsız taraf.
                "box-shadow:0 4px 16px rgba(0,0,0,.2);opacity:1;" +
                "transition:opacity .3s;" + (link ? "cursor:pointer;" : "pointer-events:none;");
            if (link) el.addEventListener("click", () => { window.location.href = link; });
            document.body.appendChild(el);
            setTimeout(() => {
                el.style.opacity = "0";
                setTimeout(() => el.remove(), 350);   // geçiş ilerlemese de kaldırılır
            }, link ? 6000 : 4000);
        } catch (_) { /* bildirim ASLA akışı kırmasın */ }
    }

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
                try { await yanit.json(); } catch (_) {}   // gövde tüketilsin; içeriği kullanılmıyor
                bildirimGoster("Yetersiz kredi! Paket yükseltmek için tıklayın.", "uyari", "/fiyatlandirma_odeme_bolumu");
                return null;
            }

            if (!yanit.ok) {
                const hata = await yanit.json();
                throw new Error(hata.detail || "Bir hata oluştu");
            }

            return await yanit.json();

        } catch (e) {
            console.error(`API hatası [${metot} ${yol}]:`, e);
            bildirimGoster(e && e.message ? e.message : "Bir hata oluştu", "hata");
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
        },

        // Google ile giriş/kayıt. Profil + 3 kredi + free plan, auth.users trigger'ı
        // (handle_new_user) ile HER kayıt yolunda otomatik oluşur — ek iş gerekmez.
        // firma_adi Google'dan GELMEZ (metadata: name/email/picture) → boş '' kalır,
        // kullanıcı profil ekranında doldurur (profil_tamamlandi=false).
        async googleIleGiris() {
            const supabase = sbClient();
            if (!supabase) throw new Error("Supabase istemcisi yüklenemedi");
            const { data, error } = await supabase.auth.signInWithOAuth({
                provider: "google",
                options: { redirectTo: CONFIG.SUPABASE_URL + "/dashboard" }
            });
            if (error) throw new Error(error.message);
            return data;
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
