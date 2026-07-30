-- ============================================================
-- ilanlar.usul — ham i18n anahtarı sızıntısı temizliği (31 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: 1.296 kayıtta `usul` çözümlenmemiş Angular i18n anahtarı taşıyor, örn:
--   "TENDER_SEARCH.MAIN.PAGEITEM.TENDER_TYPE TENDER_SEARCH.ENUMERATIONS.SEARCH_METHOD.OPEN"
-- KÖK NEDEN: bu kayıtlar ekap_scraper.usul_donustur() guard'ı (satır 886-903) eklenmeden
--   ÖNCE yazıldı — EKAP sayfası, Angular çeviri sözlüğü DOM'a uygulanmadan önce okunmuş,
--   ham çeviri anahtarı metin olarak yakalanmış. Yeni kayıtlar artık temiz (Accept-Language
--   + usul_donustur). Bu tarihsel kalıntıyı AYNI eşlemeyle düzeltiyoruz.
-- Suffix → anlam: SEARCH_METHOD.OPEN = Açık İhale · BARGAIN = Pazarlık · AMONG_CERTAIN_BIDDERS
--   = Belli İstekliler Arasında · ENUMERATIONS.DIGER = Diğer.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_usul_i18n_temizlik.sql
-- ============================================================

UPDATE public.ilanlar SET usul = CASE
  WHEN upper(usul) LIKE '%OPEN%'                  THEN 'Açık İhale'
  WHEN upper(usul) LIKE '%AMONG_CERTAIN_BIDDERS%' THEN 'Belli İstekliler Arasında'
  WHEN upper(usul) LIKE '%BARGAIN%'               THEN 'Pazarlık Usulü'
  WHEN upper(usul) LIKE '%DESIGN_COMPETITION%'    THEN 'Tasarım Yarışması'
  WHEN upper(usul) LIKE '%DIRECT_PROCUREMENT%'    THEN 'Doğrudan Temin'
  WHEN upper(usul) LIKE '%FRAMEWORK_AGREEMENT%'   THEN 'Çerçeve Anlaşma'
  ELSE 'Diğer / İstisna'
END
WHERE usul ~ '(TENDER_SEARCH|PAGEITEM|ENUMERATIONS)';

-- Doğrulama (0 dönmeli):
--   SELECT count(*) FROM ilanlar WHERE usul ~ '(TENDER_SEARCH|PAGEITEM|ENUMERATIONS)';
