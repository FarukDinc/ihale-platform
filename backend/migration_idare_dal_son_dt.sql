-- =============================================================================
-- migration_idare_dal_son_dt.sql — Kurum Agaci: "dalin son dogrudan teminleri"
-- =============================================================================
--
-- AMAC: kurum-analiz.html Kurum Agaci sekmesinde "Son ihaleler" butonunun DT
-- aynasi ("⚡ Son DT"). idare_dal_son_ihaleler ile birebir ayni desen, sadece
-- kaynak tablo dogrudan_temin_ilanlari. Kapanis tablosu (idare_ata_torun)
-- sayesinde tek JOIN; dalin kendisi + tum alt birimleri kapsanir.
--
-- ONKOSUL: migration_idare_agac_rpc.sql uygulanmis (idare_ata_torun +
-- dogrudan_temin_ilanlari.detsis_no + idx_dt_detsis). O dosya prod'a uygulanmis
-- oldugundan burada TEKRAR kosulmaz — yeni RPC bu AYRI dosyada.
--
-- ANON'A KAPALI: idare-DT bagi kimlik verisi; fonksiyon PUBLIC EXECUTE ile
-- dogar → REVOKE ACIKCA yazildi (bkz. migration_idare_dal_ihaleler.sql).
--
-- Uygulama:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_dal_son_dt.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- idare_dal_son_dt(detsis, limit) — dalin (kendisi + tum alt birimleri) en
-- guncel dogrudan teminleri. Siralama: ilan_tarihi DESC NULLS LAST.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_dal_son_dt(
  p_detsis text, p_limit integer DEFAULT 20
)
RETURNS TABLE (
  dt_no text, baslik text, il text, usul text,
  ilan_tarihi timestamptz, durum text
)
LANGUAGE sql STABLE
AS $$
  SELECT d.dt_no, d.baslik, d.il, d.usul, d.ilan_tarihi, d.durum
    FROM public.idare_ata_torun at
    JOIN public.dogrudan_temin_ilanlari d ON d.detsis_no = at.torun_no
   WHERE at.ata_no = p_detsis
   ORDER BY d.ilan_tarihi DESC NULLS LAST
   LIMIT LEAST(COALESCE(p_limit, 20), 100);
$$;

-- Kok dallar on binlerce torun taramasi → 3s varsayilanin kenarina gelebilir
-- (bkz. hafiza statement-timeout-edge). idare_dal_son_ihaleler ile ayni desen.
ALTER FUNCTION public.idare_dal_son_dt(text, integer) SET statement_timeout = '15s';

REVOKE EXECUTE ON FUNCTION public.idare_dal_son_dt(text, integer) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.idare_dal_son_dt(text, integer) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KURULUM SONRASI DOGRULAMA
-- =============================================================================
-- psql (supabase_admin):
--   SELECT * FROM public.idare_dal_son_dt('<detsis>', 20);
--
-- ANON DOGRULAMASI (deploy sonrasi SART — bkz. hafiza anon-maske):
--   curl -s -o /dev/null -w '%{http_code}\n' \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     -X POST https://ihaleglobal.com/rest/v1/rpc/idare_dal_son_dt \
--     -H 'Content-Type: application/json' -d '{"p_detsis":"0"}'
--   -- beklenen: 401/403/404 (200 DONMEMELI)
