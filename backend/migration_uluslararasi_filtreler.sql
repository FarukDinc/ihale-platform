-- Uluslararası ihaleler ekranı: ülke + kategori filtre seçenekleri (DISTINCT, sunucu tarafında).
--
-- NEDEN: uluslararasi.html `select('ulke,kategori').limit(5000)` ile dropdown'ları ve "ülke
-- sayısı" sayacını ÖRNEKLEMDEN üretiyordu. ORDER BY olmadığı için 5.000 satır tavanı aşıldığı
-- anda liste keyfî bir örnekleme dönüşür → dropdown'da SESSİZCE eksik ülke/kategori, yanlış
-- sayaç. TED scraper'ın gün-gün pencerelemesi tabloyu günde ~1.280 satır büyüttüğü için tavan
-- birkaç gün içinde aşılıyordu (1.249 + 1.280×3 = 5.089); --sadece-acik (~31.000) veya 90
-- günlük backfill (~93.000) ile anında kırılıyordu.
--
-- Aynı ekrandaki dünya haritası zaten ulke_ihale_dagilimi() ile sunucu tarafında topluyor;
-- bu RPC o deseni takip eder ve hacimden bağımsız olarak DOĞRU kalır.
--
-- Sıralama bilerek yapılmaz: çağıran taraf localeCompare(...,'tr') ile sıralar (Türkçe
-- harf sırası — İ/ı, Ç, Ş, Ğ, Ö, Ü — DB collation'ına güvenilmez).

CREATE OR REPLACE FUNCTION public.uluslararasi_filtre_secenekleri()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT jsonb_build_object(
    'ulkeler', (
      SELECT coalesce(jsonb_agg(v), '[]'::jsonb)
      FROM (SELECT DISTINCT ulke AS v FROM public.uluslararasi_ihaleler
            WHERE ulke IS NOT NULL AND btrim(ulke) <> '') t
    ),
    'kategoriler', (
      SELECT coalesce(jsonb_agg(v), '[]'::jsonb)
      FROM (SELECT DISTINCT kategori AS v FROM public.uluslararasi_ihaleler
            WHERE kategori IS NOT NULL AND btrim(kategori) <> '') t
    )
  );
$$;

GRANT EXECUTE ON FUNCTION public.uluslararasi_filtre_secenekleri() TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
