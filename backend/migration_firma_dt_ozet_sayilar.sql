-- ============================================================
-- firma_dt_ozet — il_sayisi + kategori_sayisi (DISTINCT) ekle (31 Tem 2026)
-- ------------------------------------------------------------
-- firma-analiz DT KPI satırı "Kapsanan İl (DT)" / "Kapsanan Sektör (DT)" ister; firma_dt_ozet
-- yalnız top-10/8 il/kategori LİSTESİ dönüyordu (sayı ≤10 → yanıltıcı). Toplam DISTINCT il ve
-- kategori sayısı eklenir. İmza/return tipi (jsonb) AYNI → CREATE OR REPLACE, frontend geriye
-- uyumlu (yeni alanlar). Firma-scope'lu (d küçük) → ek join ucuz.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_ozet_sayilar.sql
-- ============================================================

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
  dj AS (   -- d ⋈ ilan: il + kategori (dağılım + distinct sayım tek join'den)
    SELECT i.il, i.kategori
    FROM d JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = d.dt_no
  ),
  il AS (
    SELECT il, count(*) AS n FROM dj WHERE il IS NOT NULL AND btrim(il) <> ''
    GROUP BY il ORDER BY n DESC LIMIT 10
  ),
  kat AS (
    SELECT kategori, count(*) AS n FROM dj WHERE kategori IS NOT NULL AND btrim(kategori) <> ''
    GROUP BY kategori ORDER BY n DESC LIMIT 8
  ),
  says AS (
    SELECT count(DISTINCT il)       FILTER (WHERE il IS NOT NULL AND btrim(il) <> '')             AS il_sayisi,
           count(DISTINCT kategori) FILTER (WHERE kategori IS NOT NULL AND btrim(kategori) <> '') AS kategori_sayisi
    FROM dj
  )
  SELECT jsonb_build_object(
    'dt_sayisi',      (SELECT dt_sayisi FROM ozet),
    'bedelli_sayisi', (SELECT bedelli_sayisi FROM ozet),
    'toplam_bedel',   (SELECT toplam_bedel FROM ozet),
    'medyan_bedel',   (SELECT medyan_bedel FROM ozet),
    'il_sayisi',      (SELECT il_sayisi FROM says),
    'kategori_sayisi',(SELECT kategori_sayisi FROM says),
    'iller',       COALESCE((SELECT jsonb_agg(jsonb_build_object('il', il, 'sayi', n)) FROM il), '[]'::jsonb),
    'kategoriler', COALESCE((SELECT jsonb_agg(jsonb_build_object('kategori', kategori, 'sayi', n)) FROM kat), '[]'::jsonb)
  );
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_ozet(text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_ozet(text) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
