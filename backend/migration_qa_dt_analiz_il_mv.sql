-- ============================================================================
-- migration_qa_dt_analiz_il_mv.sql — DT Analizi il-filtresi timeout (DOĞRU çözüm)
--   (2 Ağu 2026). idx_dt_ilanlari_il ZATEN VAR → timeout indeks değil, AGGREGATE maliyeti:
--   il=ANKARA alt-kümesinde `son` JOIN (dogrudan_temin_sonuclari) + percentile_cont (medyan)
--   15s'i aşıyor. YIL için dt_analiz_yil_mv nasıl çözüyorsa, il için per-il MV aynısını yapar
--   (birebir aynı desen: migration_dt_analiz_yil_mv.sql).
--   dt_analiz_il_mv: her il için _dt_ozet_json ÖNCEDEN hesaplı (~81 satır); il-only sorgu MV'den
--   ANLIK. il+kategori/tur/yıl kombinasyonu CANLI kalır (alt-küme küçük).
--
--   ⚠️ MV KURULUMU AĞIR: _dt_ozet_json'u ~81 kez çalıştırır (ANKARA dahil) → birkaç dakika.
--     · _dt_ozet_json içindeki 15s cap MV kurulumunu ÖLDÜRMEZ: iç içe SET, üst-düzey ifadenin
--       zamanlayıcısını yeniden kurmaz (yıl-MV çok-dakikalık build'iyle KANITLI). Yine de
--       kurulum psql oturumunda statement_timeout=0 verip her ihtimale karşı garantiye alıyoruz.
--     · Yeni MV olduğu için okuyucu yok, kilit sorunu olmaz.
--
--   Çalıştırma (superuser — mevcut sahip supabase_admin):
--     docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_dt_analiz_il_mv.sql
--   GECE REFRESH run_scraper.sh'a eklendi (dt_analiz_mv/yil_mv yanına, -U postgres CONCURRENTLY).
-- ============================================================================
SET statement_timeout = 0;   -- uzun MV kurulumu kesilmesin

-- 1) Per-il önceden hesaplı özet
DROP MATERIALIZED VIEW IF EXISTS public.dt_analiz_il_mv;
CREATE MATERIALIZED VIEW public.dt_analiz_il_mv AS
  SELECT t.il, public._dt_ozet_json(t.il, NULL, NULL, NULL) AS ozet
  FROM (SELECT DISTINCT il FROM public.dogrudan_temin_ilanlari
        WHERE il IS NOT NULL AND btrim(il) <> '') t;
CREATE UNIQUE INDEX IF NOT EXISTS dt_analiz_il_mv_pk ON public.dt_analiz_il_mv (il);  -- CONCURRENTLY için ŞART
GRANT SELECT ON public.dt_analiz_il_mv TO authenticated, service_role;

-- Gece REFRESH `-U postgres` ile CONCURRENTLY çalışır → MV postgres SAHİPLİ olmalı, yoksa
-- "permission denied for materialized view" → sessizce BAYAT kalır (MADDE 12/14 owner-fix dersi).
ALTER MATERIALIZED VIEW public.dt_analiz_il_mv OWNER TO postgres;
-- postgres REFRESH sırasında _dt_ozet_json'u ÇAĞIRABİLMELİ (owner-fix'te verildi; idempotent güvence).
-- SECURITY DEFINER olduğundan iç veri erişimi yine supabase_admin yetkisiyle çalışır; bu grant
-- yalnız çağrı iznini açar (postgres iç rol — anon/authenticated/service_role'e dokunmaz).
GRANT EXECUTE ON FUNCTION public._dt_ozet_json(text, text, text, integer) TO postgres;

-- 2) Genel RPC — il-ONLY sorguyu MV'ye yönlendir (kategori/tur/yıl da null ise).
--    Yıl-MV dalını KORU (migration_dt_analiz_yil_mv.sql), il dalını EKLE.
CREATE OR REPLACE FUNCTION public.dt_analiz_ozet(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL, p_yil int DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = public SET statement_timeout = '15s' AS $$
BEGIN
  IF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NULL) THEN
    RETURN (SELECT ozet FROM public.dt_analiz_mv);                        -- hiç filtre: genel MV
  ELSIF (p_il IS NOT NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NULL) THEN
    RETURN COALESCE((SELECT ozet FROM public.dt_analiz_il_mv WHERE il = p_il),
                    public._dt_ozet_json(p_il, NULL, NULL, NULL));        -- il-tek: il-MV (yoksa canlı)
  ELSIF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NOT NULL) THEN
    RETURN COALESCE((SELECT ozet FROM public.dt_analiz_yil_mv WHERE yil = p_yil),
                    public._dt_ozet_json(NULL, NULL, NULL, p_yil));       -- yıl-tek: yıl-MV (yoksa canlı)
  END IF;
  RETURN public._dt_ozet_json(p_il, p_kategori, p_tur, p_yil);           -- kombinasyon: canlı (küçük)
END;
$$;
GRANT EXECUTE ON FUNCTION public.dt_analiz_ozet(text, text, text, int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (ANKARA artık anlık dönmeli):
\timing on
SELECT public.dt_analiz_ozet('ANKARA',NULL,NULL,NULL) -> 'toplam' AS ankara_dt;
