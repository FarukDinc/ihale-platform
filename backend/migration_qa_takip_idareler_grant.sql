-- ============================================================================
-- migration_qa_takip_idareler_grant.sql — 26-7 idare remap: takip_idareler UPDATE yetkisi
--   (2 Ağu 2026). idare_ad_temizle --apply, ilanlar + dogrudan_temin_ilanlari'nı 138 idarede
--   başarıyla güncelledi ama takip_idareler'de HER satır 403/42501 "permission denied" verdi:
--   service_role'e bu tabloda UPDATE GRANT'ı yokmuş. service_role backend'in güvenilir (RLS-bypass)
--   rolü; idare adı bakım-yazması meşru. Grant verilince apply --sadece-takip ile takip listesi de
--   yeni adlara taşınır (yoksa kullanıcının takip ettiği idare eski bozuk adda kalır, yeni ilanlarla
--   eşleşmez).
--
-- Çalıştırma (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_takip_idareler_grant.sql
-- ============================================================================
GRANT UPDATE ON public.takip_idareler TO service_role;

NOTIFY pgrst, 'reload schema';
