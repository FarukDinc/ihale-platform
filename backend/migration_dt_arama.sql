-- =============================================================================
-- migration_dt_arama.sql — DT serbest metin aramasına Türkçe katlama + trigram
-- (Backlog #15, 20 Tem 2026)
-- =============================================================================
--
-- ── SORUN 1: İ/ı katlaması yok (sessiz sonuç kaybı) ──────────────────────────
-- dogrudan-temin.html ve dashboard.html DT aramayı ham ILIKE ile yapıyor.
-- PostgreSQL lower() bu veritabanının kolasyonunda Türkçe 'ı'yı 'i'ye ÇEVİRMEZ →
-- kullanıcı klavyeden "kirtasiye" yazınca "kırtasiye" başlıklı ilanlar DÜŞER.
-- Hata değil, SESSİZ eksik sonuç: kullanıcı "böyle bir ilan yok" sanır.
--
-- CANLI KANIT (20 Tem, anon key, /rest/v1 — bu migration ÖNCESİ):
--   ?dt_no=eq.26DT350368&baslik=ilike.*kirtasiye*  -> []            ← KAYIP
--   ?dt_no=eq.26DT350368&baslik=ilike.*rtasiye*    -> [26DT350368]  ← satır orada
--   (26DT350368 başlığı: "kırtasiye malzemesi alımı")
--   NOT: ASCII 'I' zaten 'i'ye iniyor (*kirtasiye* -> "KIRTASIYE" eşleşiyor);
--   kaybolan yalnız Türkçe ı/İ/ş/ğ/ü/ö/ç içeren yazımlar. Bu yüzden arama
--   "kısmen çalışıyor" görünüyor ve hata bugüne kadar fark edilmedi.
--
-- ── SORUN 2: baslik'te trigram indeksi yok (seq-scan) ────────────────────────
-- 1,48M satırda `baslik ILIKE '%x%'` indekslenemiyor → tam tarama. Sayfa bunu
-- bildiği için arama varken sekme sayaçlarını KAPATIYOR (sayimYapilabilirMi:
-- "aramaVar -> return false"), yani hata zaten bir özelliği devre dışı bırakmış
-- durumda. Liste sorgusu da ~3sn statement_timeout kenarında.
--
-- ── ÇÖZÜM: ilanlar tarafındaki desenin BİREBİR aynısı ────────────────────────
-- migration_ilanlar_arama_fold.sql: tr_fold() IMMUTABLE fonksiyonu + katlanmış
-- generated STORED kolon + pg_trgm GIN indeks; frontend arama terimini JS
-- trFold() ile aynı normal forma indirip katlanmış kolonda ILIKE ediyor.
-- Burada da aynısı, iki kolonla (nedeni aşağıda).
--
-- ── NEDEN İKİ KOLON (maskeleme zorunluluğu) ─────────────────────────────────
-- ilanlar.arama_fold anon'a KAPALI, çünkü içinde idare geçiyor
-- (migration_anon_maske.sql:8 — "arama_fold (içinde idare geçer!)"). DT'de de
-- idare misafire kapalı, dolayısıyla idare içeren tek bir kolon misafire
-- verilemez: verilirse maskelenmiş idare adı trigram aramasıyla harf harf geri
-- okunabilir (oracle saldırısı) — maskeyi tümden delen bir sızıntı olurdu.
--
--   arama_fold  = tr_fold(baslik || ' ' || idare)   → YALNIZ authenticated
--                 (üye araması `.or(baslik.ilike,idare.ilike)` ile tam parite)
--   baslik_fold = tr_fold(baslik)                    → anon + authenticated
--                 (baslik zaten anon'a AÇIK; ek ifşa YOK, misafir araması da
--                  böylece Türkçe katlar — ilanlar'da misafir hâlâ katlamıyor,
--                  orada baslik/idare aynı kolonda olduğu için çare yoktu)
--
-- Tek alanlık fold kolonunun emsali: migration_ihale_sonuclari_arama_fold.sql
-- (kazanan_firma_fold). idx_ilanlar_baslik_fold_trgm ise ifade indeksi olarak
-- var (migration_uygun_firmalar_v3_1.sql) ama PostgREST WHERE'de fonksiyon
-- çağıramaz → misafirin kullanabilmesi için kolon olması ŞART.
--
-- ── KAPSAM DIŞI (bilinçli, bilinen açık) ────────────────────────────────────
-- Detaylı arama panelindeki "İdare" alanı (dogrudan-temin.html f-dt-idare, yalnız
-- üye) hâlâ ham `idare ILIKE` kullanıyor → orada Türkçe katlama YOK ve indeks YOK.
-- Kapatmak için üçüncü bir kolon (idare_fold) + üçüncü bir GIN indeks gerekirdi;
-- 1,48M satırda maliyeti, tek bir üye-alanı için haklı çıkarmıyor. Serbest metin
-- araması (asıl şikâyet) arama_fold üzerinden idare'yi ZATEN kapsıyor.
-- ⚠️ Bir gün idare_fold eklenirse: saf idare kopyası olduğu için arama_fold ile
-- AYNI muameleyi görmeli — migration_anon_maske.sql'deki `anon_yasak` listesine
-- girmeli (bekçi zaten sınıflandırmadan geçmesine izin vermez).
--
-- ── ⚠️ YENİ KOLON = ANON GRANT ŞART ─────────────────────────────────────────
-- DT tablosunda anon DA authenticated DA kolon-bazlı yetkiyle okuyor
-- (migration_anon_maske.sql:98-137 ve migration_dt_token_authenticated.sql).
-- Kolon-GRANT'lar SONRADAN eklenen kolonlara GENİŞLEMEZ → yeni kolon açıkça
-- GRANT edilmezse onu select/WHERE eden sayfa 42501 ile TÜMDEN ölür. Bu tuzağa
-- bu projede 3 kez düşüldü (bkz. migration_dt_yayin_tarihi.sql:36,
-- migration_idare_tur_anon_grant.sql). Aşağıdaki DO bloğu yetkileri hem verir
-- hem DOĞRULAR; yanlışsa COMMIT ETMEZ.
--
-- ── ⛔ TERS YÖN: migration_anon_maske.sql AYNI COMMIT'TE DEĞİŞTİRİLDİ ────────
-- Yukarıdaki tuzağın simetriği, ondan daha sinsi. migration_anon_maske.sql'in DT
-- bloğu (tek tablo olarak) KARA liste kullanıyor: "şu kolonlar HARİÇ hepsini
-- anon'a GRANT et". arama_fold o listeye eklenmeseydi, yalnızca burada anon'a
-- GRANT etmemek YETMEZDİ — maske dosyası bir sonraki koşusunda arama_fold'u
-- anon'a KENDİLİĞİNDEN açardı ve iki-kolonlu bu tasarımın tek varlık sebebi
-- (idare'nin trigram oracle'ıyla harf harf okunamaması) buharlaşırdı. Üstelik
-- migration_dt_token_authenticated.sql:45-49 yeni kolon eklerken o dosyayı
-- TEKRAR çalıştırmayı emrediyor → yordamı doğru izleyen kişi maskeyi delerdi.
-- Aşağıdaki ADIM 1 doğrulaması bunu YAKALAMAZ; başka dosyanın koşusunda ihlal
-- sessiz kalır (hafıza: anon-maske-iki-kok-neden, kök neden A/C).
-- Bu yüzden migration_anon_maske.sql'de İKİ değişiklik yapıldı ve iki dosya
-- birlikte taşınmalıdır:
--   1) arama_fold kara listeye eklendi (baslik_fold bilinçli olarak anon'a açık),
--   2) sınıflandırılmamış her `*_fold` kolonunda migration'ı durduran bekçi +
--      kendi kontrol bölümünde arama_fold negatif testi eklendi — böylece
--      gelecekteki bir fold kolonu (örn. aşağıda anılan idare_fold) sessizce
--      değil, GÜRÜLTÜYLE arızalanır.
--
-- ── ⏱ MALİYET / KİLİT DAVRANIŞI (1.489.878 satır) ───────────────────────────
-- ADIM 1 — ALTER TABLE ... ADD COLUMN ... GENERATED ... STORED:
--   • Tabloyu TAMAMEN YENİDEN YAZAR ve ACCESS EXCLUSIVE kilidi rewrite'ın
--     TAMAMI boyunca tutar (kısa metadata kilidi DEĞİL — migration_dt_kategori.sql'
--     deki NULLable kolonla karıştırmayın, o milisaniyelikti).
--   • Tahmin: ~3-8 dakika. Bu süre boyunca DT'ye dokunan HER sorgu bekler →
--     /dogrudan-temin, /dt-detay, dashboard DT modu ve harita DT katmanı
--     pratikte 502/timeout verir. GÜNDÜZ + DÜŞÜK TRAFİKTE koşun.
--   • Gece 02:00 UTC scraper turuyla ÇAKIŞTIRMAYIN: rewrite sırasında upsert
--     bekler, scraper'ın kendi timeout'una takılıp turu yarım bırakabilir.
--   • İki kolon TEK ALTER içinde ekleniyor — bilinçli: ayrı ayrı yazılsaydı
--     tablo İKİ KEZ yeniden yazılırdı (kilit süresi iki katı).
--   • Disk: rewrite sırasında tablonun eski + yeni kopyası aynı anda durur →
--     geçici olarak tablo boyutu kadar EK boş alan gerekir.
--   • Kalıcı büyüme tahmini: baslik ort. 53 bayt (400 satırlık canlı örneklem),
--     idare ort. ~60 bayt varsayımıyla baslik_fold ~75 MB, arama_fold ~165 MB.
--
-- ADIM 3 — CREATE INDEX CONCURRENTLY (transaction DIŞINDA, bilinçli):
--   • CONCURRENTLY transaction bloğu içinde çalışmaz (25001). Bu yüzden
--     BEGIN/COMMIT bloklarından SONRA, çıplak duruyorlar.
--   • Karşılığında tabloyu yazmaya kapatmazlar; scraper koşarken bile güvenli.
--   • Tahmin: GIN trigram, kolon başına ~8-20 dk (CONCURRENTLY iki geçiş yapar).
--     Takılmadı, sabırlı olun. Toplam indeks boyutu ~0,8-1,2 GB bekleniyor.
--   • Hızlandırmak isterseniz indeksleri kurmadan ÖNCE (aynı psql oturumunda):
--       SET maintenance_work_mem = '512MB';
--     VDS RAM'ine göre ayarlayın; emin değilseniz dokunmayın.
--
-- ── İdempotent ───────────────────────────────────────────────────────────────
-- IF NOT EXISTS / CREATE OR REPLACE. Tekrar çalıştırmak zararsız; ikinci koşuda
-- ADIM 1 tabloyu yeniden YAZMAZ (kolonlar zaten var).
--
-- ── tr_fold() DEĞİŞTİRİLMEDİ ────────────────────────────────────────────────
-- Aşağıdaki CREATE OR REPLACE, migration_ilanlar_arama_fold.sql'deki gövdenin
-- BAYT BAYT aynısıdır — bu dosya tek başına da çalışabilsin diye var.
-- ⛔ Gövdesini ASLA değiştirmeyin: tr_fold() aynı zamanda idare-türü
-- eşleştirmesinin JOIN ANAHTARI (hafıza: idare-tur-siniflandirici); bir bayt
-- oynarsa `tazele` sessizce 0 satır eşleştirir.
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_arama.sql
--
-- İlgili hafıza: ilike-tr-locale-tuzagi, anon-maske-iki-kok-neden,
--                statement-timeout-edge, veri-disa-aktarim-yasagi
-- =============================================================================


-- ── ADIM 0: trigram eklentisi (leading-wildcard %x% ILIKE indekslenebilsin) ──
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- tr_fold() — frontend trFold() ile BİREBİR. Zaten prod'da var; idempotent güvence.
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


-- =============================================================================
-- ADIM 1: katlanmış kolonlar + yetkiler  (TEK transaction, TEK tablo rewrite)
-- =============================================================================
BEGIN;

-- lock_timeout: ACCESS EXCLUSIVE kuyruğa girerken uzun süren bir okuyucunun
-- arkasında beklerken TÜM yeni okumaları da bloklamayalım. Zaman aşımında
-- migration temiz düşer, düşük trafikte tekrar denenir (migration_dt_kategori.sql
-- deseni). NOT: bu yalnız kilidi ALMA süresini sınırlar, rewrite'ın kendisini DEĞİL.
SET LOCAL lock_timeout = '10s';

-- Rewrite dakikalar sürer; oturumda dar bir statement_timeout varsa migration
-- yarıda ölür. 0 = sınırsız, yalnız BU transaction için.
SET LOCAL statement_timeout = 0;

-- İki kolon TEK ifadede → tablo yalnız BİR kez yeniden yazılır.
ALTER TABLE public.dogrudan_temin_ilanlari
  ADD COLUMN IF NOT EXISTS baslik_fold text
    GENERATED ALWAYS AS (tr_fold(coalesce(baslik, ''))) STORED,
  ADD COLUMN IF NOT EXISTS arama_fold text
    GENERATED ALWAYS AS (
      tr_fold(coalesce(baslik, '') || ' ' || coalesce(idare, ''))
    ) STORED;

-- ── Yetkiler ────────────────────────────────────────────────────────────────
-- baslik_fold: misafire AÇIK. baslik zaten anon'a açık olduğundan ek ifşa yok.
GRANT SELECT (baslik_fold) ON public.dogrudan_temin_ilanlari TO anon;
GRANT SELECT (baslik_fold) ON public.dogrudan_temin_ilanlari TO authenticated;

-- arama_fold: SADECE üyeye. anon'a GRANT YOK — içinde idare geçiyor
-- (ilanlar.arama_fold ile aynı gerekçe). Buraya "anon" eklemek maskeyi deler.
GRANT SELECT (arama_fold) ON public.dogrudan_temin_ilanlari TO authenticated;

-- service_role kolon yetkilerini aşar (superuser-benzeri BYPASSRLS + tablo geneli),
-- ayrıca GRANT gerekmez; generated kolonlara zaten YAZILAMAZ (scraper upsert'i
-- bu kolonlara dokunmaz, PGRST204 riski yok).

-- ── DOĞRULAMA: yanlışsa COMMIT ETME ─────────────────────────────────────────
-- has_column_privilege() rol değiştirmeden yetkiyi sorar (SET ROLE'dan temiz).
DO $$
BEGIN
  -- 1) Yeni kolonlar gerçekten oluştu mu?
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='dogrudan_temin_ilanlari'
                    AND column_name='baslik_fold') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: baslik_fold kolonu olusmadi';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='dogrudan_temin_ilanlari'
                    AND column_name='arama_fold') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: arama_fold kolonu olusmadi';
  END IF;

  -- 2) POZİTİF: misafir baslik_fold okuyabilmeli — yoksa /dogrudan-temin ve
  --    dashboard DT araması misafirde 42501 ile TÜMDEN ölür (3 kez yasandi).
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'baslik_fold', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon baslik_fold okuyamiyor — misafir aramasi 42501 alir';
  END IF;
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'baslik_fold', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated baslik_fold okuyamiyor';
  END IF;
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'arama_fold', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated arama_fold okuyamiyor — uye aramasi kirilir';
  END IF;

  -- 3) NEGATİF: arama_fold içinde idare geçiyor → anon'a ASLA açılmamalı.
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'arama_fold', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon arama_fold okuyabiliyor — idare maskesi DELINDI';
  END IF;

  -- 4) Mevcut maske bozulmamış olmalı (bu migration ona dokunmadı, yine de kontrol)
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon idare okuyabiliyor — maske delinmis';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT')
     OR has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: dt_ihale_token acilmis — migration_dt_token_authenticated.sql geri mi alindi?';
  END IF;

  -- 5) Misafir sayfasının temel kolonları hâlâ açık mı
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'baslik', 'SELECT')
     OR NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_no', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon temel kolonlari okuyamiyor — misafir sayfasi kirilir';
  END IF;

  RAISE NOTICE 'OK: baslik_fold anon+uye acik, arama_fold yalniz uye, idare/token maskesi saglam';
END $$;

COMMIT;

-- PostgREST yeni kolonları görsün (yoksa 42703 "column does not exist")
NOTIFY pgrst, 'reload schema';


-- =============================================================================
-- ADIM 2: dogrudan_temin_hiyerarsi(p_kok) RPC'sini yeni kolonlarla tazele
-- =============================================================================
-- ZORUNLU — atlanırsa "kurum hiyerarşi filtresi AÇIK + arama yapan ÜYE" hâlinde
-- sorgu 42703 ile düşer. Sebep: bu RPC'nin döndürdüğü kolon listesi, kurulduğu
-- ANIN fotoğrafıdır (migration_hiyerarsifiltre.sql:131-133 bunu kalıcı bakım
-- notu olarak yazmış: "DT tablosuna yeni kolon eklenirse bu dosya YENİDEN
-- çalıştırılmalı"). Kurum filtresi aktifken taban tablo değil bu RPC sorgulanır,
-- yani arama arama_fold'a taşındığı anda RPC de o kolonu döndürmek zorunda.
--
-- Kolon listesi ELLE YAZILMIYOR: migration_hiyerarsifiltre.sql'deki dinamik
-- desenin aynısı — "authenticated'ın okuyabildiği her kolon" pg_attribute'dan
-- türetiliyor, yani GRANT'in birebir aynası. Böylece kolon atlamak imkânsız.
-- (Bu, migration_hiyerarsifiltre.sql'i DEĞİŞTİRMEZ; onu yeniden koşmaya da gerek
-- kalmasın diye fonksiyon burada aynı tanımla yeniden kuruluyor.)
BEGIN;
SET LOCAL statement_timeout = 0;

DROP FUNCTION IF EXISTS public.dogrudan_temin_hiyerarsi(text);
DO $dt$
DECLARE
  kolon_tanim text;   -- "id uuid, dt_no text, ..."
  kolon_secim text;   -- "d.id, d.dt_no, ..."
BEGIN
  SELECT string_agg(quote_ident(a.attname) || ' ' || format_type(a.atttypid, a.atttypmod), ', ' ORDER BY a.attnum),
         string_agg('d.' || quote_ident(a.attname), ', ' ORDER BY a.attnum)
    INTO kolon_tanim, kolon_secim
    FROM pg_attribute a
   WHERE a.attrelid = 'public.dogrudan_temin_ilanlari'::regclass
     AND a.attnum > 0 AND NOT a.attisdropped
     AND has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', a.attname, 'SELECT');

  IF kolon_tanim IS NULL THEN
    RAISE EXCEPTION 'ABORT: authenticated icin secilebilir DT kolonu bulunamadi — grant durumu bozuk olabilir';
  END IF;
  -- Güvenlik ağı: tokenlar listeye sızdıysa (grant geri açılmışsa) burada dur.
  IF kolon_secim LIKE '%dt_ihale_token%' OR kolon_secim LIKE '%dt_idare_token%' THEN
    RAISE EXCEPTION 'ABORT: token kolonlari listeye sizdi — migration_dt_token_authenticated.sql geri mi alindi?';
  END IF;
  -- Bu migration'ın asıl amacı: arama_fold listede OLMALI.
  IF kolon_secim NOT LIKE '%arama_fold%' THEN
    RAISE EXCEPTION 'ABORT: arama_fold RPC kolon listesine girmedi — ADIM 1 grantlari uygulanmis mi?';
  END IF;

  EXECUTE format($f$
    CREATE FUNCTION public.dogrudan_temin_hiyerarsi(p_kok text)
    RETURNS TABLE (%s)
    LANGUAGE sql STABLE
    AS $fn$
      SELECT %s
        FROM public.dogrudan_temin_ilanlari d
       WHERE d.detsis_no IN (SELECT at.torun_no
                               FROM public.idare_ata_torun at
                              WHERE at.ata_no = p_kok)
    $fn$
  $f$, kolon_tanim, kolon_secim);
END $dt$;

-- Fonksiyonlar PUBLIC EXECUTE ile DOĞAR → DROP+CREATE eski REVOKE'u sıfırladı,
-- yeniden yazmak ŞART (migration_hiyerarsifiltre.sql:191-196 ile aynı).
REVOKE EXECUTE ON FUNCTION public.dogrudan_temin_hiyerarsi(text) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.dogrudan_temin_hiyerarsi(text) TO authenticated, service_role;

DO $$
BEGIN
  IF has_function_privilege('anon', 'public.dogrudan_temin_hiyerarsi(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon dogrudan_temin_hiyerarsi calistirabiliyor (idare adi sizar)';
  END IF;
  IF NOT has_function_privilege('authenticated', 'public.dogrudan_temin_hiyerarsi(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated RPC calistiramiyor — kurum filtresi kirilir';
  END IF;
  IF pg_get_functiondef('public.dogrudan_temin_hiyerarsi(text)'::regprocedure) LIKE '%dt_ihale_token%'
     OR pg_get_functiondef('public.dogrudan_temin_hiyerarsi(text)'::regprocedure) LIKE '%dt_idare_token%' THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: RPC tanimi token kolonu iceriyor';
  END IF;
  RAISE NOTICE 'OK: dogrudan_temin_hiyerarsi arama_fold ile yeniden kuruldu, anon a kapali';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';


-- =============================================================================
-- ADIM 3: trigram GIN indeksleri  — TRANSACTION DIŞINDA (CONCURRENTLY)
-- =============================================================================
-- !! Buradan aşağısı BİLİNÇLİ olarak BEGIN/COMMIT dışında.
--    CREATE INDEX CONCURRENTLY transaction bloğunda 25001 hatası verir.
--    Karşılığında tabloyu yazmaya kapatmaz (migration_dt_index.sql ile aynı desen).
--    Süre tahmini ve INVALID indeks kontrolü için dosya başındaki ⏱ bölümüne bakın.

-- Misafir + üye ortak yolu (baslik araması)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_baslik_fold_trgm
  ON public.dogrudan_temin_ilanlari USING gin (baslik_fold gin_trgm_ops);

-- Üye yolu (baslik + idare birleşik araması)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_arama_fold_trgm
  ON public.dogrudan_temin_ilanlari USING gin (arama_fold gin_trgm_ops);

-- Planlayıcı yeni kolon/indeks istatistiklerini görsün
ANALYZE public.dogrudan_temin_ilanlari;


-- =============================================================================
-- DOĞRULAMA — uygulamadan SONRA
-- =============================================================================
--
-- A) İndeksler geçerli mi? (CONCURRENTLY başarısız olursa INVALID kalır ve
--    sorguda KULLANILMAZ — sessizce eski yavaşlığa dönersiniz.)
--   SELECT c.relname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
--    WHERE NOT i.indisvalid;
--   Çıkan olursa: DROP INDEX CONCURRENTLY <ad>;  sonra ADIM 3'ü tekrar çalıştırın.
--
-- B) Katlama doğru mu (SQL):
--   SELECT count(*) FROM public.dogrudan_temin_ilanlari WHERE baslik_fold LIKE '%kirtasiye%';
--   -- ham `baslik ILIKE '%kirtasiye%'` sayısından BELİRGİN ŞEKİLDE BÜYÜK olmalı
--   SELECT baslik, baslik_fold FROM public.dogrudan_temin_ilanlari
--    WHERE dt_no = '26DT350368';   -- baslik_fold = 'kirtasiye malzemesi alimi'
--
-- C) İndeks gerçekten kullanılıyor mu:
--   EXPLAIN (ANALYZE, BUFFERS)
--   SELECT dt_no FROM public.dogrudan_temin_ilanlari
--    WHERE baslik_fold LIKE '%kirtasiye%' ORDER BY tarih DESC LIMIT 25;
--   Beklenen: "Bitmap Index Scan on idx_dt_ilanlari_baslik_fold_trgm".
--   "Seq Scan" görürseniz indeks INVALID ya da ANALYZE koşmamış demektir.
--   NOT: 3 KARAKTERDEN KISA terimde trigram indeksi KULLANILAMAZ (seq-scan'e
--   döner) — bu bir hata değil, pg_trgm'in doğası. Frontend 3 karakter altı
--   aramalarda da eskisi gibi yavaş kalır.
--
-- D) anon curl doğrulaması — ATLANMAZ ("deploy sonrası anon curl'süz doğrulama YOK"):
--   ANON=<js/api.js içindeki anon key>
--   B=https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari
--
--   D1) Misafir baslik_fold okuyabilmeli → 200 + DOLU gövde beklenir:
--     curl -s "$B?select=dt_no,baslik_fold&limit=1" -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
--   D2) Misafir katlanmış arama ÇALIŞMALI → 26DT350368 DÖNMELİ (öncesi: []):
--     curl -s "$B?select=dt_no&dt_no=eq.26DT350368&baslik_fold=ilike.*kirtasiye*" \
--       -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
--   D3) Misafir arama_fold'u GÖREMEMELİ → 401/42501 beklenir (SELECT'te):
--     curl -s "$B?select=arama_fold&limit=1" -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
--   D4) Misafir arama_fold'u WHERE'de de KULLANAMAMALI → 401/42501 beklenir.
--       Bu ayrı bir test: WHERE de SELECT yetkisi ister; açık kalsaydı maskelenmiş
--       idare adı harf harf tahmin edilebilirdi (oracle).
--     curl -s "$B?select=dt_no&arama_fold=ilike.*ankara*&limit=1" \
--       -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
--   ⚠️ D3/D4'te "200 + boş dizi" YETERLİ DEĞİL — gövdeye bakın. 200+[] RLS'in
--   kurtardığı anlamına gelir, yetki yine de fazladır (hafıza: http-200-ifsa-degil).
--
--   D5) ÜYE token'ıyla ($UYE = giriş yapmış kullanıcının access_token'ı) → 200 dolu:
--     curl -s "$B?select=dt_no,arama_fold&limit=1" -H "apikey: $ANON" -H "Authorization: Bearer $UYE"
--
-- E) Sayfa akışı: /dogrudan-temin misafir (gizli pencere) → "kirtasiye" araması
--    "kırtasiye" başlıklı ilanları GETİRMELİ, konsolda 42501/42703 OLMAMALI.
--    Üye olarak → aynı arama idare adında geçenleri de getirmeli.
--    Kurum hiyerarşi filtresi + arama birlikte (üye) → 42703 OLMAMALI (ADIM 2).
--
-- =============================================================================
-- GERİ ALMA (acil durum)
-- =============================================================================
--   DROP INDEX CONCURRENTLY IF EXISTS public.idx_dt_ilanlari_arama_fold_trgm;
--   DROP INDEX CONCURRENTLY IF EXISTS public.idx_dt_ilanlari_baslik_fold_trgm;
--   ALTER TABLE public.dogrudan_temin_ilanlari DROP COLUMN IF EXISTS arama_fold;
--   ALTER TABLE public.dogrudan_temin_ilanlari DROP COLUMN IF EXISTS baslik_fold;
--   -- ardından ADIM 2'yi tekrar çalıştırın (RPC kolon listesi bayat kalır) ve
--   -- NOTIFY pgrst, 'reload schema';
--   -- Frontend zaten 42703'te eski ILIKE aramasına düşüyor (foldKolonVar bayrağı),
--   -- yani sayfa geri alma sırasında da çalışmaya devam eder.
