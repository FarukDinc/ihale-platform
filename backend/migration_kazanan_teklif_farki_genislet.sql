-- ============================================================
-- İhaleGlobal — kazanan_teklif_farki_yuzde kolonunu genişlet
--
-- Kök neden: kolon NUMERIC(5,2) (maks ±999.99) olarak tanımlıydı ama
-- ekap_sonuc_backfill.py tenzilat'ı `round(..., 3)` ile 3 ondalıkla
-- hesaplıyor (zaten scale uyumsuzluğu vardı) VE nadir durumlarda
-- (yaklaşık maliyet kazanan tekliften çok küçükse) yüzde ±999.99'u
-- aşabiliyor. Gece log'unda (14 Tem) "numeric field overflow" hatasıyla
-- bu satırlar sessizce yazılamıyordu.
--
-- tenzilat_yuzde (aynı anlamdaki başka kolon, Design B) zaten NUMERIC(6,3) —
-- burada tutarlılık + ekstra güvenlik payı için NUMERIC(9,3) seçildi
-- (maks ±999999.999, gerçek dünya aykırı değerlerini de kapsar).
--
-- Additive/güvenli: sadece kolon tipini genişletiyor, veri kaybı yok
-- (genişletme her zaman güvenlidir, daraltmanın aksine).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kazanan_teklif_farki_genislet.sql
-- ============================================================

BEGIN;

ALTER TABLE public.ihale_sonuclari
  ALTER COLUMN kazanan_teklif_farki_yuzde TYPE NUMERIC(9,3);

COMMIT;

-- Kontrol
SELECT column_name, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'ihale_sonuclari' AND column_name = 'kazanan_teklif_farki_yuzde';
