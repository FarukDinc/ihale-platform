-- ============================================================================
-- migration_idare_tur_fix.sql — idare_normalize şema niteleme düzeltmesi
--
-- SORUN: migration_idare_tur.sql'de idare_normalize() gövdesinde tr_fold()
--   ŞEMA ADI OLMADAN çağrılıyordu. Fonksiyonun kendisi oluştu ama `ilanlar`
--   üzerindeki İFADE İNDEKSİ kurulurken inlining sırasında search_path farklı
--   olduğu için:
--       ERROR: function tr_fold(text) does not exist
--   → indeks OLUŞMADI. İndekssiz kalırsa idare_tur_bosluk()/kapsama() 350K+
--     satırda satır-başı fonksiyon çağırır ve timeout'a girer.
--
-- DERS: IMMUTABLE + ifade indeksinde kullanılacak fonksiyonların gövdesindeki
--   TÜM çağrılar şema-nitelikli olmalı (public.tr_fold), yoksa index build
--   ortamında çözülemez.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_tur_fix.sql
-- ============================================================================

-- 1) tr_fold gerçekten var mı? (yoksa burada tanımla — ilanlar.arama_fold ile aynı gövde)
CREATE OR REPLACE FUNCTION public.tr_fold(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT lower(translate(coalesce(s, ''),
    'İIıŞşĞğÜüÖöÇç',
    'iiissgguuoocc'));
$$;

-- 2) idare_normalize — ŞEMA NİTELİKLİ çağrı ile yeniden tanımla
CREATE OR REPLACE FUNCTION public.idare_normalize(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT btrim(regexp_replace(
           regexp_replace(public.tr_fold(coalesce(s, '')), '[^a-z0-9]+', ' ', 'g'),
           '\s+', ' ', 'g'));
$$;

-- 3) İfade indeksi (bu sefer kurulmalı)
CREATE INDEX IF NOT EXISTS idx_ilanlar_idare_norm
  ON public.ilanlar (public.idare_normalize(idare));

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT public.idare_normalize('T.C. ANKARA BÜYÜKŞEHİR BELEDİYESİ');
--     → 'tc ankara buyuksehir belediyesi'
--   SELECT indexname FROM pg_indexes WHERE indexname='idx_ilanlar_idare_norm';
--     → 1 satır dönmeli
