# İhalePro (app.ihalepro.com) Detaylı Rakip Analizi — 23 Tem 2026

> Kaynak: kullanıcının Chrome'undaki "busra aleyna" Temel-paket hesabıyla sayfa sayfa gezildi
> (dashboard, Analiz, İhaleler, Sonuçlar, Sözleşmeler, Kararlar, Firmalar, Kurumlar, Sektörler, Global).
> Temel pakette satır içerikleri maskeli (`*****`) ama sayfa yapısı/kolonlar/sekmeler tam görünüyor.

## 0. VERİ KAPSAMI KARŞILAŞTIRMASI (en kritik tablo)

| veri | İhalePro | Biz | fark |
|---|---|---|---|
| Sonuçlanan ihale | **1.688.002** | 539.203 | ⛔ 3,1x |
| Sözleşme kaydı | **2.945.049** | 539.203 | ⛔ 5,5x |
| Yüklenici firma | **441.510** | ~200K (yukleniciler) | ⛔ 2,2x |
| KİK kararı | **120.884** | 0 (sayfa var, veri yok) | ⛔ |
| İdare | 50.611 | ~87K DETSİS | ✅ bizde fazla |
| Aktif ihale | 5.129 | ~4.3K güncel | ≈ |
| Doğrudan temin | 6.013 (aktif) | 1,8M arşivli | ✅ DT arşivimiz ezici |
| Uluslararası | Premium'a kilitli | CANLI | ✅ |

**Sonuç:** aktif taraf başabaş; TARİHSEL sonuç/sözleşme tarafında 3-5 kat gerideyiz.
2024 sonuç backfill'i (bizde 6.029 kayıt!) bu yüzden ilk iş.

## 1. NAVİGASYON / TEMA (kullanıcı bunu istedi)
- Sol dar ikon çubuğu: Bana Özel · Analiz · İhaleler · Sonuçlar · Sözleşmeler · Kararlar · Firmalar · Kurumlar · Sektörler · Global
- Tıklayınca **ikinci bir flyout panel** açılıyor (ör. Sonuçlar → Tümü / Sonuç Bekleyenler / İptal Edilenler / Sonuçlananlar)
- Liste sayfası düzeni: sol filtre sütunu + sağda tablo; satır **accordion** ile genişleyip
  "Özet Bilgi" + eylem butonları (İhale İlanı · Dokümanı İndir · Mail Gönder · Takibe Al) gösteriyor
- Üstte global arama: kapsam dropdown'u (İhale/Firma/Kurum/Sonuç/Sözleşme) + tek kutu
- KULLANICI KARARI: temayı bu yapıya taşıyacağız — üst sekmeler yerine sol flyout alt menüler;
  Sonuçlar bölümüne "Biten Sözleşmeler / Devam Eden Sözleşmeler" eklenecek.

## 2. SAYFA SAYFA ENVANTER

### Dashboard ("Bana Özel")
- TR haritası (il yoğunluğu) + 6 KPI (aktif ihale, işveren idare, DT, sektör, sözleşme, yüklenici)
- **Takip Listem**: firma + kurum + sektör takibi tek panelde; "takip ettiğim firmaların TÜM sözleşmeleri"
- **"Yapay Zeka İle Size İş Fırsatı Bulduk"** bloğu (firma profili yoksa maskeli teaser)
- AI asistan onboarding: "hangi firmayı temsil ediyorsunuz?" → Firma Belirle
- **İhale Raporlarım / İhale Sonuç Raporlarım**: kriter bazlı kayıtlı rapor motoru (bizim bülten+kayıtlı arama birleşimi)
- Son incelediğim ihaleler · tarihi yaklaşan ihalelerim · favori aramalarım

### Analiz (İhalePro Veri Analizi)
- Firma segmentleri: **Parlayan Yıldızlar** (1.858) · **İlk Kez Kazananlar** (7.238) ·
  **150Mn+ Kazanan** (2.816) · **Sönen Yıldızlar** (15.479) · **İhale Yasaklıları** (17.055)
- Tarih aralıklı "Geçmiş Analizler": imzalanan sözleşme sayısı (gauge, mal/yapım/hizmet kırılımı),
  sonuçlanan ihalelerin toplam büyüklüğü, en büyük ihaleyi kazanan firma
- Canlı akışlar: en son ihale kazananlar · ilk defa kazananlar · "Bugün Parlayanlar"
- Parlayan Yıldızlar tablosu: iş artırma oranı % + son 1 yıl iş bitirme tutarı

### İhaleler (Aktif / Doğrudan Teminler)
- Filtreler: E-İhale toggle · **AI ile Önerilen İhaleler toggle** · kelime · yayın tarihi · ihale tarihi ·
  yaklaşık maliyet · tip · usul · idare · sektör · ihale ili · **işin yapılacağı il (ayrı!)** ·
  **Benzer İş (iş deneyim grubu)** · **Sözleşme Tipi** · **Düzeltme İlanı** · diğer + Aramayı Kaydet
- Satır: tarih + kalan gün · İKN/ad · tip/usul · il · **takvime ekle ikonu** · accordion özet
- Accordion: idare HİYERARŞİSİ (BELEDİYELER > VAN İLİ > Büyükşehir > Daire Bşk.) + 4 buton
- "Listede Ara" (sonuç içinde ikinci arama) + Excel indir (bizde kasıtlı yok)

### Sonuçlar
- Alt sekmeler: **Tümü / Sonuç Bekleyenler / İptal Edilenler / Sonuçlananlar** ← kullanıcının istediği ayrım
- Her birinde Açık İhaleler | Doğrudan Teminler toggle'ı
- 1.688.002 sonuç

### Sözleşmeler
- Alt sekmeler: **Tüm / Biten İşler / Devam Eden İşler** (başlangıç+bitiş tarihi kolonlarıyla!)
- Kolonlar: yüklenici · İKN/ad · **bedel (nominal TL + USD + bugünkü-değer TL)** · sözleşme tarihi ·
  **başlangıç tarihi · bitiş tarihi**
- 2.945.049 kayıt; firma arama + "takip ettiğim firmalar" filtresi
- NOT: bedelin 3 değeri = nominal, USD kuru (o günkü), enflasyon-düzeltmeli bugünkü değer — ℹ tooltip'li

### Kararlar
- **Tüm Kararlar / Uyuşmazlık / Mahkeme Kararları / Mahkeme Tutanakları / Yasaklı Sorgulama**
- 120.884 karar; filtreler: ihalede/karar no/kararda (tam metin)/kurumda/**şikayetçide** arama
- Kolonlar: karar no · karar tarihi · ihale adı · kurum

### Firmalar (Yüklenici Merkezi)
- 441.510 firma; kolonlar: ihale sayısı · sözleşme sayısı · toplam tutar (3 değerli)
- Filtre: firma ara · **Ürün/Hizmet/CETVELDE ara** (birim fiyat cetveli içinde arama!) · kurum · sektör · il · tip
- **Firma detay sekmeleri**: Firma Hakkında · Kazanılan İhaleler · **Katılabileceği İhaleler** (AI eşleştirme) ·
  **İlgilendiği İhaleler** · **Katılmadığı İhaleler** · **Rakip Analizi** · **Rakipler** ·
  İş Yapılan Kurumlar · İş Yapılan Sektörler · **Ortak Girişim** · **Notlar** (kullanıcı CRM notu)
- Özet: X ihale · Y sözleşme · **Z kurum ile iş bitirme** · toplam/ortalama sözleşme bedeli ·
  en çok iş yaptığı sektör · 81-il Türkiye haritası/tablosu

### Kurumlar (Kurum Merkezi)
- İki seviye: **36 üst kurum kategorisi** (bakanlık/kurum tipi) + 50.611 idare
- Kolonlar: aktif ihale · arşiv ihale · sözleşme sayısı · **toplam harcama** (nominal+USD+bugünkü değer)
- Bizim idare_tur'un birebir karşılığı ama HARCAMA tutarlarıyla zenginleştirilmiş

### Sektörler
- **48 sektör** (bizde 41 kanonik — yakın); kolonlar: aktif/geçmiş ihale · sözleşme · toplam harcama (4 değerli)
- "Sektörlerimdeki Parlayan Firmalar" kişiselleştirmesi

### Global
- Temel pakette tamamen kilitli (Premium) → bizim uluslararası modül AVANTAJ

## 3. ONLARDA OLUP BİZDE OLMAYAN — ÖNCELİKLİ LİSTE

### 🔴 Yüksek değer / bizim veriyle hemen yapılabilir
1. **2024 (+2025 boşlukları) sonuç backfill** — 1,69M'e karşı 539K'nın ana sebebi (bizde 2024=6K, 2023=127K)
2. **Sol flyout menü + Sonuçlar/Sözleşmeler bilgi mimarisi** (Tümü/Bekleyen/İptal/Sonuçlanan + Biten/Devam Eden) — KULLANICI ONAYLADI
3. **Sözleşme başlangıç/bitiş tarihleri** → "biten/devam eden" (EKAP sözleşme verisinde var demek ki; sonuç backfill'i bu alanları da toplamalı)
4. **Firma segmentleri** (Parlayan/Sönen/İlk kez kazanan/150Mn+) — bizim ihale_sonuclari'ndan SQL ile türetilebilir, kazıma gerekmez
5. **İptal edilen ihaleler** ayrımı (bizde durum=iptal var mı kontrol edilmeli; EKAP'tan geliyor)
6. **Bugünkü-değer (enflasyon düzeltmeli) tutar gösterimi** — TÜFE serisiyle çarpan tablosu, ucuz ve çok etkileyici
7. **Yasaklı firma listesi** (17.055) — kamu kaynağı (Resmî Gazete/EKAP yasaklılar); firma karnesine risk sinyali (fesih şeridimizin yanına)

### 🟠 Orta
8. **KİK kararları** (120.884; uyuşmazlık+mahkeme+tutanak) — YAPILACAKLAR'da zaten vardı (kik-kararlari.html iskeleti var), kaynak kazıması gerekiyor
9. **Takvime ekle** (ihale tarihi → ICS dosyası) — çok ucuz, listede satır başına ikon
10. **Kurum merkezi harcama tutarları** — idare listemize toplam sözleşme bedeli kolonları
11. **Firma detayında "İş Yapılan Kurumlar / Rakipler / Ortak Girişim" sekmeleri** — verimiz var (firma-analiz'de kısmen mevcut, sekmeleşmeli)
12. **Firma notları** (CRM benzeri kullanıcı notu) — basit tablo
13. **Mail Gönder** (ihaleyi e-postayla paylaş) — mailto: ile ucuz başlangıç

### 🟡 Düşük / sonra
14. Ürün/hizmet CETVELİNDE arama (birim fiyat kalemlerinde) — bizde kalemler jsonb yeni doldu; ileride
15. Kapsamlı rapor motoru (İhale Raporlarım) — bizim bülten sistemi benzer; birleştirilebilir
16. Katılmadığı/İlgilendiği ihaleler (doküman indirme sinyali EKAP'tan alınamıyor bizde — veri yok)
17. USD karşılığı gösterimi (sözleşme tarihindeki kurla) — TCMB kur tablosu gerekir

## 4. BİZDE OLUP ONLARDA OLMAYAN (koru + pazarla)
- Uluslararası ihaleler herkese açık (onlarda Premium kilidi)
- 1,8M DT arşivi + DT kazanan verisi (onlarda yalnız 6K aktif DT görünüyor)
- AI şartname analizi, teklif robotu, uyumluluk modülü
- Dünya ticaret analizi, harita, sektör dizini
- Belge linki (336K ihale) + malzeme listesi + fesih/tasfiye şeridi
