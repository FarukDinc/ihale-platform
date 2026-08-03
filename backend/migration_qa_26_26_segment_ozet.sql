-- ============================================================================
-- migration_qa_26_26_segment_ozet.sql — 26-26: Firma Segmentleri özet rozetleri (3 Ağu 2026)
--
-- firma_segment_sayilari() eski hali TEK sorguda `count(*) FILTER (WHERE seg_X)` yapıyordu →
-- 433K yukleniciler üzerinde tek seq-scan (~970ms). Kısmi indeksler (ix_yuk_seg_parlayan/…)
-- FILTER'da KULLANILAMIYOR → tablo büyüdükçe timeout'a yaklaşıp rozetler "hesaplanıyor"da takılır.
-- FIX: her sayıyı AYRI skaler alt-sorgu yap → kısmi indeksten index-only scan (ölçüm: ~85ms).
-- Çıktı (parlayan/sonen/ilk_kez/yuz50mn/guncellendi/ref_tarih) BİREBİR korunur.
--
-- Çalıştırma: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_26_segment_ozet.sql
-- ============================================================================

CREATE OR REPLACE FUNCTION public.firma_segment_sayilari()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT jsonb_build_object(
    'parlayan', (SELECT count(*) FROM public.yukleniciler WHERE seg_parlayan),
    'sonen',    (SELECT count(*) FROM public.yukleniciler WHERE seg_sonen),
    'ilk_kez',  (SELECT count(*) FROM public.yukleniciler WHERE seg_ilk_kez),
    'yuz50mn',  (SELECT count(*) FROM public.yukleniciler WHERE seg_150mn),
    'guncellendi', (SELECT max(segment_guncellendi) FROM public.yukleniciler),
    -- Kıyas çapası: segment hesabının kullandığı referans tarih (bugün DEĞİL).
    'ref_tarih', (SELECT max(s.sonuc_tarihi)::date FROM public.ihale_sonuclari s WHERE s.sonuc_tarihi <= now())
  );
$$;

NOTIFY pgrst, 'reload schema';
