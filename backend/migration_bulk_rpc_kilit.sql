-- ============================================================================
-- migration_bulk_rpc_kilit.sql — Toplu-veri RPC'leri anon'a KAPATILDI (16 Tem 2026)
--
-- Kullanıcı kararı (CSV kaldırmanın devamı): platformun topladığı veri toplu
-- indirilemesin. UI butonları kaldırıldı (commit afb7b1b) ama anon key sayfa
-- kaynağında olduğundan bu iki RPC login'siz curl'le TÜM idare dizinini
-- döküyordu (23K satır; idare_dizin_json tek istekte 2MB):
--   idare_dizin_json()  — tam dizin, tek istek
--   idare_sayim()       — aynı veri, 1000'er satır sayfalı
-- İkisi de artık YALNIZ giriş yapmış kullanıcı (authenticated) + service_role.
--
-- NOT: Postgres'te fonksiyonlar varsayılan PUBLIC EXECUTE ile doğar; sadece
-- "REVOKE FROM anon" yetmez — anon, PUBLIC üzerinden yine çalıştırabilirdi.
-- Bu yüzden önce PUBLIC'ten, sonra anon'dan REVOKE ediyoruz.
--
-- BİLİNÇLİ AÇIK BIRAKILANLAR (küçük aggregate'ler / sayfa vitrinleri):
--   kategori_sayim(46 satır), il_sayim(83), il_firma_dagilimi(81),
--   yuklenici_ozet(1), sonuc_ozet(1), il_sektor_ozet(3.1K il×kategori istatistiği),
--   il_sektor_firmalar(≤50/istek), analiz_pivot(≤500 aggregate), kurum_ozet,
--   rekabet_ozet, il_rfq_dagilimi — bunlar istatistik/vitrin, ham kayıt dökümü değil.
--   Ham tabloların (ilanlar/ihale_sonuclari/yukleniciler/...) anon SELECT'i AYRI
--   ve daha büyük bir karar (misafir sayfaları tamamen kilitler) — YAPILACAKLAR'da.
--
-- Frontend eşleri (aynı commit): idareler.html misafire 🔒 giriş kapısı,
-- dashboard Top Kurumlar widget'ı misafirde "giriş gerekli" der.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_bulk_rpc_kilit.sql
-- Idempotent; geri almak istersen: GRANT EXECUTE ... TO anon;
-- ============================================================================

REVOKE EXECUTE ON FUNCTION public.idare_dizin_json() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.idare_dizin_json() FROM anon;
GRANT  EXECUTE ON FUNCTION public.idare_dizin_json() TO authenticated, service_role;

REVOKE EXECUTE ON FUNCTION public.idare_sayim() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.idare_sayim() FROM anon;
GRANT  EXECUTE ON FUNCTION public.idare_sayim() TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol: anon reddedilmeli, authenticated çalışmalı
SET ROLE anon;
DO $$
BEGIN
  BEGIN
    PERFORM public.idare_sayim();
    RAISE EXCEPTION 'HATA: anon hala idare_sayim calistirabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'OK: anon -> idare_sayim reddedildi';
  END;
  BEGIN
    PERFORM public.idare_dizin_json();
    RAISE EXCEPTION 'HATA: anon hala idare_dizin_json calistirabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'OK: anon -> idare_dizin_json reddedildi';
  END;
END $$;
RESET ROLE;

SET ROLE authenticated;
SELECT 'OK: authenticated -> ' || jsonb_array_length(public.idare_dizin_json())::text || ' idare' AS auth_testi;
RESET ROLE;
