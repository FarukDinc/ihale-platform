-- ============================================================================
-- migration_harita_firma_mv.sql — Harita sektör katmanı: canlı aggregate → MV (16 Tem 2026)
--
-- Kök neden (canlıda ölçüldü): harita.html'in sektör katmanı iki AĞIR canlı
-- aggregate'e dayanıyordu (ihale_sonuclari 529K ⋈ ilanlar 355K):
--   - il_sektor_ozet(): sektör seçilince 9.2sn (tarayıcı ölçümü, sıcakken!)
--   - il_sektor_firmalar(): ile tıklayınca sıcak ~1.8sn, SOĞUKTA 57014
--     statement timeout → panel "Yüklenemedi"/takılı ("bir ile tıklayın" şikayeti).
-- ALTER SET statement_timeout (30s/15s) semptomu erteliyor, beklemeyi çözmüyor.
--
-- Çözüm — idare_ozet_mv ile bugün kanıtlanan desen: il×kategori×firma kırılımı
-- il_sektor_firma_mv'de ÖNCEDEN hesaplanır (gece run_scraper.sh sonunda REFRESH
-- CONCURRENTLY — sonuç verisi zaten yalnız gece backfill'de değişir). Her iki RPC
-- de İMZA DEĞİŞMEDEN MV'den okur hale gelir → frontend değişikliği YOK, tıklama
-- soğuk/sıcak fark etmeksizin ~ms.
--
-- Bilinçli semantik düzeltme: il_sektor_ozet.firma_adet artık normalize_firma
-- bazlı distinct (eskiden yuklenici_id-veya-ham-ad idi) → ünvan varyantları
-- birleşir, sayılar il_sektor_firmalar listesiyle TUTARLI olur (biraz düşebilir).
-- 'Diğer' kategorisi: boş/NULL kategori her iki RPC'de de 'Diğer'e katlanır
-- (eski il_sektor_firmalar raw eşleşiyordu → 'Diğer' tıklaması NULL'ları kaçırıyordu).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_harita_firma_mv.sql
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. İlk MV build'i normalize_firma
-- 529K çağrısı nedeniyle birkaç dakika sürebilir (yuklenici_yenile ölçeği).
-- ============================================================================

-- 1) MV: il × kategori × normalize_firma kırılımı
CREATE MATERIALIZED VIEW IF NOT EXISTS public.il_sektor_firma_mv AS
SELECT i.il                                                                    AS il,
       tr_fold(i.il)                                                           AS il_fold,
       COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer')                        AS kategori,
       normalize_firma(s.kazanan_firma)                                        AS firma_norm,
       (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS ad,
       max(s.sonuc_tarihi)                                                     AS son_tarih,
       count(*)::bigint                                                        AS sozlesme,
       sum(COALESCE(s.kazanan_teklif, 0))                                      AS toplam_bedel
FROM public.ihale_sonuclari s
JOIN public.ilanlar i ON i.id = s.ilan_id
WHERE s.kazanan_firma IS NOT NULL
  AND i.il IS NOT NULL AND btrim(i.il) <> ''
  AND normalize_firma(s.kazanan_firma) IS NOT NULL
GROUP BY i.il, tr_fold(i.il),
         COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer'),
         normalize_firma(s.kazanan_firma);

-- REFRESH CONCURRENTLY şartı (grup anahtarı = doğal unique)
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_firma_mv_pk
  ON public.il_sektor_firma_mv (il, kategori, firma_norm);
-- il_sektor_firmalar erişim yolu
CREATE INDEX IF NOT EXISTS idx_il_sektor_firma_mv_fold
  ON public.il_sektor_firma_mv (il_fold, kategori);

ANALYZE public.il_sektor_firma_mv;

GRANT SELECT ON public.il_sektor_firma_mv TO anon, authenticated, service_role;

-- 2) il_sektor_ozet(): aynı jsonb çıktı, artık MV'den (~ms). İmza/format aynı.
CREATE OR REPLACE FUNCTION public.il_sektor_ozet()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
           'il', il, 'kategori', kategori, 'firma_adet', firma_adet,
           'sozlesme_adet', sozlesme_adet, 'toplam_bedel', toplam_bedel)), '[]'::jsonb)
  FROM (
    SELECT il, kategori,
           count(*)::bigint      AS firma_adet,
           sum(sozlesme)::bigint AS sozlesme_adet,
           sum(toplam_bedel)     AS toplam_bedel
    FROM public.il_sektor_firma_mv
    GROUP BY il, kategori
  ) t;
$$;
-- CREATE OR REPLACE proconfig'i sıfırlar → timeout güvencesini yeniden koy
ALTER FUNCTION public.il_sektor_ozet() SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_ozet() TO anon, authenticated, service_role;

-- 3) il_sektor_firmalar(): aynı imza, MV'den. Kategori NULL = il genelinde
--    firma bazında topla; görünen ad en güncel sonuçtaki ham ünvan.
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8
)
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE
AS $$
  SELECT (array_agg(ad ORDER BY son_tarih DESC NULLS LAST))[1] AS ad,
         sum(sozlesme)::bigint AS sozlesme,
         sum(toplam_bedel)     AS toplam_bedel
  FROM public.il_sektor_firma_mv
  WHERE il_fold = ANY(p_il_folds)
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY firma_norm
  ORDER BY sum(toplam_bedel) DESC, sum(sozlesme) DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
ALTER FUNCTION public.il_sektor_firmalar(text[], text, int) SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol
SELECT count(*) AS mv_satir FROM public.il_sektor_firma_mv;
SELECT jsonb_array_length(public.il_sektor_ozet()) AS ozet_grup;
SELECT * FROM public.il_sektor_firmalar(ARRAY['ankara'], NULL, 3);
