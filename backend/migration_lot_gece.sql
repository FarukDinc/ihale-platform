-- ============================================================================
-- migration_lot_gece.sql — lot_sayisi gece tazelemesi: ucuz, hedefli fonksiyon
--                                                              (20 Tem 2026)
-- ARKA PLAN: ihale_sonuclari.lot_sayisi migration_sonuc_lot_sayisi.sql'de BİR KEZ
--   dolduruldu (ihale başına satır sayısı = kısım sayısı). Tenzilat yüzeyleri
--   "lot_sayisi = 1 değilse gösterme" kuralıyla çalışıyor; kolon bayatlarsa yeni
--   çok-kısımlı ihaleler yine sahte %95 tenzilat üretir (18 Tem hatasının dönüşü).
--
-- SORUN: run_scraper.sh'teki mevcut gece adımı (c021157) satır-içi tam tablo
--   GROUP BY koşuyor — her gece ~538K satırın TAMAMI yeniden sayılıyor, oysa
--   gecelik yeni sonuç ~5K satır tavanında (ekap_sonuc_backfill --max-pages 50).
--
-- ÇÖZÜM: idare_tur_tazele()/etkin_tarih_tazele() desenine uygun fonksiyon:
--   yalnız İÇİNDE lot_sayisi IS NULL satır bulunan ihale GRUPLARINI yeniden sayar.
--   Grup bazlı sayım kritik: mevcut bir ihaleye sonradan yeni kısım satırı
--   gelirse yalnız yeni satırı doldurmak yetmez — KARDEŞ satırların sayısı da
--   değişir (lot_sayisi=1 kalan eski kardeş yine sahte tenzilat gösterirdi).
--   Bu yüzden hedef gruptaki TÜM satırlar IS DISTINCT FROM ile güncellenir.
--
-- MALİYET: hedef seçimi idx_sonuc_lot_sayisi (lot_sayisi) indeksinden, grup
--   sayımı idx_ihale_sonuclari_ilan_id'den gider → gecelik iş ≤ ~5K satır
--   (tipik birkaç yüz), tam tablo taraması YOK. Idempotent: ikinci çalıştırma
--   0 satır yazar (yeni NULL yoksa hedef küme boş).
--
-- SINIR: satır SİLİNEN bir grupta NULL satır kalmayacağı için bu hedefli geçiş
--   o grubu görmez. Boru hattında DELETE yok (yalnız upsert); olursa tam
--   yeniden sayım için migration_sonuc_lot_sayisi.sql'deki UPDATE'i elle koşun.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_lot_gece.sql
-- Idempotent.
-- ============================================================================

-- ── Tazeleme fonksiyonu (gece run_scraper.sh çağırır) ───────────────────────
-- SECURITY DEFINER + service_role'a kısıtlı: misafir/üye çağıramaz (REVOKE
-- aşağıda). Kendi timeout'u var — REST rolünün kısa timeout'una tabi kalmasın
-- (idare_tur_tazele 20 Tem dersi: 57014 ile sessizce ölmüştü).
CREATE OR REPLACE FUNCTION public.lot_sayisi_tazele()
  RETURNS jsonb
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = public
  SET statement_timeout = '600s'
AS $$
DECLARE
  n_guncellenen int;
BEGIN
  WITH hedef AS (
    -- yeni gelen sonuç satırları lot_sayisi=NULL doğar (scraper kolonu bilmez)
    SELECT DISTINCT ilan_id
      FROM public.ihale_sonuclari
     WHERE lot_sayisi IS NULL
       AND ilan_id IS NOT NULL
  ),
  sayim AS (
    -- hedef ihalelerin GÜNCEL kısım sayısı (kardeş satırlar dahil)
    SELECT s.ilan_id, count(*)::int AS n
      FROM public.ihale_sonuclari s
      JOIN hedef h ON h.ilan_id = s.ilan_id
     GROUP BY s.ilan_id
  )
  UPDATE public.ihale_sonuclari s
     SET lot_sayisi = c.n
    FROM sayim c
   WHERE c.ilan_id = s.ilan_id
     AND s.lot_sayisi IS DISTINCT FROM c.n;
  GET DIAGNOSTICS n_guncellenen = ROW_COUNT;

  RETURN jsonb_build_object('guncellenen', n_guncellenen);
END;
$$;

REVOKE EXECUTE ON FUNCTION public.lot_sayisi_tazele() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.lot_sayisi_tazele() TO service_role;

-- İlk çalıştırma — migration uygulandığı andaki birikmiş NULL'ları kapatır
SELECT public.lot_sayisi_tazele();

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT count(*) FROM ihale_sonuclari WHERE lot_sayisi IS NULL AND ilan_id IS NOT NULL;  -- 0 beklenir
--   SELECT public.lot_sayisi_tazele();  -- ikinci çağrı {"guncellenen": 0} dönmeli (idempotentlik)
