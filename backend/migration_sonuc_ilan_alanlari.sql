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

-- =============================================================================
-- migration_sonuc_ilan_alanlari.sql — SONUÇ İLANI HTML'inden çıkarılan alanlar
-- 29 Tem 2026
-- =============================================================================
--
-- NEDEN
-- ─────
-- `ekap_sonuc_backfill.py` her sonuç kaydında EKAP'ın SONUÇ İLANI HTML'ini zaten
-- indiriyordu; içinden 4 regex okunup gerisi ATILIYORDU. O HTML'de bugün hiçbir
-- yerde saklanmayan 20+ alan var. Ayrıştırıcı genişletildi (ekap_sonuc_backfill.py,
-- `html_sonuc_detay_parse`) — bu dosya karşılık gelen kolonları açar.
-- EK EKAP İSTEĞİ YOKTUR: aynı yanıttan okunuyor.
--
-- YAN BULGU (aynı koşuda ölçüldü, kod tarafında düzeltildi):
--   `html_teklif_sayisi_parse` kalıbı ('Toplam Teklif Sayısı[^0-9]{0,20}?(\d+)')
--   gerçek HTML'de HİÇ eşleşmiyor — etiketle değer arasında ~54 karakter <td>
--   işaretlemesi var. 5 gerçek sonuç ilanında 3/3 alan None döndü. `katilimci_sayisi`
--   kolonunun 2,5M satırda tamamen boş olmasının sebebi bu.
--
-- ZATEN VAR OLAN KOLONLAR (migration_sonuc_B_kurulum.sql) — burada TEKRAR açılmıyor,
-- yalnız artık DOLDURULUYOR:
--   is_baslama_tarihi, is_bitis_tarihi, is_suresi_gun, sonuc_tur, ham_json,
--   yuklenici_il, katilimci_sayisi, gecerli_teklif_sayisi
--
-- KOLON EKLEMEYEN ALANLAR (HTML'de YOK — uydurulmadı):
--   karar_tarihi        → sonuç ilanında ihale komisyonu karar tarihi geçmiyor
--   yuklenici_vergi_no  → sonuç ilanında VKN hiç yayınlanmıyor
--
-- ÇALIŞTIRMA: VDS'te psql -f. Backfill KOŞARKEN güvenlidir:
--   · ADD COLUMN (nullable, DEFAULT'suz) PG11+ üzerinde salt meta veri → anlık.
--   · İndeksler KISMİ (WHERE ... IS NOT NULL) → şu an 0 satır eşleşiyor, anında kurulur.
--   · Kod migration'sız da çalışır (bkz. ekap_sonuc_backfill.SONUC_OPSIYONEL:
--     bilinmeyen kolon PGRST204 verirse o alan düşürülüp yeniden denenir).
-- =============================================================================

BEGIN;

-- ── 1) Yeni kolonlar ────────────────────────────────────────────────────────
ALTER TABLE public.ihale_sonuclari
  -- 1) İhalenin / c) Usulü — örn. 'Açık', 'Pazarlık (MD 21 C)', '4734 / 3-g'
  ADD COLUMN IF NOT EXISTS ihale_usulu            TEXT,
  -- yukarıdaki metinden türetilen madde referansı — '3-g', '21-c', '21-f'
  ADD COLUMN IF NOT EXISTS kanun_maddesi          TEXT,
  -- 1) İhalenin / d) Pazarlık Usulünün Seçilme Gerekçesi (yalnız pazarlık ihalelerinde)
  ADD COLUMN IF NOT EXISTS usul_gerekce           TEXT,
  -- 2) İhale konusu … / b) Yapılacağı yer | Yapılacağı/teslim edileceği yer
  ADD COLUMN IF NOT EXISTS isin_yeri              TEXT,
  -- 1) İhalenin / a) Tarihi (ihalenin yapıldığı gün; sözleşme tarihinden AYRI)
  ADD COLUMN IF NOT EXISTS ihale_tarihi           TIMESTAMPTZ,
  -- 3) Teklifler / a) Dokümanı EKAP üzerinden e-imza kullanarak indiren sayısı
  -- Rekabet hunisinin ÜST ucu: kaç firma baktı → kaç teklif verdi.
  ADD COLUMN IF NOT EXISTS dokuman_indiren_sayisi INTEGER,
  -- 3) Teklifler / Yerli istekli (veya yerli malı teklif eden istekli) lehine fiyat avantajı
  ADD COLUMN IF NOT EXISTS yerli_fiyat_avantaji   BOOLEAN,
  -- 4) Sözleşmenin / Yüklenicinin adresi  ⚠ ŞAHIS FİRMALARINDA KİŞİSEL VERİ → anon'a KAPALI
  ADD COLUMN IF NOT EXISTS yuklenici_adres        TEXT,
  -- 4) Sözleşmenin / Yüklenicinin uyruğu ('Türkiye' / yabancı) → yerli-yabancı ayrımı
  ADD COLUMN IF NOT EXISTS yuklenici_uyruk        TEXT;

COMMENT ON COLUMN public.ihale_sonuclari.dokuman_indiren_sayisi IS
  'SONUÇ İLANI 3-a: dokümanı e-imzayla indiren firma sayısı. teklif sayısıyla oranı = ilgi/katılım dönüşümü.';
COMMENT ON COLUMN public.ihale_sonuclari.yuklenici_adres IS
  'SONUÇ İLANI 4: yüklenici adresi. Şahıs firmalarında kişisel veri — anon''a AÇILMAZ.';
COMMENT ON COLUMN public.ihale_sonuclari.kanun_maddesi IS
  'ihale_usulu metninden türetilir: ''4734 / 3-g'' → ''3-g'', ''Pazarlık (MD 21 C)'' → ''21-c''.';

-- ── 2) İndeksler ────────────────────────────────────────────────────────────
-- Hepsi KISMİ: kolonlar bugün %100 NULL olduğu için kurulum anlık, tablo kilidi
-- pratikte yok. Backfill doldurdukça indeks kendiliğinden büyür.
-- (CONCURRENTLY KULLANILMADI: bu dosya tek transaction içinde koşuyor.)
CREATE INDEX IF NOT EXISTS idx_sonuc_yuklenici_il
  ON public.ihale_sonuclari (yuklenici_il) WHERE yuklenici_il IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sonuc_ihale_usulu
  ON public.ihale_sonuclari (ihale_usulu) WHERE ihale_usulu IS NOT NULL;

-- "sözleşmesi yakında bitecek işler" radarı — yenileme ihalesi öngörüsünün tabanı
CREATE INDEX IF NOT EXISTS idx_sonuc_is_bitis
  ON public.ihale_sonuclari (is_bitis_tarihi DESC) WHERE is_bitis_tarihi IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sonuc_kanun_maddesi
  ON public.ihale_sonuclari (kanun_maddesi) WHERE kanun_maddesi IS NOT NULL;

-- ── 3) ANON MASKESİ ─────────────────────────────────────────────────────────
-- ⚠ [[anon-maske-iki-kok-neden]]: yeni kolon varsayılan ayrıcalıkla anon'a AÇIK
-- doğabilir. ihale_sonuclari BEYAZ LİSTE modelinde (migration_anon_maske.sql:55-62
-- REVOKE + kolon GRANT) olduğu için yeni kolonlar teorik olarak kapalı doğar —
-- ama "teorik olarak" yetmez: aşağıda AÇIKÇA revoke ediliyor, sonra yalnız
-- kişisel/rekabet-hassasiyeti olmayan alanlar dar GRANT ile açılıyor.
REVOKE SELECT (
  ihale_usulu, kanun_maddesi, usul_gerekce, isin_yeri, ihale_tarihi,
  dokuman_indiren_sayisi, yerli_fiyat_avantaji, yuklenici_adres, yuklenici_uyruk
) ON public.ihale_sonuclari FROM anon;

-- Misafire AÇIK: usul/tarih/yer/sayı — mevcut kuralla aynı hat
-- ("Sayılar/tarihler/il/tür/kategori/bedeller misafire AÇIK", migration_anon_maske.sql:14).
GRANT SELECT (
  ihale_usulu, kanun_maddesi, isin_yeri, ihale_tarihi,
  dokuman_indiren_sayisi, yerli_fiyat_avantaji
) ON public.ihale_sonuclari TO anon;

-- Misafire KAPALI ve öyle kalacak:
--   yuklenici_adres  → şahıs firmalarında kişisel veri (KVKK)
--   yuklenici_uyruk  → yuklenici_* ailesi zaten anon'a kapalı, tutarlılık
--   usul_gerekce     → ihtiyaç duyan yüzey yok; açık yüzeyi bilerek dar tutuyoruz
--   ham_json         → İÇİNDE yüklenici adı + adresi var (migration_anon_maske.sql:9)
-- authenticated için ayrıca bir şey gerekmez: migration_sonuc_B_kurulum.sql'deki
-- TABLO düzeyi GRANT SELECT ... TO authenticated sonradan eklenen kolonları da kapsar.

COMMIT;

-- ── 4) Doğrulama (COMMIT sonrası, ayrı transaction) ─────────────────────────
DO $$
BEGIN
  BEGIN
    -- LIMIT 1: tek satır okur, 2,5M satırı taramaz. Amaç sadece kolonun VARLIĞI.
    PERFORM ihale_usulu, kanun_maddesi, usul_gerekce, isin_yeri, ihale_tarihi,
            dokuman_indiren_sayisi, yerli_fiyat_avantaji, yuklenici_adres, yuklenici_uyruk
      FROM public.ihale_sonuclari LIMIT 1;
  EXCEPTION WHEN undefined_column THEN
    RAISE EXCEPTION 'HATA: yeni kolonlar oluşmamış';
  END;
  RAISE NOTICE 'OK: yeni sonuç kolonları mevcut';
END $$;

-- anon maskesi denetimi — has_column_privilege doğrudan sorulur (HTTP 200 yanıltır,
-- bkz. [[http-200-ifsa-degil]]: gövdeye/ayrıcalığa bakmadan durum koduna güvenilmez).
DO $$
DECLARE kapali TEXT[] := ARRAY['yuklenici_adres','yuklenici_uyruk','usul_gerekce','ham_json'];
        acik   TEXT[] := ARRAY['ihale_usulu','kanun_maddesi','isin_yeri','ihale_tarihi',
                               'dokuman_indiren_sayisi','yerli_fiyat_avantaji'];
        k TEXT;
BEGIN
  FOREACH k IN ARRAY kapali LOOP
    IF has_column_privilege('anon', 'public.ihale_sonuclari', k, 'SELECT') THEN
      RAISE EXCEPTION 'HATA: anon "%" kolonunu okuyabiliyor!', k;
    END IF;
  END LOOP;
  FOREACH k IN ARRAY acik LOOP
    IF NOT has_column_privilege('anon', 'public.ihale_sonuclari', k, 'SELECT') THEN
      RAISE EXCEPTION 'HATA: anon "%" kolonunu okuyamıyor (misafir sayfası 42501 ile ölür)!', k;
    END IF;
  END LOOP;
  RAISE NOTICE 'OK: anon maskesi beklendiği gibi (% kapalı, % açık)',
               array_length(kapali,1), array_length(acik,1);
END $$;

NOTIFY pgrst, 'reload schema';
