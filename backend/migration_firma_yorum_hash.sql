-- =============================================================================
-- migration_firma_yorum_hash.sql — Firma AI yorumuna VERİ-HASH kolonu
-- =============================================================================
--
-- AMAÇ: Firma AI yorumu (yukleniciler.ai_yorum) şimdiye dek yalnız 7 günlük tarih
-- cache'iyle çalışıyordu; veri değişse bile yorum kendiliğinden güncellenmiyordu.
-- Bu kolon, kurum tarafındaki ai_yorumlari.veri_hash muadilidir: gece tazeleme
-- (backend/ai_yorum_tazele.py) firma kırılımlarının (firma_ai_yorum.firma_veri_hash)
-- güncel imzasını bu kolonla kıyaslar; DEĞİŞTİYSE ai_yorum/ai_yorum_tarih/ai_yorum_hash
-- NULL'lanır → kullanıcı sonraki görüntülemede güncel veriye dayalı taze yorum alır.
--
-- Nullable + default YOK → hızlı metadata değişimi (tablo yeniden yazılmaz).
-- lock_timeout: gündüz yoğun okuma/yuklenici_yenile ile ACCESS EXCLUSIVE çakışırsa
-- kuyruk-kilidi (site donması) yerine hızlıca vazgeçilsin (yeniden denenir).
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_firma_yorum_hash.sql
-- =============================================================================

SET lock_timeout = '5s';
ALTER TABLE public.yukleniciler ADD COLUMN IF NOT EXISTS ai_yorum_hash text;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_name='yukleniciler' AND column_name='ai_yorum_hash';
