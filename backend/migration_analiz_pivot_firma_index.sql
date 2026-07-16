-- ============================================================================
-- migration_analiz_pivot_firma_index.sql — analiz_pivot firma filtresi gerçek fix (16 Tem 2026)
--
-- Kök neden (canlıda ölçüldü): analiz_pivot(p_firma=REC ...) 21.5sn sürüp yeni 20s
-- limitinde bile 57014 veriyordu. Sorun timeout değil sorgunun kendisi:
--   WHERE ... normalize_firma(s.kazanan_firma) = normalize_firma($1)
-- ifadesi 537K ihale_sonuclari satırının HER BİRİNDE plpgsql normalize_firma()
-- (~15 ardışık regexp_replace) çalıştırıyordu. Timeout büyütmek çare değil.
--
-- Fix iki parça:
--  1) normalize_firma IMMUTABLE olduğundan ifade indeksi: eşitlik artık index scan.
--  2) Firma predicate'i s-tarafına sadeleştirildi: eski `y.normalize_ad = X OR
--     normalize_firma(s.kazanan_firma) = X` OR'u iki TABLO arasında olduğundan
--     hiçbir index kullanılamıyordu. Platformun kanonik firma kimliği zaten
--     normalize_firma(kazanan_firma) (yuklenici_yenile, il_sektor_firma_mv aynı
--     anahtar; yuklenici_id ~92K satırda NULL — bkz. hafıza). y join'i p_grup='firma'
--     görünen adı için DURUYOR, yalnız filtre s-tarafına indirildi.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_analiz_pivot_firma_index.sql
-- Index build ~537K × normalize_firma = birkaç dakika sürebilir (bir kere).
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sonuc_kazanan_firma_norm
  ON public.ihale_sonuclari (normalize_firma(kazanan_firma));

ANALYZE public.ihale_sonuclari;

CREATE OR REPLACE FUNCTION analiz_pivot(
  p_grup      TEXT,
  p_firma     TEXT DEFAULT NULL,
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

  -- Firma filtresi yalnız s.kazanan_firma normalize'ı üzerinden:
  -- idx_sonuc_kazanan_firma_norm ifade indeksiyle eşleşir (sağ taraf sabit —
  -- normalize_firma($1) parametre başına 1 kez hesaplanır).
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
      AND ($1 IS NULL OR normalize_firma(s.kazanan_firma) = normalize_firma($1))
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

-- CREATE OR REPLACE proconfig'i sıfırlar → 20s güvenceyi yeniden koy
-- (index'le ~ms beklenir; 20s yalnız firmasız ağır pivotlar için pay).
ALTER FUNCTION public.analiz_pivot(text, text, text, text, text, int)
  SET statement_timeout = '20s';
GRANT EXECUTE ON FUNCTION analiz_pivot(TEXT, TEXT, TEXT, TEXT, TEXT, INT) TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- Kontrol (REC = eski timeout vakası; artık index scan ile gelmeli)
EXPLAIN (COSTS OFF) SELECT * FROM ihale_sonuclari
 WHERE normalize_firma(kazanan_firma) = 'REC ULUSLARARASI İNŞAAT YATIRIM';
SELECT grup_deger, ihale_sayisi FROM analiz_pivot('idare',
  p_firma := 'REC ULUSLARARASI İNŞAAT YATIRIM SANAYİ VE TİCARET ANONİM ŞİRKETİ') LIMIT 3;
