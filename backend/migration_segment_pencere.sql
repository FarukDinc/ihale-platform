-- =============================================================================
-- migration_segment_pencere.sql — segment sayaç RPC'sine KIYAS PENCERESİ eklenir
-- 29 Tem 2026
-- =============================================================================
--
-- NEDEN
-- ─────
-- Firma Segmentleri sayfası "son 12 ayda kazancı artan/düşen firmalar" diyordu ama
-- KIYAS PENCERESİNİ hiçbir yerde göstermiyordu: kullanıcı "son 12 ayı neyle
-- kıyaslıyorsun?" diye sordu ve haklıydı.
--
-- Kıyasın özelliği şu: pencerelerin bitiş noktası BUGÜN DEĞİL, arşivdeki en güncel
-- gerçek sonuç tarihi (`ref_tarih`). Bu bilinçli bir seçim — sonuç backfill'i sürekli
-- akıyor, son günler henüz işlenmemiş olabilir; bugünü çapa alsaydık her firma sahte
-- düşüş gösterirdi. Ama bu seçim ARAYÜZDE GÖRÜNMÜYORDU, dolayısıyla kullanıcı
-- rakamların hangi iki dönemi karşılaştırdığını bilemiyordu.
--
-- `yuklenici_segment_yenile()` ref_tarih'i hesaplıyor ama hiçbir yere SAKLAMIYOR;
-- sayaç RPC'si de bilmiyordu. Burada aynı ifadeyle yeniden hesaplanıp jsonb'ye
-- ekleniyor (max() geriye doğru tarar, indeksle ucuz).
--
-- ⚠️ Hesaplama mantığı DEĞİŞMİYOR — yalnızca zaten kullanılan çapa dışarıya açılıyor.
--    ref_tarih ifadesi yuklenici_segment_yenile() satır 38-40 ile BİREBİR aynı olmalı;
--    ayrışırsa arayüz yanlış pencere gösterir (sessiz tutarsızlık).
-- =============================================================================

CREATE OR REPLACE FUNCTION public.firma_segment_sayilari()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT jsonb_build_object(
    'parlayan', count(*) FILTER (WHERE seg_parlayan),
    'sonen',    count(*) FILTER (WHERE seg_sonen),
    'ilk_kez',  count(*) FILTER (WHERE seg_ilk_kez),
    'yuz50mn',  count(*) FILTER (WHERE seg_150mn),
    'guncellendi', max(segment_guncellendi),
    -- Kıyas çapası: segment hesabının kullandığı referans tarih (bugün DEĞİL).
    'ref_tarih', (
      SELECT max(s.sonuc_tarihi)::date
      FROM public.ihale_sonuclari s
      WHERE s.sonuc_tarihi <= now()
    )
  )
  FROM public.yukleniciler;
$$;

-- Yetki: sayaçlar üyeye özel (tablo düzeyi RLS zaten anon'u durduruyor).
GRANT EXECUTE ON FUNCTION public.firma_segment_sayilari() TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (migration sonrası):
--   SELECT public.firma_segment_sayilari();
--   → 'ref_tarih' anahtarı dolu gelmeli. NULL geliyorsa ihale_sonuclari'nda
--     sonuc_tarihi <= now() koşulunu sağlayan hiç satır yok demektir (beklenmez).
