# İhalePlatform — Yapılacaklar Listesi

> Son güncelleme: 1 Temmuz 2026
> Bu dosya, Code modunda kodlama yaparken referans alınacak. Her madde mümkün olduğunca net ve uygulanabilir yazıldı.
> 29 Haz 2026: **tendermeister.com** ve **ihaleciler.com** canlı olarak detaylı gezildi; rekabet/özellik-açığı analizi en alta "🆚 REKABET ANALİZİ" bölümüne eklendi (Öncelik 9). Önce o bölümü oku.

---

## 📌 KALICI ÇALIŞMA TALİMATI (HER YENİ AI OTURUMU BUNU UYGULAR)

> Bu bölüm, projede çalışan her yapay zekanın (Claude/Gemini/diğer) uyması gereken
> daimi kuraldır. Kullanıcı her seferinde tekrar söylemek zorunda kalmasın diye buraya yazıldı.

1. **Bu dosyayı sürekli güncel tut.** Bir madde üzerinde çalıştıktan sonra, ne yaptığını
   ilgili maddenin altına özetle (✅/🟡/⚠️ durum işareti + kısa açıklama + dokunulan dosyalar).
   Tamamlananları "TAMAMLANDI", kısmi olanları "BÜYÜK KISMI TAMAM" gibi işaretle.
2. **Tavsiye ve öngörülerini ekle.** Çalışırken fark ettiğin iyileştirme, risk, teknik borç
   veya gelecekte yapılması gerekeni uygun başlık altına (ya da "GELECEK / FİKİRLER" bölümüne) yaz.
3. **Kullanıcının ileriye dönük isteklerini otomatik buraya işle.** Kullanıcı "şunu da isterim",
   "ileride şöyle olsun" derse, onu beklemeden bu dosyaya uygun maddeye/bölüme ekle.
4. **Önce öncelik sırasına bak** (en altta "Önerilen Sıra"). Aksi belirtilmedikçe o sırayı izle.
5. **Her özellik sonrası doğrula** (mümkünse tarayıcıda/Supabase'e karşı test) ve commit mesajında ne yaptığını açıkla.

---

## 🚀 CANLIYA ALMA İLERLEMESİ (5 Tem 2026)

**✅ Çözülenler:**
- **Anasayfa haritası prod'da bozuktu** → eksik `data/turkey-provinces.geojson` commit'lendi. Ayrıca il sayımı 13 istek yerine tek RPC'ye taşındı (`backend/migration_il_sayim_rpc.sql` — Supabase'de çalıştır; fallback var).
- **Dashboard'a Türkiye haritası eklendi** (giriş sonrası yoktu) → `js/harita.js` (yeniden kullanılabilir), ile tıklayınca `ihaleler?il=X`.
- **3 UX bug'ı:** (1) "EKAP'ta Görüntüle" 406 hata → çalışan public arama sayfası ("EKAP'ta Ara"); (2) AI analiz kutusundaki `python analiz_runner.py` geliştirici metni → "Teklif Hazırla" CTA; (3) Dashboard→Kurum Analizi "parametre eksik" → İdareler Dizini'ne yönlendirme.
- **🔴 GECE CRON'U ÇÖKMÜŞTÜ (4 gün 0 kayıt)** → kök neden: `upsert(ignore_duplicates=True)` sahte supabase wrapper'ında desteklenmiyordu, her yazma sessizce TypeError. Wrapper düzeltildi (commit 5e5a08e). Cron yarından itibaren tekrar çalışır. Bugünkü veri elle tam turla tazelendi.

**⏳ Devam eden / planlanan:**
- **Tüm geçmiş (2003+) backfill** (kullanıcı kararı): EKAP'ın sonuçlanmış listesi (~1.68M) taranacak → milyonlarca kayıt. GEREKSİNİM: (a) Webshare proxy (boş — IP ban riski), (b) Supabase plan yükseltme (free tier milyonları kaldırmaz), (c) ayrı checkpoint'li backfill workflow'u (`ekap_sonuc_backfill.py` temeli var). Firma/yüklenici verisi bunun çıktısı olarak gelecek.
- Cron'un GitHub Actions'ta gerçekten yeşil döndüğünü ilk gece sonrası doğrula (`olusturulma` bugüne yakın mı).

---

## 🖥️ BÜYÜK PLAN — TEK VDS'E TAŞIMA (5 Tem 2026, DEVAM EDECEK)

> **Bu bölüm bir sonraki oturum/AI için devir notudur.** Kullanıcı sistemi tek bir sunucuda
> (VDS) birleştirmeye karar verdi. Aşağıdaki karar/gerekçe/plan aynen sürdürülecek.

### KARAR & GEREKÇE
- **Hedef:** Şu an dağıtık olan sistemi (Cloudflare Pages + Supabase + Render + GitHub Actions)
  **tek bir Türk VDS'te** birleştir.
- **3 neden:** (1) tek pencereden yönetim (bugün cron 4 gün sessiz çökmüştü — dağıtık sistemin bedeli),
  (2) milyonlarca geçmiş ihale satırını **ucuza/sınırsız** saklama (Supabase free 500MB yetmiyor,
  Pro $25/ay pahalı bulundu), (3) **KVKK / kamu:** kamuyla çalışılacağı için veri **Türkiye'de**
  tutulmalı (Cumhurbaşkanlığı Bilgi ve İletişim Güvenliği Rehberi + kamu ihale şartnameleri veri-yeri ister).
- **Kritik:** Sağlayıcı **fiziksel olarak Türkiye'de** olmalı. Yurt dışı olursa gerekçe çöker → o durumda
  Hetzner (~€4/ay, daha ucuz/güvenilir) tercih edilir. Yani "Türk sağlayıcı"nın TEK sebebi veri-yeri.

### SAĞLAYICI SEÇİMİ (KARAR AŞAMASINDA)
Kullanıcı Türk VDS bakıyor. Değerlendirilen adaylar (spec ~4-6 çekirdek / 8-10GB RAM / 60-130GB, Ubuntu 22.04, tam root):
- **Hosting Dünyam — TR-VDS6:** 4 çekirdek E5-2699v4 / 8GB ECC / 60GB SATA SSD / 395₺/ay. İstanbul, Tier III+, %99.9. Sağlam.
- **Datacasa — Premium Sunucu 10:** 6 çekirdek E5-2698v4 / 10GB / **130GB NVMe** / 349,99₺/ay. Spec/fiyat daha iyi
  AMA **datacenter Türkiye'de mi doğrulanmalı** (belirsiz) + sağlayıcı itibarı teyit edilmeli. Türkiye'deyse tercih edilir.
- ⚠️ Alınacak ürün MUTLAKA **VDS / Cloud Sunucu (tam root)** olmalı — "Hosting/Web Hosting" DEĞİL.
- Öneri seviyesi: 8GB RAM yeterli (analiz için); 12GB gerekince sonradan yükseltilir. CPU farkı ikincil.

### SSH ANAHTARI (HAZIR)
- Kullanıcının makinesinde üretildi: **`~/.ssh/ihale_oracle`** (private) + **`~/.ssh/ihale_oracle.pub`** (public).
- Public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJgxU49zYE9enXlSCbgAwddf+dTIZai9VrtgDlJJYMdN ihale-oracle-vm`
- Herhangi bir sağlayıcıda geçerli. VM alınca panele eklenir ya da root şifresiyle sonra kurulur.

### HEDEF MİMARİ (VDS üstünde)
| Bileşen | Nasıl | Şu an nerede |
|---|---|---|
| DB + Auth + API + RLS + Storage | **Self-hosted Supabase** (Docker) — supabase-js/frontend/RLS AYNEN çalışır, sadece URL değişir | Supabase (managed) |
| Backend API | FastAPI → `systemd` + `uvicorn`, önünde nginx | Render |
| Scraper | Linux `cron` → `python ekap_scraper.py` (gece) | GitHub Actions |
| Geçmiş backfill | VM'de uzun süren checkpoint'li iş (Actions 6h/Render cron yok — VM'de sınır yok) | (yapılmadı) |
| Frontend | nginx (statik) — AMA **Cloudflare önde proxy** kalsın (bedava CDN+DDoS+SSL, sıfır yönetim) | Cloudflare Pages |

### DEPOLAMA STRATEJİSİ — HİBRİT (ÖNEMLİ)
- Tam ihale satırı ~**25KB** (ilan HTML dahil), kompakt ~**0.5KB** → **50x fark**.
- **Aktif/güncel ihaleler (~12k): TAM HTML sakla** (detay + içerik araması + AI). ~300MB, ucuz.
- **Geçmiş arşiv (milyonlarca): KOMPAKT sakla** (meta + sonuç: yüklenici/bedel/tenzilat). ~4GB.
- Geçmişi HTML'li saklasaydık ~40-100GB gerekirdi (60GB'a sığmazdı). Kompakt sayesinde TR-VDS6/130GB rahat.
- **Backfill script'i bu mantıkla yazılacak (geçmiş = kompakt, HTML yok).**

### FAZLAR (adım adım)
1. **Faz 1 — Hesap + VM (KULLANICI):** Türk VDS al (Ubuntu 22.04, ~8GB, tam root). Datacasa'yı seçerse önce
   "Türkiye'de mi + itibar" doğrula. IP + root erişimini AI'a ver.
2. **Faz 2 — Sunucu kurulumu (AI, SSH'tan):** Docker + docker-compose, güvenlik duvarı (ufw: 22/80/443),
   SSH sertleştirme (key-only), self-hosted Supabase stack.
3. **Faz 3 — Uygulamalar:** FastAPI systemd servisi, scraper cron, nginx (frontend + reverse proxy).
4. **Faz 4 — Veri taşıma:** Supabase → yeni Postgres (pg_dump/restore), Storage `belgeler` bucket taşı,
   frontend'in SUPABASE_URL/KEY'lerini yeni VM adresine çevir, RLS policy'lerini uygula (backend/rls_*.sql).
5. **Faz 5 — Geçmiş backfill:** VM'de kompakt 2003+ backfill başlat (ekap_sonuc_backfill.py temeli) → firma verisi dolar.
6. **Faz 6 — Cut-over:** Cloudflare DNS'i VM'e çevir (proxy açık), uçtan uca test, sonra eski servisleri kapat.
- **Paralel çalışılacak:** mevcut managed sistem taşıma boyunca AYAKTA kalır, sadece test bitince DNS çevrilir → sıfır kesinti.

### AÇIK KARARLAR / SIRADAKI
- [ ] Kullanıcı sağlayıcı+paketi kesinleştirsin (Datacasa Türkiye'deyse o; değilse Hosting Dünyam TR-VDS6 ya da Hetzner).
- [ ] VM alınınca: **Public IP + root erişimi** → Faz 2 başlar.
- [ ] Kullanıcının kendi tercihi: taşımayı launch'tan ÖNCE yapıyor (managed paralel ayakta kalacağı için risksiz).

---

## 🔐 CANLIYA ALMA — GÜVENLİK DENETİMİ & E2E (4 Tem 2026)

> Canlı Supabase'e karşı anon key + gerçek test kullanıcısı (signup→login) ile uçtan uca denetim yapıldı.

**✅ Okuma (veri sızıntısı) tarafı TAM KORUMALI:**
- Tüm kullanıcı tabloları (`profil`, `kullanici_krediler`, `kredi_hareketleri`, `bildirimler`, `teklifler`, `takipler`, `kullanici_profiller`) anon SELECT'e `[]` / `count */0` döndü → RLS okumayı filtreliyor.
- Kimlik doğrulanmış kullanıcı SADECE kendi satırlarını görüyor; `kredi_hareketleri` no-filter sorgusu bile `*/0` (başkasınınki görünmüyor).

**✅ Yazma tarafı — doğrulananlar:**
- `profil`: kendi satırını yazabiliyor (201), **başka user_id ile yazma RLS'le engellendi (403/42501)**.
- `takipler`: kendi satırı OK, **çapraz-kullanıcı yazma engellendi (403)**.
- `kullanici_krediler.kalan_kredi` **generated (hesaplanan) kolon** → doğrudan kredi yazılamıyor. İyi tasarım.

**🔴 KRİTİK AÇIK — ONAYLANDI (policy listesiyle, 4 Tem 2026):**
- `kullanici_krediler` ve `kredi_hareketleri` policy'leri `cmd=ALL` + `auth.uid()=kullanici_id`, WITH CHECK boş → INSERT/UPDATE'te USING'e düşüyor. **Giriş yapmış kullanıcı kendi kredi satırını UPDATE edebiliyor** (`toplam_kredi`'yi şişir → `kalan_kredi` hesaplanan kolon otomatik artar → sınırsız bedava kredi, İyzico bypass).
- **DÜZELTME HAZIR → `backend/rls_fix_kredi.sql`'i Supabase SQL Editor'da çalıştır.** İki tabloyu salt-okur yapar. Backend payment.py service_role ile yazdığı için ödeme/kredi yükleme ETKİLENMEZ (frontend krediyi zaten sadece okuyor). **Canlıya/İyzico'ya geçmeden ÖNCE uygulanmalı.**
- `ilanlar`: GÜVENLİ — write policy'leri `yayinlayan_id`'ye bağlı; EKAP kayıtlarında `null` → kullanıcı EKAP ihalelerini değiştiremez.
- Denetim SQL'i: `backend/rls_audit.sql` (salt-okur, RLS on/off + policy listesi).

**🐛 BULUNAN & DÜZELTİLEN BUG — takip DB senkronu kırıktı (`js/takip.js`):**
- `from('takip')` → var olmayan tablo (gerçek ad `takipler`); kolon `user_id` → gerçek ad `kullanici_id`. Hatalar `catch{}` ile sessizce yutuluyordu → **takipler DB'ye hiç yazılmıyordu, sadece localStorage'da kalıyordu** (cihaz değişince/çıkışta kayboluyor).
- Düzeltme uygulandı ve canlıda doğrulandı (insert→read→delete OK, çapraz-kullanıcı yazma bloklu). Artık takip cihazlar arası senkron olacak.

**⚠️ Launch notu — e-posta doğrulaması KAPALI:** signup anında `email_verified:true` token verdi, onay adımı yok → sahte e-postayla hesap açılabilir. Ücretli ürün için Supabase Auth'ta e-posta doğrulamayı açmayı değerlendir.

### 🔲 YAPILACAK — E-posta doğrulamasını aç (canlıya almadan önce)
- [ ] Supabase Dashboard → **Authentication → Sign In / Providers → Email** → **"Confirm email"** seçeneğini AÇ.
  - Etki: yeni kayıt olan kullanıcı, e-postasındaki doğrulama linkine tıklamadan giriş yapamaz → sahte/çalıntı e-postayla hesap açılması engellenir.
  - Not: Doğrulama e-postaları Supabase'in varsayılan SMTP'siyle gider (düşük limit). Canlıda güvenilir teslim için **Authentication → Emails → SMTP Settings**'ten Resend SMTP'yi bağla (Resend zaten bildirimler için kullanılıyor).
  - Test: aç → yeni bir e-postayla kayıt ol → giriş engellenmeli, kutuya doğrulama maili düşmeli.

**🧹 Temizlik:** Denetimde 1 test kullanıcısı oluşturuldu (`e2e.test.1783161485@ihaleglobal-e2etest.com`). Profil satırı silinemedi (profil'de DELETE policy yok — zararsız). Supabase Dashboard → Auth → Users'tan bu test kullanıcısını silebilirsin (profil satırı cascade gider).

---

## 🔴 ÖNCELİK 1 — Acil Bug'lar (Önce bunlar çözülmeli) — ✅ TAMAMLANDI (28 Haz 2026)

### 1.1 Redirect Loop — ✅ ÇÖZÜLDÜ
**Kök neden:** Cloudflare Pages zaten `/sayfa.html`'i uzantısız `/sayfa` adresinde servis edip `/sayfa.html → /sayfa` 301'i KENDİSİ yapıyor. `_redirects`'teki `/sayfa → /sayfa.html` kuralı bunun tersi → sonsuz döngü.
**Çözüm:** `_redirects`'teki TÜM aynı-isimli 301 kuralları kaldırıldı (tüm iç linkler zaten uzantısız). Dosyaya neden açıklaması eklendi.
- Ek olarak: hakkimizda/iletisim/mesafeli-satis sayfalarındaki `.html` uzantılı linkler uzantısıza çevrildi; kırık `/fiyatlandirma.html` → `/fiyatlandirma_odeme_bolumu`, var olmayan `/kullanim-kosullari` → `/kvkk` düzeltildi.

### 1.2 ihaleler.html crash — ✅ KONTROL EDİLDİ
- Referans verilen tüm JS dosyaları (`sidebar-user.js`, `plan.js`, `takip.js`) mevcut; eksik dosya crash'i yok.
- **Ayrıca bulunan gerçek bug:** index.html ve dashboard.html, `ilanlar` tablosunda var olmayan `created_at` kolonunu sorguluyordu → `Promise.all` çöküyor, tüm sayaçlar "—" kalıyordu. Doğru kolon `olusturulma` ile düzeltildi.

### 1.3 Login → Dashboard akışı — ✅ KOD DOĞRULANDI
- Login `signInWithPassword` ile supabase-js session'ı kalıcılaştırıyor; dashboard `sb.auth.getUser()` ile aynı session'ı okuyor → oturum korunuyor. Dashboard'da login'e zorla atan guard yok (loop riski yok). Canlı E2E testi deploy sonrası yapılmalı.

### 1.4 ilanlar tablosu — ✅ DOLU (premise yanlıştı)
- `ilanlar` tablosunda **11.878 gerçek kayıt var** (curl ile doğrulandı). YAPILACAKLAR'daki "0 kayıt" bilgisi eskiydi; PROJE_DURUM doğru.
- ⚠️ Not: scraper her upsert'te `olusturulma`'yı bugüne çektiği için "Bugün Eklenen" şişkin (≈11.868). Gerçek "yeni eklenen" semantiği için ayrı bir `ilk_gorulme` kolonu gerekir (gelecek iş).
- ⚠️ Veri kalitesi: `baslik`/`idare` alanlarında Türkçe karakter mojibake (çift-encode) var — scraper encoding düzeltmesi gerekiyor (gelecek iş).

---

## 🗺️ ÖNCELİK 2 — Türkiye Haritası (İl Bazlı Isı Haritası) — ✅ TAMAMLANDI (28 Haz 2026)

> Referans: ihalegram.com — Leaflet.js ile yapılmış, çok temiz.

**Yapıldı (index.html):**
- ✅ Leaflet.js choropleth harita (türkiye-provinces.geojson + Supabase il sayımı)
- ✅ Quantile-bazlı 6 renk skalası (navy→turuncu→kırmızı); proje temasıyla uyumlu
- ✅ Hover tooltip (il adı + sayı), hover'da sınır beyazlanır
- ✅ Legend: dinamik sayı aralıkları (örn. 0 | 1–42 | 43–76 | ...)
- ✅ Harita üstünde 3 sekme: **İlanlar** (aktif) | Firmalar "Yakında" | Kurumlar "Yakında"
- ✅ Bir ile tıklayınca → `ihaleler?il=İL_ADI` — ihaleler.html filtresi otomatik set edilir
- ✅ Özet kartlar: Toplam / Güncel / Bugün Eklenen / Kapsanan İl
- ✅ Lazy-load: harita görünür olunca başlar (IntersectionObserver)
- ⚠️ **Performans notu:** İl sayımı şu an 13 paralel istek (×1000 satır) ile yapılıyor. İdeal: Supabase'de `il_sayim()` RPC fonksiyonu (GROUP BY il) — gelecekte hız için eklenebilir.

### 2.1 Teknik altyapı
- **Kütüphane:** Leaflet.js 1.9.4 (CDN: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` + CSS)
- **Veri:** Türkiye 81 il sınırları GeoJSON dosyası (GitHub'da açık kaynak mevcut, repoya `data/turkey-provinces.geojson` olarak eklenebilir)
- **Render:** SVG tabanlı (81 path, her path bir il)

### 2.2 Görsel özellikler (ihalegram'dan birebir)
- Her il, içindeki ihale sayısına göre renklendirilir (choropleth / ısı haritası)
- **Renk skalası (8 kademe):** koyu lacivert `#312e81` → mor `#4338ca` → ... → kırmızı `#ef4444`
- **Legend (lejant):** Sağ altta `0 | 1-2k | 2k-4.7k | 4.7k-9.8k | 9.8k-17.6k | 17.6k-25.5k | 25.5k-33.3k | 33.3k+`
  - NOT: Bizim veri hacmimiz başta küçük olacağı için kademe aralıklarını dinamik hesaplamak daha doğru (örn. quantile bazlı). Sabit 33.3k aralıkları bizde hep koyu kalır.
- `fill-opacity: 0.9`, `stroke: #334155` (il sınırları)
- **Hover tooltip:** Sol üstte kutu → "İl Adı | ihale sayısı" (örn. "Kırıkkale | 1932")
- Hover'da ilin sınırı beyaza döner (vurgu)
- **Zoom kontrolü:** Sağ üstte +/- butonları

### 2.3 Etkileşim
- Bir ile **tıklayınca** → o il için ihale listesi filtrelenir (şehir filtresi otomatik o ile set edilir)
- Harita üstünde 3 sekme: **İlanlar | Firmalar | Kurumlar** (ihalegram'daki gibi — başta sadece "İlanlar" yeterli, diğerleri sonra)

### 2.4 Veri sorgusu (Supabase)
- `ilanlar` tablosundan il bazlı sayım:
  ```sql
  SELECT sehir, COUNT(*) as adet FROM ilanlar GROUP BY sehir;
  ```
- Sonuç bir JS objesine map'lenir: `{ "Ankara": 1234, "İstanbul": 5678, ... }`
- GeoJSON'daki il isimleriyle Supabase'deki `sehir` değerleri **birebir eşleşmeli** (Türkçe karakter / büyük-küçük harf normalizasyonu gerekebilir → eşleştirme tablosu)

### 2.5 Üst özet kartları (haritanın altında — ihalegram'daki gibi)
- **Bugün Yayınlanan** (sayı)
- **Bugün Bitecekler** (sayı)
- **Güncellenen İhaleler** (sayı)
- **Toplam İhale** (sayı) ← `ilanlar` tablosu COUNT

---

## 🔍 ÖNCELİK 3 — Gelişmiş Arama & Filtreleme — 🟡 BÜYÜK KISMI TAMAM (28 Haz 2026)

**Yapıldı (ihaleler.html):**
- ✅ 3.1 Sekmeler: Güncel / Geçmiş / Sonuç / Detaylı Ara (Güncel=teklif tarihi gelecekte, Geçmiş=geçmişte, Sonuç=veri yok→bilgi mesajı, Detaylı Ara=gelişmiş panel açılır)
- ✅ 3.2 Filtreler: Şehir (81 il statik), İhale türü (+Kiralama), İhale usulü (ham EKAP enum→ilike fragment eşleştirme), Yaklaşık maliyet **min-max**, İhale içeriği (full-text, 5 kolon OR ilike), Yayın tarihi aralığı
- ✅ 3.3 Detaylı Ara: İdare adı arama, Teklif tarihi aralığı, Yayın tarihi aralığı
- ✅ 3.4 Full-text (baslik+idare+okas+isin_yapilacagi_yer+ilan_metni)
- ✅ 3.5/3.6 Sıralama + sayaç + sayfalama (zaten vardı)

**Kalan / engelli (veri eksikliği):**
- ✅ **Kategori filtresi**: `ihaleler.html`'e KATEGORİ dropdown eklendi (29 kategori); scraper artık OKAS/CPV'den kategori türetiyor; `migration_kategori_backfill.sql` ile mevcut kayıtlar backfill edilebilir (Supabase SQL Editor'dan çalıştır).
- ✅ **Hızlı Tarih Filtreleri** (30 Haz 2026): `ihaleler.html`'e tab-bar ile filter-bar arası chip satırı eklendi — Tümü / Bugün / Bu Hafta / Son 7 Gün / Son 30 Gün. `f-yayin-bas`/`f-yayin-bit` giriş alanlarını siler veya set eder, "Detaylı Ara" panelini açmadan tek tıkla filtre uygular. Sıfırla butonu chip'i de sıfırlar.
- ⚠️ Detaylı Ara'nın bazı alanları (teklif türü, ihale kaynağı, içerik türü, idare türü, işin/teslim/ödeme süresi, sınır değer) eklenmedi — bu kolonlar DB'de yok.
- ✅ **Veri-borcu çözüldü (scraper):** `usul` artık Türkçe'ye çevriliyor; `baslik`/`idare`/`il` mojibake scraper'da düzeltiliyor. Mevcut kayıtlar için:
  - `migration_veri_temizlik.sql`: il UPPER normalize + ham usul enum düzeltme (Supabase SQL Editor'da çalıştır)
  - `mojibake_fix.py`: mevcut kayıtlardaki bozuk Türkçe karakterleri Python'da düzeltir (`--dry-run` ile önce test et)

### (orijinal plan ↓)
## 🔍 ÖNCELİK 3 — referans

> Hedef: ihaleciler.com kadar güçlü filtre, ama **daha sade/temiz** bir arayüz. Onların ekranı kalabalık; biz aynı gücü daha az görsel yükle vereceğiz.

### 3.1 Sekme yapısı (üstte)
ihaleciler.com'da 4 sekme var, bizde de olmalı:
- **Güncel** — açık/aktif ihaleler (teklif tarihi geçmemiş)
- **Geçmiş** — teklif tarihi geçmiş ihaleler
- **Sonuç** — sonuçlanmış / sözleşmeye bağlanmış ihaleler
- **Detaylı Ara** — tüm filtrelerin açıldığı geniş ekran

### 3.2 Temel filtre alanları (Güncel/Geçmiş/Sonuç sekmelerinde)
Her sekmede şu filtreler bulunmalı:
| Filtre | Tip | Not |
|--------|-----|-----|
| **Kategori** | dropdown | 32 kategori (ihaleciler.com taksonomisi) |
| **Şehir** | dropdown | 81 il |
| **İhale türü** | dropdown | Yapım İşi, Mal Alımı, Hizmet Alımı, Danışmanlık, **Kiralama** ← BİZDE EKSİK! |
| **İhale usulü** | dropdown | Açık, Pazarlık, Belli İstekliler, Doğrudan Temin vb. |
| **Yaklaşık maliyet** | aralık (min-max) | "₺X TL ye kadar" formatı |
| **İhale içeriği** | metin arama | İhalenin içinde geçen HERHANGİ bir kelime (full-text search) |
| **Yayın tarihi** | tarih aralığı (gg.aa.yyyy) | başlangıç–bitiş |

### 3.3 Detaylı Ara sekmesi (genişletilmiş — ihaleciler.com görsel 2'deki gibi)
Yukarıdakilere EK olarak:
- **Teklif türü** (E-ihale, Yerli istekli vb.)
- **İhale kaynağı** (EKAP, Yerel vb.)
- **İçerik türü**
- **İdare türü** (dropdown)
- **İdare adı** (metin arama)
- **Teklif tarihi** (tarih aralığı)
- **İşin süresi** (min-max gün)
- **Teslim süresi** (min-max)
- **Ödeme süresi** (min-max)
- **Sınır değer katsayısı**

### 3.4 Arama davranışı
- **"İhale içeriği" araması full-text olmalı:** ihale başlığı + işin niteliği + idare adı + tüm metin alanlarında arama yapmalı.
- Supabase'de `ilanlar` tablosuna full-text search index (Postgres `tsvector`) eklenebilir, ya da basitçe `ILIKE '%kelime%'` ile birden fazla kolonda OR araması.

### 3.5 Sıralama seçenekleri (sonuç listesi üstünde)
- Otomatik (varsayılan)
- Görüntülenme sayısı
- Yayın tarihi
- Teklif tarihi
- Şehir
- (Sonuç sekmesinde: Sözleşme tarihi, İş bitiş)

### 3.6 Sonuç listesi üst bilgi
- "Toplam: X ihale" sayacı
- Sayfalama: İlk sayfa | Önceki | [1. Sayfa ▼] | Sonraki | Son sayfa

---

## 📋 ÖNCELİK 4 — İhale Listesi Kartı — 🟢 TEMEL TAMAM (28 Haz 2026)

**Yapıldı (ihaleler.html):** Tablo düzeni zengin **kart** düzenine çevrildi. Her kartta:
- ✅ Kayıt no (ekap_id), tıklanabilir başlık (→ detay), idare adı
- ✅ Etiketler: EKAP (mavi), ihale türü, ihale usulü (ham enum→Türkçe), 📍 il
- ✅ Yaklaşık maliyet (aralık formatı), durum rozeti (Açık/Son N Gün/Kapandı)
- ✅ Tarihler: Yayın + Son Teklif; uyum % barı; Takibe Al + Detay butonları
- Hover efekti, dark/amber tema korundu. Tarayıcıda doğrulandı (25 kart, il filtresi dahil).

**Kart'ta gösterilemeyen (veri yok — sonuçlanmış ihale gerekir):**
- ⚠️ Yüklenici adı, sözleşme bedeli + tenzilat %, sözleşme/iş tarihleri, katılımcı sayısı.
  Bunlar "Sonuç" verisi toplanınca (Öncelik 6 / scraper sonuç ilanı) eklenebilir.

### 🔑 BULUNAN VERİ-BORÇLARI (filtrelerin tam değeri için ÖNEMLİ)
> Bunlar scraper (`backend/ekap_scraper.py`) ingest aşamasında düzeltilmeli:
1. **il değerleri Türkçe BÜYÜK HARF** (örn. `İSTANBUL`, `ANKARA`) — tutarsız (birkaç seed kaydı Title Case). Frontend dropdown buna göre büyük-harf value kullanacak şekilde ayarlandı, ama **ideal olan ingest'te normalize etmek** (Title Case). il-bazlı her yeni özellik (harita!) bu kasing'e dikkat etmeli.
2. **usul ham i18n anahtarı** (`...SEARCH_METHOD.OPEN`) — Türkçe'ye çevrilmeli.
3. **baslik/idare mojibake** (çift-encode Türkçe karakter) — encoding düzeltmesi.
4. **kategori kolonu NULL** — kategori filtresi için doldurulmalı (OKAS/CPV'den türetilebilir).
5. **olusturulma her upsert'te bugüne çekiliyor** → "Bugün Eklenen" sayacı şişkin; gerçek yeni-kayıt takibi için `ilk_gorulme` kolonu ekle.

---

## 📋 ÖNCELİK 4 — referans (orijinal plan)

> ihaleciler.com'daki ihale kartı çok detaylı. Bizimki de bu bilgileri göstermeli ama **daha sade** kartlarla.

### 4.1 İhale kartında gösterilecek alanlar
Her ihale kartında (Sonuç sekmesi örneği):
- **Kayıt no** (örn. `2026/796063`)
- **İhale başlığı** (tıklanabilir → detay sayfası)
- **Katılımcı adı** (varsa)
- **Yüklenici adı** (tıklanabilir → o firmanın tüm ihaleleri) ← firma bazlı arama linki
- **Yaklaşık maliyet** (₺ formatında)
- **Sözleşme bedeli** + **tenzilat yüzdesi** (yeşil rozet, örn. `%10,30`)
- **İdare adı** (tıklanabilir → o idarenin tüm ihaleleri) + **şehir**
- **Etiketler:** Ekap, ihale usulü (örn. "Pazarlık usulü")
- **Tarihler:** Yayın tarihi, Teklif tarihi, İş başlangıç, İş bitiş, Sözleşme tarihi
- **Durum rozeti:** Tamamlandı / Devam ediyor / Güncellendi
- **Aksiyon butonları:** Sözleşme listesi | Sonuç İlanı | Benzer ihale geçmişi
- **Yıldız (takip et)** + **ataç (dosya ekle)** ikonları

### 4.2 Uyum (compatibility) skoru
- Bizim ekstra özelliğimiz: kullanıcının seçtiği kategorilere göre uyum % skoru
- Hesap: kategori eşleşmesi (40p) + şehir (25p) + ihale türü (20p) + bütçe aralığı (15p)
- % olarak gösterilir (ihaleciler.com'da yok, bizim artımız)

---

## 📄 ÖNCELİK 5 — İhale Detay Sayfası — 🟢 BÜYÜK KISMI HAZIRDI (28 Haz 2026)

**Zaten vardı:** Header (EKAP#/IKN, başlık, idare+il, rozetler, Takibe Al / Teklif Hazırla / EKAP'ta Görüntüle), KPI grid (maliyet/son teklif/ilan tarihi/uyum), uyum skoru barı, sekmeler (İhale Bilgileri / İlan Bilgileri / Belgeler), benzer ihaleler.
**Bu oturumda eklendi/düzeltildi:**
- ✅ usul ham enum (`...SEARCH_METHOD.BARGAIN`) → "Pazarlık Usulü" (rozet + bilgi satırı; `usulLabel`)
- ✅ **AI Analizi sekmesi** eklendi: `yapay_zeka_ozeti` varsa gösterir (+analiz tarihi/tür), yoksa "Teklif Hazırla & Analiz Et" CTA'lı bilgilendirme. Tarayıcıda doğrulandı.

**Bu oturumda eklendi (28 Haz 2026):**
- ✅ **Kategori satırı**: İhale Bilgileri kartına `kategori` alanı eklendi; tıklanınca `ihaleler?kategori=X` filtreli lista açar
- ✅ **URL parametresi**: `ihaleler.html` artık `?kategori=`, `?usul=`, `?tur=` URL parametrelerini de destekler

**Kalan (veri yok):** İdare adres/telefon/toplantı adresi, sözleşme bilgileri bloğu (yüklenici/bedel/süre) — sonuçlanmış ihale + idare detayı toplanınca. CPV adı (sadece OKAS kodu var).

---

## 📄 ÖNCELİK 5 — referans (orijinal plan)

> ihaleciler.com'daki tek ihale detay sayfası yapısı (görsel: /tender/...)

### 5.1 Bloklar (yukarıdan aşağı)
1. **Üst butonlar:** Not ekle | Takip et | Tümünü yazdır | Benzer ihale geçmişi
2. **İhale bilgileri bloğu:**
   - Kayıt no, İhale başlığı, İşin adı, Yayın tarihi, Teklif tarihi, İhale türü, İhale usulü, İhale kaynağı, Teklif türü
3. **Kategori bilgileri bloğu:**
   - Kategori, Sektör (CPV kodu + isim, örn. `45234100 - Demiryolu İnşaatı İşleri`)
   - Butonlar: Güncel ihaleler | Geçmiş ihaleler | Analiz
4. **İdare bilgileri bloğu:**
   - İdare adı (tam hiyerarşi), adres, telefon, şehir, toplantı adresi
   - Butonlar: Güncel ihaleler | Geçmiş ihaleler | Analiz
5. **İhale konusu / işin niteliği** (uzun metin)
6. **Sözleşme bilgileri:**
   - Tarih, bedel, süre, yüklenici, yüklenici uyruğu, yüklenici adresi
7. **Footer:** "Bu ilan bilgilendirme amaçlıdır" + yayın tarihi

### 5.2 AI Analizi (bizim artımız)
- Gemini ile PDF analizi → ihale şartnamesinden özet, riskler, gereksinimler
- Detay sayfasında "AI Analizi" sekmesi/bloğu

---

## 📊 ÖNCELİK 6 — Analiz Ekranları (Firma & Kurum Bazlı) — 🟡 KISMI (28 Haz 2026)

**Yapıldı:**
- ✅ **`kurum-analiz.html`** oluşturuldu (`?kurum=IDARE_ADI` parametresiyle):
  - 4 KPI kartı: Toplam İhale / Aktif / Toplam Bütçe / Kapsanan İl
  - Genel Bakış sekmesi: Yıllık bar chart (Chart.js, `son_teklif_tarihi` fallback), İhale Türü breakdown (yatay progress bar), İl Bazlı Dağılım
  - İhale Listesi sekmesi: sayfalanmış kart listesi (20/sayfa)
  - Dokunulan dosyalar: `kurum-analiz.html`
- ✅ **idare isimlerini tıklanabilir** hale getirdi:
  - `ihaleler.html`: kart-idare → `kurum-analiz?kurum=...`
  - `ihale-detay.html`: detay-idare + info-row İdare → `kurum-analiz?kurum=...`
- ✅ `ihaleler.html` `urlFiltreleriUygula`: `?idare=` parametresi desteklendi (kurum-analiz'den "Tüm İhalelerini Gör" butonu)

- ✅ **`firma-analiz.html`** iskelet oluşturuldu ve Genel Bakış gerçek veriyle dolduruldu (30 Haz 2026):
  - 4 KPI kart: Toplam Kayıt / Aktif İhale / Kapsanan İl / Kapsanan Sektör (gerçek sayımlar)
  - **Genel Bakış sekmesi**: Yıllık bar chart (Chart.js) + İhale Türü progress bar + İl Dağılımı + Kategori Dağılımı
  - Sonuçlar sekmesi "Yakında" placeholder (yüklenici verisi gelince doldurulacak)
- ✅ **`kurum-analiz.html` Aylık Trend Grafiği** (30 Haz 2026): 24 aylık amber line chart Genel Bakış sekmesinde
  - Dokunulan dosyalar: `kurum-analiz.html`
- ✅ **`rekabet-analizi.html` İl + Kategori filtresi** (30 Haz 2026): topbar'a 2 yeni dropdown; `yukleData()` server-side filtreler
  - Dokunulan dosyalar: `rekabet-analizi.html`
  - İhaleler sekmesi: mevcut DB'den idare/başlık eşleşmeli kayıtları sayfalı listeler
  - Tüm sidebar nav'lara Firma/Kurum Analizi linkleri eklendi
  - Dokunulan dosyalar: `firma-analiz.html`

**Kalan:**
- ⚠️ Firma Sonuçlar & Genel Bakış sekmeleri: EKAP sonuç ilanı scrape edilince gerçek veri gelecek (yüklenici adı, sözleşme bedeli, tenzilat, KİK kararları)
- ⚠️ 6.3 Üst navigasyon (Kategoriler/Şehirler/Sektörler/İdareler/Yükleniciler/KİK) → veri tabanı dolunca eklenir



> ihaleciler.com'un en güçlü özelliği bu — firma/kurum bazlı detaylı istatistik.

### 6.1 Firma (Yüklenici) Analiz Ekranı
Bir firma seçilince gösterilecek özet (görsel 3'teki gibi):
- Geçmiş ihaleler (sayı + Listele)
- İptal edilen ihaleler
- KİK kararları
- Devam eden (sayı + toplam ₺)
- Tamamlanan (sayı + ₺ + €)
- Toplam iş bitirme (5 yıl) (sözleşme sayısı + ₺)
- Toplam sözleşme (sayı + ₺ + €)
- Yıllık ortalama
- Ortalama sözleşme bedeli
- **Ortalama tenzilat** (yüzde + tutar)
- Ortalama sözleşme süresi (gün)
- İlk sözleşme tarihi / Son sözleşme tarihi

**Alt sekmeler:**
- **Yıllık** tablo: Yıl | Ort. katılımcı | Ort. geçerli teklif | Devam eden | Tamamlanan | Ortalama sözleşme bedeli | Toplam sözleşme
- **Sektörler** tablo: Sektör (CPV) | Sektör adı | Güncel | Geçmiş | Devam eden | Tamamlanan | Toplam sözleşme
- **İdareler** tablo: İdare adı | Güncel | Geçmiş | Devam eden | Tamamlanan | Toplam sözleşme

### 6.2 Kurum (İdare) Analiz Ekranı
- İdare bazlı benzer istatistikler (o idarenin açtığı tüm ihaleler, hangi firmalar kazanmış vb.)

### 6.3 Üst navigasyon (ihaleciler.com menüsü)
ihaleciler.com'da üstte 6 ana kategori var, bunları değerlendir:
- **Kategoriler** (kategori bazlı ihale listesi + günlük sayılar)
- **Şehirler** (il bazlı + ilçe kırılımı)
- **Sektörler** (CPV kodu bazlı)
- **İdareler** (kurum bazlı)
- **Yükleniciler** (firma bazlı)
- **KİK Kararları**

---

## 📊 Dashboard İyileştirmeleri — ✅ TAMAM (30 Haz 2026)

**Yapıldı (dashboard.html):**
- ✅ **En Aktif Kurumlar** widget: aktif ihalelerdeki idare sayımı (tüm kayıtlar taranır, JS'te sıralanır), ilk 7 kurum amber progress bar + tıklanabilir kurum-analiz linki ile
- ✅ **Son Eklenen İhaleler** widget: `ilan_tarihi` DESC son 6 ihale (30 Haz: `olusturulma` → `ilan_tarihi` düzeltildi), başlık + il + maliyet + yayın tarihi + son teklif tarihi; ihale-detay linki
- İki widget yan yana 2 kolonluk grid düzeni, KPI grid altında, filtre üstünde
- ✅ **Kategori Dağılımı widget** eklendi: 12 renkli progress bar, tıklanınca `ihaleler?kategori=X` açar (28 Haz 2026)
- ✅ **KPI "Bugün Eklenen"**: `olusturulma` → `ilan_tarihi` ile düzeltildi (30 Haz 2026)
- ✅ **index.html "Bugün Eklenen" (harita + üst sayaçlar)**: `olusturulma` → `ilan_tarihi` düzeltildi (30 Haz 2026)
- ✅ **`ihaleler.html` `sekme` URL parametresi**: `?sekme=guncel/gecmis/sonuc/detayli` ile doğrudan sekme seçimi; `sektorler.html` "Geçmiş" butonu bu parametreyi kullanıyor

---

## 🤖 AI ANALİZ ALTYAPISI — ✅ TAMAMLANDI (28 Haz 2026)

**Yapıldı:**
- ✅ `backend/analiz_runner.py` oluşturuldu (Gemini 2.5 Flash + Supabase)
- ✅ `backend/migration_ai_analiz.sql`: `yapay_zeka_ozeti`, `analiz_tarihi`, `analiz_pdf_turu` kolonları
- ✅ `ihale-detay.html` AI Analizi sekmesi: 7 bölümlü renkli kart render (ÖZET/KİLİT BİLGİLER/GİRİŞ ENGELLERİ/MALİ YÜKÜMLÜLÜKLER/RİSKLER/FIRSATLAR/TAVSİYE)
- ✅ İlk 3 analiz başarıyla oluşturuldu ve Supabase'e kaydedildi (3640-3998 karakter/analiz)
- ✅ Supabase wrapper'a `in_()` ve `is_()` metodları eklendi (batch update + NULL filtre)

**Kullanım:**
```
python analiz_runner.py --limit 20        # 20 ihale analiz et
python analiz_runner.py --ikn 2026/123456  # tek ihale
python analiz_runner.py --yenile          # daha önce analizlenenleri yenile
```

---

## 🧹 VERİ TEMİZLİK — ✅ TAMAMLANDI (28 Haz 2026)

**Yapıldı:**
- ✅ **Usul normalize**: 5538 kayıt `SEARCH_METHOD.OPEN → Açık İhale`; Diğer (603), Doğrudan Temin (1292), Pazarlık 21/a (21), Pazarlık 21/e (10) düzeltildi
- ✅ **Usul normalize (kalan)**: Pazarlık 21/b (234), 21/ı (248), 21/c (12), 21/f (29), BARGAIN (4), Diğer (32) — tüm ham enum'lar temizlendi
- ✅ **Kategori backfill**: ~5500 kayıt OKAS/CPV'den 32 kategori türetildi; `in_()` batch ile
- ✅ **tur=Yapım fallback**: 246 kayıt `→ İnşaat & Yapım` (kategori boş olanlar)
- ✅ **tur fallback (tam)**: Mal (4199) → "Mal Alımı", Hizmet (1236) → "Hizmet Alımı", Danışmanlık (3) → "Danışmanlık"; kalan 9 OKAS kaydı da düzeltildi
- ✅ **Kategori dropdown güncellendi** (ihaleler.html): scraper ile tam uyumlu 50+ seçenek; "Genel" (Mal Alımı/Hizmet Alımı/Danışmanlık) + "Sektör" optgroup'ları
- ✅ **ekap_scraper.py** `kategori_tur()`: Mal/Hizmet/Danışmanlık tur fallback eklendi
- ✅ Supabase wrapper'a `in_()` batch + `is_()` NULL filtresi eklendi (timeout sorununu aştı)
- ⚠️ `ilk_gorulme` kolonu hâlâ yok — DDL gerektiriyor (Supabase SQL Editor'dan çalıştır: `migration_ai_analiz.sql`)
- ⚠️ `idx_ilanlar_analiz` btree index drop gerekiyor — `migration_fix_analiz_index.sql` Supabase SQL Editor'dan çalıştır

---

## 🔧 ÖNCELİK 7 — Altyapı / Entegrasyonlar — 🟡 KISMI (28 Haz 2026)

**Yapıldı (scraper kalite iyileştirmeleri):**
- ✅ `usul_donustur`: EKAP ham enum (`TENDER_SEARCH.ENUMERATIONS.OPEN` vb.) → Türkçe etiket (`Açık İhale`, `Pazarlık Usulü` vb.) haritası eklendi
- ✅ `supabase_yaz`: 2-pass upsert — yeni kayıtlarda `olusturulma` korunur, güncellemelerde üzerine yazılmaz ("Bugün Eklenen" şişkinliği önlendi)
- ✅ `tur_donustur`: "Kiralama" tipi eklendi

**Bu oturumda yapıldı (scraper kalite iyileştirmeleri — 28 Haz 2026):**
- ✅ `mojibake_duzelt()`: UTF-8 metin Latin-1 olarak yanlış decode edilmişse onarır; `baslik`/`idare`/`il` alanlarına uygulandı
- ✅ `kategori_tur()`: OKAS/CPV kodunun ilk 2 hanesinden 40+ kategori haritası; `tur`'dan fallback. `kategori` kolonu artık scraper'da doldurulacak
- ✅ `ilan_tarihi` çıkarma: `detay_cek()` → `ilanList[0].ilanTarihi/tarih/yayimTarihi/baslangicTarihi` ve `bilgi.ilanTarihi` fallback zinciri; `ihaleleri_isle()` → liste response alanlarından da fallback
- ⚠️ Debug print'ler eklendi — scraper çalışınca hangi field adının dolu geldiği görülecek; yanlış field adıysa düzeltilmeli
- ⚠️ `ilk_gorulme TIMESTAMPTZ DEFAULT NOW()` kolonu Supabase'de manuel eklenecek

**Kalan:**

### 7.1 EKAP Scraper (worker.py)
- Playwright ile EKAP'tan dinamik auth token yakalama
- 15 kategori için scraping listesi
- `ilanlar` tablosuna yazma
- Webshare.io rotating proxy entegrasyonu (IP ban önleme) — **credentials hâlâ boş**

### 7.2 İyzico Ödeme
- `iyzipay==1.0.46`
- Merchant credentials **hâlâ boş** (.env)
- `odeme_loglari` tablosunda UNIQUE `payment_id` (webhook replay koruması) — kurulu

### 7.3 AI (Gemini)
- PDF analizi: pdfplumber (metin) + Gemini Vision (taranmış belge fallback)
- Sonuçlar Supabase'de cache'lenir (tekrar API çağrısı önleme)

---

## 🎯 ÖNCELİK 8 — UX Felsefesi (Genel İlke)

> **"ihaleciler.com kadar güçlü, ama yarısı kadar kalabalık."**

- ihaleciler.com'un filtre gücünü al, ama görsel yoğunluğunu azalt
- Detaylı Ara'yı varsayılan değil, "ileri seviye" olarak konumla — sade kullanıcı 4-5 filtreyle iş görsün
- Harita ana sayfada öne çıksın (ihalegram'daki gibi) — görsel ve davetkâr
- Renk paleti: mevcut koyu lacivert/turuncu tema korunsun (ihaleglobal kimliği)

---

## ✅ Önerilen Sıra (Code modunda hangi sırayla yapalım)

1. **Redirect loop'u tümden çöz** (1.1) — site açılmadan hiçbir şey test edilemez
2. **worker.py çalıştır, ilanlar tablosunu doldur** (1.4) — veri olmadan harita/arama boş
3. **Gelişmiş arama + filtreler** (3) — çekirdek işlev
4. **İhale listesi kartları** (4) — verinin gösterimi
5. **İhale detay sayfası** (5)
6. **Türkiye haritası** (2) — görsel vitrin
7. **Firma/Kurum analiz ekranları** (6) — ileri özellik
8. **İyzico + AI** (7) — para kazanma + katma değer

---
---

# 🆚 ÖNCELİK 9 — REKABET ANALİZİ & ÖZELLİK AÇIKLARI (29 Haz 2026)

> **Kaynak:** 29 Haziran 2026'da **tendermeister.com** ve **ihaleciler.com** canlı hesaplarla uçtan uca gezildi
> (tendermeister'da tarama çalıştırıldı: 16 portaldan 136 ihale; ihaleciler'de firma analizi + KİK kararları açıldı).
> **Amaç:** ihaleglobal.com'da bu iki sitedeki HİÇBİR önemli özelliğin eksiği kalmasın. Aşağıdaki maddeler,
> "bizde var / kısmen var / yok" olarak işaretlendi ve P0–P3 öncelik verildi.
>
> **İşaretler:** 🟢 bizde var · 🟡 kısmen/iskelet var · 🔴 yok (eklenecek) · 🧱 veri-bağımlı (önce scraper)

## 9.0 Üç ürünün tek bakışta karşılaştırması

| Eksen | ihaleglobal (biz) | tendermeister | ihaleciler.com |
|---|---|---|---|
| **Konum** | TR / EKAP | DE menşeli, AB+DE+TR | TR (köklü) |
| **Kaynaklar** | EKAP | EU TED + 16 DE eyalet portalı + Bund.de + TR eKAP (18) | EKAP + Gazete + İstihbarat (özel) |
| **Çekirdek değer** | Takip + AI şartname analizi | AI eşleşme + ihale-başına AI teklif workflow | Veri zenginliği + firma/idare analitiği |
| **AI eşleşme** | basit ağırlıklı uyum % | semantik AI skor + %70 bildirim eşiği | yok (manuel filtre) |
| **Firma/idare analizi** | 🟡 iskelet | yok | 🟢 derin pivot (amiral gemisi) |
| **Sonuç/sözleşme verisi** | 🔴 yok | n/a | 🟢 var (analitiğin temeli) |
| **KİK kararları** | 🔴 yok | yok | 🟢 34.7k karar |
| **AI teklif yazımı** | 🟡 teklif-olustur.html (backend bağı eksik) | 🟢 KO tarayıcı + form doldurma + konsept yazıcı | yok |
| **Çoklu dil** | TR | TR/EN/DE/FR/AR | TR |
| **Fiyat** | Free / ₺1.490 / ₺3.990 | €299 / €499 / €899 | abonelik |

> **Stratejik okuma:** Türkiye pazarında asıl rakip **ihaleciler.com** (veri + analitik). tendermeister ise
> **ürün/AI vizyonu** açısından nereye gideceğimizi gösteriyor (AI Brain + ihale-başına teklif workflow'u).
> İkisinin kesişiminde durursak ("ihaleciler'in verisi + tendermeister'in AI'ı, daha sade arayüzle") fark yaratırız.

---

## 9.1 🧱 P0 — SONUÇ / SÖZLEŞME VERİSİ (her şeyin temeli) — 🟢 ÇALIŞIYOR, VERİ AKIYOR (1 Tem 2026)

> Bu olmadan firma-analiz, idare-analiz, "Sonuç" sekmesi, rekabet/fiyat istihbaratı ve uyum skorunun
> "kazanma oranı" iddiası BOŞ kalır. ihaleciler'in tüm gücü bu veriden geliyor. **En kritik açık.**

### ✅ 1 Tem 2026 — Uçtan uca çalışan pipeline kuruldu ve canlı veri akıyor

**Önemli düzeltme:** `backend/migration_sonuc_schema.sql` (29 Haz) hiç Supabase SQL Editor'dan çalıştırılmamış —
onun yerine Supabase'de **farklı, daha eski bir `ihale_sonuclari` şeması** zaten kuruluydu (muhtemelen bir
önceki oturumdan): `ilan_id` (ilanlar.id UUID FK) + `kazanan_firma` / `kazanan_teklif` / `en_dusuk_teklif` /
`en_yuksek_teklif` / `toplam_teklif_sayisi` / `kazanan_teklif_farki_yuzde` / `sonuc_tarihi` / `tum_teklifler` (jsonb).
`yukleniciler` ve `scrape_log` tabloları ise hiç oluşturulmamış (DDL gerektiriyor, SQL Editor'dan manuel).

**Doğru EKAP endpoint'i bulundu:** `ekap_sonuc_scraper.py --probe` çalıştırıldı — ihale bazlı "sonuç" endpoint'leri
(`GetByIhaleIdSonucIlan` vb.) hepsi 404 verdi. Ama zaten **çalışan** `GetByIhaleIdIhaleDetay` endpoint'i (ana
scraper'da aktif ihale detayı için kullanılıyor), ihale "Result Announcement Published" (durum kodu **"15"**)
durumundaysa yanıtına **`sozlesmeBilgiList`** (yüklenici adı, sözleşme bedeli, en yüksek/düşük teklif, sözleşme
tarihi) ve **`ilanList[].veriHtml`** içinde tam "SONUÇ İLANI" HTML metnini (teklif sayıları dahil) veriyor.
Yani ayrı bir "sonuç endpoint'i" yok — zaten var olan detay endpoint'i, sonuçlanan ihalelerde otomatik olarak
sonuç bilgisini de içeriyor.

**Verimli tarama yönü bulundu (deneme-yanılmayla):** Kendi DB'mizdeki "son_teklif_tarihi geçmiş" ilanları tek
tek EKAP'ta aratmak (IKN ile) çok düşük isabet verdi (rastgele örneklemde 0/15, 0/9, 0/4) — çünkü çoğu idare
"Sonuç İlanı"nı hiç yayınlamıyor ya da aylarca gecikmeli yayınlıyor; bizdeki "tarih geçmiş" olması EKAP'ta
sonuçlandığı anlamına gelmiyor. **Doğru yön tam tersi:** EKAP'ın zaten `ihaleDurumIdList=[5]` filtresiyle
"sonuçlanmış" (1.68M kayıt) listesini baştan sayfalayıp, her sayfadaki IKN'leri bizim ~12.7k IKN'lik kendi
`ilanlar` tablomuzla kesiştirmek — ilk 1000 kayıtta 7 isabet (%0.7) bulundu, çok daha verimli.

- ✅ **`backend/ekap_sonuc_backfill.py`** (yeni script — `ekap_sonuc_scraper.py`'nin varsayımları güncel şemayla
  uyuşmadığı için ayrı yazıldı, o dosyaya dokunulmadı):
  - Kendi `ilanlar` tablosunu `{ikn: {id, yaklasik_maliyet_min, ...}}` olarak indeksler
  - EKAP'ın durum=5 (sonuçlanmış) listesini sayfalar, IKN eşleşmesi bulunca `GetByIhaleIdIhaleDetay` çağırır
  - **Bulunan veri kalitesi sorunları ve düzeltmeleri:**
    - `sozlesmeBilgiList.yaklasikMaliyet(Degeri)` alanı EKAP'ta gözlemlenen örneklerde **10x hatalı** geliyor
      (örn. gerçek 26.737.250 TL yerine 267.372.500 TL) → bunun yerine **SONUÇ İLANI HTML metnindeki**
      "Yaklaşık Maliyeti" rakamı regex ile çıkarılıp kullanılıyor (`html_yaklasik_maliyet_parse`)
    - `ilanList` bazen hem orijinal ilanı hem sonuç ilanını içeriyor, sıra garanti değil →
      "SONUÇ İLANI" başlığını taşıyan girdi özellikle aranıyor (`sonuc_ilan_html_bul`)
    - Bazı (çok kısımlı/ithal) ihalelerde sözleşme bedeli **USD/EUR** cinsinden geliyor ama alan sayısal —
      TRY sanılırsa tenzilat hesabı tamamen bozuluyor → para birimi tespit edilirse o kayıt atlanıyor
    - Mojibake (Türkçe karakter bozulması) `mojibake_duzelt()` ile düzeltiliyor
  - Checkpoint dosyası (`.sonuc_backfill_checkpoint.json`) ile kaldığı yerden devam eder (kesintiye dayanıklı)
  - `--dry-run` ile DB'ye yazmadan test edilebilir
- ✅ **Canlı veri akıyor — ilk gerçek parti tamamlandı (1 Tem 2026)**: `ihale_sonuclari` tablosuna **15 gerçek
  sonuç kaydı** yazıldı (örn. "KESKİNLER GLOBAL DANIŞMANLIK... — 13.120.750 TL, tenzilat %50.93",
  "AKSU OTOM.PET... — 26.680.000 TL, tenzilat %5.26" vb.).
  **Önemli gözlem — plato tespit edildi:** EKAP'ın sonuçlanmış (durum=5) listesi tarandıkça, bizim ~12.7k IKN'lik
  havuzla kesişim sadece listenin **ilk ~16-20 bin kaydında** yoğunlaşıyor; skip=22.100'e kadar (toplam ~22k
  kayıt tarandı) yeni eşleşme çıkmadı, skip=100k/300k/600k/1M nokta kontrollerinde de sıfır eşleşme bulundu.
  Bu beklenen bir durum: EKAP listesi büyük ihtimalle yakın zamanda sonuçlanan ihaleleri önce veriyor ve bizim
  `ilanlar` tablomuz da esasen "yakın zamanda aktifti" ihalelerden oluşuyor — iki küme sadece dar bir pencerede
  kesişiyor. **Script artık bunu otomatik yönetiyor**: son 100 sayfada (10.000 kayıt) hiç yeni kayıt yazılmazsa
  plato tespit edilip tarama kendiliğinden durur (boşuna binlerce istek atılmıyor).
- ✅ **Frontend bağlandı (`ihaleler.html` + `ihale-detay.html`)**: "Sonuç" sekmesi artık gerçek veriyle çalışıyor —
  eskiden hiç dolmayan `ilanlar.durum='sonuclandi'` filtresi yerine PostgREST'in **otomatik FK embed**
  özelliği kullanıldı: `ilanlar?select=...,ihale_sonuclari!inner(...)` (view/RPC gerekmeden, FK zaten
  tanınıyor). Her ihale kartına, sonucu varsa yeşil "✓ Sonuçlandı — Kazanan: X · ₺Y · Tenzilat %Z" bloğu
  eklendi (diğer sekmelerde de sonuç varsa gösteriliyor). Sekme sayacı da `ihale_sonuclari` COUNT'una bağlandı.
  `ihale-detay.html` sayfa başlığının altına da aynı bilgiyi gösteren bir blok eklendi (`sonucBilgiGoster()`).
  Dokunulan dosyalar: `ihaleler.html`, `ihale-detay.html`
- **Kalan (bir sonraki oturum):**
  - **Hacmi büyütmenin gerçek yolu bu script'i daha sık koşmak DEĞİL** (aynı skip aralığını tekrar tekrar
    taramak aynı platoyu verir) — asıl kaldıraç **ana `ekap_scraper.py`'nin her gece daha fazla/farklı ihale
    keşfetmesi** (yeni aktif ihaleler zamanla sonuçlanıp bu havuza girecek) ve/veya EKAP'ın durum=5 listesinde
    farklı bir sıralama/filtre parametresi bulup (örn. tarih aralığı filtresi varsa) hedefli tarama yapmak.
    `--start-skip` ile farklı bir aralık da denenebilir ama önce spot-check yapılmalı (bu oturumda 100k/300k/
    600k/1M noktalarında sıfır çıktı, yani rastgele ileri atlamak muhtemelen boşuna).
  - `yukleniciler` + `scrape_log` tabloları hâlâ yok (DDL — Supabase SQL Editor'dan elle çalıştırılmalı);
    olmadan da `ihale_sonuclari` tek başına Sonuç sekmesi + gelecekteki firma-analiz için yeterli veri sağlıyor
  - Çok kısımlı (kısım/lot) ihalelerde şu an sadece ilk `sozlesmeBilgiList[0]` kaydediliyor — çoklu kazanan
    firma senaryosu (aynı ihalede birden fazla lot/kazanan) tek satıra sığmıyor; ileride ayrı bir
    `ihale_sonuclari_kisim` tablosu gerekebilir

- [x] 🟢 **DB şeması hazırlandı**: `backend/migration_sonuc_schema.sql` (29 Haz 2026)
  - `ihale_sonuclari` tablosu (yüklenici, sözleşme bedeli, tenzilat, katılımcı sayısı vb.)
  - `yukleniciler` tablosu (firma sözlüğü: normalize_ad, ciro, sözleşme sayısı)
  - `scrape_log` tablosu (hangi ihaleler denendi, başarılı mı?)
  - `ilanlar_sonuc` VIEW (ilanlar + ihale_sonuclari join)
  - `idare_sayim()` ve `kategori_sayim()` RPC fonksiyonları (performans için)
  - ⚠️ **Çalıştır**: Supabase SQL Editor'dan `backend/migration_sonuc_schema.sql`
- [x] 🟢 **`backend/ekap_sonuc_scraper.py`** oluşturuldu (29 Haz 2026)
  - `--probe` modu: 1-11 arası durum kodları + tüm endpoint kombinasyonlarını test eder
  - `--limit N`, `--ikn IKN`, `--all`, `--retry-failed` parametreleri
  - 5 farklı EKAP sonuç endpoint'i sırayla denenir (kesinlesme/sonuc_ilan/karar/sozlesme/sonuc_detay)
  - `yukleniciler` tablosuna upsert (normalize_ad ile dedup + ciro/sayı güncelleme)
  - ⚠️ **Önce probe çalıştır**: `python ekap_sonuc_scraper.py --probe`
- [ ] 🔴 **EKAP sonuç ilanı (kesinleşen ihale kararı / sözleşme) scrape'i** — `ekap_scraper.py`'a yeni akış:
  - Çekilecek alanlar: **yüklenici adı + vergi no/uyruk**, **sözleşme bedeli**, **yaklaşık maliyet**, **tenzilat %**,
    **katılımcı sayısı**, **geçerli teklif sayısı**, **sözleşme tarihi**, **işe başlama/bitiş**, **iş bitirme belgesi tutarı**.
  - EKAP v2'de sonuç endpoint'i araştır (`GetByIhaleIdSonucIlan` / `KesinlesenIhaleKarari` benzeri); yoksa
    "Sonuç İlanı" HTML'ini ayrıştır.
- [ ] 🔴 **DB şeması**: `ilanlar`a sonuç kolonları veya ayrı `ihale_sonuclari` + `firma_istatistikleri` tablosu
  (PLATFORM_CONTEXT'te zaten planlı — hayata geçir). Yüklenici adlarını normalize et (tekil firma anahtarı).
- [ ] 🔴 **`yukleniciler` tablosu** (firma sözlüğü): ad, vergi no, normalize_ad, toplam sözleşme, sektör[].
- **Tahmini etki:** Bu tek iş, 9.2 + 9.3 + 9.7'nin önünü açar. **İlk yapılacak P0 bu.**

> ✅ **Önemli düzeltme (29 Haz 2026):** "hangi idare / hangi sektör" verisi ASLINDA ZATEN YAZILIYOR.
> `ekap_scraper.py` upsert kaydında: `idare` (idareAdi) ✅, `il` ✅, `okas` (CPV/OKAS kodu) ✅,
> `kategori` (OKAS'tan türetiliyor) ✅. Yani her ihalenin idaresi ve sektörü DB'de var.
> **Eksik olan üç şey:** (1) idare bazlı **arama/dizin sayfası** (9.9), (2) **CPV-kodu seviyesinde sektör**
> gezinmesi — şu an sadece OKAS ilk-2-hane ana kategori var (9.9), (3) **geçmişte ihale alan firma listesi**
> = yüklenici/sonuç verisi (bu madde, 9.1). Yani idare/sektör için "veri yok" değil, "arama yüzeyi yok".

### 9.1.1 🕰️ Geçmiş (bugünden önceki) veri & kaynak — HUKUKİ NOT

> Kullanıcı sorusu: "Geçmişe yönelik veriyi çekmek için ihaleciler.com'dan veri çekebilir miyiz?"
> **Kısa cevap: Teknik olarak mümkün ama YAPMA — yanlış kaynak. Doğru kaynak EKAP'ın kendisi.**

- ⛔ **ihaleciler.com'dan veri kazımak RİSKLİ ve YANLIŞ:**
  - ihaleciler'in derlenmiş veritabanı onların **emeği/ürünü**; kullanım şartları otomatik veri çekmeyi yasaklar.
  - Bir rakibin DB'sini kopyalayıp **kendi ticari ürünümüzde** kullanmak Türkiye'de **haksız rekabet** (TTK m.54-55)
    ve sözleşme ihlali riski doğurur; üstelik bunu **kendi ücretli hesabımızla** yapmak ihlali ikiye katlar (hesap kapatma + hukuki risk).
  - Onların verisi de zaten çoğunlukla EKAP'tan türetilmiş — yani aracıdan kopyalamak yerine **kaynağa gitmek** hem
    yasal hem daha sağlam (onların scrape hataları/gecikmeleri bize miras kalmaz).
- ✅ **DOĞRU yol — geçmiş & sonuç verisini doğrudan EKAP'tan al (kamuya açık):**
  - EKAP **İhale Sonuç İlanları / Kesinleşen İhale Kararları**'nı KAMUYA açık yayınlar → yüklenici, sözleşme bedeli,
    tenzilat, katılımcı sayısı burada. Bunlar bizim **meşru** geçmiş-veri kaynağımız.
  - [ ] 🔴 **Geçmiş ihale backfill akışı**: mevcut scraper sadece AKTİF listeyi çekiyor (`GetListByParameters` ~11.878).
    Kapanmış/geçmiş ihaleleri ve sonuç ilanlarını çekmek için: tarih aralığı/sayfalama ile **geçmişe doğru tara**
    (EKAP v2'de kapanmış ihale + sonuç endpoint'lerini test et; yoksa sonuç ilanı HTML'ini ayrıştır).
  - [ ] 🔴 Backfill'i **incremental + idempotent** yaz (ikn bazlı upsert, dedup) — bir kez geçmişi doldur, sonra günlük ekle.
  - ⚠️ Gece Actions 45dk limiti → backfill'i ayrı, manuel/parça parça çalışan bir job olarak kur (cron değil).
- ℹ️ **ihaleciler'in "İstihbarat" kaynağı** (özel/erken intel) EKAP'ta YOK — o onların özel katma değeri.
  Onu kopyalayamayız/kopyalamamalıyız; karşılığını **kendi "özel sektör alım ilanları"** modülümüzle (9.6) kurarız.


---

## 9.2 📊 P1 — FİRMA (YÜKLENİCİ) & İDARE ANALİZİ (ihaleciler amiral gemisi) — 🟡 İSKELET VAR

> ihaleciler'in `/analyze` ekranı: bir yüklenici/idare/sektör için çok-boyutlu pivot. Her satırda "Listele" ile
> alttaki ihalelere iniliyor. Bizim `firma-analiz.html` + `kurum-analiz.html` iskeleti var ama veri yok.

- [ ] 🧱 **firma-analiz.html'i gerçek veriye bağla** (9.1 sonrası). Pivot tabloları (ihaleciler birebir):
  - **Yıllık**: Yıl · Ort. katılımcı · Ort. geçerli teklif · Devam eden · Tamamlanan · Ort. sözleşme bedeli · Toplam sözleşme
  - **Sektörler (CPV)**: CPV kodu · ad · Güncel · Geçmiş · Devam eden · Tamamlanan · Toplam sözleşme
  - **İdareler**: idare (tam hiyerarşi) · aynı kırılım
  - **Yükleniciler (rakipler)**: aynı sektörde yarışan firmalar
  - **Şehirler / İhale türü / İhale usulü / Teklif türü**: aynı kırılım
  - Üst KPI: Ortalama tenzilat %, ort. sözleşme süresi, ilk/son sözleşme tarihi, toplam iş bitirme (5 yıl)
- [ ] 🧱 **kurum-analiz.html'i derinleştir**: o idarenin açtığı tüm ihaleler, hangi firmalar kazanmış,
  ortalama tenzilat, tekrar eden yükleniciler (idare-firma ilişki ağı).
- [ ] 🔴 **`/analyze` esnek motoru**: herhangi bir filtre kombinasyonuna (firma+sektör+il) pivot üretebilen
  tek bir analiz endpoint'i (ihaleciler bunu yapıyor). Supabase RPC (GROUP BY) ile performanslı yaz.
- 🟢 Not: Bizim artımız → bu ekranlara **AI yorumu** ekleyebiliriz ("bu firma X idaresinde güçlü, tenzilatı düşük").

### 9.2.1 🔎 FİRMA ARAŞTIRMA MODÜLÜ (yeni — kullanıcı isteği 29 Haz 2026) — 🔴 YOK

> Kullanıcı net istedi: "geçmişte o işleri almış firmaları" araştırabileceğimiz bir **firma araştırma / firma
> istihbarat** modülü. **Kaynak = EKAP sonuç ilanları (kamuya açık olgu), ihaleciler DEĞİL.** Olgular serbest;
> derlemeyi biz yaparız. Bu modül, P0 sonuç verisi (9.1) gelince hayata geçer; `firma-analiz.html` bunun temeli.

**Veri (9.1'den gelir):** `yukleniciler` tablosu (firma sözlüğü: ad, normalize_ad, vergi_no?, il, sektör[]) +
`ihale_sonuclari` (ihale ↔ kazanan firma ↔ sözleşme bedeli, tenzilat, katılımcı/geçerli teklif sayısı, tarih).

**(a) Firma Dizini / Arama** (`/firmalar` veya yükleniciler dizini, 9.9):
- [ ] 🔴 Firma adına göre arama + sektör/şehir filtresi; toplam ciroya göre sıralama; sayfalama.
- [ ] 🔴 Her firma kartı: ad, şehir, toplam sözleşme sayısı, toplam ciro (₺), son iş tarihi → profile link.

**(b) Firma Profil Sayfası** (`firma-analiz.html?firma=...` — derinleştir):
- [ ] 🔴 **Kimlik**: ad, (varsa) vergi no, şehir, ana sektörler (CPV).
- [ ] 🔴 **KPI şeridi**: toplam sözleşme sayısı · toplam ciro · devam eden · tamamlanan · **ort. tenzilat %** ·
  ort. sözleşme bedeli · ilk/son sözleşme tarihi · 5-yıllık iş bitirme toplamı.
- [ ] 🔴 **Kazandığı ihaleler listesi** (drill-down, sayfalı): ihale adı · idare · bedel · tenzilat · tarih.
- [ ] 🔴 **Sektör (CPV) kırılımı**: hangi sektörlerde ne kadar iş aldı.
- [ ] 🔴 **İdare kırılımı / ilişki haritası**: hangi idarelerden iş alıyor (tekrar eden idare = güçlü ilişki sinyali).
- [ ] 🔴 **Rakip firmalar**: aynı ihalelerde yarıştığı/birlikte teklif verdiği firmalar (co-bidder ağı).
- [ ] 🔴 **Şehir / ihale türü / usul kırılımı** (Chart.js + tablo).
- [ ] 🔴 **Yıllık trend** grafiği (sözleşme sayısı + ciro / yıl).
- [ ] 🟡 **Ortaklık / konsorsiyum geçmişi** (JV ortakları) — sonuç verisinde ortak girişim bilgisi varsa.
- [ ] 🟢 **AI firma yorumu (artımız)**: Gemini ile özet — "bu firma X idaresinde baskın, Y sektöründe agresif
  tenzilat veriyor, son 1 yılda Z'ye yöneldi" → ihaleciler'de OLMAYAN katma değer.

**(c) Rakip Takibi** (üretkenlik — 9.10 ile bağlı):
- [ ] 🔴 Kullanıcı bir/birkaç **rakip firmayı takibe alır** → o firma yeni iş aldığında/teklif verdiğinde bildirim.
- [ ] 🔴 "Rakiplerim" panosu: takip edilen firmaların son hareketleri (kazandığı/girdiği ihaleler).

**Satış değeri:** "Rakibini araştır, hangi idareyle çalışıyor, ne kadar tenzilat veriyor, nereye yöneliyor — gör."
Bu, fiyat/rekabet istihbaratının (landing'de PREMIUM vaat edilen) somut karşılığı. **9.1 olmadan başlayamaz.**


---

## 9.3 ⚖️ P1 — KİK KARARLARI VERİTABANI — 🔴 YOK

> ihaleciler'de: **32.255 uyuşmazlık kararı + 2.454 mahkeme kararı**, kategori/şehir/tür/usul/şikayetçi/tarih ile aranır.
> Teklif verenin "itiraz edersem kazanır mıyım / bu idare çok mu şikayet alıyor" sorusuna cevap = yüksek katma değer.

- [ ] 🔴 **KİK kararları scrape** (kik.gov.tr / EKAP karar arşivi): karar no, tarih, idare, şikayetçi, konu, sonuç, tam metin.
- [ ] 🔴 `kik_kararlari` tablosu + arama sayfası (`kik-kararlari.html`): full-text + filtreler.
- [ ] 🟢 **Artımız**: kararları Gemini ile özetle ("emsal karar: benzer şikayet reddedilmiş") + ihale-detayda
  "bu idarenin/konunun emsal kararları" bloğu.

---

## 9.4 🧠 P2 — AI ŞİRKET PROFİLİ "BRAIN" + RAG BİLGİ TABANI — 🟡 profil.html var + doluluk skoru YAPILDI (30 Haz 2026)

**Yapıldı (30 Haz 2026):**
- ✅ **Profil Doluluk Skoru banner'ı** (`profil.html`): sektör(30p) + il(20p) + tür(20p) + bütçe(15p) + eşik(15p) = max 100p.
  Renk: yeşil(%80+), amber(%50+), kırmızı(<%50). Seçimler değiştikçe anlık güncellenir.
  Dokunulan dosyalar: `profil.html`

**Yapıldı (30 Haz 2026 — devam):**
- ✅ **Firma Adı input** eklendi (`profil.html`): Firma Bilgileri bölümü; `firma_adi` DB kolonuna kaydeder, sidebar'da gösterilir.
- ✅ **Anahtar Kelimeler alanı** eklendi (`profil.html`): virgülle ayrılmış özel kelimeler (ör: "boya, kaplama").
  `localStorage('ihale_anahtar_kelimeler')` ile anlık kaydedilir; DB'ye ayrıca best-effort upsert.
  Textarea oninput → kelimelerKaydet(); başlangıçta localStorage'dan önceden yüklenir.
- ✅ **Anahtar kelime bonusu** (`ihaleler.html`): uyumHesapla() sonuna +10p eklendi; ihale başlığında
  localStorage keywords bulunursa puan artar (Math.min ile 100'de kısıtlı).
  Dokunulan dosyalar: `profil.html`, `ihaleler.html`

> profil.html var, RAG yok

> tendermeister'ın kalbi: şirket profili sadece form değil, **bilgi tabanı**. Belgeler/referanslar/sertifikalar
> yüklenir → **indekslenir** → hem eşleştirmede hem teklif yazımında kullanılır. "Yapay Zeka Bilgi Düzeyi %"
> profil doluluğunu gösterir.

- [ ] 🔴 **Firma bilgi tabanı**: kullanıcı kendi belgelerini (iş bitirme, ISO, kapasite raporu, referans mektupları)
  yükler → Gemini ile özetlenir/embed'lenir → Supabase `pgvector`'da saklanır (RAG).
- [ ] 🔴 **Profil doluluk skoru** ("AI Bilgi Düzeyi %") — profili tamamlamaya teşvik (onboarding gamification).
- [ ] 🔴 **Profil alanları (tendermeister'dan eksiklerimiz)**: temel yetkinlikler, anahtar kelimeler,
  **sertifikalar/yeterlilikler** (uygunluk kontrolü için), **faaliyet yarıçapı (km)**, **min sözleşme değeri**,
  çok ülke kapsamı (yurtdışı için), iletişim kişisi.
- [ ] 🔴 **Otomatik CPV/OKAS kodu önerisi**: sektör+yetkinlikten AI ile CPV/OKAS belirlet (tendermeister CPV/NUTS yapıyor).
- 🟢 Mevcut `profil.html` + `kullanici_profiller` bunun iskeleti; üzerine RAG ve doluluk skoru eklenecek.

---

## 9.5 🤖 P2 — İHALE-BAŞINA AI TEKLİF WORKFLOW'U — 🟡 teklif-olustur.html var, entegre değil

> tendermeister'da her ihalenin "Detaylar"ı bir **workflow** sayfası: 6 sekme. Bizim `teklif-olustur.html` +
> `uyumluluk.html` + `ihale-detay.html` parçalı; bunları tek bir akışta birleştir.

- [ ] 🔴 **Belge yükle → AI sınıflandır**: kullanıcı şartname/eklerini (PDF/DOCX/XLSX/ZIP) yükler → AI tür ayırır
  (idari şartname, teknik şartname, birim fiyat cetveli, sözleşme tasarısı). (tendermeister: ZIP extraction + GAEB tanıma;
  bizde TR karşılığı = **birim fiyat cetveli / standart formlar** ayrıştırma.)
- [ ] 🔴 **KO (eleme) kriter tarayıcı** = bizim **uyumluluk** modülümüzün güçlendirilmiş hali: şartnameden zorunlu
  yeterlilik şartlarını (iş deneyim oranı, teminat, kapasite, belgeler) çıkar → firmanın bilgi tabanıyla (9.4)
  **"giriş engeli var/yok"** kontrolü. *uyumluluk.html'i buraya entegre et.*
- [ ] 🔴 **AI form doldurma**: standart formları (birim fiyat teklif mektubu, iş deneyim beyanı) firma profilinden doldur.
- [ ] 🔴 **AI konsept/teklif metni yazıcı**: teknik teklif/metodoloji taslağı üret (teklif-olustur.html'in backend bağı).
- [ ] 🔴 **Alt yüklenici / konsorsiyum modülü**: bu ihale için alt yüklenici/ortak öner (PLATFORM_CONTEXT'te konsorsiyum planlı).
- [ ] 🟡 **Bölünmüş ekran inceleme**: solda şartname, sağda teklif (nice-to-have).
- 🟢 Mevcut **AI Analizi sekmesi (7 bölüm)** zaten bu workflow'un "analiz" adımı — üzerine "aksiyon" adımlarını ekle.

---

## 9.6 📡 P3 — ÇOK KAYNAKLI RADAR + ANLIK TARAMA — 🟡 EKAP gece cron var

> tendermeister 18 portalı, ihaleciler 3 kaynağı (EKAP+Gazete+İstihbarat) topluyor. Biz tek kaynak + gece taraması.

- [ ] 🔴 **Gazete/özel sektör ilanları kaynağı** (ihaleciler'in "Gazete" + "İstihbarat"ı): özel sektör alım ilanları,
  resmi gazete ihale ilanları. (PLATFORM_CONTEXT'te "Özel sektör alım ilanları" zaten Faz 2'de planlı — başlat.)
- [ ] 🔴 **"Şimdi tara" / anlık yenile** butonu (kullanıcı tetikli incremental tarama) — gece cron'a ek.
- [ ] 🟡 **Yurtdışı/AB ihale altyapısı** (tendermeister EU TED yapıyor; PLATFORM_CONTEXT'te "Yurtdışı ihale altyapısı" planlı).
  → çok dilli arayüz gerektirir (9.8).
- 🟢 Bizim gece cron + link-only mimarimiz sağlam temel; üzerine kaynak çeşitliliği eklenecek.

---

## 9.7 🔔 P2 — AKILLI EŞLEŞME SKORU + BİLDİRİM EŞİĞİ — 🟡 UI TAMAM, AI BEKLEMEDE (30 Haz 2026)

**Yapıldı (29-30 Haz 2026):**
- ✅ **Minimum uyum eşiği kullanıcı ayarı**: `profil.html`'e "Akıllı Eşleşme Eşiği" bölümü eklendi
  - Range input (0–90, 5'er adım): Tümü(0) / %40+(40) / %60+(60) / %75+(75) / %85+(85) preset butonları
  - Seçilen değer hem `profil.min_uyum_esigi` Supabase kolonuna hem de `localStorage('ihale_min_uyum_esigi')` kaydedilir
  - `ihaleler.html` açılışında localStorage'dan okuyup filtre uygular (Supabase beklemeden anlık)
  - Dokunulan dosyalar: `profil.html`, `ihaleler.html`
- ✅ **"En İyi Eşleşmeler" widget** (`dashboard.html`): profil yüklendikten sonra 150 aktif ihale çekip
  `uyumHesapla()` ile skorlar, eşiği geçenlerin en iyi 6'sını 3×2 grid olarak gösterir.
  - Skor renkleri: yeşil (%80+), amber (%60+), gri (düşük)
  - Kalan gün göstergesi (kırmızı ≤3 gün), tıklanınca ihale-detay açılır
  - Profil yoksa "profilinizi doldurun" CTA; eşikten düşükse "eşiği düşür" yönlendirmesi
  - Dokunulan dosyalar: `dashboard.html`

- [ ] 🔴 **Semantik AI eşleşme**: şu anki uyum % formülü basit (kategori+il+tür+bütçe). tendermeister profil
  anahtar kelimeleri + CPV/NUTS + bilgi tabanıyla **semantik** skor veriyor. Gemini embedding ile firma profili ↔
  ihale şartnamesi benzerliği hesapla.

---

## 9.8 🌐 P3 — ÇOK DİLLİ ARAYÜZ — 🔴 sadece TR

- [ ] 🔴 i18n altyapısı (TR/EN, sonra AR). tendermeister 5 dil (AR dahil) sunuyor — yurtdışı/uluslararası firma hedefi için.
  Yurtdışı ihale (9.6) açılırsa zorunlu.

---

## 9.9 🗂️ P2 — VERİ ZENGİNLİĞİ & GEZİNME (ihaleciler dizinleri) — 🟡 DEVAM EDİYOR (30 Haz 2026)

> ihaleciler üst menüsü: **Kategoriler · Şehirler · Sektörler · İdareler · Yükleniciler · KİK Kararları** —
> her biri sayılı bir dizin sayfası. Bizde Kategoriler/Şehirler (harita) var; diğerleri eksik.
>
> ✅ Not: **idareye göre ve sektöre göre ARAMA için gereken veri DB'de zaten var** (`idare`, `okas`, `kategori`).
> Yani bu maddeler "veri toplama" değil, **arama/dizin yüzeyi (UI + GROUP BY sorgusu)** işidir → görece hızlı.

- [x] 🟢 **İdareye göre arama/dizin**: `idareler.html` oluşturuldu (29 Haz 2026).
  - Tüm idareler paginated batch ile çekilir, client-side GROUP BY + sort
  - Özet kartlar: Toplam İdare / Aktif İdareler / Toplam İhale / Aktif İhale
  - Arama (anlık filter), İl filtresi, 5 sıralama seçeneği (en çok ihale/aktif/isim/il)
  - Her satırda: idare adı, başlıca il, toplam sayı, aktif sayı, Analiz + İhaleler butonları
  - 50/sayfa sayfalama; sidebar nav'a tüm sayfalarda eklendi
  - Dokunulan dosyalar: `idareler.html` (yeni), sidebar güncellemesi (tüm sayfalar)
- [x] 🟢 **Sektörler dizini** (`sektorler.html`) oluşturuldu (30 Haz 2026).
  - `kategori_sayim()` RPC denemesi (varsa hızlı yol) → yoksa paginated batch fallback
  - Özet kartlar: Toplam Sektör / Aktif Sektörler / Toplam İhale / Aktif İhale
  - Arama, sıralama (en çok ihale/aktif/alfabetik/aktiflik oranı), min ihale filtresi
  - Her sektör kartı: ikon (45 sektöre emoji map) + toplam/aktif/kapandı sayıları + oran barı + "Aktif İhaleler / Tümü" butonları
  - Sidebar nav'a tüm sayfalarda eklendi
  - Dokunulan dosyalar: `sektorler.html` (yeni)
- ✅ **Sektörler & İdareler dizini geliştirmeleri** (`sektorler.html`, `idareler.html`) (30 Haz 2026):
  - `sektorler.html`: "Sadece Aktif" filtresi (min-filter select'e seçenek), ilk 3 sektöre 🥇🥈🥉 rozeti, her karta "📊 Analiz" butonu (→ `rekabet-analizi?kategori=X`), 🔗 Paylaş butonu (clipboard)
  - `idareler.html`: "Sadece Aktif" filtresi (ayrı select + event), 🔗 Paylaş butonu, Ctrl+K arama odağı kısayolu
  - `rekabet-analizi.html`: URL param desteği — `?kategori=X&il=Y&durum=Z` → sayfa açılışında filtreleri önceden doldurur (baslat() içinde URLSearchParams okuma). Sektör/İdare kartlarındaki Analiz linkleri artık filtreyi otomatik set eder.
  - Dokunulan dosyalar: `sektorler.html`, `idareler.html`, `rekabet-analizi.html`
- ✅ **Sidebar tutarlılığı tamamlandı (30 Haz 2026)**: Kurum Analizi + Firma Analizi + Sektörler nav linkleri tüm sayfalara eklendi.
  - `bildirimler.html` + `fiyatlandirma_odeme_bolumu.html`: eksik kurum-analiz/firma-analiz linkleri eklendi
  - `dashboard.html`: kurum-analiz ikonu 🏛️ → 🔍 düzeltildi
  - Tüm sayfalarda sidebar tutarlı
- ✅ **Sidebar son düzeltmeler (30 Haz 2026)**: `uyumluluk.html` + `dokumanlar.html` + `teklif-olustur.html` eski sidebar
  (href="#" Rekabet Analizi, eksik idareler/sektorler/kurum/firma-analiz linkleri) güncel yapıya çevrildi.
- ✅ **İhale Detay — Notlarım sekmesi** (`ihale-detay.html`): kişisel not alma alanı (localStorage `ihale_not_{id}`),
  auto-save oninput, karakter sayacı, temizle butonu, tab badge (not varsa · göstergesi). Rakiplerde yok — özgün özellik.
  Benzer İhaleler: kategori+il → kategori → tür waterfall; il göstergesi eklendi.
  Dokunulan dosyalar: `ihale-detay.html`, `uyumluluk.html`, `dokumanlar.html`, `teklif-olustur.html`
- [ ] 🔴 **Yükleniciler dizini**: geçmişte ihale alan firmaların listesi (9.1 sonuç verisi gelince) + analiz linki.
- [ ] 🔴 **Resmi KİK iş-deneyim grup taksonomisi** ((A) Köprü/Tünel/Karayolu… (B) Bina… (C) Tesisat… (D) Enerji… (E) Haberleşme):
  yeterlilik/iş deneyim eşleştirmesi için kategori ağacına ekle (ihaleciler'de var).
- 🟢 Bizim **Türkiye haritası** ihaleciler'de yok — bu bizim görsel artımız, koru/öne çıkar.

---

## 9.10 👤 P2 — HESAP / ÜRETKENLİK ÖZELLİKLERİ — 🟡 BÜYÜK KISMI TAMAM (30 Haz 2026)

> ihaleciler hesap menüsü: **Bültenlerim · Okuduklarım · Takip listem · Sözleşme listem · Bildirimler**.

**Yapıldı (29-30 Haz 2026):**
- ✅ **Kayıtlı Aramalar (Bültenlerim altyapısı)**: `ihaleler.html`'e "⭐ Aramayı Kaydet" + "📂 Kayıtlı" butonları
  eklendi. `KayitliArama` modülü localStorage (`ihale_kayitli_aramalar_v1`) ile saklar.
  - Filtre panelinin özeti okunabilir metne dönüştürülür (`filtrelerOzet`)
  - Modal ile isim verilerek kaydedilir; URL parametresiyle tek tıkla uygulanır
  - Dokunulan dosyalar: `ihaleler.html`
- ✅ **Bültenlerim sekmesi** (`bildirimler.html`): Kayıtlı aramaları listeler, "▶ Çalıştır" ile filtreli ihale listesi açılır,
  "✕ Sil" ile localStorage'dan kaldırılır. Sekme badge'i ile kayıt sayısı gösterilir.
  - Dokunulan dosyalar: `bildirimler.html`
- ✅ **Dashboard — Kayıtlı Aramalar widget**: Dashboard'da son 5 kayıtlı arama tıklanabilir linkler olarak gösterilir.
  - Dokunulan dosyalar: `dashboard.html`
- ✅ **Dashboard — Yaklaşan Son Tarihler widget**: Takip listesindeki aktif ihalelerin kalan günlerine göre renkli
  geri sayım kutuları (kırmızı ≤3g, amber ≤7g, yeşil >7g).
  - Dokunulan dosyalar: `dashboard.html`
- ✅ **Okuduklarım sekmesi** (`bildirimler.html`): `ihale_okundu_v1` localStorage'dan ID'leri okur, Supabase'den
  baslik/idare/il/tur/son_teklif_tarihi çeker, ihale-detay linki olarak listeler. Sekme badge'i ile sayı gösterilir.
  - Dokunulan dosyalar: `bildirimler.html`
- ✅ **Sözleşme Listesi sekmesi** (`bildirimler.html`) (30 Haz 2026): Takip.liste() ID'lerinden aktif ihaleleri çeker,
  kalan gün geri sayımıyla renkli kartlar gösterir (kırmızı ≤3g, turuncu ≤7g, yeşil >7g). Süresi dolmuşlar da listelenir.
  Sekme badge'i Takip sayısından beslenir. `sekmeGoster()` refactor edildi: tüm panel toggle mantığı array iteration'a çevrildi.
  - Dokunulan dosyalar: `bildirimler.html`
- ✅ **Rekabet Analizi — Aylık İhale Trendi** (30 Haz 2026): `rekabet-analizi.html`'e 24 aylık line chart eklendi.
  Amber dolgu, tension 0.3. `ilan_tarihi` → `son_teklif_tarihi` fallback. Mevcut chart'lardan önce gösterilir.
  - Dokunulan dosyalar: `rekabet-analizi.html`
- ✅ **Rekabet Analizi — Usul Dağılımı + Paylaş** (`rekabet-analizi.html`) (30 Haz 2026):
  - `usul` alanı data sorgusuna eklendi; `usulBarsRender()` ile yatay bar chart (mavi, top 8 usul) eklendi.
  - 🔗 Paylaş butonu: mevcut filtre state'ini URL parametrelerine (kategori/il/durum) kodlar + clipboard'a kopyalar. URL param desteğiyle (baslat() içinde URLSearchParams okuma) filtreli görünüm paylaşılabilir.
  - Dokunulan dosyalar: `rekabet-analizi.html`

**Kalan:**
- [ ] 🔴 **Bültenlerim e-posta**: kayıtlı arama → Supabase Edge Function ile günlük/haftalık otomatik e-posta özeti.
  (Şu an sadece UI; backend tetikleyici yok.)
- ✅ **Takip listem — Bittileri Kaldır butonu** (`takipte.html`) (30 Haz 2026): "↩ Bittileri Kaldır" butonu eklendi. Teklif tarihi geçmiş ihaleleri toplu olarak takip listesinden kaldırır; DOM güncellemesi + istatistik güncelleme. Dokunulan dosyalar: `takipte.html`
- ✅ **Takip listem — CSV Export** (`takipte.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()` fonksiyonu. BOM eklenerek UTF-8 Excel uyumlu CSV (id/ekap_id/baslik/idare/il/tur/durum/son_teklif_tarihi/yaklasik_maliyet_min). Dokunulan dosyalar: `takipte.html`
- ✅ **Uyumluluk — Takibe Al butonu** (`uyumluluk.html`) (30 Haz 2026): Her tablo satırına ☆/★ Takip toggle butonu eklendi; kategori sütun meta'ya eklendi; select sorgusuna `kategori` alanı eklendi. Dokunulan dosyalar: `uyumluluk.html`
- ✅ **Uyumluluk — CSV Export** (`uyumluluk.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()` fonksiyonu. `tumScoredIlanlar` global ile tüm eşleşmeler (aktif sayfa değil) export edilir; uyum % dahil. Dokunulan dosyalar: `uyumluluk.html`
- ✅ **Kurum Analizi — CSV Export** (`kurum-analiz.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()`. `tumIhaleler` global; dosya adında kurum adı + tarih. Dokunulan dosyalar: `kurum-analiz.html`
- ✅ **Firma Analizi — CSV Export** (`firma-analiz.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()`. `tumIhaleler` global; dosya adında firma adı + tarih. Dokunulan dosyalar: `firma-analiz.html`
- ✅ **İdareler Dizini — CSV Export** (`idareler.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()`. `filtrelenmis` array (uygulanan filtreler dahil) export edilir. Dokunulan dosyalar: `idareler.html`
- ✅ **Sektörler Dizini — CSV Export** (`sektorler.html`) (30 Haz 2026): "↓ CSV" butonu + `csvIndir()`. `filtrelenmis` array (aktiflik oranı dahil) export edilir. Dokunulan dosyalar: `sektorler.html`
- ✅ **Rekabet Analizi — Sıfırla butonu** (`rekabet-analizi.html`) (30 Haz 2026): Topbar'a ↺ Sıfırla butonu + `filtreleriSifirla()` fonksiyonu eklendi. Dokunulan dosyalar: `rekabet-analizi.html`
- ✅ **Profil — Belgeler & Yetkilendirmeler** (`profil.html`) (30 Haz 2026): Yeni section-card: textarea + localStorage(`ihale_sertifikalar`); `sertifikalarKaydet()` + init yükleme + kaydet() persist. Dokunulan dosyalar: `profil.html`
- ✅ **Profil — İletişim & Vergi bilgileri** (`profil.html`) (30 Haz 2026): Firma Bilgileri kartına İletişim Kişisi + Telefon + Vergi No alanları eklendi. localStorage(`ihale_iletisim_kisi`, `ihale_iletisim_tel`, `ihale_vergi_no`) ile saklanır. AI teklif workflow için zemin. Ctrl+S ile kaydet kısayolu eklendi. Dokunulan dosyalar: `profil.html`
- ✅ **Dashboard — Yaklaşan Bitiş widget budget** (`dashboard.html`) (30 Haz 2026): Yaklaşan Son Tarihler widget'ına yaklaşık maliyet + idare adı eklendi. Select sorgusuna `idare,il,yaklasik_maliyet_min,tahmini_bedel` eklendi. `paraCevir()` helper ile amber renkte maliyet gösterimi. Dokunulan dosyalar: `dashboard.html`
- ✅ **İhaleler — Alt+1/2/3/4 sekme kısayolları** (`ihaleler.html`) (30 Haz 2026): Ctrl+K yanına Alt+1 (Güncel), Alt+2 (Geçmiş), Alt+3 (Sonuç), Alt+4 (Detaylı Ara) kısayolları eklendi. Dokunulan dosyalar: `ihaleler.html`
- ✅ **Uyumluluk — Başlık/idare arama** (`uyumluluk.html`) (30 Haz 2026): Tablo araç çubuğuna metin arama inputu eklendi. `aramaFiltrele()` 250ms debounce ile `yukle(1)` tetikler; `yukle()` içinde client-side `f-arama` filtresi uygulanır (baslik/idare). Dokunulan dosyalar: `uyumluluk.html`
- ✅ **İhaleler — Hızlı Tarih Filtreleri** (30 Haz 2026): → bkz. Öncelik 3 güncelleme. Dokunulan dosyalar: `ihaleler.html`
- ✅ **Takip listem** (`takipte.html`) (30 Haz 2026): renkli kalan gün etiketleri (kırmızı ≤3g, turuncu ≤7g, yeşil),
  uyum renklendirmesi, topbar sıralama select (Son Eklenen / En Yakın Tarih / En Yüksek Uyum), il gösterimi kart alt satırına eklendi.
  `uyum.js` paylaşılan modülüne anahtar kelime bonusu (+10p) eklendi — takipte + dashboard da güncellendi.
  `firma-analiz.html`: Son Aramalar localStorage (`ihale_son_aramalar_firma_v1`) + tıklanabilir chips, `kategori`+`ilan_tarihi` select'e eklendi (grafik/sektör düzeltmesi).
  `ihale-detay.html`: `benzerIhaleler()` kategori+il → kategori → tür fallback zinciriyle güçlendirildi; il gösterildi.
    Son görüntülenenler tracking: `ihale_son_gorulenler_v1` localStorage'a id/baslik/idare/il/tarih kaydedilir.
  `dashboard.html`: "Son Görüntülenenler" widget eklendi (localStorage'dan okur, ihale-detay linkleri).
  `bildirimler.html`: Tarayıcı push notification banner (izin default ise gösterilir, Notification.requestPermission, dismiss → localStorage).
  Dokunulan dosyalar: `takipte.html`, `js/uyum.js`, `firma-analiz.html`, `ihale-detay.html`, `dashboard.html`, `bildirimler.html`
- ✅ **Dökümanlar — UX iyileştirmeleri** (`dokumanlar.html`) (1 Tem 2026):
  - Topbar'a "Tümünü Aç / Tümünü Kapat" toggle butonu eklendi; `tumAcik` state'i tutar.
  - ≤3 sonuç varsa tüm kartlar sayfa yüklenince otomatik açılır.
  - Ctrl+K → arama kutusuna odaklan kısayolu eklendi.
  - Alt+1/2/3 → Takip Dökümanları / Teknik / İdari sekme kısayolları eklendi.
  - Kart `<div>`'ine `data-id` eklendi (toggle-all'ın karta ulaşabilmesi için).
  Dokunulan dosyalar: `dokumanlar.html`
- ✅ **Bildirimler — UX & veri düzeltmesi** (`bildirimler.html`) (1 Tem 2026):
  - `sozlesmeListesiYukle()`: select sorgusuna `yaklasik_maliyet_min` eklendi; maliyet gösterimi `yaklasik_maliyet_min || tahmini_bedel` önceliğiyle güncellendi (diğer tüm sayfalarla tutarlı).
  - Alt+1–7 → sekme kısayolları: Tümü / Okunmamış / İhale / Sistem / Bültenlerim / Okuduklarım / Sözleşme Listesi.
  Dokunulan dosyalar: `bildirimler.html`
- ✅ **Uyumluluk — mojibake bug fix + arama performansı** (`uyumluluk.html`) (1 Tem 2026):
  - **Bulunan gerçek bug**: Pro kilit ekranı metni bozuk kodlanmıştı (`Uyumluluk Analizi � Pro �zelliği` / `g�re` / `�zeldir`) — düzgün Türkçe karakterlerle düzeltildi.
  - **Arama performans iyileştirmesi**: önceki oturumda not edilen optimizasyon uygulandı — `yukle()` artık sadece Supabase fetch+skor+min-uyum filtresini yapıyor; yeni `renderSayfa()` fonksiyonu metin araması + sayfalamayı `tumScoredIlanlar` üzerinde bellekte (anlık, Supabase'e gitmeden) uyguluyor. `aramaFiltrele()` artık debounce'lu `yukle(1)` yerine doğrudan `renderSayfa(1)` çağırıyor (250ms network gecikmesi kalktı). Sayfalama butonları da `renderSayfa()`'a yönlendirildi (sayfa değişince gereksiz refetch yok).
  Dokunulan dosyalar: `uyumluluk.html`
- [ ] 🟡 **Çok kanallı bildirim**: landing'de SMS/WhatsApp/Telegram vaat ediliyor ama backend yok → en azından
  **e-posta + tarayıcı push** (tendermeister push yapıyor) gerçekle; SMS/WhatsApp'ı sonra.

---

## 9.11 💰 Fiyatlandırma / konumlandırma notu

- tendermeister €299–€899 (kurumsal/AB). ihaleciler TR abonelik. Bizimki ₺1.490/₺3.990 — TR pazarına uygun.
- **Risk:** ihaleciler veri derinliğinde önde; biz **AI + sadelik + harita + uyum skoru** ile farklılaşmalıyız.
  Satış mesajı: *"ihaleciler'in tüm verisi + yapay zekâ ile teklif/analiz, yarısı kadar kalabalık arayüzde."*
- Bu yüzden **P0 (sonuç verisi) + P1 (analitik/KİK)** olmadan "ihaleciler'e eş" diyemeyiz; **P2 (AI Brain/teklif)**
  olmadan "tendermeister'e eş" diyemeyiz. Sıra bu yüzden aşağıdaki gibi.

---

## 🎯 ÖNERİLEN UYGULAMA SIRASI (Öncelik 9 için)

> "Asla eksiğimiz kalmasın" hedefi → önce ihaleciler paritesi (TR pazarı), sonra tendermeister AI vizyonu.

1. **P0 — Sonuç/sözleşme verisi scrape + şema** (9.1) → analitiğin yakıtı. *Her şeyden önce bu.*
2. **P1 — Firma & idare derin analizi** (9.2) → ihaleciler amiral gemisine parite.
3. **P1 — KİK kararları DB + arama** (9.3) → ihaleciler'in diğer büyük kozu.
4. **P2 — AI Brain + RAG profil** (9.4) → eşleşme ve teklifin temeli; profil alanlarını tamamla.
5. **P2 — Akıllı eşleşme skoru + eşik** (9.7) → AI farkı görünür olur.
6. **P2 — İhale-başına AI teklif workflow** (9.5) → tendermeister'in çekirdek değeri (uyumluluk.html'i entegre et).
7. **P2 — Hesap üretkenlik** (9.10: Bültenlerim, Okuduklarım, Sözleşme listem, push) + **dizinler** (9.9).
8. **P3 — Çok kaynak + anlık tarama** (9.6), **çok dil** (9.8), **yurtdışı/AB**.

> **Not (kalıcı talimat gereği):** Bu bölüm üzerinde çalışırken her tamamlanan maddeyi 🟢'ya çevir,
> dokunulan dosyaları yaz, ve yeni fark edilen açıkları buraya ekle. Veriye bağlı (🧱) maddeler 9.1 bitmeden başlamaz.
