-- ============================================================
-- MADDE 18-B (perf) — firma_dizin_dt hızlandırma (31 Tem 2026)
-- ------------------------------------------------------------
-- firma_dizin_dt ~2.8s: LEFT JOIN yukleniciler, ORDER BY dt_bedel + LIMIT'ten ÖNCE tam
--   birleşme yapıyor → indeksli top-N kullanılamıyor. ÇÖZÜM: önce firma_dt_toplam'da
--   ORDER BY+LIMIT (firma_dt_toplam_bedel indeksi), SONRA yalnız o N satırı yukleniciler'e
--   join et (normalize_ad indeksiyle N hızlı arama).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dizin_dt_fix.sql
-- ============================================================

-- Join anahtarı indeksi (top-N satırın yukleniciler eşlemesi hızlansın).
CREATE INDEX IF NOT EXISTS idx_yukleniciler_normalize_ad
  ON public.yukleniciler (normalize_ad) WHERE normalize_ad IS NOT NULL;

CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH top AS (
    SELECT firma_norm, ad, dt_sozlesme, dt_bedel
    FROM public.firma_dt_toplam
    WHERE (p_ara IS NULL OR firma_norm LIKE '%'||public.normalize_firma(p_ara)||'%')
    ORDER BY dt_bedel DESC NULLS LAST, dt_sozlesme DESC
    LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0)
  )
  SELECT y.id, t.ad, y.il, t.dt_sozlesme, t.dt_bedel, NULL::timestamptz, t.dt_bedel
  FROM top t
  LEFT JOIN public.yukleniciler y ON y.normalize_ad = t.firma_norm
  ORDER BY t.dt_bedel DESC NULLS LAST, t.dt_sozlesme DESC;
$$;
GRANT EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anlık olmalı):
--   \timing on
--   SELECT ad, toplam_sozlesme_sayisi, dt_bedel FROM firma_dizin_dt(NULL,5,0);
