-- ============================================================
-- firma_dizin_birlikte → DİNAMİK SQL (aynı latent bug: parametreli LIKE seq-scan) — 3 Ağu 2026
-- ------------------------------------------------------------
-- firma_dizin_dt ile AYNI sorun: fonksiyon içinde `y.arama_fold LIKE '%'||tr_fold(p_ara)||'%'`
-- parametre-bağımlı → trigram GIN kullanılmaz → seq-scan → uzun terim REST'te 57014.
-- Dizin "İkisi" (birlikte) modu + ileride B özelliği (liste DT) bunu kullanır. Aynı dinamik-SQL
-- çözümü: deseni plpgsql'de hesapla, EXECUTE ile literal göm.
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dizin_birlikte_dinamik.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_dizin_birlikte(
  p_ara text DEFAULT NULL, p_il text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0,
  p_sort text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public SET statement_timeout = '20s' AS $$
DECLARE
  v_like text := NULL;
BEGIN
  IF p_ara IS NOT NULL AND btrim(p_ara) <> '' THEN
    v_like := '%' || replace(replace(left(public.tr_fold(p_ara), 40), '%', ''), '_', '') || '%';
  END IF;
  RETURN QUERY EXECUTE format($q$
    SELECT y.id, y.ad, y.il,
           (COALESCE(y.toplam_sozlesme_sayisi,0)+COALESCE(d.dt_sozlesme,0))::bigint,
           (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0))::numeric,
           y.son_sozlesme_tarihi, COALESCE(d.dt_bedel,0)
    FROM public.yukleniciler y
    LEFT JOIN public.firma_dt_toplam d ON d.firma_norm = y.normalize_ad
    WHERE (%L::text IS NULL OR y.arama_fold LIKE %L)
      AND (%L::text IS NULL OR y.il = %L)
      AND (%L::boolean OR NOT public.firma_kurum_mu(y.ad))
    ORDER BY
      (CASE WHEN %L='bedel'    THEN (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) END) DESC NULLS LAST,
      (CASE WHEN %L='sozlesme' THEN (COALESCE(y.toplam_sozlesme_sayisi,0)+COALESCE(d.dt_sozlesme,0)) END) DESC NULLS LAST,
      (CASE WHEN %L='tarih'    THEN y.son_sozlesme_tarihi END) DESC NULLS LAST,
      (CASE WHEN %L='ad'       THEN y.ad END) ASC NULLS LAST,
      (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) DESC NULLS LAST
    LIMIT %s OFFSET %s
  $q$, v_like, v_like, p_il, p_il, p_kamu_dahil, p_sort, p_sort, p_sort, p_sort,
       LEAST(GREATEST(p_limit,1),200), GREATEST(p_offset,0));
END;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text,boolean) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text,boolean) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
