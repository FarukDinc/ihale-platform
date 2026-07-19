-- ============================================================================
-- migration_etkin_tarih.sql — ilanlar için "etkin tarih" (sıralama/filtre ekseni)
--                                                              (19 Tem 2026)
-- SORUN (ölçüldü): 356.904 ihalenin 340.538'inde (%95) ÜÇ tarih alanı da BOŞ
--   (ilan_tarihi, son_teklif_tarihi, ihale_tarihi). Bunlar sonuç-backfill'inden
--   gelen geçmiş kayıtlar. Sonuç: tarih filtresi/sıralaması bu kayıtlarda
--   çalışmıyor; Güncel/Geçmiş sekmeleri yalnız 16,4K kaydı görüyor.
--
-- ÇÖZÜM: kazımaya GEREK YOK — 538.064 sonuç kaydının TAMAMINDA sonuc_tarihi dolu
--   ve tarihsiz ihalelerin 335.212'sinin (%98,4) bağlı sonuç kaydı var.
--
-- ⚠️ NEDEN ilan_tarihi'ye YAZMIYORUZ: sonuç tarihi ≠ ilan tarihi (haftalar/aylar
--   sonra). Boş alanı sonuç tarihiyle doldurmak VERİYİ ÇARPITIR — "bu ihale şu
--   tarihte ilan edildi" diye yanlış bilgi üretir. Bunun yerine AYRI bir eksen:
--     etkin_tarih        = sıralama/filtreleme için "eldeki en iyi tarih"
--     etkin_tarih_kaynak = o tarihin NE olduğu ('son_teklif'|'ilan'|'ihale'|'sonuc')
--   Arayüz kaynağa bakıp "Sonuç tarihi" diye dürüstçe etiketleyebilir.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_etkin_tarih.sql
-- Idempotent. 356K satır UPDATE — birkaç dakika sürebilir.
-- ============================================================================

ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS etkin_tarih        timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS etkin_tarih_kaynak text;

-- Sıralama + yıl filtresi bu indeksten gider (DESC: en yeni önce, tipik kullanım)
CREATE INDEX IF NOT EXISTS idx_ilanlar_etkin_tarih
  ON public.ilanlar (etkin_tarih DESC NULLS LAST);

-- ── Tazeleme fonksiyonu (gece scraper çağırır) ─────────────────────────────
-- Öncelik: son_teklif > ilan > ihale > (sonuç kayıtlarının EN ERKENİ).
-- Yalnız DEĞİŞENLERİ yazar → gereksiz WAL yok.
CREATE OR REPLACE FUNCTION public.etkin_tarih_tazele()
  RETURNS jsonb
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = public
AS $$
DECLARE
  n_dogrudan int;
  n_sonuc    int;
BEGIN
  -- 1) Kendi tarih alanı olanlar
  UPDATE public.ilanlar i
     SET etkin_tarih        = COALESCE(i.son_teklif_tarihi, i.ilan_tarihi, i.ihale_tarihi),
         etkin_tarih_kaynak = CASE
                                WHEN i.son_teklif_tarihi IS NOT NULL THEN 'son_teklif'
                                WHEN i.ilan_tarihi       IS NOT NULL THEN 'ilan'
                                ELSE 'ihale'
                              END
   WHERE COALESCE(i.son_teklif_tarihi, i.ilan_tarihi, i.ihale_tarihi) IS NOT NULL
     AND i.etkin_tarih IS DISTINCT FROM COALESCE(i.son_teklif_tarihi, i.ilan_tarihi, i.ihale_tarihi);
  GET DIAGNOSTICS n_dogrudan = ROW_COUNT;

  -- 2) Hiç tarihi olmayanlar → bağlı sonuç kaydının EN ERKEN sonuc_tarihi'si
  --    (çok kısımlı ihalede birden çok sonuç satırı olur; ilk sonuçlanma alınır)
  UPDATE public.ilanlar i
     SET etkin_tarih        = s.ilk_sonuc,
         etkin_tarih_kaynak = 'sonuc'
    FROM (SELECT ilan_id, min(sonuc_tarihi) AS ilk_sonuc
            FROM public.ihale_sonuclari
           WHERE ilan_id IS NOT NULL AND sonuc_tarihi IS NOT NULL
           GROUP BY ilan_id) s
   WHERE s.ilan_id = i.id
     AND COALESCE(i.son_teklif_tarihi, i.ilan_tarihi, i.ihale_tarihi) IS NULL
     AND i.etkin_tarih IS DISTINCT FROM s.ilk_sonuc;
  GET DIAGNOSTICS n_sonuc = ROW_COUNT;

  RETURN jsonb_build_object('kendi_tarihi', n_dogrudan, 'sonuctan_turetilen', n_sonuc);
END;
$$;

REVOKE EXECUTE ON FUNCTION public.etkin_tarih_tazele() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.etkin_tarih_tazele() TO service_role;

-- İlk doldurma
SELECT public.etkin_tarih_tazele();

-- ── Yetki: yeni kolonlar kolon-GRANT'a girmez (19 Tem dersi!) ──────────────
-- ilanlar misafir maskesi kolon bazlı → yeni kolon açıkça verilmezse filtre
-- 42501 döner ve sayfa boşalır. Tarih hassas veri değil, misafire de açık.
GRANT SELECT (etkin_tarih, etkin_tarih_kaynak) ON public.ilanlar TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT etkin_tarih_kaynak, count(*) FROM ilanlar GROUP BY 1 ORDER BY 2 DESC;
--   SELECT count(*) FROM ilanlar WHERE etkin_tarih IS NULL;   -- ~5K kalmalı
--   SELECT date_part('year', etkin_tarih) y, count(*) FROM ilanlar
--     WHERE etkin_tarih IS NOT NULL GROUP BY 1 ORDER BY 1 DESC LIMIT 10;
