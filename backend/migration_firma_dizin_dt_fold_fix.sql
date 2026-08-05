-- =============================================================================
-- migration_firma_dizin_dt_fold_fix.sql — firma_dizin_dt arama Türkçe-locale fix
-- 5 Ağu 2026
-- =============================================================================
-- BUG: firma_dizin_dt aramayı `firma_norm LIKE normalize_firma(p_ara)` ile yapıyordu.
-- normalize_firma() Latin upper() kullanır → 'i'→'I' (Türkçe 'İ' DEĞİL). Kullanıcı
-- küçük harf "dinç lazer" yazınca normalize_firma → "DINÇ LAZER" (Latin I), oysa stored
-- firma_norm = "DİNÇ LAZER..." (Türkçe İ) → İ≠I → SESSİZCE 0 sonuç. DT-only firma
-- (Dinç Lazer gibi) v1-firmalar İhale-modu DT fallback'inde bulunamıyordu.
-- FIX: aramayı tr_fold ile yap (firma_dizin_birlikte ile aynı; İ/ı/ç doğru katlanır).
-- Bkz [[ilike-tr-locale-tuzagi]]. firma_dt_toplam ~280K, tr_fold(ad) LIKE ~0,6s (kabul).
--
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_firma_dizin_dt_fold_fix.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit integer DEFAULT 100, p_offset integer DEFAULT 0,
  p_sort text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE(id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
              toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path TO 'public'
SET statement_timeout TO '20s'
AS $function$
DECLARE
  v_like text := NULL;
BEGIN
  IF p_ara IS NOT NULL AND btrim(p_ara) <> '' THEN
    -- FIX: tr_fold (İ/ı/ç case-insensitive) — eskiden normalize_firma (Latin upper, İ≠I bug)
    v_like := '%' || replace(replace(left(public.tr_fold(p_ara), 40), '%', ''), '_', '') || '%';
  END IF;
  RETURN QUERY EXECUTE format($q$
    WITH top AS (
      SELECT firma_norm, ad, dt_sozlesme, dt_bedel
      FROM public.firma_dt_toplam
      WHERE (%L::text IS NULL OR public.tr_fold(ad) LIKE %L)   -- FIX: tr_fold(ad), firma_norm DEĞİL
        AND (%L::boolean OR NOT public.firma_kurum_mu(ad))
      ORDER BY (CASE WHEN %L = 'sozlesme' THEN dt_sozlesme END) DESC NULLS LAST, dt_bedel DESC NULLS LAST
      LIMIT %s OFFSET %s
    )
    SELECT y.id, t.ad, y.il, t.dt_sozlesme, t.dt_bedel, NULL::timestamptz, t.dt_bedel
    FROM top t LEFT JOIN public.yukleniciler y ON y.normalize_ad = t.firma_norm
    ORDER BY (CASE WHEN %L = 'sozlesme' THEN t.dt_sozlesme END) DESC NULLS LAST, t.dt_bedel DESC NULLS LAST
  $q$, v_like, v_like, p_kamu_dahil, p_sort,
       LEAST(GREATEST(p_limit,1),200), GREATEST(p_offset,0), p_sort);
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.firma_dizin_dt(text,integer,integer,text,boolean) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_dt(text,integer,integer,text,boolean) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA: SELECT ad FROM firma_dizin_dt('dinç lazer',5,0,'bedel',true);  -- DİNÇ LAZER bulmalı
