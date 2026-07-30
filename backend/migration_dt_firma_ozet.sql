-- ============================================================
-- MADDE 16 (part 1) — DT kazanan firma bazında özet (30 Tem 2026)
-- ------------------------------------------------------------
-- AMAÇ: Bir firmanın DOĞRUDAN TEMİN kazanımlarını firma bazında topla. Firma Analizi
--   şu an yalnız ihale evrenini (yukleniciler+ihale_sonuclari) gösteriyor; firmanın DT
--   tarafı hiç görünmüyordu. Veri VAR: dogrudan_temin_sonuclari (853K satır) —
--   kazanan_firma (isim), kazanan_bedel, dt_no. İl/kategori dogrudan_temin_ilanlari'nda.
--
-- YAKLAŞIM: yukleniciler.id'ye RİSKLİ isim-eşlemesi YAPMADAN, DT'yi kazanan firma ADINA
--   göre (tr_fold ile normalize edilmiş EŞİT eşleşme — sahte pozitif üretmeyen tutucu yol)
--   topla. Firma Analizi firmanın adını (FIRMA) bu RPC'ye geçirir → o firmanın DT özeti.
--   İki evren ölçek farkı (DT medyanı ≈ ₺37 bin) korunur: sonuç AYRI kutu/rozetle sunulur,
--   ihale cirosuyla TOPLANMAZ (bkz. hafıza dt-kazanan-captcha, vkn-yok-beyan-rozet).
--
-- Çalıştır (yeni fonksiyon + indeks → superuser gerekir; postgres tablo sahibi değil):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_firma_ozet.sql
-- ============================================================

BEGIN;

-- tr_fold(kazanan_firma) fonksiyonel indeksi — isim-normalize eşleşme için ŞART
-- (mevcut idx_dt_sonuc_kazanan_firma HAM ada göre; tr_fold eşitliği onu kullanamaz).
-- 853K satır → indekssiz tr_fold eşitliği seq scan/timeout riski.
CREATE INDEX IF NOT EXISTS idx_dt_sonuc_kazanan_fold
  ON public.dogrudan_temin_sonuclari (public.tr_fold(kazanan_firma))
  WHERE kazanan_firma IS NOT NULL;

COMMIT;

-- Firma adı → o firmanın DT özeti. SECURITY DEFINER: kazanan_firma anon'a kapalı,
-- ama bu RPC yalnız authenticated'a açık ve toplu (agregat) veri döndürür.
CREATE OR REPLACE FUNCTION public.firma_dt_ozet(p_firma_ad text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH d AS (
    SELECT s.dt_no, s.kazanan_bedel
    FROM public.dogrudan_temin_sonuclari s
    WHERE s.kazanan_firma IS NOT NULL
      AND public.tr_fold(s.kazanan_firma) = public.tr_fold(p_firma_ad)
  ),
  ozet AS (
    SELECT count(*)                                         AS dt_sayisi,
           count(kazanan_bedel)                             AS bedelli_sayisi,
           COALESCE(sum(kazanan_bedel), 0)                  AS toplam_bedel,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY kazanan_bedel)
             FILTER (WHERE kazanan_bedel IS NOT NULL)       AS medyan_bedel
    FROM d
  ),
  il AS (
    SELECT i.il, count(*) AS n
    FROM d JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = d.dt_no
    WHERE i.il IS NOT NULL GROUP BY i.il ORDER BY n DESC LIMIT 10
  ),
  kat AS (
    SELECT i.kategori, count(*) AS n
    FROM d JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = d.dt_no
    WHERE i.kategori IS NOT NULL GROUP BY i.kategori ORDER BY n DESC LIMIT 8
  )
  SELECT jsonb_build_object(
    'dt_sayisi',      (SELECT dt_sayisi FROM ozet),
    'bedelli_sayisi', (SELECT bedelli_sayisi FROM ozet),
    'toplam_bedel',   (SELECT toplam_bedel FROM ozet),
    'medyan_bedel',   (SELECT medyan_bedel FROM ozet),
    'iller',       COALESCE((SELECT jsonb_agg(jsonb_build_object('il', il, 'sayi', n)) FROM il), '[]'::jsonb),
    'kategoriler', COALESCE((SELECT jsonb_agg(jsonb_build_object('kategori', kategori, 'sayi', n)) FROM kat), '[]'::jsonb)
  );
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_ozet(text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_ozet(text) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle, örnek bir firma adıyla):
--   SELECT public.firma_dt_ozet('ÜNTES ISITMA KLİMA SOĞUTMA SANAYİ VE TİCARET ANONİM ŞİRKETİ');
