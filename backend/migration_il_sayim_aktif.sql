-- ============================================================
-- İhaleGlobal — Harita için AKTİF il sayımları (il_sayim_aktif / dt_il_sayim_aktif)
--
-- SORUN: Harita `il_sayim` + `dt_il_sayim` kullanıyordu; ikisi de TÜM ZAMANLARI sayıyor
-- (ilanlar 356.904, DT 1.490.591 — geçmiş + sonuçlanmış dahil). Popup ise "Güncel
-- İhaleler" diyordu → etiket ile veri uyuşmuyordu. Dashboard KPI'sı ("Aktif Türkiye
-- İhalesi" 100.455) zaten AKTİF sayıyor, yalnız harita toplamı gösteriyordu.
--   Aktif: ilanlar 4.654 · DT 95.695  (toplam ≈100.349 → KPI ile tutarlı)
--
-- NEDEN YENİ RPC (mevcutlar DEĞİŞTİRİLMEDİ):
--   • `dt_il_sayim` — dogrudan-temin.html'de İL DROPDOWN'ının tam listesini besliyor.
--     Aktif-only yapılsaydı aktif DT'si olmayan iller dropdown'dan sessizce düşerdi
--     (o dosyadaki yoruma göre bu regresyon bir kez zaten yaşanmış).
--   • `il_sayim` — index.html ve başka yerlerden çağrılıyor.
--
-- NEDEN MV DEĞİL: "aktif" zamana bağlı (son_teklif_tarihi >= now()); MV gün içinde
-- bayatlar (süresi dolan ihaleler aktif görünmeye devam eder). Canlı sorgu:
-- ilanlar tarafı tarih indeksiyle ucuz, DT tarafı ~0,3sn (ölçüldü) — kabul edilebilir.
--
-- Aktif tanımları, arayüzdeki "Güncel" sekmeleriyle BİREBİR aynı olmalı:
--   ilanlar → son_teklif_tarihi >= now()                     (ihaleler.html 'guncel')
--   DT      → durum IN ('Doğrudan Temin Duyurusu Yayımlanmış',
--                       'Teklifler Değerlendiriliyor')       (dogrudan-temin.html 'guncel')
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_il_sayim_aktif.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.il_sayim_aktif()
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
SET statement_timeout TO '20s'
AS $function$
  SELECT il, count(*)::bigint AS adet
  FROM   public.ilanlar
  WHERE  il IS NOT NULL AND il <> ''
    AND  son_teklif_tarihi >= now()
  GROUP  BY il;
$function$;

CREATE OR REPLACE FUNCTION public.dt_il_sayim_aktif()
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
SET statement_timeout TO '20s'
AS $function$
  SELECT il, count(*)::bigint AS adet
  FROM   public.dogrudan_temin_ilanlari
  WHERE  il IS NOT NULL AND il <> ''
    AND  durum IN ('Doğrudan Temin Duyurusu Yayımlanmış', 'Teklifler Değerlendiriliyor')
  GROUP  BY il;
$function$;

GRANT EXECUTE ON FUNCTION public.il_sayim_aktif()    TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.dt_il_sayim_aktif() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama: toplamlar ~4.654 ve ~95.695 olmalı (tümü 356.904 / 1.490.591 DEĞİL)
SELECT 'ihale_aktif' AS ne, sum(adet) FROM public.il_sayim_aktif()
UNION ALL
SELECT 'dt_aktif', sum(adet) FROM public.dt_il_sayim_aktif();
