-- ============================================================
-- TAKİP LİSTEM — sektör takibi + panel RPC'leri (26 Tem 2026)
-- takip_firmalar / takip_idareler ZATEN CANLI; sektör için üçüncü ikizi kurar.
-- Blueprint: bana_ozel_blueprintler.md (gerçek şemaya doğrulanmış).
-- ============================================================

-- 1) takip_sektorler — takip_idareler ile birebir desen (service_role GRANT baştan!)
CREATE TABLE IF NOT EXISTS public.takip_sektorler (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id uuid NOT NULL,
  sektor       text NOT NULL,
  olusturulma  timestamptz DEFAULT now(),
  UNIQUE (kullanici_id, sektor)
);
ALTER TABLE public.takip_sektorler ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "takip_sektorler_kendi_okur"  ON public.takip_sektorler;
DROP POLICY IF EXISTS "takip_sektorler_kendi_ekler"  ON public.takip_sektorler;
DROP POLICY IF EXISTS "takip_sektorler_kendi_siler"  ON public.takip_sektorler;
CREATE POLICY "takip_sektorler_kendi_okur" ON public.takip_sektorler FOR SELECT USING (auth.uid() = kullanici_id);
CREATE POLICY "takip_sektorler_kendi_ekler" ON public.takip_sektorler FOR INSERT WITH CHECK (auth.uid() = kullanici_id);
CREATE POLICY "takip_sektorler_kendi_siler" ON public.takip_sektorler FOR DELETE USING (auth.uid() = kullanici_id);
GRANT SELECT, INSERT, DELETE ON public.takip_sektorler TO authenticated;
GRANT SELECT                 ON public.takip_sektorler TO service_role;  -- gece bildirim okur
-- anon'a HİÇ GRANT yok (varsayılan REVOKE) — deploy sonrası anon curl → 401 beklenir.

-- 2) Panel özeti — takip firma/kurum/sektör sayıları + son 30g takip-firma sözleşmesi
CREATE OR REPLACE FUNCTION public.takip_ozet()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  SELECT jsonb_build_object(
    'firma',  (SELECT count(*) FROM public.takip_firmalar  WHERE kullanici_id = auth.uid()),
    'idare',  (SELECT count(*) FROM public.takip_idareler  WHERE kullanici_id = auth.uid()),
    'sektor', (SELECT count(*) FROM public.takip_sektorler WHERE kullanici_id = auth.uid()),
    'yeni_sozlesme_30g', (
      SELECT count(*) FROM public.takip_firmalar tf
      JOIN public.ihale_sonuclari s ON s.kazanan_firma_fold = public.tr_fold(tf.firma_ad)
      WHERE tf.kullanici_id = auth.uid() AND s.sonuc_tarihi >= now() - interval '30 days')
  );
$$;
REVOKE ALL ON FUNCTION public.takip_ozet() FROM public, anon;
GRANT EXECUTE ON FUNCTION public.takip_ozet() TO authenticated, service_role;

-- 3) Takip edilen firmaların sözleşme akışı (keyset sayfalama, OFFSET değil)
CREATE OR REPLACE FUNCTION public.takip_firma_sozlesmeleri(
  p_limit int DEFAULT 30, p_once timestamptz DEFAULT NULL)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  WITH takip AS (
    SELECT public.tr_fold(firma_ad) AS fold, min(firma_ad) AS firma_ad
    FROM public.takip_firmalar WHERE kullanici_id = auth.uid()
    GROUP BY public.tr_fold(firma_ad)
  )
  SELECT COALESCE(jsonb_agg(row_to_json(x)::jsonb ORDER BY x.sonuc_tarihi DESC NULLS LAST), '[]'::jsonb)
  FROM (
    SELECT s.id, s.ilan_id, t.firma_ad AS takip_firma, s.kazanan_firma,
           s.kazanan_teklif, s.sozlesme_bedeli, s.sozlesme_tarihi, s.sonuc_tarihi,
           i.il, i.kategori, s.fesih_var, s.tasfiye_var, s.lot_sayisi, i.baslik, i.ikn
    FROM takip t
    JOIN public.ihale_sonuclari s ON s.kazanan_firma_fold = t.fold
    LEFT JOIN public.ilanlar i ON i.id = s.ilan_id
    WHERE (p_once IS NULL OR s.sonuc_tarihi < p_once)
    ORDER BY s.sonuc_tarihi DESC NULLS LAST
    LIMIT LEAST(p_limit, 50)
  ) x;
$$;
REVOKE ALL ON FUNCTION public.takip_firma_sozlesmeleri(int, timestamptz) FROM public, anon;
GRANT EXECUTE ON FUNCTION public.takip_firma_sozlesmeleri(int, timestamptz) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
