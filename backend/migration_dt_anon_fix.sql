-- =============================================================================
-- migration_dt_anon_fix.sql — DT nesnelerinde anon maskeleme deliğini kapatır
-- =============================================================================
--
-- SORUN (18 Tem 2026, canlıda doğrulandı):
--   Self-hosted Supabase'de şu varsayılan yürürlükte:
--       ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES
--         TO anon, authenticated, service_role;
--   Bu yüzden public şemasında YENİ oluşturulan her tablo VE materialized view,
--   doğuştan TABLO-GENELİ anon SELECT yetkisine sahip olur.
--
--   Sonuç: sadece
--       GRANT SELECT (kolon, listesi) ON <tablo> TO anon;
--   yazmak MASKELEME YAPMAZ. Kolon-bazlı GRANT yetkiyi *daraltmaz*, ekler.
--   Önce tablo-geneli yetki REVOKE edilmezse kolon listesi tamamen dekoratiftir.
--
--   Doğru kalıp backend/migration_anon_maske.sql içinde: her tabloda ÖNCE
--       REVOKE SELECT ON public.<tablo> FROM anon;
--   sonra kolon-GRANT. migration_dt_kazanan.sql ve migration_dashboard_dt_ozet.sql
--   bu REVOKE'u atladığı için 3 nesnede delik açıldı.
--
-- CANLI KANIT (anon key ile, düzeltme öncesi):
--   GET /rest/v1/dt_idare_ozet_mv?select=idare&limit=1        -> 200 + GERÇEK idare adı  (AKTİF SIZINTI)
--   GET /rest/v1/idare_ozet_mv?select=idare&limit=1           -> 401 42501               (referans: doğru)
--   GET /rest/v1/dogrudan_temin_sonuclari?select=*            -> 200                     (tablo boş, sızıntı henüz yok)
--   GET /rest/v1/dogrudan_temin_sonuclari?select=kazanan_firma-> 200                     (maskelenmiş olmalıydı)
--   GET /rest/v1/dt_takipler?select=*                         -> 200, 0 satır            (RLS kurtarıyor, yetki yine de fazla)
--
-- ETKİ SIRASI:
--   1) dt_idare_ozet_mv    — KRİTİK. 38.105 satır idare adı misafire açıktı ve
--                            bilinçli kapatılan dt_idare_sayim() RPC'sini baypas ediyordu.
--   2) dogrudan_temin_sonuclari — YÜKSEK. kazanan_firma + enc_sozlesme_id açıktı.
--                            Tablo şu an boş; kazanan/bedel backfill'i koşmadan ÖNCE kapatılmalı.
--   3) dt_takipler         — ORTA. Tablo-geneli GRANT fazlalık; RLS (auth.uid()=kullanici_id)
--                            sayesinde anon 0 satır görüyor, fiili ifşa yok.
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_anon_fix.sql
--
-- İlgili hafıza: veri-disa-aktarim-yasagi, studio-3000-exposure
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) dogrudan_temin_sonuclari — kimlik kapalı, sayılar/tarihler açık
--    (kapalı kalanlar: enc_sozlesme_id, kazanan_firma, yuklenici_id, guncellenme)
-- ---------------------------------------------------------------------------
REVOKE SELECT ON public.dogrudan_temin_sonuclari FROM anon;

GRANT SELECT (
  id, dt_no, kazanan_bedel, sozlesme_tarihi, en_yuksek_teklif, en_dusuk_teklif,
  sozlesme_mi, olusturulma
) ON public.dogrudan_temin_sonuclari TO anon;

-- ---------------------------------------------------------------------------
-- 2) dt_idare_ozet_mv — anon'a tamamen kapalı (idare_ozet_mv ile birebir aynı).
--    Erişim yalnızca dt_idare_sayim() RPC'si üzerinden, o da anon'a kapalı.
-- ---------------------------------------------------------------------------
REVOKE SELECT ON public.dt_idare_ozet_mv FROM anon;

-- ---------------------------------------------------------------------------
-- 3) dt_takipler — kullanıcıya özel tablo; anon'un hiçbir işi yok.
--    RLS zaten satırları filtreliyor ama yetki de verilmemeli (derinlemesine savunma).
-- ---------------------------------------------------------------------------
REVOKE ALL ON public.dt_takipler FROM anon;

-- dt_kategori_sayim_mv BİLİNÇLİ olarak anon'a açık bırakıldı: yalnızca
-- kategori adı + toplam/aktif sayaç içerir, kimlik verisi yok. Proje ilkesi
-- "sayılar/kategoriler misafire açık" (kategori_sayim_mv ile aynı).

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA — düzeltmeden sonra 3'ü de 42501 dönmeli
-- =============================================================================
--   curl -s -o /dev/null -w '%{http_code}\n' -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     'https://ihaleglobal.com/rest/v1/dt_idare_ozet_mv?select=idare&limit=1'              # 401 bekleniyor
--   curl ... 'https://ihaleglobal.com/rest/v1/dogrudan_temin_sonuclari?select=kazanan_firma&limit=1'  # 401 bekleniyor
--   curl ... 'https://ihaleglobal.com/rest/v1/dt_takipler?select=dt_no&limit=1'            # 401 bekleniyor
--   curl ... 'https://ihaleglobal.com/rest/v1/dogrudan_temin_sonuclari?select=kazanan_bedel&limit=1'  # 200 bekleniyor (açık kalmalı)

-- SQL tarafı doğrulama: anon'a tablo-geneli SELECT yetkisi kalan nesneleri listeler.
-- Buradan çıkan her satır BİLİNÇLİ bir karar olmalı; yeni bir tablo eklendiğinde
-- listeye habersiz düşüyorsa maskeleme unutulmuş demektir.
--
--   SELECT c.relname,
--          CASE c.relkind WHEN 'r' THEN 'tablo' WHEN 'v' THEN 'view' WHEN 'm' THEN 'mv' END AS tur
--     FROM pg_class c
--     JOIN pg_namespace n ON n.oid = c.relnamespace
--    WHERE n.nspname = 'public'
--      AND c.relkind IN ('r','v','m')
--      AND has_table_privilege('anon', c.oid, 'SELECT')
--      AND NOT EXISTS (                      -- kolon-bazlı maskelenmişleri ele
--            SELECT 1 FROM information_schema.column_privileges cp
--             WHERE cp.grantee = 'anon' AND cp.table_name = c.relname)
--    ORDER BY 2, 1;
