-- =============================================================================
-- migration_kurum_dt_ozet.sql — Kurum Analizi "Dağılım Analizi" İhale/DT seçici
-- =============================================================================
--
-- AMAÇ: kurum-analiz Dağılım Analizi sekmesine İhale/Doğrudan Temin toggle'ı.
-- kurum_ozet(p_idare) ihale dağılımını (ilanlar) döner; bu RPC onun DT AYNASI —
-- dogrudan_temin_ilanlari'ndan kategori/tür/il/durum dağılımı. İki evren AYRI.
--
-- kurum_ozet ile birebir desen: SECURITY DEFINER (idare anon'a maskeli ama RPC
-- authenticated'a açık), idare ILIKE '%p_idare%' (hiyerarşik ad varyasyonları).
-- 2,9M satır + ILIKE + GROUP BY on-demand → statement_timeout 25s (yalnız DT
-- toggle'ına tıklanınca çağrılır).
--
-- ANON'A KAPALI: REVOKE açıkça (kurum_ozet ile aynı asimetri).
--
-- Uygulama:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_kurum_dt_ozet.sql
-- =============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.kurum_dt_ozet(p_idare text)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, pg_temp
SET statement_timeout = '25s'
AS $$
  WITH f AS (
    -- idare ILIKE: idx_dt_idare_trgm (GIN gin_trgm_ops) ile hızlı (bkz migration_dt_idare_trgm.sql).
    -- O indeks OLMADAN 2,9M'de TIMEOUT verir — önce onu uygula.
    SELECT dt_no, tur, il, kategori, durum, tarih
    FROM public.dogrudan_temin_ilanlari
    WHERE idare ILIKE '%' || p_idare || '%'
  )
  SELECT jsonb_build_object(
    'kpi', jsonb_build_object(
      'toplam',    (SELECT count(*) FROM f),
      'acik',      (SELECT count(*) FROM f WHERE durum = 'Doğrudan Temin Duyurusu Yayımlanmış' AND tarih >= now()),
      'il_sayisi', (SELECT count(DISTINCT il) FROM f WHERE il IS NOT NULL)
    ),
    'kategori', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT COALESCE(NULLIF(kategori, ''), 'Kategorisiz') k, count(*) n
                       FROM f GROUP BY 1 ORDER BY count(*) DESC LIMIT 12) x),
    'tur',      (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT COALESCE(NULLIF(tur, ''), 'Diğer') k, count(*) n FROM f GROUP BY 1) x),
    'il',       (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT il k, count(*) n FROM f WHERE il IS NOT NULL GROUP BY il) x),
    'durum', jsonb_build_object(
      'aktif',   (SELECT count(*) FROM f WHERE durum = 'Doğrudan Temin Duyurusu Yayımlanmış' AND tarih >= now()),
      'kapandi', (SELECT count(*) FROM f WHERE NOT (durum = 'Doğrudan Temin Duyurusu Yayımlanmış' AND tarih >= now()))
    ),
    -- DT kazanan firmaları: dogrudan_temin_sonuclari.kazanan_firma (anon-kapalı; RPC SECURITY DEFINER)
    'kazanan', (SELECT COALESCE(jsonb_agg(jsonb_build_object('grup_deger', k, 'ihale_sayisi', n) ORDER BY n DESC), '[]'::jsonb)
                FROM (SELECT s.kazanan_firma k, count(*) n
                      FROM f JOIN public.dogrudan_temin_sonuclari s ON s.dt_no = f.dt_no
                      WHERE s.kazanan_firma IS NOT NULL AND s.kazanan_firma <> ''
                      GROUP BY s.kazanan_firma ORDER BY count(*) DESC LIMIT 12) x)
  );
$$;

REVOKE EXECUTE ON FUNCTION public.kurum_dt_ozet(text) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.kurum_dt_ozet(text) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA:
--   SELECT public.kurum_dt_ozet('<idare adı>')->'kpi';
-- ANON (401/403/404 beklenir, 200 DEĞİL):
--   curl -s -o /dev/null -w '%{http_code}\n' -H "apikey:$ANON" -H "Authorization:Bearer $ANON" \
--     -X POST https://ihaleglobal.com/rest/v1/rpc/kurum_dt_ozet -H 'Content-Type: application/json' -d '{"p_idare":"x"}'
-- =============================================================================
