-- ============================================================
-- idare_sayim_birlikte() — dashboard "İşveren İdare" birleşik sayı (31 Tem 2026)
-- ------------------------------------------------------------
-- Bana Özel dashboard geneli İhale+DT BİRLEŞİK gösteriyor (harita İhale+DT toplam,
-- "Toplam DT+İhale", ve artık "Yüklenici Firma" firma_ozet_birlikte ile). Ama "İşveren
-- İdare" idare_sayim → idare_ozet_mv = YALNIZ İHALE idareleri (~42K); DT idareleri ayrı
-- dt_idare_ozet_mv'de. Birleşik distinct sayıyı veren küçük RPC.
--
-- İSİM DÖNMEZ (yalnız count) → SECURITY DEFINER ile anon'a AÇILABİLİR (idare adları
-- anon'a kapalı; bu yalnız toplam). tr_fold ile büyük/küçük+locale varyantı dedup edilir;
-- "X Belediyesi" vs "X Belediye Başkanlığı" gibi gerçek farklı adlar ayrı sayılır (headline
-- yaklaşık — İhale-only'nin eksik saymasından daha doğru).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_sayim_birlikte.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.idare_sayim_birlikte()
RETURNS bigint
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT count(DISTINCT public.tr_fold(idare))
  FROM (
    SELECT idare FROM public.idare_ozet_mv    WHERE idare IS NOT NULL AND btrim(idare) <> ''
    UNION ALL
    SELECT idare FROM public.dt_idare_ozet_mv WHERE idare IS NOT NULL AND btrim(idare) <> ''
  ) u;
$$;
ALTER FUNCTION public.idare_sayim_birlikte() SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.idare_sayim_birlikte() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anon): SELECT public.idare_sayim_birlikte();   -- İhale-only 42K'dan büyük olmalı
