-- ============================================================
-- MV sahip düzeltmesi (31 Tem 2026) — MADDE 12/14 gece refresh için
-- ------------------------------------------------------------
-- dt_analiz_mv, dt_analiz_yil_mv ve il_yil_firma supabase_admin ile oluşturuldu (fonksiyonlar öyle
-- olmak zorundaydı) → sahibi supabase_admin. run_scraper.sh gece refresh'i `-U postgres` ile çalışır;
-- REFRESH MATERIALIZED VIEW sahiplik/superuser ister → postgres "permission denied for materialized
-- view" alır ve SESSİZCE atlar (cron 2>&1 log'a yazar ama devam eder) → bu 3 MV her gece BAYAT kalır.
-- Kanıt (1 Ağu denetim): pg_matviews'te bu 3'ü supabase_admin sahipli; `REFRESH … -U postgres` = hata.
-- Diğer TÜM MV'ler zaten postgres sahipli. Tutarlılık için bu 3'ünü de postgres'e devret. (dt_analiz_mv
-- tanımı `_dt_ozet_json()` SECURITY DEFINER çağırır → refresh definer yetkisiyle çalışır; sahip değişimi
-- okuma/veri yolunu BOZMAZ. CONCURRENTLY için gereken benzersiz indeks zaten var — denetimde doğrulandı.)
--
-- ⚠️ NOT (1 Ağu düzeltme): ESKİ sürüm yalnız 2 MV'yi devrediyordu, dt_analiz_mv'yi ATLIYORDU (o da
--    supabase_admin sahibiydi → yine bayatlıyordu). Üçü de eklendi.
--
-- Çalıştır (superuser — mevcut sahip supabase_admin devredebilir):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_mv_owner_fix.sql
-- ============================================================

ALTER MATERIALIZED VIEW public.il_yil_firma      OWNER TO postgres;
ALTER MATERIALIZED VIEW public.dt_analiz_yil_mv  OWNER TO postgres;
ALTER MATERIALIZED VIEW public.dt_analiz_mv      OWNER TO postgres;

-- ⚠️ (1 Ağu KANIT — kritik ikinci adım): dt_analiz_mv ve dt_analiz_yil_mv tanımları
-- `_dt_ozet_json()` (SECURITY DEFINER, ACL yalnız supabase_admin=X) ÇAĞIRIR. Sahip postgres'e
-- geçince REFRESH artık postgres olarak çalışır → fonksiyonu ÇAĞIRMAK için EXECUTE ister; postgres
-- superuser DEĞİL → "permission denied for function _dt_ozet_json" (owner devri TEK BAŞINA bu 2 MV'yi
-- BOZAR — il_yil_firma bu fonksiyonu çağırmaz, o yüzden yalnız o düzelirdi). Çözüm: postgres'e EXECUTE
-- ver. SECURITY DEFINER olduğundan İÇ veri erişimi yine supabase_admin yetkisiyle çalışır; bu grant
-- SADECE çağrı iznini açar ve postgres iç roldür (anon/authenticated/service_role'e dokunmaz).
GRANT EXECUTE ON FUNCTION public._dt_ozet_json(text, text, text, integer) TO postgres;

-- Doğrulama:
--   \dm+ public.il_yil_firma      -- Owner: postgres olmalı
--   REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_yil_firma;   -- postgres ile hatasız
