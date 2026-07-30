-- ============================================================
-- MV sahip düzeltmesi (31 Tem 2026) — MADDE 12/14 gece refresh için
-- ------------------------------------------------------------
-- il_yil_firma ve dt_analiz_yil_mv supabase_admin ile oluşturuldu (fonksiyonlar öyle olmak
-- zorundaydı) → sahibi supabase_admin. run_scraper.sh gece refresh'i `-U postgres` ile çalışır;
-- REFRESH MATERIALIZED VIEW sahiplik/superuser ister → postgres "must be owner" alır.
-- Diğer tüm MV'ler postgres sahipli (eski migration'lar -U postgres ile kurulmuştu). Tutarlılık
-- için bu ikisini de postgres'e devret. (İçindeki _dt_ozet_json SECURITY DEFINER olduğundan
-- refresh'te yine supabase_admin yetkisiyle çalışır; sahip değişimi okuma yolunu bozmaz.)
--
-- Çalıştır (superuser — mevcut sahip supabase_admin devredebilir):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_mv_owner_fix.sql
-- ============================================================

ALTER MATERIALIZED VIEW public.il_yil_firma      OWNER TO postgres;
ALTER MATERIALIZED VIEW public.dt_analiz_yil_mv  OWNER TO postgres;

-- Doğrulama:
--   \dm+ public.il_yil_firma      -- Owner: postgres olmalı
--   REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_yil_firma;   -- postgres ile hatasız
