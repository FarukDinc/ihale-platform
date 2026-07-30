-- ============================================================
-- MADDE 20 Parça A — Firma dizini DT & İkisi modlarında sıralama (31 Tem 2026)
-- ------------------------------------------------------------
-- firma_dizin_dt / firma_dizin_birlikte'ye p_sort eklenir → liste sort dropdown'ı DT ve
-- İkisi modlarında da çalışır. Ölçütler: 'bedel' (en çok ciro/bedel), 'sozlesme' (en çok
-- sözleşme), 'tarih' (son iş — yalnız İkisi), 'ad' (isim — yalnız İkisi). İmza değişiyor →
-- DROP + CREATE (PostgREST kısa çağrıları default'la eşler).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dizin_sort.sql
-- ============================================================

DROP FUNCTION IF EXISTS public.firma_dizin_dt(text,int,int);
CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0, p_sort text DEFAULT 'bedel')
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH top AS (
    SELECT firma_norm, ad, dt_sozlesme, dt_bedel
    FROM public.firma_dt_toplam
    WHERE (p_ara IS NULL OR firma_norm LIKE '%'||public.normalize_firma(p_ara)||'%')
    ORDER BY (CASE WHEN p_sort='sozlesme' THEN dt_sozlesme END) DESC NULLS LAST,
             dt_bedel DESC NULLS LAST
    LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0)
  )
  SELECT y.id, t.ad, y.il, t.dt_sozlesme, t.dt_bedel, NULL::timestamptz, t.dt_bedel
  FROM top t LEFT JOIN public.yukleniciler y ON y.normalize_ad = t.firma_norm
  ORDER BY (CASE WHEN p_sort='sozlesme' THEN t.dt_sozlesme END) DESC NULLS LAST,
           t.dt_bedel DESC NULLS LAST;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text) TO authenticated, service_role;

DROP FUNCTION IF EXISTS public.firma_dizin_birlikte(text,text,int,int);
CREATE OR REPLACE FUNCTION public.firma_dizin_birlikte(
  p_ara text DEFAULT NULL, p_il text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0,
  p_sort text DEFAULT 'bedel')
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT y.id, y.ad, y.il,
         (COALESCE(y.toplam_sozlesme_sayisi,0) + COALESCE(d.dt_sozlesme,0))::bigint,
         (COALESCE(y.toplam_ciro,0) + COALESCE(d.dt_bedel,0))::numeric,
         y.son_sozlesme_tarihi, COALESCE(d.dt_bedel,0)
  FROM public.yukleniciler y
  LEFT JOIN public.firma_dt_toplam d ON d.firma_norm = y.normalize_ad
  WHERE (p_ara IS NULL OR y.arama_fold LIKE '%'||public.tr_fold(p_ara)||'%')
    AND (p_il  IS NULL OR y.il = p_il)
  ORDER BY
    (CASE WHEN p_sort='bedel'    THEN (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) END) DESC NULLS LAST,
    (CASE WHEN p_sort='sozlesme' THEN (COALESCE(y.toplam_sozlesme_sayisi,0)+COALESCE(d.dt_sozlesme,0)) END) DESC NULLS LAST,
    (CASE WHEN p_sort='tarih'    THEN y.son_sozlesme_tarihi END) DESC NULLS LAST,
    (CASE WHEN p_sort='ad'       THEN y.ad END) ASC NULLS LAST,
    (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) DESC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0);
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
