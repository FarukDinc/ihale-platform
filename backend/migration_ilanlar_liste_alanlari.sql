-- ⛔⛔ BU DOSYA ARTIK KOŞULMAMALI — migration_ekap_hasat.sql İLE BİRLEŞTİRİLDİ (29 Tem 2026)
--
-- 4 ayrı çalışmanın önerdiği kolonlar TEK migration'da toplandı:
--     backend/migration_ekap_hasat.sql
-- Birleştirme sırasında İKİ KOLON YENİDEN ADLANDIRILDI (iki ajan aynı anlamı
-- farklı adla önermişti):
--     kanun_maddesi  → yasa_madde_kodu   (ihale_sonuclari)
--     en_ust_idare   → en_ust_idare_adi  (dogrudan_temin_ilanlari)
-- İlgili .py dosyaları YENİ adlara göre düzeltildi. Bu dosya koşulursa ESKİ adlı,
-- hiçbir kodun YAZMADIĞI ölü kolonlar oluşur ve maske bekçileri şaşar.
--
-- Tarihsel kayıt olarak duruyor; çalıştırılmasın diye aşağıda ABORT var.
DO $$
BEGIN
  RAISE EXCEPTION 'BU DOSYA DEVRE DISI: migration_ekap_hasat.sql ile birlestirildi. Onu kosun.';
END $$;

-- migration_ilanlar_liste_alanlari.sql — 29 Tem 2026
--
-- BAĞLAM: "zaten çekilen ama okunmadan atılan EKAP yanıtı" denetimi.
-- ilanlar.ekap_ihale_id yalnız %17,7 dolu (347.010/1.962.279) — oysa bu hash EKAP'ın
-- liste yanıtının İÇİNDE geliyor; iki backfill (ekap_ihale_backfill / ekap_sonuc_backfill)
-- onu kayıt sözlüğüne koymadan atıyordu. Aynı kayıtta `usul` ve `son_teklif_tarihi` de
-- kompakt yolda düşüyordu. Kod tarafı 29 Tem'de düzeltildi; bu dosya ŞEMA tarafını
-- garanti altına alır + bugüne kadar yazılmış BOZUK belge linklerini onarır.
--
-- ⚠️ Bu migration UYGULANMADAN da kod çökmez: yazma katmanı PostgREST'in
--    PGRST204/42703 yanıtını yakalayıp YALNIZ eksik opsiyonel alanı düşürerek yeniden
--    dener (bkz. ekap_ihale_backfill.eksik_kolon / ekap_sonuc_backfill.kompakt_eksik_kolon).
--    Yani migration bir ÖN KOŞUL değil, alanların gerçekten yazılabilmesinin koşuludur.
--
-- ⚠️ TABLO düzeyinde REVOKE YOK. ilanlar'da anon'un tablo-geneli SELECT'i YOKTUR
--    (misafir maskesi kolon-GRANT'larıyla kurulu). PostgreSQL'de `REVOKE SELECT ON t`
--    kolon-GRANT'ları da siler → misafir tarafı topyekûn ölürdü. Bu yüzden aşağıda
--    yalnız KOLON düzeyinde revoke/grant yapılıyor.

BEGIN;

-- ── 1) Kolonlar (canlıda üçü de VAR — bu blok yeni/temiz ortamlar için güvence) ──
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ekap_ihale_id     text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS usul              text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS son_teklif_tarihi timestamptz;

-- ── 2) Misafir görünürlüğü (kolon bazlı, açıkça yazılmış) ──────────────────────
-- Üçü de HASSAS DEĞİL ve ihale-detay.html ANON_KOLONLAR listesinde zaten var:
--   ekap_ihale_id → EKAP'ın kendi genel doküman sayfasının anahtarı (kişi verisi yok)
--   usul / son_teklif_tarihi → ilan sayfasının rozet/sayaç yüzeyleri
-- Önce dar REVOKE, sonra dar GRANT: "sonradan eklenen kolon varsayılan ayrıcalıkla
-- açık doğar" tuzağına karşı niyeti kayda geçirir; mevcut durumu DEĞİŞTİRMEZ.
REVOKE SELECT (ekap_ihale_id, usul, son_teklif_tarihi) ON public.ilanlar FROM anon;
GRANT  SELECT (ekap_ihale_id, usul, son_teklif_tarihi) ON public.ilanlar TO   anon;

-- ── 3) "Hâlâ eksik olanı bul" indeksi (kısmi → küçük kalır) ────────────────────
-- CONCURRENTLY DEĞİL: bu dosya tek işlemde (BEGIN…COMMIT) çalışıyor.
CREATE INDEX IF NOT EXISTS idx_ilanlar_ekap_ihale_id_eksik
    ON public.ilanlar (ikn) WHERE ekap_ihale_id IS NULL AND kaynak = 'ekap';

-- ── 4) BOZUK BELGE LİNKLERİNİ ONAR ────────────────────────────────────────────
-- ilanlar.belgeler içindeki url'ler `…/b_ihalearama/api/Dokuman/GetFile?id=…` olarak
-- üretiliyordu. O bir API endpoint'i: imzalı crypto header olmadan 401 döner, yani
-- kullanıcının TARAYICISINDA ÇALIŞMAZ. Çalışan uç EKAP'ın vatandaş doküman sayfası;
-- ihale hash'iyle (ekap_ihale_id) açılıyor — ihale-detay.html'in ürettiği şablonun aynısı.
--
-- ⚠️ GetDokumanUrl'in DÖNDÜĞÜ hash saklanmaz: 29 Tem'de ölçüldü, aynı ihaleId+islemId
--    için ardışık üç çağrı üç FARKLI hash döndürdü → oturumluk token, DB'de bayatlar.
--    Kalıcı olan liste hash'idir (ekap_ihale_id).
--
-- jsonb_typeof guard'ı ŞART: dizi olmayan (çift kodlanmış/bozuk) değerlerde
-- jsonb_array_elements sorgunun tamamını düşürürdü.
UPDATE public.ilanlar i
SET belgeler = (
        SELECT jsonb_agg(
                 CASE WHEN e->>'url' LIKE '%/api/Dokuman/GetFile%'
                      THEN jsonb_set(
                             e, '{url}',
                             to_jsonb(
                               'https://ekap.kik.gov.tr/EKAP/Ortak/VatandasIlanGoruntuleme.aspx'
                               || '?ddac=true&aramaDownload=true&ihaleId=' || i.ekap_ihale_id
                               || '&wots=false&Iszylnm=false'
                             ))
                      ELSE e END
                 ORDER BY ord)
        FROM jsonb_array_elements(i.belgeler) WITH ORDINALITY AS t(e, ord)
    )
WHERE i.ekap_ihale_id IS NOT NULL
  AND jsonb_typeof(i.belgeler) = 'array'
  AND i.belgeler::text LIKE '%/api/Dokuman/GetFile%';

COMMIT;

-- PostgREST şema önbelleği (yeni kolon/GRANT görünür olsun).
NOTIFY pgrst, 'reload schema';

-- ── DOĞRULAMA (elle koş) ──────────────────────────────────────────────────────
-- Doluluk:
--   SELECT count(*) FILTER (WHERE ekap_ihale_id IS NOT NULL) AS dolu, count(*) AS toplam
--   FROM public.ilanlar;
-- Bozuk link kaldı mı (0 beklenir; ekap_ihale_id'si NULL olanlar hariç):
--   SELECT count(*) FROM public.ilanlar
--   WHERE belgeler::text LIKE '%/api/Dokuman/GetFile%';
-- Misafir hâlâ görebiliyor mu (kolon-GRANT bozulmadı mı):
--   curl -s "https://ihaleglobal.com/rest/v1/ilanlar?select=ekap_ihale_id,usul,son_teklif_tarihi&limit=1" \
--        -H "apikey: <ANON>" -H "Authorization: Bearer <ANON>"
--   → 200 + gövde beklenir; 42501 gelirse GRANT geri alınmış demektir.
