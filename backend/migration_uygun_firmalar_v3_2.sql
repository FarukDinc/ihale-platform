-- ============================================================================
-- migration_uygun_firmalar_v3_2.sql (17 Tem 2026) — PERFORMANS DÜZELTMESİ
--
-- SORUN (EXPLAIN ANALYZE, canlı): ihaleye_uygun_firmalar v3 baslik-kelimesi
-- yolunda 10.2 sn — authenticated statement_timeout'u aşıyor, "Uygun Firmalar"
-- kutusu bu yüzden hiç görünmüyordu. Plan ters kurulmuş: 537K satırlık
-- ihale_sonuclari SEQ SCAN → her satır için ilanlar pkey + regexp subplan
-- (310K kez). idx_ilanlar_baslik_fold_trgm hiç kullanılmadı.
--
-- ÇÖZÜM: plpgsql'e geçir, iki dal:
--   * kategori dalı: v2'deki gibi (kategori indeksi, hızlıydı)
--   * başlık dalı: ÖNCE konu-eşleşen ilanları trigram indeksten MATERIALIZED
--     topla (token → bitmap scan), SONRA idx_ihale_sonuclari_ilan_id ile
--     sonuçlara git. 10.2sn → ~ms bekleniyor (analiz_pivot ifade-indeksi dersi).
-- + ihale_konu_kelimeleri'ne ROWS 5 ipucu (varsayılan 1000 satır tahmini
--   planlayıcıyı seq scan'e itebiliyor).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_uygun_firmalar_v3_2.sql
-- ============================================================================

-- Token fonksiyonu: aynı gövde + ROWS 5 (bir başlıktan tipik 1-5 konu kelimesi çıkar)
CREATE OR REPLACE FUNCTION public.ihale_konu_kelimeleri(p_baslik text)
RETURNS TABLE (kelime text)
LANGUAGE sql IMMUTABLE PARALLEL SAFE
ROWS 5
AS $$
  SELECT DISTINCT w
  FROM regexp_split_to_table(tr_fold(coalesce(p_baslik, '')), '[^a-z0-9]+') AS w
  WHERE length(w) >= 4
    AND w !~ '^[0-9]+$'
    AND w NOT IN (
      'kisim','kalem','adet','muhtelif','cesitli','cesit','grubu','grup','paket',
      'takim','mali','hizmet','hizmeti','alim','alimi','alimlari','alinmasi',
      'alinacak','alinacaktir','satin','yapim','yapimi','isleri','ihale','ihalesi',
      'madde','maddesi','mamul','temin','temini','ihtiyaci','ihtiyac','yillik',
      'aylik','gunluk','donem','donemi','donemlik','malzeme','malzemesi',
      'malzemeleri','dahil','birlikte','genel','kapsaminda','uzere','kullanilmak'
    );
$$;

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
    -- Kategori dalı (v2 plan şekli: idx_ilanlar_kategori → sonuçlar)
    RETURN QUERY
    SELECT
      s.kazanan_firma,
      (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1],
      mode() WITHIN GROUP (ORDER BY i.il),
      count(*),
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)),
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))),
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / ln(p_bant), 1))::numeric, 1) END)
      )
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
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)),
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))),
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / ln(p_bant), 1))::numeric, 1) END)
      )
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

-- Anon kilidi korunur (migration_anon_maske.sql modeli)
REVOKE EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   EXPLAIN ANALYZE SELECT * FROM ihaleye_uygun_firmalar(NULL,'ANKARA',809000,8,'10 KISIM 13 KALEM GIDA MADDESİ');
--   -- Bitmap Index Scan on idx_ilanlar_baslik_fold_trgm görülmeli; Execution Time < 1000 ms hedef
