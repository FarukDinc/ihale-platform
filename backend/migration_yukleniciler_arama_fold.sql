-- ============================================================================
-- migration_yukleniciler_arama_fold.sql
-- Firma Analizi redesign (ihaleciler.com modeli): arama → yukleniciler'den AYRI
-- firmaların listesi. Arama Türkçe katlamalı olmalı ("dinç" → "DİNÇ GRUP..."
-- bulmalı; şu an İ/ç yüzünden 0 dönüyor). tr_fold() zaten prod'da mevcut.
--
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION tr_fold(s text)
  RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT lower(translate(coalesce(s, ''), 'İIıŞşĞğÜüÖöÇç', 'iiissgguuoocc')); $$;

ALTER TABLE yukleniciler
  ADD COLUMN IF NOT EXISTS arama_fold text
  GENERATED ALWAYS AS (tr_fold(ad)) STORED;

CREATE INDEX IF NOT EXISTS idx_yukleniciler_arama_fold_trgm
  ON yukleniciler USING gin (arama_fold gin_trgm_ops);

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT ad, toplam_sozlesme_sayisi FROM yukleniciler
--   WHERE arama_fold ILIKE '%dinc%' ORDER BY toplam_ciro DESC LIMIT 5;
