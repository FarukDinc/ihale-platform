-- ============================================================
-- FİRMA (YÜKLENİCİ) AGREGASYONU — ÖNCELİK 10 Faz B2 (9 Tem 2026)
-- normalize_firma(): Python firma_normalize.py'deki normalize_ad() ile davranışça eşleşen
--   PL/pgSQL karşılığı (SQL tarafında sorgulama/gruplama için gerekli).
-- yuklenici_yenile(): ihale_sonuclari'nı normalize edip yukleniciler'i her gece tazeler
--   (scrape DEĞİL — mevcut sonuç verisinden türetilen agregasyon).
-- Çalıştır: VDS psql -f  VE  managed Supabase SQL Editor (cutover'a dek ikisinde de).
-- ============================================================

BEGIN;

CREATE OR REPLACE FUNCTION normalize_firma(ham_ad TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  ad TEXT;
BEGIN
  IF ham_ad IS NULL OR btrim(ham_ad) = '' THEN
    RETURN NULL;
  END IF;
  ad := upper(btrim(ham_ad));
  -- Yaygın firma ekleri/bağlaçları — Python normalize_ad() ile aynı küme.
  ad := regexp_replace(ad, '\mA\.?\s*Ş\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mLTD\.?\s*ŞT[İI]\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mL[İI]M[İI]TED\s*Ş[İI]RKET[İI]\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mT[İI]C\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mSAN\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\m[İI]NŞ\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mTAAH\.?\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mVE\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mT[İI]CARET\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mSANAY[İI]\M', ' ', 'gi');
  ad := regexp_replace(ad, '\m[İI]NŞAAT\M', ' ', 'gi');
  ad := regexp_replace(ad, '\mTAAHHÜT\M', ' ', 'gi');
  ad := regexp_replace(ad, '[.,\-–—()]+', ' ', 'g');
  ad := regexp_replace(ad, '\s+', ' ', 'g');
  ad := btrim(ad);
  IF ad = '' THEN
    RETURN NULL;
  END IF;
  RETURN ad;
END;
$$;

-- yukleniciler'e ortak-girişim işareti + ortak listesi (Faz B1'in "ortaklar" alanı)
ALTER TABLE yukleniciler
  ADD COLUMN IF NOT EXISTS ortak_girisim BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS kategori TEXT[];

CREATE OR REPLACE FUNCTION yuklenici_yenile()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
  guncellenen INTEGER;
BEGIN
  WITH agg AS (
    SELECT
      normalize_firma(s.kazanan_firma)                    AS normalize_ad,
      (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS gorunen_ad,
      COUNT(*)                                             AS sozlesme_sayisi,
      COALESCE(SUM(s.kazanan_teklif), 0)                   AS toplam_ciro,
      MIN(s.sonuc_tarihi)                                  AS ilk_tarih,
      MAX(s.sonuc_tarihi)                                  AS son_tarih,
      (array_agg(i.il) FILTER (WHERE i.il IS NOT NULL))[1] AS il,
      array_agg(DISTINCT i.kategori) FILTER (WHERE i.kategori IS NOT NULL) AS kategoriler,
      bool_or(s.kazanan_firma ILIKE '%İŞ ORTAKLIĞI%' OR s.kazanan_firma ILIKE '%ORTAK GİRİŞİM%') AS ortak_girisim
    FROM ihale_sonuclari s
    JOIN ilanlar i ON i.id = s.ilan_id
    WHERE s.kazanan_firma IS NOT NULL AND normalize_firma(s.kazanan_firma) IS NOT NULL
    GROUP BY normalize_firma(s.kazanan_firma)
  )
  INSERT INTO yukleniciler (normalize_ad, ad, toplam_sozlesme_sayisi, toplam_ciro,
                             ilk_sozlesme_tarihi, son_sozlesme_tarihi, il, sektor, kategori,
                             ortak_girisim, guncellendi)
  SELECT normalize_ad, gorunen_ad, sozlesme_sayisi, toplam_ciro, ilk_tarih, son_tarih,
         il, kategoriler, kategoriler, ortak_girisim, NOW()
  FROM agg
  ON CONFLICT (normalize_ad) DO UPDATE SET
    ad                     = EXCLUDED.ad,
    toplam_sozlesme_sayisi = EXCLUDED.toplam_sozlesme_sayisi,
    toplam_ciro            = EXCLUDED.toplam_ciro,
    ilk_sozlesme_tarihi    = EXCLUDED.ilk_sozlesme_tarihi,
    son_sozlesme_tarihi    = EXCLUDED.son_sozlesme_tarihi,
    il                     = EXCLUDED.il,
    sektor                 = EXCLUDED.sektor,
    kategori               = EXCLUDED.kategori,
    ortak_girisim          = EXCLUDED.ortak_girisim,
    guncellendi            = NOW();

  GET DIAGNOSTICS guncellenen = ROW_COUNT;

  -- ihale_sonuclari.yuklenici_id'yi de doldur (Faz C'nin firma-analiz JOIN'i için)
  UPDATE ihale_sonuclari s
  SET yuklenici_id = y.id
  FROM yukleniciler y
  WHERE s.kazanan_firma IS NOT NULL
    AND normalize_firma(s.kazanan_firma) = y.normalize_ad
    AND s.yuklenici_id IS DISTINCT FROM y.id;

  RETURN guncellenen;
END;
$$;

GRANT EXECUTE ON FUNCTION yuklenici_yenile() TO service_role;
GRANT EXECUTE ON FUNCTION normalize_firma(TEXT) TO anon, authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Manuel çalıştırma (cron'a bağlanana kadar test için):
-- SELECT yuklenici_yenile();
