-- ============================================================
-- İhaleGlobal — Eşik (sınır değer) katsayısı backfill
--
-- ekap_scraper.py'deki ESIK_KATSAYI_RE düzeltildi (bare integer "1" artık
-- eşleşiyor). Bu, GELECEKTEKİ scrape'leri düzeltir ama var olan kayıtları
-- doldurmaz. Bu backfill, ilan_metni'nde katsayı geçen ama esik_katsayi'si
-- NULL olan mevcut ilanları düzeltilmiş desenle yeniden ayrıştırır.
--
-- Additive/güvenli: SADECE esik_katsayi NULL olan satırları günceller,
-- yalnızca metinde gerçekten eşleşme varsa (WHERE ~* guard). Başka veri
-- dokunulmaz. Python ESIK_KATSAYI_RE ile aynı desen (senkron).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_esik_katsayi_backfill.sql
-- ============================================================

BEGIN;

UPDATE public.ilanlar
SET esik_katsayi = replace(
      (regexp_match(
         ilan_metni,
         'sınır\s*değer\s*katsayısı\s*\(?\s*n\s*\)?\s*[:=;]\s*(\d+(?:[.,]\d+)?)',
         'i'
      ))[1], ',', '.')::numeric
WHERE esik_katsayi IS NULL
  AND ilan_metni IS NOT NULL
  AND ilan_metni ~* 'sınır\s*değer\s*katsayısı\s*\(?\s*n\s*\)?\s*[:=;]\s*\d';

COMMIT;

-- Kontrol: kaç aktif Yapım ihalesinde katsayı artık dolu
SELECT
  count(*) FILTER (WHERE esik_katsayi IS NOT NULL) AS dolu,
  count(*)                                          AS toplam
FROM public.ilanlar
WHERE durum = 'aktif' AND tur ILIKE '%yapım%';
