# İhalePlatform — Yapılacaklar Listesi

> Son güncelleme: 28 Haziran 2026
> Bu dosya, Code modunda kodlama yaparken referans alınacak. Her madde mümkün olduğunca net ve uygulanabilir yazıldı.

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

## 🗺️ ÖNCELİK 2 — Türkiye Haritası (İl Bazlı Isı Haritası)

> Referans: ihalegram.com — Leaflet.js ile yapılmış, çok temiz.

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
- ⚠️ **Kategori filtresi**: `kategori` kolonu DB'de NULL → server-side filtre imkânsız. Scraper kategori doldurmalı (ya da OKAS/CPV'den türet). Şu an kategori sadece uyum skoru için keyword-map ile kullanılıyor.
- ⚠️ Detaylı Ara'nın bazı alanları (teklif türü, ihale kaynağı, içerik türü, idare türü, işin/teslim/ödeme süresi, sınır değer) eklenmedi — bu kolonlar DB'de yok.
- ⚠️ **Veri-borcu (scraper):** `usul` ham i18n anahtarı (`...SEARCH_METHOD.OPEN`) olarak saklanıyor; ingest sırasında Türkçe'ye çevrilmeli. `baslik`/`idare` mojibake (çift-encode).

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

## 📋 ÖNCELİK 4 — İhale Listesi Kartı (Her ihale satırı)

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

## 📄 ÖNCELİK 5 — İhale Detay Sayfası (ihale-detay.html)

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

## 📊 ÖNCELİK 6 — Analiz Ekranları (Firma & Kurum Bazlı)

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

## 🔧 ÖNCELİK 7 — Altyapı / Entegrasyonlar

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
