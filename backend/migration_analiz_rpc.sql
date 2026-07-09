-- ============================================================
-- ANALİZ PİVOT RPC — ÖNCELİK 10 Faz C1 (9 Tem 2026)
-- ihaleciler.com'un /analyze ekranına parite: tek esnek RPC, firma-analiz.html /
-- kurum-analiz.html / rekabet-analizi.html'in TEK veri kaynağı olacak (client-side
-- 1000'er batch çekme alışkanlığı yerine).
-- Çalıştır: VDS psql -f  VE  managed Supabase SQL Editor (cutover'a dek ikisinde de).
-- ============================================================

BEGIN;

CREATE OR REPLACE FUNCTION analiz_pivot(
  p_grup      TEXT,               -- 'yil' | 'kategori' | 'idare' | 'il' | 'usul' | 'tur' | 'firma'
  p_firma     TEXT DEFAULT NULL,  -- normalize_ad ile eşleşir
  p_idare     TEXT DEFAULT NULL,
  p_kategori  TEXT DEFAULT NULL,
  p_il        TEXT DEFAULT NULL,
  p_yil       INT  DEFAULT NULL
)
RETURNS TABLE (
  grup_deger          TEXT,
  ihale_sayisi         BIGINT,
  toplam_bedel         NUMERIC,
  ort_bedel            NUMERIC,
  ort_tenzilat         NUMERIC,
  ort_katilimci        NUMERIC,
  ort_gecerli_teklif   NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  grup_expr TEXT;
BEGIN
  -- p_grup whitelist — kullanıcı girdisi doğrudan SQL'e gitmiyor, sabit ifadeler seçiliyor.
  grup_expr := CASE p_grup
    WHEN 'yil'      THEN 'EXTRACT(YEAR FROM s.sonuc_tarihi)::TEXT'
    WHEN 'kategori' THEN 'COALESCE(i.kategori, ''Bilinmiyor'')'
    WHEN 'idare'    THEN 'COALESCE(i.idare, ''Bilinmiyor'')'
    WHEN 'il'       THEN 'COALESCE(i.il, ''Bilinmiyor'')'
    WHEN 'usul'     THEN 'COALESCE(i.usul, ''Bilinmiyor'')'
    WHEN 'tur'      THEN 'COALESCE(i.tur, ''Bilinmiyor'')'
    WHEN 'firma'    THEN 'COALESCE(y.ad, s.kazanan_firma, ''Bilinmiyor'')'
    ELSE NULL
  END;

  IF grup_expr IS NULL THEN
    RAISE EXCEPTION 'geçersiz p_grup: % (izinli: yil, kategori, idare, il, usul, tur, firma)', p_grup;
  END IF;

  RETURN QUERY EXECUTE format($f$
    SELECT
      %s                                          AS grup_deger,
      COUNT(*)                                    AS ihale_sayisi,
      COALESCE(SUM(s.kazanan_teklif), 0)::NUMERIC AS toplam_bedel,
      ROUND(AVG(s.kazanan_teklif), 0)             AS ort_bedel,
      ROUND(AVG(s.tenzilat_yuzde), 2)             AS ort_tenzilat,
      ROUND(AVG(s.katilimci_sayisi), 1)           AS ort_katilimci,
      ROUND(AVG(s.gecerli_teklif_sayisi), 1)      AS ort_gecerli_teklif
    FROM ihale_sonuclari s
    JOIN ilanlar i ON i.id = s.ilan_id
    LEFT JOIN yukleniciler y ON y.id = s.yuklenici_id
    WHERE s.kazanan_teklif IS NOT NULL
      AND ($1 IS NULL OR y.normalize_ad = $1 OR normalize_firma(s.kazanan_firma) = $1)
      AND ($2 IS NULL OR i.idare = $2)
      AND ($3 IS NULL OR i.kategori = $3)
      AND ($4 IS NULL OR i.il = $4)
      AND ($5 IS NULL OR EXTRACT(YEAR FROM s.sonuc_tarihi) = $5)
    GROUP BY %s
    ORDER BY ihale_sayisi DESC
    LIMIT 500
  $f$, grup_expr, grup_expr)
  USING p_firma, p_idare, p_kategori, p_il, p_yil;
END;
$$;

GRANT EXECUTE ON FUNCTION analiz_pivot(TEXT, TEXT, TEXT, TEXT, TEXT, INT) TO anon, authenticated;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Test örnekleri:
-- SELECT * FROM analiz_pivot('yil');
-- SELECT * FROM analiz_pivot('firma', p_kategori := 'İnşaat & Yapım', p_il := 'ANKARA');
-- SELECT * FROM analiz_pivot('idare', p_firma := 'ABC İNŞAAT');
