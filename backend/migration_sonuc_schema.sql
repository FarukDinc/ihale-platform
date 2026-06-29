-- ============================================================
-- P0 — Sonuç / Sözleşme Verisi Şeması
-- Çalıştırma: Supabase SQL Editor
-- ============================================================

-- 1) YÜKLENİCİLER (firma sözlüğü)
CREATE TABLE IF NOT EXISTS yukleniciler (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  normalize_ad          TEXT UNIQUE NOT NULL,   -- lowercase, trimmed, dedup anahtarı
  ad                    TEXT NOT NULL,           -- orjinal görünen ad
  vergi_no              TEXT,
  il                    TEXT,
  toplam_sozlesme_sayisi INTEGER DEFAULT 0,
  toplam_ciro           BIGINT  DEFAULT 0,      -- TL kuruş cinsinden
  ilk_sozlesme_tarihi   TIMESTAMPTZ,
  son_sozlesme_tarihi   TIMESTAMPTZ,
  sektor                TEXT[],                  -- kategori listesi
  guncellendi           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_yukleniciler_normalize ON yukleniciler (normalize_ad);
CREATE INDEX IF NOT EXISTS idx_yukleniciler_il ON yukleniciler (il);
CREATE INDEX IF NOT EXISTS idx_yukleniciler_ciro ON yukleniciler (toplam_ciro DESC);

-- 2) İHALE SONUÇLARI (ihale başına sonuç / sözleşme bilgisi)
CREATE TABLE IF NOT EXISTS ihale_sonuclari (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ekap_id               TEXT NOT NULL,           -- ilanlar.ekap_id ile join
  ikn                   TEXT,                    -- ilanlar.ikn ile join
  ihale_id              TEXT,                    -- EKAP dahili ihaleId
  yuklenici_ad          TEXT,                    -- kazanan firma adı
  yuklenici_vergi_no    TEXT,
  yuklenici_il          TEXT,
  yuklenici_id          UUID REFERENCES yukleniciler(id) ON DELETE SET NULL,
  sozlesme_bedeli       BIGINT,                  -- TL
  sozlesme_tarihi       TIMESTAMPTZ,
  tenzilat_yuzde        NUMERIC(6,3),            -- % (örn. 10.305)
  yaklasik_maliyet      BIGINT,                  -- orijinal tahmini (doğrulama için)
  katilimci_sayisi      INTEGER,
  gecerli_teklif_sayisi INTEGER,
  is_baslama_tarihi     TIMESTAMPTZ,
  is_bitis_tarihi       TIMESTAMPTZ,
  is_suresi_gun         INTEGER,
  karar_tarihi          TIMESTAMPTZ,             -- kesinleşme kararı tarihi
  sonuc_tur             TEXT,                    -- 'Kesinleşen Karar', 'Sözleşme', 'İptal' vb.
  ham_json              JSONB,                   -- EKAP'tan gelen ham yanıt (debugging)
  scrape_tarihi         TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ihale_sonuclari_ekap ON ihale_sonuclari (ekap_id);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_yuklenici ON ihale_sonuclari (yuklenici_ad);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_sozlesme ON ihale_sonuclari (sozlesme_tarihi DESC);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_bedel ON ihale_sonuclari (sozlesme_bedeli DESC);

-- 3) SCRAPE LOG (hangi ihaleler için sonuç denendi)
CREATE TABLE IF NOT EXISTS scrape_log (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ekap_id       TEXT NOT NULL,
  ihale_id      TEXT,
  deneme_tarihi TIMESTAMPTZ DEFAULT NOW(),
  basarili      BOOLEAN DEFAULT FALSE,
  hata_mesaji   TEXT
);

CREATE INDEX IF NOT EXISTS idx_scrape_log_ekap ON scrape_log (ekap_id);
CREATE INDEX IF NOT EXISTS idx_scrape_log_tarih ON scrape_log (deneme_tarihi DESC);

-- 4) ilanlar tablosuna join için yardımcı view
-- (Her ihalede sonuç varsa birleşik gösterim)
CREATE OR REPLACE VIEW ilanlar_sonuc AS
SELECT
  i.id,
  i.ekap_id,
  i.ikn,
  i.baslik,
  i.idare,
  i.il,
  i.tur,
  i.usul,
  i.kategori,
  i.son_teklif_tarihi,
  i.ilan_tarihi,
  i.yaklasik_maliyet_min,
  i.yaklasik_maliyet_max,
  i.durum,
  s.yuklenici_ad,
  s.sozlesme_bedeli,
  s.tenzilat_yuzde,
  s.katilimci_sayisi,
  s.gecerli_teklif_sayisi,
  s.sozlesme_tarihi,
  s.is_baslama_tarihi,
  s.is_bitis_tarihi,
  s.sonuc_tur
FROM ilanlar i
LEFT JOIN ihale_sonuclari s ON i.ekap_id = s.ekap_id;

-- 5) İdare bazlı GROUP BY RPC (idareler.html için performans optimizasyonu)
-- Çok büyük veri setinde JS tarafı döngü yerine bu kullanılabilir.
CREATE OR REPLACE FUNCTION idare_sayim()
RETURNS TABLE (
  idare TEXT,
  toplam BIGINT,
  aktif BIGINT,
  en_yakin_il TEXT
) AS $$
  SELECT
    idare,
    COUNT(*) AS toplam,
    COUNT(*) FILTER (WHERE durum = 'aktif') AS aktif,
    MODE() WITHIN GROUP (ORDER BY il) AS en_yakin_il
  FROM ilanlar
  WHERE idare IS NOT NULL
  GROUP BY idare
  ORDER BY toplam DESC;
$$ LANGUAGE SQL STABLE;

-- 6) Kategori bazlı GROUP BY RPC
CREATE OR REPLACE FUNCTION kategori_sayim()
RETURNS TABLE (
  kategori TEXT,
  toplam BIGINT,
  aktif BIGINT
) AS $$
  SELECT
    COALESCE(kategori, 'Diğer') AS kategori,
    COUNT(*) AS toplam,
    COUNT(*) FILTER (WHERE durum = 'aktif') AS aktif
  FROM ilanlar
  GROUP BY kategori
  ORDER BY toplam DESC;
$$ LANGUAGE SQL STABLE;
