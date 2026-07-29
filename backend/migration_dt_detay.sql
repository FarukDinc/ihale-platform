-- ⛔⛔ BU DOSYA ARTIK KOŞULMAMALI — migration_ekap_hasat.sql İLE BİRLEŞTİRİLDİ (29 Tem 2026)
--
-- 4 ayrı çalışmanın önerdiği kolonlar TEK migration'da toplandı:
--     backend/migration_ekap_hasat.sql
-- Birleştirme sırasında İKİ KOLON YENİDEN ADLANDIRILDI (iki ajan aynı anlamı
-- farklı adla önermişti):
--     kanun_maddesi  → yasa_madde_kodu   (ihale_sonuclari)
--     en_ust_idare   → en_ust_idare_adi  (dogrudan_temin_ilanlari)
-- İlgili .py dosyaları YENİ adlara göre düzeltildi. Bu dosya koşulursa ESKİ adlı,
-- hiçbir kodun YAZMADIĞI ölü kolonlar oluşur ve maske bekçileri şaşar.
--
-- Tarihsel kayıt olarak duruyor; çalıştırılmasın diye aşağıda ABORT var.
DO $$
BEGIN
  RAISE EXCEPTION 'BU DOSYA DEVRE DISI: migration_ekap_hasat.sql ile birlestirildi. Onu kosun.';
END $$;

-- ============================================================================
-- migration_dt_detay.sql — dtDetayGetir'in ATILAN 3 bloğu için yazma alanı (29 Tem 2026)
--
-- BULGU: dt_kazanan_scraper.py, EKAP'ın dtDetayGetir yanıtından yalnız
--   dogrudanTeminDetayResult.SozlesmeBilgileri.SozlesmeBilgisiList
-- okuyordu. Yanıtta 4 blok var; 3'ü OKUNMADAN ATILIYORDU:
--
--   1) DogrudanTeminBilgileri (18 alan) — en değerlisi BransKodList: DT'nin OKAS'ı.
--      DT ilanlarında OKAS YOK diye kategori bugüne kadar yalnız başlıktan tahmin
--      ediliyor (ekap_dogrudan_temin_scraper.py:191 → kategori_belirle(None, tur, baslik));
--      oysa EKAP bu kaydın CPV kodunu ("33194120", "44316400" — canlı doğrulandı)
--      aynı yanıtta ZATEN veriyordu. Ayrıca 22-d / 22-c ayrımı (YasaKapsamiTeminMaddesi),
--      KismiTeklif, KisimSayisi, EIhale, IptalNedeni/IptalTarihi hep buradaydı.
--   2) IdareBilgileri — EnUstIdare/UstIdare, yani idarenin ÜÇ KADEMELİ zinciri.
--      İdare türü sınıflandırıcısının (813K sınıfsız satır) elle kural yazarak
--      çıkarmaya çalıştığı üst-kurum zinciri, DT tarafında hazır geliyordu.
--   3) IlanBilgileri — 4 ilan listesi (duyuru/düzeltme/iptal/sonuç) ve her birinde
--      EncIlanId (64 haneli EKAP hash'i) → belge/ilan derin linki. `tum_teklifler`
--      içindeki EKAP hash'inin 336K belge linkini bedavaya doldurmasıyla AYNI desen.
--
-- ⏰ ACİLİYET: bu bloklar EK İSTEK GEREKTİRMEZ — zaten çekilen yanıtın içindeler.
--    815.895 DT kaydı eski (detaysız) kodla `kazanan_denendi` damgası yediği için
--    kuyruktan düştü; kalan ~1,62M kayıt için pencere AÇIK ama gece cron'u kuyruğu
--    her gece eritiyor. Damgalı-ama-detaysız satırları geri kazanmak için
--    ayrı bir dosya var: backend/migration_dt_detay_kurtarma.sql (BU DOSYA DEĞİL).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_detay.sql
-- Idempotent: ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS / GRANT. Tekrarı zararsız.
--
-- ⚠️ KOD İLE SIRALAMA SERBEST: dt_kazanan_scraper.py bu migration'a BAĞIMLI DEĞİL.
--    Tur başında kolonların varlığını bir kez sınar (sema_sinama), yoksa yeni alanları
--    HİÇ göndermez ve birebir eski davranışla çalışır. Yani "önce kod mu, önce migration
--    mı" sorusu yok; backfill sürerken `git pull` yapılsa da tur çökmez.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) dogrudan_temin_ilanlari — blok 1/2/3 (dt_no başına TEK satır, 1:1)
-- ---------------------------------------------------------------------------
-- NOT: Zaten yakalanan alanlar BİLEREK tekrarlanmadı —
--   Dtn=dt_no, IsinAdi=baslik(E2), Turu=tur(E4), DtTarihSaati=tarih(E7),
--   DtDurumu=durum(E9), IdareBilgileri.Idare=idare(E3), .Ili=il(E12).
-- Hepsi liste yanıtından (dtAra) zaten geliyor; detaydan tekrar yazmak
-- kuyruk filtresini (durum IN (...)) tur ortasında kaydırma riski taşırdı.
ALTER TABLE public.dogrudan_temin_ilanlari
  -- ── blok 1: DogrudanTeminBilgileri ────────────────────────────────────────
  -- BransKodList: DT'nin OKAS/CPV'si. Bir DT birden çok branş kodu taşıyabilir
  -- (canlıda tek elemanlı görüldü ama alan DİZİ) → text[]; eşleştirme motoru
  -- `dt_brans_kodlari && ARRAY[...]` / PostgREST `cs.{kod}` ile sorgulayabilsin.
  ADD COLUMN IF NOT EXISTS dt_brans_kodlari      TEXT[],
  -- Ham metin: '22-d* (Parasal Limit Kapsamında)' — kayıpsız saklanır.
  ADD COLUMN IF NOT EXISTS yasa_maddesi          TEXT,
  -- Ham metinden türetilen kanonik kod: '22-d' / '22-c'. Filtrelenebilir olsun diye
  -- AYRI kolon; kalıp tutmazsa NULL kalır (uydurma değer üretilmez).
  ADD COLUMN IF NOT EXISTS yasa_madde_kodu       TEXT,
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
  -- ⚠️ KİMLİK VERİSİ: `idare` ile aynı sınıf → anon'a KAPALI kalmalı (aşağıya bak).
  ADD COLUMN IF NOT EXISTS en_ust_idare          TEXT,
  ADD COLUMN IF NOT EXISTS ust_idare             TEXT,
  -- ── blok 3: IlanBilgileri ─────────────────────────────────────────────────
  -- 4 listenin tamamı ham jsonb: {DogrudanTeminIlanBilgisiList, DuzeltmeIlanBilgisiList,
  -- IptalIlanBilgisiList, SonucIlanBilgisiList}, her eleman {IlanTarihi, IlanTipi, EncIlanId}.
  -- ⚠️ EncIlanId = EKAP erişim hash'i (dt_ihale_token ile AYNI sınıf: saf altyapı,
  --    frontend'in ihtiyacı yok) → anon VE authenticated'a KAPALI, yalnız service_role.
  ADD COLUMN IF NOT EXISTS dt_ilanlar            JSONB,
  -- jsonb'ye inmeden sorgulanabilsin diye denormalize edilmiş en erken tarihler.
  -- yayin_tarihi (E8) ile KARIŞTIRMAYIN: o duyurunun liste yanıtındaki yayın günü.
  ADD COLUMN IF NOT EXISTS dt_ilan_tarihi        TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS dt_sonuc_ilan_tarihi  TIMESTAMPTZ,
  -- ── işleme damgası ────────────────────────────────────────────────────────
  -- kazanan_denendi'den AYRI olmak ZORUNDA: 815.895 satır ESKİ (detaysız) kodla
  -- damgalandı. "Detay bloklarıyla birlikte işlendi mi?" sorusunun tek yanıtı bu
  -- kolondur; kurtarma sorgusu (migration_dt_detay_kurtarma.sql) buna dayanır.
  ADD COLUMN IF NOT EXISTS detay_cekildi         TIMESTAMPTZ;

-- ---------------------------------------------------------------------------
-- 2) dogrudan_temin_sonuclari — SozlesmeBedeli'nin para birimi
-- ---------------------------------------------------------------------------
-- bedel_parse() 'TL'/'TRY'/'₺' eklerini SİLİP sayıya çeviriyor; TRY dışı bir bedel
-- ('1.000,00 USD') float()'ta patlayıp NULL'a düşüyor ve HANGİ para biriminde
-- olduğu tümden kayboluyordu. Ham metinden okunan kod artık ayrı kolonda.
ALTER TABLE public.dogrudan_temin_sonuclari
  ADD COLUMN IF NOT EXISTS para_birimi TEXT;

-- ---------------------------------------------------------------------------
-- 3) İndeksler — HEPSİ KISMİ (partial), bilerek
-- ---------------------------------------------------------------------------
-- dogrudan_temin_ilanlari ~2,4M satır ve bu migration CONCURRENTLY kullanmıyor
-- (tek işlemde koşuyor) → tam indeks derlemesi tabloyu yazmaya kapatırdı ve gece
-- cron'u ile çakışabilirdi. Uygulama anında bu kolonların TAMAMI NULL olduğu için
-- `WHERE ... IS NOT NULL` kısmi indeksleri SIFIR satır kapsar ve ANINDA kurulur;
-- scraper veri yazdıkça indeks kendiliğinden büyür.
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_brans
  ON public.dogrudan_temin_ilanlari USING GIN (dt_brans_kodlari)
  WHERE dt_brans_kodlari IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_yasa_madde
  ON public.dogrudan_temin_ilanlari (yasa_madde_kodu)
  WHERE yasa_madde_kodu IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 4) YETKİLER — ⚠️ BU TABLOLARDA "ÖNCE REVOKE" KALIBI UYGULANMAZ
-- ---------------------------------------------------------------------------
-- Projenin genel kuralı "yeni kolon anon'a açık doğar → önce REVOKE, sonra dar GRANT"
-- YENİ TABLOLAR içindir (ALTER DEFAULT PRIVILEGES tablo-geneli GRANT verir).
-- Burada tablolar ZATEN VAR ve anon/authenticated'ın tablo-geneli yetkisi YOK,
-- yalnız KOLON-BAZLI yetkileri var (canlı doğrulandı: anon `select=*` → 42501).
-- Bu durumda:
--   · Yeni kolon BOŞ ACL ile doğar → anon/authenticated OTOMATİK GÖREMEZ (güvenli yön).
--   · `REVOKE SELECT ON <tablo> FROM anon` YAZMAK FELAKET OLURDU: mevcut kolon
--     yetkilerini de silip misafir DT sayfasını tümden 42501'e düşürürdü.
-- Bu yüzden aşağısı SALT EKLEMELİ (additive) GRANT'tir; hiçbir REVOKE yok.
-- (Bkz. hafıza: anon-maske-iki-kok-neden — "SONRADAN eklenen kolon kolon-GRANT'a
--  girmez → misafirde sayfayı ÖLDÜRÜR". Çare kolonu açmak, maskeyi yıkmak DEĞİL.)

-- anon (misafir): kimlik OLMAYAN alanlar. Proje ilkesi "sayılar/tarihler/bayraklar
-- misafire açık, kimlik kapalı".
-- KAPALI BIRAKILANLAR (bilinçli): en_ust_idare, ust_idare (idare kimliği — `idare`
-- ile aynı sınıf), dt_ilanlar (EncIlanId = EKAP erişim hash'i, altyapı).
GRANT SELECT (
  dt_brans_kodlari, yasa_maddesi, yasa_madde_kodu, kismi_teklif, kisim_sayisi,
  e_ihale, ilan_sekli, sozlesme_tasarisi_var, sozlesme_veya_alim,
  istisna_dayanagi, mevzuat_dayanagi, duyuru_yapilacak, iptal_nedeni, iptal_tarihi,
  dt_ilan_tarihi, dt_sonuc_ilan_tarihi, detay_cekildi
) ON public.dogrudan_temin_ilanlari TO anon;

-- authenticated (üye): yukarıdakilerin tamamı + idare zinciri (üyeye `idare` zaten açık).
-- dt_ilanlar YİNE KAPALI — token sınıfı veri.
GRANT SELECT (
  dt_brans_kodlari, yasa_maddesi, yasa_madde_kodu, kismi_teklif, kisim_sayisi,
  e_ihale, ilan_sekli, sozlesme_tasarisi_var, sozlesme_veya_alim,
  istisna_dayanagi, mevzuat_dayanagi, duyuru_yapilacak, iptal_nedeni, iptal_tarihi,
  en_ust_idare, ust_idare, dt_ilan_tarihi, dt_sonuc_ilan_tarihi, detay_cekildi
) ON public.dogrudan_temin_ilanlari TO authenticated;

-- service_role'ün bu tabloda tablo-geneli SELECT/INSERT/UPDATE'i var (yeni kolonlar
-- otomatik kapsanır); yine de açıkça yazıyoruz — idempotent, ileride biri
-- tablo-geneli yetkiyi daraltırsa scraper sessizce ölmesin.
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_ilanlari TO service_role;

-- dogrudan_temin_sonuclari.para_birimi: bedel/tarih sınıfı (kimlik değil) → anon'a açık,
-- kazanan_bedel ile birebir aynı muamele (migration_dt_anon_fix.sql'deki liste).
GRANT SELECT (para_birimi) ON public.dogrudan_temin_sonuclari TO anon;
GRANT SELECT (para_birimi) ON public.dogrudan_temin_sonuclari TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_sonuclari TO service_role;

-- ---------------------------------------------------------------------------
-- 5) DOĞRULAMA — yanlışsa COMMIT ETME
-- ---------------------------------------------------------------------------
-- has_column_privilege() rol değiştirmeden yetkiyi sorar (SET ROLE'dan temiz).
-- HTTP 200 ≠ ifşa dersinin SQL karşılığı: durum koduna değil, yetkiye bakıyoruz.
DO $$
BEGIN
  -- 5a) Kimlik/altyapı kolonları anon'a KAPALI olmalı
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'en_ust_idare', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: en_ust_idare anon a ACIK — idare kimligi maskesi delindi';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'ust_idare', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: ust_idare anon a ACIK — idare kimligi maskesi delindi';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_ilanlar', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: dt_ilanlar anon a ACIK — EncIlanId erisim hash i sizar';
  END IF;
  IF has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'dt_ilanlar', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: dt_ilanlar authenticated a ACIK — EncIlanId erisim hash i sizar';
  END IF;

  -- 5b) Mevcut maske BOZULMAMIŞ olmalı (bu migration hiçbir REVOKE yapmıyor;
  --     yine de yanlışlıkla bir REVOKE eklenirse burada yakalanır)
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: idare anon a ACIK — migration_anon_maske.sql maskesi bozulmus';
  END IF;
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_no', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'baslik', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'durum', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: anon un MEVCUT kolon yetkileri kaybolmus — misafir DT sayfasi olurdu';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_sonuclari', 'kazanan_firma', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: kazanan_firma anon a ACIK — migration_dt_anon_fix.sql maskesi bozulmus';
  END IF;

  -- 5c) Yeni kolonlar gerçekten açılmış olmalı (sessizce eksik kalmasın)
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_brans_kodlari', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: dt_brans_kodlari anon a acilamadi';
  END IF;
  IF NOT has_column_privilege('service_role', 'public.dogrudan_temin_ilanlari', 'detay_cekildi', 'UPDATE') THEN
    RAISE EXCEPTION 'ABORT: service_role detay_cekildi yazamaz — scraper damgalayamaz';
  END IF;

  RAISE NOTICE 'migration_dt_detay: 20 kolon (ilanlari) + 1 kolon (sonuclari) hazir, maske saglam.';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- SONRAKİ ADIMLAR (bu dosya YAPMAZ — bilinçli)
-- ============================================================================
-- 1) migration_anon_maske.sql ve migration_dt_token_authenticated.sql'in kara
--    listeleri bu commit'te GÜNCELLENDİ (en_ust_idare/ust_idare/dt_ilanlar eklendi).
--    O iki dosya "tüm kolonlar EKSİ kara liste" mantığıyla çalışır; güncellenmeselerdi
--    bir dahaki koşuşta yeni kimlik kolonlarını anon'a SESSİZCE AÇARLARDI.
-- 2) Eski (detaysız) kodla damgalanmış 815.895 satırı geri kazanmak için:
--    backend/migration_dt_detay_kurtarma.sql — AYRI dosya, kasıtlı olarak burada değil
--    (yüz binlerce satırı kuyruğa geri koyar; ne zaman koşulacağı ayrı bir karar).
--
-- Doğrulama (canlı, anon anahtarıyla — 200 vs 401'e DEĞİL GÖVDEYE bakın):
--   curl -s "$URL/rest/v1/dogrudan_temin_ilanlari?select=dt_no,dt_brans_kodlari&limit=1" ...  # 200
--   curl -s "$URL/rest/v1/dogrudan_temin_ilanlari?select=en_ust_idare&limit=1" ...            # 401/42501
--   curl -s "$URL/rest/v1/dogrudan_temin_ilanlari?select=dt_ilanlar&limit=1" ...              # 401/42501
--   curl -s "$URL/rest/v1/dogrudan_temin_ilanlari?select=dt_no,baslik,durum,il&limit=1" ...   # 200 (regresyon)
