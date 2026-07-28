# v2 → v1 FARK RAPORU (28 Tem 2026)

> v2'de olup v1'de olmayan sayfa ve özellikler. 4 paralel ajan v2 kaynak kodunu okuyarak çıkardı.

## Grup: analiz-sayfalari

v2'nin 7 analiz sayfası incelendi. Sonuç: v1'de 3 sayfanın HİÇ karşılığı yok (rekabet-analizi, dt-analiz, ticaret-analiz), 4 sayfanın ise yalnız yüzeysel karşılığı var (v1-firmalar = düz liste, v1-kurumlar = düz liste, v1-analiz = tek firmalık panel, v1-benim-sayfam = TR haritası). En büyük kayıplar: (1) firma-analiz'in derin firma karnesi + ⚖️ firma karşılaştırma overlay'i + 🤖 AI rakip analizi + fesih/tasfiye risk şeridi, (2) kurum-analiz'in 🌳 DETSİS Kurum Ağacı + "İlk 3 Firma Payı" yoğunlaşma endeksi + 3 sekmeli kurum karnesi, (3) rekabet-analizi'nin filtreli pazar paneli (usul/bütçe/kategori dağılımları + paylaşılabilir URL), (4) dt-analiz'in tüm doğrudan temin pazar analizi, (5) ticaret-analiz'in dünya haritası + HS6 kalem sorgusu modülü. Ayrıca v1'de hiç bulunmayan çapraz özellikler: Pro plan kilidi (Plan.lockPage), misafir maskeleme dalları (uyeMi), "yalnız ihaleler / DT hariç" kapsam rozetleri, örneklem-payda dürüstlük etiketleri (SONUC_LIMIT=500), 🔗 Paylaş (URL parametreli derin link) ve tema-degisti olayında Chart.js yeniden çizimi.

### Firma Dizini & Analizi (dizin + derin firma karnesi + karşılaştırma)  ·  `firma-analiz.html`
- **v1 karşılığı:** KISMİ — v1-firmalar.html (düz firma listesi: ciro/sözleşme sıralama, arama, takip et) + v1-analiz.html (yalnız KENDİ seçtiğin tek firmanın paneli). v2'deki 'herhangi bir firmaya tıkla → aynı ekranda derin analiz' akışı, karşılaştırma, AI yorumu ve risk şeridi v1'de YOK.
- **Önem:** yuksek
- **Eksik özellik (27):**
  - Dizin KPI 4'lüsü: Toplam Firma / Toplam Sözleşme / Toplam Ciro / İş Ortaklığı sayısı (yuklenici_ozet RPC)
  - Dizin il filtresi (il_firma_dagilimi ile dolan 'Tüm İller' select)
  - 4 sıralama seçeneği: En Çok Ciro / En Çok Sözleşme / Son İş (En Yeni) / İsme Göre (A→Z) + kolon başlığından sıralama (dzSirala)
  - Sunucu taraflı sayfalama (range + count:'exact', 'Sayfa X / Y' + Önceki/Sonraki)
  - Dizin satırında 'İŞ ORT.' (ortak_girisim) rozeti ve 'Son İş' tarihi sütunu
  - 📋 Liste / 🗺️ Harita görünüm anahtarı — dizin içinde gömülü TR il-yoğunluk haritası (quantile eşikli choropleth, lejant, hover tooltip)
  - Harita görünümünde sektör seçici (41 kanonik kategori) + il tıklayınca 'o ilde o sektörde en çok kazanan firmalar' paneli (il_sektor_firmalar RPC)
  - Firma detay KPI 4'lüsü: Toplam Kayıt / Kazanılan İhale / Kapsanan İl / Kapsanan Sektör
  - ⚠ Sözleşme Riski şeridi — fesih_var + tasfiye_var TAM sayımı (head:true count), yalnız sıfırdan büyükse gösterilir
  - VKN gösterimi + '✓ resmî kayıt' rozeti (vergi_no, EKAP sözleşme devir kaydı kaynaklı; beyan VKN bilinçli gizli)
  - ⭐ Rakibi Takip Et butonu (takip_firmalar upsert/delete + '✓ Takip Ediliyor' durumu)
  - ⚖️ Firmayla Karşılaştır overlay'i: 2. firma arama + 5 satırlık yan yana KPI tablosu (toplam sözleşme, toplam ciro, kapsanan il, kapsanan sektör, ort. tenzilat) ve yeşil 'kazanan' vurgusu
  - Karşılaştırmada iki firmanın sektör dağılım çubukları (amber vs mavi) + '🤝 Ortak Zemin' kartı (ortak idareler ve ortak sektörler)
  - Genel Bakış sekmesi: Chart.js 'Yıllara Göre İhale Sayısı' bar grafiği
  - Genel Bakış: İhale Türü dağılımı çubukları + İl Bazlı Dağılım listesi + Sektör/Kategori dağılım çubukları
  - Katıldığı İhaleler sekmesi: 3 KPI (Katıldığı/Kazandığı ihale, Toplam Sözleşme bedeli, Ort. Tenzilat) + payda etiketleri
  - Sonuç kartı listesi: tenzilat rozeti veya 'N kısımlı' rozeti, idare linki (kurum-analiz'e), tür/il/bedel/tarih/teklif sayısı satırı
  - 5 butonlu sayfalama (« İlk · ‹ Önceki · Sonraki › · Son »)
  - analiz_pivot kırılımı: '🏛️ En Çok Çalıştığı İdareler' ve '🏭 Sektör Kırılımı' kartları (iş sayısı + ort. tenzilat)
  - 🤖 AI Rakip Analizi kartı — Pro'da 'Analizi Oluştur (1 kredi)' (API.firma.yorum_al), free'de bulanık önizleme + Pro CTA
  - Örneklem dürüstlüğü: SONUC_LIMIT=500 kesme uyarıları, 'son N kayıttan' payda etiketleri, resmî toplam vs örneklem ayrımı
  - Kapsam rozetleri ('yalnız ihaleler') + 'Doğrudan temin dahil değildir' kapsam notu
  - Tek kısımlı ihale kuralı: lot_sayisi>1 olan kayıtlarda tenzilat gösterilmez (tenzilatDegeri)
  - 🔗 Paylaş butonu (link kopyala)
  - Son Aramalar chip'leri (localStorage)
  - Misafir maskeleme: dizin adları '***', arama/detay için giriş kapısı (girisKapisi)
  - ?yid= / ?ara= / ?firma= derin link rotalaması + history.pushState

### İdare Dizini + Kurum Analizi + Kurum Ağacı  ·  `kurum-analiz.html`
- **v1 karşılığı:** KISMİ — v1-kurumlar.html yalnız 'Tüm Kurumlar / Takip Ettiklerim' listesi (toplam+aktif ihale, çubuk, takip et). Kurum karnesi (sekmeler, grafikler), DETSİS Kurum Ağacı ve kazanan firma yoğunlaşma analizi v1'de YOK.
- **Önem:** yuksek
- **Eksik özellik (24):**
  - İdare dizini KPI 4'lüsü: Toplam İdare / Aktif İdareler / Toplam İhale / Aktif İhale
  - Dizin filtre barı: idare-adı+il araması, 'Tüm İller' filtresi, 'Sadece Aktif' filtresi
  - 5 sıralama seçeneği (En Çok İhale / En Çok Aktif / İsme Göre A→Z / Z→A / İle Göre) + TOPLAM ve AKTİF kolon başlığından sıralama
  - Dizin sayfalaması (iz-pager: Önceki/Sonraki + 'N idare' sayacı, idare_dizin_json RPC)
  - 🌳 Kurum Ağacı görünümü — DETSİS hiyerarşisi, tembel açılan dallar (idare_agac_dallar RPC)
  - Ağaç düğüm rozetleri: '📋 kendi / dal toplamı' ihale ve '⚡ kendi / dal toplamı' doğrudan temin sayıları
  - Ağaç düğümünde 'tüm kayıtlar içindeki pay yüzdesi' etiketi
  - Dal bazlı '📋 Son ihaleler' butonu (idare_dal_son_ihaleler RPC — kendisi + tüm alt birimler)
  - Ağaçta arama (idare_agac_ara + idare_agac_bagsiz_liste, 350ms debounce) ve arama sonucundan ağaç yolunu açma (idare_agac_yol)
  - '🔗 Bağlantısız Kurumlar' ayrı dalı — DETSİS'e eşlenemeyen idareler gizlenmeden listelenir
  - 'Ağaç kapsaması' şeridi — ihale ve DT kayıtlarının ağaca bağlanma oranı, yüzde + ilerleme çubuğu
  - Kurum ağacı için 30 dakikalık sessionStorage önbelleği
  - Kurum başlığı aksiyonları: '📋 Tüm İhalelerini Gör', '⚡ Doğrudan Temin Kayıtları', '🔔 Kurumu Takip Et' (takip_idareler)
  - Kurum KPI 4'lüsü: Toplam İhale / Aktif-Açık / Toplam Bütçe (payda notuyla) / Kapsanan İl
  - 3 sekmeli kurum karnesi: Genel Bakış / Dağılım Analizi / İhale Listesi
  - Genel Bakış: Chart.js 'Aylık İhale Hareketi' (son 24 ay) grafiği
  - Genel Bakış: 'Yıllara Göre İhale Hareketi' grafiği + İhale Türü dağılım çubukları + İl Bazlı Dağılım
  - Dağılım Analizi: Sektör/Kategori dağılımı + İhale Usulü dağılımı çubukları
  - Dağılım Analizi: 'Aktif vs Kapanmış İhaleler' Chart.js grafiği
  - '🏆 Kazanan Firmalar' kartı (analiz_pivot p_grup='firma') — iş sayısı + ort. tenzilat çubukları
  - 'İlk 3 Firma Payı' yoğunlaşma endeksi — %60+ kırmızı 'yüksek yoğunlaşma', %35+ amber, altı yeşil 'dağınık' yorumuyla
  - İhale Listesi sekmesi + 5 butonlu sayfalama (« İlk ... Son »)
  - 'Kapsam: yalnız ihaleler' notu + kapsam rozeti ve bütçe paydası açıklaması
  - 🔗 Paylaş butonu (kurum derin linki kopyalama)

### Rekabet Analizi (pazar dağılımı paneli)  ·  `rekabet-analizi.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok. (v1-bank.html'in 'Sektörler/Kurumlar' sekmeleri yalnız ham sayım listeleri veriyor; filtreli pazar analizi paneli değil.)
- **Önem:** yuksek
- **Eksik özellik (16):**
  - 3'lü filtre barı: durum (Aktif İhaleler / Tüm İhaleler), 81 il seçici, 41 kanonik kategori seçici (js/kategoriler.js + 'Diğer' kovası)
  - '↺ Sıfırla' butonu ve '🔗 Paylaş' — filtreleri ?durum/?il/?kategori olarak URL'e yazıp panoya kopyalama, açılışta bu parametreleri geri okuma
  - 4 KPI: Toplam İhale / Ort. Yaklaşık Maliyet / En Yoğun Sektör / En Aktif İl
  - Ort. maliyet KPI'sında görünür payda: 'N / M ihale üzerinden · X kayıtta maliyet yok'
  - Chart.js 'Aylık İhale Hareketi' çizgi grafiği (son 24 ay, etkin_tarih ekseni)
  - İhale Türü Dağılımı yatay bar grafiği (top 10)
  - İl Bazlı Dağılım yatay bar grafiği (top 10)
  - Kategori Dağılımı yatay bar grafiği (OKAS/CPV, top 15)
  - İhale Usulü Dağılımı çubukları + ham EKAP i18n key temizleyici (usulTemizle → 'İstisna (4734 3-g)')
  - Bütçe Aralığı Dağılımı çubukları (7 bant: <500 Bin … >200 Mn + 'Belirtilmemiş')
  - 'En Çok İhale Açan İdareler' top 10 tablosu (kurum-analiz'e linkli)
  - 'Türe Göre Ortalama Maliyet' top 10 tablosu + payda uyarısı (ortalamanın paydası ihale sayısı değildir)
  - Pro plan kilidi (Plan.lockPage — free kullanıcıya kilit ekranı)
  - Tek RPC ile sunucu taraflı toplama (rekabet_ozet — 8 breakdown tek çağrıda)
  - 'Kapsam: yalnız ihaleler' notu + parasal kartlarda 'yalnız ihaleler' kapsam rozetleri
  - tema-degisti olayında tüm grafiklerin yeniden çizilmesi

### Doğrudan Temin Analizi  ·  `dt-analiz.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok. v1-ihaleler.html'de yalnız 'Doğrudan Teminler' liste sekmesi var; DT pazarına dair hiçbir analiz/grafik yok.
- **Önem:** yuksek
- **Eksik özellik (13):**
  - 4 KPI: Toplam DT / Sonuçlanan (+ '%X kazanan bedeli açıklanmış') / Ort. Kazanan Bedel / Medyan Kazanan Bedel
  - Chart.js 'Aylık Doğrudan Temin Hareketi' çizgi grafiği (son 24 ay)
  - Tür Dağılımı yatay bar grafiği (Mal / Hizmet / Yapım / Danışmanlık)
  - İl Bazlı Dağılım yatay bar grafiği (en fazla DT yapılan 15 il)
  - Kategori Dağılımı yatay bar grafiği (OKAS/CPV türetimi, top 15)
  - Kurum Türü Dağılımı çubukları + idare_tur slug→Türkçe etiket eşlemesi (belediye, saglik, bakanlik_tasra, milli_egitim, universite, kit, dce, tbmm …)
  - Kazanan Bedel Aralığı Dağılımı çubukları (5 bant: <₺50 bin, ₺50-200 bin, ₺200 bin-₺1 mn, ₺1-5 mn, >₺5 mn)
  - 'En Çok Doğrudan Temin Yapan İdareler' top 12 tablosu (kurum-analiz'e linkli)
  - Tek çağrılık dt_analiz_ozet RPC (toplam, sonuclanan, ort/medyan bedel, tur, il, kategori, idare, idare_tur, trend, bedel_bant)
  - Pro plan kilidi (Plan.lockPage)
  - 'Kapsam: yalnız doğrudan temin' açıklama notu (DT medyanı ≈ ₺37 bin; ihale evreniyle toplanmaz) + Rekabet Analizi'ne çapraz link
  - Üst barda '⚡ DT Listesi' kısayolu
  - tema-degisti olayında grafiklerin yeniden çizilmesi

### Türkiye Dış Ticaret Analizi (dünya haritası + HS6 sorgusu)  ·  `ticaret-analiz.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok. v1-global.html yalnız TED uluslararası ihale listesi; makro ticaret verisi/dünya haritası içermiyor.
- **Önem:** orta
- **Eksik özellik (15):**
  - 4 KPI: Dünyaya İhracat / Dünyadan İthalat / Dış Ticaret Dengesi (negatifte kırmızı, pozitifte yeşil) / Kapsanan Ülke
  - İnteraktif dünya SVG haritası — ihracat büyüklüğüne göre 5 kovalı choropleth, Türkiye ayrı 'anavatan' vurgusu
  - Harita zoom/pan (svg-zoom.js, maxZoom 12)
  - Yıl ve Kıyas Yılı dropdown'ları (ticaret_yillar RPC) + tüm rakamlarda ▲▼ %değişim gösterimi
  - 16 sektör grubu filtresi (Hayvansal, Bitkisel, Gıda, Mineraller, Yakıtlar, Kimyasallar, Plastik & Kauçuk, Deri, Ahşap & Kağıt, Tekstil, Ayakkabı, Taş-Cam-Seramik, Metaller, Makine & Elektrik, Ulaşım Araçları, Diğer İmalat) — harita, lejant ve liste birlikte süzülür
  - Ülke tooltip'i: TR→ülke ihracat, ülke→TR ithalat, sektör satırı, Türkiye için 'referans ülke' balonu
  - Dinamik lejant (sektör modunda eşikler $2M/$20M/$100M/$500M, toplamda $10M/$100M/$1Mr/$5Mr)
  - Ülke Listesi tablosu — 5 sıralanabilir sütun (Ülke / İhracat / Değişim / İthalat / Değişim), ülke arama kutusu
  - Liste satırı ↔ harita karşılıklı vurgulama (hover'da ülkeyi haritada işaretleme, haritada tıklayınca satıra kaydırma)
  - '🔎 HS Kodu / Sektör Sorgusu' kartı — 'Sektöre göre' ve 'HS koduna göre' iki mod
  - Hiyerarşik HS otomatik tamamlama (📚 Fasıl 2-hane / 📂 Pozisyon 4-hane / 📦 Kalem 6-hane; kod veya Türkçe açıklama ile arama, lazy js/hs-kodlar.js)
  - HS kodu → ülke ülke sonuç tablosu (ticaret_hs_ulkeler RPC) + 'Türkiye toplam ihracat/ithalat · N ülke' özeti + sıralanabilir başlıklar
  - HS6 kalem-kalem drill-down kartı (ticaret_hs_kalem RPC): fasıl süzgeci, kalem/pozisyon/fasıl araması, sıralanabilir sütunlar, 'fasıl › pozisyon' breadcrumb satırı
  - Veri kırpılma uyarısı (1000 satır tavanına dayanınca sarı uyarı şeridi)
  - '📚 Veri Kaynakları ve Yöntem' kartı — UN Comtrade / Dünya Bankası WITS atıfları, TÜİK linki, ticari platform ToS gerekçesi

### Firma Segmentleri  ·  `firma-segmentleri.html`
- **v1 karşılığı:** KISMİ — v1-firmalar.html'de yalnız 'Parlayan Yıldızlar' sekmesi var. Diğer 3 segment (İlk Kez Kazananlar, 150Mn+ Kazananlar, Sönen Yıldızlar), segment sayaçları ve büyüme sütunu v1'de YOK.
- **Önem:** orta
- **Eksik özellik (8):**
  - 4 tıklanabilir segment kartı ve canlı sayaçları (firma_segment_sayilari RPC): 🌟 Parlayan Yıldızlar, 🆕 İlk Kez Kazananlar, 💰 150Mn+ Kazananlar, 📉 Sönen Yıldızlar
  - Segmente göre değişen tablo başlıkları: 'Son 12 ay kazancı' / 'İlk kazanım' / 'Toplam kazanç' / 'Önceki 12 ay kazancı'
  - Büyüme % sütunu — pozitifte yeşil (+X%), negatifte kırmızı
  - Segment listesi sunucu taraflı sayfalama (firma_segment_listesi, 50'şer + 'X / Y · N firma' sayacı)
  - '⚠️ Önizleme' uyarı şeridi — ihale_sonuclari sayımını hedefle karşılaştırıp arşiv tamamlanma yüzdesini gösterir
  - Üye giriş kapısı (misafire '🔒 Firma segmentleri üyelere özeldir' ekranı)
  - Satırdan firma-analiz'e derin link (?firma=)
  - firma-analiz sayfasından '⭐ Firma Segmentleri →' çapraz geçiş butonu

### Türkiye Haritası (firma yoğunluğu + açık RFQ katmanı)  ·  `harita.html`
- **v1 karşılığı:** KISMİ — v1-benim-sayfam.html ve v1-analiz.html içinde TR haritası var (KPI hero / il bazlı iş dağılımı), ama bağımsız bir keşif haritası sayfası, sektör katmanı ve RFQ katmanı v1'de YOK.
- **Önem:** orta
- **Eksik özellik (14):**
  - 4 istatistik kartı: Toplam Firma / En Yoğun İl / Açık RFQ / Kapsanan İl (81 ilden)
  - İki katman anahtarı: '🏢 Firma Yoğunluğu' ve '🤝 Açık RFQ' (yeşil pin + halo, il centroid'inde)
  - Sektör seçici (41 kanonik kategori) — harita o sektörün yoğunluğuna göre yeniden boyanır (il_sektor_ozet RPC, sessionStorage'da 6 saat önbellek)
  - Quantile ile veriden hesaplanan 6 kovalı choropleth + dinamik lejant (tema duyarlı 'veri yok' rengi)
  - SVG zoom/pan (svg-zoom.js, maxZoom 6)
  - Hover tooltip: il adı, firma sayısı + ciro, sektör satırı (firma/sözleşme/bedel), açık RFQ sayısı
  - İl tıklama paneli KPI 4'lüsü: Firma / Toplam Ciro / Açık RFQ / Türkiye Payı (sektör modunda Firma / Sözleşme / Toplam Bedel / Sektör Payı)
  - Panelde 'Bu ilde öne çıkan firmalar' top 8 listesi (il_sektor_firmalar RPC veya yukleniciler sorgusu, firma-analiz'e linkli)
  - Panelde 'Bu ildeki açık RFQ'lar' listesi — satinalma_talepleri (🤝 RFQ rozeti) + Kalkınma Ajansı ilanları (🏛️ KA rozeti, dış link)
  - Sektör seçiliyken il sıralama paneli (top 15, çubuklu, 'firma · sözleşme' sayılarıyla) ve '← sıralamaya dön' geri bağlantısı
  - RFQ modunda süresi geçmiş talep filtresi (son_teklif_tarihi NULL veya gelecek — il_rfq_dagilimi ile birebir aynı kural)
  - Derin bağlantı desteği: ?katman=rfq ve ?sektor=<kategori>
  - İ/ı locale tuzağına karşı eq-listesi il eşleştirmesi + 'AFYON → afyonkarahisar' alias haritası
  - Misafir maskeleme: firma sıralaması üyelere özel, yoğunluk boyama ve istatistikler misafirde de çalışır

## Grup: liste-detay

7 v2 dosyası tek tek okundu (ihaleler 126KB ve dogrudan-temin 81KB grep+bölüm okumasıyla), v1 karşılıkları (v1-ihaleler, v1-ihale-detay, v1-kararlar, v1-sektorler, v1-global) de baştan sona okunarak karşılaştırıldı. Bulgular: (1) dt-detay.html'in v1'de HİÇ karşılığı yok — v1-ihaleler.html DT satırları `dogrudan-temin?id=` ile v2 amber sayfasına atıyor (satır 261), yani DT detay akışı v1'de kopuk. (2) dogrudan-temin.html'in tam karşılığı yok; v1'de sadece v1-ihaleler içinde 3. sekme olarak kısmî bir liste var (DT'ye özel KPI/sekme/detaylı panel/kurum hiyerarşisi yok). (3) En büyük iş değeri kaybı ihale-detay'da: "Bu İhaleye Uygun Firmalar" (ihaleye_uygun_firmalar RPC), "Tahmini Kazanma Bandı" (analiz_pivot RPC), TÜFE bugünkü değer, çok-kısımlı sonuç kartı, fesih/tasfiye uyarısı, Belgeler ve Notlarım sekmeleri v1'de yok. (4) ihaleler.html'de uyum skoru + semantik_skor_batch harmanı, okundu sistemi, kayıtlı aramalar paneli, kurum hiyerarşisi (DETSİS) filtresi, sonuc_ozet KPI barı, kaynak/idare türü/OKAS/sınır değer filtreleri v1'de yok. (5) uluslararasi.html'deki dünya haritası + Türkiye ticaret katmanı v1-global'de tamamen yok. AYRICA DİKKAT: v1-kararlar.html sekmeleri `karar_turu` kolonunu 'UK'/'MK'/'MT' ile filtreliyor (satır 35-37), v2 kik-kararlar.html ise aynı kolon için 'uyusmazlik'/'inceleme'/'duzenleyici' kullanıyor — ikisinden biri sıfır sonuç döndürüyor olmalı, taşımadan önce DB'deki gerçek değerler doğrulanmalı.

### İhaleler (ana liste)  ·  `ihaleler.html`
- **v1 karşılığı:** v1-ihaleler.html (liste şablonu var ama filtre/zeka katmanı çok daha dar)
- **Önem:** yuksek
- **Eksik özellik (24):**
  - 'Geçmiş' sekmesi (v1'de Aktif/Sonuçlar/DT var, Geçmiş yok)
  - Sekme başlıklarında canlı kayıt sayacı (tab-cnt-guncel / gecmis / sonuc)
  - Sonuç sekmesine özel KPI barı: Toplam Sözleşme Bedeli + Ortalama Tenzilat + Farklı Kazanan Firma (sonuc_ozet RPC)
  - Hızlı tarih çipleri: Tümü / Bugün / Bu Hafta / Son 7 Gün / Son 30 Gün
  - Kaynak filtresi (EKAP / ilan.gov.tr Gazete / DMO / Jandarma)
  - İdare Türü filtresi (14 seçenek: belediye, büyükşehir, su_kanal, KİT, yargı…)
  - Kurum Hiyerarşisi filtresi — DETSİS alt ağacı canlı arama (idare_agac_ara + idare_alt_kurum_sayisi + ilanlar_hiyerarsi RPC) ve kaldırılabilir kurum çipi
  - OKAS / CPV kodu filtresi
  - Sınır Değer Katsayısı (esik_katsayi) bant filtresi ve kartta 'N: 0,82' etiketi
  - Kısmi Teklif / Fiyat Türü / İstekli (yerli-yabancı) filtreleri
  - Min. Uyum filtresi (%40+/%55+/%70+/%85+)
  - Profil uyum skoru: kartta compat-bar yüzdesi + 'Uyum % ↓' sıralaması
  - semantik_skor_batch RPC ile AI cosine benzerliği harmanı (%60 kural + %40 semantik)
  - Okundu sistemi: kart okundu işaretleme, 'Okunanları Gizle' toggle, Okundu rozeti, KullaniciVeri ile cihazlar arası senkron
  - Kayıtlı Aramalar paneli: modal ile isim verip kaydetme, ▶ Çalıştır / ✕ Sil, kayıtlı sayısı rozeti
  - '📊 Bu Aramayı Analiz Et' — mevcut filtrelerle rekabet-analizi sayfasını açma
  - Satır başına 'Takvim' butonu — .ics indirme (VALARM ile 1 gün önce hatırlatma)
  - Kayıt No kopyala (⧉ kopyala mikro-etkileşimi)
  - Kaynak rozeti (EKAP / 📰 Gazete / 📦 DMO / 🪖 Jandarma)
  - Kart içinde sonuç bloğu: '✓ Sonuçlandı — Kazanan / bedel / Tenzilat %'
  - Topbar kapsam araması + Ctrl+K kısayolu ve klavye ile sekme değiştirme
  - Toast bildirim sistemi
  - Geçmiş sekmesi kapsam uyarısı şeridi (yaklaşık maliyet/OKAS verisi eksik uyarısı)
  - Tahmini sayım '~' rozeti (planned count modu)

### Doğrudan Temin (liste)  ·  `dogrudan-temin.html`
- **v1 karşılığı:** KISMÎ — v1'de ayrı sayfa yok, sadece v1-ihaleler.html içindeki 'Doğrudan Teminler' sekmesi
- **Önem:** yuksek
- **Eksik özellik (20):**
  - 4 KPI stat kartı: Toplam Duyuru / Mal Alımı / Hizmet Alımı / Yapım Alımı
  - Durum bazlı 3 sekme: Güncel / Sonuç / Tümü + her sekmede aktif filtre kapsamlı canlı sayaç
  - 'Doğrudan Temin nedir?' bilgi banner'ı (4734 md.22 açıklaması)
  - İdare Türü filtresi (14 seçenek)
  - '🔍 Detaylı Ara' aç/kapa paneli
  - Hızlı tarih butonları: Bugün / Bu Hafta / Son 7 Gün / Son 30 Gün / ✕ Tarihi Temizle
  - Kurum Hiyerarşisi filtresi (DETSİS alt ağacı canlı arama, dogrudan_temin_hiyerarsi RPC)
  - Ham DURUM dropdown'ı (optgroup'lu: Duyurusu Yayımlanmış / Teklifler Değerlendiriliyor / Sonuç Duyurusu Yayımlanmış / Sonuçlandırıldı / Sonuç Bilgileri Gönderildi)
  - 'Yalnız dokümanı olanlar' onay kutusu
  - Aktif filtre çipleri (tek tek ✕ ile kaldırılabilir)
  - 'Neden bazı filtreler yok?' açıklama bölümü (yaklaşık maliyet/usul/OKAS/kaynak/yayın tarihi gerekçeleri)
  - Sıralama butonları: 📅 En Yeni / 🏛️ İdare
  - Kartta takibe al ★ butonu (TakipDT)
  - Kartta 📅 takvime ekle butonu — .ics indirme
  - '📄 Doküman var' rozeti + durum rozeti (🟢 Açık / ✅ Sonuçlandı)
  - İdare adına tıklayınca o idarenin tüm DT'leri (derin link)
  - Pager: « İlk / ‹ Önceki / Sonraki › / Son » + sayım bilinmeyen modda '+' gösterimi
  - Derin link parametreleri: ?idare= ?kategori= ?il= ?dt_no= ?kurum= ?tarihBas/?tarihBit + tarih aralığı bilgi rozeti
  - dt_il_sayim RPC ile TAM il dropdown'ı (v1 örneklemden kuruyor)
  - Misafir maskeleme rozeti ve idare/kurum filtrelerinin misafirde disable edilmesi

### İhale Detayı  ·  `ihale-detay.html`
- **v1 karşılığı:** v1-ihale-detay.html (temel bilgi kartı + sonuç + benzer ihaleler var, analiz katmanı yok)
- **Önem:** yuksek
- **Eksik özellik (23):**
  - 5 sekmeli yapı: İhale Bilgileri / İlan Bilgileri / Belgeler (n) / 🤖 AI Analizi / 📝 Notlarım
  - 'Belgeler' sekmesi: belge listesi tür ikonlu (📕 pdf, 📗 excel, 📘 word, 🗜️ zip), storage_url ile '⬇ İndir', EKAP VatandasIlanGoruntuleme derin linki (ekap_ihale_id hash'inden üretiliyor)
  - '📝 Notlarım' sekmesi: localStorage'a otomatik kaydeden not alanı, karakter sayacı, 💾 Kaydet / Temizle, not varsa sekme başlığında nokta işareti
  - AI Analizi render'ı: yapay_zeka_ozeti'ni ### başlıklarına göre renkli bölüm kartlarına ayırma (ÖZET / KİLİT BİLGİLER / GİRİŞ ENGELLERİ / MALİ YÜKÜMLÜLÜKLER / RİSKLER VE UYARILAR / FIRSATLAR / TAVSİYE) + analiz tarihi ve pdf türü
  - 4'lü KPI grid (Yaklaşık Maliyet + itiraz bedeli alt satırı, Son Teklif, İlan Tarihi, Profil Uyumu)
  - Animasyonlu Profil Uyum Skoru barı + uyum etiketleri (✓ tür, ✓ il, ✓ bütçe aralığı)
  - 🎯 'Bu İhaleye Uygun Firmalar' bloğu — ihaleye_uygun_firmalar RPC (konu çapası + ±%500 ölçek bandı + il), firma başına kazanım sayısı/max/ort bedel, 'Aynı il' ve 'Ölçek ✓' rozetleri
  - 📊 'Tahmini Kazanma Bandı' — analiz_pivot RPC ile ağırlıklı ort. tenzilattan teklif bandı hesabı + emsal sayısı + aynı idare/sektörde son 5 sözleşme listesi
  - Çok kısımlı ihale desteği: 'N kısım', Toplam Sözleşme Bedeli, ihale geneli tenzilat ve kısım bazlı tenzilat gösterilmeme kuralı açıklaması
  - TÜFE ile 'bugünkü değer' hesabı (js/tufe.js — sözleşme bedelinin enflasyon düzeltmeli karşılığı)
  - Fesih / tasfiye uyarı kutusu (kaç kısımda fesih/tasfiye var)
  - Katılımcı sayısı + geçerli teklif sayısı gösterimi
  - İlan metni için ilan_html güvenli sanitize render (script/style/iframe temizliği, on* ve javascript: URL kaldırma, inline style temizliği)
  - OKAS/CPV kodlarını tıklanabilir linke çevirme + kaynak ihalenin durumuna göre hedef sekme seçimi (listeSekmesi)
  - Malzeme / Kalem Listesi kartı (kalemler jsonb)
  - Dış kaynak desteği: ilan.gov.tr / DMO / Jandarma etiketi ve 'kaynağında aç' butonu (pdf_url)
  - '↗ EKAP'ta Ara' butonu (usul'e göre ekap/search vs ekap-dt/search ayrımı)
  - 🔗 Paylaş / link kopyala butonu
  - usulLabel — ham EKAP enum'unu (OPEN, BARGAIN…) okunabilir Türkçeye çevirme
  - Topbar'da ikinci 'Takibe Al' butonu (çift buton senkronu)
  - İdare adının kurum-analiz sayfasına linklenmesi
  - Kazanan firmanın firma-analiz sayfasına linklenmesi
  - benzer_ihaleler RPC (v1 düz kategori+tür sorgusu kullanıyor)

### Doğrudan Temin Detayı  ·  `dt-detay.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok (v1-ihaleler.html DT satırları v2'nin dogrudan-temin sayfasına atıyor)
- **Önem:** yuksek
- **Eksik özellik (11):**
  - Tek duyuru detay sayfası (dt_no ile) — başlık, durum/tür/kategori/il/doküman rozetleri
  - Duyuru Bilgileri ızgarası: İdare, İl, Tür, Kategori, Durum, Duyuru No
  - Akıllı tarih bloğu: sonuçlanmışta 'Sonuç Duyurusu Tarihi', açıkta 'Son Teklif Tarihi' + 'N gün kaldı' / 'BUGÜN' acil vurgusu
  - Sonuç Bilgileri kartı — ÇOK SATIRLI sözleşme desteği (bir dt_no'da birden fazla kalem): kazanan firma, sözleşme bedeli, sözleşme tarihi, teklif aralığı (en düşük–en yüksek), üstte 'N kalem, toplam ₺X'
  - Takibe al ★ butonu (TakipDT)
  - 🔗 Bağlantıyı kopyala butonu
  - EKAP Kaydı kartı + 'EKAP doğrudan temin arama →' linki ve kalıcı derin link olmadığı açıklaması
  - İlgili Aramalar kartı: bu idarenin diğer duyuruları / aynı kategori / o ilin duyuruları
  - Misafir maskeleme (idare ve kazanan_firma kolonları anon'a kapalı, 🔒 *** rozeti)
  - noindex,follow meta etiketi (1,49M DT kaydı için crawl patlaması koruması)
  - 'Duyuru bulunamadı' boş durum ekranı

### KİK Kararlar  ·  `kik-kararlar.html`
- **v1 karşılığı:** v1-kararlar.html (4 sekme + TR-katlamalı arama + sayfalama var)
- **Önem:** orta
- **Eksik özellik (12):**
  - Çok alanlı arama formu: Anahtar Kelime, Karar No (örn. 2024/UH.I-1234), Karar Türü, Sonuç
  - Tarih aralığı filtresi (Başlangıç / Bitiş karar tarihi)
  - '🔍 Ara' ve '✕ Temizle' butonları + Enter ile arama
  - İstatistik barı: Toplam Karar / İptal / Kabul / Red sayaçları
  - Sonuç filtre çipleri (Tümü / 🔴 İptal / 🟢 Kabul / ⚪ Red) — client tarafı anlık filtre
  - Kart görünümü (v1 tablo kullanıyor): karar no + tür rozeti + sonuç rozeti + 2 satır clamp'li özet + 'Karara git →'
  - '🔗 KİK Resmi Site' linki (topbar + boş durum ekranlarında)
  - Bilgi banner'ı (KİK uyuşmazlık kararları açıklaması)
  - arama_fold yoksa legacy ILIKE + trAramaKalibi yedek arama yolu
  - 'Türkçe karakter katlaması devre dışı' uyarı şeridi (foldYok)
  - Sunucu tarafı kırpma uyarısı: 'Bu aramaya uyan N karar var; en yeni M tanesi listeleniyor'
  - Tablo henüz oluşturulmamışsa (42P01) 'Veri Yükleniyor' özel boş durumu

### Sektörler Dizini  ·  `sektorler.html`
- **v1 karşılığı:** v1-sektorler.html (tablo + Tüm/Takip sekmeleri + arama + çubuk + takip et var)
- **Önem:** orta
- **Eksik özellik (11):**
  - 4 KPI stat kartı: Toplam Sektör / Aktif Sektörler / Toplam İhale / Aktif İhale
  - Kart grid görünümü (v1 tablo kullanıyor) — 41 kanonik kategoriye birebir eşlenmiş emoji ikon haritası
  - Sıralama dropdown'ı: En Çok İhale / En Çok Aktif / Alfabetik (A→Z) / Aktiflik Oranı
  - Minimum hacim filtresi: Tüm sektörler / Sadece Aktif / Min 10 / Min 50 / Min 100 ihale
  - Aktiflik oranı yüzdesi ('%42 aktiflik oranı') ve 'Kapandı' sayacı (toplam − aktif)
  - 🥇🥈🥉 madalya rozetleri (ilk 3 sektör)
  - 'Diğer' jenerik kovasını sıralamada daima listenin SONUNA atma kuralı (madalyaları çalmasın diye)
  - Kart aksiyon butonları: 'Aktif İhaleler' / '📊 Analiz' (rekabet-analizi?kategori=) / 'Geçmiş' (ihaleler?sekme=gecmis)
  - 🔗 Paylaş butonu (link kopyala + '✓ Kopyalandı' geri bildirimi)
  - Topbar hızlı linkleri: 'İdareler →' ve 'Tüm İhaleler →'
  - kategori_sayim RPC başarısız olursa sayfalı (1000'lik) fallback veri çekimi + ilerleme çubuğu

### Uluslararası İhaleler  ·  `uluslararasi.html`
- **v1 karşılığı:** v1-global.html (sol filtre paneli + tablo + sayfalama var, harita/KPI yok)
- **Önem:** orta
- **Eksik özellik (19):**
  - 4 KPI stat kartı: Toplam İhale / Ülke Sayısı / Yapım İşi / Hizmet Alımı
  - İnteraktif DÜNYA HARİTASI (SVG): ihale olan ülkeye tıklayınca liste filtreleme, hover tooltip, renk lejantı (ulke_ihale_dagilimi RPC)
  - Harita üzerinde yakınlaştırma/kaydırma (svgZoomKur, maxZoom 12 — küçük ülkeler için)
  - Haritada 'Ticaret modu': Türkiye'nin o ülkeyle ihracat/ithalat hacmi + yıllık % değişim (js/ticaret-tr-veri.js — UN Comtrade/WITS)
  - Ticaret modunda sektör seçim dropdown'ı (16 sektör kırılımı)
  - '📈 Türkiye ile ticaret analizi →' geçiş linki
  - Bilgi banner'ı (TED Europa, Türkçe'ye çevrilerek gösterim açıklaması)
  - İhale Türü filtresi (Mal / Hizmet / Yapım)
  - Sıralama dropdown'ı: 📅 İlan tarihi / ⏰ Son teklif / 💶 Tahmini bedel
  - İlan tarihi aralığı filtresi + '✕ temizle' butonu
  - uluslararasi_filtre_secenekleri RPC ile TAM ülke/kategori listesi (v1 .limit(2000) örneklemi kullanıyor → eksik dropdown riski)
  - Kart görünümü (v1 tablo kullanıyor): ülke/kategori/tür rozetleri, idare, son teklif tarihi
  - publication_no 'İlan No / Duyuru No' gösterimi + tek tıkla kopyalama (kaynak portalda aratmak için)
  - Kaynağa göre buton metni ve etiket ayrımı (TED'de İncele / Gürcistan Portalında İncele)
  - Çevrilmemiş orijinal başlığın ayrıca gösterilmesi
  - Placeholder bedel eşiği (GECERLI_BEDEL_ESIK=100 — TED'in 1 EUR / 0.01 nominal değerlerini 'bedel yok' sayma)
  - Pager: « İlk / ‹ Önceki / Sonraki › / Son »
  - trAramaKalibi ile Türkçe karakter toleranslı arama (v1 düz ilike → İ/ı'da sessiz veri kaybı riski)
  - publication_no ikincil sıralama anahtarı (sayfalar arası satır tekrarı/atlaması önleme)

## Grup: kullanici-sayfalari

7 v2 dosyası tek tek okundu ve v1 karşılıkları (v1-benim-sayfam, v1-profil, v1-raporlar, v1-ajanda, v1-bank, v1-kabuk.js) ile satır satır karşılaştırıldı. Sonuç: 3 sayfanın v1'de HİÇ karşılığı yok (dashboard.html, takipte.html, bildirimler.html, ayrıca ihalelerim.html), 2 sayfanın karşılığı var ama işlevsel olarak çok daha zayıf (profil, raporlar), 1 sayfa ise neredeyse birebir portlanmış ama iki dinamik bloğu sadeleştirilmiş (benim-sayfam). En kritik boşluk profil: v1-profil `kullanici_profiller` (firma künyesi) tablosuna yazarken v2 profil.html `profil` tablosuna (sektör/il/tür/bütçe/uyum eşiği) yazıyor — yani v1'de uyum-eşleşme motorunun tüm girdileri hiç ayarlanamıyor, dolayısıyla "En İyi Eşleşmeler"/uyum skoru v1 tarafında beslenemiyor. İkinci kritik boşluk takipte.html: v1'de takip yönetimi (çıkarma, DT/kurum/firma takipleri, toplu temizleme) yapılabilen tek bir ekran yok. Üçüncüsü bildirimler.html: 7 sekmeli bildirim merkezi, bülten (kayıtlı arama e-posta aboneliği) yönetimi ve push izni v1'de yok. Not: v1 kabuğunda arama kapsam seçici ve Ctrl+K kısayolu ZATEN VAR (js/v1-kabuk.js), bunlar eksik listesine alınmadı.

### Anasayfa (Dashboard) — pazar geneli özet + ihale listesi  ·  `dashboard.html`
- **v1 karşılığı:** YOK — v1'de dashboard sayfası hiç yok; v1-kabuk.js sol rayında 'Anasayfa' menü girişi bile bulunmuyor. Widget'ların sadece küçük bir kısmının benzeri dağınık halde v1-benim-sayfam (TR harita + 6 KPI) ve v1-bank (kategori_sayim / idare_sayim / il_sayim_aktif tabloları) içinde var.
- **Önem:** yuksek
- **Eksik özellik (17):**
  - Global mod seçici: Tümü / İhaleler / Doğrudan Temin — sayfadaki TÜM widget'ları (KPI, harita, trend, kategori, kurumlar, liste) tek noktadan yeniden çizer (window.aktifDashMod)
  - Günlük canlı sayaç şeridi: 'Bugün Eklendi', 'Bugün Son Teklif', 'Sonuçlanan İhale + DT' (mod'a göre etiketi değişen kazanım kartı)
  - 4 tıklanabilir KPI kartı: Takipteki İhale, Aktif Türkiye İhalesi, 7 Gün İçinde Bitecek, Büyük İhale (₺43 Mn+) — her biri filtreli derin linke gidiyor
  - Leaflet tabanlı interaktif TR ısı haritası (js/harita.js + data/turkey-provinces.geojson): 6 kovalı renk skalası, legend, hover'da İhale/DT ayrı sayı, tıklayınca 'İhaleler mi Doğrudan Temin mi' popup seçimi (v1'de yalnız statik SVG choropleth var)
  - Son 7 gün günlük yayın trendi çubuk grafiği (bugün amber vurgulu, ihale+DT toplamı)
  - Kategori Dağılımı widget'ı (kategori_sayim + dt_kategori_sayim sonuçlarını birleştiren dashBirlestir)
  - En Aktif Kurumlar widget'ı (idare_sayim + dt_idare_sayim birleşimi)
  - Son Eklenen İhaleler widget'ı (mod-farkındalıklı başlık/link)
  - Yaklaşan Son Tarihler widget'ı
  - Kayıtlı Aramalar widget'ı — localStorage + KullaniciVeri.syncFromDB senkronu, kayıtlı tüm filtreleri URL'e taşıyan '▶' linki
  - 'En İyi Eşleşmeler' bloğu — profil bazlı uyum skoru hesabı, localStorage min_uyum_esigi eşiğiyle filtreleme, DT modunda DT eşleşmeleri
  - Son Görüntülenenler widget'ı (DT modunda dürüst 'karşılığı yok' mesajı)
  - Alt filtre çubuğu: Durum / İl / Bütçe (1-5-20-43 Mn) / Sıralama + sonuç sayacı
  - Alt ihale tablosu: Uyum skoru sütunu, satır içi 'Takibe Al' butonu, DT modunda dtSatirOlustur ile ayrı kolon seti
  - Ücretsiz planda 10 ihale sınırı + 'Pro'ya Geç' premium nudge bloğu
  - Topbar zil dropdown'ı: okunmamış nokta (notif-dot) + son bildirim listesi + 'Tümünü Gör'
  - Misafir maskeleme dalı (uyeMi) — anon'a kapalı idare/ekap_id kolonlarını select'ten çıkarıp '🔒 ***' rozeti gösterme

### Takip Listesi (ihale + DT + kurum + firma takipleri)  ·  `takipte.html`
- **v1 karşılığı:** YOK — v1'de takip yönetim sayfası hiç yok. v1-benim-sayfam yalnızca 3 sayaç kartı (firma/kurum/sektör) ve en fazla 12 satırlık salt-okunur bir liste gösterip 'takipte' (v2) sayfasına link veriyor; v1-ajanda ise sadece takvim + yaklaşan tarihler kısmını kapsıyor.
- **Önem:** yuksek
- **Eksik özellik (14):**
  - 4 özet istatistik kartı: Takip Edilen, 7 Gün İçinde Bitiyor, Açık İhale, Toplam Tahmini Değer
  - Takip listesi içi arama kutusu (istemci tarafı satır filtreleme, data-baslik üzerinden)
  - Sıralama seçici: Son Eklenen Önce / En Yakın Tarih Önce / En Yüksek Uyum Önce
  - Satır bazlı Uyum skoru çubuğu + yüzde (js/uyum.js + profil tablosu)
  - Satır bazlı '✕ Çıkar' ile takipten çıkarma (animasyonlu satır kaldırma + istatistik güncelleme)
  - '↩ Bittileri Kaldır' — teklif tarihi geçmiş ihaleleri toplu temizleme
  - 'Listeyi Temizle' — tüm takibi onaylı silme
  - Liste / Takvim görünüm değiştirici (js/ajanda.js takvimini sayfa içinde açar, takip-veri-hazir event'i ile besler)
  - '⚡ Takip Ettiğim Doğrudan Teminler' bölümü — TakipDT.syncFromDB ile dt_takipler senkronu, dt-detay linki, 'Takibi Bırak'
  - '🏛️ Takip Ettiğim Kurumlar' bölümü (takip_idareler tablosu, kurum-analiz derin linki, 'Takibi Bırak')
  - '🏆 Takip Ettiğim Firmalar (Rakip Takibi)' bölümü (takip_firmalar tablosu, firma-analiz derin linki, 'Takibi Bırak')
  - Kalan gün renk kodu (≤3 gün kırmızı / ≤7 gün amber / üstü yeşil) ve '● Son N Gün' durum rozeti
  - Misafir/üye dalı: anon'a kapalı idare/ekap_id kolonlarını select'ten çıkarma + misafire üyelik çağrısı metni
  - Boş durum ekranı (☆ ikon + 'İhalelere Git' CTA)

### Bildirimler (bildirim merkezi + bültenler + okuduklarım + sözleşme listesi)  ·  `bildirimler.html`
- **v1 karşılığı:** YOK — v1'de bildirim sayfası hiç yok. v1-kabuk.js topbar'ındaki zil ikonu doğrudan v2 'bildirimler' sayfasına atıyor (v1 kabuğu bozuluyor); v1-benim-sayfam'daki 'Takip Edilenlerde Son Güncellemeler' kartı yalnızca son 6 bildirimi salt-okunur listeliyor.
- **Önem:** yuksek
- **Eksik özellik (14):**
  - 7 sekmeli bildirim merkezi: Tümü / Okunmamış / İhale / Sistem / ⭐ Bültenlerim / 📖 Okuduklarım / 📋 Sözleşme Listesi — her sekmede rozet sayacı
  - 'Tümünü okundu işaretle' + satıra tıklayınca tek tek okundu işaretleme (bildirimler.okundu UPDATE)
  - Bültenlerim: '+ Yeni Bülten' formu (ad, anahtar kelime, il, ihale türü, min bedel, günlük/haftalık frekans) → bultenler tablosuna insert
  - Bülten kartı: e-posta aktif/kapalı durumu, frekans, son gönderim tarihi, '▶ Çalıştır' (filtreyi ihaleler sayfasında açar), '✕ Sil'
  - İl değerini toLocaleUpperCase('tr') ile kaydetme (izmir→İZMİR eşleşme tuzağı çözümü)
  - Oturum yoksa localStorage 'ihale_kayitli_aramalar_v1' bültenlerine düşme (misafir uyumluluğu)
  - 📖 Okuduklarım sekmesi: cihazda görüntülenen son 50 ihale, ● AKTİF / ◯ Sona Erdi rozeti, '↺ Geçmişi Sil' (DB'den de siler)
  - 📋 Sözleşme Listesi sekmesi: takip listesinden kalan gün renkli (≤3 kırmızı, ≤7 turuncu) + bedel özetli liste
  - Bildirim Tercihleri kartı: Yeni İhale Bildirimi, Son Teklif Hatırlatıcı (kaç gün önce input'u), E-posta Bildirimi, Rekabet Uyarısı (PRO kilitli) → profil tablosuna upsert
  - Tarayıcı push bildirim izin banner'ı (Notification.requestPermission, 'İzin Ver', kapatmayı localStorage'da hatırlama)
  - Alt+1..7 klavye kısayollarıyla sekme değiştirme
  - DB'de bildirim yoksa takip listesinden yerel bildirim üretme (son 7 gün içinde biten ihaleler için 'N gün kaldı' / 'Bugün son gün!')
  - kurum_takip ve rakip_hareketi bildirim türlerine özel ikon + 'Kuruma Git' / 'Firmaya Git' aksiyon linki (aksiyon_url öncelikli)
  - Takip + KullaniciVeri senkronu (başka cihazda eklenen kayıtlı arama/okundu verisinin gelmesi)

### Profil & Filtreler (eşleşme/uyum motoru ayarları)  ·  `profil.html`
- **v1 karşılığı:** v1-profil.html VAR ama TAMAMEN FARKLI bir işi yapıyor: v1 `kullanici_profiller` tablosuna firma künyesi yazıyor (MERSİS, web sitesi, çalışan sayısı, ciro, hizmet alanları, referanslar, kaçınılanlar) + hesap özeti gösteriyor; v2 ise `profil` tablosuna eşleşme filtrelerini yazıyor. Yani v1'de uyum skorunun/En İyi Eşleşmeler'in TÜM girdileri (sektörler, tercih_iller, tercih_turler, min/max bedel, min_uyum_esigi) hiçbir yerden ayarlanamıyor.
- **Önem:** yuksek
- **Eksik özellik (17):**
  - Faaliyet sektörleri seçim ızgarası — js/kategoriler.js'ten 41 kanonik kategori, emoji + açıklama kartları, çoklu seçim; eski kısa kodları kanonik ada çeviren KATEGORI_ESKI_MAP göçü
  - Tercih edilen iller chip ızgarası ('Tüm Türkiye' seçeneği dahil) → profil.tercih_iller
  - İhale türü chip'leri: Hizmet / Mal / Yapım / Danışmanlık → profil.tercih_turler
  - Yaklaşık maliyet aralığı Min–Max alanları → profil.min_bedel / max_bedel
  - Profil Doluluk Skoru banner'ı: 0-100 puan, renk değiştiren ilerleme çubuğu (≥80 yeşil, ≥50 amber, altı kırmızı) ve 5 madde rozeti (Sektörler 30p, İller 20p, İhale Türü 20p, Bütçe 15p, Eşik 15p)
  - Akıllı Eşleşme Eşiği: 0-90 arası 5'er adımlı slider + büyük yüzde göstergesi + 5 hazır ayar butonu (Tümü / %40 Orta / %60 İyi / %75 Yüksek / %85 Mükemmel), localStorage 'ihale_min_uyum_esigi' senkronu
  - Anahtar Kelimeler alanı — ihale başlığında geçerse uyum skoruna +10 puan (profil.anahtar_kelimeler + localStorage)
  - Belgeler & Yetkilendirmeler alanı — AI şartname analizinde 'eleme kriteri uygunluğu' kontrolü için (localStorage 'ihale_sertifikalar')
  - E-posta bildirim tercihleri bölümü: bildirim_email aç/kapa, açıkken görünen alt seçenekler (bildirim_son_teklif, bildirim_gun_oncesi 1-14) — sektör seçilmese bile ayrı upsert ile kaydediliyor
  - 'Uyum Skoru Hesaplama Mantığı' önizleme kartı: Sektör %40 · İl %25 · İhale Türü %20 · Bütçe %15 dağılım çubukları
  - İş yeri adresi bloğu: İl (dropdown) / İlçe / Açık Adres → profil.firma_il, firma_ilce, acik_adres (MaaS-harita eşleştirmesi ve e-Satınalma için)
  - VKN alanı — e-Satınalma'da ihale açarken otomatik gelen, orada değiştirilemeyen kaynak (profil.vergi_no)
  - İletişim kişisi + iletişim telefonu (yazarken anlık localStorage'a kaydeden alanlar)
  - Ctrl+S ile kaydet klavye kısayolu
  - Toast bildirim bileşeni (başarı/hata)
  - Chip'lerde klavye erişilebilirliği: Enter/Space ile tetikleme + aria-pressed senkronu
  - 'profil' tablosuna onConflict:'user_id' ile upsert (satır yoksa oluşturma) — v1 farklı tabloya yazdığı için v2 tarafındaki uyum verisi hiç güncellenmiyor

### Benim Sayfam (Bana Özel)  ·  `benim-sayfam.html`
- **v1 karşılığı:** v1-benim-sayfam.html — düzen ihalepro akışıyla birebir portlanmış (selamlama, TR harita + 6 KPI hero, Takip Listem, Sizin İçin, AI promo, Raporlarım, Takip Ettiğim İhaleler, Son Bildirimler, Tarihi Yaklaşan, Son İncelediğim + Favori Aramalarım). Ancak v2'nin iki dinamik bloğu (js/takip-panel.js ve js/firmam.js) v1'de basit satır-içi kodla sadeleştirilmiş.
- **Önem:** orta
- **Eksik özellik (10):**
  - Takip Listem'de '⊕ Yeni Ekle' modalı: Firma / Kurum / Sektör sekmeleri, 280ms debounce'lu autocomplete (yukleniciler.arama_fold ile TR-katlamalı arama, ilanlar.idare için benzersizleştirme), '✓ ekli / +' toggle ile anında takip ekle-çıkar
  - 'Takip ettiğim firmaların son sözleşmeleri' listesi — takip_firma_sozlesmeleri RPC ile firma, iş başlığı, il, sözleşme bedeli, sonuç tarihi ve fesih/tasfiye risk rozeti
  - takip_ozet RPC ile tek çağrıda sayaç (v1 üç ayrı count sorgusu atıyor ve kullanıcı filtresi uygulamıyor)
  - Firmam eşleşme kartlarında eşleşme skoru rozeti (%) — v1 sadece düz satır listesi gösteriyor
  - Eşleşme kartında 'eşleşme_nedeni' açıklama metni (neden bu ihale önerildi)
  - Eşleşme kartında '📅 Takvime Ekle' — istemci tarafı ICS dosyası üretip indirme
  - Eşleşme kartlarında kategori çipi, il ve yaklaşık maliyet gösterimi (12 kart, ızgara düzeni)
  - Sayfa içi firma onboarding'i: yukleniciler autocomplete ile firma seçme + firmami_belirle RPC (v1 kullanıcıyı v1-analiz sayfasına yönlendiriyor)
  - Seçili firma karne meta satırı: firma rozeti + il · kazanım sayısı · toplam ciro + 'Firmayı değiştir' butonu
  - localStorage 'firmam' önbelleğiyle hızlı ilk boya, sonra sunucudan teyit

### Raporlarım (İhale / Sonuç raporu + Excel)  ·  `raporlar.html`
- **v1 karşılığı:** v1-raporlar.html VAR — iki sekme (İhale / Sonuç), aynı rapor_ihale / rapor_sonuc RPC'leri, kriter formu, Raporu Kaydet ve Kayıtlı Raporlarım iskeleti mevcut (hatta v1'de v2'de olmayan 'Yükle' butonu da var). Eksikler işlevsel derinlikte.
- **Önem:** orta
- **Eksik özellik (8):**
  - Durum filtresi (Tümü / Aktif / Sonuçlanan) — yalnız İhale Raporu sekmesinde görünen, sekme değişince gizlenen alan
  - Gerçek XLSX çıktısı (SheetJS/xlsx 0.18.5 ile .xlsx dosyası + A1'de filigran/kaynak/oluşturma zamanı satırı) — v1 yalnızca CSV üretiyor
  - Excel için 5.000 satıra kadar sayfa sayfa toplu çekim döngüsü — v1 sadece ekranda duran 200 satırı dışa aktarıyor
  - Sonuç tablosunda sayfalama: 50'şerlik sayfalar, '← Önceki / Sonraki →', 'sayfa / toplam sayfa' sayacı — v1 tek seferde 200 satır çekip orada duruyor
  - Plan tabanlı kademeli erişim: ücretsizde ilk 2 sayfa, tam liste Pro, Excel Kurumsal (js/plan.js Plan.isPro / Plan.isKurumsal)
  - Plan durumuna göre buton kilidi ve açıklama metni ('⬇ Excel İndir 🔒 Premium' + 'İlk 2 sayfa ücretsiz · tam rapor Pro · Excel Kurumsal')
  - 81 ilin tamamı il dropdown'ında — v1'de yalnızca 27 il sabitlenmiş (kalan 54 il hiç seçilemiyor)
  - Toplam kayıt göstergesinde tavan aşıldığında '50.000+' ve 'ilk 2 sayfa (Pro değilsiniz)' uyarısı

### İhalelerim & Tekliflerim (e-Satınalma / RFQ modülü)  ·  `ihalelerim.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok; v1 sol rayında e-Satınalma / özel ihale modülünün hiçbir girişi bulunmuyor (satinalma_talepleri / tedarikci_teklifleri tarafı v1'e hiç taşınmamış).
- **Önem:** orta
- **Eksik özellik (6):**
  - 'Açtığım İhaleler' sekmesi — satinalma_talepleri'nden başlık, kategori, il, tahmini bedel, son teklif tarihi ve gömülü tedarikci_teklifleri(count) ile 'N teklif' sayacı
  - 'Verdiğim Teklifler' sekmesi — tedarikci_teklifleri'nden teklif bedeli, ilgili ihale başlığı/kategorisi ve teklif tarihi
  - Açtığım ihalelerde durum rozetleri: '● Açık', '⏹ Süresi doldu' (son_teklif_tarihi geçmişse; NULL tarih süresiz sayılır), '● Kapandı'
  - Verdiğim tekliflerde sonuç rozetleri: '🏆 Kazandınız' (kazanan_teklif_id eşleşmesi), 'Kapandı', 'Değerlendirmede'
  - Topbar'da '+ Yeni İhale Aç' aksiyonu ve kartlardan ozel-ihale-detay derin linkleri
  - Girişsiz kullanıcı için 'giriş yapın' çağrı bloğu ve boş durumlarda 'İlk ihaleni aç' / 'Açık ihalelere göz at' yönlendirmeleri

## Grup: ozel-ve-arac

Altı v2 dosyasi tek tek okundu ve v1 sayfa listesiyle karsilastirildi. Sonuc: alti sayfanin BESI icin v1'de hicbir karsilik yok (ozel-ihaleler, ozel-ihale-detay, teklif-olustur, dokumanlar, fiyatlandirma_odeme_bolumu); uyumluluk.html icin yalnizca kismi/zayif bir karsilik var (v1-benim-sayfam + v1-analiz'deki "Sizin Icin" eslesmesi, firmam_acik_ihaleler RPC — profil tabanli yuzde skoru, esik filtresi ve profil ozet karti yok). js/v1-kabuk.js'deki 11 menuluk sol rayda e-Satinalma, Uyumluluk, Dokumanlar, Teklif Olustur ve Abonelik girisi hic yok. Iki sayfa v1'den DOGRUDAN linkleniyor ama v2 (amber) temada aciliyor: teklif-olustur (v1-ihale-detay.html:104-105 "Teklif Olustur" ve "AI Fiyat Stratejisi" butonlari + v1-ihaleler.html:306 genislet satirindaki link) ve fiyatlandirma_odeme_bolumu (js/v1-kabuk.js:82 "Paket Yukselt" + tum v1 sayfalarindaki "uye olun" linkleri) — yani kullanici akis ortasinda mavi temadan amber temaya dusuyor. Ayrica onemli bir veri modeli farki var: uyumluluk.html ve js/uyum.js `profil` tablosundan sektorler/tercih_iller/tercih_turler/min_bedel/max_bedel okuyor, oysa v1-profil.html `kullanici_profiller` tablosuna yaziyor ve bu tercih alanlarinin HICBIRINI icermiyor — uyum skoru v1'e tasinirsa profil formunun da genisletilmesi sart. En buyuk is degeri sirasiyla: teklif-olustur (6 adimli sihirbaz + 2 ayri AI motoru + kredi dusumu), ozel-ihaleler/ozel-ihale-detay (RFQ pazar yeri, Kurumsal plan kapisi, tedarikci eslestirme v3 RPC) ve uyumluluk (Pro ozelligi).

### Teklif Oluştur — 6 adımlı teklif hazırlama sihirbazı (AI destekli)  ·  `teklif-olustur.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok. AMA v1-ihale-detay.html:104-105 ("📝 Teklif Oluştur" + "💡 AI Fiyat Stratejisi" butonları) ve v1-ihaleler.html:306 (genişlet satırındaki "Teklif oluştur →") doğrudan bu v2 dosyasına link veriyor; kullanıcı mavi temadan amber temaya düşüyor.
- **Önem:** yuksek
- **Eksik özellik (29):**
  - 6 adımlı sihirbaz: İhale Özeti / Firma Bilgileri / Teknik Teklif / Mali Teklif / Ekler / Önizleme & İndir
  - Sol yapışkan adım paneli (adım noktaları + tıklayarak adıma atlama, adimGit/adimIleri/adimGeri)
  - Kalan Kredi kutusu — kullanici_krediler.kalan_kredi okuma, 'AI teklif yazımı: 1 kredi' notu
  - AI Teknik Teklif Oluştur butonu — backend /teklif-olustur çağrısı (kapsam/neden/yöntem alanlarını doldurur), 402 'Yetersiz kredi' yönetimi
  - AI çalışırken dönen yükleme mesajları (Şartname analiz ediliyor / Teknik gereksinimler çıkarılıyor / …)
  - Backend'e ulaşılamazsa devreye giren şablon metin yedeği (alan bazlı — kısmi AI içeriğini ezmez)
  - AI Fiyat Stratejisi paneli — /ai/teklif-strateji (DeepSeek) ile geçmiş gerçek tenzilata dayalı teklif bandı önerisi (1 kredi)
  - AI stratejisinin dayanak verilerinin gösterimi: kırılım (Sektör / İl / Genel) · ihale sayısı · ort. tenzilat + 'tahmindir' uyarısı
  - Teknik teklif 4 sekmesi: Genel Bilgiler, Çalışma Yöntemi, İş Takvimi, Ekip & Makine
  - İş Programı & Teslim Takvimi tablosu (faaliyet / başlangıç / bitiş, satır ekle-sil, otomatik numaralandırma)
  - Anahtar Personel tablosu (ad soyad / görev / deneyim yılı, satır ekle-sil)
  - İş Makineleri & Ekipman tablosu (ekipman / adet / marka-model / Mülkiyet-Kiralık-Temin edilecek)
  - Birim Fiyat Teklif Cetveli — miktar, birim (Adet/m²/m³/m/ton/kg/LS), KDV hariç birim fiyat, satır bazlı KDV oranı (%1/8/10/18/20), satır toplamı
  - Canlı toplam hesabı: Ara Toplam (KDV hariç) + KDV Toplamı + Genel Toplam (KDV dahil), toplamHesapla()
  - Para birimi seçimi (TRY/USD/EUR) ve teklif geçerlilik süresi (30/60/90/120 gün)
  - Ödeme Planı & Koşulları serbest metin alanı
  - Firma Bilgileri adımı: vergi no, vergi dairesi, ticaret sicil no, yetkili ad/unvan, telefon, e-posta, adres
  - Deneyim & Kapasite alanları: sektör deneyimi (yıl), çalışan sayısı, daha önce tamamlanan benzer projeler
  - Ekler adımı: 5 sık istenen belge (vergi levhası, ticaret sicil gazetesi, iş deneyim belgesi, geçici teminat mektubu, bilanço) + 3 opsiyonel belge (ISO, referans fotoğrafları, personel CV) checkbox listesi
  - Ek dosya yükleme alanı (PDF/Word/Excel/JPEG, maks 10MB, çoklu seçim, yüklenen dosyayı listeden çıkarma)
  - Resmî teklif belgesi önizlemesi: firma anteti, tarih/ref no, Konu bloğu, 4 numaralı bölüm, mali cetvel (ara toplam/KDV/toplam), çift imza bloğu
  - PDF İndir — ayrı pencerede yazdırılabilir belge üretip window.print() ile PDF kaydettirme (print CSS gömülü)
  - Word İndir butonu (backend entegrasyonu bekleyen placeholder)
  - Kaydet — teklifler tablosuna upsert (ilan_id + teklif_veren_id çakışmasında mevcut taslağı güncelleme), teklif_metni'ne JSON paketleme, teklif_tutari sayısal alan
  - Son teklif tarihine ≤7 gün kaldıysa çıkan turuncu uyarı bandı
  - Adım doğrulaması (firma unvanı / yetkili adı zorunlu) ve toast bildirim sistemi (başarı/hata/bilgi)
  - Topbar'da 'Otomatik kaydediliyor' / '✓ Kaydedildi' durum göstergesi
  - Şablon Seç butonu (şablon kütüphanesi placeholder)
  - Misafir/üye ayrımlı dar select (idare kolonu anon'a kapalı olduğu için sorgudan çıkarılıyor)

### e-Satınalma / Özel İhaleler (RFQ) — firma ihalesi açma + tedarikçi eşleştirme + platform ihale listesi  ·  `ozel-ihaleler.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok; js/v1-kabuk.js'deki 11 menülük sol rayda e-Satınalma girişi de yok.
- **Önem:** yuksek
- **Eksik özellik (17):**
  - '➕ Yeni Satınalma İhalesi Aç' akordeon formu (başlık, kategori, miktar, tahmini bedel, son teklif tarihi, açıklama)
  - Firma Kimliği & Adresi bloğu — profilden otomatik dolan KİLİTLİ (readonly) alanlar: ünvan, VKN, il, ilçe, açık adres
  - Kurumsal plan kapısı — Plan.isKurumsal() ile formu kilitleme + 'Yayınla — Kurumsal Plan' buton rozeti + upsell diyaloğu
  - Profil tamlık kapısı — eksik alanları (Firma ünvanı / VKN 10 hane / İl / Açık adres) listeleyip formu kapatma
  - GİB algoritmasıyla VKN checksum doğrulama fonksiyonu (vknGecerli)
  - '🎯 Uygun Tedarikçileri Bul' — ihaleye_uygun_firmalar v3 RPC (p_baslik konu çapası + p_bant ±%500 ölçek bandı), hata durumunda ihaleye_uygun_firmalar_geo yedeğine düşme
  - Tedarikçi öneri listesi: sıra numarası, firma-analiz derin linki, firma ili, ~mesafe_km, kategori kazanım sayısı, en büyük kazanım, 'Aynı il' ve 'Ölçek ✓' rozetleri
  - Ölçek bandı bilgi metni ('~₺X–₺Y için önerilen firmalar')
  - Platform Satınalma İhaleleri listesi — satinalma_talepleri (RFQ) + kamu_ihaleleri kaynak='ka' (Kalkınma Ajansı) kayıtlarının client-side tek listede birleştirilmesi
  - Kaynak rozeti: '🤝 Platform RFQ' / '🏛️ Kalkınma Ajansı · KOD' + 26 ajans kodunun tam adı (AJANS_AD tooltip)
  - Güncel / Geçmiş / Tümü durum sekmeleri (son_teklif_tarihi bazlı)
  - RFQ filtre çubuğu: metin araması (350ms debounce, baslik/olusturan_firma/aciklama), kaynak, il (81 il), sektör (41 kanonik kategori), son teklif tarih aralığı (başlangıç+bitiş), sıralama (🆕 En yeni / ⏰ Son teklife göre), sonuç sayacı
  - Harita köprüsü — 'Açık RFQ'ları haritada gör' (harita?katman=rfq) linki + il_rfq_dagilimi RPC'den hesaplanan yeşil rozet sayısı
  - Süresi dolmuş kartların soluk gösterimi + Açık / Kapandı / Süresi doldu / Yayında durum etiketleri
  - KA ilanlarının orijinal_url ile ka.gov.tr'ye yeni sekmede açılması (↗ ka.gov.tr etiketi)
  - Misafirde tedarikçi önerisi yerine 'üyelere özeldir — giriş yapın' mesajı (42501 yerine anlaşılır uyarı)
  - RLS ihlali mesajının kullanıcı diline çevrilmesi ('Geçerli bir Kurumsal aboneliğiniz olduğundan emin olun')

### Özel İhale (RFQ) Detayı — teklif verme / gelen teklifleri değerlendirme  ·  `ozel-ihale-detay.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok. v1-ihale-detay.html yalnızca kamu ihalesi detayıdır; RFQ akışına ait hiçbir bölüm içermiyor.
- **Önem:** yuksek
- **Eksik özellik (12):**
  - RFQ başlık kartı: '🤝 Özel Satınalma İhalesi' etiketi, kategori / 📍il-ilçe / durum rozetleri
  - Tahmini Bedel · Miktar · Son Teklif üçlü KPI ızgarası
  - Alıcı beyan bloğu: firma ünvanı + VKN + 'ⓘ doğrulanmamış' uyarısı ve açık adres satırı
  - Süre-doldu mantığı: durum='acik' olsa bile son_teklif_tarihi geçmişse teklif kabul etmeme (sureDoldu/teklifAcik)
  - Tedarikçi görünümü: 'Teklif Ver' formu (firma adı, teklif bedeli ₺, açıklama/notlar) + 'kapalı-zarf, yalnızca alıcı görür' notu
  - Aynı ihaleye ikinci teklifi engelleme (duplicate yakalama) ve '✓ Teklifiniz Alındı' kartı
  - Alıcı görünümü: '📥 Gelen Teklifler (n)' listesi — bedele göre artan sıralı, açıklama satırı
  - 'Kazanan Seç' butonu — satinalma_talepleri.kazanan_teklif_id + durum='kapali' güncellemesi, onay diyaloğu
  - KAZANAN rozeti ve kazanan teklif satırının yeşil vurgusu
  - Alıcıya özel '🎯 Önerilen Tedarikçiler' kartı — ihaleye_uygun_firmalar_geo RPC (mesafe_km, kategori kazanımı, en büyük kazanım, 'Aynı il' / 'Kapasite ✓' rozetleri, firma-analiz derin linki)
  - Anon-güvenli sorgu: giriş yoksa VKN / açık adres / koordinat / olusturan_user_id kolonlarını select dışında bırakan sabit kolon listesi
  - Girişsiz kullanıcıya 'Teklif vermek için giriş yapın' bloğu

### Uyumluluk Analizi — profile göre ihale uyum skoru (Pro özelliği)  ·  `uyumluluk.html`
- **v1 karşılığı:** KISMEN — v1-benim-sayfam.html ve v1-analiz.html'deki "Sizin İçin Katılabileceğiniz İhaleleri Bulduk" bölümü (firmam_acik_ihaleler RPC, kamu karnesi tabanlı) benzer amaca hizmet ediyor; ancak profil tabanlı yüzde skoru, eşik filtresi, sıralama ve profil özet kartı v1'de yok.
- **Önem:** yuksek
- **Eksik özellik (12):**
  - Uyum skoru yüzdesi + renkli ilerleme çubuğu (yüksek ≥70 yeşil / orta ≥45 amber / düşük kırmızı) — js/uyum.js Uyum.hesapla
  - Min. Uyum eşiği filtresi (Tümü / %40+ / %60+ (varsayılan) / %75+ / %85+)
  - Sıralama seçenekleri: Uyum % ↓ / Son Teklif ↑ / Maliyet ↓
  - Profil özet kartı — seçili Sektörler, İller ve İhale Türleri chip'leri (+N taşma rozeti) ve 'Profili Güncelle →' linki
  - Profil eksikse çıkan kesikli çerçeveli uyarı bandı ('sektör veya il tercihi seçilmemiş, genel tahmin kullanılır')
  - Başlık / idare metin araması (Supabase'e gitmeden anlık client-side filtre)
  - Satır içi ★/☆ takibe al-çıkar butonu (Takip.toggle, buton durumu anında güncellenir)
  - Durum rozeti: '● Son N Gün' (≤3 gün) / '● Açık'
  - Yaklaşık maliyet aralığı gösterimi (min–max, ₺K/₺M/₺Mr kısaltmalı)
  - Pro plan kapısı — Plan.getPlan() ile kontrol, Pro değilse Plan.lockPage ile sayfayı kilitleme
  - 25 kayıtlık sayfalama + '<n> eşleşme' sayacı + sayfa aralığı bilgisi
  - profil tablosundan sektorler / tercih_iller / tercih_turler / min_bedel / max_bedel okuma — DİKKAT: v1-profil.html bu tercih alanlarının hiçbirini içermiyor ve kullanici_profiller tablosuna yazıyor; skor v1'e taşınırsa profil formu da genişletilmeli

### Dökümanlar — takip edilen ihalelerin EKAP belgeleri  ·  `dokumanlar.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok; ayrıca v1-ihale-detay.html'de de belge/döküman bölümü bulunmuyor (grep ile doğrulandı), yani ilanlar.belgeler verisi v1'de hiçbir yüzeyde gösterilmiyor.
- **Önem:** orta
- **Eksik özellik (10):**
  - Takip listesindeki ihalelerin ilanlar.belgeler kayıtlarını akordeon kartlarda listeleme (kart başlığında idare, il ve döküman sayısı)
  - Döküman ızgarası — dosya adı + tür + yeni sekmede açılan indirme linki
  - Döküman türüne göre ikon eşlemesi (pdf 📕 / excel 📗 / word 📘 / zip 🗜️ / teknik 🔧 / idari 📎 / şartname 📋)
  - 'Tümünü Aç' / 'Tümünü Kapat' toggle butonu ve ≤3 kart varsa otomatik açma davranışı
  - Döküman veya ihale adı arama kutusu + Ctrl+K odaklama kısayolu
  - 'EKAP'ta Görüntüle ↗' derin linki — doğrudan temin usulü için ekapv2 ekap-dt/search, diğerleri için ekap/search ayrımı
  - 3 sekme: Takip Dökümanları / Teknik Şartnameler / İdari Şartnameler (son ikisi 'yakında' boş durumu) + Alt+1..3 sekme kısayolu
  - Misafir maskeleme dalı — ekap_id ve idare kolonlarını select dışında bırakan dar sorgu + '🔒 ***' üyelik teşvik rozeti
  - Boş durum ekranları: 'Takip listesi boş → İhalelere Göz At' ve 'Veri bulunamadı'
  - EKAP bilgi kutusu ('dökümanlar 24 saat içinde güncellenir')

### Abonelik & Ödeme — plan kartları, iyzico ödeme modalı, kupon  ·  `fiyatlandirma_odeme_bolumu.html`
- **v1 karşılığı:** YOK — v1'de bu sayfa hiç yok; ancak js/v1-kabuk.js:82'deki topbar 'Paket Yükselt' butonu ile v1-analiz/v1-benim-sayfam/v1-firmalar/v1-kurumlar/v1-kararlar/v1-sozlesmeler/v1-raporlar/v1-profil sayfalarındaki 'üye olun' ve 'Paket Yükselt' linkleri doğrudan bu v2 dosyasına gidiyor (tema kırılıyor).
- **Önem:** orta
- **Eksik özellik (12):**
  - 3 planlı fiyat kartı ızgarası: Ücretsiz ₺0 / Pro ₺1.490 (⭐ En Popüler) / Kurumsal ₺3.990 — her kartta ✓/✗ özellik listesi
  - Mevcut plan durumuna göre buton değişimi ('✓ Aktif Plan' / '✓ Mevcut Plan' / 'Ücretsize Geç')
  - 'Pro Plan Aktif' üst banner'ı
  - iyzico ödeme modalı — ad, soyad, kart numarası (4'lü otomatik gruplama), ay, yıl, CVV, taksit (Tek Çekim / 2 / 3)
  - VISA + Mastercard + iyzico kart logoları (CSS ile çizilmiş)
  - Mesafeli Satış Sözleşmesi zorunlu onay kutusu (mesafeli-satis sayfasına link)
  - odeme-baslat edge function çağrısı (plan_kodu + kart bilgileri, Authorization header) + başarı/hata sonuç kutusu + Plan.clearCache()
  - Plan düşürme akışı — planDusur() → backend /plan-iptal endpoint'i (service_role, onay diyaloğu ile)
  - Kupon kodu kullanma kutusu — /kupon-kullan endpoint'i, başarı/hata mesajı, sonrasında otomatik sayfa yenileme
  - Güven rozetleri barı (256-bit SSL / iyzico güvenceli / 14 gün iade / istediğin an iptal)
  - Sık Sorulan Sorular bölümü (4 soru: ödeme güvenliği, iptal, taksit, çok kullanıcılı Kurumsal)
  - Modal dışına tıklayarak kapatma + kart numarası uzunluk doğrulaması
