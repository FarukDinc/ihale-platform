-- =============================================================================
-- migration_hiyerarsifiltre.sql — İhale + DT aramasına "bu kurum ve altındakiler"
--                                 SUNUCU TARAFI hiyerarşi süzgeci (YAPILACAKLAR #4)
-- =============================================================================
--
-- ÖNKOŞUL ZİNCİRİ (hepsi canlıda kurulu):
--   migration_idare_hiyerarsi.sql       → idare_ata_torun kapanış tablosu (312K satır)
--   migration_idare_agac_rpc.sql        → ilanlar/DT detsis_no kolonları + ağaç RPC'leri
--   migration_idare_hiyerarsi_sayim.sql → idare_hiyerarsi_sayim_mv (idare_agac_ara bunu okur)
--   ilan_detsis_esle()                  → detsis_no doluluk (gece taramasıyla ~%90)
--
-- ── NEDEN "SATIR-KÜMESİ DÖNEN FONKSİYON", NEDEN KLASİK ARAMA-RPC DEĞİL ───────
-- İki arama sayfası da (ihaleler.html / dogrudan-temin.html) PostgREST sorgu
-- kurucusuyla DOĞRUDAN tablo üstünde arıyor (eq/ilike/or/order/range/count/embed).
-- Aramayı yeni bir RPC'ye taşımak filtre mantığının İKİNCİ kopyasını yaratırdı —
-- kopya-arama yasak, bakımı imkânsızlaşır. PostgREST satır-kümesi döndüren
-- fonksiyonlara TABLO GİBİ davranır: select projeksiyonu, TÜM filtreler, order,
-- Range başlığı, count ve (dönüş tipi gerçek tablo tipiyse) ilişki embed'i
-- fonksiyon sonucuna aynen uygulanır. Yani sayfada taban `from('ilanlar')` yerine
-- `rpc('ilanlar_hiyerarsi', {p_kok})` konur; mevcut arama kodu DEĞİŞMEDEN çalışır.
--
-- Alternatif (istemcinin idare_alt_agac_detsis ile no listesi indirip in.(...)
-- kurması) YASAK: EGM dalı 1.090 no → ~10KB URL; bakanlık kökleri on binlerce
-- no → URL/istek patlar, ayrıca client-load-all sınıfı bir hata olur.
--
-- ── İNLİNE ŞARTI (performansın anahtarı) ─────────────────────────────────────
-- Fonksiyonlar bilinçli olarak: LANGUAGE sql + STABLE + tek SELECT + SECURITY
-- INVOKER + STRICT'siz + SET'siz. Bu koşullarda planlayıcı fonksiyonu çağıran
-- sorgunun İÇİNE AÇAR (inline): PostgREST'in dış WHERE/ORDER/LIMIT'i alt-ağaç
-- semijoin'iyle aynı planda birleşir, indeksler kullanılır. SECURITY DEFINER ya
-- da SET statement_timeout eklemek inlining'i ÖLDÜRÜR → 1,49M satırlık DT'de
-- fonksiyon sonucu önce materialize edilir (statement-timeout-edge sınıfı risk).
-- SECURITY INVOKER yeterli: authenticated'ın tablo yetkileri zaten var; anon'un
-- EXECUTE'u aşağıda açıkça kaldırılıyor.
--
-- ── İNDEKS ENVANTERİ (SQL'den kontrol edildi — YENİ İNDEKS GEREKMEDİ) ────────
--   idare_ata_torun : PRIMARY KEY (ata_no, torun_no) → ata_no önek taraması ✓
--                     idx_ata_torun_torun (torun_no) ✓  (migration_idare_hiyerarsi.sql)
--   ilanlar         : idx_ilanlar_detsis (detsis_no) WHERE detsis_no IS NOT NULL ✓
--   DT              : idx_dt_ilanlari_detsis (detsis_no) WHERE detsis_no IS NOT NULL ✓
--                     (migration_idare_agac_rpc.sql — CONCURRENTLY kuruldu)
--   Kısmi indeks eşleşmesi: `detsis_no = <torun_no>` katı (strict) operatör
--   olduğundan IS NOT NULL öngerektirmesi planlayıcıca kanıtlanabilir → kısmi
--   indeks KULLANILIR. Yine de deploy sonrası EXPLAIN ŞART (dosya sonunda sorgu).
--
-- ── ANON'A TAMAMEN KAPALI ────────────────────────────────────────────────────
-- idare kimliği misafire maskeli (migration_anon_maske.sql); alt-ağaç süzgeci o
-- maskenin dolaylı kırılımı olurdu ("kurum X'in ilanları" listesi = idare ifşası).
-- Fonksiyonlar PUBLIC EXECUTE ile doğar → REVOKE AÇIKÇA yazıldı (18 Tem dersi:
-- "GRANT yazmamak" yetmiyor, bkz. migration_dt_anon_fix.sql).
--
-- ── KAPSAMA DÜRÜSTLÜĞÜ ───────────────────────────────────────────────────────
-- detsis_no NULL satırlar (DETSİS'e eşleşmemiş ilanlar) bu filtrede ELENİR.
-- Bu bilinçli: eşleşmemiş kaydın hangi kuruma ait olduğu bilinmiyor, "dahilmiş
-- gibi" göstermek yalan olur. UI iki sayfada da küçük notla açıkça söylüyor.
--
-- Çalıştırma (VDS):
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_hiyerarsifiltre.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0) ÖN KONTROLLER — varsayımlar tutmuyorsa COMMIT ETME
-- ---------------------------------------------------------------------------
DO $on$
DECLARE
  eksik text;
BEGIN
  IF to_regclass('public.idare_ata_torun') IS NULL THEN
    RAISE EXCEPTION 'ABORT: idare_ata_torun yok — once migration_idare_hiyerarsi.sql uygulanmali';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'ilanlar'
                    AND column_name = 'detsis_no') THEN
    RAISE EXCEPTION 'ABORT: ilanlar.detsis_no yok — once migration_idare_agac_rpc.sql uygulanmali';
  END IF;

  -- ilanlar_hiyerarsi `SELECT i.*` yapar → authenticated HER kolonu okuyabilmeli.
  -- (DT tarafında bu varsayım BOZUK: dt_ihale_token/dt_idare_token authenticated'a
  --  kapalı — migration_dt_token_authenticated.sql. O yüzden DT fonksiyonu aşağıda
  --  DİNAMİK kolon listesiyle üretiliyor, `d.*` DEĞİL.)
  SELECT string_agg(c.column_name, ', ') INTO eksik
    FROM information_schema.columns c
   WHERE c.table_schema = 'public' AND c.table_name = 'ilanlar'
     AND NOT has_column_privilege('authenticated', 'public.ilanlar', c.column_name, 'SELECT');
  IF eksik IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: authenticated ilanlar kolonlarini okuyamiyor (%) — SELECT i.* 42501 verir; ilanlar_hiyerarsi DT''deki gibi dinamik kolon listesine cevrilmeli', eksik;
  END IF;

  -- WHERE'de kullanılan kolon da SELECT yetkisi ister (19 Tem dersi: idare_tur 42501)
  IF NOT has_column_privilege('authenticated', 'public.dogrudan_temin_ilanlari', 'detsis_no', 'SELECT') THEN
    RAISE EXCEPTION 'ABORT: authenticated dogrudan_temin_ilanlari.detsis_no okuyamiyor — filtre calisamaz';
  END IF;
END $on$;

-- ---------------------------------------------------------------------------
-- 1) ilanlar_hiyerarsi(p_kok) — İHALE aramasının hiyerarşi tabanı
--
-- RETURNS SETOF public.ilanlar BİLİNÇLİ (RETURNS TABLE değil): PostgREST ilişki
-- embed'i (ihaleler.html'in ihale_sonuclari / !inner join'i) yalnız gerçek tablo
-- tipinde dönüşlerde çalışır. Kolon budaması dert değil: fonksiyon inline olunca
-- dış select yalnız istenen kolonları değerlendirir (ilan_metni/ilan_html gibi
-- ağır kolonlar taşınmaz).
--
-- mesafe=0 satırı düğümün KENDİSİDİR (kapanış tablosu tasarımı) → tek koşulla
-- "kendisi + tüm altları" gelir.
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.ilanlar_hiyerarsi(text);
CREATE FUNCTION public.ilanlar_hiyerarsi(p_kok text)
RETURNS SETOF public.ilanlar
LANGUAGE sql STABLE
AS $$
  SELECT i.*
    FROM public.ilanlar i
   WHERE i.detsis_no IN (SELECT at.torun_no
                           FROM public.idare_ata_torun at
                          WHERE at.ata_no = p_kok)
$$;

-- ---------------------------------------------------------------------------
-- 2) dogrudan_temin_hiyerarsi(p_kok) — DT aramasının hiyerarşi tabanı
--
-- `SELECT d.*` KULLANILAMAZ: authenticated'ın DT tablosunda kolon-bazlı yetkisi
-- var (E10/E11 tokenları kapalı) ve `*` tüm kolonlarda yetki ister → 42501.
-- Kolon listesi ELLE de yazılMIYOR (bir kolon atlanırsa sayfa sessizce kırılır):
-- migration_dt_token_authenticated.sql'in dinamik deseniyle "authenticated'ın
-- OKUYABİLDİĞİ her kolon" pg_attribute'dan türetiliyor — grant'in birebir aynası.
--
-- ⚠️ KALICI BAKIM NOTU: kolon listesi bu migration'ın çalıştığı ANIN fotoğrafı.
-- DT tablosuna yeni kolon eklenirse (ve sayfa onu kullanacaksa) bu dosya YENİDEN
-- çalıştırılmalı — aynen kolon-GRANT'ların yeniden çalıştırılması gerektiği gibi.
--
-- DT sayfası embed kullanmıyor → RETURNS TABLE yeterli (embed kaybı sorun değil).
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- 3) idare_alt_kurum_sayisi(p_detsis) — "X ve altındaki N kurum" çipinin N'i
--    PK (ata_no, torun_no) önek taraması → anlık. mesafe=0 kendisi olduğundan
--    1 düşülür; detsis hiç yoksa negatif çıkmasın diye GREATEST.
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.idare_alt_kurum_sayisi(text);
CREATE FUNCTION public.idare_alt_kurum_sayisi(p_detsis text)
RETURNS bigint
LANGUAGE sql STABLE
AS $$
  SELECT GREATEST(count(*) - 1, 0)::bigint
    FROM public.idare_ata_torun at
   WHERE at.ata_no = p_detsis
$$;

-- ---------------------------------------------------------------------------
-- 4) YETKİLER — anon'a KAPALI, üyeye açık (üstteki gerekçe bloğuna bakın)
-- ---------------------------------------------------------------------------
REVOKE EXECUTE ON FUNCTION public.ilanlar_hiyerarsi(text)        FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.dogrudan_temin_hiyerarsi(text) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.idare_alt_kurum_sayisi(text)   FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.ilanlar_hiyerarsi(text)        TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.dogrudan_temin_hiyerarsi(text) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_alt_kurum_sayisi(text)   TO authenticated, service_role;

-- ---------------------------------------------------------------------------
-- 5) DOĞRULAMA — migration kendi kendini denetler, yanlışsa COMMIT ETMEZ
-- ---------------------------------------------------------------------------
DO $chk$
BEGIN
  IF has_function_privilege('anon', 'public.ilanlar_hiyerarsi(text)', 'EXECUTE')
     OR has_function_privilege('anon', 'public.dogrudan_temin_hiyerarsi(text)', 'EXECUTE')
     OR has_function_privilege('anon', 'public.idare_alt_kurum_sayisi(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon hiyerarsi RPC''lerinden en az birini calistirabiliyor';
  END IF;

  IF NOT has_function_privilege('authenticated', 'public.ilanlar_hiyerarsi(text)', 'EXECUTE')
     OR NOT has_function_privilege('authenticated', 'public.dogrudan_temin_hiyerarsi(text)', 'EXECUTE')
     OR NOT has_function_privilege('authenticated', 'public.idare_alt_kurum_sayisi(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated RPC''leri calistiramiyor — uye filtresi calismaz';
  END IF;

  IF pg_get_functiondef('public.dogrudan_temin_hiyerarsi(text)'::regprocedure) ILIKE '%dt_ihale_token%'
     OR pg_get_functiondef('public.dogrudan_temin_hiyerarsi(text)'::regprocedure) ILIKE '%dt_idare_token%' THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: DT fonksiyon govdesi token kolonu iceriyor';
  END IF;

  RAISE NOTICE 'OK: 3 fonksiyon kuruldu — anon kapali, authenticated acik, tokenlar disarida';
END $chk$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- UYGULAMA SONRASI DOĞRULAMA (atlanmamalı — "deploy sonrasi curl'suz dogrulama YOK")
-- =============================================================================
-- A) İNLİNE + İNDEKS KONTROLÜ (psql'de). Planda "Function Scan on
--    ilanlar_hiyerarsi" GÖRÜLMEMELİ — görülüyorsa inline olmamış demektir
--    (muhtemel neden: fonksiyona sonradan SET/STRICT/SECURITY DEFINER eklendi).
--    Beklenen: idare_ata_torun PK taraması + idx_ilanlar_detsis üstünde
--    Nested Loop / Hash Semi Join.
--
--   EXPLAIN (ANALYZE, BUFFERS)
--   SELECT id FROM public.ilanlar_hiyerarsi(
--     (SELECT detsis_no FROM idare_hiyerarsi WHERE ad ILIKE 'EMNİYET GENEL%' LIMIT 1))
--   ORDER BY son_teklif_tarihi LIMIT 25;
--
--   EXPLAIN (ANALYZE, BUFFERS)
--   SELECT dt_no FROM public.dogrudan_temin_hiyerarsi(
--     (SELECT detsis_no FROM idare_hiyerarsi WHERE ad ILIKE 'EMNİYET GENEL%' LIMIT 1))
--   ORDER BY tarih DESC LIMIT 25;
--
-- B) ANON KAPALI MI (curl) — 401/404 BEKLENİR:
--   curl -s -o /dev/null -w "%{http_code}\n" \
--     "https://ihaleglobal.com/rest/v1/rpc/ilanlar_hiyerarsi?p_kok=X&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON"
--
-- C) ÜYE İLE ÇALIŞIYOR MU ($UYE = giriş yapmış kullanıcının access_token'ı) —
--    200 + satırlar BEKLENİR; PostgREST filtre/order/range'in fonksiyona
--    uygulandığını da bu test kanıtlar:
--   curl -s "https://ihaleglobal.com/rest/v1/rpc/ilanlar_hiyerarsi?p_kok=<EGM_detsis>&select=id,baslik,idare&order=son_teklif_tarihi.asc&limit=3" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $UYE"
--
-- D) EMBED ÇALIŞIYOR MU (ihaleler.html Sonuç sekmesi buna muhtaç):
--   curl -s "https://ihaleglobal.com/rest/v1/rpc/ilanlar_hiyerarsi?p_kok=<EGM_detsis>&select=id,ihale_sonuclari(kazanan_teklif)&limit=3" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $UYE"
--
-- E) Sayfa akışı: /ihaleler ve /dogrudan-temin üye olarak → Detaylı Ara'da
--    "Kurum Hiyerarşisi" alanından EGM seç → çip "... ve altındaki N kurum"
--    görünmeli, liste il müdürlüklerinin ilanlarını da içermeli. Misafirde alan
--    kilitli olmalı, konsolda 42501 OLMAMALI.
-- =============================================================================
