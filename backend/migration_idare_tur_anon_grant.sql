-- ============================================================================
-- İhaleGlobal — `idare_tur` kolonunu anon'a AÇ (canlı hatayı kapatır)
--
-- CANLI HATA (19 Tem 2026, curl ile doğrulandı):
--   commit cf18d8c "İdare Türü" filtresini ihaleler.html + dogrudan-temin.html'e
--   ekledi ve sorguya `.eq('idare_tur', X)` koydu — uyeMi dalı OLMADAN.
--   Ama `idare_tur` kolonu anon'a GRANT edilmemiş:
--     /rest/v1/ilanlar?select=id&idare_tur=eq.belediye              → 42501
--     /rest/v1/dogrudan_temin_ilanlari?...&idare_tur=eq.belediye    → 42501
--   Kontrol (anon'a açık kolon): ?tur=eq.Mal → 200
--   Yani MİSAFİR "Belediye" seçtiği anda liste tamamen ölüyor ("Veri yüklenemedi").
--
-- KÖK NEDEN — tekrar eden tuzak:
--   Kolon-seviyesi GRANT'lar SONRADAN EKLENEN kolonlara genişlemez. migration_
--   anon_maske.sql çalıştığında `idare_tur` henüz yoktu (migration_idare_tur_kolon.sql
--   ile sonra eklendi) → kolon doğuştan anon'a kapalı.
--   NOT: WHERE'de kullanmak da SELECT yetkisi ister — kolon select listesinde
--   olmasa bile. Bu yüzden "select'e koymadık, güvendeyiz" YANLIŞ.
--
-- NEDEN AÇMAK DOĞRU (maskeleme politikasıyla tutarlı):
--   Maskelenen şey idare ADI (`idare`). `idare_tur` ise kaba bir sınıf etiketi
--   (belediye / hastane / üniversite / bakanlık…) — tek başına hiçbir idareyi
--   tanımlamıyor. `kategori`, `il`, `tur` kolonlarıyla AYNI sınıfta ve onlar
--   zaten anon'a açık. Üstelik bu bir gezinme filtresi; misafire kapatmak
--   özelliğin amacını bozardı.
--   ALTERNATİF (uygulanmadı): sayfada `uyeMi` dalı ile filtreyi üyeye özel yapmak.
--   Reddedildi çünkü filtre kategoriyle eşdeğer bir tarama aracı, üyelik duvarı
--   arkasına koymak için bir gerekçe yok.
--
-- Çalıştırma (VDS):
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_tur_anon_grant.sql
-- ============================================================================

BEGIN;

DO $$
BEGIN
  -- Kolon gerçekten var mı? (ilanlar ve DT'de ayrı ayrı — biri yoksa diğerini yine aç)
  -- EXECUTE ile: projedeki mevcut desen (migration_anon_maske.sql) ve PL/pgSQL'in
  -- utility komutlarını yorumlamasına dair her türlü belirsizliği ortadan kaldırır.
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='ilanlar' AND column_name='idare_tur') THEN
    EXECUTE 'GRANT SELECT (idare_tur) ON public.ilanlar TO anon';
    RAISE NOTICE 'ilanlar.idare_tur → anon GRANT edildi';
  ELSE
    RAISE NOTICE 'ATLANDI: ilanlar.idare_tur kolonu yok (migration_idare_tur_kolon.sql uygulanmamis)';
  END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='dogrudan_temin_ilanlari' AND column_name='idare_tur') THEN
    EXECUTE 'GRANT SELECT (idare_tur) ON public.dogrudan_temin_ilanlari TO anon';
    RAISE NOTICE 'dogrudan_temin_ilanlari.idare_tur → anon GRANT edildi';
  ELSE
    RAISE NOTICE 'ATLANDI: dogrudan_temin_ilanlari.idare_tur kolonu yok';
  END IF;
END $$;

-- ── DOĞRULAMA: yanlışsa COMMIT ETMEZ ────────────────────────────────────────
DO $$
BEGIN
  -- 1) idare_tur artık anon'a açık olmalı (asıl amaç)
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='ilanlar' AND column_name='idare_tur')
     AND NOT has_column_privilege('anon', 'public.ilanlar', 'idare_tur', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon hala ilanlar.idare_tur okuyamiyor';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='dogrudan_temin_ilanlari' AND column_name='idare_tur')
     AND NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare_tur', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon hala DT.idare_tur okuyamiyor';
  END IF;

  -- 2) MEVCUT MASKE BOZULMAMIŞ olmalı — bu migration yalnız BİR kolon açar,
  --    idare/kazanan gibi maskeli kolonlara dokunmaz. Kaza eseri genişleme olursa yakala.
  IF has_column_privilege('anon', 'public.ilanlar', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon ilanlar.idare okuyabiliyor — maske delinmis';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon DT.idare okuyabiliyor — maske delinmis';
  END IF;
  IF has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'dt_ihale_token', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon DT token okuyabiliyor';
  END IF;

  RAISE NOTICE 'OK: idare_tur anon a acik, idare/token maskesi saglam';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── UYGULAMA SONRASI curl DOĞRULAMASI (atlanmamalı) ─────────────────────────
--   curl -s -o /dev/null -w "%{http_code}\n" \
--     "https://ihaleglobal.com/rest/v1/ilanlar?select=id&idare_tur=eq.belediye&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON"      # 200 BEKLENIR
--   curl -s -o /dev/null -w "%{http_code}\n" \
--     "https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari?select=dt_no&idare_tur=eq.belediye&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON"      # 200 BEKLENIR
--   curl -s "https://ihaleglobal.com/rest/v1/ilanlar?select=idare&limit=1" \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON"      # 42501 BEKLENIR (maske)
-- Ardından gizli pencerede /ihaleler ve /dogrudan-temin açıp "İdare Türü"
-- filtresinden Belediye seç → liste DOLU gelmeli, konsolda 42501 OLMAMALI.

-- ============================================================================
-- 🔁 TEKRARI ÖNLEMEK İÇİN — yeni kolon eklendiğinde ÇALIŞTIRILACAK TEŞHİS
--
-- Bu tuzak (yeni kolon → anon'a kapalı → sayfa 42501) üçüncü kez yaşandı.
-- Aşağıdaki sorgu, anon'a KAPALI olan kolonları listeler. Yeni bir kolon
-- ekledikten sonra çalıştırın; listede beklemediğiniz bir kolon varsa
-- ya GRANT edin ya da bilinçli maskelediğinizi teyit edin.
--
--   SELECT c.table_name, c.column_name
--   FROM information_schema.columns c
--   WHERE c.table_schema = 'public'
--     AND c.table_name IN ('ilanlar', 'dogrudan_temin_ilanlari',
--                          'ihale_sonuclari', 'dogrudan_temin_sonuclari', 'yukleniciler')
--     AND NOT has_column_privilege('anon', 'public.' || c.table_name, c.column_name, 'SELECT')
--   ORDER BY c.table_name, c.column_name;
--
-- BEKLENEN (bilinçli maskeli) çıktı: ilanlar.idare, DT.idare,
--   DT.dt_ihale_token, DT.dt_idare_token, dogrudan_temin_sonuclari.kazanan_firma,
--   yukleniciler.* (isim kolonları) — bunlar DIŞINDA ne çıkarsa incelenmeli.
-- ============================================================================
