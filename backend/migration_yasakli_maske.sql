-- =============================================================================
-- YASAKLI FİRMALAR — anon maskesi + scraper'ın çalışması için şema ön koşulu
-- 29 Tem 2026 · backend/yasakli_scraper.py ile birlikte gelir
-- =============================================================================
-- UYGULANMADI — bu dosya yazıldı, koşulmadı. Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_yasakli_maske.sql
--
-- ⚠️ Bu dosyanın İKİ işi var ve ikisi de yasakli_scraper.py çalışmadan ÖNCE
-- yapılmak zorunda; o yüzden tek transaction'da duruyorlar:
--   BÖLÜM A — ŞEMA: karar_no + PostgREST'in çıkarabileceği doğal-anahtar indeksi
--                    + arama_fold + normalize_ad tetikleyicisi
--   BÖLÜM B — YETKİ: anon'dan REVOKE, authenticated'a DAR kolon GRANT'ı
--   BÖLÜM C — DOĞRULAMA: maskeyi ve misafir dalını SET ROLE ile sınar
--
-- =============================================================================
-- KOLON ADLARI TAHMİN DEĞİL — PostgREST ile CANLIDA ÖLÇÜLDÜ (29 Tem 2026)
-- =============================================================================
-- Yöntem: anon anahtarıyla `?select=<kolon>&limit=1`.
--   42501 (permission denied) = kolon VAR, anon'a kapalı
--   42703 (does not exist)    = kolon YOK
--
--   VAR  : id · firma_ad · normalize_ad · karar_veren_kurum · yasak_baslangic ·
--          yasak_bitis · yasak_suresi · tc_vergi_no · kanun_madde · uyruk · il ·
--          kaynak · resmi_gazete_tarih · aktif · olusturulma · guncellenme
--   YOK  : karar_no (42703) · arama_fold (42703) · kapsam (42703) ·
--          ham_json / ham_veri / kaynak_url / sicil_no (42703)
--
--   Tablonun TAMAMI anon'a kapalı (42501 her kolonda) — yani BUGÜN maske
--   YÖNÜNDEN delik YOK. Bu dosya deliği kapatmıyor, deliği AÇILAMAZ hale
--   getiriyor: aşağıda eklenen YENİ kolonlar (karar_no, arama_fold) varsayılan
--   ayrıcalıkla doğup anon'a açılmasın diye önce REVOKE ediliyor
--   (hafıza: anon-maske-iki-kok-neden, kök neden A ve C).
--
-- =============================================================================
-- ⛔ CANLIDA BULUNAN GERÇEK DELİK: FONKSİYONLARDA VARSAYILAN PUBLIC EXECUTE
-- =============================================================================
-- Ölçüm (anon anahtarıyla POST /rest/v1/rpc/yasakli_listesi, gövde {}):
--     {"code":"42501", ... "permission denied for table yasakli_firmalar"}
-- Dikkat: hata TABLO'dan geldi, EXECUTE'tan DEĞİL. Yani anon fonksiyonu
-- ÇALIŞTIRABİLİYOR; onu durduran tek şey tablo yetkisi. Sebep: PostgreSQL yeni
-- fonksiyonlara varsayılan olarak PUBLIC'e EXECUTE verir ve
-- migration_yasakli_firmalar.sql yalnız GRANT yazmış, REVOKE yazmamış.
-- Bugün zararsız; ama biri "misafir de görsün" diye tabloya anon GRANT verdiği
-- gün yasakli_listesi 50'şer satırlık BULK dökümü anon'a açar
-- (hafıza: veri-disa-aktarim-yasagi — toplu RPC'ler login'li). Aşağıda kapatılıyor.
--
-- =============================================================================
-- v1-yasakli.html MİSAFİR DALI — anon'a HİÇBİR GRANT GEREKMİYOR
-- =============================================================================
-- Sayfa okundu (satır satır doğrulandı, tahmin değil):
--   · satır 91  : `if(!uyeMi){ alert('… üyelere özeldir. Giriş yapın.'); return; }`
--                 → misafir sorgusu DB'ye HİÇ ULAŞMIYOR, sorgula() erken dönüyor.
--   · satır 125 : `if(uyeMi){ const {count}=await sb.from('yasakli_firmalar')… }`
--                 → "veri var mı" sayımı da ÜYE dalının içinde.
--   · misafirin yaptığı tek çağrı `sb.auth.getSession()` — tabloya dokunmuyor.
-- SONUÇ: misafir dalının çalışması için gereken GRANT listesi = BOŞ KÜME.
-- Aşağıda anon'a bilerek HİÇBİR ŞEY verilmiyor ve BÖLÜM C bunu sınıyor.
-- ⚠️ Sayfa ileride misafire "toplam kaç yasaklı var" gibi bir sayaç gösterecekse
-- bu, tabloya anon GRANT'ı ile DEĞİL, SECURITY DEFINER bir sayaç RPC'si ile
-- yapılmalı (tek sayı döner, satır dökmez).
--
-- =============================================================================
-- ⛔ AYRI BİR HATA — BU DOSYA ÇÖZMEZ, SAYFA DEĞİŞİKLİĞİ GEREKİR
-- =============================================================================
-- v1-yasakli.html:97  `s.ilike('normalize_ad','%'+trFold(q)+'%')`
-- Canlıda ölçüldü (RPC ile):
--     normalize_firma('AKÇA İNŞAAT SANAYİ VE TİCARET ANONİM ŞİRKETİ') → 'AKÇA'
--     normalize_firma('2C BİLGİ TEKNOLOJİLERİ LİMİTED ŞİRKETİ')       → '2C BİLGİ TEKNOLOJİLERİ'
--     tr_fold('AKÇA İNŞAAT SANAYİ…')                                  → 'akca insaat sanayi…'
-- normalize_ad BÜYÜK harfli ve ŞAPKALI harfleri KORUYOR; sayfanın trFold'u ise
-- küçük+katlanmış üretiyor → ILIKE '%akca%' ile 'AKÇA' EŞLEŞMEZ (Ç ≠ c).
-- Yani veri yüklendikten sonra kullanıcı "akça" arayınca sayfa
-- "✅ yasaklılık kaydı bulunamadı" der: YASAKLI FİRMA İÇİN TEMİZ RAPORU.
-- Bir yasaklılık ekranında bu, hatanın EN KÖTÜ biçimidir.
--
-- Tersini yapmak (normalize_ad'ı tr_fold'la doldurmak) da kırıktır:
-- firma_yasakli_mi() `normalize_ad = normalize_firma(p_firma)` ile eşliyor ve
-- yukleniciler join'i de normalize_ad üzerinden — o sözleşme bozulur.
--
-- ÇÖZÜM (yukleniciler tablosundaki ikili deseni birebir kopyalıyoruz; orada da
-- normalize_ad + arama_fold YAN YANA duruyor ve ikisi de canlıda mevcut — REST
-- ile doğrulandı): normalize_ad DEĞİŞMİYOR, ayrıca arama_fold ekleniyor.
--   ⇒ ZORUNLU TAKİP İŞİ: v1-yasakli.html:97'de
--        .ilike('normalize_ad', …)   →   .ilike('arama_fold', …)
--      ve satır 96'daki select'e arama_fold'a gerek YOK (yalnız filtre).
--      CSS/JS cache yüzünden ?v bump ŞART (hafıza: cloudflare-cache-v-bump).
--   ⇒ İKİNCİ TAKİP İŞİ: satır 95-97'deki sayısal dal `.eq('tc_vergi_no', q)`
--      bu kaynakla HER ZAMAN boş döner (uç TC/VKN VERMİYOR). Ya kapatılmalı ya
--      da kullanıcıya "vergi/TC ile sorgulama henüz desteklenmiyor" denmeli;
--      şu hâliyle "bulunamadı" diyerek YANLIŞ GÜVEN veriyor.
-- =============================================================================


BEGIN;

SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = 0;

-- ── ÖN KOŞUL GUARD'LARI (yer tutucu/eksik ortamda yıkım yapmasın) ───────────
DO $$
DECLARE n bigint;
BEGIN
  IF to_regclass('public.yasakli_firmalar') IS NULL THEN
    RAISE EXCEPTION 'ABORT: public.yasakli_firmalar YOK — önce migration_yasakli_firmalar.sql uygulayın';
  END IF;
  -- to_regprocedure (to_regproc DEĞİL): argüman tipli imzayı yalnız bu kabul eder.
  IF to_regprocedure('public.tr_fold(text)') IS NULL THEN
    RAISE EXCEPTION 'ABORT: tr_fold(text) YOK — migration_idare_tur_fix.sql / migration_dt_arama.sql uygulanmamış';
  END IF;
  IF to_regprocedure('public.normalize_firma(text)') IS NULL THEN
    RAISE EXCEPTION 'ABORT: normalize_firma(text) YOK — firma normalizasyon migration''ı uygulanmamış';
  END IF;
  SELECT count(*) INTO n FROM public.yasakli_firmalar;
  RAISE NOTICE 'yasakli_firmalar mevcut satır sayısı: %', n;
END $$;


-- =============================================================================
-- BÖLÜM A — ŞEMA ÖN KOŞULU (scraper bunlar olmadan YAZAMAZ)
-- =============================================================================

-- A.1 karar_no — yanıttaki `nosu` (yasaklama karar no, ör. 117212). Canlıda YOK (42703).
-- NOT NULL DEFAULT '': doğal-anahtar indeksine gireceği için NULL olamaz; NULL'lu
-- unique indekste NULL'lar birbiriyle ÇAKIŞMAZ ve dedup sessizce çalışmaz olurdu.
ALTER TABLE public.yasakli_firmalar
  ADD COLUMN IF NOT EXISTS karar_no text;
UPDATE public.yasakli_firmalar SET karar_no = '' WHERE karar_no IS NULL;
ALTER TABLE public.yasakli_firmalar
  ALTER COLUMN karar_no SET DEFAULT '',
  ALTER COLUMN karar_no SET NOT NULL;

-- A.2 kaynak — zaten var ama NULLABLE; anahtarın parçası olacağı için sıkılaştırılıyor.
UPDATE public.yasakli_firmalar SET kaynak = 'ekap' WHERE kaynak IS NULL;
ALTER TABLE public.yasakli_firmalar
  ALTER COLUMN kaynak SET DEFAULT 'ekap',
  ALTER COLUMN kaynak SET NOT NULL;

-- A.3 DOĞAL ANAHTAR — PostgREST'in ÇIKARABİLECEĞİ düz-kolon unique indeksi
--
-- ⛔ NEDEN MEVCUT İNDEKS YETMİYOR: ux_yasakli_dedup bir İFADE içeriyor —
--      (firma_ad, yasak_baslangic, COALESCE(karar_veren_kurum,''))
--    PostgREST'in `on_conflict=` parametresi yalnız DÜZ kolon adları üretir
--    (`ON CONFLICT (a,b,c)`), COALESCE'lı indeksi çıkaramaz → upsert 42P10
--    ("no unique or exclusion constraint matching the ON CONFLICT specification")
--    ile patlar. Yani scraper hiç yazamaz.
--
-- ⛔ İKİNCİ NEDEN — eski indeks SEMANTİK OLARAK DA YANLIŞ: aynı kurumun aynı gün
--    aynı firmaya verdiği İKİ AYRI karar (farklı `nosu`) çakışır ve ikincisi
--    sessizce kaybolur. Yeni anahtar karar_no'yu görüyor.
--
-- ℹ NEDEN (kaynak, karar_no, firma_ad): bir karar (nosu) ortak girişimin BİRDEN
--   FAZLA üyesini yasaklayabilir → karar_no tek başına firma anahtarı DEĞİL.
--   kaynak öne alındı ki ileride resmi_gazete satırları ekap satırlarıyla çakışmasın.
--   ⚠ Resmî Gazete yükleyicisi geldiğinde karar_no'yu MUTLAKA doldurmalı
--     (ör. RG tarih+sayı); '' bırakılırsa aynı firmanın tüm RG kayıtları tek
--     satıra çöker.
CREATE UNIQUE INDEX IF NOT EXISTS ux_yasakli_dogal
  ON public.yasakli_firmalar (kaynak, karar_no, firma_ad);

-- Yeni indeks BAŞARIYLA kurulduktan SONRA eskiyi düşür. Sıra önemli: eski indeks
-- ayakta kalırsa, doğru anahtarla yapılan upsert onun kısıtını 23505 ile ihlal eder
-- (ON CONFLICT yalnız ÇIKARILAN indeksi ele alır, diğerini değil) → parti düşer.
DO $$
BEGIN
  IF to_regclass('public.ux_yasakli_dogal') IS NULL THEN
    RAISE EXCEPTION 'ABORT: ux_yasakli_dogal kurulamadı — eski indeks DÜŞÜRÜLMÜYOR';
  END IF;
  DROP INDEX IF EXISTS public.ux_yasakli_dedup;
  RAISE NOTICE 'OK: ux_yasakli_dedup düşürüldü, ux_yasakli_dogal devrede';
END $$;

-- A.4 arama_fold — sayfanın ILIKE'ı için (yukarıdaki "AYRI BİR HATA" bölümü).
-- normalize_ad'a DOKUNULMUYOR: o, firma_yasakli_mi() ve yukleniciler join'inin
-- sözleşmesi. Bu kolon YALNIZ serbest metin araması için.
ALTER TABLE public.yasakli_firmalar
  ADD COLUMN IF NOT EXISTS arama_fold text
    GENERATED ALWAYS AS (public.tr_fold(coalesce(firma_ad, ''))) STORED;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Baştan joker'li ILIKE ('%akca%') yalnız trigram indeksiyle indekslenebilir.
CREATE INDEX IF NOT EXISTS ix_yasakli_arama_fold_trgm
  ON public.yasakli_firmalar USING gin (arama_fold gin_trgm_ops);

-- A.5 normalize_ad'ı DB DOLDURUR — scraper DEĞİL.
-- ⛔ NEDEN: normalize_firma() bir SQL fonksiyonu. Python'da kopyalamak, fold()
-- dersindeki bayt-kayması tuzağının aynısıdır: normalize_ad bir JOIN ANAHTARI
-- (firma_yasakli_mi + yukleniciler); bir bayt oynarsa eşleşme SESSİZCE 0 döner
-- ve kimse fark etmez. Tek doğru kaynak DB tarafı.
CREATE OR REPLACE FUNCTION public.yasakli_normalize_doldur()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.normalize_ad := public.normalize_firma(NEW.firma_ad);
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_yasakli_normalize ON public.yasakli_firmalar;
CREATE TRIGGER trg_yasakli_normalize
  BEFORE INSERT OR UPDATE OF firma_ad ON public.yasakli_firmalar
  FOR EACH ROW EXECUTE FUNCTION public.yasakli_normalize_doldur();

-- Mevcut satırlar (varsa) için tek seferlik dolgu.
UPDATE public.yasakli_firmalar
   SET normalize_ad = public.normalize_firma(firma_ad)
 WHERE normalize_ad IS DISTINCT FROM public.normalize_firma(firma_ad);


-- =============================================================================
-- BÖLÜM B — YETKİLER  (önce REVOKE, sonra DAR GRANT)
-- =============================================================================
-- Sıra ŞART: yeni kolon/nesne varsayılan ayrıcalıkla doğup anon'a açık olabilir;
-- kolon-GRANT'ı önce REVOKE etmeden yazmak deliği kapatmaz
-- (hafıza: anon-maske-iki-kok-neden — kök neden A).

-- B.1 TABLO — anon ve PUBLIC tamamen dışarıda
REVOKE ALL ON TABLE public.yasakli_firmalar FROM PUBLIC;
REVOKE ALL ON TABLE public.yasakli_firmalar FROM anon;
-- Kolon düzeyinde artık kalmış olabilecek eski GRANT'lar da temizlensin:
REVOKE ALL (id, firma_ad, normalize_ad, arama_fold, karar_no, karar_veren_kurum,
            yasak_baslangic, yasak_bitis, yasak_suresi, tc_vergi_no, kanun_madde,
            uyruk, il, kaynak, resmi_gazete_tarih, aktif, olusturulma, guncellenme)
  ON public.yasakli_firmalar FROM anon;

-- B.2 authenticated — YALNIZ sayfanın ve iki RPC'nin gerçekten okuduğu kolonlar
--
-- Kolon kolon gerekçe (v1-yasakli.html:96 select'i + yasakli_listesi + firma_yasakli_mi):
--   id                → sayfa:126 `select('id',{count:'exact',head:true})`
--   firma_ad          → sayfa:110 · her iki RPC
--   arama_fold        → sayfa:97 ILIKE filtresi (takip işi sonrası)
--   normalize_ad      → firma_yasakli_mi() eşitliği + yukleniciler join'i
--   karar_veren_kurum → sayfa:113 · her iki RPC
--   yasak_baslangic   → sayfa:114 · sıralama anahtarı
--   yasak_bitis       → sayfa:107-108 (durum rozeti)
--   yasak_suresi      → sayfa:114
--   kanun_madde       → sayfa:111
--   il                → sayfa:111
--   tc_vergi_no       → sayfa:97 `.eq()` filtresi + :112 gösterim
--   aktif             → sayfa:108 · yasakli_listesi filtresi
--   kaynak            → 'ekap' / 'resmi_gazete' ayrımı, kaynak gösterimi
--
-- ⚠️ WHERE'de kullanmak da SELECT yetkisi ister — arama_fold ve tc_vergi_no
-- yalnız filtrede geçse bile listede OLMAK ZORUNDA (hafıza: kök neden C, 19 Tem'de
-- `idare_tur` filtresi tam bu yüzden iki sayfayı 42501 ile öldürmüştü).
--
-- ⚠️ KVKV NOTU — tc_vergi_no: bu uç TC/VKN VERMİYOR, alan bugün NULL. Ama
-- yasaklananların bir kısmı GERÇEK KİŞİ; Resmî Gazete kaynağı bağlandığında bu
-- kolona 11 haneli T.C. KİMLİK NO düşebilir. O gün bu satır yeniden
-- değerlendirilmeli (son 4 hane maskesi / ayrı rol / hiç göstermemek). anon'a
-- ZATEN kapalı; risk authenticated tarafındadır.
GRANT SELECT (id, firma_ad, arama_fold, normalize_ad, karar_veren_kurum,
              yasak_baslangic, yasak_bitis, yasak_suresi, kanun_madde, il,
              tc_vergi_no, aktif, kaynak)
  ON public.yasakli_firmalar TO authenticated;

-- Bilerek VERİLMEYENLER (gerekirse buraya EKLENEREK açılır — yeni kolon
-- otomatik gelmez, kök neden C):
--   karar_no · uyruk · resmi_gazete_tarih · olusturulma · guncellenme

-- B.3 service_role — scraper'ın yazdığı rol
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.yasakli_firmalar TO service_role;

-- B.4 FONKSİYONLAR — varsayılan PUBLIC EXECUTE deliği kapatılıyor
--     (yukarıdaki "CANLIDA BULUNAN GERÇEK DELİK" bölümü)
REVOKE ALL ON FUNCTION public.yasakli_listesi(text, boolean, int, int) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.firma_yasakli_mi(text)                   FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.yasakli_aktif_tazele()                   FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.yasakli_normalize_doldur()               FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.yasakli_listesi(text, boolean, int, int) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.firma_yasakli_mi(text)                   TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.yasakli_aktif_tazele()                   TO service_role;
-- yasakli_normalize_doldur() bir TETİKLEYİCİ fonksiyonu — kimsenin doğrudan
-- çağırmasına gerek yok; tetikleyici tablo sahibinin hakkıyla çalışır.


-- =============================================================================
-- BÖLÜM C — DOĞRULAMA  (migration_anon_maske.sql deseni)
-- =============================================================================
-- "GRANT yazdım" kanıt DEĞİL. anon-maske dersinde 5 nesnede delik çıkmıştı;
-- burada maske SET ROLE ile canlı sınanıyor ve delik varsa migration ROLLBACK olur.

SET ROLE anon;
DO $$
BEGIN
  BEGIN
    PERFORM firma_ad FROM public.yasakli_firmalar LIMIT 1;
    RAISE EXCEPTION 'HATA: anon yasakli_firmalar.firma_ad okuyabiliyor — MASKE DELİK!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: firma_ad anon-kapali'; END;
  BEGIN
    PERFORM tc_vergi_no FROM public.yasakli_firmalar LIMIT 1;
    RAISE EXCEPTION 'HATA: anon tc_vergi_no okuyabiliyor — KİŞİSEL VERİ AÇIK!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: tc_vergi_no anon-kapali'; END;
  -- YENİ kolonlar: varsayılan ayrıcalıkla doğup anon'a açılmış olabilirler
  BEGIN
    PERFORM arama_fold FROM public.yasakli_firmalar LIMIT 1;
    RAISE EXCEPTION 'HATA: anon arama_fold okuyabiliyor — yeni kolon anon-acik dogmus!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: arama_fold anon-kapali'; END;
  BEGIN
    PERFORM karar_no FROM public.yasakli_firmalar LIMIT 1;
    RAISE EXCEPTION 'HATA: anon karar_no okuyabiliyor — yeni kolon anon-acik dogmus!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: karar_no anon-kapali'; END;
  -- Toplu RPC anon'a KAPALI olmalı (veri-disa-aktarim-yasagi)
  BEGIN
    PERFORM public.yasakli_listesi(NULL::text, true, 1, 0);
    RAISE EXCEPTION 'HATA: anon yasakli_listesi() calistirabiliyor — BULK DOKUM ACIK!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: yasakli_listesi anon-kapali'; END;
  BEGIN
    PERFORM public.firma_yasakli_mi('X');
    RAISE EXCEPTION 'HATA: anon firma_yasakli_mi() calistirabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: firma_yasakli_mi anon-kapali'; END;
END $$;
RESET ROLE;

SET ROLE authenticated;
DO $$
BEGIN
  -- POZİTİF yön: üye dalı çalışmaya DEVAM etmeli. Bu blok düşerse sayfa canlıda
  -- 42501 alır (aşırı REVOKE, maskenin ters yönde kırılması).
  PERFORM id, firma_ad, arama_fold, normalize_ad, karar_veren_kurum,
          yasak_baslangic, yasak_bitis, yasak_suresi, kanun_madde, il,
          tc_vergi_no, aktif, kaynak
    FROM public.yasakli_firmalar LIMIT 1;
  RAISE NOTICE 'OK: authenticated sayfa kolonlarini okuyor';
  -- Sayfanın FİLTRELERİ (WHERE'de kullanmak da SELECT yetkisi ister)
  PERFORM 1 FROM public.yasakli_firmalar WHERE arama_fold ILIKE '%akca%' LIMIT 1;
  PERFORM 1 FROM public.yasakli_firmalar WHERE tc_vergi_no = '0' LIMIT 1;
  RAISE NOTICE 'OK: authenticated arama_fold/tc_vergi_no filtreleri calisiyor';
  PERFORM public.yasakli_listesi(NULL::text, true, 1, 0);
  PERFORM public.firma_yasakli_mi('X');
  RAISE NOTICE 'OK: authenticated yasakli_listesi + firma_yasakli_mi calisiyor';
END $$;
RESET ROLE;

-- Doğal anahtarın gerçekten upsert'e uygun olduğunu kanıtla: bu indeks yoksa
-- PostgREST on_conflict=kaynak,karar_no,firma_ad 42P10 ile patlar.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_index i
    JOIN pg_class c ON c.oid = i.indexrelid
    WHERE c.relname = 'ux_yasakli_dogal' AND i.indisunique
  ) THEN
    RAISE EXCEPTION 'ABORT: ux_yasakli_dogal unique degil/yok — scraper upsert edemez';
  END IF;
  RAISE NOTICE 'OK: ux_yasakli_dogal(kaynak,karar_no,firma_ad) upsert icin hazir';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- UYGULAMA SONRASI — anon curl'süz doğrulama YOKTUR
-- =============================================================================
-- Durum kodu YANILTIR: 200 + [] = RLS/filtre koruyor, 200 + DOLU GÖVDE = İFŞA.
-- Gövdeye bakın, -o /dev/null ile yetinmeyin (hafıza: http-200-ifsa-degil).
--
--   ANON="<anon key>"
--   curl -s "https://ihaleglobal.com/rest/v1/yasakli_firmalar?select=firma_ad&limit=1" \
--        -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--   # BEKLENEN: {"code":"42501", ... "permission denied for table yasakli_firmalar"}
--
--   curl -s "https://ihaleglobal.com/rest/v1/yasakli_firmalar?select=arama_fold&limit=1" \
--        -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--   # BEKLENEN: 42501  (42703 gelirse migration uygulanmamış demektir)
--
--   curl -s -X POST "https://ihaleglobal.com/rest/v1/rpc/yasakli_listesi" \
--        -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--        -H "Content-Type: application/json" -d '{}'
--   # BEKLENEN: EXECUTE reddi (42501/PGRST202) — "permission denied for TABLE" DEĞİL;
--   #           tablo hatası gelirse PUBLIC EXECUTE deliği HÂLÂ AÇIK demektir.
-- =============================================================================
