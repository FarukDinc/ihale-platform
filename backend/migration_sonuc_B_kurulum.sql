-- ============================================================
-- SONUÇ / YÜKLENİCİ VERİSİ — Tasarım B kurulumu (8 Tem 2026, NON-DESTRUCTIVE)
-- ekap_sonuc_scraper.py'ın yazdığı Tasarım B kolonlarını MEVCUT ihale_sonuclari'ya
-- ekler (drop YOK — eski 15 satır korunur, null ekap_id'li zararsız kalır).
-- + yukleniciler (firma sözlüğü) + scrape_log (işlem takibi) + view.
-- anon/authenticated SELECT + RLS public-read (ilanlar ile aynı model).
-- Çalıştır: VDS psql -f  VE  managed Supabase SQL Editor (cutover'a dek ikisinde de).
-- ============================================================

BEGIN;

-- 1) YÜKLENİCİLER (firma sözlüğü — dedup + agregat)
CREATE TABLE IF NOT EXISTS yukleniciler (
  id                     UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  normalize_ad           TEXT UNIQUE NOT NULL,
  ad                     TEXT NOT NULL,
  vergi_no               TEXT,
  il                     TEXT,
  toplam_sozlesme_sayisi INTEGER DEFAULT 0,
  toplam_ciro            BIGINT  DEFAULT 0,
  ilk_sozlesme_tarihi    TIMESTAMPTZ,
  son_sozlesme_tarihi    TIMESTAMPTZ,
  sektor                 TEXT[],
  guncellendi            TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_yukleniciler_normalize ON yukleniciler (normalize_ad);
CREATE INDEX IF NOT EXISTS idx_yukleniciler_il ON yukleniciler (il);
CREATE INDEX IF NOT EXISTS idx_yukleniciler_ciro ON yukleniciler (toplam_ciro DESC);

-- 2) İHALE SONUÇLARI — mevcut tabloya Tasarım B kolonlarını ekle (NON-DESTRUCTIVE)
ALTER TABLE ihale_sonuclari
  ADD COLUMN IF NOT EXISTS ekap_id               TEXT,
  ADD COLUMN IF NOT EXISTS ikn                   TEXT,
  ADD COLUMN IF NOT EXISTS ihale_id              TEXT,
  ADD COLUMN IF NOT EXISTS yuklenici_ad          TEXT,
  ADD COLUMN IF NOT EXISTS yuklenici_vergi_no    TEXT,
  ADD COLUMN IF NOT EXISTS yuklenici_il          TEXT,
  ADD COLUMN IF NOT EXISTS yuklenici_id          UUID REFERENCES yukleniciler(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS sozlesme_bedeli       BIGINT,
  ADD COLUMN IF NOT EXISTS sozlesme_tarihi       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS tenzilat_yuzde        NUMERIC(6,3),
  ADD COLUMN IF NOT EXISTS yaklasik_maliyet      BIGINT,
  ADD COLUMN IF NOT EXISTS katilimci_sayisi      INTEGER,
  ADD COLUMN IF NOT EXISTS gecerli_teklif_sayisi INTEGER,
  ADD COLUMN IF NOT EXISTS is_baslama_tarihi     TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS is_bitis_tarihi       TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS is_suresi_gun         INTEGER,
  ADD COLUMN IF NOT EXISTS karar_tarihi          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS sonuc_tur             TEXT,
  ADD COLUMN IF NOT EXISTS ham_json              JSONB,
  ADD COLUMN IF NOT EXISTS scrape_tarihi         TIMESTAMPTZ DEFAULT NOW();

-- upsert(on_conflict=ekap_id) için unique index (mevcut null ekap_id'ler çok-null'a izin verir)
CREATE UNIQUE INDEX IF NOT EXISTS idx_ihale_sonuclari_ekap ON ihale_sonuclari (ekap_id);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_yuklenici ON ihale_sonuclari (yuklenici_ad);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_sozlesme ON ihale_sonuclari (sozlesme_tarihi DESC);
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_bedel ON ihale_sonuclari (sozlesme_bedeli DESC);

-- 3) SCRAPE LOG (işlem takibi)
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

-- 4) İlan + sonuç birleşik view (ekap_id join)
CREATE OR REPLACE VIEW ilanlar_sonuc AS
SELECT
  i.id, i.ekap_id, i.ikn, i.baslik, i.idare, i.il, i.tur, i.usul, i.kategori,
  i.son_teklif_tarihi, i.ilan_tarihi, i.yaklasik_maliyet_min, i.yaklasik_maliyet_max, i.durum,
  s.yuklenici_ad, s.sozlesme_bedeli, s.tenzilat_yuzde, s.katilimci_sayisi,
  s.gecerli_teklif_sayisi, s.sozlesme_tarihi, s.is_baslama_tarihi, s.is_bitis_tarihi, s.sonuc_tur
FROM ilanlar i
LEFT JOIN ihale_sonuclari s ON i.ekap_id = s.ekap_id;

-- 5) Erişim: public read (ilanlar ile aynı). scrape_log service-only.
GRANT SELECT ON yukleniciler    TO anon, authenticated;
GRANT SELECT ON ihale_sonuclari TO anon, authenticated;
GRANT SELECT ON ilanlar_sonuc   TO anon, authenticated;

ALTER TABLE yukleniciler ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_log   ENABLE ROW LEVEL SECURITY;
-- ihale_sonuclari RLS + 'sonuclar_herkese_acik' policy zaten mevcut

DROP POLICY IF EXISTS yukleniciler_public_read ON yukleniciler;
CREATE POLICY yukleniciler_public_read ON yukleniciler FOR SELECT USING (true);
-- scrape_log: policy yok → anon göremez; service_role bypass eder (scraper yazar)

COMMIT;

NOTIFY pgrst, 'reload schema';
