-- ============================================================================
-- migration_kik_kararlar_arama_fold.sql
--
-- KÖK NEDEN (20 Tem 2026 ölçümü): kik-kararlar.html'in kelime araması dört
-- kolonda düz ILIKE yapıyordu (baslik/idare/ihale_konusu/ozet). PostgreSQL'in
-- lower()'ı Türkçe 'İ'yi 'i'ye katlamadığı için ILIKE noktalı İ içeren satırları
-- HİÇBİR ZAMAN eşleştirmiyor. Canlı anon REST ölçümü (saf ASCII desenler):
--
--     /rest/v1/kik_kararlar?idare=ilike.*BELED*      -> 19 satır
--     /rest/v1/kik_kararlar?idare=ilike.*belediye*   ->  2 satır
--     /rest/v1/kik_kararlar?idare=ilike.*BELEDIYE*   ->  2 satır
--
-- Aradaki 17 satırda 'BELEDİYE' yazıyor; ASCII 'I' ile yazılan hiçbir desen
-- onları getirmiyor. Yani sayfanın TEK işlevi olan arama, eşleşmelerin ~%89'unu
-- sessizce yutuyordu. Tablo 97 satırdayken bu görünmüyordu; kik_backfill'in
-- penceresi 3 günden 90 güne çıkıp tablo binlerce satıra büyüdüğünde arama ilk
-- kez gerçekten kullanılacak.
--
-- AYRICA: aynı sorguya count:'exact' eklendi — düzeltilmezse kullanıcı
-- "Bu aramaya uyan 2 karar var" diye KENDİNDEN EMİN ve YANLIŞ bir toplam görür.
-- Eskiden sayı hiç değilse indirilen diliminkiydi.
--
-- ÇÖZÜM: repoda zaten var olan reçete (migration_ilanlar_arama_fold.sql,
-- migration_ihale_sonuclari_arama_fold.sql) — tr_fold() + generated STORED
-- katlanmış birleşik kolon + pg_trgm GIN indeks. Frontend arama terimini de
-- trFold()'layıp bu kolonda arar, iki taraf da aynı normal forma iner.
--
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrar çalıştırmak zararsız.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     < backend/migration_kik_kararlar_arama_fold.sql
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- tr_fold() migration_ilanlar_arama_fold.sql'de tanımlı — burada da idempotent
-- olarak garanti altına alınıyor (bu migration tek başına da çalıştırılabilsin diye).
--
-- ⛔ Bu gövde SQL tarafında BAYT BAYT sabit kalmalı: frontend trFold()
-- (kik-kararlar.html, ihaleler.html, firma-analiz.html) ile birebir aynı katlamayı
-- yapmak zorunda. Değişirse arama sessizce 0 döndürmeye başlar.
CREATE OR REPLACE FUNCTION tr_fold(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT lower(translate(coalesce(s, ''),
    'İIıŞşĞğÜüÖöÇç',
    'iiissgguuoocc'));
$$;

-- Katlanmış birleşik arama kolonu.
--
-- MALİYET: ilanlar'daki eşdeğer migration'ın aksine burada uyarı gerekmiyor —
-- kik_kararlar küçük (97 satır; 365 günlük backfill sonrası ~birkaç bin) ve
-- birleştirilen alanlar kısa metin (ilan_metni gibi ~6,7KB/satır bir alan YOK).
-- ADD COLUMN GENERATED tabloyu bir kez yeniden yazar ama bu ölçekte anlık.
--
-- Birleştirilen 4 alan, kik-kararlar.html'in
-- eski .or(...) listesiyle TAM PARİTE olsun diye birebir aynı seçildi:
--   baslik, idare, ihale_konusu, ozet
-- (karar_no bilerek DIŞARIDA: '2026/UH.II-1234' biçiminde saf ASCII ve sayfada
--  ayrı bir alandan eq/ilike ile aranıyor — katlamaya ihtiyacı yok.)
ALTER TABLE public.kik_kararlar
  ADD COLUMN IF NOT EXISTS arama_fold text
  GENERATED ALWAYS AS (
    tr_fold(
      coalesce(baslik, '')       || ' ' ||
      coalesce(idare, '')        || ' ' ||
      coalesce(ihale_konusu, '') || ' ' ||
      coalesce(ozet, '')
    )
  ) STORED;

CREATE INDEX IF NOT EXISTS idx_kik_kararlar_arama_fold_trgm
  ON public.kik_kararlar USING gin (arama_fold gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- ⚠️ ANON KOLON GRANT'I — ATLANIRSA MİSAFİRDE SAYFA ÖLÜR
--
-- kik_kararlar tablo-geneli SELECT'i migration_anon_maske_v2.sql'de anon'dan
-- REVOKE edildi ve yerine 10 kolonluk bir KOLON-GRANT'ı verildi. Kolon-grant
-- modelinde SONRADAN eklenen kolon o listeye KENDİLİĞİNDEN GİRMEZ — yeni kolon
-- anon için yetkisiz doğar. Üstelik PostgreSQL bir kolonu WHERE'de kullanmak
-- için de SELECT yetkisi ister; yani grant'sız arama_fold, misafirin arama
-- sorgusunun TAMAMINI 42501 ile reddettirir (aynı sınıf hata 19 Tem'de
-- idare_tur ile iki sayfayı düşürdü).
--
-- İFŞA RİSKİ YOK: arama_fold yalnızca zaten anon'a AÇIK olan 4 kolonun
-- (baslik/idare/ihale_konusu/ozet) katlanmış birleşimi — yeni bir veri yüzeyi
-- açmıyor. ham_veri/olusturulma kapalı kalmaya devam ediyor.
--
-- authenticated'ın tablo-geneli SELECT'i duruyor (v2 yalnız anon'dan revoke
-- etti), yani orada kolon zaten miras alınıyor; yine de açıkça yazıyoruz ki
-- ileride authenticated da kolon-grant'a çevrilirse bu satır sessizce düşmesin.
-- ---------------------------------------------------------------------------
GRANT SELECT (arama_fold) ON public.kik_kararlar TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- DOĞRULAMA — uygulamadan sonra
-- ============================================================================
--   SELECT tr_fold('BELEDİYE BAŞKANLIĞI');     -- -> 'belediye baskanligi'
--
--   -- Eskiden 2, şimdi 19 dönmeli (BELEDİYE'li 17 satır artık yakalanıyor):
--   SELECT count(*) FROM public.kik_kararlar WHERE arama_fold ILIKE '%belediye%';
--
--   -- Misafir (anon) dumanı — 200 BEKLENİR, 42501 gelirse GRANT düşmüş demektir:
--   curl -s -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     "https://ihaleglobal.com/rest/v1/kik_kararlar?select=karar_no&arama_fold=ilike.*belediye*&limit=1"
--
--   -- ham_veri HÂLÂ kapalı olmalı (401/42501 BEKLENİR):
--   curl ... "https://ihaleglobal.com/rest/v1/kik_kararlar?select=ham_veri&limit=1"
