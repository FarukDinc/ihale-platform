-- ============================================================================
-- migration_anon_maske_index.sql — sonuclananlar misafir sorgusu index'leri (17 Tem 2026)
--
-- Kök neden (canlıda görüldü): migration_anon_maske.sql sonrası sonuclananlar
-- misafir dalı `WHERE kazanan_teklif IS NOT NULL ORDER BY sonuc_tarihi DESC`
-- kullanıyor (kazanan_firma anon'a kapalı — WHERE'de de kullanılamaz). Mevcut
-- idx_is_tarih/bedel/tenzilat partial'ları `WHERE kazanan_firma IS NOT NULL`
-- olduğundan plan eşleşmedi → 537K satır full-sort → 3s statement timeout →
-- misafir listesi "Veri yüklenemedi". Üye yolu eski index'lerle çalışmaya devam ediyor.
--
-- Çözüm: aynı üç sıralama için kazanan_teklif-predicate'li partial ikizler.
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_anon_maske_index.sql
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_is_tarih_anon
  ON public.ihale_sonuclari (sonuc_tarihi DESC NULLS LAST)
  WHERE kazanan_teklif IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_is_bedel_anon
  ON public.ihale_sonuclari (kazanan_teklif DESC NULLS LAST)
  WHERE kazanan_teklif IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_is_tenzilat_anon
  ON public.ihale_sonuclari (kazanan_teklif_farki_yuzde DESC NULLS LAST)
  WHERE kazanan_teklif IS NOT NULL;

ANALYZE public.ihale_sonuclari;

-- Kontrol: anon rolüyle plan index kullanmalı + hızlı dönmeli
SET ROLE anon;
EXPLAIN (COSTS OFF)
  SELECT ilan_id, kazanan_teklif, sonuc_tarihi
  FROM public.ihale_sonuclari
  WHERE kazanan_teklif IS NOT NULL
  ORDER BY sonuc_tarihi DESC NULLS LAST LIMIT 30;
SELECT count(*) FROM (
  SELECT ilan_id FROM public.ihale_sonuclari
  WHERE kazanan_teklif IS NOT NULL
  ORDER BY sonuc_tarihi DESC NULLS LAST LIMIT 30
) t;
RESET ROLE;
