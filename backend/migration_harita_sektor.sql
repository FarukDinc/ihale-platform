-- ============================================================================
-- migration_harita_sektor.sql — Harita sektör katmanı (16 Tem 2026)
--
-- harita.html'e sektör boyutu: il × kategori yoğunluk (choropleth) + bir il/sektör
-- kombinasyonunda öne çıkan firmaların SEKTÖRE ÖZGÜ sıralaması (yukleniciler.toplam_ciro
-- firma-geneli olduğundan yanıltıcıydı; burada ihale_sonuclari⋈ilanlar'dan sektör-içi
-- sözleşme/bedel hesaplanır).
--
-- Boyutlar (16 Tem): ihale_sonuclari 529K, ilanlar 355K → il_sektor_ozet tam-tablo
-- aggregate'i PostgREST varsayılan ~3s timeout KENARINDA (bkz. hafıza: rekabet_ozet
-- dersi). Çözüm aynı desen: ALTER FUNCTION ... SET statement_timeout. Client tek
-- sefer çeker, sessionStorage'da saklar (çıktı ≤ 81 il × ~42 kategori ≈ 3.4K satır).
--
-- yuklenici_id BİLİNÇLİ kullanılmıyor: ~92K sonuç satırında NULL (gece
-- yuklenici_yenile turu gecikmeli/çöp-ad) → JOIN yukleniciler firmaları düşürürdü.
-- Firma gruplaması normalize_firma(kazanan_firma) ile (migration_yuklenici_agg.sql).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_harita_sektor.sql
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE / DROP IF EXISTS. Tekrarı zararsız.
-- ============================================================================

-- 1) İndeksler
-- il+kategori firma sıralaması tr_fold(il) üzerinden eşleşir (ilanlar.il 'İSTANBUL'
-- gibi BÜYÜK; client display adı 'İstanbul' gönderir — I/ı locale tuzağına düşmemek
-- için iki taraf da tr_fold'lanır; fonksiyon IMMUTABLE, migration_ilanlar_arama_fold.sql).
CREATE INDEX IF NOT EXISTS idx_ilanlar_il_fold_kategori
  ON public.ilanlar (tr_fold(il), kategori);
-- sonuç→ilan join'i (FK indeksi yoksa güvence; varsa no-op)
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_ilan_id
  ON public.ihale_sonuclari (ilan_id);

-- 2) il × kategori yoğunluk özeti — harita katmanının tamamı TEK çağrıda.
--    firma_adet: yuklenici_id doluysa onunla, değilse ham ad (upper/btrim) ile
--    distinct — normalize_firma 529K satırda regex maliyeti nedeniyle burada YOK
--    (yoğunluk haritası için ± birkaç varyant sapması kabul edilebilir; firma
--    SIRALAMASI ise normalize_firma kullanan il_sektor_firmalar'dan gelir).
-- jsonb DÖNER (TABLE değil): ~3.4K satır PostgREST'in varsayılan db-max-rows=1000 limitine
-- takılıp KESİLİYORDU → harita eksik boyanıyordu. jsonb tek değer olduğundan satır limiti yok.
-- harita.html data.forEach(...) aynen çalışır (data = dizi). Return tipi değiştiği için DROP+CREATE.
DROP FUNCTION IF EXISTS public.il_sektor_ozet();
CREATE OR REPLACE FUNCTION public.il_sektor_ozet()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
           'il', il, 'kategori', kategori, 'firma_adet', firma_adet,
           'sozlesme_adet', sozlesme_adet, 'toplam_bedel', toplam_bedel)), '[]'::jsonb)
  FROM (
    SELECT i.il,
           COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer') AS kategori,
           count(DISTINCT COALESCE(s.yuklenici_id::text, upper(btrim(s.kazanan_firma))))::bigint AS firma_adet,
           count(*)::bigint AS sozlesme_adet,
           sum(COALESCE(s.kazanan_teklif, 0)) AS toplam_bedel
    FROM public.ihale_sonuclari s
    JOIN public.ilanlar i ON i.id = s.ilan_id
    WHERE s.kazanan_firma IS NOT NULL
      AND i.il IS NOT NULL AND btrim(i.il) <> ''
    GROUP BY i.il, COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer')
  ) t;
$$;
ALTER FUNCTION public.il_sektor_ozet() SET statement_timeout = '30s';
GRANT EXECUTE ON FUNCTION public.il_sektor_ozet() TO anon, authenticated, service_role;

-- 3) Bir il (+ opsiyonel kategori) için öne çıkan firmalar — sektör-İÇİ sözleşme/bedel.
--    p_il_folds: tr_fold'lanmış il varyantları (['afyonkarahisar','afyon'] gibi —
--    client alias'ları ekler). Görünen ad: en güncel sonuçtaki ham kazanan_firma.
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8
)
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE
AS $$
  SELECT (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS ad,
         count(*)::bigint AS sozlesme,
         sum(COALESCE(s.kazanan_teklif, 0)) AS toplam_bedel
  FROM public.ihale_sonuclari s
  JOIN public.ilanlar i ON i.id = s.ilan_id
  WHERE tr_fold(i.il) = ANY(p_il_folds)
    AND (p_kategori IS NULL OR i.kategori = p_kategori)
    AND s.kazanan_firma IS NOT NULL
    AND normalize_firma(s.kazanan_firma) IS NOT NULL
  GROUP BY normalize_firma(s.kazanan_firma)
  ORDER BY sum(COALESCE(s.kazanan_teklif, 0)) DESC, count(*) DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
-- İstanbul gibi büyük il + normalize_firma regex maliyeti için pay bırak
ALTER FUNCTION public.il_sektor_firmalar(text[], text, int) SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int) TO anon, authenticated, service_role;

-- 4) il_rfq_dagilimi'ne kategori filtresi (geriye uyumlu: parametresiz çağrı aynı sonucu verir).
--    Eski sıfır-arg overload DROP edilir — PostgREST'te çift overload boş-body çağrıda
--    belirsizlik yaratır; DEFAULT NULL'lı tek fonksiyon iki kullanımı da karşılar.
DROP FUNCTION IF EXISTS public.il_rfq_dagilimi();
CREATE OR REPLACE FUNCTION public.il_rfq_dagilimi(p_kategori text DEFAULT NULL)
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT il, count(*)::bigint
  FROM public.satinalma_talepleri
  WHERE durum = 'acik' AND il IS NOT NULL AND btrim(il) <> ''
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY il;
$$;
GRANT EXECUTE ON FUNCTION public.il_rfq_dagilimi(text) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM il_sektor_ozet();                                      -- ~2-3.4K satır
--   SELECT * FROM il_sektor_ozet() WHERE kategori LIKE 'Sağlık%' ORDER BY sozlesme_adet DESC LIMIT 5;
--   SELECT * FROM il_sektor_firmalar(ARRAY['ankara'], 'Sağlık - Medikal - İlaç - Kozmetik', 5);
--   SELECT * FROM il_rfq_dagilimi(NULL) LIMIT 5;
