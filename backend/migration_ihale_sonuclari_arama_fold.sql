-- ============================================================================
-- migration_ihale_sonuclari_arama_fold.sql
-- firma-analiz.html bug: kullanıcı firma isminde geçen bir kelimeyi (örn.
-- "yavcin" için "Yavçin") yazınca ILIKE Türkçe katlamadığı için 0 sonuç
-- dönüyordu (ihaleler.html'in 10. bug'ıyla aynı kök neden — bkz.
-- migration_ilanlar_arama_fold.sql). Aynı çözüm burada ihale_sonuclari.kazanan_firma
-- için uygulanıyor: tr_fold() zaten prod'da var (yeniden CREATE etmek zararsız/idempotent).
--
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrar çalıştırmak zararsız.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- tr_fold() migration_ilanlar_arama_fold.sql'de tanımlı — burada da idempotent
-- olarak garanti altına alınıyor (bu migration tek başına da çalıştırılabilsin diye).
CREATE OR REPLACE FUNCTION tr_fold(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT lower(translate(coalesce(s, ''),
    'İIıŞşĞğÜüÖöÇç',
    'iiissgguuoocc'));
$$;

ALTER TABLE ihale_sonuclari
  ADD COLUMN IF NOT EXISTS kazanan_firma_fold text
  GENERATED ALWAYS AS (tr_fold(kazanan_firma)) STORED;

CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_kazanan_firma_fold_trgm
  ON ihale_sonuclari USING gin (kazanan_firma_fold gin_trgm_ops);

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM ihale_sonuclari WHERE kazanan_firma_fold ILIKE '%yavcin%';
