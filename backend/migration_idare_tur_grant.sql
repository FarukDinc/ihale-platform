-- ============================================================================
-- migration_idare_tur_grant.sql — yeni idare_tur kolonuna okuma yetkisi
--                                                              (19 Tem 2026)
-- CANLI HATA: ihaleler.html'de "İdare Türü" filtresi seçilince
--     42501 permission denied for table ilanlar
--   Filtresiz sorgu çalışıyordu (4.654 sonuç), filtreli patlıyordu.
--
-- KÖK NEDEN: ilanlar/dogrudan_temin_ilanlari misafir maskesi KOLON BAZLI
--   GRANT ile korunuyor (migration_anon_maske.sql). Kolon-bazlı yetkilendirmede
--   SONRADAN EKLENEN kolon anon'a OTOMATİK GELMEZ — ayrıca GRANT edilmeli.
--   PostgREST WHERE için de SELECT yetkisi arar → filtre komple 42501 verir.
--
-- ⚠️ KALICI KURAL: bu iki tabloya kolon eklendiğinde bu dosyaya da satır ekle,
--   yoksa kolon "yok" gibi davranır ve sebebi geç anlaşılır.
--
-- GÜVENLİK DEĞERLENDİRMESİ: idare_tur bir KATEGORİ ('belediye','saglik'…),
--   kurum KİMLİĞİ değil. `idare` kolonu misafire kapalı kalmaya devam ediyor —
--   misafir "bu bir belediye ihalesi" görür ama HANGİ belediye olduğunu göremez.
--   Maskeleme amacı (kurum kimliğini gizlemek) bozulmuyor.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_tur_grant.sql
-- ============================================================================

GRANT SELECT (idare_tur) ON public.ilanlar                 TO anon, authenticated;
GRANT SELECT (idare_tur) ON public.dogrudan_temin_ilanlari TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- Kontrol (anon olarak):
--   curl "…/rest/v1/ilanlar?idare_tur=eq.saglik&select=id&limit=1" -H "apikey: <anon>"
--     → 200 dönmeli (42501 DEĞİL)
--   SELECT grantee, privilege_type FROM information_schema.column_privileges
--    WHERE table_name='ilanlar' AND column_name='idare_tur';
