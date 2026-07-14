-- ============================================================
-- İhaleGlobal — takip_firmalar'a eksik service_role GRANT'i
--
-- Kök neden: migration_takip_firmalar.sql (Faz E1) sadece
-- "GRANT ... TO authenticated" yapmıştı, service_role'e hiç GRANT verilmemişti.
-- Daha sonra yazılan migration_takip_idareler.sql'de bu unutulmamış (hem
-- authenticated hem service_role grant ediliyor) — takip_firmalar geride kalmış.
--
-- Sonuç: rakip_bildirim.py (gece cron, service_role key ile REST üzerinden
-- takip_firmalar'ı okur) her gece "403 permission denied for table
-- takip_firmalar" hatasıyla başarısız oluyordu — yani rakip (firma) takibi
-- bildirimleri deploy edildiğinden beri (12 Tem) HİÇ gönderilmemiş olabilir.
--
-- Additive/güvenli: sadece eksik GRANT'i ekler, RLS politikalarına dokunmaz
-- (service_role zaten RLS'i bypass eder, sorun salt tablo-seviyesi izindi).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_takip_firmalar_service_role_grant.sql
-- ============================================================

BEGIN;

GRANT SELECT ON public.takip_firmalar TO service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT grantee, privilege_type FROM information_schema.role_table_grants
WHERE table_name = 'takip_firmalar' AND grantee = 'service_role';
