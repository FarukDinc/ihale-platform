-- ============================================================
-- İhaleGlobal — ticaret_ulke_yil'e iso2 (ISO-3166 alpha-2) ekle
--
-- Frontend Türkçe ülke adı için: Intl.DisplayNames(['tr']) ISO2 ister.
-- SVG haritadaki adlar İngilizce; a2 olmadan tooltip/liste İngilizceye düşer.
-- iso2 backfill'de UN Comtrade partnerAreas.json'dan (PartnerCodeIsoAlpha2) yazılır.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ticaret_iso2.sql
-- ============================================================

BEGIN;

ALTER TABLE public.ticaret_ulke_yil ADD COLUMN IF NOT EXISTS iso2 CHAR(2);

-- ticaret_liste: iso2'yi de döndür (Türkçe ad için)
CREATE OR REPLACE FUNCTION public.ticaret_liste(p_yil INT, p_kiyas_yil INT)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_agg(row_to_json(t) ORDER BY t.yil_ihr DESC NULLS LAST), '[]'::jsonb)
  FROM (
    SELECT a.iso3, a.iso2,
           a.ihracat AS yil_ihr, k.ihracat AS kiyas_ihr,
           a.ithalat AS yil_ith, k.ithalat AS kiyas_ith
    FROM        public.ticaret_ulke_yil a
    LEFT JOIN   public.ticaret_ulke_yil k ON k.iso3 = a.iso3 AND k.yil = p_kiyas_yil
    WHERE  a.yil = p_yil AND a.iso3 <> 'WLD'
  ) t;
$$;

GRANT EXECUTE ON FUNCTION public.ticaret_liste(INT, INT) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;
