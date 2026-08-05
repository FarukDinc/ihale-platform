-- =============================================================================
-- migration_idare_dedup_detsis.sql — Kurum dedup: aynı DETSİS'li isim varyantlarını tek kurum say (5 Ağu)
-- =============================================================================
-- SORUN: "Tüm Kurumlar" isme göre gruplu → aynı kurum farklı yazımla 2 satır.
--   Ör. BEL-PA: "BEL-PA ANKARA…" (18 ihale) + "ANKARA BÜYÜKŞEHİR BELEDİYE BAŞK… - BEL-PA…" (9 ihale)
--   AMA ikisinin de detsis_no'su AYNI: 87767631. Sistem zaten aynı kurum biliyor.
-- ÇÖZÜM (İKİ EVREN Kural 1 — kurum kanonik anahtarı = detsis_no): idare_ozet_mv'ye detsis_no ekle,
--   idare_dizin_json çıktısına taşı, frontend detsis_no'ya göre grupla (isme değil).
-- NOT: idare_harcama_mv OKUMASI aynen korunur (parse-oturumunun değişikliğine dokunma).
-- Uygula: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_dedup_detsis.sql
-- =============================================================================

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS public.idare_ozet_mv;
CREATE MATERIALIZED VIEW public.idare_ozet_mv AS
SELECT idare,
  count(*)                                                                       AS toplam,
  count(*) FILTER (WHERE durum = 'aktif' AND son_teklif_tarihi >= now())         AS aktif,
  mode() WITHIN GROUP (ORDER BY il)                                             AS en_yakin_il,
  max(detsis_no)                                                                AS detsis_no  -- isim→detsis (isim başına tekil; dedup anahtarı)
FROM public.ilanlar
WHERE idare IS NOT NULL
GROUP BY idare;
CREATE UNIQUE INDEX idx_idare_ozet_mv_idare ON public.idare_ozet_mv (idare);
-- KRİTİK: gece REFRESH `-U postgres` (run_scraper.sh:183) → sahip postgres OLMALI (yoksa sessiz-bayat).
ALTER MATERIALIZED VIEW public.idare_ozet_mv OWNER TO postgres;

-- idare_dizin_json: çıktı dizisine detsis_no eklenir (eleman [8]). harcama/DT okuması AYNEN.
CREATE OR REPLACE FUNCTION public.idare_dizin_json()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT COALESCE(jsonb_agg(
    jsonb_build_array(i.idare, i.toplam, i.aktif, i.en_yakin_il,
                      COALESCE(d.toplam, 0), COALESCE(d.aktif, 0),
                      COALESCE(h.sozlesme_sayisi, 0), COALESCE(h.toplam_harcama, 0),
                      i.detsis_no, hi.ad)
    ORDER BY i.toplam DESC), '[]'::jsonb)
  FROM public.idare_ozet_mv i
  LEFT JOIN public.dt_idare_ozet_mv d ON d.idare = i.idare
  LEFT JOIN public.idare_harcama_mv h ON h.idare = i.idare
  LEFT JOIN public.idare_hiyerarsi hi ON hi.detsis_no = i.detsis_no;  -- [9] DETSİS resmi (temiz) ad → dedup kanonik adı
$$;
ALTER FUNCTION public.idare_dizin_json() SET statement_timeout = '20s';
REVOKE EXECUTE ON FUNCTION public.idare_dizin_json() FROM public, anon;   -- idare adı kimlik verisi
GRANT  EXECUTE ON FUNCTION public.idare_dizin_json() TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA: BEL-PA iki varyantı da detsis_no=87767631 dönmeli:
--   SELECT idare, detsis_no FROM idare_ozet_mv WHERE idare ILIKE '%BEL-PA%';
