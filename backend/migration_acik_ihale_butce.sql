-- ============================================================================
-- migration_acik_ihale_butce.sql — anasayfa bütçe KPI'si sessizce kesiliyordu
--                                                              (20 Tem 2026)
-- ÖLÇÜLEN HATA (canlı): index.html'deki KPI şu sorguyu atıyordu —
--     .select('yaklasik_maliyet_min')
--     .gte('son_teklif_tarihi', simdi)
--     .not('yaklasik_maliyet_min','is',null)
--   ...ve dönen satırları TARAYICIDA topluyordu. `.limit()` yok, dolayısıyla
--   PostgREST `db-max-rows=1000` devreye giriyor ve sorgu SESSİZCE 1000 satırda
--   kesiliyor. Ölçüldü: eşleşen 4.452 kayıt var, dönen 1.000 → gösterilen
--   25,0 milyar TL, gerçeğin yaklaşık DÖRTTE BİRİ. Hata mesajı yok, sayfa
--   "başarılı" görünüyor. (Aynı sınıf hata için bkz. client-load-all dersi.)
--
-- ⚠️ Bu sayı 1,6M geçmiş ihale backfill'inden ETKİLENMEZ — KPI zaten
--   son_teklif_tarihi >= now() ile açık ihalelere kısıtlı, geçmiş kayıtların
--   son_teklif_tarihi'si NULL. Yani bu backfill riski değil, MEVCUT bir hata.
--
-- ÇÖZÜM: toplamayı sunucuda yap. Ayrıca KAPSAMI da döndür — kaç kaydın maliyeti
--   var, kaç açık ihale var. Arayüz "4.452 ihale üzerinden" diye dürüstçe
--   yazabilsin; eksik veriden türetilmiş toplamı kesin gibi sunmayalım.
--
-- GÜVENLİK: SECURITY DEFINER — yalnız AGGREGATE döner, satır sızdırmaz.
--   (idare_tur_kapsama() ile aynı gerekçe; misafir maskesi delinmez.)
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_acik_ihale_butce.sql
-- Idempotent.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.acik_ihale_butce()
  RETURNS jsonb
  LANGUAGE sql
  STABLE
  SECURITY DEFINER
  SET search_path = public
AS $$
  SELECT jsonb_build_object(
    -- Toplam yaklaşık maliyet (yalnız değeri OLAN kayıtlar)
    'toplam_butce',  (SELECT coalesce(sum(yaklasik_maliyet_min), 0)
                        FROM public.ilanlar
                       WHERE son_teklif_tarihi >= now()
                         AND yaklasik_maliyet_min IS NOT NULL),
    -- Toplamın DAYANDIĞI kayıt sayısı
    'butce_kayit',   (SELECT count(*)
                        FROM public.ilanlar
                       WHERE son_teklif_tarihi >= now()
                         AND yaklasik_maliyet_min IS NOT NULL),
    -- Kapsam paydası: tüm açık ihaleler
    'acik_ihale',    (SELECT count(*)
                        FROM public.ilanlar
                       WHERE son_teklif_tarihi >= now())
  );
$$;

REVOKE EXECUTE ON FUNCTION public.acik_ihale_butce() FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.acik_ihale_butce() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (beklenen: toplam_butce >> 25 milyar, butce_kayit ≈ 4452):
--   SELECT public.acik_ihale_butce();
