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

## MADDE 4 — Haritayı v2 davranışına taşı (BÜYÜK) 📋
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

## MADDE 5 — "Benim Firmam" → "Benim Firmam & Referans Firmam" 📋
Bana Özel'deki "Benim Firmam" butonu, kullanıcının kendi firması yanında bir **referans firma**
(yakın gördüğü / rakip) seçmesini de kapsayacak.
**Neden:** Kullanıcı ihale takibine yeni başlamış, henüz ihaleye girmemiş olabilir → kendi geçmişi
yoksa, referans bir firmayı seçip **ona uygun ihaleleri** kovalayabilir.
- Buton etiketi: "Benim Firmam" → "Benim Firmam & Referans Firmam".
- Akış: kendi firma + referans firma seçimi; eşleşme motoru referans firma profiline göre de öneri versin.
- MADDE 6 ile doğrudan bağlantılı (eşleşme algoritması referans firmayı da beslemeli).
→ `v1-benim-sayfam.html` (`.v1-firmam-btn` ~95) + `v1-analiz.html` akışı + backend eşleşme.

## MADDE 6 — "Sizin İçin Katılabileceğiniz İhaleleri Bulduk" algoritması: analiz + iyileştir 📋
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
adayı: filtresiz kelimede ilanlar'ı ilan_tarihi son 1 yıl ile de daralt, ya da en az bir
filtre zorunlu kıl. → sonraki tur.
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

## MADDE 9 — "Benzer İhaleler" skorlu (kategori + şehir + idare + başlık kelimesi) 🟡 migration hazır
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

## MADDE 12 — "Bu ilde öne çıkan firmalar": YIL bazlı sıralama/filtre 📋
(Kategori sıralaması yerine — kullanıcı bunu istedi.)
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

## MADDE 14 — Doğrudan Temin Analizi'ne YIL filtresi 📋
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

## MADDE 16 — DT kazanan firma analizi (firma bazında DT istatistiği) 🟡 part-1 migration hazır
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

## MADDE 18 — Firma Analizi: DT kazanımları görünür 🟡 Phase-A yapıldı
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

---

### Sıradaki (kullanıcı söyleyecek)
- [ ] …
