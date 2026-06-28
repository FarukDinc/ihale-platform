# İhalePlatform — Yapılacaklar Listesi

> Son güncelleme: 28 Haziran 2026
> Bu dosya, Code modunda kodlama yaparken referans alınacak. Her madde mümkün olduğunca net ve uygulanabilir yazıldı.

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

- ✅ **`firma-analiz.html`** iskelet oluşturuldu (`?firma=AD` ile arama; idare/başlık içinde firma arar):
  - 4 KPI kart (3'ü "sonuç verisi bekleniyor")
  - Genel Bakış + Sonuçlar sekmesi "Yakında" placeholder (yüklenici verisi gelince doldurulacak)
  - İhaleler sekmesi: mevcut DB'den idare/başlık eşleşmeli kayıtları listeler
  - Tüm sidebar nav'lara Firma/Kurum Analizi linkleri eklendi

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

## 📊 Dashboard İyileştirmeleri — ✅ EKLENDİ (28 Haz 2026)

**Yapıldı (dashboard.html):**
- ✅ **En Aktif Kurumlar** widget: aktif ihalelerdeki idare sayımı (tüm kayıtlar taranır, JS'te sıralanır), ilk 7 kurum amber progress bar + tıklanabilir kurum-analiz linki ile
- ✅ **Son Eklenen İhaleler** widget: `olusturulma` DESC son 6 ihale, başlık + il + maliyet + tarih; ihale-detay linki
- İki widget yan yana 2 kolonluk grid düzeni, KPI grid altında, filtre üstünde
- ⚠️ "Son Eklenen" aslında "son güncellenen" — `olusturulma` her upsert'te tazeleniyor. Gerçek "ilk görülme" için `ilk_gorulme` kolonu gerekir (Supabase'de manual eklenecek)

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
- ✅ **Kategori backfill**: ~5500 kayıt OKAS/CPV'den 32 kategori türetildi; `in_()` batch ile
- ✅ **tur=Yapım fallback**: 246 kayıt `→ İnşaat & Yapım` (kategori boş olanlar)
- ✅ Supabase wrapper'a `in_()` batch metodu eklendi (timeout sorununu aştı)
- ⚠️ `ilk_gorulme` kolonu hâlâ yok — DDL gerektiriyor (Supabase SQL Editor'dan çalıştır)

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
