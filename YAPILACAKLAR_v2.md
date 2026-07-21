# YAPILACAKLAR v2 — İş Kuyruğu

> **Tek iş kuyruğu (v2).** Yeni talep gelince ÖNCE buraya yazılır, sonra uygulanır; sıradaki iş buradan seçilir. Eski kuyruk: `YAPILACAKLAR.md`.
> Oluşturma: **21 Temmuz 2026**. Kaynak: 6 boyutlu paralel kod+DB araştırması (workflow wcczbhev5).
> Durum kodları: `[ ]` beklemede · `[~]` devam ediyor · `[x]` bitti · `[?]` karar bekliyor

---

## V2-1 · Uluslararası İhaleler — tarih sıralama (yeniden→eskiye) + tarih aralığı filtresi  `[x]` ✅ (tarayıcıda doğrulandı: sort yeni→eski + tarih aralığı 9205→3163, tiebreaker eklendi)

**İstek:** Uluslararası ihaleler ekranında tarihe göre yeniden→eskiye sıralama ve tarih aralığı filtresi.

**Mevcut durum (kanıtlı):**
- `uluslararasi.html` veriyi doğrudan PostgREST ile `uluslararasi_ihaleler`'den, **server-side sayfalama** (25/sayfa, count=exact + `.range`) ile çekiyor — client-load-all riski YOK (9205 ilan client'a inmiyor).
- Şu anki tek sıralama: `son_teklif_tarihi DESC nullsLast` (satır ~309, ~349). İkincil (tiebreaker) sıralama YOK.
- Tarih alanları: `ilan_tarihi` (yayın, **0 NULL** — sıralama için ideal), `son_teklif_tarihi` (deadline, **1073 NULL** ≈ %11,6), `olusturulma`.
- Filtre RPC'si (`uluslararasi_filtre_secenekleri`) canlıda **ZATEN UYGULANMIŞ**. Ek migration GEREKMEZ.

**Plan (yalnız `uluslararasi.html`, saf client — DB dokunuşu yok):**
1. Toolbar'a **sıralama select'i** ekle: `İlan tarihi (yeni→eski)` [varsayılan], `Son teklif (yakın→uzak)`, `Tahmini bedel`.
2. Toolbar'a **iki `<input type="date">`** ekle (`f-tarih-bas`, `f-tarih-son`) + hangi alana uygulandığını gösteren etiket.
3. `siralamaAlan` varsayılanını `son_teklif_tarihi` → `ilan_tarihi` yap.
4. `filtreleriUygula`'ya tarih aralığı ekle: `gte(alan, bas)` + `lte(alan, son+'T23:59:59')` (bitiş günü dahil).
5. **KRİTİK — sayfalama tiebreaker:** `.order()`'a ikincil benzersiz anahtar (`publication_no` veya `id`) ekle. Günlük batch ~1280 satır AYNI `ilan_tarihi` ile geldiğinden tek-kolon sıralamada `.range()` pencereleri arası **satır tekrarı/atlaması** olur.
6. (Opsiyonel) `ilan_tarihi DESC` indeksi — 9205 satırda şart değil, büyümeyle önerilir (ayrı küçük migration).

**Riskler:** ① Tiebreaker olmazsa sayfalar arası satır kayması (gerçek). ② Aralık `son_teklif_tarihi`'ye uygulanırsa 1073 NULL satır sessizce düşer → aralık varsayılan `ilan_tarihi`. ③ `lte` gün sonu (`T23:59:59`) eklenmezse son gün kaybolur. ④ Stat kartları/dünya haritası global kalır (filtreden etkilenmez) — kabul edilebilir.

**Deploy:** VDS'te `git pull` (frontend). DB yok.

---

## V2-2 · €1 bedel hatası — TED placeholder temizliği  `[x]` ✅ (UI guard + scraper NULL + DB temizlik 191 satır; 494411-2026 artık bedelsiz)

**İstek:** "Almanya – Eczacılık – Olanzapin Münhasır Olmayan İndirim Anlaşması" ilanında bedel **€1** görünüyor, hata gibi.

**Kök neden (kanıtlı):** Hesaplama hatası DEĞİL. TED API bu ilan için tahmini değeri (`BT-27-Procedure`) düz **`"1.00"`** dönüyor — Alman idaresi §130a SGB V indirim anlaşmasında gerçek toplam bedel olmadığı için zorunlu alana **nominal 1 EUR placeholder** girmiş. `ted_scraper.py:400-404` bunu `float(1.0)` yapıp yazıyor, filtre yok. UI (`uluslararasi.html:402/315`) 1 truthy olduğu için `€1` basıyor (0 ve NULL zaten falsy → gizli).
- **Yaygınlık (canlı):** `tahmini_bedel=1` → **41 ilan**, `=0` → 128, `0<bedel<1` (çoğu 0.01) → 19; toplam **0<bedel≤1 = 60 kayıt**. `<100 EUR` = ~63 kayıt (63/64'ü placeholder, ilk gerçekçi değer 149,93). NULL = 5362 (doğru gizli). TED cn-standard ilanları AB-eşiği-üstü olduğundan birkaç yüz EUR altı gerçek değer pratikte olmaz.

**Plan (iki katman + opsiyonel temizlik):**
1. **UI guard (öncelikli, re-scrape'siz 41+ kaydı düzeltir):** `uluslararasi.html:315` `bedelFormat` başına eşik: `if (!v || v < 100) return '';`. Böylece placeholder değerler NULL gibi ele alınır, `€1` hiç basılmaz. (İstenirse "Bedel belirtilmemiş" etiketi; varsayılan: mevcut NULL davranışıyla tutarlı → boş.)
2. **Scraper normalizasyonu (kalıcı):** `ted_scraper.py:404` sonrası `if tahmini is not None and tahmini < 100: tahmini = None`. Upsert merge-duplicates olduğu için re-scrape'te eski `1.0` da NULL'a döner.
3. **(Opsiyonel) tek seferlik temizlik (yazma onayı gerekir):** `UPDATE uluslararasi_ihaleler SET tahmini_bedel=NULL WHERE tahmini_bedel<100;` (~63 satır).
4. Eşik sabiti tek yerde (`GECERLI_BEDEL_ESIK=100`), hem UI hem scraper aynı değeri kullansın.

**Latent (ayrı iş, bu görevde değil):** `para_birimi` scraper'da SABİT `'EUR'` (`ted_scraper.py:415`). TED tüm AB'yi kapsar → Polonya/PLN, Çekya/CZK, İsveç/SEK yanlış birimde etiketlenir. Ayrı düzeltme.

---

## V2-3 · e-Satınalma — yeniden→eskiye sıralama  `[x]` ✅ (🆕 En yeni / ⏰ Son teklif selector; olusturulma anon-safe doğrulandı, RFQ+KA tek eksende)  ·  (güncel/geçmiş ZATEN VAR)

**İstek:** (a) güncelleme alıyor mu izle, (b) yeniden→eskiye sıralama, (c) güncel/geçmiş kategorisi + son teklif geçince otomatik geçmişe alma.

**Bulgular (kanıtlı):**
- **(a) Güncelleme:** RFQ'lar kullanıcı web formundan INSERT edilir (`ozel-ihaleler.html:382`, Kurumsal+RLS+profil kapılı). **Scraper/ingestion YOK.** Canlıda **3 kayıt** (üçü "DNC Grup", aynı saniye → seed/test) + **0 gelen teklif** (`tedarikci_teklifleri` boş). Yani özellik "soğuk başlangıç"ta, organik veri yok. → Kod tarafında yapılacak yok; bu bir **ürün kararı** (tedarikçi davet/bildirim Faz-2, bu görev kapsamı değil).
- **(c) Güncel/Geçmiş: ZATEN UYGULANMIŞ.** Sekmeler `ozel-ihaleler.html:220-224` (🟢 Güncel / 🕓 Geçmiş / Tümü). Otomatik geçiş **sorgu-anı filtresiyle** (`son_teklif_tarihi >= now()`, NULL-güvenli `.or(...is.null)`). **Cron UPDATE bilinçle REDDEDİLMİŞ** (`migration_rfq_bayat.sql:20-23`: türev daima sorgu anında hesaplanır; cron alıcının 'kapali' kararını ezer). → **Yeniden yapma.**

**Asıl eksik iş = (b) sıralama:**
- Şu an liste **deadline'a** göre sıralı; `olusturulma` SELECT'e bile alınmıyor. `olusturulma` anon-GRANT'lı (42501 riski yok).
- **Plan (yalnız `ozel-ihaleler.html`):** ① `rfqCek` + `kaCek` select'lerine `olusturulma` ekle, map objelerine `olus` ekle. ② Birleşik client sort'u `new Date(b.olus)-new Date(a.olus)` (yeniden→eskiye) yap. ③ **DB `.order`'larını da `olusturulma DESC` yap** (`.limit(200)` penceresi deadline'a göre seçilirse >200 kayıtta en yeniler pencereden düşer — sinsi regresyon). İndeks `idx_satinalma_durum(durum, olusturulma DESC)` zaten var.
- **Tuzaklar:** NULL-güvenli `.or()` kalıbını BOZMA; hassas kolon (olusturan_user_id/vkn, acik_adres, enlem/boylam) SELECT'e EKLEME (anon'dan REVOKE'lu). Canlıda geçmiş RFQ olmadığı için test için bir seed kaydın tarihini geçmişe çek.

---

## V2-4 · Açık RFQ haritası — mod-duyarlı panel düzeltmesi  `[x]` ✅  ·  KA dahil ✅ (canlı: 3→13, RFQ modu firma yerine RFQ+KA gösteriyor)

**İstek:** (1) "Açık RFQ" 3 gösteriyor, gerçek veriler girilmemiş. (2) Firma Yoğunluğu→Açık RFQ moduna geçip şehre tıklayınca sağda hâlâ **firmalar** çıkıyor; RFQ modunda **RFQ'lar** görünmeli.

**Bulgular (kanıtlı):**
- **(2) Net kod bug'ı:** `harita.html:376 ilSec(key)` şehir tıklama handler'ı `aktifKatman`'ı **hiç okumuyor** → her modda "firma-önce" panel çiziyor. RFQ sorgusu (`satinalma_talepleri`, satır 468-482) panelde ZATEN var ama altta/ikincil. Ayrıca `katmanSec()` (349-355) mod değişince paneli yenilemiyor (seçili il varsa eski firma paneli takılı kalır).
- **(1) "3" doğru ama eksik:** `il_rfq_dagilimi()` yalnız `satinalma_talepleri`'ni (3 kayıt) sayıyor. e-Satınalma **listesi** ise KA'yı (`kamu_ihaleleri` kaynak='ka') da gösteriyor; harita RFQ katmanı KA'yı HİÇ saymıyor → harita listeden az fırsat gösteriyor.

**Plan — Bölüm A (net bug, uygulanacak, yalnız `harita.html`):**
1. `ilSec` başında `const rfqModu = (aktifKatman==='rfq');`.
2. Panel şablonunu dallandır: rfqModu iken **RFQ-önce** (üstte açık-RFQ KPI + "Bu ildeki açık RFQ'lar"), firma bloklarını `if(!rfqModu){...}` ile sar (gereksiz firma RPC'si atılmaz).
3. `katmanSec()` sonuna: `if (seciliIlKey) ilSec(seciliIlKey);` → moda basınca panel anında yeniden çizilir.
- **Tuzaklar:** il anahtarı fold'lu (`keyOf`), EKAP verisi BÜYÜK olabilir → `ilVeriAdlari` eq-listesi, **ilike YAZMA** (İ/ı tuzağı). NULL-güvenli `.or()` koru.

**Bölüm B — KARAR VERİLDİ ✅ KA DAHİL:** Haritanın açık-fırsat katmanına **Kalkınma Ajansı (KA) güncel ilanları da eklenecek** (KA: 99 toplam, **10 güncel**). `il_rfq_dagilimi()` RPC'si `kamu_ihaleleri` kaynak='ka', `son_teklif_tarihi>=now()` kayıtlarını UNION ALL ile içerecek (imza sabit, dönen alanlar il+adet — maske etkilenmez). `rfqYukle` + `ilSec` RFQ sorgusu KA'yı `kaCek` mantığıyla (il eq-listesi, ilike YAZMA) merge edecek. Etiket "Açık RFQ" olarak kalır.

---

## V2-5 · Gürcistan verisi — DOĞRULANDI aktif  `[x kontrol]`  ·  kapsam+guard opsiyonel `[ ]`

**Bulgu (kanıtlı):** Gürcistan **çekiliyor.** `georgia_scraper.py` gece cron'unda (`run_scraper.sh:78`, TED'in ardından, 15 Tem'den beri). `uluslararasi_ihaleler`'e `kaynak='georgia'`, `ulke='Gürcistan'`, `ulke_kodu='GEO'` ile yazıyor; TED ile **aynı birleşik listede**, ülke filtresinde ve dünya haritasında görünüyor. Canlıda **20 satır**, son yazım bugün 05:20.
- **Neden az (20):** TED sayfalanıp tamamı çekilirken Gürcistan **tek POST** atıyor (tarih penceresi/pagination yok) → yalnız varsayılan sonuç kümesi. Bu tasarım sınırı, bug değil.

**Opsiyonel iyileştirme (istenirse):** ① `georgia_scraper` SEARCH_BODY'ye tarih penceresi/sayfalama ekleyip TED gibi döngüye al (kapsam artışı). ② **Silent-zero guard:** parser 0 satır dönerse (İngilizce HTML string'leri değişirse) script sessizce "başarı" basıyor → 0 satırda uyarı/non-zero exit. Şu an cron exit-kodu kontrol etmiyor.

---

## V2-6 · Analiz tarafı — Doğrudan Temin / İhaleler ayrımı  `[x]` ✅ (ayrı `dt-analiz.html` + `dt_analiz_ozet` RPC/MV canlıda)

**Yapıldı (v1):** `dt-analiz.html` — DT pazarının genel analizi: KPI (toplam 1,49M / sonuçlanan / ort+medyan kazanan bedel ₺37K), aylık trend, tür/il/kategori dağılımı, kurum türü dağılımı, kazanan bedel aralığı, en çok DT yapan idareler. Pro-gated. `migration_dt_analiz.sql`: `_dt_ozet_json` (DRY) + `dt_analiz_mv` (filtresiz özet, gece CONCURRENTLY refresh — run_scraper.sh'e eklendi) + `dt_analiz_ozet` wrapper RPC (authenticated-only, anon 42501). Sidebar linki 23 sayfaya eklendi.
**Mimari not:** DT 1,49M satır → filtresiz aggregate ~5s (timeout üstü) → **MV zorunlu**. Filtresiz view anında (MV); filtreli canlı yol RPC'de VAR ama tür='Mal' (1,06M) ~18s → **v1'de sayfa filtre GÖSTERMİYOR** (güvenli). AÇIK v2: filtreler için per-boyut MV (il/kategori/tür başına özet) gerekir.

**Bulgu (kanıtlı):** Analiz sayfaları (rekabet/kurum/firma) **zaten yalnız İhale evrenini** okuyor; DT karışmıyor ("kapsam rozeti" ile UI'da yazılı). DT bilinçle ayrı tabloda (`dogrudan_temin_ilanlari`/`_sonuclari`), kazananı yüklenici cirosuna karıştırılmıyor. Yani istek = **DT için AYRI bir analiz yüzeyi EKLEMEK** ("karışıyor" değil, "DT analiz edilemiyor").
- **DT veri olgunluğu (canlı):** `dogrudan_temin_sonuclari` = **247.207 satır, hepsinde kazanan_bedel dolu**; DT ilan toplam 1,49M. → Bedel-bazlı DT analizi (kategori/il/idare/tür/trend + bedel dağılımı) **fizibıl**. DT'de usul/tenzilat/katılımcı/yaklaşık-maliyet KAVRAMLARI YOK → o kartlar DT görünümünde gösterilmez.

**Seçenekler (kullanıcıya sunuldu):**
- **A) Her analiz sayfasına "İhaleler | Doğrudan Temin" toggle** (dashboard'daki mod-seçici deseni). Artı: tanıdık UX, sıfır sayı karışması. Eksi: metrik farkı → koşullu UI karmaşası.
- **B) Ayrı `dt-analiz.html` sayfası** (TAVSİYE). Artı: en temiz/dürüst ayrım, İhale sayfalarına sıfır risk, `dogrudan-temin.html` gözat sayfasının analiz kardeşi. Eksi: yeni sayfa bakımı.
- **C) `dogrudan-temin.html`'e "Analiz" sekmesi.** Artı: tek DT kapısı. Eksi: İhale tarafıyla IA asimetrisi (orada liste/analiz ayrı).
- **Ortak backend:** 1 yeni `dt_rekabet_ozet` benzeri agregasyon RPC — **MV + gece REFRESH** deseniyle (DT 1,49M satır, canlı GROUP BY statement_timeout riski). Yeni MV/RPC'de idare/kazanan_firma anon'a KAPALI (REVOKE şart).

---

## V2-7 · Mobil/telefon uyumu + tema denetimi (tüm sayfalar)  `[~]`

**İstek (22 Tem):** Platform telefon/mobil için uygun mu, görüntü/temada sıkıntı var mı — tek tek araştır ve düzelt.

**DENETİM SONUCU (7 ajan, 25 sayfa):** Temel altyapı sağlam — tüm sayfalarda viewport meta var, `js/main.js` mobilde hamburger (☰) enjekte ediyor (900px), `js/theme.js` açık/koyu tema. Ama sistematik + sayfa-özel kırılımlar bulundu:
- **KRİTİK (mobil kullanılamaz):** `profil` + `teklif-olustur` + `ihale-detay` sidebar'ı mobilde gizlemiyordu (240px sabit kalıp .main'i eziyordu) · `takipte` + `uyumluluk` 6-kolon tabloyu `overflow:hidden` ile kırpıyordu · `kik-kararlar` (tarih kutuları min-width:160px + flex-wrap yok) · `bildirimler` (7 sekme wrap yok) · `index` (harita sekme şeridi wrap yok) yatay taşma.
- **ORTA (tema):** `rekabet-analizi` + `dt-analiz` grafik y-ekseni etiketleri sabit `#F5F6F8` → açık temada BEYAZ ÜSTÜNE BEYAZ (görünmez) · `uluslararasi` + `ticaret-analiz` `.dunya-tooltip` metni açık temada görünmez · `harita` sabit koyu il dolguları · `login` style.css/theme.js yüklemiyor (hep koyu) · `fiyatlandirma` kupon mesajı koyu-koyu.
- **ORTA (grid/topbar):** dashboard/ihaleler/firma inline grid'ler mobilde collapse etmiyor · birçok topbar sabit 56px + flex-wrap yok.

**GLOBAL DÜZELTMELER (yapıldı):**
- `css/style.css` — mobil (900px) global blok: `.app>.sidebar{display:none}` (specificity ile, !important YOK → hamburger overlay bozulmaz), `.app .table-wrap` yatay scroll + `min-width:560px`, `.app .topbar` height:auto+flex-wrap. → sidebar/tablo/topbar sorunlarının çoğunu tek yerden çözer.
- `js/theme.js` — tema değişince `tema-degisti` CustomEvent dispatch (grafik sayfaları dinleyip yeniden çizsin).

**SAYFA-ÖZEL DÜZELTMELER (7 ajan paralel, devam ediyor):** grid collapse (auto-fit), grafik cssVar tema renkleri + tema-degisti listener, tooltip/oner-kutu tema, kik/bildirimler/index kritik taşmalar, login açık tema bloğu, fiyatlandirma kupon renkleri.

**CACHE-BUST (deploy'da):** theme.js?v=5→v6 + style.css?v=mob1 (26+30 sayfa) — değişen CSS/JS anında görünsün (HTML DYNAMIC, CSS/JS 4h cache).

**Yöntem doğrulaması:** canlı 375px probe'ları (dashboard/ihaleler/uluslararasi/harita/ozel-ihaleler) → hamburger çalışıyor, sayfa-seviyesi taşma yok, açık tema uygulanıyor. Kalan görsel doğrulama deploy sonrası.

---

### Durum: V2-1..V2-4 + V2-6 TAMAM ✅ · V2-5 doğrulandı (opsiyonel iyileştirmeler açık)
Tek kalan opsiyonel iş: **V2-5 Gürcistan kapsam artışı** (tek POST→sayfalama) + silent-zero guard. Veri zaten geliyor (20 satır), acil değil.

### DEPLOY GEÇMİŞİ
- **21 Tem, commit 3448bc2** → VDS pull, migration_rfq_ka_dahil.sql uygulandı. V2-1/2/3/4 CANLI+doğrulandı.
- **21 Tem, commit 6013860** → VDS pull, migration_dt_analiz.sql uygulandı (dt_analiz_mv CONCURRENTLY refresh test edildi). V2-6 CANLI: dt-analiz.html Pro-lock guest'te doğru, render pipeline (4 chart + KPI + bant + tablo) gerçek veriyle test edildi, RPC anon'a 42501. run_scraper.sh gece refresh'e dt_analiz_mv eklendi.
