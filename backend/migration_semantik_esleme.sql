-- ============================================================
-- İhalePlatform — Faz D3: Semantik Eşleşme (pgvector)
--
-- İlanlar ve firma profillerini 768-boyutlu embedding'e çevirip (backend/embed_ortak.py,
-- Gemini gemini-embedding-001) cosine benzerliğiyle "AI destekli uyum skoru" üretmenin
-- DB tarafı. Üretim tarafı ayrı: backend/ilan_embed_uret.py (gece cron, bounded batch)
-- + api.py PUT /profil (kullanıcı profilini kaydettiğinde kendi embedding'i tazelenir).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_semantik_esleme.sql
-- ============================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE public.ilanlar
  ADD COLUMN IF NOT EXISTS embedding vector(768),
  ADD COLUMN IF NOT EXISTS embedding_guncelleme TIMESTAMPTZ;

ALTER TABLE public.kullanici_profiller
  ADD COLUMN IF NOT EXISTS embedding vector(768),
  ADD COLUMN IF NOT EXISTS embedding_guncelleme TIMESTAMPTZ;

-- Aktif ilanlar arasında benzerlik aramasını hızlandırır (opsiyonel ama ucuz — sadece
-- embedding dolu satırlar indexlenir zaten NULL'lar HNSW'e girmez).
CREATE INDEX IF NOT EXISTS ilanlar_embedding_hnsw_idx
  ON public.ilanlar USING hnsw (embedding vector_cosine_ops);

-- Bir kullanıcının kendi firma-profili embedding'ine karşı, verilen ilan ID listesinin
-- cosine benzerliğini döner. SECURITY DEFINER + auth.uid() ZORUNLU (p_kullanici_id
-- parametre olarak ALINMAZ) — kullanici_profiller RLS'i own-row'a sıkılaştırıldığı için
-- (bkz. migration_kullanici_profiller_rls_sikilastir.sql, gizlilik açığı dersi) bu RPC'nin
-- de aynı ilkeyi bozmaması gerekiyor: sadece çağıranın KENDİ embedding'i kullanılabilir.
CREATE OR REPLACE FUNCTION public.semantik_skor_batch(p_ilan_ids uuid[])
RETURNS TABLE(ilan_id uuid, skor numeric)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public
AS $$
  SELECT i.id, GREATEST(0, LEAST(1, 1 - (i.embedding <=> p.embedding)))::numeric
  FROM public.ilanlar i, public.kullanici_profiller p
  WHERE i.id = ANY(p_ilan_ids)
    AND p.id = auth.uid()
    AND i.embedding IS NOT NULL
    AND p.embedding IS NOT NULL;
$$;

GRANT EXECUTE ON FUNCTION public.semantik_skor_batch(uuid[]) TO authenticated;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT proname, prosecdef FROM pg_proc WHERE proname = 'semantik_skor_batch';
