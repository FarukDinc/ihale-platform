-- ============================================================================
-- migration_hs_hiyerarsi.sql — HS6 hiyerarşisi (fasıl → pozisyon → alt pozisyon)
-- + 1000-SATIR KIRPILMA HATASI DÜZELTMESİ                       (18 Tem 2026)
--
-- SORUN 1 (veri hatası): ticaret-analiz.html `detayAc` ülkenin HS6 kalemlerini
--   `.limit(4000)` ile çekiyordu; PostgREST db-max-rows=1000 tavanı yüzünden
--   büyük ortaklarda veri SESSİZCE kırpılıyordu:
--     DEU 16.450 satır / USA 14.929 / ITA 14.944 / ROU 10.309 → hepsi 1.000'e düşüyordu.
--   Sonuç: "N kalem" sayısı yanlış, İthalat/Değişim sıralaması kırpılmış alt kümeye göre.
--
-- SORUN 2 (özellik): fasıl (2-hane) / pozisyon (4-hane) bazlı sorgu client-side
--   imkânsız (hs6 LIKE '84%' = 96.718 satır). Hiyerarşik arama için şart.
--
-- ÇÖZÜM: jsonb dönen sunucu-taraflı agregasyon (bu projede kanıtlanmış desen —
--   jsonb skaler olduğu için satır tavanına takılmaz, bkz. idare_dizin_json).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_hs_hiyerarsi.sql
-- Idempotent (CREATE OR REPLACE + IF NOT EXISTS).
-- ============================================================================

-- ── İndeksler ───────────────────────────────────────────────────────────────
-- prefix (LIKE 'xx%') sorguları için text_pattern_ops şart; normal btree LIKE'ta kullanılmaz.
CREATE INDEX IF NOT EXISTS idx_dth_hs6_pattern ON public.dis_ticaret_hs (hs6 text_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_dth_ulke_hs6    ON public.dis_ticaret_hs (ulke_iso3, hs6);

-- ── 1) Bir ülkenin HS6 kalemleri (opsiyonel fasıl/pozisyon prefix'i) ────────
-- Dönüş: { guncel_yil, onceki_yil, kalemler:[{hs6, ihr_g, ihr_o, ith_g, ith_o}] }
-- Kırpma YOK — ülkenin TÜM kalemleri döner (DEU ~4.100 kalem).
CREATE OR REPLACE FUNCTION public.ticaret_hs_kalem(p_iso3 text, p_prefix text DEFAULT NULL)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH y AS (
    SELECT max(yil) AS guncel, min(yil) AS onceki
    FROM public.dis_ticaret_hs WHERE ulke_iso3 = p_iso3
  ),
  k AS (
    SELECT d.hs6,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'X' AND d.yil = (SELECT guncel FROM y)) AS ihr_g,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'X' AND d.yil = (SELECT onceki FROM y)) AS ihr_o,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'M' AND d.yil = (SELECT guncel FROM y)) AS ith_g,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'M' AND d.yil = (SELECT onceki FROM y)) AS ith_o
    FROM public.dis_ticaret_hs d
    WHERE d.ulke_iso3 = p_iso3
      AND (p_prefix IS NULL OR d.hs6 LIKE p_prefix || '%')
    GROUP BY d.hs6
  )
  SELECT jsonb_build_object(
    'guncel_yil', (SELECT guncel FROM y),
    'onceki_yil', (SELECT onceki FROM y),
    'kalemler',   COALESCE((SELECT jsonb_agg(to_jsonb(k) ORDER BY k.ihr_g DESC NULLS LAST) FROM k), '[]'::jsonb)
  );
$$;

-- ── 2) Bir HS kodu/prefix'i için ülke ülke ticaret ──────────────────────────
-- p_kod: '84' (fasıl) | '8407' (pozisyon) | '840710' (alt pozisyon) — hepsi çalışır.
-- Dönüş: { guncel_yil, onceki_yil, kod_adet, ulkeler:[{iso3, ihr_g, ihr_o, ith_g, ith_o}] }
CREATE OR REPLACE FUNCTION public.ticaret_hs_ulkeler(p_kod text)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH y AS (
    SELECT max(yil) AS guncel, min(yil) AS onceki
    FROM public.dis_ticaret_hs WHERE hs6 LIKE p_kod || '%'
  ),
  u AS (
    SELECT d.ulke_iso3 AS iso3,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'X' AND d.yil = (SELECT guncel FROM y)) AS ihr_g,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'X' AND d.yil = (SELECT onceki FROM y)) AS ihr_o,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'M' AND d.yil = (SELECT guncel FROM y)) AS ith_g,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'M' AND d.yil = (SELECT onceki FROM y)) AS ith_o
    FROM public.dis_ticaret_hs d
    WHERE d.hs6 LIKE p_kod || '%'
    GROUP BY d.ulke_iso3
  )
  SELECT jsonb_build_object(
    'guncel_yil', (SELECT guncel FROM y),
    'onceki_yil', (SELECT onceki FROM y),
    'kod_adet',   (SELECT count(DISTINCT hs6) FROM public.dis_ticaret_hs WHERE hs6 LIKE p_kod || '%'),
    'ulkeler',    COALESCE((SELECT jsonb_agg(to_jsonb(u) ORDER BY u.ihr_g DESC NULLS LAST) FROM u), '[]'::jsonb)
  );
$$;

-- ── 3) Fasıl (2-hane) özeti — hiyerarşik gezinme için ──────────────────────
-- Bir ülkenin fasıl bazında toplamları (drill-down'da gruplama/katlama için).
-- p_iso3 NULL ise TÜM dünya (Türkiye toplamı).
CREATE OR REPLACE FUNCTION public.ticaret_hs_fasil(p_iso3 text DEFAULT NULL)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH y AS (
    SELECT max(yil) AS guncel, min(yil) AS onceki FROM public.dis_ticaret_hs
  ),
  f AS (
    SELECT left(d.hs6, 2) AS fasil,
           count(DISTINCT d.hs6) AS kalem_adet,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'X' AND d.yil = (SELECT guncel FROM y)) AS ihr_g,
           SUM(d.deger_usd) FILTER (WHERE d.yon = 'M' AND d.yil = (SELECT guncel FROM y)) AS ith_g
    FROM public.dis_ticaret_hs d
    WHERE (p_iso3 IS NULL OR d.ulke_iso3 = p_iso3)
    GROUP BY left(d.hs6, 2)
  )
  SELECT jsonb_build_object(
    'guncel_yil', (SELECT guncel FROM y),
    'fasillar',   COALESCE((SELECT jsonb_agg(to_jsonb(f) ORDER BY f.ihr_g DESC NULLS LAST) FROM f), '[]'::jsonb)
  );
$$;

-- ── Yetkiler (misafir de görebilir — istatistik/vitrin, ham döküm değil) ────
GRANT EXECUTE ON FUNCTION public.ticaret_hs_kalem(text, text) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ticaret_hs_ulkeler(text)     TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ticaret_hs_fasil(text)       TO anon, authenticated, service_role;

-- Ağır agregasyon güvenliği. DİKKAT: CREATE OR REPLACE proconfig'i sıfırlar →
-- bu ALTER'lar fonksiyon tanımlarından SONRA gelmeli (statement-timeout-edge dersi).
ALTER FUNCTION public.ticaret_hs_kalem(text, text) SET statement_timeout = '20s';
ALTER FUNCTION public.ticaret_hs_ulkeler(text)     SET statement_timeout = '20s';
ALTER FUNCTION public.ticaret_hs_fasil(text)       SET statement_timeout = '20s';

NOTIFY pgrst, 'reload schema';

-- Kontrol (migration sonrası):
--   SELECT jsonb_array_length(ticaret_hs_kalem('DEU')->'kalemler');   -- >1000 olmali (kirpma yok)
--   SELECT ticaret_hs_ulkeler('8407')->'kod_adet';                    -- pozisyon altindaki kalem sayisi
--   SELECT jsonb_array_length(ticaret_hs_fasil('DEU')->'fasillar');    -- ~90 fasil
