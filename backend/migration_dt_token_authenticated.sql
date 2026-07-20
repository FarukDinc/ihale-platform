-- ============================================================================
-- İhaleGlobal — dogrudan_temin_ilanlari: token kolonlarını `authenticated`a KAPAT
--
-- AÇIK (19 Tem 2026 denetiminde bulundu):
--   migration_dogrudan_temin.sql:45 → GRANT SELECT ON public.dogrudan_temin_ilanlari
--   TO authenticated;  ← TABLO GENELİ, hiç geri alınmamış.
--   migration_anon_maske.sql:84 anon için REVOKE yapmış ama `authenticated` için
--   AYNI İŞLEM YAPILMAMIŞ. Sonuç: herhangi bir üye (ücretsiz kayıt yeterli)
--     GET /rest/v1/dogrudan_temin_ilanlari?select=dt_no,dt_ihale_token,dt_idare_token
--   ile EKAP'ın E10/E11 anahtarlarını toplu çekebiliyor.
--
--   migration_dt_kazanan.sql:24-26'daki yorum bu tokenların "authenticated'a kapalı"
--   olduğunu varsayıyor — YANLIŞ. Bu migration o varsayımı GERÇEK yapar.
--
-- NEDEN ÖNEMLİ: tokenlar "teaser" veri değil, saf altyapı. dt_kazanan_scraper.py
-- bunlarla dtDetayGetir'i CAPTCHA'sız çağırıyor. Açık kalırsa üçüncü taraf bizim
-- E10/E11 keşfimizi kopyalayıp kendi toplu erişimini kurar.
--
-- ── TASARIM: neden ELLE kolon listesi DEĞİL ──────────────────────────────────
-- Kolon listesi elle yazılsaydı ve BİR kolon atlansaydı, giriş yapmış tüm
-- kullanıcılarda ilgili sorgu 42501 ile ölürdü (kısmî sonuç değil — TÜM sorgu).
-- Bunun yerine migration_anon_maske.sql'in dinamik deseni: information_schema'dan
-- "iki token DIŞINDAKİ her kolon" türetiliyor. Böylece kolon atlamak imkânsız.
--
-- anon'dan FARKI: `idare` burada GRANT ediliyor. İdare adı üyelere açık bir
-- özellik (dogrudan-temin.html/dt-detay.html'de uyeMi dalı onu seçiyor);
-- maskelenen yalnız misafirdir.
--
-- ── ÖNCE REVOKE, SONRA GRANT (sıra kritik) ───────────────────────────────────
-- Kolon-bazlı GRANT yetkiyi DARALTMAZ, EKLER. Tablo-geneli yetki durduğu sürece
-- kolon listesi tamamen dekoratiftir (bkz. migration_dt_anon_fix.sql:14-15 —
-- bu ders 3 nesnede delik açarak öğrenildi).
--
-- ── ETKİLENMEYENLER (denetlendi) ─────────────────────────────────────────────
--   • backend/dt_kazanan_scraper.py ve ekap_dogrudan_temin_scraper.py →
--     SUPABASE_SERVICE_KEY (service_role) kullanıyor; service_role kolon
--     yetkilerini aşar, ETKİLENMEZ.
--   • Token döndüren VIEW / MATERIALIZED VIEW / SECURITY DEFINER fonksiyon YOK
--     (tüm backend/*.sql tarandı). DT tarafındaki MV'ler — dt_kategori_sayim_mv,
--     dt_idare_ozet_mv, dt_il_sayim(_aktif) — yalnız sayım/özet döndürüyor.
--     Bu ÖNEMLİ: view'lar SAHİP yetkisiyle çalışır, taban tablodaki kolon maskesi
--     onlara uygulanmaz (ilanlar_sonuc olayı, bkz. migration_anon_maske_v2.sql).
--   • Frontend hiçbir yerde token select etmiyor (tüm .html/.js tarandı).
--
-- ── ⚠️ KALICI BAKIM NOTU ─────────────────────────────────────────────────────
-- Bu migration'dan sonra tabloya EKLENEN YENİ KOLONLAR ne anon'a ne authenticated'a
-- otomatik açılır (kolon-GRANT'lar yeni kolonlara genişlemez). Yeni kolon eklerken
-- bu dosyayı ve migration_anon_maske.sql'i TEKRAR çalıştırın, yoksa yeni kolonu
-- select eden sayfa 42501 alır.
--
-- Çalıştırma (VDS):
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_token_authenticated.sql
-- ============================================================================

BEGIN;

DO $$
DECLARE
  kolonlar   text;
  token_adet int;
BEGIN
  -- Güvenlik ağı: token kolonları gerçekten var mı? Yoksa bu migration konusuz
  -- kalır ve sessizce tüm tabloyu yeniden GRANT etmiş oluruz — o yüzden dur.
  SELECT count(*) INTO token_adet
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = 'dogrudan_temin_ilanlari'
    AND column_name IN ('dt_ihale_token', 'dt_idare_token');

  IF token_adet <> 2 THEN
    RAISE EXCEPTION 'ABORT: dt_ihale_token/dt_idare_token bulunamadi (bulunan: %). migration_dt_kazanan.sql uygulanmis mi?', token_adet;
  END IF;

  SELECT string_agg(quote_ident(column_name), ', ')
    INTO kolonlar
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = 'dogrudan_temin_ilanlari'
    AND column_name NOT IN ('dt_ihale_token', 'dt_idare_token');

  IF kolonlar IS NULL THEN
    RAISE EXCEPTION 'ABORT: kolon listesi bos cikti — tablo adi yanlis olabilir';
  END IF;

  -- SIRA: önce tablo-geneli yetkiyi al, sonra kolon listesini ver.
  --
  -- PUBLIC'ten de REVOKE ŞART: yetki PUBLIC üzerinden geliyorsa yalnız
  -- authenticated'dan almak HİÇBİR ŞEY yapmaz — rol yine PUBLIC'ten miras alır.
  -- (Aynı tuzak fonksiyonlarda yaşandı: migration_bulk_rpc_kilit.sql:13-14.)
  -- Zararsız: bu tabloda anon/authenticated/service_role'ün kendi açık yetkileri
  -- var, superuser'lar (postgres/supabase_admin) zaten yetki denetimini aşar.
  EXECUTE 'REVOKE SELECT ON public.dogrudan_temin_ilanlari FROM PUBLIC';
  EXECUTE 'REVOKE SELECT ON public.dogrudan_temin_ilanlari FROM authenticated';
  EXECUTE format('GRANT SELECT (%s) ON public.dogrudan_temin_ilanlari TO authenticated', kolonlar);

  RAISE NOTICE 'authenticated icin % kolon GRANT edildi (2 token haric)',
    (SELECT count(*) FROM information_schema.columns
      WHERE table_schema='public' AND table_name='dogrudan_temin_ilanlari'
        AND column_name NOT IN ('dt_ihale_token','dt_idare_token'));
END $$;

-- ── DOĞRULAMA: migration kendi kendini denetler, yanlışsa COMMIT ETMEZ ───────
-- has_column_privilege() rol değiştirmeden yetkiyi sorar; SET ROLE'dan temiz.
DO $$
BEGIN
  -- 1) Tokenlar authenticated'a KAPALI olmalı
  IF has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated hala dt_ihale_token okuyabiliyor';
  END IF;
  IF has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'dt_idare_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated hala dt_idare_token okuyabiliyor';
  END IF;

  -- 2) Sayfaların kullandığı kolonlar AÇIK kalmalı (yoksa canlı site kırılır)
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated idare okuyamiyor — uye ozelligi kirilir';
  END IF;
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'dt_no', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated dt_no okuyamiyor';
  END IF;
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'yayin_tarihi', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated yayin_tarihi okuyamiyor';
  END IF;

  -- 3) anon maskesi BOZULMAMIŞ olmalı — İKİ YÖNLÜ kontrol.
  --    Negatif yön (maske duruyor mu):
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon idare okuyabiliyor — maske delinmis';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon dt_ihale_token okuyabiliyor';
  END IF;
  --    Pozitif yön (misafir sayfası HÂLÂ çalışıyor mu): yukarıdaki
  --    "REVOKE ... FROM PUBLIC" anon'un erişimini de kesebilirdi. anon'un kendi
  --    kolon-GRANT'ları var (migration_anon_maske.sql) ama bunu VARSAYMIYORUZ —
  --    bu kontrol olmasaydı migration misafir sayfasını sessizce öldürebilirdi.
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_no', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'baslik', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'durum', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'il', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'tarih', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon temel kolonlari okuyamiyor — misafir sayfasi kirilir (PUBLIC REVOKE yan etkisi?)';
  END IF;

  -- 4) service_role dokunulmamış olmalı (scraper'lar buna bağlı)
  IF NOT has_column_privilege('service_role', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: service_role token okuyamiyor — dt_kazanan_scraper kirilir';
  END IF;

  RAISE NOTICE 'OK: tokenlar authenticated+anon a kapali, sayfa kolonlari acik, service_role saglam';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── GERİ ALMA (gerekirse) ────────────────────────────────────────────────────
-- Aşağıdaki tek satır eski (AÇIK) duruma döner. Yalnız acil durumda kullanın:
--   GRANT SELECT ON public.dogrudan_temin_ilanlari TO authenticated;
-- Not: kolon-GRANT'lar kalır ama tablo-geneli yetki onları gölgeler.

-- ── UYGULAMA SONRASI DIŞ DOĞRULAMA (curl — atlanmamalı) ──────────────────────
-- Bu projede kural: "deploy sonrası anon curl'süz doğrulama YOK".
-- SQL içi kontrol yetkiyi doğrular, PostgREST'in gerçek davranışını doğrulamaz.
--
-- A) anon ile token → 401/42501 BEKLENİR:
--   curl -s -o /dev/null -w "%{http_code}\n" \
--     "https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari?select=dt_no,dt_ihale_token&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
-- B) ÜYE token'ı ile token kolonu → 401/42501 BEKLENİR (asıl test, $UYE = giriş
--    yapmış bir kullanıcının access_token'ı; tarayıcıda localStorage.ihale_token):
--   curl -s "https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari?select=dt_no,dt_ihale_token&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $UYE"
--
-- C) ÜYE token'ı ile NORMAL kolonlar → 200 + idare dolu BEKLENİR:
--   curl -s "https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari?select=dt_no,baslik,idare&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $UYE"
--
-- D) Sayfa akışı: /dogrudan-temin üye olarak açılmalı, idare adları görünmeli;
--    misafir (gizli pencere) '***' görmeli. Konsolda 42501 OLMAMALI.
