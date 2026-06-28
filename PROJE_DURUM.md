# İhale Platform — Proje Durumu & Devir Notu

> Son güncelleme: 2026-06-27. Bu doküman başka bir AI oturumunun (Claude/Gemini) projeyi
> hızla kavrayıp ilerletebilmesi için yazıldı. Geniş kapsamlıdır.

---

## 1. Proje Nedir?

**İhale Platform** — Türkiye kamu ihaleleri (EKAP) için bir SaaS. Müteahhit/tedarikçi firmalara:
- Aktif ihaleleri arama/filtreleme/takip
- İhale detayları (yaklaşık maliyet tahmini, ilan metni, belgeler)
- E-posta bildirimleri (yeni/uygun ihaleler)
- Şartname analizi (AI ile)
- Teklif oluşturma yardımı
- Rekabet analizi
- Kredi tabanlı ödeme (İyzico)

Hedef: Firmalara abonelik/kredi ile satılan, ihaleleri otomatik çekip değer katan bir ürün.

---

## 2. Mimari & Stack

| Katman | Teknoloji | Detay |
|---|---|---|
| **Frontend** | Statik HTML/JS | Cloudflare Pages. Uzantısız URL'ler prod'da çalışır (local `python -m http.server`'da 404 verir — normal). |
| **DB + Auth + Storage** | Supabase | Proje ref: `lpgelwfoarhouollhwur`. PostgREST API + Storage (`belgeler` bucket). |
| **Scraper** | Python (httpx) | GitHub Actions, gece 02:00 UTC cron. `backend/ekap_scraper.py`. Playwright YOK (tamamen httpx). |
| **Backend API** | FastAPI | Render'da: `https://ihaleplatform-backend.onrender.com` (frontend teklif-olustur için çağırıyor). `backend/api.py`. |
| **Ödeme** | İyzico | `backend/payment.py` — webhook ile kredi güncelleme. |
| **E-posta** | Resend | `backend/notify.py`. |
| **AI** | Google Gemini | **Paralı tier AKTİF** (~$2-6/ay). CAPTCHA çözme + şartname analizi. `google-genai` paketi (eski `google.generativeai` DEĞİL). |
| **Proxy** | Webshare | `backend/proxy_config.py` — EKAP IP blokajını önlemek için rotating proxy. |

### Backend modülleri
- `ekap_scraper.py` (813 satır) — **ana scraper**. EKAP v2 API + eski portal CAPTCHA + Supabase yazımı.
- `api.py` (298) — FastAPI backend.
- `worker.py` (325) — scraper+analyzer+supabase entegrasyon.
- `analyzer.py` (354) — **şartname analizörü** (pdfplumber + Gemini text/vision). İleride proaktif eşleştirme özelliğinin temeli.
- `notify.py` (287) — e-posta bildirim.
- `payment.py` (351) — İyzico.
- `proxy_config.py` (60) — Webshare proxy.

### Frontend sayfaları
`index, dashboard, ihaleler, ihale-detay, takipte, rekabet-analizi, teklif-olustur, dokumanlar, bildirimler, profil, login, fiyatlandirma_odeme_bolumu, hakkimizda, iletisim, kvkk, mesafeli-satis, uyumluluk, 404`

### Supabase tabloları
`ilanlar` (ANA tablo — ihale verisi), `takip`/`takipler`, `profil`/`kullanici_profiller`, `kullanici_krediler`, `kredi_hareketleri`, `bildirimler`, `analiz_gecmisi`, `ihaleler`.
⚠️ Bazı isimler **çift görünüyor** (takip vs takipler, profil vs kullanici_profiller, ihaleler vs ilanlar) — hangisi kanonik, doğrulanmalı (teknik borç).

---

## 3. EKAP Entegrasyonu — Kritik Teknik Bilgi

### 3.1 EKAP v2 API (`ekapv2.kik.gov.tr`)
- `GetListByParameters` → aktif ihale listesi (~11.800 ihale)
- `GetByIhaleIdIhaleDetay` → detay + ilan HTML (`veriHtml`)
- `GetByIdItirazenSikayetBasvuruBedel` → itiraz bedeli → yaklaşık maliyet aralığı tahmini
- `GetDokumanUrl` → belge indirme linki (eski portala yönlendirir)
- `GetDokumanListByIhaleId` → **ARTIK 404, kullanılmıyor** (kaldırıldı)
- Korumalı endpointler **imzalı header** ister: `crypto_headers()` (AES-CBC, `CRYPTO_KEY`). Bkz. hafıza notu.

### 3.2 EKAP Belge İndirme — 3 Adımlı CAPTCHA Akışı (girişsiz çalışır!)
`ekap_captcha_indir()` fonksiyonu:
1. `GetDokumanUrl` linki (`VatandasIlanGoruntuleme.aspx`) → GET → 302 ile `/EKAP/Ilan/IlanDokumanDownload.aspx`'e yönlenir (CAPTCHA sayfası). **Form action MUTLAKA final redirect URL baz alınarak çözülmeli** (`str(r.url)`), yoksa yanlış path'e POST → login'e atar (eski "giriş gerekli" yanılgısının kök nedeni buydu).
2. CAPTCHA çöz + POST → "İhale Dokümanı başarıyla indirilmiştir" onay sayfası.
3. `btnTmpNormal` postback (yeni ViewState) → gerçek ZIP/PDF.

**CAPTCHA çözme** (`captcha_coz_gemini`): görsel BMP, kırmızı gürültü + koyu soru. `_captcha_temizle` (numpy renk filtresi) gürültüyü atar. Sorular çeşitli (matematik/sıralama/"rakamla yazınız"/"hangisi büyük harfle"). **Cevap formatı: `<soru_cevabı><sağdaki_doğrulama_sayısı>` birleşik** (örn `zil87075`). Gemini'ye SOL/SAĞ olarak sorulur.

### 3.3 Belge Stratejisi (KARAR)
- **Gece turu = LINK-ONLY** (`EKAP_BELGE_LINK=1`, varsayılan). İndirmez, sadece `GetDokumanUrl` linkini saklar. Frontend "EKAP'ta Aç" gösterir, kullanıcı CAPTCHA'yı kendi çözer. Bedava, hızlı, sıfır Storage.
- **Ağır indirme** (`EKAP_BELGE_INDIR=1`) = CAPTCHA çöz + indir + Storage. **Şu an KAPALI**, ileride müşteri başına kullanılacak.
- Link rastgele-IV şifreli ihaleId içerir → tekrar kullanılabilir/kalıcı görünüyor.

---

## 4. Bu Oturumda Ne Yapıldı? (2026-06-27)

1. **EKAP belge indirme tamamen çözüldü** — "giriş gerekli" yanılgısı çürütüldü, 3 adımlı akış uçtan uca çalışıyor (gerçek 10MB ZIP'ler indirildi, 12 belge doğrulandı).
2. **Kritik bug'lar bulundu & düzeltildi:**
   - `backend/supabase/` özel httpx wrapper'ında **`.storage` yoktu** → belge yükleme sessizce patlıyordu. Storage REST desteği eklendi.
   - Supabase Storage anahtarı **ASCII olmalı** → Türkçe→ASCII çeviri (`dosya_adi_temizle`).
   - İçerik-hash **dedup** (islem 1-4 aynı dosyayı döndürünce tek yükleme).
   - **TARİH BUG'I (en büyük etki):** `son_teklif_tarihi` Türkçe `GG.AA.YYYY` formatı Postgres'i kırıyordu → 50'lik batch'ler sessizce düşüyor, DB'de yıllardır sadece **1.115** kayıt vardı. `tarih_iso()` ile düzeltildi.
3. **Link-only mod** eklendi (varsayılan), workflow link-only'e alındı.
4. **main'e merge edildi (PR #1), canlı tur çalıştırıldı, doğrulandı:**
   - Toplam ilan: **1.115 → 11.878** (10× artış, tarih fix sayesinde)
   - Belge linkli: **4 → 733**
   - Tarih ISO ✅, EKAP linki ✅, storage_url=None ✅

Commit'ler: `a84f313`, `badb449`, `6ded455` (main'de).

---

## 5. ⚠️ Sonraki AI İçin Kritik Tuzaklar

1. **`backend/supabase/__init__.py` SAHTE bir pakettir** — greenlet sorunu için httpx ile yazılmış supabase-py taklidi. `python backend/x.py` çalışınca `backend/` path'te ilk olduğu için **gerçek pip paketini gölgeler**. Yeni bir supabase özelliği (`.storage`, `.auth.admin`, realtime...) kullanılacaksa **önce wrapper'a eklenmeli**, yoksa `'Client' object has no attribute ...` ile sessizce patlar.
2. **Gemini**: `google-genai` paketi (yeni SDK), `google.generativeai` DEĞİL. Billing açık. Model: `gemini-2.5-flash` / `gemini-2.5-flash-lite`. En güncel/yetkin Claude/Gemini modellerini tercih et.
3. **e-Devlet login YOLU REDDEDİLDİ** — EKAP girişi e-Devlet ister, scraping'i şahsa hukuken bağlar. Girişsiz "vatandaş" yolunda kalınacak.
4. **Windows konsol** cp1254 — Unicode print çökertir; script `__main__`'de UTF-8 reconfigure yapıyor, yerel testte `PYTHONIOENCODING=utf-8` kullan.
5. **`.env`** `backend/.env`'de (gitignore'lu). Script `.env`'i OTOMATİK yüklemez; GitHub Actions env'leri secret'tan verir. Yerel testte elle yükle.
6. Tarihler **`tarih_iso()`**'dan geçmeli (Türkçe → ISO).

---

## 6. Yapılacaklar / Yol Haritası

### Yakın
- [ ] **733/11.878 belgeli oranını doğrula** — düşük görünüyor; `GetDokumanUrl` yoğunlukta boş mu dönüyor, yoksa çoğu ihale gerçekten belgesiz mi (`dokumanSayisi=0`)? Araştır.
- [ ] **Frontend kontrol** — `ihale-detay.html` belge linklerini "EKAP'ta Aç" olarak doğru gösteriyor mu (canlıda).
- [ ] **GitHub Secret** `GEMINI_API_KEY` — link-only için gerekmez ama ağır indirme açılınca lazım. (SUPABASE secret'ları zaten var, scraper çalışıyor.)
- [ ] Teknik borç: çift tablo isimleri (`takip`/`takipler`, `profil`/`kullanici_profiller`, `ihaleler`/`ilanlar`) — kanonik olanı belirle, ölüleri temizle.
- [ ] `backend/ekap_fields_check.py` debug dosyası (untracked) — gerekmiyorsa sil.

### Orta — ANA GELECEK ÖZELLİĞİ
- [ ] **Proaktif ihale eşleştirme**: Müşteri geldikçe → ilgili yeni ihalelerin şartnamelerini indir (`EKAP_BELGE_INDIR=1`, altyapı HAZIR) → **Gemini'ye yorumlat** (`analyzer.py` zaten şartname analizi yapıyor — başlangıç noktası) → firmanın profiline/sektörüne **uygun ihaleleri otomatik öner** (e-posta/dashboard). Bu, ürünün asıl satış değeri.
- [ ] Ağır indirme açılırsa: 45dk Actions timeout'u aşmamak için **sadece yeni/takip edilen** ihalelere indirme uygula (incremental). Gemini maliyeti hâlâ düşük (~$0.0001/çözüm).

### Uzun
- [ ] Kullanıcı onboarding / firma profili (sektör, OKAS kodları, il) → eşleştirme girdisi.
- [ ] Rekabet analizi & teklif oluşturma sayfalarının backend bağlantısı.
- [ ] Ödeme akışının uçtan uca testi (İyzico webhook → kredi).

---

## 7. Hafıza Notları (AI auto-memory'de)
- `ekap-belge-indirme-captcha` — 3 adımlı CAPTCHA akışı + cevap formatı + strateji + Gemini billing.
- `ekap-crypto-headers` — imzalı header üretimi + korumalı endpointler.
- `project-stack` — stack + **sahte supabase paketi uyarısı** + Cloudflare uzantısız URL.

---

## 8. Hızlı Başlangıç (yeni oturum)
```bash
# Yerel test (env yükleyerek)
cd backend && set -a && source .env && set +a
PYTHONIOENCODING=utf-8 EKAP_DETAY_LIMIT=2 python ekap_scraper.py   # 2 ihale test

# Link-only varsayılan; ağır indirme için: EKAP_BELGE_INDIR=1 (GEMINI_API_KEY gerekir)
```
Scraper akışı: liste çek → detay+ilan_html+belge linki → tekilleştir → Supabase `ilanlar` upsert → notify.py e-posta.
