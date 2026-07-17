-- ============================================================================
-- migration_uygun_firmalar_v3_3.sql (17 Tem 2026) — v3.2 düzeltmeleri (2 hata)
--
--  1) TİP: kazanan_teklif/sozlesme_bedeli kolonları BIGINT; plpgsql RETURN QUERY
--     (SQL fonksiyonların aksine) örtük coercion yapmaz → "Returned type bigint
--     does not match expected type numeric in column 5". max(...)::numeric cast'i.
--  2) DURUM DEĞERİ: ilanlar_durum_check = {taslak, aktif, kapali, iptal, sonuclandi}.
--     Bayatlama 'kapandi' değil 'kapali' yazmalı (v3.1'deki ERROR'un düzeltmesi).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_uygun_firmalar_v3_3.sql
-- ============================================================================

CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar(
  p_kategori text,
  p_il       text    DEFAULT NULL,
  p_bedel    numeric DEFAULT NULL,
  p_limit    int     DEFAULT 20,
  p_baslik   text    DEFAULT NULL,
  p_bant     numeric DEFAULT 5
)
RETURNS TABLE (
  kazanan_firma    text,
  yuklenici_id     uuid,
  firma_il         text,
  kategori_kazanim bigint,
  max_kazanim      numeric,
  ort_kazanim      numeric,
  ayni_il          boolean,
  kapasite_uygun   boolean,
  skor             numeric
)
LANGUAGE plpgsql STABLE
AS $fn$
BEGIN
  -- Dayanak yoksa gösterme kuralı: ne kanonik kategori ne başlık → boş
  IF p_kategori IS NULL AND (p_baslik IS NULL OR p_baslik = '') THEN
    RETURN;
  END IF;

  IF p_kategori IS NOT NULL THEN
    -- Kategori dalı (idx_ilanlar_kategori → idx_ihale_sonuclari_ilan_id)
    RETURN QUERY
    SELECT
      s.kazanan_firma,
      (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1],
      mode() WITHIN GROUP (ORDER BY i.il),
      count(*),
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))::numeric,
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))::numeric,
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / ln(p_bant), 1))::numeric, 1) END)
      )::numeric
    FROM public.ihale_sonuclari s
    JOIN public.ilanlar i ON i.id = s.ilan_id AND i.kategori = p_kategori
    WHERE s.kazanan_firma IS NOT NULL
      AND s.kazanan_firma <> ''
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)
              BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
    GROUP BY s.kazanan_firma
    ORDER BY 9 DESC, 5 DESC NULLS LAST
    LIMIT p_limit;
  ELSE
    -- Başlık dalı: konu-eşleşen ilanlar ÖNCE (trigram indeks), sonuçlar SONRA
    RETURN QUERY
    WITH ilgili AS MATERIALIZED (
      SELECT DISTINCT i2.id, i2.il
      FROM public.ihale_konu_kelimeleri(p_baslik) t
      JOIN public.ilanlar i2 ON tr_fold(i2.baslik) LIKE '%' || t.kelime || '%'
    )
    SELECT
      s.kazanan_firma,
      (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1],
      mode() WITHIN GROUP (ORDER BY i.il),
      count(*),
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))::numeric,
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))::numeric,
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / ln(p_bant), 1))::numeric, 1) END)
      )::numeric
    FROM public.ihale_sonuclari s
    JOIN ilgili i ON i.id = s.ilan_id
    WHERE s.kazanan_firma IS NOT NULL
      AND s.kazanan_firma <> ''
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)
              BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
    GROUP BY s.kazanan_firma
    ORDER BY 9 DESC, 5 DESC NULLS LAST
    LIMIT p_limit;
  END IF;
END
$fn$;

REVOKE EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) TO authenticated, service_role;

-- Bayatlama: izinli değer 'kapali' (constraint: taslak/aktif/kapali/iptal/sonuclandi)
CREATE OR REPLACE FUNCTION public.ilan_durum_bayatlat()
RETURNS bigint
LANGUAGE sql VOLATILE
AS $$
  WITH kapat AS (
    UPDATE public.ilanlar
       SET durum = 'kapali'
     WHERE durum = 'aktif'
       AND son_teklif_tarihi IS NOT NULL
       AND son_teklif_tarihi < now()
    RETURNING 1
  )
  SELECT count(*) FROM kapat;
$$;

REVOKE EXECUTE ON FUNCTION public.ilan_durum_bayatlat() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ilan_durum_bayatlat() TO service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   EXPLAIN ANALYZE SELECT * FROM ihaleye_uygun_firmalar(NULL,'ANKARA',809000,8,'10 KISIM 13 KALEM GIDA MADDESİ');
--     -- hedef: Execution Time < 1000 ms, Bitmap Index Scan on idx_ilanlar_baslik_fold_trgm
--   SELECT public.ilan_durum_bayatlat();  -- bayat aktif sayısını döner, hata VERMEMELİ
