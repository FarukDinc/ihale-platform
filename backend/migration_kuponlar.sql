-- ============================================================
-- İhalePlatform — Ücretsiz Deneme Kuponları
--
-- Amaç: iyzico entegrasyonu tamamlanmadan önce, tanıdık firmalara test
-- amaçlı belirli süreli (1/3/6/12 ay) ücretsiz Pro/Kurumsal üyelik
-- verebilmek. Kuponlar backend/kupon_olustur.py ile (SSH üzerinden)
-- üretilir; kullanıcı kuponu fiyatlandirma_odeme_bolumu.html'deki
-- kutuya girer → backend /kupon-kullan (service_role) planı aktifleştirir.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kuponlar.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.kuponlar (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kod                 TEXT NOT NULL UNIQUE,
  plan_kodu           TEXT NOT NULL CHECK (plan_kodu IN ('standart', 'kurumsal')),
  sure_ay             INT  NOT NULL CHECK (sure_ay IN (1, 3, 6, 12)),
  max_kullanim        INT  NOT NULL DEFAULT 1,
  kullanim_sayisi     INT  NOT NULL DEFAULT 0,
  aktif               BOOLEAN NOT NULL DEFAULT true,
  aciklama            TEXT,
  son_kullanma_tarihi TIMESTAMPTZ,
  olusturulma         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.kupon_kullanimlari (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kupon_id         UUID NOT NULL REFERENCES public.kuponlar(id) ON DELETE CASCADE,
  kullanici_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  kullanilma_tarihi TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kupon_id, kullanici_id)
);

-- RLS açık, hiçbir client policy yok — yalnızca service_role (backend) erişir.
-- Kredi tablolarıyla aynı güvenlik deseni (bkz. kullanici_krediler).
ALTER TABLE public.kuponlar ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kupon_kullanimlari ENABLE ROW LEVEL SECURITY;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT relname, relrowsecurity FROM pg_class
 WHERE relname IN ('kuponlar', 'kupon_kullanimlari');
