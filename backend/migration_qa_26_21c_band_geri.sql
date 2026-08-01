-- ============================================================================
-- migration_qa_26_21c_band_geri.sql — 26-21 GERİ ALMA (ürün kararı: band'i koru)
--   (2 Ağu 2026). migration_qa_26_data_fixes.sql, itiraz-bedeli kademesinden türetilen
--   yaklaşık maliyet BANDINI (10785492,43142132) yanlışlıkla "çöp" sanıp 2.940 aktif
--   ihalede null'lamıştı. Karar: band GERÇEK bir sinyal (KİK itiraz-bedeli kademesi,
--   AI teklif kullanır) → geri getir. itiraz_bedeli sağlam olduğu için birebir türetilir.
--   MALIYET_TABLOSU (ekap_scraper.py): 64652→(0,10.78M) 129385→(10.78M,43.14M)
--                                      194085→(43.14M,323.57M) 258810→(323.57M,NULL)
--   ⚠️ 26-21b (placeholder2) ÇALIŞTIRILMAYACAK — band silinmiyor, korunuyor.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_21c_band_geri.sql
-- Idempotent (yalnız min IS NULL + itiraz_bedeli dolu satırları türetir).
-- ============================================================================
\pset pager off
BEGIN;
\echo '26-21c: band geri turetilecek (min NULL + itiraz_bedeli dolu) satir sayisi:'
SELECT itiraz_bedeli, count(*) FROM ilanlar
 WHERE yaklasik_maliyet_min IS NULL AND itiraz_bedeli IN (64652,129385,194085,258810)
 GROUP BY itiraz_bedeli ORDER BY itiraz_bedeli;

UPDATE ilanlar SET yaklasik_maliyet_min = 0,         yaklasik_maliyet_max = 10785492
 WHERE itiraz_bedeli = 64652  AND yaklasik_maliyet_min IS NULL;
UPDATE ilanlar SET yaklasik_maliyet_min = 10785492,  yaklasik_maliyet_max = 43142132
 WHERE itiraz_bedeli = 129385 AND yaklasik_maliyet_min IS NULL;
UPDATE ilanlar SET yaklasik_maliyet_min = 43142132,  yaklasik_maliyet_max = 323566103
 WHERE itiraz_bedeli = 194085 AND yaklasik_maliyet_min IS NULL;
UPDATE ilanlar SET yaklasik_maliyet_min = 323566103, yaklasik_maliyet_max = NULL
 WHERE itiraz_bedeli = 258810 AND yaklasik_maliyet_min IS NULL;
COMMIT;

\echo '=== KONTROL: aktif band dagilimi geri geldi mi ==='
SELECT yaklasik_maliyet_min, yaklasik_maliyet_max, count(*)
  FROM ilanlar WHERE durum='aktif' AND yaklasik_maliyet_min IS NOT NULL
 GROUP BY 1,2 ORDER BY 1;
