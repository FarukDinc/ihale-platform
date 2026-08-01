-- ============================================================================
-- migration_qa_26_23_kurum_mu.sql — 26-23: DMO/kamu kuruluşları yüklenici listesinde
--   (2 Ağu 2026). Firmalar dizini İHALE modu yukleniciler'i doğrudan PostgREST ile
--   sorguluyor → filtrede firma_kurum_mu(ad) çağrılamaz. Kalıcı `kurum_mu` kolonu ekle,
--   firma_kurum_mu ile doldur; frontend .not('kurum_mu','is',true) ile kamu kuruluşlarını
--   varsayılan gizler (NULL/yeni firma yine görünür → kaybolmaz). Gece run_scraper.sh
--   NULL olanları doldurur.
--
-- firma_kurum_mu: migration_firma_dt_liste_kamu.sql (kurumsal sonek + DMO/PTT/İşyurtları).
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_23_kurum_mu.sql
-- Idempotent.
-- ============================================================================
BEGIN;
ALTER TABLE public.yukleniciler ADD COLUMN IF NOT EXISTS kurum_mu boolean;

-- İlk doldurma (220K firma; firma_kurum_mu metin-desen, saniyeler mertebesi):
UPDATE public.yukleniciler SET kurum_mu = public.firma_kurum_mu(ad)
 WHERE kurum_mu IS NULL;

-- Kısmi indeks: liste sorgusu "kamu olmayan" (kurum_mu IS NOT TRUE) üzerinden gider.
CREATE INDEX IF NOT EXISTS idx_yuk_kurum_mu_true ON public.yukleniciler(kurum_mu) WHERE kurum_mu = true;
COMMIT;

NOTIFY pgrst, 'reload schema';

\echo '--- kurum_mu dağılımı ---'
SELECT kurum_mu, count(*) FROM public.yukleniciler GROUP BY kurum_mu;
\echo '--- örnek: gizlenecek kamu kuruluşları (kurum_mu=true, en çok sözleşmeli) ---'
SELECT left(ad,55) ad, toplam_sozlesme_sayisi FROM public.yukleniciler
 WHERE kurum_mu = true ORDER BY toplam_sozlesme_sayisi DESC NULLS LAST LIMIT 10;
