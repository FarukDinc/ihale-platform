-- =============================================================================
-- migration_dt_aktif_deadline.sql
-- =============================================================================
--
-- SORUN: dt_il_sayim_aktif() "aktif DT"yi YALNIZ durum ile sayiyordu
-- (durum IN 'Duyurusu Yayimlanmis','Teklifler Degerlendiriliyor') -> 283.285.
-- Teklif son tarihi (tarih) GECMIS ama durumu guncellenmemis bayat kayitlari da
-- "aktif" sayiyordu. Ihale tarafi (il_sayim_aktif) DOGRU: son_teklif_tarihi>=now().
-- Kullanici ihalepro ile kiyasladi: onlar 3.421 aktif DT gosteriyor, biz 283.285.
--
-- COZUM: DT aktif tanimina ihale tarafiyla PARITE olacak sekilde tarih>=now() ekle
-- ("teklif vermeye hala acik"). Boylece harita + dashboard gercek acik DT'yi sayar.
--
-- Uygulama:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_aktif_deadline.sql
-- =============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.dt_il_sayim_aktif()
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
SET statement_timeout TO '20s'
AS $function$
  SELECT il, count(*)::bigint AS adet
  FROM   public.dogrudan_temin_ilanlari
  WHERE  il IS NOT NULL AND il <> ''
    AND  durum IN ('Doğrudan Temin Duyurusu Yayımlanmış', 'Teklifler Değerlendiriliyor')
    AND  tarih >= now()                       -- YENI: teklif son tarihi gecmemis (gercekten acik)
  GROUP  BY il;
$function$;

GRANT EXECUTE ON FUNCTION public.dt_il_sayim_aktif() TO anon, authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- TESHIS + DOGRULAMA (calisir, sonucu ekrana basar)
-- =============================================================================
SELECT
  count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış','Teklifler Değerlendiriliyor'))                          AS durum_aktif_283k,
  count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış','Teklifler Değerlendiriliyor') AND tarih >= now())       AS gercekten_acik,
  count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış','Teklifler Değerlendiriliyor') AND tarih <  now())       AS bayat_suresi_gecti,
  count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış','Teklifler Değerlendiriliyor') AND tarih IS NULL)        AS tarih_null
FROM public.dogrudan_temin_ilanlari;
