-- ============================================================
-- İhaleGlobal — ihale_sonuclari.lot_sayisi (kısım sayısı sinyali)
--
-- NEDEN: EKAP kısım bazlı yaklaşık maliyet yayımlamıyor; çok kısımlı ihalede
-- ihalenin TOPLAM maliyeti HER kısım satırına kopyalanıyor (46.077/46.083 ihalede
-- doğrulandı) → satır bazlı `kazanan_teklif_farki_yuzde` sahte %95-100 çıkıyor.
-- 246.639 satır (%46) etkileniyor. Kısım bazlı DOĞRU tenzilat mevcut veriden
-- hesaplanamıyor (tum_teklifler.kisimList sözleşmeyle eşleşmiyor — 3 yöntem denendi:
-- indeks eşleme %17, değer eşleme %4,8, yapısal inceleme → bağ yok).
--
-- ÇÖZÜM: hesaplayamadığımızı göstermeyelim. Bu kolon her satıra ihalesinin kısım
-- sayısını yazar; tüketiciler tek kuralla doğru davranır:
--   lot_sayisi = 1  → satırdaki tenzilat GEÇERLİ, göster
--   lot_sayisi > 1  → satır tenzilatı BİLİNEMEZ, gösterme / ortalamalara katma
--                     (gerekirse ihale geneli: (ym − Σ kısım bedeli)/ym)
--
-- Kullanacak yüzeyler: firma-analiz, kurum-analiz, teklif_ai.py, firma_ai_yorum.py
-- (ihale-detay client'ta zaten sayıyor — commit 7ea9b52).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_sonuc_lot_sayisi.sql
--
-- BAKIM: yeni sonuçlar geldikçe bayatlar. run_scraper.sh'e gece şu satırı ekle
-- (MV refresh'lerinin yanına):
--   UPDATE public.ihale_sonuclari s SET lot_sayisi = c.n
--   FROM (SELECT ilan_id, count(*)::int n FROM public.ihale_sonuclari GROUP BY ilan_id) c
--   WHERE c.ilan_id = s.ilan_id AND s.lot_sayisi IS DISTINCT FROM c.n;
-- ============================================================

BEGIN;

ALTER TABLE public.ihale_sonuclari ADD COLUMN IF NOT EXISTS lot_sayisi INT;

UPDATE public.ihale_sonuclari s
SET    lot_sayisi = c.n
FROM   (SELECT ilan_id, count(*)::int AS n FROM public.ihale_sonuclari GROUP BY ilan_id) c
WHERE  c.ilan_id = s.ilan_id
  AND  s.lot_sayisi IS DISTINCT FROM c.n;

CREATE INDEX IF NOT EXISTS idx_sonuc_lot_sayisi ON public.ihale_sonuclari (lot_sayisi);

-- Misafir maskeleme deseni kolon-bazlı (migration_anon_maske.sql): yeni kolonda
-- anon'un yetkisi OLMAZ → açıkça ver. Hassas değil (yalnız kısım adedi).
GRANT SELECT (lot_sayisi) ON public.ihale_sonuclari TO anon;

COMMIT;

-- Doğrulama: tek-kısımlı ~288.728 satır, çok-kısımlı ~249.336 satır beklenir
SELECT (lot_sayisi = 1) AS tek_kisimli, count(*) AS satir
FROM public.ihale_sonuclari WHERE lot_sayisi IS NOT NULL GROUP BY 1 ORDER BY 1;
