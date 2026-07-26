-- ============================================================
-- BENİM FİRMAM → kişisel eşleşme (26 Tem 2026)
-- Kullanıcı firmasını seçer → firmanın GEÇMİŞ kazanımlarına benzer AKTİF ihaleler.
-- Blueprint: bana_ozel_blueprintler.md (paralel tasarım turu, gerçek şemaya doğrulanmış).
-- Yeniden kullanılan: ihale_konu_kelimeleri(), idx_ilanlar_baslik_fold_trgm, tr_fold,
--   ihaleye_uygun_firmalar v3 bant/skor mantığı (tersi yön: firma→ihale).
-- ============================================================

BEGIN;

-- 1) Kalıcı firma seçimi (kullanici_profiller'e). anon zaten tablodan REVOKE'lu → ek maske yok.
ALTER TABLE public.kullanici_profiller
  ADD COLUMN IF NOT EXISTS firma_id      uuid REFERENCES public.yukleniciler(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS firma_secildi timestamptz;

-- 2) ihale_sonuclari.yuklenici_id İNDEKSİ EKSİKTİ → firma profili çıkarımı seq scan/timeout riski.
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_yuklenici_id
  ON public.ihale_sonuclari (yuklenici_id) WHERE yuklenici_id IS NOT NULL;

COMMIT;

-- 3) Firma seçimini yaz — SECURITY DEFINER (kullanici_profiller'de UPDATE policy YOK).
--    Her kullanıcıda satır olmayabilir (16 satır) → UPSERT. Yalnız gerçek yüklenici id kabul.
CREATE OR REPLACE FUNCTION public.firmami_belirle(p_yuklenici_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'giris gerekli'; END IF;
  IF p_yuklenici_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM public.yukleniciler WHERE id = p_yuklenici_id) THEN
    RAISE EXCEPTION 'firma bulunamadi';
  END IF;
  INSERT INTO public.kullanici_profiller (id, firma_id, firma_secildi)
  VALUES (auth.uid(), p_yuklenici_id, now())
  ON CONFLICT (id) DO UPDATE SET firma_id = EXCLUDED.firma_id, firma_secildi = now();
END; $$;
REVOKE EXECUTE ON FUNCTION public.firmami_belirle(uuid) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmami_belirle(uuid) TO authenticated, service_role;

-- 4) Seçili firmanın bilgisini getir (dashboard bloğu için firma adı/ciro rozeti).
CREATE OR REPLACE FUNCTION public.firmam_getir()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT CASE WHEN kp.firma_id IS NULL THEN NULL
    ELSE jsonb_build_object('firma_id', y.id, 'ad', y.ad, 'il', y.il,
           'toplam_ciro', y.toplam_ciro, 'toplam_sozlesme_sayisi', y.toplam_sozlesme_sayisi) END
  FROM public.kullanici_profiller kp
  LEFT JOIN public.yukleniciler y ON y.id = kp.firma_id
  WHERE kp.id = auth.uid();
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_getir() FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_getir() TO authenticated, service_role;

-- 5) Ana eşleşme RPC'si: firmanın kazanım profili → benzer AKTİF ihaleler (v3 bant + konu-kelime).
CREATE OR REPLACE FUNCTION public.firma_icin_acik_ihaleler(
  p_yuklenici_id uuid, p_limit int DEFAULT 12, p_bant numeric DEFAULT 5)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE AS $$
  WITH firma AS (
    SELECT
      (SELECT array_agg(k) FROM (
         SELECT i.kategori k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL
         GROUP BY i.kategori ORDER BY count(*) DESC LIMIT 5) t)          AS kategoriler,
      (SELECT array_agg(DISTINCT i.il) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.il IS NOT NULL)       AS iller,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))
         FROM public.ihale_sonuclari s WHERE s.yuklenici_id=p_yuklenici_id) AS bedel
  )
  SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
         i.yaklasik_maliyet_min::numeric, i.yaklasik_maliyet_max::numeric, i.tahmini_bedel::numeric,
         i.son_teklif_tarihi::timestamptz,
         round((
           (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 40 ELSE 0 END)
         + (CASE WHEN i.il = ANY(f.iller) THEN 15 ELSE 0 END)
         + (CASE WHEN f.bedel IS NULL OR f.bedel<=0 THEN 0
                 ELSE 20*(1 - LEAST(abs(ln(GREATEST(
                        COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0),1),1)::numeric/f.bedel))/ln(p_bant),1)) END)
         )::numeric, 1)                                                    AS skor,
         (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 'Uzmanlık alanınız' ELSE 'Benzer konu' END
          || CASE WHEN i.il = ANY(f.iller) THEN ' · daha önce iş aldığınız il' ELSE '' END) AS eslesme_nedeni
  FROM public.ilanlar i, firma f
  WHERE i.durum='aktif'
    AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
    AND ( i.kategori = ANY(f.kategoriler)
       OR EXISTS (
            SELECT 1 FROM public.ihale_konu_kelimeleri(
              (SELECT string_agg(i2.baslik,' ') FROM (
                 SELECT i3.baslik FROM public.ihale_sonuclari s2
                   JOIN public.ilanlar i3 ON i3.id=s2.ilan_id
                 WHERE s2.yuklenici_id=p_yuklenici_id LIMIT 50) i2)) t
            WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%') )
    AND (f.bedel IS NULL OR f.bedel<=0
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0)) IS NULL
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0))
         BETWEEN f.bedel/p_bant AND f.bedel*p_bant)
  ORDER BY skor DESC, i.son_teklif_tarihi ASC NULLS LAST
  LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) TO authenticated, service_role;

-- 6) Dashboard varyantı: firma id'yi client'tan almaz (anti-enumerasyon), oturumdan okur.
CREATE OR REPLACE FUNCTION public.firmam_acik_ihaleler(p_limit int DEFAULT 12)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT * FROM public.firma_icin_acik_ihaleler(
    (SELECT firma_id FROM public.kullanici_profiller WHERE id = auth.uid()), p_limit, 5);
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
