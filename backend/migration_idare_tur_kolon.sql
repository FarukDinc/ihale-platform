-- ============================================================================
-- migration_idare_tur_kolon.sql — idare_tur'u ilanlar + DT tablolarına taşı
--                                                              (19 Tem 2026)
-- NEDEN DENORMALİZE KOLON (join/view değil):
--   ihaleler.html ve dogrudan-temin.html filtreleri düz PostgREST çağrıları:
--     .eq('il', il) .eq('kategori', kategori) .eq('tur', tur) ...
--   Aynı desene oturması için tabloya `idare_tur` kolonu ekliyoruz → frontend'e
--   TEK SATIR eklenir (.eq('idare_tur', ...)), RPC/view yazmaya gerek kalmaz.
--   Veri gece scraper'ında tazelenir (idare_tur tablosu otoriter kaynak).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_tur_kolon.sql
-- Idempotent. UPDATE'ler uzun sürebilir (350K+ satır) — tek seferlik.
-- ============================================================================

-- ── 1) Kolonlar ─────────────────────────────────────────────────────────────
ALTER TABLE public.ilanlar                  ADD COLUMN IF NOT EXISTS idare_tur text;
ALTER TABLE public.dogrudan_temin_ilanlari  ADD COLUMN IF NOT EXISTS idare_tur text;

-- Filtre indeksleri (kullanıcı "sadece belediyeler" derse buradan gider)
CREATE INDEX IF NOT EXISTS idx_ilanlar_idare_tur ON public.ilanlar (idare_tur) WHERE idare_tur IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dt_idare_tur      ON public.dogrudan_temin_ilanlari (idare_tur) WHERE idare_tur IS NOT NULL;

-- ── 2) Tazeleme fonksiyonu (gece scraper'ı bunu çağırır) ────────────────────
-- idare_tur eşleme tablosundan iki ana tabloyu günceller.
-- Yalnız DEĞİŞENLERİ yazar (IS DISTINCT FROM) → gereksiz WAL/şişme yok.
CREATE OR REPLACE FUNCTION public.idare_tur_tazele()
  RETURNS jsonb
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = public
AS $$
DECLARE
  n_ilan int;
  n_dt   int;
BEGIN
  UPDATE public.ilanlar i
     SET idare_tur = t.tur
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(i.idare)
     AND i.idare_tur IS DISTINCT FROM t.tur;
  GET DIAGNOSTICS n_ilan = ROW_COUNT;

  UPDATE public.dogrudan_temin_ilanlari d
     SET idare_tur = t.tur
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(d.idare)
     AND d.idare_tur IS DISTINCT FROM t.tur;
  GET DIAGNOSTICS n_dt = ROW_COUNT;

  RETURN jsonb_build_object('ilanlar_guncellenen', n_ilan, 'dt_guncellenen', n_dt);
END;
$$;

REVOKE EXECUTE ON FUNCTION public.idare_tur_tazele() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.idare_tur_tazele() TO service_role;

-- ── 3) İlk doldurma ─────────────────────────────────────────────────────────
SELECT public.idare_tur_tazele();

-- ── 4) Kapsama raporu düzeltmesi ────────────────────────────────────────────
-- ÖNCEKİ HATA: fonksiyon çağıranın yetkisiyle çalışıyordu → anon'da
--   "permission denied for table ilanlar" (misafir maskesi). Yalnız SAYI/YÜZDE
--   döndürüyor, satır sızdırmıyor → SECURITY DEFINER güvenli.
-- Artık denormalize kolondan okuyor (join yok, hızlı).
CREATE OR REPLACE FUNCTION public.idare_tur_kapsama()
  RETURNS jsonb
  LANGUAGE sql
  STABLE
  SECURITY DEFINER
  SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'toplam_ihale',  (SELECT count(*) FROM public.ilanlar),
    'siniflanmis',   (SELECT count(*) FROM public.ilanlar WHERE idare_tur IS NOT NULL),
    'kapsama_yuzde', (SELECT round(100.0 * count(*) FILTER (WHERE idare_tur IS NOT NULL)
                                   / nullif(count(*), 0), 1) FROM public.ilanlar),
    'tur_dagilimi',  (SELECT coalesce(jsonb_object_agg(coalesce(idare_tur, 'siniflanmamis'), n), '{}'::jsonb)
                        FROM (SELECT idare_tur, count(*) n FROM public.ilanlar GROUP BY idare_tur) x),
    'dt_siniflanmis',(SELECT count(*) FROM public.dogrudan_temin_ilanlari WHERE idare_tur IS NOT NULL),
    'esleme_sayisi', (SELECT count(*) FROM public.idare_tur)
  );
$$;

GRANT EXECUTE ON FUNCTION public.idare_tur_kapsama() TO anon, authenticated, service_role;
ALTER FUNCTION public.idare_tur_kapsama() SET statement_timeout = '30s';

-- ── 5) Tür listesi (arayüz dropdown'ı — sayılarla) ──────────────────────────
-- Yalnız VERİSİ OLAN türleri döndürür ki dropdown'da boş seçenek çıkmasın.
CREATE OR REPLACE FUNCTION public.idare_tur_sayim()
  RETURNS jsonb
  LANGUAGE sql
  STABLE
  SECURITY DEFINER
  SET search_path = public
AS $$
  SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.adet DESC), '[]'::jsonb)
  FROM (
    SELECT idare_tur AS tur, count(*) AS adet
    FROM public.ilanlar
    WHERE idare_tur IS NOT NULL
    GROUP BY idare_tur
  ) t;
$$;

GRANT EXECUTE ON FUNCTION public.idare_tur_sayim() TO anon, authenticated, service_role;
ALTER FUNCTION public.idare_tur_sayim() SET statement_timeout = '20s';

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT public.idare_tur_kapsama();
--   SELECT public.idare_tur_sayim();
--   SELECT idare_tur, count(*) FROM ilanlar GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
