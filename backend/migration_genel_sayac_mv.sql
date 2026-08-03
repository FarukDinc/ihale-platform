-- =============================================================================
-- migration_genel_sayac_mv.sql — Panel "Toplam DT + İhale" icin sayac MV
-- =============================================================================
-- NEDEN: v1-benim-sayfam panelinde "Toplam DT + İhale" tile'i iki CANLI
--   count=exact sorgusuyla (ilanlar + DT) hesaplaniyordu (satir 338). ilanlar
--   count'u 1,96M satirda ~2s suruyor; buyuk UPDATE sonrasi olu-tuple bloatiyla
--   3s misafir statement_timeout'unu asip sayac 0 donuyordu → tile yanlis (yalniz
--   DT). Cozum: gece cache'lenen tek-satir MV; panel bunu okur (~0,15s, veri
--   buyudukce sabit). Bkz. hafiza orphan-kurum-greft (VACUUM dersi),
--   statement-timeout-edge, client-load-all-bug.
--
-- ANON'A ACIK: yalniz AGREGAT toplamlar (kimlik verisi degil; acilis sayfasi da
--   benzer toplamlar gosterir). idare adi gibi maskeli veri yok.
-- REFRESH: gece run_scraper.sh'te (NON-concurrent; tek satir, benzersiz indeks
--   yok → CONCURRENTLY calismaz; ~1-3s kilit gece kabul).
-- CALISTIRMA: docker exec -i supabase-db psql -U postgres -d postgres < bu_dosya
-- =============================================================================
DROP MATERIALIZED VIEW IF EXISTS public.genel_sayac_mv;
CREATE MATERIALIZED VIEW public.genel_sayac_mv AS
SELECT (SELECT count(*) FROM public.ilanlar)::bigint                 AS toplam_ihale,
       (SELECT count(*) FROM public.dogrudan_temin_ilanlari)::bigint AS toplam_dt,
       now() AS guncelleme;

REVOKE ALL   ON public.genel_sayac_mv FROM PUBLIC;
GRANT SELECT ON public.genel_sayac_mv TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
