# YAPILACAKLAR — V1 Versiyon

> Tek iş kuyruğu (v1). Yeni talep gelince ÖNCE buraya yaz, sonra uygula. Sıradaki işi bu dosyadan seç.
> Ana dosya: `v1-benim-sayfam.html` (Bana Özel / Merhaba dashboard'u). Parça parça ilerlenecek.

Durum: ✅ bitti · ⏳ sıradaki · 📋 planlandı

---

## MADDE 1 — Harita renk skalası (geçici düzeltme) ✅
Hiç ihalesi olmayan iller bembeyaz görünüp arka planla karışıyordu.
`renk()`'te "ihale yok" `#EDF1F6`→`#C4DAF0`, alt basamaklar bir kademe koyulaştı.
**NOT: Madde 4 bu haritayı tamamen değiştirecek → bu geçici düzeltme oraya devrolacak.**
→ `v1-benim-sayfam.html` `renk()` (~301)

## MADDE 2 — Yeni logo (tema uyumlu) ✅
Sol menüde beyaz daire içinde amber favicon vardı, mavi temaya sırıtıyordu.
Yeni `favicon-v1.svg` (mavi→teal gradyan "iG"), beyaz daire kaldırıldı, img 48px.
Global tarayıcı favicon'u (amber marka) korundu. Tüm v1 sayfalarında `?v` bump yapıldı.
Canlı doğrulandı (DOM: src=favicon-v1.svg, daire bg=transparent).
→ `favicon-v1.svg`, `js/v1-kabuk.js`, `css/v1.css`

## MADDE 3 — KPI kartları düzeni ✅
"Doğrudan Temin" (tüm geçmiş) → **Aktif Doğrudan Temin** (harita ile aynı aktif tanımı:
durum IN duyuru-yayımlanmış/teklifler-değerlendiriliyor). "Sözleşme" kartı SİLİNDİ → yerine
**Toplam DT + İhale** (tüm dogrudan_temin_ilanlari + tüm ilanlar sayısı). "Aktif İhale" aynı kaldı.
Konsol temiz; değerler üye girişinde dolar. → `v1-benim-sayfam.html` `kpiYukle()`
--- eski açık sorular kapandı: (a) aktif DT = harita tanımı; (b) toplam = DT(hepsi)+ilanlar(hepsi).
6 KPI kartı yeniden kurgulanacak:
- "Aktif İhale 6.226" → doğrudan teminler dahil DEĞİL, kalsın.
- "Doğrudan Temin 3 Mn" → şu an TÜM geçmiş DT sayısı (yanlış). **AKTİF DT sayısı** göstersin.
- "Sözleşme 2,7 Mn" kartını SİL → yerine **Toplam Geçmiş (DT + İhale) sayısı** kartı.
- AÇIK SORULAR: (a) Aktif DT tanımı = harita ile aynı `durum IN (...)` mı? (b) "Toplam Geçmiş"
  = DT+ilanlar mı, DT+ihale_sonuclari mı?
→ `v1-benim-sayfam.html` `kpiYukle()` (~273)

## MADDE 4 — Dashboard haritası interaktif Leaflet ✅ CANLI DOĞRULANDI (81 il, zoom, toplam renk, lejant)
`js/harita.js` `window.HARITA_CFG` ile parametrik yapıldı (renkler/kayitYok/hrefIhale/hrefDt/lejantRenk;
CFG yoksa v2 amber → dashboard.html DEĞİŞMEDEN çalışır). Lejant başlığı rengi CFG'ye bağlandı.
`v1-benim-sayfam.html`: eski SVG harita (`renderHarita`+tr-harita.js) KALDIRILDI → Leaflet iskeleti
(#turkiye-harita/#harita-yukleniyor/#harita-legend) + unpkg Leaflet CSS/JS + js/harita.js?v=4 +
HARITA_CFG (v1 mavi palet, hedef v1-ihaleler?il= / v1-ihaleler?tur=dt&il=) + v1 CSS
(il-tooltip/il-popup/legend açık tema). Yerel: Leaflet+CFG+haritaModSec yüklü, konsol temiz.
Artık: zoom, hover'da İhale+DT+Toplam, tıkla→popup (Güncel İhaleler/Doğrudan Temin), quantile lejant.
**Pull yeterli (migration yok); canlıda üye girişiyle doğrulanacak.** → `js/harita.js`, `v1-benim-sayfam.html`
Şu an v1'de basit satır-içi SVG choropleth var (`renderHarita()`), yalnız aktif İHALE sayısına
göre renk, hover'da düz title. v2 anasayfa haritası (`js/harita.js`, Leaflet) aynısı yapılacak:
- Leaflet tabanlı (zoom +/−, kaydırma).
- **Renk = ilin İhale + Doğrudan Temin TOPLAMI** (quantile 6 kademe; "kayıt yok" ayrı).
- Hover tooltip: şehir + 📋 İhale + ⚡ Doğrudan Temin + Toplam.
- Tıklama → kalıcı popup: "📋 Güncel İhaleler (n)" + "⚡ Doğrudan Temin (n)" butonları
  (`v1-ihaleler?il=` / `v1-ihaleler?tur=dt&il=`).
- Alt lejant: "Renkler ildeki İhale + Doğrudan Temin TOPLAMINI gösterir: [kutular] Az→Çok".
- Veri hazır: RPC `il_sayim_aktif` + `dt_il_sayim_aktif`, GeoJSON `data/turkey-provinces.geojson`.

Uygulama (v2'yi bozmadan, tek kaynak):
1. `js/harita.js`'i `window.HARITA_CFG` ile parametrik yap (`renkler[]`, `kayitYokRenk`,
   `hrefIhale`, `hrefDt`). CFG yoksa mevcut v2 amber değerleri → v2 aynen çalışır.
2. Lejant başlığı rengini satır-içi `var(--white,...)` yerine sınıfa taşı (v1 açık zeminde görünsün).
3. `v1-benim-sayfam.html`: `#v1-harita` SVG kutusunu Leaflet iskeletiyle değiştir, Leaflet CSS/JS +
   `js/harita.js` ekle, `window.HARITA_CFG`=v1 mavi paleti + hedefleri; eski `renderHarita()` ve
   inline TR SVG'yi kaldır.
4. v1 CSS: `.il-tooltip/.il-popup*/.lg-item/.lg-box/#turkiye-harita/.harita-legend` v1 mavi/açık temaya.
5. Palet: v1 mavi sequential (açık→koyu), "kayıt yok"=açık nötr gri-mavi (v2 amber kalır).
→ `js/harita.js`, `v1-benim-sayfam.html`, `css/v1.css`

## MADDE 5 — "Benim Firmam & Referans Firmam" ✅ (frontend)
Mekanizma ZATEN vardı: `firmami_belirle(p_yuklenici_id)` + `firma_icin_acik_ihaleler` herhangi
bir firmayı kabul ediyor → kullanıcı kendi yerine referans/rakip firma seçebiliyordu, ama
yüzeyde yoktu. Yapılan: dashboard butonu "Benim Firmam"→"Benim Firmam & Referans Firmam";
firma seçim ekranı (v1-analiz onboarding) metni "kendi ya da referans/rakip firma" olarak
güncellendi; "Katılabileceğiniz İhaleler" boş-durum metinleri referans firmayı öneriyor.
**Pull yeterli (migration yok).** → `v1-benim-sayfam.html`, `v1-analiz.html`
--- ESKİ PLAN:
Bana Özel'deki "Benim Firmam" butonu, kullanıcının kendi firması yanında bir **referans firma**
(yakın gördüğü / rakip) seçmesini de kapsayacak.
**Neden:** Kullanıcı ihale takibine yeni başlamış, henüz ihaleye girmemiş olabilir → kendi geçmişi
yoksa, referans bir firmayı seçip **ona uygun ihaleleri** kovalayabilir.
- Buton etiketi: "Benim Firmam" → "Benim Firmam & Referans Firmam".
- Akış: kendi firma + referans firma seçimi; eşleşme motoru referans firma profiline göre de öneri versin.
- MADDE 6 ile doğrudan bağlantılı (eşleşme algoritması referans firmayı da beslemeli).
→ `v1-benim-sayfam.html` (`.v1-firmam-btn` ~95) + `v1-analiz.html` akışı + backend eşleşme.

## MADDE 6 — Eşleşme algoritması ✅ CANLI (v3: KATMANLI sektör-öncelikli)
v3 (`migration_firmam_eslesme_v3.sql`): kullanıcı 'il kötü referans' dedi → KESİN KATMAN skoru:
Sektör 100 / Kurum 30 / İl 10 → Sektör+Kurum(130)>Sektör+İl(110)>Sektör(100)>Kurum(30)>İl(10).
Bedel-yakınlığı artık katman DEĞİL, aynı katman içi tiebreaker; ±%500 hard bant KALDIRILDI.
Sektör=kategori VEYA başlık kelimesi. İl gerekçede yalnız TEK sinyalse. **v4** (`migration_firmam_eslesme_v4.sql`): FREKANS-AĞIRLIKLI — Sektör 100+50×pay (firma o kategoride ne kadar iş almışsa öne) + Kurum 30 + İl 10 + TAKİP bonusu (takip sektör/kurum +15, takip firma 0). Wrapper takip_sektorler/takip_idareler'i geçirir.
`backend/migration_firmam_eslesme_v2.sql` — firma_icin_acik_ihaleler'e **IDARE sinyali** (en çok
iş aldığı ilk 8 idare → +25 puan + OR filtresi + "sık çalıştığınız idare" gerekçesi); **bant
±%500→±%300** (p_bant 5→3, wrapper da 3). Frontend eslesme()'ye 🎯 gerekçe satırı (deploy-güvenli).
**VDS'te supabase_admin ile uygulanacak.**
--- ESKİ ANALİZ:
Bu bölüm `firmam_acik_ihaleler()` RPC'sini çağırıyor (→ `firma_icin_acik_ihaleler`).
**Mevcut algoritma** (kaynak: `backend/migration_firmam_eslesme.sql`):
Kullanıcının SEÇTİĞİ firmanın GEÇMİŞ KAZANIMLARINDAN profil çıkarır:
  - `kategoriler` = firmanın en çok kazandığı ilk 5 kategori,
  - `iller` = firmanın iş aldığı iller (distinct),
  - `bedel` = kazanan tekliflerin MEDYANI.
Sonra AKTİF ihaleleri (durum='aktif', son teklif ≥ bugün) şöyle eşler/puanlar:
  - Kategori firmanın uzmanlık listesindeyse VEYA başlık, firmanın geçmiş başlık
    anahtar kelimeleriyle eşleşiyorsa (`ihale_konu_kelimeleri`+`tr_fold LIKE`),
  - VE yaklaşık maliyet firmanın medyanının ±5 katı (±%500) bandında.
  - Puan (skor): +40 kategori · +15 il · +20 bedel-yakınlığı (ln oranı). Sırala: skor↓, tarih↑.
  - Eşleşme nedeni: "Uzmanlık alanınız"/"Benzer konu" + "· daha önce iş aldığınız il".

**Kısacası neye göre:** şehir DEĞİL asıl sürücü; SEÇİLİ firmanın (1) kazandığı kategoriler,
(2) çalıştığı iller, (3) tipik iş büyüklüğü. Kendi aktivite/şehrin değil, seçtiğin firmanın karnesi.

**Zayıf noktalar / iyileştirme adayları:**
- Firma seçili değilse veya firmanın kazanımı yoksa → BOŞ döner (Madde 5 bunu referans firmayla çözer).
- ±%500 bant çok geniş → daralt / dinamik.
- Kullanılmayan güçlü sinyaller: idare (çalıştığı kurumlar), CPV/OKAS, sektör, YAKINLIK/zaman ağırlığı.
- Anahtar-kelime dalı her çağrıda 50 başlıktan yeniden çıkarılıyor (maliyet) → önceden hesapla.
- Kategori top-5 sabit; ağırlıklar (40/15/20) sabit → ayarlanabilir/öğrenen olabilir.
- Bkz. hafıza: eşleştirme-motoru-v3 (OKAS %2,8 ölü, jenerik kova %58).
→ `backend/migration_firmam_eslesme.sql`, `v1-benim-sayfam.html` (`eslesme()` ~334)

## MADDE 7 — Sonuç Raporu "statement timeout" hatası (BUG) ✅ (filtreli), 🟡 (kelime-tek edge)
`backend/migration_rapor_sonuc_timeout_fix.sql` — `rapor_sonuc` artık ÖNCE ilanlar'ı
(il+kategori+başlık trigram) süzüp SONRA ihale_sonuclari'na ilan_id ile join ediyor.
VDS'te `-U supabase_admin` ile UYGULANDI (postgres sahibi değildi). **Canlı test:** belpa+ANKARA
→ timeout GİTTİ, anında 0 kayıt döndü (eskiden timeout). ✅
KALAN EDGE: kelime TEK BAŞINA (il/kategori/tarih filtresiz) hâlâ yavaş olabilir — ilanlar
trigram taraması tek başına yetmiyor. (Regresyon değil; eskiden de yavaştı.) İyileştirme
adayı: STORED `baslik_fold` kolonu + idx_ilanlar_baslik_fold_trgm2. ✅ YAPILDI:
`backend/migration_rapor_sonuc_edge_fix.sql` — kelime filtresi `tr_fold(baslik)` ifadesi yerine
STORED `baslik_fold` (idx_ilanlar_baslik_fold_trgm2) → SPESİFİK/nadir kelime artık hızlı (belpa-tipi=asıl hata). CANLI: 'okul' gibi ÇOK YAYGIN kelime tek başına hâlâ ağır (17K sonuç — indeks değil HACİM sorunu; gerçek çözüm arama-motoru altyapısı, kapsam dışı). UX: v1-raporlar'da geniş kelime-tek sonuç aramasında 'il/tarih filtresi ekleyin' ipucu. ✅ (nadir kelime + reported bug) / yaygın kelime = filtre gerektirir. **B UYGULANDI** (`migration_rapor_sonuc_6ay.sql`): kelime-tek geniş aramada varsayılan pencere son 6 AY (kullanıcı tarih girerse COALESCE onun değerini kullanır → seçtiğine dokunmaz); frontend 'son 6 ay' notu.
**Belirti:** Raporlarım → "İhale Sonuç Raporlarım", Kelime="belpa", İl=ANKARA →
> "Rapor alınamadı. canceling statement due to statement timeout"

**Kök neden** (kaynak `backend/migration_rapor.sql` → `rapor_sonuc`): Sorgu ihale_sonuclari'nı
ÖNCE yalnız `sonuc_tarihi ≥ (tarih verilmezse son 1 yıl)` + `kazanan_firma NOT NULL` ile
MATERIALIZED daraltıyor → bu küme KOCAMAN (bir yıllık sonuç). SONRA `ilanlar`'a LEFT JOIN edip
`il=ANKARA` ve `tr_fold(baslik) LIKE '%belpa%'` süzülüyor. il/kelime filtresi JOIN'DEN SONRA
uygulandığı için trigram/il indeksleri DEVREYE GİRMİYOR → dev nested-loop → timeout.
(Karşılaştır: `rapor_ihale` doğrudan ilanlar'ı süzdüğü için trigram indeksini kullanıyor, hızlı.)

**Çözüm yönü:** il/kategori/kelime verildiğinde ÖNCE `ilanlar`'ı süz (idx_ilanlar_baslik_fold_trgm
+ il indeksi ile küçük aday kümesi), SONRA `ihale_sonuclari`'na `ilan_id` ile join. Yani
sürücü tabloyu ters çevir. Tarih boşken 1 yıl tavanı tek başına yeterince seçici değil.
- İkincil: sonuç kutusu başlığı ilk açılışta "İhale Raporu" kalıntısı gösteriyor (satır 126
  yalnız çalıştırınca güncelleniyor) — küçük etiket düzeltmesi.
→ `backend/migration_rapor.sql` (`rapor_sonuc`), `v1-raporlar.html`

## MADDE 8 — İhale listesinde satır aksiyonu: "Takip Et" eklendi ✅
İhale satırlarına BİRİNCİL yuvarlak "Takip Et" (yıldız) butonu eklendi (Takvime Ekle + Detay
korundu). Takip edilince altın renkli, tıklayınca `takipler` tablosuna upsert/delete (detay
sayfasıyla aynı kanıtlı mantık); misafirde login'e yönlendirir; sayfa yüklenince mevcut takipler
işaretlenir. DT satırlarında yok (takipler ilan_id'ye bağlı). Canlı doğrulandı (sıra: Takip et ·
Takvime ekle · Detay). → `v1-ihaleler.html`
--- ESKİ PLAN NOTU:
İhaleler listesinde (Aktif İhaleler) her satırdaki belirgin yuvarlak buton "Takvime ekle"
(takvim ikonu). Kullanıcı: yanlış — orada **kolay erişilebilir "Takip Et"** (yıldız) olmalı.
- Birincil yuvarlak buton "Takip Et" (yıldız, takibe al/çıkar toggle) olsun; "Takvime ekle"
  ikincil/menüye alınsın (ya da yanında dursun ama takip öncelikli).
- Takip durumu satırda görünsün (dolu/boş yıldız). Giriş yoksa login'e yönlendir.
→ `v1-ihaleler.html` (satır aksiyonu, ~408 `data-takvim`; `takipler` tablosu + `v1-ihale-detay`'daki takip mantığı örnek)

## MADDE 9 — "Benzer İhaleler" skorlu ✅ CANLI DOĞRULANDI (balık→balık, "Aynı idare/il")
YAZILDI: `backend/migration_benzer_ihaleler.sql` — `benzer_ihaleler(p_ilan_id,p_limit)` skorlu
RPC (aynı idare +35, il +20, kategori +20, başlık konu-kelimesi +8/kelime; tur ön-eleme).
SECURITY DEFINER (idare içeride skorlar, döndürmez → misafire sızmaz). `v1-ihale-detay.html`
`benzerYukle` RPC'ye geçirildi + "neden" alt satırı (Aynı idare/kategori/il) + RPC yoksa eski
filtreye düşen fallback (deploy penceresi güvenli). **VDS'te supabase_admin ile uygulanacak.**
Balık↔un sorununu başlık kelimesi ("balik" vs "un") ayırır.
--- ESKİ PLAN:
**Mevcut** (`v1-ihale-detay.html` `benzerYukle` ~367): yalnız `kategori` = aynı VE `tur` = aynı
sabit filtre (`.eq`). İl yok, idare yok, başlık kelimesi yok.
**Sorun (kullanıcı örneği):** İstanbul'daki BALIK ihalesine, Aksaray'daki EKMEKLİK UN ihalesi
"benzer" çıkıyor — ikisi de "Gıda" kategorisi + "Mal" tipi. Kategori tek başına çok kaba.
**İstenen:** kategori + **şehir** + **idare** birlikte (mantıklı skorlama), + kategorizasyonu
daha iyi yap.
**Çözüm yönü:** sabit `.eq` yerine SKORLU bir `benzer_ihaleler(p_ilan_id)` RPC'si —
  - aynı idare (+yüksek), aynı il (+orta), aynı kategori (+orta), aynı tur (ön-eleme),
  - **başlık konu-kelime örtüşmesi** (`ihale_konu_kelimeleri`+`tr_fold`) → "balık" vs "un"
    ayrışır (aynı kategoride bile),
  - skor↓ sırala, ilk N. (MADDE 6 eşleşme motoruyla aynı ailedendir — ortak sinyal seti.)
→ `v1-ihale-detay.html` (`benzerYukle`), yeni `backend/migration_benzer_ihaleler.sql`

## MADDE 10 — Tüm v1 haritalarında "boş il" rengi (bembeyaz sorunu) ✅
Birden çok v1 haritasında iş/talep olmayan iller sayfa zeminiyle karışıp bembeyaz görünüyordu.
Hepsi tek tutarlı palete oturtuldu: kovalar `#C3D8EF→#0C3E70`, boş il `#DBE1E9` (nötr gri-mavi).
- Dashboard SVG haritası (`v1-benim-sayfam.html`) — MADDE 1'de yapıldı (geçici, MADDE 4'e kadar).
- Firma-analiz "İl Bazlı İş Dağılımı" (`v1-firma-analiz.html`): `H_BOS #F1F4F8→#DBE1E9`,
  `H_RENK` en açık iki kova koyulaştırıldı.
- `v1-harita.html` "Firma Yoğunluğu / Açık Talepler": `VERI_YOK #EAEFF5→#DBE1E9`,
  `RAMPA` en açık iki kova koyulaştırıldı.
→ `v1-benim-sayfam.html`, `v1-firma-analiz.html`, `v1-harita.html`

## MADDE 11 — "RFQ" → "Açık Talepler" (Türkçeleştirme) ✅
`v1-harita.html`'de kullanıcıya görünen "Açık RFQ" / "Açık Talep (RFQ)" / "🤝 RFQ" ifadeleri
Türkçeleştirildi: KPI etiketi, sektör-seçili etiket, lejant başlığı, panel alanı "Açık Talepler";
satır rozeti "🤝 Talep". Kod içi `rfq` anahtarları/id'ler ve yorumlar korundu.
→ `v1-harita.html`
(NOT: "Bu ilde öne çıkan firmalar" kategori bazlı sıralama önerisi — kullanıcı ES GEÇ dedi, iptal.)

## MADDE 12 — "Bu ilde öne çıkan firmalar": YIL bazlı sıralama ✅ CANLI (MV, 20sn→109ms)
YAZILDI: `backend/migration_il_firma_yil.sql` — `il_firma_yil(p_il_folds,p_yil,p_limit)` RPC
(il_sektor_firmalar deseninin yıl varyantı; idx_ilanlar_il_fold_kategori kullanır, statement_timeout
15s, normalize_firma grup). `v1-harita.html`: panele "Tüm Yıllar + 2004→bugün" yıl seçici (24 opt);
yıl seçilince il_firma_yil'e geçer (sektörden bağımsız il+yıl), "Tüm Yıllar"=mevcut davranış.
Yerel: seçici render + konsol temiz.
⚠️ PERF: ilk RPC canlıda ~20sn (ANKARA 2024) → timeout. ÇÖZÜM: `backend/migration_il_yil_firma_mv.sql`
— `il_yil_firma` materialized view (il_fold×yıl×normalize_firma → sözleşme+bedel) + indeks;
il_firma_yil artık MV'den anlık okur (imza aynı, frontend değişmez). MV kurulumu tek seferlik
ağır (2.9M satır, dakikalar). **GECE REFRESH cron'a eklenecek** (REFRESH ... CONCURRENTLY il_yil_firma).
**VDS'te supabase_admin ile uygulanacak, sonra <50ms doğrulanacak.**
(Kategori sıralaması yerine — kullanıcı bunu istedi.)
⚠️ BULGU (30 Tem canlı probe): dinamik en-eski-yıl KIRILGAN — ihale_sonuclari sonuc_tarihi
sıralaması TIMEOUT (indekssiz tam-tablo); DT'de en eski tarih 1926-01-22 = ÇÖP veri.
→ KARAR: yıl aralığı SABİT **2004 → currentYear** (client-side üret; 4734 Kanunu 2003).
Backend yeni RPC `il_firma_yil(p_il_folds, p_yil, p_limit)` — ihale_sonuclari (o yıl sonuc/
sozlesme tarihi) → ilanlar (il) join → yuklenici bazında grupla. "Tüm Yıllar"=mevcut davranış.
**Mevcut** (`v1-harita.html` `firmaListesi` ~478): sektörsüz modda firmalar
`yukleniciler.toplam_ciro` (TÜM-ZAMAN toplam) ile sıralanıyor → hep toplam en yüksek çıkıyor.
Bu alanlar önceden hesaplanmış toplam; yıla göre süzülemez.
**İstenen:** Sağ panele bir **yıl seçici** ("Tüm Yıllar" + yıl listesi). Seçilen yıla göre
o ildeki öne çıkan firmalar listelensin.
- **Yıl aralığı:** hardcode DEĞİL — elimizdeki verinin en eski yılından bugüne. Min yıl
  `ihale_sonuclari`'ndan dinamik alınmalı (min `sonuc_tarihi`/`sozlesme_tarihi` yılı;
  ~2000'ler). Dropdown: "Tüm Yıllar" + o aralıktaki her yıl.
- **"Tüm Yıllar"** = mevcut davranış (yukleniciler toplam ciro/sözleşme).
- **Belirli yıl** = yeni RPC, örn. `il_firma_yil(p_il_folds, p_yil, p_limit)`:
  `ihale_sonuclari` (o yılın sozlesme/sonuc tarihi) → `ilanlar` (il) join → yuklenici_id
  bazında grupla, sözleşme sayısı + toplam bedel, ilk N. (idx_is_tarih/yuklenici_id indeksleri var.)
  Sektör modunda `il_sektor_firmalar`'a da opsiyonel `p_yil` eklenebilir.
- Misafir maskesi mevcut kuralla korunur (firma listesi üyelere özel).
→ `v1-harita.html` (panel + `firmaListesi`), yeni `backend/migration_il_firma_yil.sql`

## MADDE 13 — İhale detayında "EKAP'a Git" butonu ✅
İhale detay aksiyon çubuğuna (Takibe Al / Takvime Ekle / Teklif Oluştur / AI Fiyat Stratejisi
yanına) "🔗 EKAP'a Git" eklendi. EKAP IKN'ye özel public deep-link SUNMADIĞI için (oturum ister,
406) doğru EKAP modülüne yönlendiriyor: Doğrudan Temin ise `ekapv2.kik.gov.tr/ekap-dt/search`,
ihale ise `ekapv2.kik.gov.tr/ekap/search`. Kullanıcı sayfada görünen IKN ile aratır/giriş yapar.
DT/ihale ayrımı usul+tur metninden. (v2 `ihale-detay.html` `ekapLink` mantığıyla aynı.)
→ `v1-ihale-detay.html` (`ciz`, aksiyon çubuğu)

## MADDE 14 — Doğrudan Temin Analizi'ne YIL filtresi ✅ CANLI (MV, 12.4s→6.6ms)
`backend/migration_dt_analiz_yil.sql` — `_dt_ozet_json`+`dt_analiz_ozet`'e `p_yil` eklendi (sargable
tarih aralığı; imza 3→4 arg → MV+fonksiyonlar DROP+recreate). Filtresiz→MV, yıllı→canlı (15s).
`v1-dt-analiz.html`: filtre barına "Tüm Yıllar + 2004→bugün" seçici; p_yil YALNIZ yıl seçiliyken
gönderilir (deploy-güvenli: migration'dan önce yıl seçilmedikçe eski RPC ile çalışır). Yerel: seçici
render + konsol temiz.
⚠️ PERF: yıl-tek ~12.4s (2024 DT=305K) → çözüm `backend/migration_dt_analiz_yil_mv.sql`:
idx_dt_ilanlari_tarih + `dt_analiz_yil_mv` (yıl başına özet, ~23 satır). Yıl-tek→MV anlık,
yıl+il→canlı. **VDS'te supabase_admin ile uygulanacak; gece refresh cron'a.**
⚠️ Yıl aralığı SABİT 2004→currentYear (MADDE 12 ile aynı bulgu: çöp 1926 + timeout).
**Neden:** Yüksek enflasyonlu bir ülke → "Ort./Medyan Kazanan Bedel" gibi ₺ metrikleri yıla göre
çok değişken; tüm-zaman ortalaması yanıltıcı. Yıl bazlı süzme gerekli.
**Mevcut** (`v1-dt-analiz.html`): filtreler Tüm Türler / Tüm İller / Tüm Sektörler — yıl YOK.
**İstenen:** "Tüm Yıllar" + yıl seçici (MADDE 12 ile aynı yaklaşım). Seçilen yıla göre tüm KPI'lar
(Toplam DT, Sonuçlanan, Ort./Medyan Kazanan Bedel) ve grafikler yeniden hesaplansın.
- Yıl aralığı hardcode DEĞİL — DT verisinin en eski yılından bugüne (min ilan/sonuç tarihi yılı).
- DT özet RPC'lerine `p_yil` parametresi + tarih filtresi eklenmeli (arka uç).
→ `v1-dt-analiz.html` (filtre barı), DT analiz RPC'leri (`backend/migration_dt_analiz.sql` vb.)

## MADDE 15 — DT Analizi: aktif sekme "DT Analizi" görünmüyordu ✅
Üst kısayol barında aktif (mavi) buton kendi sayfası yerine "DT Listesi"ni işaret ediyordu →
"DT Analizi" yazısı hiç yoktu. Aktif buton bu sayfaya çevrildi: "⚡ DT Analizi" (dolu),
"📋 DT Listesi" ayrı kısayol olarak eklendi. Canlı doğrulandı (aktif = "⚡ DT Analizi").
→ `v1-dt-analiz.html` (`v1-kisayol`)

## MADDE 16 — DT kazanan firma analizi (firma bazında DT istatistiği) ✅ CANLI (part-1 + part-2 bağlama)
**✅ CANLI DENETİM (1 Ağu):** `firma_dt_ozet(p_firma_ad)` canlı (pg_proc doğrulandı). part-1 uygulanmış.
**✅ PART-2 BAĞLAMA (1 Ağu):** `dogrudan_temin_sonuclari.yuklenici_id` dolduruldu (2M NULL'du).
`dt_yuklenici_baglama()` (postgres sahipli INVOKER, normalize_firma=normalize_ad kesin eşitlik,
IS DISTINCT guard) → **1.103.448 satır bağlandı (%54,5)**, 61.544 firma; kalan %45,5 = yalnız DT
kazanmış (yukleniciler'de yok) → NULL DOĞRU. normalize_ad BENZERSIZ (220.181) → belirsizlik yok.
Gece tazeleme run_scraper.sh'a eklendi (yuklenici_yenile'den sonra). `backend/migration_dt_yuklenici_baglama.sql`.
**✅ İL BAZLI DT FİRMA SIRALAMASI (1 Ağu):** haritada il tıklanınca "öne çıkan firmalar" paneline
📋 İhale / ⚡ DT toggle eklendi → DT modu `il_sektor_firmalar_dt` çağırır (İhale ile aynı kolonlar,
aynı render; iki evren ayrı). DT modunda yıl seçici gizlenir. Canlı doğrulandı (toggle/mod/kilit/0 hata);
üye-özel (uyeMi guard). → `v1-harita.html`. MADDE 16 part-2 TAMAMEN kapandı.
**KEŞİF (canlı):** Kazanan verisi `dogrudan_temin_ilanlari`'nda DEĞİL → ayrı tablo
`dogrudan_temin_sonuclari` (**853.170 satır**): kazanan_firma, kazanan_bedel, dt_no,
sozlesme_tarihi, yuklenici_id (boş, bilerek). İl/kategori dogrudan_temin_ilanlari'nda (dt_no join).
kazanan_firma anon'a KAPALI.
**PART-1 YAZILDI:** `backend/migration_dt_firma_ozet.sql` — `firma_dt_ozet(p_firma_ad)` RPC
(SECURITY DEFINER, authenticated) + `idx_dt_sonuc_kazanan_fold` fonksiyonel indeksi. tr_fold ile
tutucu isim-eşitliği (sahte pozitif yok). Döndürür: dt_sayisi, bedelli, toplam/medyan bedel,
il+kategori kırılımı. **VDS'te `-U supabase_admin` ile uygulanacak.**
KALAN (part-2): opsiyonel yukleniciler.id bağlama; il bazında DT firma sıralaması (harita paneli).
--- ESKİ PLAN:
**Boşluk:** Firma Analizi yalnız ihale evrenini (`yukleniciler`+`ihale_sonuclari`) gösteriyor →
bir firmanın **doğrudan temin kazanımları hiç görünmüyor**. Oysa veri VAR:
`dogrudan_temin_ilanlari.kazanan_firma` (isim) + `kazanan_bedel`, ~853K sonuçlanmış DT kaydı.
**Kök neden:** DT kazananları `yukleniciler.id`'ye BAĞLI DEĞİL — sadece isim; `yuklenici_id`
linkleme scraper'da "ileride" olarak bırakılmış (`dt_kazanan_scraper.py` notu). VKN %0 →
tek join anahtarı normalize isim (bulanık).
**Yapılacak (2 parça):**
1. **Veri bağlama / toplama:** DT `kazanan_firma` → `yukleniciler.id` isim-normalize eşleştirme
   (veya ilk aşama: isim bazında DT firma agregasyonu). Yeni RPC: firma bazında DT sözleşme
   sayısı + toplam/medyan kazanan bedel + il/sektör kırılımı.
2. **UI:** Firma Analizi'ne "Doğrudan Temin Kazanımları" bloğu — ihale evreninden AYRI kutu,
   "yalnız DT" rozetiyle (iki evren toplanmaz ilkesi korunur). Alternatif: ayrı DT firma analizi.
**Uyarı:** İsim eşleştirmesi sahte pozitif üretebilir → doğrulanmamış eşleşmeyi "kesin" gibi sunma
(bkz. hafıza `vkn-yok-beyan-rozet` — beyan≠doğrulanmış).
→ yeni `backend/migration_dt_firma.sql`, `v1-firma-analiz.html` (DT bloğu)

## MADDE 17 — Analiz gezinmesi tek merkezde; DT sayfasından nav kaldırıldı ✅
**Nihai tasarım (kullanıcı):** Gezinme YALNIZ "Analiz" sayfasında (hub). Her analiz başlı başına
bir sayfa → alt sayfada tekrar nav OLMAZ.
- `v1-dt-analiz.html`: sayfa-içi analiz nav'ı TAMAMEN kaldırıldı (sadece başlık+içerik). ✓
- `v1-analiz.html`: hub nav'a "🏢 Firma Analizi" + "🏛️ Kurum Analizi" eklendi → 9 sekme:
  Rekabet · Türkiye Haritası · Sektör · Dış Ticaret · Doğrudan Temin · Uyumluluk · Firma Analizi ·
  Kurum Analizi · Firma Segmentleri. Canlı doğrulandı.
- (İki yanlış deneme düzeltildi: önce 4-sekme kısaltma, sonra 7-sekme sayfa-içi bar — ikisi de
  kullanıcının istediği değildi; doğrusu: alt sayfada nav YOK.)
→ `v1-dt-analiz.html`, `v1-analiz.html`
KALAN: diğer analiz alt sayfalarında (varsa) benzer sayfa-içi nav'ları da kaldır (MADDE 19).

**Sonradan (isim + sıra):** "Rekabet Analizi" → "**İhale Analizi**" olarak yeniden adlandırıldı
(nav + sayfa başlığı `v1-rekabet.html` + kirinti + DT sayfasındaki metin göndermesi). Nav sırası:
1. İhale Analizi (aktif) 2. Doğrudan Temin Analizi 3. Türkiye Haritası 4. Sektör 5. Firma Analizi
6. Kurum Analizi 7. Uyumluluk 8. Firma Segmentleri 9. Dış Ticaret Analizi (en son). Canlı doğrulandı.

## MADDE 18 — Firma Analizi: DT kazanımları görünür ✅ CANLI (Phase-A + Phase-B)
**✅ CANLI DENETİM (1 Ağu):** `firma_dt_toplam` MV (postgres sahipli) + `firma_dizin_dt`/`firma_dizin_birlikte`
(p_kamu_dahil dahil) canlı. İki faz da uygulanmış — 🟡 bayat işaretti.
**Phase-B ✅ CANLI DOĞRULANDI (MADDE 18-B):** 3 mod (İhale/DT/İkisi) canlı; dt 133ms, birlikte 614ms. `backend/migration_firma_dt_toplam_mv.sql` — firma_dt_toplam MV
(normalize_firma → DT sözleşme+bedel) + `firma_dizin_dt` (DT bedeline göre) + `firma_dizin_birlikte`
(yukleniciler LEFT JOIN DT, normalize_ad=firma_norm KESİN eşitlik → ihale+DT toplamı). Firma dizinine
3 mod toggle (📋 İhale/⚡ DT/🔗 İkisi); ciro kolon başlığı moda göre değişir; RPC modunda count-yok
pager. MV sahibi postgres'e devredildi + run_scraper.sh gece refresh'e eklendi. **supabase_admin ile uygulanacak.**
**Phase-A YAPILDI:** Firma detayına "⚡ Doğrudan Temin Kazanımları" bloğu eklendi (ihale
KPI'larının altında, "yalnız DT" rozetli, altın çerçeve) — `firma_dt_ozet(y.ad)` ile:
DT sözleşme sayısı + toplam/medyan bedel + DT il/kategori dağılımı. Firma adı normalize eşleşme
uyarısı da var. DT kazanımı yoksa blok hiç açılmaz. → `v1-firma-analiz.html`
Canlı doğrulanacak (ÜNTES: 42 DT / ₺13,65M).
**KALAN Phase-B:** firma LİSTESİNİ 3 moda göre SIRALAMA (① ihale ② DT ③ birlikte) — bu, tüm
firmalar genelinde DT toplamı gerektirir (top-firmalar-by-DT RPC / MV). Ayrı iş.
--- ESKİ PLAN:
Firma Analizi'nde firmaları 3 farklı temele göre sıralayan/gösteren alt sekme:
1. **Sadece İhaleler** (mevcut davranış — ihale_sonuclari).
2. **Sadece Doğrudan Teminler** (DT kazanan verisi — MADDE 16'ya BAĞLI).
3. **İhale + Doğrudan Temin birlikte** (ikisini toplayan bütünsel firma görünümü).
**Gerekçe (kullanıcı):** Bir firmanın gerçek büyüklüğünü ancak ihale + DT birlikte görünce
doğru değerlendiririz.
**Bağımlılık:** 2 ve 3 için MADDE 16 (DT kazanan → firma bağlama) ÖNCE bitmeli. İki evren
ölçek farkı (DT medyanı ≈ ₺37 bin) → "birlikte" modda toplama değil, AYRI kolon/rozetle sun.
→ `v1-firma-analiz.html`, DT firma RPC'si (MADDE 16)

## MADDE 19 — Diğer analiz alt sayfalarından sayfa-içi nav kaldır ✅
Tarandı: firma-analiz, uyumluluk, firma-segmentleri, harita, sektorler, kurumlar sayfalarında
çok-sekmeli sayfa-içi analiz nav'ı YOK (yalnız başlık/breadcrumb/tekil buton). Kaldırılacak
fazla nav kalmadı — DT sayfasındaki tek istisnaydı (MADDE 17'de kaldırıldı). Prensip sağlandı.

---


## GECE REFRESH (housekeeping) ✅ CANLI DOĞRULANDI (1 Ağu — İKİ KATMANLI fix)
**Sessiz-fail bug'ı denetimle bulundu ve kapatıldı.** 3 MV (dt_analiz_mv, dt_analiz_yil_mv,
il_yil_firma) supabase_admin sahibiydi → cron `-U postgres` REFRESH'i her gece "permission denied"
alıp SESSİZCE bayatlıyordu (MADDE 12/14 verisi eski kalıyordu). `backend/migration_mv_owner_fix.sql`
ile İKİ KATMAN düzeltildi:
- **Katman 1 (owner):** 3'ü de postgres'e devredildi (eski migration yalnız 2'ydi, dt_analiz_mv atlanmıştı).
- **Katman 2 (grant):** owner devri, `_dt_ozet_json` (SECURITY DEFINER, ACL yalnız supabase_admin=X)
  çağıran dt_analiz_mv + dt_analiz_yil_mv'yi bozdu (postgres superuser değil → çağıramaz). postgres'e
  EXECUTE verildi (iç veri erişimi yine definer yetkisiyle; anon/authenticated etkilenmez).
**KANIT (canlı):** GRANT sonrası 3 MV de `-U postgres` + CONCURRENTLY ile hatasız refresh oldu →
cron artık gece bunları güncelleyecek. Unique index + SECURITY DEFINER denetimde doğrulandı.
→ `backend/migration_mv_owner_fix.sql` (uygulandı, VDS'te canlı)


## MADDE 20 — Firma dizini & haritada tam sıralama (DT/İhale/İkisi + sektör + ölçüt + son 1 yıl) ✅
Kullanıcı: firma dizini/haritasında sıralamayı İHALE ile yapabiliyoruz ama DT ve İkisi'de yapamıyoruz;
ayrıca haritada il-bazlı firma sıralaması İhale/DT ayrı seçilebilmeli + sektör + ölçüt.

**PARÇA A — LİSTE: DT & İkisi modlarında sıralama** ✅ YAPILDI (`migration_firma_dizin_sort.sql`)
- İhale modu: sıralama zaten var (en çok ciro/sözleşme/son iş/isim).
- DT modu: `firma_dizin_dt`'ye p_sort ekle (dt_bedel / dt_sozlesme). Sort dropdown DT'de aktif.
- İkisi modu: `firma_dizin_birlikte`'ye p_sort ekle (toplam bedel / toplam sözleşme).
- (Son-1-yıl list sort DT'de yıl-boyutu gerektiriyor → Parça B'deki MV ile.)

**PARÇA B — HARİTA: il bazında firma sıralaması, İhale/DT bazlı + sektör + ölçüt + son 1 yıl** ✅ (deploy bekliyor)
- Harita paneline İhale/DT toggle + ölçüt seçici (4: tüm-zaman & son-1-yıl × ciro & sözleşme).
- MİMARİ: İhale büyük MV il_sektor_firma_mv'ye `sozlesme_1y`/`bedel_1y` FILTER kolonları (REBUILD;
  CASCADE düşen mini il_sektor_ozet_mv yeniden kuruldu). DT için AYNI ikili: il_sektor_firma_dt_mv
  (anon KAPALI, isim) + il_sektor_ozet_dt_mv (anon açık, yoğunluk). now() refresh anında = rolling 1y.
  DT yıl kaynağı i.tarih (~%100 dolu). Firma listesi RPC'leri isim döndüğü için authenticated.
- Choropleth yoğunluğu tüm-zaman; son-1-yıl+ölçüt yalnız FİRMA LİSTESİNİ etkiler (cold-start timeout
  kesildi — MV'de önceden hesaplı). ANON MASKE KORUNDU (yeni firma-adı MV'lerinde REVOKE anon,public).
- ✅ DEPLOY EDİLDİ + CANLI DOĞRULANDI: İhale MV 731.185 / DT MV 399.433 satır; DT yoğunluk
  anon'a açık gerçek veri; İhale+DT firma MV'leri anon'a `permission denied` (maske ✅); harita
  81 il DT'ye göre boyanıyor; panel KPI baz-duyarlı (Ankara Gıda 1.698 firma/8.168 söz.). Auth
  firma-listesi sıralaması: RPC var+auth-gated+MV dolu ama claude-in-chrome içerik-filtresi
  firma-adı sayfasını bloklayıp makine-doğrulamayı engelledi (giriş yapmış haritada gözle görülür).
→ `v1-firma-analiz.html` (harita), `backend/migration_harita_20b.sql`, `backend/run_scraper.sh` (2 yeni MV refresh)
- Not: Parça A (dizin listesi DT/İkisi sıralama) daha önce ✅ (migration_firma_dizin_sort.sql).


## MADDE 21 — Arama: min 3 harf + debounce + Ara butonu (boşa sorguyu kes) ✅
Kullanıcı: her harfte DB sorgusu (a/ah/ahm...) boşa yük. Standart: min 3 harf + 500ms debounce +
Enter + "🔍 Ara" butonu. **YAPILDI:**
- v1-firma-analiz dizin araması (dz-arama) — min3/500ms/Enter/Ara butonu.
- **Üst-bar global arama** (js/v1-kabuk.js `git()`): zaten Enter/butonla çalışıyor (per-keystroke
  DB yok); min-3 guard eklendi → 1-2 harf hedef sayfayı tam-tablo taramaya YOLLAMAZ (kırmızı
  kenar + "En az 3 harf" uyarısı). 31 sayfada `?v=10→11` bump.
- **v1-analiz onboarding (v1-ac)**: per-keystroke `yukleniciler` autocomplete'i min-2/300ms →
  **min-3/500ms + Enter=hemen ara**; placeholder "(en az 3 harf)".
- MUAF (client-side, DB'ye gitmiyor → min-3 sadece yavaşlatır): v1-kurumlar (tüm liste tek
  seferde inip `suz()` filtreler), v1-sektorler (41 sabit kategori), v1-ihaleler "Listede Ara".
Canlı doğrulandı: üst-bar 2 harf→nav yok/3 harf→`?ara=`; 0 konsol hatası.
→ `js/v1-kabuk.js`, `v1-analiz.html`, 31× `?v` bump


## MADDE 22 — Firma dizini KPI'ları mod-duyarlı ✅ CANLI
**✅ CANLI DENETİM (1 Ağu):** `firma_ozet_dt()` + `firma_ozet_birlikte()` canlı (pg_proc doğrulandı). Uygulanmış — 🟡 bayat.
Kullanıcı: üst KPI'lar (Toplam Firma/Sözleşme/Ciro/İş Ortaklığı) hep "yalnız ihaleler" →
mod değişince değişsin. YAPILDI: `firma_ozet_dt()` + `firma_ozet_birlikte()` RPC (yuklenici_ozet
ile aynı şekil); frontend dzIstatistik moda göre RPC seçer + rozet/etiketleri günceller
(yalnız ihaleler / yalnız DT / ihale + DT). İkisi'de firma = normalize isim BİRLEŞİMİ (çift saymaz).
→ `v1-firma-analiz.html`, `backend/migration_firma_ozet_modlar.sql`

## MADDE 23 — İhaleler: Geçmiş sekmesi + Sonuç/Geçmiş'te İhale/DT seçici + enum bug ✅
Kullanıcı: (a) "zamanı geçmiş ama sonucu açıklanmamış" ihaleler nerede? → **Geçmiş** sekmesi
(durum='aktif' AND son_teklif<now = 299 ihale). (b) DT sonuçları neden Sonuçlar'da yok? →
Sonuçlar + Geçmiş sekmelerine "Sadece E-İhale"nin üstüne **İhale / Doğrudan Temin** segment
seçicisi; DT seçilince ayrı tablodan (dogrudan_temin_ilanlari) durum'a göre çekilir — böylece
ayrı "Geçmiş DT" / "DT Sonuçları" sekmesine gerek yok.
  - **Sonuçlar+DT** = durum='Sonuç Duyurusu Yayımlanmış' (2,55M); kazanan_bedel sayfa başına
    dogrudan_temin_sonuclari'den dt_no ile eşleştirilir (kazanan ADI anon'a kapalı, bedel açık;
    kapsam ~%33 — backfill sürüyor).
  - **Geçmiş+DT** = durum='Doğrudan Temin Duyurusu Yayımlanmış' (84.785, henüz sonuçlanmamış).
  - **Enum bug** (kullanıcı fark etti): `ilanlar.usul`'de 1.296 kayıtta ham i18n anahtarı
    ("TENDER_SEARCH…SEARCH_METHOD.OPEN"). Kök neden: bu kayıtlar ekap_scraper.usul_donustur()
    guard'ından ÖNCE, Angular çeviri sözlüğü uygulanmadan yakalanmış. Düzeltme: data-fix
    migration (usul_donustur ile aynı eşleme) + frontend `usulTemiz()` son savunması.
  - Canlı doğrulandı (localhost:3737, prod REST): Geçmiş 299 · Geçmiş+DT 84.785 · Sonuçlar+DT
    2,55M · guard "…OPEN"→"Açık İhale" · Aktif/DT sekmeleri sağlam · 0 konsol hatası.
→ `v1-ihaleler.html`, `backend/migration_usul_i18n_temizlik.sql`

## MADDE 24 — Kamu kuruluşu filtresi (harita) + firma-analiz "Katıldığı DT" sekmesi ✅ CANLI (RPC'ler deploy edildi)
**✅ CANLI DENETİM (1 Ağu):** `firma_kurum_mu`, `il_sektor_firmalar(_dt)` (p_kamu_dahil), `firma_dt_liste`,
`firma_dizin_dt/birlikte` (p_kamu_dahil) hepsi canlı (pg_proc doğrulandı). "deploy bekliyor" notu kalktı.
Kullanıcı 2 gözlem:
- (a) Harita firma sıralamasında DMO / cezaevi (İşyurtları) / PTT gibi **kamu kuruluşları** kazanan
  çıkıyor. Veri DOĞRU (bunlar DT'de gerçek tedarikçi) ama rakip analizinde gürültü. Karar (onaylı):
  **varsayılan gizle + toggle**. → `firma_kurum_mu(ad)` sınıflandırıcı (kurumsal sonek + DMO/PTT/İşyurtları
  ad-içi) + `il_sektor_firmalar(_dt)`'ye `p_kamu_dahil` (default false, agregasyon SONRASI süzer) +
  haritada "Kamu kuruluşlarını da göster" checkbox'ı (yalnız firma listesini etkiler).
- (b) firma-analiz'de ihale ve DT kazanımları AYRI ekranlarda olsun; tıklanınca detayına gitsin. →
  "Katıldığı İhaleler" (var) yanında **"Katıldığı Doğrudan Teminler"** sekmesi; `firma_dt_liste` RPC
  (dt_no/başlık/il/tür/tarih/bedel/idare, tr_fold eşleşme + idx_dt_sonuc_kazanan_fold) → satır
  `v1-dt-detay?dt_no=`'ya link, sayaç firma_dt_ozet.dt_sayisi'nden, sayfalama.
Canlı (localhost): DT tab/panel/pager + kamu checkbox var, 0 konsol hatası; RPC'ler deploy sonrası.
→ `v1-firma-analiz.html`, `backend/migration_firma_dt_liste_kamu.sql`
- EK (31 Tem): kamu-kuruluşu filtresi firma DİZİNİNE de taşındı (DT & İkisi modları) —
  firma_dizin_dt/birlikte'ye `p_kamu_dahil` (varsayılan gizle, filtre LIMIT'ten ÖNCE) + dizine
  "Kamu kuruluşlarını da göster" checkbox'ı (yalnız DT/İkisi'de görünür; İhale modu doğrudan
  yukleniciler sorgular, kirlilik az → dokunulmadı). → `backend/migration_firma_dizin_kamu.sql`
- NOT: DMO/cezaevi "veri hatası mı?" — HAYIR, gerçek kamu tedarikçileri (tarayıcı içerik-filtresi
  makine-doğrulamayı engelledi ama alan bilgisi kesin: DMO 4734/3-e, İşyurtları üretim-satış).

## MADDE 25 — Teklif rekabeti + "önemli veriyi saklama" (direkt göster) ✅
Kullanıcı: önemli veriyi tıklama arkasına saklama.
- ihale-detay: kısım bazlı dağılım `<details open>` (varsayılan açık).
- Teklif Rekabeti (mevcut kolonlar, migration YOK): yaklaşık maliyet + en düşük/en yüksek/ortalama
  teklif — ihale-detay "İhale Sonucu" kartında + çok kısımlıda kısım tablosunda; firma-analiz
  "Katıldığı İhaleler" kartlarında "3 teklif" yanında 📊 aralık + 🎯 yak.maliyet.
  ⚠️ EKAP kişi-bazlı teklif listesi (kim ne verdi) YAYIMLAMAZ → yalnız zarf (aralık)+katılımcı;
  tum_teklifler de yalnız bu zarfı taşıyor (kaynak kod doğrulandı).
- firma-analiz: firma açılınca ÖZET yerine "Katıldığı İhaleler" (sözleşme listesi) karşılar.
  Firmanın sözleşmeleri = Katıldığı İhaleler (ihale) + Katıldığı Doğrudan Teminler (DT) = zaten
  iki ayrı tam sekme. "Sözleşmeler" ayrı veri DEĞİL (global Sözleşmeler de ihale_sonuclari okur).
- DT-sınıflama şüphesi (belediye-şirketi küçük alımlar): yanlış-sınıflanmış DT DEĞİL — ilanlar'da
  IKN'li + yaklaşık maliyet/tenzilat taşıyorlar (ihale evreni); DT kayıtları ayrı (dt_no).
→ `v1-ihale-detay.html`, `v1-firma-analiz.html` (frontend-only, git pull)
- ⚠️ İHLAL (ayrı task açıldı): v1-sozlesmeler.html CSV export → Veri Dışa Aktarım Yasağı'na aykırı.

## MADDE 26 — QA Turu Bulguları (34) — tam site denetimi (1 Ağu, claude-in-chrome)
İki turlu tam denetim (her sayfa/sekme/filtre/analiz). Konsol hatası YOK. Önem sırası + fixability.
Durum: ✅ bitti · ⏳ sıradaki · 📋 planlandı (FE=frontend/pull · DB=migration/scraper, ayrı onay)

### 🔴 Önemli
- [26-1] ✅ FE — Sözleşmeler "Excel" export butonu → Veri Dışa Aktarım Yasağı ihlali → KALDIR. (v1-sozlesmeler.html)
- [26-2] 📋 DB — Firma cirosu trilyon anomali: YAMAN ENERJİ ₺1,111 Mr/47 söz. Bozuk sozlesme_bedeli → bul&düzelt (Bank 12,3Tn'i şişiriyor).
- [26-3] 📋 DB — İmkânsız tenzilat (tek-kısımlı): %-268,7 / %97,4 / %55,7. yaklaşık maliyet parse hatası; lot filtresi yakalamıyor.
- [26-4] ⏳ FE — Üst-bar arama "Aktif İhaleler" sekmesine düşüp aktif-dışı (2021-23) döndürüyor; İhale Tarihi "—"; başlık/kapsam çelişkili. (v1-ihaleler sorguKur/ara)
- [26-21] 📋 FE — İhale Analizi (v1-rekabet) Bütçe histogramı bozuk: maliyetli tüm kayıt ₺10-50Mn kovasında; küçükler 0. Bucketing/ölçek.
- [26-22] 📋 FE — Uyumluluk: tüm satır sabit %60 (profil tercihi boş); %75+/%85+ filtre + sıralama işlevsiz; eşleşme motoru tutarsız.
- [26-23] 📋 DB/FE — Firmalar: DMO yüklenici firma olarak listeleniyor (alıcı idare) → firma_kurum_mu ile dizinde gizle/işaretle.
- [26-24] 📋 DB/FE — DT Sonuçları ~640K satırda kazanan yok (sayaç 2,7M ama kazananlı 2,07M) → sonuç filtresi kazananlı DT'ye.

### 🟠 Orta
- [26-5] 📋 DB — DT ileri-tarih +1yıl (24 Kas 2028 / 23 Tem 2027); scraper yıl-parse; +test kaydı "denme". (bkz UV-5)
- [26-6] 📋 DB/FE — İl dup "İZMIR (1)" vs "İZMİR (1.494)" (noktasız/noktalı İ) → il normalize.
- [26-7] 📋 DB — Ad-ortası boşluk (ALTINPAR K / BET ON / STANBUL) = UV-4 ile aynı.
- [26-8] 📋 DB/FE — Sektör taksonomi sızıntısı: "Mal Alımı"/"Hizmet Alımı"/"İnşaat & Yapım" 41 kanonik dışı.
- [26-10] 📋 DB — Kararlar "Sonuç" hep "Belirtilmemiş"; Düzenleyici(0)+Mahkeme(0) kapsam ince.
- [26-25] 📋 FE — Usul normalizasyon tutarsız ("Açık" + "4734 KİK Açık İhale" + "2886 Açık Teklif" ayrı) → usulTemiz() genişlet.
- [26-26] 📋 DB — Firma Segmentleri üst özet rozetler "—/hesaplanıyor" takılı (aggregate timeout → MV).
- [26-27] 📋 DB — Segment mantığı: "Parlayan Yıldızlar"a 0-taban ilk-kez JV karışıyor (+182.126%) → İlk Kez'e ayır.
- [26-28] 📋 DB — Bağlantısız Kurumlar 17.329 (%41 DETSİS'e bağlanamamış).

### 🟡 Düşük
- [26-11] ⏳ FE — Arama/Analiz "katılabileceğiniz ihaleler" İhale Tarihi "—" → tarih fallback (26-4 ile beraber).
- [26-12] ⏳ FE — Takibim'de "Takip Ettiğim Sektörler" bölümü yok (Bana Özel 1 sayıyor).
- [26-13] ⏳ FE — İhalelerim breadcrumb "e-Satınalma" ama Kamu sidebar'ında.
- [26-14] ⏳ FE — v2 Kurumsal kapısı native prompt() → styled modal.
- [26-15] ⏳ FE — "Dökümanlar" → TDK "Dokümanlar" (sidebar + sayfa).
- [26-16] 📋 FE — Bildirim "Standart Plan/50 kredi" ama paket Pro (kozmetik/tarihsel).
- [26-17] ⏳ FE — UNGM global ilan sektör "—" (data); "Palestine, State of" TR çeviri.
- [26-29] ⏳ FE — Firmalar segment sayacı il-toplamını gösteriyor (segmenti yansıtmıyor).
- [26-30] ⏳ FE — Maliyet filtre çipi ham sayı ("50000000 – …") → ₺ format.
- [26-31] ⏳ FE — Sayı flash/stale (filtre/sekme değişince bayat toplam) → yüklenirken gizle.
- [26-32] ⏳ FE — Kurum Ağacı görünümünde başlık hâlâ "İdare Dizini".
- [26-33] ⏳ FE — Büyüme kolonu tutarsız (₺0 son-12 → "—" vs "-100%").
- [26-34] 📋 DB — Kategori misassignment (düzeltme ilanı/irtifak "İnşaat"a) = sınıflandırıcı kalitesi.

### İLERLEME (2 Ağu)
**✅ FE CANLI (a039532 + 8dfb4f1):** 26-1 (Excel kaldırıldı) · 26-4/11 (arama başlık+tarih fallback) · 26-12 (Takibim sektör) ·
26-13 (İhalelerim→E-Satınalma) · 26-14 (v2 modal) · 26-15 (Dokümanlar) · 26-17 (global ülke TR) · 26-29 (segment sayaç) ·
26-30 (maliyet çip ₺) · 26-32 (Kurum Ağacı başlık) · 26-33 (büyüme tooltip).
**✅ FE + migration GEREKLİ (aafaa1d):** 26-23 (Firmalar kamu-kurulusu gizle toggle + kurum_mu kolonu) · 26-24 (DT sonuç "kazanan işleniyor" etiketi).
**✅ MIGRATION HAZIR (çalıştırılacak — sıra aşağıda):**
- `migration_qa_26_2_cop_bedel.sql` (429eec3) → 26-2 trilyon çöp bedel.
- `migration_qa_26_data_fixes.sql` (a53f4d8) → 26-3 tenzilat · 26-21 placeholder maliyet · 26-6 İZMIR · 26-8 sektör · 26-5 DT tarih.
- `migration_qa_26_23_kurum_mu.sql` (aafaa1d) → 26-23 kurum_mu kolonu doldur.
- `migration_qa_26_27_parlayan.sql` (9a2d2c1) → 26-27 Parlayan segment 0-taban fix.
**⏸️ Bug DEĞİL / kaynak kısıtı:** 26-10 (Kurul listesinde sonuç yayımlanmıyor) · 26-28 (idare_bagsiz_mv = DETSİS eşleşmeyen; kapsam metriği, ayrı zenginleştirme) · 26-33 · 26-16 (kozmetik, tarihsel bildirim).
**✅ 26-22 CANLI (commit 6192dd6):** Uyum skoru — açık tercih yoksa `firmam_getir`+`yukleniciler.kategori`'den skorlama profili türetilir → skorlar 45/65/80'e yayıldı (sabit-60 gitti); %75+/%85+ süzgeci + sıralama anlamlı; "firma geçmişinden" notu. Firma da yoksa "firma seç" uyarısı.
**✅ 26-25 CANLI (6083cd6):** usul dağılımı normalizasyonu — "Açık" ailesi ("Açık"/"4734 KİK Açık İhale"/"2886 Açık Teklif"/"Açık İhale") tek "Açık İhale" kovasında birleşir (usulKanon+usulGrupla; v1-rekabet + kurum-analiz; yalnız gösterim, veriye dokunmaz).
**✅ 26-26 MIGRATION HAZIR (eb3de9a):** Firma Segmentleri üst özet timeout → `idx_ihale_sonuclari_sonuc_tarihi` (firma_segment_sayilari ref_tarih max()'ı indekssiz 2.7M tarıyordu). `migration_qa_26_26_sonuc_tarihi_idx.sql` (CONCURRENTLY). MADDE 12/14 timeout'unu da giderir.
**✅ 26-34 KOD+MIGRATION HAZIR (d143c10):** taşınmaz irtifak/kira/satış → İnşaat yerine Gayrimenkul. kategori_siniflandir.py ön-kontrol (gelecek) + `migration_qa_26_34_gayrimenkul.sql` (mevcut İnşaat-etiketli Kiraya Verme/Satış + irtifak/taşınmaz, tr_fold locale-güvenli).
**✅ DT ANALİZİ İL-TIMEOUT ÇÖZÜLDÜ + DOĞRULANDI (b38b76d):** İl filtresi (ör. ANKARA) >15s statement timeout veriyordu. ⚠️ TEŞHİS DÜZELTMESİ: `idx_dt_ilanlari_il` ZATEN VARDI → sorun indeks değil AGGREGATE maliyeti (`son` JOIN + medyan büyük il alt-kümesinde). ÇÖZÜM = yıl-MV deseninin aynısı: `dt_analiz_il_mv` (per-il önceden hesaplı, 81 il) + `dt_analiz_ozet` il-tek dalı MV'ye yönlendirildi. owner→postgres + `_dt_ozet_json` EXECUTE + gece REFRESH (run_scraper.sh) eklendi. **CANLI: ANKARA 237503 @ 4.2ms** (eski >15s).
**⏭️ Kalan tek ayrı pas — 26-7 (=UV-4):** İdare ad-ortası boşluk ("ALTINPAR K"/"BET ON"). ⚠️ KÖK NEDEN DÜZELTİLDİ: idare `idareAdi` JSON alanından gelir (HTML join DEĞİL); `mojibake_duzelt` boşluk eklemez → **boşluklar EKAP KAYNAK verisinde** (sabit-genişlik wrap). Fix = idare adı normalizasyonu ama idare = kurum-analiz/filtre/DETSİS/takip_idareler JOIN ANAHTARI → **yüksek blast-radius**, kör boşluk-silme meşru boşlukları bozar. GÜVENLİ pas gerekir: (a) teşhis (kaç bozuk + kaçının temiz varyantı var), (b) fuzzy dedup temiz varyanta VEYA elle sözlük, (c) ilanlar+dt+idare_ozet_mv+takip_idareler tutarlı güncelle + MV refresh. Aceleye getirilmez.
  → **SCRIPT HAZIR (b38b76d):** `backend/idare_ad_temizle.py` — `ai_ortak` üzerinden (DeepSeek birincil, Gemini yedek; Gemini KEY sonra aktifleşecek) heuristik aday + AI doğrulama + dry-run CSV → `--apply`. ⏭️ **SIRADAKİ ADIM (bir dahaki oturum):** `cd /opt/ihale-platform/backend && ./venv/bin/python idare_ad_temizle.py --dry-run --limit 80` → `logs/idare_remap_oneri.csv`'yi Claude ile incele → `--apply --min-guven 0.85` → MV refresh. (NOT: kullanıcı `--apply`'ı erken denedi, script doğru şekilde "önce dry-run" diye reddetti — CSV yok.)
**⏭️ Opsiyonel iyileştirme:** 26-22+ uyum.js kategori-kelime eşleşmesi kaba (çok kategori → çoğu ihale %80); firma kategori KONSANTRASYONUYLA ağırlıklandırma (MADDE 6 v4 deseni; skorlama-modeli değişikliği, bug değil).

# UZUN VADE (ayrı seri — "uzun vade" dendiğinde bu liste çıkarılır)

## UV-1 — AI Teklif/Fiyat Asistanı revizyonu: teknik şartname okuması 📋
**Sorun (canlı örnek):** Asistan şöyle diyor →
> "İl bazında tenzilat bilginiz bulunmadığı için yalnızca genel ortalamayı (%11,6) referans
> alabiliriz. Yaklaşık maliyet bilgisi de olmadığından somut bir teklif bandı (₺ alt–₺ üst)
> veremiyorum. Katılımcı sayısı verisi de olmadığından rekabet yoğunluğunu değerlendiremiyorum."

**Kök neden** (kaynak `backend/teklif_ai.py` + `analiz_pivot`): öneri yalnız yapılandırılmış
alanlara dayanıyor — (a) ihalede `yaklasik_maliyet` boşsa ₺ band YOK, (b) o il için geçmiş
tenzilat kırılımı yoksa Türkiye geneli %11,6'ya düşüyor, (c) katılımcı sayısı yoksa rekabet
yorumu yok. Yani "geçmiş ihale bulamadı" = o ihaleyle EŞLEŞEN kırılım seyrek.

**İyileştirme fikri (kullanıcı):** AI **teknik şartnameyi/ilan dokümanını okusun** →
  - Yaklaşık maliyet boşsa şartnameden **kapsam/kalem çıkarımı** ile tahmini büyüklük üret,
  - Daha isabetli **benzer geçmiş ihale eşleşmesi** (başlık+şartname konu vektörü),
  - Böylece genel %11,6 yerine **ihaleye özgü** band + daha doğru sonuç.
**Kapsam:** doküman erişimi (EKAP belge indirme — hafıza `ekap-belge-indirme-captcha`),
PDF/şartname parse, konu çıkarımı, `analiz_pivot` eşleşmesini şartname sinyaliyle besleme.
→ `backend/teklif_ai.py`, `backend/api.py`, doküman pipeline

## UV-2 — POS ekleme 📋
Ödeme POS entegrasyonu eklenecek (detay kullanıcıdan alınacak).

## UV-3 — Dış Ticaret Analizi altyapısı: yeni algoritma 📋
Dış Ticaret Analizi altyapısı DEĞİŞECEK — farklı bir algoritma kurulması gerekiyor (detay
kullanıcıdan alınacak). Mevcut: Comtrade/WITS tabanlı ticaret katmanı (hafıza `ticaret-katmani-kaynak`,
`ticaret_backfill.py` + `ticaret_yillar/harita/ulke/liste`). Yeni algoritma tanımı netleşecek.
→ `backend/ticaret_backfill.py`, `v1-dis-ticaret.html` / `ticaret-analiz.html`

## UV-4 — İdare/kurum adlarında kelime-ortası boşluk (scraper metin çıkarımı) 📋
**Sorun (canlı):** idare adları kelime ortasında boşlukla bozuk geliyor:
"ANFA ANKARA ALTINPAR K İŞL.LTD.ŞTİ." (→ ALTINPARK), "ANFA GÜVENLİK HİZMET LERİ VE SİSTEMLE LTD.ŞTİ."
(→ HİZMETLERİ VE SİSTEMLERİ). Bazı kurumlarda var. Ayrıca aynı idare hem bozuk hem DOĞRU adla ayrı
satır olarak görünüyor (dedup sorunu) — ör. "…ALTINPAR K İŞL.LTD.ŞTİ." + "…ALTINPARK İŞLETMELERİ
LİMİTED ŞİRKETİ MÜDÜRLÜĞÜ" ikisi de listede.
**Kök neden (hipotez):** EKAP'ta idare adı satır kaydırmasıyla birden çok metin düğümüne/hücreye
bölünmüş; scraper düğümleri boşlukla (join ' ') birleştirince WRAP noktalarında kelime ortasına
boşluk giriyor.
**Çözüm planı:** (a) `ekap_scraper.py` idare çıkarımını bul → adı tek düğümden al / normalize et
(çoklu boşluk → tek, ama kelime-ortası wrap boşluğunu ayırt etmek zor). (b) Mevcut bozuk kayıtlar:
DÜZ "boşlukları sil" YAPILAMAZ (meşru boşluklar var) → doğru varyantla fuzzy eşleştirip dedup
(aynı idarenin doğru adı çoğu zaman zaten mevcut) VEYA hedefli düzeltme sözlüğü. (c) `idare_ozet_mv`
+ `ilanlar.idare` + `dogrudan_temin_ilanlari.idare` temizliği; DETSİS eşlemesi doğru ada bağlanmalı.
→ `backend/ekap_scraper.py` (idare alanı), `ilanlar.idare`/`dogrudan_temin_ilanlari.idare`, `idare_ozet_mv`, dedup
## UV-5 — Tarih doğrulama: EKAP tarihleri baz alınmalı (saat sorunu) 📋
Bogus SAAT (ör. hep "03:00") frontend listelerinden KALDIRILDI (v1-ihaleler satir()); scraper'ın
yazdığı saat gerçeği yansıtmıyordu. KALAN İŞ: TARİH'lerin kendisi de EKAP ile teyit edilmeli —
scraper'ın son_teklif_tarihi / tarih / sonuc_tarihi alanlarını EKAP kaynağıyla karşılaştır, sapma
varsa scraper tarih ayrıştırmasını düzelt (muhtemelen timezone/parse). Saat tamamen anlamsızsa
DB'de de saat kısmını sıfırlamak/temizlemek düşünülebilir.
→ `backend/ekap_scraper.py`, `backend/ekap_dogrudan_temin_scraper.py` (tarih parse), ilanlar/dogrudan_temin tarih alanları

---

### Sıradaki (kullanıcı söyleyecek)
- [ ] …
