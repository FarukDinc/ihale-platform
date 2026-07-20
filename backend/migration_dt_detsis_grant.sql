-- ============================================================================
-- `dogrudan_temin_ilanlari.detsis_no` → authenticated'a GRANT SELECT
--
-- BULUNUŞ (20 Tem): migration_hiyerarsifiltre.sql kendi doğrulama bloğuyla
-- uygulanmayı REDDETTİ — "authenticated dogrudan_temin_ilanlari.detsis_no
-- okuyamiyor". İşlem geri alındı, yani guard tam olarak işini yaptı.
--
-- KÖK NEDEN — bu projede DÖRDÜNCÜ kez: kolon-seviyesi GRANT'lar SONRADAN eklenen
-- kolonlara genişlemez. `detsis_no` DT tablosuna idare hiyerarşisi işiyle birlikte
-- sonradan eklendi; `ilanlar.detsis_no` GRANT edilmişti (anon=f, authenticated=t)
-- ama DT'deki kardeşi unutulmuştu (anon=f, authenticated=f).
--
-- POLİTİKA: `ilanlar.detsis_no` ile BİREBİR aynı — üyeye açık, misafire kapalı.
-- Hiyerarşi filtresi zaten üyeye özel bir gezinme aracı; misafirde idare adı
-- maskeli olduğu için detsis_no'yu açmanın da anlamı yok.
--
-- Çalıştırma (VDS):
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_detsis_grant.sql
-- Ardından migration_hiyerarsifiltre.sql tekrar koşulabilir.
-- ============================================================================

BEGIN;

GRANT SELECT (detsis_no) ON public.dogrudan_temin_ilanlari TO authenticated;

DO $$
BEGIN
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'detsis_no', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated hala DT.detsis_no okuyamiyor';
  END IF;
  -- Misafir tarafı DEĞİŞMEMELİ: idare maskesi bu tabloda hâlâ geçerli olmalı.
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon DT.idare okuyabiliyor — maske delinmis';
  END IF;
  RAISE NOTICE 'OK: DT.detsis_no uyeye acik, misafir maskesi saglam';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';
