-- ============================================================
-- İhalePlatform — kullanici_profiller RLS sıkılaştırma (gizlilik düzeltmesi)
--
-- SORUN: SELECT policy'si "profil_herkes_okuyabilir" auth.role()='authenticated'
-- şartıyla — yani GİRİŞ YAPMIŞ HER KULLANICI, BAŞKA firmaların profilini
-- (vergi_no, mersisi_no, telefon, yillik_ciro_tl, calisma_illeri, referanslar...)
-- okuyabiliyordu. Hiçbir mevcut özellik bu geniş erişime ihtiyaç duymuyor —
-- Firmalar Dizini (firmalar.html) ayrı bir tablodan (yukleniciler, EKAP sonuç
-- verisi agregasyonu) okuyor, kullanici_profiller'a hiç dokunmuyor.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kullanici_profiller_rls_sikilastir.sql
-- ============================================================

drop policy if exists "profil_herkes_okuyabilir" on public.kullanici_profiller;

create policy "profil_sadece_kendi_okur" on public.kullanici_profiller
  for select using (auth.uid() = id);

-- Kontrol
select policyname, cmd, qual from pg_policies where tablename = 'kullanici_profiller';
