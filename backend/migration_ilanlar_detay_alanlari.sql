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

-- migration_ilanlar_detay_alanlari.sql — 29 Tem 2026
--
-- BAĞLAM: "zaten çekilen ama okunmadan atılan EKAP yanıtı" denetimi.
-- `GetByIhaleIdIhaleDetay` yanıtı İKİ backfill tarafından çekiliyor ama her biri
-- içinden TEK alan alıp gerisini atıyordu:
--     ilan_metni_backfill.py   → yalnız ilanList[0].veriHtml
--     ekap_sonuc_backfill.py   → yalnız sozlesmeBilgiList + ilanList
-- Atılanlar (canlı yanıtta doğrulandı, 29 Tem — iki örnek: durum=5 ve durum=2):
--     item.eIhale · item.kismiIhale · item.ihaleKapsamAciklama · item.idareId
--     item.ihtiyacKalemiOkasList · item.ihaleOzellikList
--     ihaleBilgi.{okas, isinYapilacagiYer, ihaleYeri, istisnaUsulAciklama,
--                 itirazenSikayetBasvuruBedeli, iptalTarihi/Nedeni/Madde,
--                 ihaleTarihSaatList}
--     idare.{telefon, fax, ustIdare, enUstIdareKod, enUstIdareAdi, il.adi, ilce.ilceAdi}
-- Ölçüm: ilanlar.okas %0,62 · ihtiyaç kalemi %0,41 dolu — yani veri elimizdeyken atılmış.
-- Kod tarafı 29 Tem'de düzeltildi (backend/ekap_detay_alanlar.py); bu dosya ŞEMA tarafı.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ilanlar_detay_alanlari.sql
--
-- ⚠️ BU MIGRATION UYGULANMADAN DA KOD ÇÖKMEZ. ekap_detay_alanlar.kolonlari_sapta()
--    süreç başında PostgREST'e `select=<aday kolonlar>` sorar, 42703 dönen kolonları
--    listeden düşürür; yazımda da PGRST204/42703 için düşür-ve-tekrar-dene vardır ve
--    en kötü halde YALNIZ eski gövde (ilan_metni / ihale_sonuclari) yazılır. Yani bu
--    dosya bir ÖN KOŞUL değil, alanların gerçekten yazılabilmesinin koşuludur.
--    Backfill'ler KOŞARKEN uygulanabilir: yeni kolonlar bir sonraki süreç başlangıcında
--    (ya da PATCH'teki yeniden-deneme yolunda) kendiliğinden devreye girer.
--
-- ⚠️ TABLO DÜZEYİNDE REVOKE YOK. `ilanlar`da anon'un tablo-geneli SELECT'i YOKTUR
--    (misafir maskesi kolon-GRANT'larıyla kurulu — migration_anon_maske.sql).
--    PostgreSQL'de `REVOKE SELECT ON t FROM anon` kolon-GRANT'larını da siler →
--    misafir tarafı topyekûn ölür. Aşağıda YALNIZ kolon düzeyinde revoke/grant var.
--
-- ⚠️ İNDEKS UYARISI: CREATE INDEX (CONCURRENTLY değil — tek işlem) süresince ilanlar'a
--    YAZMA bekler. İndeksler KISMİ (yalnız NOT NULL) ama tarama yine tam tablodur;
--    1,96M satırda ~10-40 sn sürebilir. O sırada akan backfill'in PATCH'i bekler,
--    30 sn timeout'a takılırsa kendi yeniden-deneme yolunu kullanır (kayıp yok).

BEGIN;

-- ── 1) İhale bloğu kolonları ──────────────────────────────────────────────────
-- yasa_kapsami: item.ihaleKapsamAciklama ('4734 Kapsamında' | 'İstisna').
--   ⚠️ ihaleBilgi.ihaleKapsamAciklama i18n ANAHTARI döner ('TENDER_SEARCH…EXCEPTION'),
--      item'daki çevrilmiş sürüm kullanılır; o da yoksa yasaKapsami4734 ('1'|'2') koduna düşülür.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS yasa_kapsami        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS istisna_usul        text;   -- '4734 / 3-g'

-- ── 2) İPTAL BİLGİSİ ──────────────────────────────────────────────────────────
-- ⛔ PROJE KARARI: bu kolonlar DOLDURULUR ama `durum` alanına 'iptal' YAZILMAZ.
--    Arayüz 'iptal' durumunu beklemiyor; yazılsaydı 236.647 kayıt tüm sekmelerden
--    SESSİZCE düşerdi. Durum dönüşümü arayüz hazırlandıktan sonra AYRI iş olarak.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_tarihi        timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_nedeni        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS iptal_madde         text;

-- ── 3) ihaleBilgi.ihaleTarihSaatList — etiketli tarihler ──────────────────────
-- DATASYNC.IHALE_TARIH_SAAT            → mevcut `ihale_tarihi` kolonuna yazılır
-- DATASYNC.YETERLIK_TARIH_SAAT         → yeterlik_tarihi
-- DATASYNC.ILK_TEKLIF_ICIN_TARIH_SAAT  → ilk_teklif_tarihi
-- Bilinmeyen bir etiket gelirse (EKAP yeni alan eklerse) HAM liste ihale_tarih_saatleri'ne
-- düşer — "bir daha veri atmayalım" ilkesi. Bilinen etiketlerde bu kolon NULL kalır.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS yeterlik_tarihi      timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ilk_teklif_tarihi    timestamptz;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ihale_tarih_saatleri jsonb;

-- ── 4) item.ihaleOzellikList — ihale nitelikleri ──────────────────────────────
-- ['EKONOMIK_MALI_YETERLIK','IS_DENEYIM_BELGE','YABANCI_ISTEKLI_KATILIM',
--  'ALT_YUKLENICI','MESLEKI_TEKNIK_YETERLIK','FIYAT_FARKI_VERILMESI','AVANS', …]
-- ('TENDER_DETAIL.' öneki kod tarafında kırpılır.)
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ihale_ozellikleri    text[];

-- ── 5) idare bloğu ────────────────────────────────────────────────────────────
-- ekap_idare_id = EKAP'ın İÇ idare kimliği (item.idareId / idare.id, ör. '1996').
--   DEĞERİ: DETSİS eşleştirmesinin ANAHTARI — arama filtresi `idareKodList=[idareId]`
--   tam bu değeri istiyor (bkz. ekap_idare_probe.py). idare ADI ile join AMBİGÜ
--   ("BİLGİ İŞLEM DAİRE BAŞKANLIĞI" = 114 kayıt); bu kolon dolunca idare_tur
--   sınıflandırması ad tahmininden çıkıp otoriter kimliğe bağlanabilir.
-- telefon/faks KURUMSAL iletişimdir (kişi verisi değil) — yine de anon'a KAPALI:
--   `idare` zaten misafir maskesinde, ondan türeyen her şey de kapalı kalmalı.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ekap_idare_id        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_telefon        text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_faks           text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ust_idare            text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS en_ust_idare_kod     text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS en_ust_idare_adi     text;   -- 'KİTLER' / 'BİTLER'
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_il             text;
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS idare_ilce           text;

-- ── 6) MİSAFİR (anon) GÖRÜNÜRLÜĞÜ — dar tutuldu ───────────────────────────────
-- KURAL: ihale bloğundan gelen kamuya açık nitelikler AÇIK; `idare` bloğundan gelen
-- HER ŞEY KAPALI (çünkü `idare` kolonunun kendisi misafir maskesinde).
--
-- "Önce REVOKE sonra dar GRANT": yeni kolon varsayılan ayrıcalıkla açık doğabilir
-- ([[anon-maske-iki-kok-neden]] kök-neden A) — niyeti şemaya kazıyoruz.
REVOKE SELECT (
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri,
  ekap_idare_id, idare_telefon, idare_faks, ust_idare,
  en_ust_idare_kod, en_ust_idare_adi, idare_il, idare_ilce
) ON public.ilanlar FROM anon;

GRANT SELECT (
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri
) ON public.ilanlar TO anon;
-- ekap_idare_id / idare_telefon / idare_faks / ust_idare / en_ust_idare_kod /
-- en_ust_idare_adi / idare_il / idare_ilce → anon'a BİLEREK VERİLMEDİ.
--
-- ⚠️⚠️ SONRAKİ İŞ (bu dosyanın DIŞINDA): migration_anon_maske.sql `ilanlar` için
--    `REVOKE SELECT ON public.ilanlar FROM anon` + SABİT bir kolon listesiyle GRANT
--    yapıyor. O dosya BİR DAHA KOŞULURSA yukarıdaki 9 anon GRANT'ı SESSİZCE SİLİNİR
--    ve misafir yolunda bu kolonlara dokunan her sorgu 42501 ile sayfayı öldürür
--    ([[anon-maske-iki-kok-neden]] kök-neden C ile aynı sınıf hata). Bu 9 kolon
--    migration_anon_maske.sql'deki ilanlar GRANT listesine de EKLENMELİ.
--    (Bu dosya onu kendi başına yapmıyor: 29 Tem'de o dosya paralel bir oturumda
--     düzenleniyordu, aynı anda iki taraftan yazmak yasak.)

-- Üye tarafı: `authenticated` ilanlar'da TABLO-GENELİ SELECT'e sahip, yani yeni kolonlar
-- ona zaten açık. Aşağıdaki GRANT bir üst küme (no-op) — niyeti açıkça kayda geçiriyor.
GRANT SELECT (
  yasa_kapsami, istisna_usul,
  iptal_tarihi, iptal_nedeni, iptal_madde,
  yeterlik_tarihi, ilk_teklif_tarihi, ihale_tarih_saatleri,
  ihale_ozellikleri,
  ekap_idare_id, idare_telefon, idare_faks, ust_idare,
  en_ust_idare_kod, en_ust_idare_adi, idare_il, idare_ilce
) ON public.ilanlar TO authenticated;

-- ── 7) İndeksler (KISMİ — ölü uzayı indekslemez) ──────────────────────────────
-- CONCURRENTLY DEĞİL: bu dosya tek işlemde (BEGIN…COMMIT) çalışıyor.
CREATE INDEX IF NOT EXISTS idx_ilanlar_ekap_idare_id
    ON public.ilanlar (ekap_idare_id) WHERE ekap_idare_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ilanlar_iptal_tarihi
    ON public.ilanlar (iptal_tarihi DESC) WHERE iptal_tarihi IS NOT NULL;

-- ── 8) DOĞRULAMA: maske gerçekten kapalı mı (HTTP 200 ≠ ifşa dersi: yetkiye BAK) ──
DO $$
DECLARE
  k text;
  acik text[] := ARRAY[]::text[];
BEGIN
  FOREACH k IN ARRAY ARRAY['ekap_idare_id','idare_telefon','idare_faks','ust_idare',
                           'en_ust_idare_kod','en_ust_idare_adi','idare_il','idare_ilce']
  LOOP
    IF has_column_privilege('anon', 'public.ilanlar', k, 'SELECT') THEN
      acik := acik || k;
    END IF;
  END LOOP;
  IF array_length(acik, 1) IS NOT NULL THEN
    RAISE EXCEPTION 'ANON MASKE DELIK: idare kokenli kolon(lar) misafire ACIK: %', acik;
  END IF;

  -- Ters yön: misafire açılması gerekenler gerçekten açık mı (sayfa 42501 ile ölmesin)
  FOREACH k IN ARRAY ARRAY['yasa_kapsami','istisna_usul','iptal_tarihi','iptal_nedeni',
                           'iptal_madde','yeterlik_tarihi','ilk_teklif_tarihi',
                           'ihale_tarih_saatleri','ihale_ozellikleri']
  LOOP
    IF NOT has_column_privilege('anon', 'public.ilanlar', k, 'SELECT') THEN
      RAISE EXCEPTION 'GRANT EKSIK: anon % kolonunu okuyamiyor', k;
    END IF;
  END LOOP;

  RAISE NOTICE 'OK: 17 kolon eklendi; idare kokenli 8 kolon misafire KAPALI, ihale nitelikleri ACIK.';
END $$;

COMMIT;

-- PostgREST şema önbelleği (yeni kolon + GRANT görünür olsun).
NOTIFY pgrst, 'reload schema';

-- ── ELLE DOĞRULAMA ────────────────────────────────────────────────────────────
-- 1) Doluluk (backfill ilerledikçe artmalı):
--    SELECT count(*) FILTER (WHERE okas IS NOT NULL)          AS okas,
--           count(*) FILTER (WHERE kalemler IS NOT NULL)      AS kalem,
--           count(*) FILTER (WHERE yasa_kapsami IS NOT NULL)  AS kapsam,
--           count(*) FILTER (WHERE ekap_idare_id IS NOT NULL) AS idare_id,
--           count(*) FILTER (WHERE iptal_tarihi IS NOT NULL)  AS iptal,
--           count(*) AS toplam
--    FROM public.ilanlar;
-- 2) İptal kolonu doldu ama durum DEĞİŞMEDİ mi (0 satır beklenir):
--    SELECT count(*) FROM public.ilanlar WHERE iptal_tarihi IS NOT NULL AND durum = 'iptal';
-- 3) Misafir maskesi (curl — gövdeye BAK, sadece HTTP koduna değil):
--    curl -s "https://ihaleglobal.com/rest/v1/ilanlar?select=idare_telefon&limit=1" \
--         -H "apikey: <ANON>" -H "Authorization: Bearer <ANON>"
--    → 42501 beklenir. 200 + dolu gövde gelirse maske DELİK.
--    curl -s "https://ihaleglobal.com/rest/v1/ilanlar?select=yasa_kapsami,iptal_tarihi&limit=1" \
--         -H "apikey: <ANON>" -H "Authorization: Bearer <ANON>"
--    → 200 beklenir (misafir sayfası bu kolonlarla filtre yaparsa ölmesin).
