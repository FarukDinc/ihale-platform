-- ============================================================
-- İhaleGlobal — Türkiye dış ticaret YILLIK serisi (2000+)
--
-- Amaç: dünya haritası "Türkiye ile Ticaret" katmanına yıl seçici + yıl
-- kıyaslama getirmek. Eski model js/ticaret-tr-veri.js'te yalnız 2 yıl
-- tutuyordu ([bu_yıl, önceki_yıl]); artık tüm yıllar DB'de, harita seçili
-- yılı RPC ile çeker (küçük payload, client-load-all yok).
--
-- Kaynak: WITS (2000→~güncel-2, toplam+sektör, omurga) + UN Comtrade (en
-- taze 1-2 yıl toplam). Her satırda kaynak işaretlenir.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ticaret_yillik.sql
-- ============================================================

BEGIN;

-- ── Ülke-yıl toplamları (TR→ülke ihracat, ülke→TR ithalat), USD ──
CREATE TABLE IF NOT EXISTS public.ticaret_ulke_yil (
  iso3       TEXT   NOT NULL,          -- partner ISO-A3 ('WLD' = dünya toplamı)
  yil        INT    NOT NULL,
  ihracat    NUMERIC,                  -- TR → ülke (USD)
  ithalat    NUMERIC,                  -- ülke → TR (USD)
  kaynak     TEXT   NOT NULL DEFAULT 'wits',   -- 'wits' | 'comtrade'
  guncelleme TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (iso3, yil)
);
CREATE INDEX IF NOT EXISTS ix_ticaret_ulke_yil_yil ON public.ticaret_ulke_yil (yil);

-- ── Ülke-yıl-sektör kırılımı, USD ──
CREATE TABLE IF NOT EXISTS public.ticaret_sektor_yil (
  iso3       TEXT   NOT NULL,
  yil        INT    NOT NULL,
  sektor     TEXT   NOT NULL,          -- js/ticaret SEKTORLER anahtarı (örn. '84-85_MachElec')
  ihracat    NUMERIC,
  ithalat    NUMERIC,
  kaynak     TEXT   NOT NULL DEFAULT 'wits',
  PRIMARY KEY (iso3, yil, sektor)
);
CREATE INDEX IF NOT EXISTS ix_ticaret_sektor_yil_yilsek ON public.ticaret_sektor_yil (yil, sektor);

-- RLS: okuma herkese açık (ihale verisiyle aynı desen), yazma yalnız service_role.
ALTER TABLE public.ticaret_ulke_yil   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ticaret_sektor_yil ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ticaret_ulke_yil_read   ON public.ticaret_ulke_yil;
DROP POLICY IF EXISTS ticaret_sektor_yil_read ON public.ticaret_sektor_yil;
CREATE POLICY ticaret_ulke_yil_read   ON public.ticaret_ulke_yil   FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY ticaret_sektor_yil_read ON public.ticaret_sektor_yil FOR SELECT TO anon, authenticated USING (true);
GRANT SELECT              ON public.ticaret_ulke_yil, public.ticaret_sektor_yil TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ticaret_ulke_yil, public.ticaret_sektor_yil TO service_role;

-- ── RPC 1: kullanılabilir yıllar + en güncel yıl ──
CREATE OR REPLACE FUNCTION public.ticaret_yillar()
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT jsonb_build_object(
    'yillar',    COALESCE((SELECT jsonb_agg(DISTINCT yil ORDER BY yil) FROM public.ticaret_ulke_yil), '[]'::jsonb),
    'guncel_yil', (SELECT max(yil) FROM public.ticaret_ulke_yil)
  );
$$;

-- ── RPC 2: bir yılın harita verisi (sektör NULL ise toplam, değilse o sektör) ──
--    Çıktı: { "DEU": {"ihr":123,"ith":456}, ... }  (WLD hariç, harita boyaması için)
CREATE OR REPLACE FUNCTION public.ticaret_harita(p_yil INT, p_sektor TEXT DEFAULT NULL)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_object_agg(iso3, jsonb_build_object('ihr', ihracat, 'ith', ithalat)), '{}'::jsonb)
  FROM (
    SELECT iso3, ihracat, ithalat
    FROM   public.ticaret_ulke_yil
    WHERE  p_sektor IS NULL AND yil = p_yil AND iso3 <> 'WLD'
    UNION ALL
    SELECT iso3, ihracat, ithalat
    FROM   public.ticaret_sektor_yil
    WHERE  p_sektor IS NOT NULL AND yil = p_yil AND sektor = p_sektor AND iso3 <> 'WLD'
  ) q;
$$;

-- ── RPC 3: bir ülkenin tam yıl-serisi (tooltip sparkline + kıyas) ──
--    Çıktı: { "toplam": [{yil,ihr,ith,kaynak}...], "sektor": [{yil,sektor,ihr,ith}...] }
CREATE OR REPLACE FUNCTION public.ticaret_ulke(p_iso3 TEXT)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT jsonb_build_object(
    'toplam', COALESCE((
      SELECT jsonb_agg(jsonb_build_object('yil',yil,'ihr',ihracat,'ith',ithalat,'kaynak',kaynak) ORDER BY yil)
      FROM public.ticaret_ulke_yil WHERE iso3 = p_iso3), '[]'::jsonb),
    'sektor', COALESCE((
      SELECT jsonb_agg(jsonb_build_object('yil',yil,'sektor',sektor,'ihr',ihracat,'ith',ithalat) ORDER BY yil, sektor)
      FROM public.ticaret_sektor_yil WHERE iso3 = p_iso3), '[]'::jsonb)
  );
$$;

-- ── RPC 4: ülke listesi — seçili yıl + kıyas yılı yan yana ──
--    Çıktı: [{iso3, yil_ihr, kiyas_ihr, yil_ith, kiyas_ith}, ...]  (WLD hariç, ihracata göre sıralı)
CREATE OR REPLACE FUNCTION public.ticaret_liste(p_yil INT, p_kiyas_yil INT)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_agg(row_to_json(t) ORDER BY t.yil_ihr DESC NULLS LAST), '[]'::jsonb)
  FROM (
    SELECT a.iso3,
           a.ihracat AS yil_ihr, k.ihracat AS kiyas_ihr,
           a.ithalat AS yil_ith, k.ithalat AS kiyas_ith
    FROM        public.ticaret_ulke_yil a
    LEFT JOIN   public.ticaret_ulke_yil k ON k.iso3 = a.iso3 AND k.yil = p_kiyas_yil
    WHERE  a.yil = p_yil AND a.iso3 <> 'WLD'
  ) t;
$$;

GRANT EXECUTE ON FUNCTION public.ticaret_yillar()                 TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ticaret_harita(INT, TEXT)        TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ticaret_ulke(TEXT)               TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.ticaret_liste(INT, INT)          TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;
