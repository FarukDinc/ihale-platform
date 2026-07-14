-- ============================================================
-- İhaleGlobal — yuklenici_yenile() RPC'sinin statement_timeout'unu artır
--
-- Kök neden: yuklenici_yenile() ihale_sonuclari (138K+ satır, gece backfill
-- ile büyüyor) ile ilanlar arasında tam JOIN+GROUP BY agregasyonu yapıp
-- ardından ihale_sonuclari üzerinde toplu UPDATE çalıştırıyor. PostgREST
-- rolünün varsayılan statement_timeout'u bu sorgu için yetersiz kaldı —
-- 13/14 Tem loglarında "57014 canceling statement due to statement timeout"
-- ile her gece başarısız oluyordu (yukleniciler tablosu tazelenmiyordu).
--
-- Additive/güvenli: sadece BU FONKSİYONA özel timeout ayarlar (ALTER FUNCTION
-- ... SET), global/diğer sorguları etkilemez. 5 dakika, veri büyüklüğüne göre
-- rahat bir üst sınır (mevcut çalıştırmalar saniyeler-birkaç dakika sürüyor).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_yuklenici_yenile_timeout_fix.sql
-- ============================================================

BEGIN;

ALTER FUNCTION yuklenici_yenile() SET statement_timeout = '300000';

COMMIT;

-- Kontrol (proconfig içinde statement_timeout görünmeli)
SELECT proname, proconfig FROM pg_proc WHERE proname = 'yuklenici_yenile';
