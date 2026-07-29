-- =============================================================================
-- migration_ekap_hasat.sql — "zaten çekilen ama okunmadan atılan EKAP yanıtı" hasadı
-- 29 Tem 2026 · 4 ayrı çalışmanın BİRLEŞTİRİLMİŞ tek migration'ı
-- =============================================================================
--
-- NEDEN
-- ─────
-- Bir denetim, EKAP'tan ZATEN İNDİRİLEN yanıtların büyük kısmının okunmadan
-- atıldığını kanıtladı. Dört ayrı yazma yolu düzeltildi; hepsi SIFIR EK EKAP
-- İSTEĞİ ile veri kazanıyor (aynı yanıttan daha çok alan okunuyor):
--
--   1) EKAP LİSTE yanıtı  (GetListByParameters)      → ekap_ihale_backfill.py
--                                                      ekap_sonuc_backfill.ilan_kompakt_ekle
--      Atılan: liste `id` (64-hane kalıcı ihale hash'i), usul, ihale tarihi.
--      ilanlar.ekap_ihale_id yalnız %17,7 dolu (347.010/1.962.279) — oysa hash
--      yanıtın içindeydi. Belge derin linkinin üretilememesinin tek nedeni buydu.
--
--   2) EKAP DETAY yanıtı  (GetByIhaleIdIhaleDetay)   → ekap_detay_alanlar.py (YENİ)
--                                                      ilan_metni_backfill.py
--                                                      ekap_sonuc_backfill.py
--      İKİ backfill bu yanıtı çekip içinden TEK alan alıyordu. Atılan: okas,
--      ihtiyaç kalemleri, işin yeri, yasa kapsamı, iptal bilgisi, etiketli tarih
--      listesi, idare telefon/faks/üst kurum zinciri/il-ilçe, itiraz bedeli.
--      Ölçüm: ilanlar.okas %0,62 · kalemler %0,41 dolu.
--
--   3) SONUÇ İLANI HTML'i                            → ekap_sonuc_backfill.py
--      4 regex okunup gerisi atılıyordu. Ayrıca KANITLI SESSİZ BUG: eski
--      `html_teklif_sayisi_parse` kalıbı gerçek HTML'de HİÇ eşleşmiyordu
--      (etiketle değer arasında ~54 karakter <td> işaretlemesi var) — 5/5 gerçek
--      ilanda 3/3 alan None döndü. `katilimci_sayisi`nın 2,5M satırda tamamen
--      boş olmasının sebebi buydu. Tablo-tabanlı ayrıştırıcı ile düzeltildi.
--
--   4) DT dtDetayGetir yanıtı                        → dt_kazanan_scraper.py
--      4 bloğun 3'ü atılıyordu. En değerlisi BransKodList = DT'nin OKAS/CPV'si:
--      "DT'de OKAS YOK" varsayımı YANLIŞ çıktı (canlı: ['33194120'], ['44316400']).
--      Ayrıca 22-d/22-c ayrımı, üst kurum zinciri, 4 ilan listesi + EncIlanId.
--
-- BU DOSYA NE YAPAR
-- ─────────────────
-- 4 tabloya toplam 47 YENİ kolon açar, misafir (anon) maskesini kolon kolon kurar,
-- ucuz kısmi indeksleri kurar ve maskenin gerçekten doğru olduğunu COMMIT'ten ÖNCE
-- doğrular (yanlışsa tüm migration geri alınır).
--
--   public.ilanlar                  → 17 yeni  (+3 zaten var, no-op güvence)
--   public.ihale_sonuclari          →  9 yeni
--   public.dogrudan_temin_ilanlari  → 20 yeni
--   public.dogrudan_temin_sonuclari →  1 yeni
--
-- ÇALIŞTIRMA
-- ──────────
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ekap_hasat.sql
--
-- ⚠️ BÖLÜM 2 ve 3 BU DOSYANIN ANA İŞLEMİNİN DIŞINDADIR (ağır/isteğe bağlı).
--    Ana işlem (BÖLÜM 1) saniyeler sürer ve akan backfill'leri pratikte durdurmaz.
--
-- ⚠️ MIGRATION ÖN KOŞUL DEĞİL — kod her iki şemada da çökmez.
--    Dört yazma yolunun DÖRDÜ de "kolon yoksa o alanı gövdeden düşür" korumasına
--    sahip (aşağıda tek tek doğrulandı). Yani backfill KOŞARKEN `git pull` yapılsa
--    bile hiçbir kayıt kaybolmaz; yalnız yeni alanlar boş kalır. Bu dosya bir ön
--    koşul değil, alanların gerçekten YAZILABİLMESİNİN anahtarıdır.
--      · ekap_ihale_backfill.py   → OPSIYONEL_ALANLAR + eksik_kolon()  (düşür-tekrarla)
--      · ekap_sonuc_backfill.py   → SONUC_OPSIYONEL / KOMPAKT_OPSIYONEL (düşür-tekrarla)
--      · ekap_detay_alanlar.py    → kolonlari_sapta() açılışta + PATCH'te düşür-tekrarla
--                                   + `zorunlu` gövde garantisi (ilan_metni her hâlükârda yazılır)
--      · dt_kazanan_scraper.py    → SEMA bayrakları (sema_sinama) + çalışma anı geri düşme
--
-- ⚠️ TABLO DÜZEYİNDE `REVOKE SELECT ON <tablo> FROM anon` ASLA YAZILMAZ.
--    Bu 4 tabloda anon'un TABLO-GENELİ SELECT'i YOKTUR; maske KOLON-GRANT'larıyla
--    kurulu (29 Tem canlı doğrulaması: ilanlar.idare / ihale_sonuclari.ham_json /
--    dogrudan_temin_ilanlari.idare / dogrudan_temin_sonuclari.kazanan_firma → 42501).
--    PostgreSQL'de tablo düzeyi REVOKE kolon-GRANT'ları da siler → misafir tarafı
--    TOPYEKÛN ölürdü. Aşağıda YALNIZ kolon düzeyinde revoke/grant var; kolon düzeyi
--    REVOKE başka kolonların yetkisine dokunmaz ve olmayan yetkiyi geri almak no-op'tur.
--
-- ⚠️ NEDEN YİNE DE HER YENİ KOLONDA ÖNCE REVOKE VAR:
--    [[anon-maske-iki-kok-neden]] kök-neden A — yeni kolon, ALTER DEFAULT PRIVILEGES
--    ayarına göre anon'a AÇIK doğabilir. "Bu tabloda kapalı doğar" varsayımı sessizce
--    yanlış olabileceği için niyet şemaya AÇIKÇA kazınıyor, sonra dar GRANT veriliyor.
-- =============================================================================


-- ###########################################################################
-- BÖLÜM 1 — ŞEMA + MASKE (tek işlem, hızlı, backfill koşarken güvenli)
-- ###########################################################################
BEGIN;

-- ---------------------------------------------------------------------------
-- 1.1) public.ilanlar — LİSTE yanıtı (3 kolon, canlıda ZATEN VAR → no-op güvence)
-- ---------------------------------------------------------------------------
-- 29 Tem PostgREST kontrolünde üçü de VAR ve anon'a AÇIK çıktı. Burada yeniden
-- yazılmalarının tek nedeni temiz/yeni ortamlarda şemanın eksik kalmaması.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ekap_ihale_id     text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS usul              text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS son_teklif_tarihi timestamptz;

COMMENT ON COLUMN public.ilanlar.ekap_ihale_id IS
  'EKAP liste yanıtındaki 64-hane KALICI ihale hash''i. Vatandaş doküman sayfasının '
  'anahtarı. ⚠ GetDokumanUrl''in döndürdüğü hash OTURUMLUK''tur (ardışık çağrılar '
  'farklı değer döndürür) ve DB''ye YAZILMAZ — kalıcı olan budur.';

-- ---------------------------------------------------------------------------
-- 1.2) public.ilanlar — DETAY yanıtı (17 YENİ kolon)
-- ---------------------------------------------------------------------------
-- Yasa kapsamı / istisna maddesi
-- ⚠ item.ihaleKapsamAciklama çevrilmiş metni verir ('İstisna'); ihaleBilgi'deki eşi
--   i18n ANAHTARI döner ('TENDER_SEARCH…EXCEPTION') → kod item'ı tercih eder,
--   o da yoksa yasaKapsami4734 ('1'|'2') koduna düşer.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS yasa_kapsami         text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS istisna_usul         text;   -- '4734 / 3-g'

-- İPTAL BİLGİSİ
-- ⛔ PROJE KARARI: bu kolonlar DOLDURULUR ama `durum` alanına 'iptal' YAZILMAZ.
--    Arayüz 'iptal' durumunu beklemiyor; yazılsaydı 236.647 kayıt tüm sekmelerden
--    SESSİZCE düşerdi. Durum dönüşümü arayüz hazırlandıktan sonra AYRI iş.
--    (Kod bu kararı testle de garanti ediyor: hiçbir yerde `durum` üretilmiyor.)
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_tarihi         timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_nedeni         text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_madde          text;

-- ihaleBilgi.ihaleTarihSaatList — etiketli tarihler
--   DATASYNC.IHALE_TARIH_SAAT           → mevcut `ihale_tarihi` kolonuna yazılır
--   DATASYNC.YETERLIK_TARIH_SAAT        → yeterlik_tarihi
--   DATASYNC.ILK_TEKLIF_ICIN_TARIH_SAAT → ilk_teklif_tarihi
-- Bilinmeyen bir etiket gelirse HAM liste ihale_tarih_saatleri'ne düşer
-- ("bir daha veri atmayalım"); bilinen etiketlerde o kolon NULL kalır.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS yeterlik_tarihi      timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ilk_teklif_tarihi    timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ihale_tarih_saatleri jsonb;

-- item.ihaleOzellikList — ihale nitelikleri ('TENDER_DETAIL.' öneki kodda kırpılır)
-- ['IS_DENEYIM_BELGE','YABANCI_ISTEKLI_KATILIM','ALT_YUKLENICI','AVANS', …]
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ihale_ozellikleri    text[];

-- idare bloğu — ⚠ TAMAMI anon'a KAPALI (aşağıda), çünkü `idare` kolonunun kendisi
-- misafir maskesinde; ondan türeyen her şey de kapalı kalmalı.
-- ekap_idare_id = EKAP'ın İÇ idare kimliği (ör. '1996'). DEĞERİ: DETSİS
-- eşleştirmesinin ANAHTARI — arama filtresi tam bu değeri istiyor (idareKodList).
-- İdare adıyla join AMBİGÜ ("BİLGİ İŞLEM DAİRE BAŞKANLIĞI" = 114 kayıt); bu kolon
-- dolunca idare_tur sınıflandırması ad tahmininden çıkıp otoriter kimliğe bağlanır.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ekap_idare_id        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_telefon        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_faks           text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ust_idare            text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS en_ust_idare_kod     text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS en_ust_idare_adi     text;   -- 'KİTLER' / 'BİTLER'
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_il             text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_ilce           text;

COMMENT ON COLUMN public.ilanlar.ekap_idare_id IS
  'EKAP iç idare kimliği (idareKodList arama anahtarı). DETSİS eşleştirmesinin '
  'otoriter anahtarı — idare ADI ile join ambigüdür.';

-- ---------------------------------------------------------------------------
-- 1.3) public.ihale_sonuclari — SONUÇ İLANI HTML'i (9 YENİ kolon)
-- ---------------------------------------------------------------------------
-- ZATEN VAR OLAN ve artık DOLDURULAN kolonlar (burada tekrar açılmıyor):
--   is_baslama_tarihi, is_bitis_tarihi, is_suresi_gun, sonuc_tur, ham_json,
--   yuklenici_il, katilimci_sayisi, gecerli_teklif_sayisi, toplam_teklif_sayisi
--
-- KOLON EKLENMEYEN ALANLAR (HTML'de YOK — bilerek uydurulmadı):
--   karar_tarihi       → kolon VAR ama sonuç ilanında komisyon karar tarihi geçmiyor;
--                        ihale gününü karar tarihi diye yazmak veri uydurmak olurdu
--   yuklenici_vergi_no → VKN sonuç ilanında hiç yayınlanmıyor ([[vkn-yok-beyan-rozet]])
ALTER TABLE public.ihale_sonuclari
  -- 1) İhalenin / c) Usulü — 'Açık', 'Pazarlık (MD 21 C)', '4734 / 3-g'
  ADD COLUMN IF NOT EXISTS ihale_usulu            TEXT,
  -- ↑ metinden türetilen kanonik madde kodu — '3-g', '21-c', '21-f'
  -- ⚠ AD BİRLEŞTİRİLDİ: bu kolon iki ajan tarafından `kanun_maddesi` (sonuç tarafı) ve
  --   `yasa_madde_kodu` (DT tarafı) diye AYRI adlarla önerilmişti. Aynı anlam, aynı
  --   değer uzayı (4734 sayılı Kanun'un maddesi) → TEK ad: `yasa_madde_kodu`.
  --   Böylece dogrudan_temin_ilanlari.yasa_madde_kodu ('22-d') ile birlikte
  --   sorgulanabiliyor. ekap_sonuc_backfill.py buna göre düzeltildi.
  ADD COLUMN IF NOT EXISTS yasa_madde_kodu        TEXT,
  -- 1) İhalenin / d) Pazarlık Usulünün Seçilme Gerekçesi (yalnız pazarlık ihalelerinde)
  ADD COLUMN IF NOT EXISTS usul_gerekce           TEXT,
  -- 2) İhale konusu … / b) Yapılacağı (veya teslim edileceği) yer
  ADD COLUMN IF NOT EXISTS isin_yeri              TEXT,
  -- 1) İhalenin / a) Tarihi — ihalenin YAPILDIĞI gün (sözleşme tarihinden AYRI)
  ADD COLUMN IF NOT EXISTS ihale_tarihi           TIMESTAMPTZ,
  -- 3) Teklifler / a) Dokümanı EKAP üzerinden e-imzayla indiren sayısı
  -- Rekabet hunisinin ÜST ucu: kaç firma baktı → kaç teklif verdi → kaçı geçerli.
  -- Canlı örnek: 15 indiren → 11 teklif → 9 geçerli. Bugüne dek hiçbir kolonda yoktu.
  ADD COLUMN IF NOT EXISTS dokuman_indiren_sayisi INTEGER,
  -- 3) Teklifler / Yerli (malı teklif eden) istekli lehine fiyat avantajı
  ADD COLUMN IF NOT EXISTS yerli_fiyat_avantaji   BOOLEAN,
  -- 4) Sözleşmenin / Yüklenicinin adresi ⚠ ŞAHIS FİRMALARINDA KİŞİSEL VERİ → anon'a KAPALI
  ADD COLUMN IF NOT EXISTS yuklenici_adres        TEXT,
  -- 4) Sözleşmenin / Yüklenicinin uyruğu ('Türkiye' / yabancı)
  ADD COLUMN IF NOT EXISTS yuklenici_uyruk        TEXT;

COMMENT ON COLUMN public.ihale_sonuclari.dokuman_indiren_sayisi IS
  'SONUÇ İLANI 3-a: dokümanı e-imzayla indiren firma sayısı. Teklif sayısına oranı '
  '= ilgi/katılım dönüşümü (rekabet hunisinin üst ucu).';
COMMENT ON COLUMN public.ihale_sonuclari.yuklenici_adres IS
  'SONUÇ İLANI 4: yüklenici adresi. Şahıs firmalarında KİŞİSEL VERİ — anon''a AÇILMAZ.';
COMMENT ON COLUMN public.ihale_sonuclari.yasa_madde_kodu IS
  'ihale_usulu metninden türetilen kanonik madde kodu: ''4734 / 3-g'' → ''3-g'', '
  '''Pazarlık (MD 21 C)'' → ''21-c''. dogrudan_temin_ilanlari.yasa_madde_kodu ile AYNI ad/anlam.';

-- ---------------------------------------------------------------------------
-- 1.4) public.dogrudan_temin_ilanlari — dtDetayGetir 3 blok (20 YENİ kolon)
-- ---------------------------------------------------------------------------
-- NOT: dtAra LİSTE yanıtından zaten gelen alanlar BİLEREK tekrarlanmadı
--   (Dtn=dt_no, IsinAdi=baslik, Turu=tur, DtTarihSaati=tarih, DtDurumu=durum,
--    IdareBilgileri.Idare=idare, .Ili=il) — detaydan tekrar yazmak, kuyruk
--   filtresini (durum IN (...)) tur ORTASINDA kaydırma riski taşırdı.
ALTER TABLE public.dogrudan_temin_ilanlari
  -- ── blok 1: DogrudanTeminBilgileri ────────────────────────────────────────
  -- BransKodList = DT'nin OKAS/CPV'si. Alan DİZİ (bir DT'de birden çok kod olabilir)
  -- → text[]; eşleştirme motoru `&& ARRAY[...]` / PostgREST `cs.{kod}` ile sorgular.
  -- Boş dizi yerine NULL: "kod yok" ile "hiç bakılmadı" ayrımı korunsun.
  ADD COLUMN IF NOT EXISTS dt_brans_kodlari      TEXT[],
  -- Ham metin: '22-d* (Parasal Limit Kapsamında)' — kayıpsız saklanır
  ADD COLUMN IF NOT EXISTS yasa_maddesi          TEXT,
  -- ↑ metinden türetilen kanonik kod: '22-d' / '22-c'. Kalıp tutmazsa NULL (uydurma yok).
  -- ihale_sonuclari.yasa_madde_kodu ile AYNI ad/anlam (bkz. 1.3).
  ADD COLUMN IF NOT EXISTS yasa_madde_kodu       TEXT,
  -- BOOLEAN'a çevrilmedi, ham metin saklanıyor: kayıpsızlık > yanlış eşleme riski
  ADD COLUMN IF NOT EXISTS kismi_teklif          TEXT,       -- 'Verilebilir' / 'Verilemez'
  ADD COLUMN IF NOT EXISTS kisim_sayisi          INTEGER,    -- çoğu kayıtta boş ('')
  ADD COLUMN IF NOT EXISTS e_ihale               BOOLEAN,
  ADD COLUMN IF NOT EXISTS ilan_sekli            TEXT,       -- 'Doğrudan Temin İlanı' / 'İlansız'
  ADD COLUMN IF NOT EXISTS sozlesme_tasarisi_var BOOLEAN,
  ADD COLUMN IF NOT EXISTS sozlesme_veya_alim    BOOLEAN,
  ADD COLUMN IF NOT EXISTS istisna_dayanagi      TEXT,
  ADD COLUMN IF NOT EXISTS mevzuat_dayanagi      TEXT,
  ADD COLUMN IF NOT EXISTS duyuru_yapilacak      BOOLEAN,
  ADD COLUMN IF NOT EXISTS iptal_nedeni          TEXT,
  ADD COLUMN IF NOT EXISTS iptal_tarihi          TIMESTAMPTZ,
  -- ── blok 2: IdareBilgileri (üst kurum zinciri) ────────────────────────────
  -- ⚠ AD BİRLEŞTİRİLDİ: DT tarafı `en_ust_idare` önermişti, ilanlar tarafı
  --   `en_ust_idare_adi`. Aynı anlam (üst kurumun ADI) → TEK ad: `en_ust_idare_adi`.
  --   (ilanlar'da ayrıca en_ust_idare_kod var; DT yanıtı kod vermiyor.)
  --   dt_kazanan_scraper.py ve migration_anon_maske.sql buna göre düzeltildi.
  -- ⚠ KİMLİK VERİSİ: `idare` ile aynı sınıf → anon'a KAPALI kalmalı.
  --   "SAĞLIK BAKANLIĞI > BAKAN YARDIMCILIKLARI" zinciri, maskelenen idare adını
  --   daraltıp geri okumaya yarayan bir oracle olurdu.
  ADD COLUMN IF NOT EXISTS en_ust_idare_adi      TEXT,
  ADD COLUMN IF NOT EXISTS ust_idare             TEXT,
  -- ── blok 3: IlanBilgileri ─────────────────────────────────────────────────
  -- 4 listenin tamamı ham jsonb: {DogrudanTeminIlanBilgisiList, DuzeltmeIlanBilgisiList,
  -- IptalIlanBilgisiList, SonucIlanBilgisiList}; her eleman {IlanTarihi, IlanTipi, EncIlanId}.
  -- ⚠ EncIlanId = EKAP erişim hash'i (dt_ihale_token ile AYNI sınıf: saf altyapı)
  --   → anon VE authenticated'a KAPALI, yalnız service_role.
  ADD COLUMN IF NOT EXISTS dt_ilanlar            JSONB,
  -- jsonb'ye inmeden sorgulanabilsin diye denormalize en erken tarihler.
  -- ⚠ yayin_tarihi (liste yanıtı E8) ile KARIŞTIRMAYIN.
  ADD COLUMN IF NOT EXISTS dt_ilan_tarihi        TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS dt_sonuc_ilan_tarihi  TIMESTAMPTZ,
  -- ── işleme damgası ────────────────────────────────────────────────────────
  -- kazanan_denendi'den AYRI olmak ZORUNDA: 815.895 satır ESKİ (detaysız) kodla
  -- damgalandı ve kuyruktan düştü. "Detay bloklarıyla birlikte işlendi mi?"
  -- sorusunun tek yanıtı bu kolondur; kurtarma sorgusu buna dayanır
  -- (backend/migration_dt_detay_kurtarma.sql — AYRI dosya, bilerek burada değil).
  ADD COLUMN IF NOT EXISTS detay_cekildi         TIMESTAMPTZ;

COMMENT ON COLUMN public.dogrudan_temin_ilanlari.dt_brans_kodlari IS
  'DT''nin OKAS/CPV kodları (EKAP BransKodList). "DT''de OKAS yok" varsayımını '
  'çürütür — kategori artık başlık tahmininden çıkabilir.';
COMMENT ON COLUMN public.dogrudan_temin_ilanlari.detay_cekildi IS
  'dtDetayGetir''in 3 detay bloğuyla BİRLİKTE işlendi damgası. kazanan_denendi DOLU '
  've bu NULL ise satır eski (detaysız) kodla damgalanmıştır.';

-- ---------------------------------------------------------------------------
-- 1.5) public.dogrudan_temin_sonuclari — sözleşme bedelinin para birimi
-- ---------------------------------------------------------------------------
-- bedel_parse() 'TL'/'TRY'/'₺' eklerini SİLİP sayıya çeviriyor; TRY dışı bir bedel
-- ('1.000,00 USD') float()'ta patlayıp NULL'a düşüyor ve HANGİ para biriminde
-- olduğu tümden kayboluyordu.
ALTER TABLE public.dogrudan_temin_sonuclari
  ADD COLUMN IF NOT EXISTS para_birimi TEXT;

-- ---------------------------------------------------------------------------
-- 1.6) MİSAFİR (anon) MASKESİ — her yeni kolonda ÖNCE REVOKE, SONRA dar GRANT
-- ---------------------------------------------------------------------------
-- KURAL: sayılar / tarihler / bayraklar / usul-madde bilgisi misafire AÇIK;
--        KİMLİK (idare zinciri, EKAP iç kimlikleri) ve KİŞİSEL VERİ (adres) KAPALI.

-- ── ilanlar ────────────────────────────────────────────────────────────────
REVOKE SELECT (
  ekap_ihale_id, usul, son_teklif_tarihi,
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri,
  ekap_idare_id, idare_telefon, idare_faks, ust_idare,
  en_ust_idare_kod, en_ust_idare_adi, idare_il, idare_ilce
) ON public.ilanlar FROM anon;

-- AÇIK: ihale niteliği (kişi/kimlik verisi yok). ekap_ihale_id EKAP'ın KENDİ genel
-- doküman sayfasının anahtarıdır ve ihale-detay.html misafirde de kullanır.
GRANT SELECT (
  ekap_ihale_id, usul, son_teklif_tarihi,
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri
) ON public.ilanlar TO anon;
-- KAPALI (bilerek): ekap_idare_id, idare_telefon, idare_faks, ust_idare,
--                   en_ust_idare_kod, en_ust_idare_adi, idare_il, idare_ilce

-- Üye tarafı: authenticated ilanlar'da TABLO-GENELİ SELECT'e sahip → yeni kolonlar
-- ona zaten açık. Aşağısı bir üst küme (no-op); niyeti açıkça kayda geçirir ve
-- ileride biri tablo-geneli yetkiyi daraltırsa üye sayfası sessizce ölmez.
GRANT SELECT (
  ekap_ihale_id, usul, son_teklif_tarihi,
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri,
  ekap_idare_id, idare_telefon, idare_faks, ust_idare,
  en_ust_idare_kod, en_ust_idare_adi, idare_il, idare_ilce
) ON public.ilanlar TO authenticated;

-- ── ihale_sonuclari ────────────────────────────────────────────────────────
REVOKE SELECT (
  ihale_usulu, yasa_madde_kodu, usul_gerekce, isin_yeri, ihale_tarihi,
  dokuman_indiren_sayisi, yerli_fiyat_avantaji, yuklenici_adres, yuklenici_uyruk
) ON public.ihale_sonuclari FROM anon;

GRANT SELECT (
  ihale_usulu, yasa_madde_kodu, isin_yeri, ihale_tarihi,
  dokuman_indiren_sayisi, yerli_fiyat_avantaji
) ON public.ihale_sonuclari TO anon;
-- KAPALI (bilerek):
--   yuklenici_adres → şahıs firmalarında kişisel veri (KVKK)
--   yuklenici_uyruk → yuklenici_* ailesi zaten anon'a kapalı, tutarlılık
--   usul_gerekce    → ihtiyaç duyan yüzey yok; açık yüzeyi bilerek dar tutuyoruz
--   ham_json        → İÇİNDE yüklenici adı + adresi var (zaten kapalı, dokunulmadı)

-- ihale_sonuclari'nda authenticated TABLO düzeyi SELECT'e sahip → yeni kolonlar kapsanır.
GRANT SELECT (
  ihale_usulu, yasa_madde_kodu, usul_gerekce, isin_yeri, ihale_tarihi,
  dokuman_indiren_sayisi, yerli_fiyat_avantaji, yuklenici_adres, yuklenici_uyruk
) ON public.ihale_sonuclari TO authenticated;

-- ── dogrudan_temin_ilanlari ────────────────────────────────────────────────
REVOKE SELECT (
  dt_brans_kodlari, yasa_maddesi, yasa_madde_kodu, kismi_teklif, kisim_sayisi,
  e_ihale, ilan_sekli, sozlesme_tasarisi_var, sozlesme_veya_alim,
  istisna_dayanagi, mevzuat_dayanagi, duyuru_yapilacak, iptal_nedeni, iptal_tarihi,
  en_ust_idare_adi, ust_idare, dt_ilanlar, dt_ilan_tarihi, dt_sonuc_ilan_tarihi,
  detay_cekildi
) ON public.dogrudan_temin_ilanlari FROM anon;
REVOKE SELECT (dt_ilanlar) ON public.dogrudan_temin_ilanlari FROM authenticated;

GRANT SELECT (
  dt_brans_kodlari, yasa_maddesi, yasa_madde_kodu, kismi_teklif, kisim_sayisi,
  e_ihale, ilan_sekli, sozlesme_tasarisi_var, sozlesme_veya_alim,
  istisna_dayanagi, mevzuat_dayanagi, duyuru_yapilacak, iptal_nedeni, iptal_tarihi,
  dt_ilan_tarihi, dt_sonuc_ilan_tarihi, detay_cekildi
) ON public.dogrudan_temin_ilanlari TO anon;
-- KAPALI (bilerek): en_ust_idare_adi, ust_idare (idare kimliği), dt_ilanlar (EncIlanId)

-- Üye: yukarıdakilerin tamamı + idare zinciri (üyeye `idare` zaten açık).
-- dt_ilanlar YİNE KAPALI — token sınıfı altyapı verisi.
GRANT SELECT (
  dt_brans_kodlari, yasa_maddesi, yasa_madde_kodu, kismi_teklif, kisim_sayisi,
  e_ihale, ilan_sekli, sozlesme_tasarisi_var, sozlesme_veya_alim,
  istisna_dayanagi, mevzuat_dayanagi, duyuru_yapilacak, iptal_nedeni, iptal_tarihi,
  en_ust_idare_adi, ust_idare, dt_ilan_tarihi, dt_sonuc_ilan_tarihi, detay_cekildi
) ON public.dogrudan_temin_ilanlari TO authenticated;

-- ── dogrudan_temin_sonuclari ───────────────────────────────────────────────
-- para_birimi bedel sınıfıdır (kimlik değil) → kazanan_bedel ile aynı muamele.
REVOKE SELECT (para_birimi) ON public.dogrudan_temin_sonuclari FROM anon;
GRANT  SELECT (para_birimi) ON public.dogrudan_temin_sonuclari TO anon;
GRANT  SELECT (para_birimi) ON public.dogrudan_temin_sonuclari TO authenticated;

-- ── scraper'ın yazma yetkisi (idempotent güvence) ──────────────────────────
-- service_role'ün bu tablolarda tablo-geneli yetkisi var; yine de açıkça yazıyoruz ki
-- ileride biri tablo-geneli yetkiyi daraltırsa scraper SESSİZCE ölmesin.
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_ilanlari  TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_sonuclari TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.ilanlar                  TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.ihale_sonuclari           TO service_role;

-- ---------------------------------------------------------------------------
-- 1.7) UCUZ KISMİ İNDEKSLER
-- ---------------------------------------------------------------------------
-- CONCURRENTLY KULLANILMADI: bu dosya tek işlemde koşuyor (CONCURRENTLY transaction
-- içinde ÇALIŞMAZ). Sorun değil, çünkü aşağıdakilerin HEPSİ yeni ve şu an %100 NULL
-- olan kolonlar üzerinde KISMİ indeks → sıfır satır kapsarlar ve anında kurulurlar.
-- (Tam tablo taraması yine olur ama indeks derlemesi yoktur; kilit çok kısadır.)
--
-- ⚠ İSTİSNA UYARISI: idx_sonuc_yuklenici_il ve idx_sonuc_is_bitis ÖNCEDEN VAR OLAN
--   kolonlar üzerinde. Denetimde bu kolonların bugüne dek HİÇ yazılmadığı ölçüldü
--   (yeni ayrıştırıcı doldurmaya yeni başlıyor), dolayısıyla onlar da boş kabul
--   edildi. Emin olmak isterseniz migration'dan ÖNCE koşun; 0 dönmüyorsa bu iki
--   satırı ayrı/düşük trafikli bir ana bırakın:
--     SELECT count(*) FILTER (WHERE yuklenici_il  IS NOT NULL) AS il,
--            count(*) FILTER (WHERE is_bitis_tarihi IS NOT NULL) AS bitis
--     FROM public.ihale_sonuclari;
CREATE INDEX IF NOT EXISTS idx_ilanlar_ekap_idare_id
  ON public.ilanlar (ekap_idare_id) WHERE ekap_idare_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ilanlar_iptal_tarihi
  ON public.ilanlar (iptal_tarihi DESC) WHERE iptal_tarihi IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sonuc_ihale_usulu
  ON public.ihale_sonuclari (ihale_usulu) WHERE ihale_usulu IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sonuc_yasa_madde_kodu
  ON public.ihale_sonuclari (yasa_madde_kodu) WHERE yasa_madde_kodu IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sonuc_yuklenici_il
  ON public.ihale_sonuclari (yuklenici_il) WHERE yuklenici_il IS NOT NULL;
-- "sözleşmesi yakında bitecek işler" radarı — yenileme ihalesi öngörüsünün tabanı
CREATE INDEX IF NOT EXISTS idx_sonuc_is_bitis
  ON public.ihale_sonuclari (is_bitis_tarihi DESC) WHERE is_bitis_tarihi IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_brans
  ON public.dogrudan_temin_ilanlari USING GIN (dt_brans_kodlari)
  WHERE dt_brans_kodlari IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_yasa_madde
  ON public.dogrudan_temin_ilanlari (yasa_madde_kodu)
  WHERE yasa_madde_kodu IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 1.8) BEKÇİ — maske yanlışsa COMMIT ETME
-- ---------------------------------------------------------------------------
-- [[http-200-ifsa-degil]] dersinin SQL karşılığı: durum koduna değil, YETKİYE bakıyoruz.
-- has_column_privilege() rol değiştirmeden sorar (SET ROLE'dan temiz).
DO $$
DECLARE
  k    text;
  acik text[] := ARRAY[]::text[];
  eksik text[] := ARRAY[]::text[];
BEGIN
  -- 1) ilanlar: idare kökenli 8 kolon misafire KAPALI olmalı
  FOREACH k IN ARRAY ARRAY['ekap_idare_id','idare_telefon','idare_faks','ust_idare',
                           'en_ust_idare_kod','en_ust_idare_adi','idare_il','idare_ilce']
  LOOP
    IF has_column_privilege('anon','public.ilanlar',k,'SELECT') THEN acik := acik || k; END IF;
  END LOOP;
  IF array_length(acik,1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: ilanlar idare kokenli kolon(lar) anon a ACIK: %', acik;
  END IF;

  -- 2) ilanlar: misafir sayfasının ihtiyaç duyduğu kolonlar AÇIK olmalı
  --    (kapalı kolona WHERE'de dokunmak da 42501 verir → misafirde sayfayı ÖLDÜRÜR)
  FOREACH k IN ARRAY ARRAY['ekap_ihale_id','usul','son_teklif_tarihi','yasa_kapsami',
                           'istisna_usul','iptal_tarihi','iptal_nedeni','iptal_madde',
                           'yeterlik_tarihi','ilk_teklif_tarihi','ihale_tarih_saatleri',
                           'ihale_ozellikleri']
  LOOP
    IF NOT has_column_privilege('anon','public.ilanlar',k,'SELECT') THEN eksik := eksik || k; END IF;
  END LOOP;
  IF array_length(eksik,1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: ilanlar GRANT eksik, anon okuyamiyor: %', eksik;
  END IF;

  -- 3) ilanlar: MEVCUT maske bozulmamış olmalı (regresyon)
  IF has_column_privilege('anon','public.ilanlar','idare','SELECT')
     OR has_column_privilege('anon','public.ilanlar','ekap_id','SELECT') THEN
    RAISE EXCEPTION 'ABORT: ilanlar.idare/ekap_id anon a ACIK — mevcut misafir maskesi bozulmus';
  END IF;

  -- 4) ihale_sonuclari
  acik := ARRAY[]::text[];
  FOREACH k IN ARRAY ARRAY['yuklenici_adres','yuklenici_uyruk','usul_gerekce','ham_json']
  LOOP
    IF has_column_privilege('anon','public.ihale_sonuclari',k,'SELECT') THEN acik := acik || k; END IF;
  END LOOP;
  IF array_length(acik,1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: ihale_sonuclari kisisel/hassas kolon(lar) anon a ACIK: %', acik;
  END IF;
  eksik := ARRAY[]::text[];
  FOREACH k IN ARRAY ARRAY['ihale_usulu','yasa_madde_kodu','isin_yeri','ihale_tarihi',
                           'dokuman_indiren_sayisi','yerli_fiyat_avantaji']
  LOOP
    IF NOT has_column_privilege('anon','public.ihale_sonuclari',k,'SELECT') THEN eksik := eksik || k; END IF;
  END LOOP;
  IF array_length(eksik,1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: ihale_sonuclari GRANT eksik, anon okuyamiyor: %', eksik;
  END IF;
  IF has_column_privilege('anon','public.ihale_sonuclari','kazanan_firma','SELECT') THEN
    RAISE EXCEPTION 'ABORT: ihale_sonuclari.kazanan_firma anon a ACIK — mevcut maske bozulmus';
  END IF;

  -- 5) dogrudan_temin_ilanlari — kimlik/altyapı KAPALI
  IF has_column_privilege('anon','public.dogrudan_temin_ilanlari','en_ust_idare_adi','SELECT')
     OR has_column_privilege('anon','public.dogrudan_temin_ilanlari','ust_idare','SELECT') THEN
    RAISE EXCEPTION 'ABORT: DT ust kurum zinciri anon a ACIK — idare kimligi maskesi delindi';
  END IF;
  IF has_column_privilege('anon','public.dogrudan_temin_ilanlari','dt_ilanlar','SELECT')
     OR has_column_privilege('authenticated','public.dogrudan_temin_ilanlari','dt_ilanlar','SELECT') THEN
    RAISE EXCEPTION 'ABORT: dt_ilanlar acik — EncIlanId erisim hash i sizar';
  END IF;
  IF has_column_privilege('anon','public.dogrudan_temin_ilanlari','idare','SELECT')
     OR has_column_privilege('anon','public.dogrudan_temin_ilanlari','dt_ihale_token','SELECT') THEN
    RAISE EXCEPTION 'ABORT: DT idare/token anon a ACIK — mevcut maske bozulmus';
  END IF;
  -- Mevcut misafir DT sayfası hâlâ çalışmalı
  IF NOT has_column_privilege('anon','public.dogrudan_temin_ilanlari','dt_no','SELECT')
     OR NOT has_column_privilege('anon','public.dogrudan_temin_ilanlari','baslik','SELECT')
     OR NOT has_column_privilege('anon','public.dogrudan_temin_ilanlari','durum','SELECT') THEN
    RAISE EXCEPTION 'ABORT: anon un MEVCUT DT kolon yetkileri kaybolmus — misafir DT sayfasi olurdu';
  END IF;
  IF NOT has_column_privilege('anon','public.dogrudan_temin_ilanlari','dt_brans_kodlari','SELECT') THEN
    RAISE EXCEPTION 'ABORT: dt_brans_kodlari anon a acilamadi';
  END IF;

  -- 6) dogrudan_temin_sonuclari
  IF has_column_privilege('anon','public.dogrudan_temin_sonuclari','kazanan_firma','SELECT') THEN
    RAISE EXCEPTION 'ABORT: DT kazanan_firma anon a ACIK — mevcut maske bozulmus';
  END IF;
  IF NOT has_column_privilege('anon','public.dogrudan_temin_sonuclari','para_birimi','SELECT') THEN
    RAISE EXCEPTION 'ABORT: para_birimi anon a acilamadi';
  END IF;

  -- 7) scraper yazabilmeli (yoksa backfill sessizce hiçbir şey yazmaz)
  IF NOT has_column_privilege('service_role','public.dogrudan_temin_ilanlari','detay_cekildi','UPDATE')
     OR NOT has_column_privilege('service_role','public.ilanlar','ekap_idare_id','UPDATE')
     OR NOT has_column_privilege('service_role','public.ihale_sonuclari','yasa_madde_kodu','INSERT') THEN
    RAISE EXCEPTION 'ABORT: service_role yeni kolonlara yazamiyor — backfill veri yazamazdi';
  END IF;

  RAISE NOTICE 'OK: 47 yeni kolon acildi. Maske saglam — idare/kimlik/kisisel veri KAPALI, ihale nitelikleri ACIK.';
END $$;

COMMIT;

-- PostgREST şema önbelleği: yeni kolonlar ve GRANT'lar görünür olsun.
NOTIFY pgrst, 'reload schema';


-- ###########################################################################
-- BÖLÜM 2 — BOZUK BELGE LİNKLERİNİ ONAR (AĞIR · AYRI İŞLEM · İSTEĞE BAĞLI)
-- ###########################################################################
-- ⚠️ BÖLÜM 1'DEN AYRI TUTULDU ÇÜNKÜ AĞIR: ~1,96M satırda seq scan + jsonb yeniden
--    yazımı. Şema değişikliğini bunun arkasında bekletmek, akan iki backfill'i
--    gereksiz yere kilitlerdi. Bu bir VERİ ONARIMI'dır, şema işi değildir —
--    istediğiniz zaman, tercihen düşük trafikli bir anda ayrıca koşabilirsiniz.
--
-- SORUN: ilanlar.belgeler içindeki url'ler `…/b_ihalearama/api/Dokuman/GetFile?id=…`
-- olarak üretiliyordu. O bir API endpoint'i: imzalı crypto header olmadan 401 döner,
-- yani kullanıcının TARAYICISINDA ÇALIŞMAZ. Çalışan uç EKAP'ın vatandaş doküman
-- sayfasıdır ve kalıcı ihale hash'iyle (ekap_ihale_id) açılır.
--
-- ⚠️ NEDEN GetDokumanUrl'İN DÖNDÜĞÜ HASH SAKLANMIYOR: 29 Tem'de ölçüldü — aynı
--    ihaleId + aynı islemId için ardışık çağrılar FARKLI hash döndürdü (oturumluk
--    token). DB'ye yazılsaydı link bayatlardı. Kalıcı olan liste hash'idir.
--
-- ⚠️ ekap_ihale_id'si NULL olan eski satırlarda bozuk link KALIR — o satırlar için
--    üretilebilecek çalışan bir link yok. Doğrulama sorgusu 0 dönmeyebilir; beklenen.
--
-- Önce kaç satır etkileniyor görün (salt okuma):
--   SELECT count(*) FROM public.ilanlar
--   WHERE belgeler::text LIKE '%/api/Dokuman/GetFile%';
--
-- Sonra AŞAĞIDAKİ BLOĞUN YORUMUNU KALDIRIP koşun:
--
-- BEGIN;
-- UPDATE public.ilanlar i
-- SET belgeler = (
--         SELECT jsonb_agg(
--                  CASE WHEN e->>'url' LIKE '%/api/Dokuman/GetFile%'
--                       THEN jsonb_set(e, '{url}', to_jsonb(
--                              'https://ekap.kik.gov.tr/EKAP/Ortak/VatandasIlanGoruntuleme.aspx'
--                              || '?ddac=true&aramaDownload=true&ihaleId=' || i.ekap_ihale_id
--                              || '&wots=false&Iszylnm=false'))
--                       ELSE e END
--                  ORDER BY ord)
--         FROM jsonb_array_elements(i.belgeler) WITH ORDINALITY AS t(e, ord))
-- WHERE i.ekap_ihale_id IS NOT NULL
--   -- jsonb_typeof guard'ı ŞART: dizi olmayan (çift kodlanmış/bozuk) değerlerde
--   -- jsonb_array_elements sorgunun TAMAMINI düşürürdü.
--   AND jsonb_typeof(i.belgeler) = 'array'
--   AND i.belgeler::text LIKE '%/api/Dokuman/GetFile%';
-- COMMIT;


-- ###########################################################################
-- BÖLÜM 3 — "HÂLÂ EKSİK OLANI BUL" İNDEKSİ (PAHALI · BİLEREK KAPALI)
-- ###########################################################################
-- ⚠️ BU İNDEKS BÖLÜM 1'E ALINMADI. Diğerlerinden farklı olarak kısmi yüklemi
--    ŞU AN ~1,6M satır eşliyor (ekap_ihale_id yalnız %17,7 dolu) → gerçek bir
--    indeks derlemesi, tabloyu yazmaya kapatır ve akan backfill'leri bekletir.
--    Ayrıca backfill kolonu doldurdukça satırlar indeksten düşer (şişme/bakım yükü).
--    Hiçbir kod yolu bu sorguyu ÇALIŞTIRMIYOR — yalnız elle denetim içindi.
--    Gerçekten gerekiyorsa backfill'ler BİTTİKTEN sonra, CONCURRENTLY ile koşun:
--
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_ekap_ihale_id_eksik
--     ON public.ilanlar (ikn) WHERE ekap_ihale_id IS NULL AND kaynak = 'ekap';


-- =============================================================================
-- KONTROL SORGULARI (elle koşun — hiçbiri bu dosya tarafından çalıştırılmaz)
-- =============================================================================
--
-- 1) 47 kolonun hepsi gerçekten açıldı mı (47 beklenir):
--    SELECT count(*) FROM information_schema.columns
--    WHERE table_schema='public' AND (
--       (table_name='ilanlar' AND column_name IN (
--          'yasa_kapsami','istisna_usul','iptal_tarihi','iptal_nedeni','iptal_madde',
--          'yeterlik_tarihi','ilk_teklif_tarihi','ihale_tarih_saatleri','ihale_ozellikleri',
--          'ekap_idare_id','idare_telefon','idare_faks','ust_idare','en_ust_idare_kod',
--          'en_ust_idare_adi','idare_il','idare_ilce'))
--    OR (table_name='ihale_sonuclari' AND column_name IN (
--          'ihale_usulu','yasa_madde_kodu','usul_gerekce','isin_yeri','ihale_tarihi',
--          'dokuman_indiren_sayisi','yerli_fiyat_avantaji','yuklenici_adres','yuklenici_uyruk'))
--    OR (table_name='dogrudan_temin_ilanlari' AND column_name IN (
--          'dt_brans_kodlari','yasa_maddesi','yasa_madde_kodu','kismi_teklif','kisim_sayisi',
--          'e_ihale','ilan_sekli','sozlesme_tasarisi_var','sozlesme_veya_alim',
--          'istisna_dayanagi','mevzuat_dayanagi','duyuru_yapilacak','iptal_nedeni',
--          'iptal_tarihi','en_ust_idare_adi','ust_idare','dt_ilanlar','dt_ilan_tarihi',
--          'dt_sonuc_ilan_tarihi','detay_cekildi'))
--    OR (table_name='dogrudan_temin_sonuclari' AND column_name='para_birimi'));
--
-- 2) ESKİ ADLAR KALMADI mı (0 beklenir — birleştirme sırasında yeniden adlandırıldılar):
--    SELECT table_name, column_name FROM information_schema.columns
--    WHERE table_schema='public'
--      AND (column_name='kanun_maddesi' OR column_name='en_ust_idare');
--
-- 3) Doluluk — backfill ilerledikçe ARTMALI (bugünkü taban: okas %0,62 · kalem %0,41):
--    SELECT count(*) FILTER (WHERE okas IS NOT NULL)           AS okas,
--           count(*) FILTER (WHERE kalemler IS NOT NULL)       AS kalem,
--           count(*) FILTER (WHERE ekap_ihale_id IS NOT NULL)  AS ihale_hash,
--           count(*) FILTER (WHERE ekap_idare_id IS NOT NULL)  AS idare_id,
--           count(*) FILTER (WHERE iptal_tarihi IS NOT NULL)   AS iptal,
--           count(*) AS toplam
--    FROM public.ilanlar;
--
--    SELECT count(*) FILTER (WHERE katilimci_sayisi IS NOT NULL)       AS katilimci,
--           count(*) FILTER (WHERE dokuman_indiren_sayisi IS NOT NULL) AS indiren,
--           count(*) FILTER (WHERE is_bitis_tarihi IS NOT NULL)        AS is_bitis,
--           count(*) AS toplam
--    FROM public.ihale_sonuclari;
--
--    SELECT count(*) FILTER (WHERE dt_brans_kodlari IS NOT NULL) AS brans,
--           count(*) FILTER (WHERE detay_cekildi IS NOT NULL)    AS detayli,
--           count(*) FILTER (WHERE kazanan_denendi IS NOT NULL)  AS damgali,
--           count(*) AS toplam
--    FROM public.dogrudan_temin_ilanlari;
--
-- 4) İPTAL DÖNÜŞÜMÜ YAPILMADI mı (0 beklenir — proje kararı):
--    SELECT count(*) FROM public.ilanlar WHERE iptal_tarihi IS NOT NULL AND durum='iptal';
--
-- 5) Misafir maskesi — GÖVDEYE bakın, sadece HTTP koduna DEĞİL ([[http-200-ifsa-degil]]):
--    KAPALI olmalı (42501 beklenir):
--      /rest/v1/ilanlar?select=idare_telefon&limit=1
--      /rest/v1/ilanlar?select=ekap_idare_id&limit=1
--      /rest/v1/ihale_sonuclari?select=yuklenici_adres&limit=1
--      /rest/v1/dogrudan_temin_ilanlari?select=en_ust_idare_adi&limit=1
--      /rest/v1/dogrudan_temin_ilanlari?select=dt_ilanlar&limit=1
--    AÇIK olmalı (200 beklenir):
--      /rest/v1/ilanlar?select=yasa_kapsami,iptal_tarihi,ihale_ozellikleri&limit=1
--      /rest/v1/ihale_sonuclari?select=ihale_usulu,yasa_madde_kodu,dokuman_indiren_sayisi&limit=1
--      /rest/v1/dogrudan_temin_ilanlari?select=dt_no,dt_brans_kodlari,yasa_madde_kodu&limit=1
--      /rest/v1/dogrudan_temin_sonuclari?select=para_birimi&limit=1
--    REGRESYON (misafir sayfaları hâlâ çalışıyor mu — 200 beklenir):
--      /rest/v1/dogrudan_temin_ilanlari?select=dt_no,baslik,durum,il&limit=1
-- =============================================================================
