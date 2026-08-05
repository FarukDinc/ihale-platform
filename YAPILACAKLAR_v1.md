# YAPILACAKLAR — V1 Versiyon

> Tek iş kuyruğu (v1). Yeni talep gelince ÖNCE buraya yaz, sonra uygula. Sıradaki işi bu dosyadan seç.
> Ana dosya: `v1-benim-sayfam.html` (Bana Özel / Merhaba dashboard'u). Parça parça ilerlenecek.

Durum: ✅ bitti · ⏳ sıradaki · 📋 planlandı

---

## AI YORUM MODÜLÜ (premium) ✅ ÜÇ VARLIK DA CANLI
Grounded+cache'li değerlendirme. **✅ KURUM:** `ai_yorum.py` (kurum_ozet+tekrar-kazananlar→DeepSeek),
`/ai/kurum-yorum`, v1-kurum-analiz butonu, cache `ai_yorumlari` (veri-hash, yaş<7g hızlı 0,1s).
**✅ FİRMA (zenginleştirildi):** `firma_ai_yorum.py`+`/ai/firma-yorum`; grounding'e **DT kazanımları
(firma_dt_ozet) + segment (parlayan/sönen) + büyüme + ortak girişim** eklendi, max_tokens 1200.
**✅ İHALE:** UV-1 teklif-strateji/sartname. Tutarlılık = grounding + cache. Bkz. [[ai-yorum-modulu]].

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
- [26-2] ✅ DB — Firma cirosu trilyon anomali ÇÖZÜLDÜ/DOĞRULANDI (3 Ağu): artık YOK. yukleniciler max ciro 187 Mr (REC İnşaat, gerçek), 1 Tn üstü 0 satır; ihale_sonuclari.sozlesme_bedeli max 83 Mr (yaklaşık maliyetle uyumlu); YAMAN ENERJİ 172 Mn/47 söz (makul); "BANK 12,3Tn" 0 satır. Gece ciro-recompute (temiz sonuç tablosu) + tenzilat/lot fix düzeltmiş. (Kategori Toplam Tutar + firma ciro KPI de bozuk-veri-şişmesi taşımıyor — teyit.)
- [26-3] ✅ DB/FE — İmkânsız tenzilat ÇÖZÜLDÜ (3 Ağu, kullanıcı kararı: "sadece fiziksel imkânsız" + "ikisi de"). Eşik: bedel/maliyet<100₺ VEYA tenzilat≥%95 VEYA ≤-%100 → NULL; orta değerler (-%55, %70) KORUNUR. 5 katman: (1) ekap_sonuc_backfill.py guard, (2) ekap_sonuc_scraper.py guard (gece kalıcı), (3) migration_26_3_tenzilat_fiziksel.sql → **191.471 satır** tenzilat_yuzde+kazanan_teklif_farki_yuzde NULL, (4) v1-ihale-detay taban+band guard, (5) v1-firma-analiz merkezi tenzilatDegeri guard. Doğrulama: lot_sayisi=1 kalan uç=0/çöp-taban=0; dolu 1,42M (min -99,995 / max 94,995); -53% aşım korundu. Not: analiz_pivot/sonuc_ozet_mv ortalamaları gece refresh'te temiz tenzilatı alır.
- [26-4] ✅ FE — ÇÖZÜLDÜ (3 Ağu): sorguKur 'aktif' dalı kelime aramasında aktif-durum filtresini atlıyordu (`!val('f-kelime')`) → sekme "Aktif" derken 2021-23 aktif-dışı dönüyordu. Artık aktif filtre kelime aramasında UYGULANIR; yalnız idare drill-down + İKN/ekap_id'de atlanır. Başlık da "Aktif İhaleler" (İKN'de "tüm zamanlar") + kapsam şeridi. Misafirde doğrulandı: "Son 1 gün" aktif sonuç, başlık tutarlı, 0 console hatası.
- [26-21] ✅ FE — BUG DEĞİL (3 Ağu triyaj): histogram kümelenmesi `yaklasik_maliyet_min=10785492/max=43142132` = KİK band tahmini (itiraz_bedelinden, 4 sabit çift) — bellek [[aktif-ihale-maliyet-band]] "çöp sanıp silme = 26-21 dersi". Gerçek maliyet yalnız ihale_sonuclari'nda. (İsteğe bağlı FE iyileştirme: bandı "KİK tahmini" diye etiketle; migration_qa_26'nın bunu null'laması yanlış teşhisti, uygulanmamalı.)
- [26-22] ✅ FE — ÇÖZÜLDÜ (3 Ağu): (a) ANA fix zaten canlıydı — `firmadanProfilTuret()` tercih yoksa seçili firmanın yukleniciler.kategori geçmişinden skor profili türetir → 45/65/80 yayılır, flat-60 kalkar (v1-uyumluluk 418/768). (b) BUGÜN: uyum.js:63 profilsizken `Math.random()` her render farklı skor + kararsız sıralama veriyordu ("eşleşme motoru tutarsız") → ilan kimliğinden DETERMİNİSTİK 55-74 (aynı ilan hep aynı). uyum.js ?v=2 (5 sayfada bump). Canlı doğrulandı: aynı ilan→aynı skor, farklı ilan→farklı, 0 console hatası. NOT (küçük): firma-türetmede max ~80 → %85+ süzgeci ancak açık il/tür/kelime tercihiyle dolar (isteğe bağlı ileride).
- [26-23] ✅ DB/FE — ÇÖZÜLMÜŞ (3 Ağu triyaj): DEVLET MALZEME OFİSİ GENEL MÜDÜRLÜĞÜ kurum_mu=true (İhale modunda gizli); özel "DMO Grup Ltd" firmaları doğru false. Gece cron senkron (run_scraper satır 54).
- [26-24] ✅ DB/FE — ÇÖZÜLMÜŞ (3 Ağu triyaj): DT sonuçlarında kazanansız 0 (2,87M'nin tamamı dolu). Gece DT-kazanan backfill'i bitirmiş.

### 🟠 Orta
- [26-5] ✅ DB — ÇÖZÜLMÜŞ (3 Ağu triyaj): DT >400 gün ileri **0**, >200 gün **0**. migration_qa_26 (+1yıl geri al / aşırı-ileri NULL) uygulanmış.
- [26-6] ✅ DB/FE — ÇÖZÜLMÜŞ (3 Ağu triyaj): İZMIR (noktasız) 0 satır. (migration_qa_26 uygulanmış.)
- [26-7] 📋 DB — Ad-ortası boşluk (ALTINPAR K / BET ON / STANBUL) = UV-4 ile aynı.
- [26-8] ✅ DB/FE — ÇÖZÜLDÜ (3 Ağu): kök neden ekap_scraper.py fallback'i "yapım"→'İnşaat & Yapım' (CPV-45 dahil) NON-KANONİK yazıyordu, jenerik kovada olmadığı için gece AI reclassify de etmiyordu → KALICI. Scraper kanonik 'İnşaat - Altyapı - Üstyapı - Yapım' yazacak (2 satır); 28 kalıntı remap edildi (0 kaldı). 'Mal/Hizmet Alımı' jenerik kovada → gece AI reclassify ediyor (geçici, dokunulmadı).
- [26-10] ⏳ SCRAPER PROJESİ (ertelendi, düşük değer) — kik_kararlar (827) sonuç/tam metin HİÇ scrape edilmemiş. Kök: liste API sonuç dönmüyor; kik_backfill.py yazarı belgelemiş (satır 74/75/288) → AYRI "detay" çağrısı gerek. Anahtar HAZIR: gundemMaddesiId 97/97 dolu. NEXT-STEP: KİK detay endpoint keşfi (gundemMaddesiId + crypto headers) → sonuç (İtirazın Reddi/Düzeltici İşlem/İptal) + düzenleyici/mahkeme türleri. Odaklı iş, maraton kuyruğunda değil.
- [26-25] ✅ FE — ÇÖZÜLDÜ (3 Ağu): v1-ihaleler `usulTemiz` genişletildi — Açık/Açık İhale/4734 KİK → "Açık İhale"; İstisna+"4734 / 3-x"+Kapsam Dışı → "İstisna / Kapsam Dışı"; 2886/Pazarlık/Belli kanonik (TR İ/ı için toUpperCase KULLANILMADI, ham metinde arandı). AYRICA İstisna FİLTRESİ `.or('%İstisna%,%4734 / 3-%')` ile 90K "4734 / 3-x" satırını kapsar (eskiden Diğer'e düşüyordu); USUL_HARIC'e eklendi. Canlı doğrulandı (REST .or çalışıyor, display kanonik, 0 hata).
- [26-26] ✅ DB — ÇÖZÜLDÜ (3 Ağu): asıl "takılma" pre-seg_* canlı-aggregate'tan; seg_* kolonlarıyla zaten timeout altındaydı (970ms). Bugün firma_segment_sayilari() partial-indeksli alt-sorgulara çevrildi (970→600ms, darboğaz max(segment_guncellendi) tam-tarama→seg_parlayan alt-kümesi); migration_qa_26_26_segment_ozet.sql. Büyümeyle timeout riski kalktı.
- [26-27] ✅ DB — ÇÖZÜLMÜŞ (3 Ağu doğrulandı): canlı seg_parlayan `önceki12>0 AND son12≥2×önceki` (OR "ilk kez büyük" dalı kaldırılmış) → 0-taban Parlayan **0 firma**. migration_qa_26_27_parlayan.sql uygulanmış + gece refresh koşmuş. Bugün: baz migration_firma_segmentleri.sql'i de fix'le senkronladım (rebuild regresyonu önlendi).
- [26-28] ✅ DB — ÇÖZÜLMÜŞ (3 Ağu triyaj): idare_bagsiz_mv **144** (17.329 değil). Orphan-kurum greft yapılmış (bellek: orphan-kurum-greft, 17.329→99 + isim/AI dağıtım).

### 🟡 Düşük
- [26-11] ✅ DB — ÇÖZÜLDÜ (3 Ağu): eşleşme motoru (firma_icin_acik_ihaleler v4) WHERE'i `son_teklif_tarihi IS NULL OR >= now()` ile null-deadline aktif ihaleleri (545/6224 ~%9) döndürüp "İhale Tarihi —" gösteriyordu. Fix: `AND son_teklif_tarihi >= now()` (null-deadline dışla — deadline'sız ihaleye teklif verilemez; ilan_tarihi'ni "İhale Tarihi" göstermek yanıltıcı olurdu). Canlıda WHERE'de IS NULL kalmadı (doğrulandı).
- [26-12] ✅ FE — ÇÖZÜLDÜ (3 Ağu): "Takip Ettiğim Sektörler" bölümü ZATEN vardı (v1-takipte 266-273, takip_sektorler'den) ama sektör "Takibi Bırak" düğmesi ÇALIŞMIYORDU — tkTikla delegesi v1-sektor-liste'ye bağlı değildi. Tek satır dinleyici eklendi.
- [26-13] ✅ FE — bug DEĞİL (3 Ağu): breadcrumb "e-Satınalma > İhalelerim" DOĞRU — sayfa E-Satınalma dünyasında (WS_OF['ihalelerim']='esatinalma'), Kamu'da değil. Rapor önermesi hatalı. Yalnız kozmetik büyük harf hizalandı (e→E).
- [26-14] ✅ FE — ÇÖZÜLMÜŞ (3 Ağu doğrulandı): v2 Kurumsal kapısı ZATEN stilize modal (js/v1-kabuk.js v2SifreModal:310-338), native prompt YOK. Rapor stale.
- [26-15] ✅ FE — ÇÖZÜLDÜ (3 Ağu): "Döküman"→TDK "Doküman" global (27 html + js/kenar-menu.js sidebar); kenar-menu.js ?v=10 bump. Canlı doğrulandı (düzgün UTF-8, mojibake 0, eski 0). sed byte-güvenli.
- [26-16] ✅ FE/Edge — ÇÖZÜLDÜ+DEPLOY (3 Ağu): odeme-baslat Edge function (icerik+aciklama) + payment.py ad "Standart Plan"→"Pro Plan". Edge volume'a (/opt/supabase/docker/volumes/functions) kopyalandı (drift yoktu, yalnız 2 string), edge-runtime istek-başı okur→restart yok/payment kesintisiz. Doğrulandı: fonksiyon HTTP 401 (düzgün yüklüyor), volume "Standart Plan" 0.
- [26-17] ⏳ FE — UNGM global ilan sektör "—" (data); "Palestine, State of" TR çeviri.
- [26-29] ⏳ FE — Firmalar segment sayacı il-toplamını gösteriyor (segmenti yansıtmıyor).
- [26-30] ⏳ FE — Maliyet filtre çipi ham sayı ("50000000 – …") → ₺ format.
- [26-31] ✅ FE (3 Ağu) — Sayı flash/stale: filtre/sekme/yıl/sektör değişince KPI+sayaç fetch'ten ÖNCE '…'
  yapılır (v1-firma-segmentleri deseni). 7 sayfa: dis-ticaret · rekabet · dt-analiz · harita · global · esatinalma · firmalar.
  Explore taramasıyla haritalandı; doğru-yapılmış referanslar: firma-segmentleri, bank, analiz, uyumluluk.
- [26-32] ⏳ FE — Kurum Ağacı görünümünde başlık hâlâ "İdare Dizini".
- [26-33] ⏳ FE — Büyüme kolonu tutarsız (₺0 son-12 → "—" vs "-100%").
- [26-34] 📋 DB — Kategori misassignment (düzeltme ilanı/irtifak "İnşaat"a) = sınıflandırıcı kalitesi.

### İLERLEME (2 Ağu)
**✅ FE CANLI (a039532 + 8dfb4f1):** 26-1 (Excel kaldırıldı) · 26-4/11 (arama başlık+tarih fallback) · 26-12 (Takibim sektör) ·
26-13 (İhalelerim→E-Satınalma) · 26-14 (v2 modal) · 26-15 (Dokümanlar) · 26-17 (global ülke TR) · 26-29 (segment sayaç) ·
26-30 (maliyet çip ₺) · 26-32 (Kurum Ağacı başlık) · 26-33 (büyüme tooltip).
**✅ FE + migration GEREKLİ (aafaa1d):** 26-23 (Firmalar kamu-kurulusu gizle toggle + kurum_mu kolonu) · 26-24 (DT sonuç "kazanan işleniyor" etiketi).
**✅ MIGRATION UYGULANDI (3 Ağu — canlı DB'de doğrulandı, hepsi live):**
- `migration_qa_26_2_cop_bedel.sql` (429eec3) → 26-2 trilyon çöp bedel ✅ (≥900Mr tekil kayıt=0).
- `migration_qa_26_data_fixes.sql` (a53f4d8) → 26-3 tenzilat ✅ · 26-6 İZMIR ✅ (0) · 26-8 sektör ✅ (0) · 26-5 DT tarih ✅.
  ⚠️ **26-21 (placeholder maliyet null'lama) UYGULANMADI ve UYGULANMAMALI** — [[aktif-ihale-maliyet-band]] dersi:
  min=10.785.492 / max=43.142.132 (max=min×4) bir **KİK BAND TAHMİNİ**, çöp DEĞİL; gece scraper'ı sürekli üretir
  (3 Ağu: 2.940 satır). Null'lamak gerçek tahmini siler + ertesi gece geri gelir → hem yanlış hem futile.
- `migration_qa_26_23_kurum_mu.sql` (aafaa1d) → 26-23 kurum_mu kolonu ✅ (kolon var).
- `migration_qa_26_27_parlayan.sql` (9a2d2c1) → 26-27 Parlayan segment fix ✅ (yeni mantık canlı).
- `migration_qa_26_26_sonuc_tarihi_idx.sql` ✅ (indeks var) · `migration_qa_26_34_gayrimenkul.sql` ✅ (0 bekleyen) · `migration_firma_kurum_mu_v3.sql` ✅ (aselsan canlı).
**⏸️ Bug DEĞİL / kaynak kısıtı:** 26-10 (Kurul listesinde sonuç yayımlanmıyor) · 26-28 (idare_bagsiz_mv = DETSİS eşleşmeyen; kapsam metriği, ayrı zenginleştirme) · 26-33 · 26-16 (kozmetik, tarihsel bildirim).
**✅ 26-22 CANLI (commit 6192dd6):** Uyum skoru — açık tercih yoksa `firmam_getir`+`yukleniciler.kategori`'den skorlama profili türetilir → skorlar 45/65/80'e yayıldı (sabit-60 gitti); %75+/%85+ süzgeci + sıralama anlamlı; "firma geçmişinden" notu. Firma da yoksa "firma seç" uyarısı.
**✅ 26-25 CANLI (6083cd6):** usul dağılımı normalizasyonu — "Açık" ailesi ("Açık"/"4734 KİK Açık İhale"/"2886 Açık Teklif"/"Açık İhale") tek "Açık İhale" kovasında birleşir (usulKanon+usulGrupla; v1-rekabet + kurum-analiz; yalnız gösterim, veriye dokunmaz).
**✅ 26-26 MIGRATION HAZIR (eb3de9a):** Firma Segmentleri üst özet timeout → `idx_ihale_sonuclari_sonuc_tarihi` (firma_segment_sayilari ref_tarih max()'ı indekssiz 2.7M tarıyordu). `migration_qa_26_26_sonuc_tarihi_idx.sql` (CONCURRENTLY). MADDE 12/14 timeout'unu da giderir.
**✅ 26-34 KOD+MIGRATION HAZIR (d143c10):** taşınmaz irtifak/kira/satış → İnşaat yerine Gayrimenkul. kategori_siniflandir.py ön-kontrol (gelecek) + `migration_qa_26_34_gayrimenkul.sql` (mevcut İnşaat-etiketli Kiraya Verme/Satış + irtifak/taşınmaz, tr_fold locale-güvenli).
**✅ DT ANALİZİ İL-TIMEOUT ÇÖZÜLDÜ + DOĞRULANDI (b38b76d):** İl filtresi (ör. ANKARA) >15s statement timeout veriyordu. ⚠️ TEŞHİS DÜZELTMESİ: `idx_dt_ilanlari_il` ZATEN VARDI → sorun indeks değil AGGREGATE maliyeti (`son` JOIN + medyan büyük il alt-kümesinde). ÇÖZÜM = yıl-MV deseninin aynısı: `dt_analiz_il_mv` (per-il önceden hesaplı, 81 il) + `dt_analiz_ozet` il-tek dalı MV'ye yönlendirildi. owner→postgres + `_dt_ozet_json` EXECUTE + gece REFRESH (run_scraper.sh) eklendi. **CANLI: ANKARA 237503 @ 4.2ms** (eski >15s).
**✅ 26-7 (=UV-4) KAPANDI — TOP-1000 (2 Ağu):** İdare ad-ortası boşluk ("ALTINPAR K"→ALTINPARK, "BET ON"→BETON, "O TEL"→OTEL). Çözüm `backend/idare_ad_temizle.py`: heuristik aday (dupe-grup + wrap imzası, meşru "E Tipi/1 Nolu/A.Ş." korunur) → **Gemini `gemini-3.1-flash-lite` doğrulama** (DeepSeek'ten iyi: MSB "BLG→BİLGİ" tuzağına düşmedi, OTEL'i düzeltti) → dry-run CSV → **SQL remap**. **CANLI: 137/138 wrap adı düzeltildi (`orijinal_hala_var=0`); + DMO daireleri Roman→Arabik normalize (24.172 satır: I/II/III/IV/V Nolu → 1/2/3/4/5); MV+idare_tur tazelendi.** ⚠️ TUZAKLAR (hepsi giderildi): (a) DeepSeek 40'lık öbekte JSON kırpıyordu → öbek 20 + 8000 token; (b) takip_idareler service_role UPDATE grant'ı yoktu → `migration_qa_takip_idareler_grant.sql`; (c) **REST `--apply` bazı idare adlarında SESSİZCE 0 satır güncelledi** (PostgREST `eq.` transport tuzağı; örnek-doğrulama yanılttı, agregat `orijinal_hala_var` gerçeği verdi) → script'e **`--sql` modu** eklendi (bayt-birebir `UPDATE...FROM VALUES`, psql'e pipe; REST apply artık uyarı basıyor). `idare_ozet_mv` YALNIZ `ilanlar`'dan (Kurumlar için ilanlar remap + refresh yeter; DT adları `dt_idare_ozet_mv`←`dogrudan_temin_ilanlari` ayrı). ⏭️ **OPSİYONEL uzun kuyruk:** kalan ~39K küçük idare için tam-katalog turu (`--dry-run --limit 0` → `--sql | psql`); değer düşük, acele değil; dry-run CSV'yi yalnız sonda yazıyor → uzun run'da resumable yapılmalı.
**⏭️ Opsiyonel iyileştirme:** 26-22+ uyum.js kategori-kelime eşleşmesi kaba (çok kategori → çoğu ihale %80); firma kategori KONSANTRASYONUYLA ağırlıklandırma (MADDE 6 v4 deseni; skorlama-modeli değişikliği, bug değil).

## MADDE 27 — Firma & Harita QA turu (2 Ağu) ✅ 7/7 CANLI
Kullanıcı tarama sırasında 7 bulgu verdi; hepsi commit+push (eab36a7, 892ad14, e346642, 0a9c436):
1. **Kurum-analiz kazanan firma linkleri** — İhale Listesi (ihale+DT) + Sonuçlar satırlarında firma adı `v1-firma-analiz?firma=` linki (firmaLink helper).
2. **DT firmaları Firmalar'da çıksın** (BELİZ GRUP) — `yukleniciler` YALNIZ ihale kazananı; firma araması artık `firma_dizin_dt` ile birleşiyor (v1-firma-analiz + v1-firmalar fallback); DT-only firma "⚡ DT kazananı" rozeti + **ad ile detay** (`firmaDtOnlyAc` → dtBlokYukle + DT sekmesi).
3. **Kabuk arama tipi kalıcı** — `#v1-kapsam` her sayfada 'ihale'ye düşüyordu → URL/sayfadan türet + sessionStorage (js/v1-kabuk.js, ?v=26).
4. **Firma-analiz sekme sırası** — "İhaleler Genel Bakış" öne (DT ikinci).
5. **Harita panel "Devamını gör"** — il paneli 8→50 firma (firma-analiz dizin harita).
6. **Kamu toggle tutarsızlığı** — bug değil, sınıflandırıcı kapsamı: `firma_kurum_mu` v3'e belediye şirketleri (BELKA/ANFA/İSTON…) + savunma/SOE A.Ş. (ASELSAN/TÜRKSAT/TÜBİTAK…) eklendi, TÜPRAŞ hariç (özel). **⏳ migration_firma_kurum_mu_v3.sql çalıştırılacak.**
7. **Filtreyle geri dön** — harita dizin'de firmaya tıklamadan önce durum URL'e (haritaURLYaz/replaceState); tarayıcı "geri" filtreli haritaya döner (rotala g=harita → haritaGeriYukle).
⚠️ **PAGE-ID DERSİ:** Ekranlardaki "Firma Yoğunluğu" haritası + kamu toggle + Liste/Harita + KPI = **v1-firma-analiz.html DİZİN görünümü**, v1-harita.html DEĞİL (o ayrı, sidebar "Harita"). Firmalar altında olduğu için sidebar "Firmalar" yanar.

# UZUN VADE (ayrı seri — "uzun vade" dendiğinde bu liste çıkarılır)

## UV-1 — AI Teklif/Fiyat Asistanı: teknik şartname okuması ✅ FAZ 1 + FAZ 2 CANLI (backend)
**✅ FAZ 2 (1 Ağu — tam şartname indirme):** 406 **Playwright** ile aşıldı (chromium VDS'te kurulu).
`backend/sartname_indir.py` (indir+ZIP/PDF/docx parse) + `/ai/sartname-analiz` endpoint (KREDİLİ premium:
cache 1 / fresh 3 kredi; ilanlar.sartname_metni cache). Zengin doküman seti iniyor (teknik şartname+birim
fiyat cetveli+poz), AI okuyup **somut ₺ band** veriyor (örn Mustafakemalpaşa %18,09→34,5-36,2M). Endpoint
401-auth kayıtlı, zincir uçtan uca doğrulandı. **UI:** teklif-olustur.html'e "📄 Teknik Şartnameyi İndir &
Analiz Et (3 Kredi)" butonu + aiSartnameAnaliz() (canlı doğrulandı, 0 konsol hatası). **FAZ 2 TAM BİTTİ.**
Bkz. [[ekap-belge-indirme-captcha]], [[ai-teklif-strateji-deepseek]].
**✅ FAZ 1 (1 Ağu):** Teknik şartname İNDİRME EKAP'ta sertleşti (spike: CAPTCHA çözülüyor ama 3. adım
406 — Playwright gerekir = Faz 2, ertelendi; bkz. [[ekap-belge-indirme-captcha]]). PIVOT: zaten çekili
`ilan_metni` (%75,8 aktif kapsam, ~4K char) AI'a okutuldu → `teklif_ai.sartname_oku` (DeepSeek, JSON:
kapsam/is_turu/kalemler/konu_kelimeler/ölçek/maliyet_ipucu). `/ai/teklif-strateji` bunu çekip stratejiye
besliyor; guard gevşetildi → tenzilat/maliyet YOKken bile kapsam-temelli band çıkar (kullanıcının asıl
derdi). Kıyas: DeepSeek = Gemini-3.1-flash-lite kalite eşit + 1,5-2× hızlı → DeepSeek. API restart'landı,
uçtan uca doğrulandı. → `backend/teklif_ai.py`, `backend/api.py`. Bkz. [[ai-teklif-strateji-deepseek]].
**✅ FAZ 1.5 (konuya-özgü tenzilat):** `konu_tenzilat(kelime)` RPC (`migration_konu_tenzilat.sql`) —
sartname konu kelimesiyle sonuçlanmış benzer ihalelerin GERÇEK tenzilatı (il/genel'den isabetli;
tenzilat_yuzde precomputed + trgm + ORDER'sız LIMIT bound). /ai/teklif-strateji jenerik-eleyip
`kirilimlar['konu']` besliyor, prompt önceliği konu>il>genel. Doğrulandı (TÜRASAŞ→%10,77). CANLI.
**FAZ 2 (ertelendi):** tam teknik şartname indirme (Playwright/headless + CAPTCHA, 406 aşımı) → 47-kalem
gibi detay birim fiyat cetveli. Faz 1 yetersiz kalırsa.
--- ESKİ PLAN (referans): ---
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

## UV-4 — İdare/kurum adlarında kelime-ortası boşluk (scraper metin çıkarımı) 🟡 TOP-1000 KAPANDI, UZUN KUYRUK BEKLİYOR
**✅ TOP-1000 YAPILDI (2 Ağu, bkz MADDE 26-7):** en yüksek-hacimli ~138 idare düzeltildi (137 wrap + DMO Roman→Arabik 24.172 satır), `orijinal_hala_var=0`, MV tazelendi. Araç: `backend/idare_ad_temizle.py` (heuristik aday → Gemini `gemini-3.1-flash-lite` doğrulama → `--dry-run` CSV → **`--sql | psql`** bayt-birebir remap). REST `--apply` sessiz-kısmi-fail ettiği için `--sql` modu eklendi ([[toplu-remap-sql-postgrest-sessiz]]).
**⏭️ UZUN KUYRUK (buraya dönünce TEK TEK inilecek — kullanıcı isteği 2 Ağu):** kalan ~39K küçük idare (çoğu 1-2 ihaleli) için tam-katalog turu. ÖNCE yapılacak: `--dry-run`'ı resumable/checkpoint'li yap (şu an CSV'yi yalnız sonda yazıyor → `--limit 0` ~40 dk run ortada çökerse kayıp; öbek-öbek append + kaldığı yerden devam). Sonra `--dry-run --limit 0` (Gemini) → CSV incele → `--sql | psql` → MV refresh + `idare_tur_tazele()`. Değer düşük ama kapsam için; aceleye gerek yok.
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
## UV-5 — Tarih doğrulama: EKAP tarihleri baz alınmalı (saat sorunu) ✅ TEŞHİS TAMAM (3 Ağu) — TAM-FIX RİSKLİ, YAPILMADI
**VERDİCT (3 Ağu, [[tarih-tz-konvansiyonlari]]):** Tarih alanları TUTARSIZ 2 tz konvansiyonu kullanıyor (DB session UTC):
`son_teklif_tarihi` naive (10:30 TR→10:30 UTC; UTC günü DOĞRU, saat +3h ama frontend gizler), `ilan_tarihi`/`dt.tarih`
tarih-only 00:00 UTC (gün doğru), `sonuc_tarihi` **tz-aware TR-gece-yarısı** (00:00 TR=21:00 UTC, DST doğru; frontend
JS→TR doğru ama server `::date`/`EXTRACT YEAR` UTC → yıl/gün sınırında 1 kayar, ör. 1 Ocak sonucu prev-yıl). **Kullanıcıya
görünen tarihler pratikte DOĞRU.** Tam düzeltme = milyonlarca satır migrate + tüm okuma-sitesi denetimi → riskli, görünür
fayda düşük → YAPILMADI. Tek edge-bug: sonuc_tarihi UTC yıl çıkarımı; istenirse `EXTRACT(YEAR FROM (sonuc_tarihi AT TIME
ZONE 'Europe/Istanbul'))`. `tarih_iso`'yu TR-aware yapmak eski naive veriyle tutarsızlık yaratır → migrate etmeden yapma.
--- (özgün not aşağıda) ---
Bogus SAAT (ör. hep "03:00") frontend listelerinden KALDIRILDI (v1-ihaleler satir()); scraper'ın
yazdığı saat gerçeği yansıtmıyordu. KALAN İŞ: TARİH'lerin kendisi de EKAP ile teyit edilmeli —
scraper'ın son_teklif_tarihi / tarih / sonuc_tarihi alanlarını EKAP kaynağıyla karşılaştır, sapma
varsa scraper tarih ayrıştırmasını düzelt (muhtemelen timezone/parse). Saat tamamen anlamsızsa
DB'de de saat kısmını sıfırlamak/temizlemek düşünülebilir.
→ `backend/ekap_scraper.py`, `backend/ekap_dogrudan_temin_scraper.py` (tarih parse), ilanlar/dogrudan_temin tarih alanları

## UV-6 — Kurumlar + Firmalar yapısını rakip (ihalepro) örnek alarak yeniden tasarla 📋
**İstek (kullanıcı, 3 Ağu):** Rakip **`app.ihalepro.com/ihalepro/kurumlar`** KURUM AĞACINI çok iyi
kurmuş → örnek alınacak. Ayrıca rakibin **Firmalar + Kurumlar** sayfa/veri yapısı da incelenip bizim
tasarım ona göre yenilenecek. Adımlar: (1) rakip ihalepro Kurumlar (kurum ağacı hiyerarşisi) + Firmalar
akış/ekran yapısını incele (giriş gerekebilir), ekran+veri-modeli notu çıkar; (2) bizim `v1-kurumlar` +
kurum ağacı + `v1-firma-analiz` dizin + `v1-firmalar`'ı o desene göre yeniden tasarla. **DETSİS hiyerarşisi
zaten elimizde** ([[ekap-detsis-idare-tur]]: DetsisAgaci 87.528, idareKodList eşleştirme) — ağaç için taban
bu. UZUN VADE: koda başlamadan ÖNCE rakip-inceleme + tasarım notu. Referans: [[rakip-ihalepro-referans]].
→ `v1-kurumlar.html`, kurum ağacı (idare_dizin / DETSİS), `v1-firma-analiz.html` (dizin), `v1-firmalar.html`
**✅ ADIM 1 — RAKİP ANALİZİ (3 Ağu, PUBLIC erişilebilir, login YOK):**
- **Kurumlar:** 2 sekme İdareler/Kurumlar; üst seviye 36 DETSİS grubu (bakanlıklar + BELEDİYELER/DMO/CUMHURBAŞKANLIĞI/
  "5018 kapsamı dışı"…); her düğüm kartında Aktif İhale + Geçmiş İhale + Sözleşme Sayısı + Toplam Tutar (TL/TL2/USD/
  enflasyon-düzeltilmiş 4 değer); ağaç hiyerarşisi; "Takip Ettiğim Kurumlar" + "Tüm Kurumlar 50.630".
- **Firmalar:** sekmeler Firmalar + **Parlayan Yıldızlar** (1.883); her firmada İhale/Sözleşme/Tutar; misafirde `*****`
  maskeli (DMO açık); "Tüm Firmalar 443.288".
- **BULGU:** parçaların ÇOĞU bizde ZATEN VAR (DETSİS ağacı idare_agac_*, Parlayan Yıldızlar seg, misafir maskeleme,
  per-kurum stat). Fark = CİLA/DÜZEN (düğüm-başı stat kartları, temiz hiyerarşi, çoklu-para tutar). Sıfırdan değil.
- **✅ ADIM 2 — KARAR:** Hibrit taksonomi (DETSİS kökleri + yerelleri düzleştir). Tasarım notu: `UV6_KURUM_MERKEZI_TASARIM.md`.

**✅ FAZ A (backend, CANLI 3 Ağu):** `kurum_kategori_ozet()` RPC — `backend/migration_kurum_kategori_ozet.sql`.
  73 DETSİS kökü döndürür; "YEREL YÖNETİM KURULUŞLARI" (24350161) gizlenip çocukları (BELEDİYELER/İL ÖZEL/BİRLİKLER/
  MUHTARLIKLAR) üst kategori olarak düzleştirilir. Döner: detsis_no, ad, grup, toplam_ihale, toplam_dt, cocuk_sayisi.
  anon KAPALI (kimlik verisi), authenticated açık. Doğrulandı (has_function_privilege).

**✅ FAZ B (v1-kurumlar, CANLI 3 Ağu):** "Kategoriler" sekmesi EKLENDİ + VARSAYILAN (Kategoriler / Tüm Kurumlar /
  Takip Ettiklerim). Kart eşiği ihale+DT ≥ 1500 → 23 ana kart (BELEDİYELER→DIŞİŞLERİ); altı "Diğer küçük kurumlar"
  katlanır kartta (askeri alt-birim gürültüsü + düşük-hacim yüksek yargı). Kart tıkla → v1-kurum-analiz?gorunum=agac&dal=.
  Derin link (?ara/?il/?sirala veya ?sekme=liste/takip) → tablo. Misafir kapısı + JS-hata + eşik-mantığı doğrulandı.

**✅ FAZ B.2 (v1-kurum-analiz, CANLI 3 Ağu):** agacBaslat() sonunda `?dal=<detsis>` → agacYoluAc() (idare_agac_yol
  ile kök→düğüm aç + hedefe kaydır/vurgula) + hedefin çocuklarını genişlet. Yollar psql'de doğrulandı.

**✅ FAZ A.2 (CANLI 3 Ağu):** kategori kartlarına **"Toplam Sözleşme Tutarı"** (tam rakam ₺). Yeni MV
  `idare_hiyerarsi_bedel_mv` (backend/migration_idare_hiyerarsi_bedel.sql) — sayim_mv'yi aynalar (detsis anahtarlı,
  aynı idare_ata_torun closure); ihale=sozlesme_bedeli (ikn→ilanlar DISTINCT ON), DT=kazanan_bedel (dt_no→ilan, TRY/boş).
  kurum_kategori_ozet'e +toplam_ihale_bedel/+toplam_dt_bedel. Gece refresh eklendi (PGOPTIONS ile paralellik kapalı — 64MB /dev/shm).
  Doğrulandı: çift-sayım yok (en büyük düğüm YEREL kökü ≤ toplam), BELEDİYELER 2,64 T₺ / ULAŞTIRMA 2,05 T₺ / SAĞLIK 900 Mr₺.
**✅ YAN BUG (A.2 sırasında):** idare_harcama_mv sahibi supabase_admin'di, gece refresh -U postgres → permission denied,
  SESSİZCE başarısız (İdareler "Toplam Harcama" kurulumdan beri bayat). Sahiplik postgres'e alındı, refresh+PGOPTIONS ile düzeltildi.
**✅ FAZ A.3 (CANLI 3 Ağu):** İdareler tablosu "Sözleşme" + "Toplam Harcama" kolonları + 💰 stat tile (compact ₺ paraKisa).
  Kolonlar/veri/render paralel oturumda eklendi; ben SIRA_ANAHTAR'a sozlesme+harcama ekleyip sortability bug'ını düzelttim
  (başlık tıklaması sıralama handler'ında erken dönüyordu, ok göstergesi boştu).
**✅ FAZ C(a) (CANLI 3 Ağu):** v1-firmalar birleşik firma KPI şeridi (4 tile: 🏢 Toplam Firma 433.558 · 📄 Sözleşme 5,59M ·
  💰 Ciro 11,7 Trilyon ₺ · 🤝 İş Ortaklığı 9.865) — `firma_ozet_birlikte()` anon-AÇIK → misafirde de dolar (çengel).
  paraBuyuk() kompakt Trilyon/Milyar format. Misafir panelinde görsel doğrulandı (değerler + 0 console hatası).
**✅ FAZ C(b) (CANLI 3 Ağu):** v1-firmalar Kapsam mod bar (📄İhale/⚡DT/🔗İkisi). İHALE YOLU DEĞİŞMEDİ (regresyon sıfır);
  DT/İkisi additive `yukleRpc()` dalı → firma_dizin_dt / firma_dizin_birlikte (7 kolon: #/Firma/İl/Sözleşme/Ciro/Son Sözleşme/takip).
  Segment ihale-only (DT/İkisi gizli); DT'de il pasif (RPC'de p_il yok); rpcSort sütun başlıkları (sozlesme/bedel/tarih);
  misafirde bar gizli + yetkiyeGoreKirp ihale'ye zorlar; takip sekmesinde ihale zorla; ?fmod= URL kalıcı; race guard (benim/istekNo) korundu.
  Doğrulama: guest tam parse + KPI + kilit + ?fmod=dt güvenli (0 console hatası); RPC şema/imza psql'de; **DT/İkisi liste render'ı girişli ekranda görülür (üyeye özel)**.
**⚠️ DOĞRULAMA:** Kategori+ağaç ÜYEYE ÖZEL → girişsiz panelde görsel test yapılamadı; görsel onay kullanıcının girişli ekranında.

**✅ FAZ D (CANLI 5 Ağu — ihalepro TARAMA sayfası paritesi; kullanıcı "tablo gibi yap" geri bildirimi):**
Kategoriler sekmesi kart-ızgarasından → **ihalepro tarzı sıralanabilir grup TABLOSU** (37 üst-DETSİS grubu).
(1) **7 kolon:** Kurum/Kategori · **Aktif İhale** · Toplam İhale · **Sözleşme** · Toplam DT · Toplam Tutar + satır→ağaç, sortable başlıklar.
(2) Yeni `idare_hiyerarsi_aktif_mv` (`backend/migration_kurum_kategori_ek.sql`): aktif_ihale (durum=aktif+son teklif ileri) +
sozlesme_sayisi (ihale_sonuclari sözleşmeli DISTINCT ikn, ikn→detsis; lot-şişmesi önlendi), idare_ata_torun rollup;
**sahip=postgres** (gece `-U postgres` refresh sessiz-bayat tuzağı; run_scraper.sh madde 3c). kurum_kategori_ozet 2 kolon genişletildi.
(3) **Arama motoru hero** (gradient "Kurum Arama Motoru") → "Tüm Kurumlar" sekmesi + mevcut arama akışını tetikler.
KALAN ihalepro farkı (opsiyonel): çoklu-para tutar (₺/enflasyon/$/güncel) + aktif-sayı VERİ KAPSAMI (bizde 6.081; DT/ihale backfill'e bağlı).

---

### Sıradaki (kullanıcı söyleyecek)
- [ ] …
