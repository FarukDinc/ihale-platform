-- RLS Denetim Teşhisi — Supabase SQL Editor'da çalıştır (SALT-OKUR, hiçbir veriye dokunmaz)
-- Amaç: Canlıya almadan önce her tabloda RLS açık mı ve hangi policy'ler var, kesin gör.
-- 4 Tem 2026 tarihli anon/authed API denetimi write tarafında iki tabloyu belirsiz bıraktı:
--   * kredi_hareketleri (kredi defteri — kalan_kredi bundan türeniyorsa kritik)
--   * ilanlar (public tablo; write testi güvenlik katmanınca engellendi)
-- Aşağıdaki 2 sorgu bunu kesinleştirir.

-- 1) Hangi public tablolarda RLS AÇIK / KAPALI?
select c.relname                as tablo,
       c.relrowsecurity         as rls_acik,
       c.relforcerowsecurity    as rls_zorunlu
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
order by c.relrowsecurity, c.relname;

-- 2) Her tablodaki policy'ler (cmd = SELECT/INSERT/UPDATE/DELETE/ALL; roles = kime uygulanıyor)
select tablename  as tablo,
       policyname as policy,
       cmd        as komut,
       roles,
       qual       as using_ifadesi,
       with_check as with_check_ifadesi
from pg_policies
where schemaname = 'public'
order by tablename, cmd;

-- BEKLENEN GÜVENLİ DURUM:
--  * TÜM kullanıcı tablolarında (profil, takipler, kullanici_krediler, kullanici_profiller,
--    kredi_hareketleri, bildirimler, teklifler) rls_acik = true olmalı.
--  * kredi_hareketleri ve kullanici_krediler'de authenticated rolü için INSERT/UPDATE policy
--    OLMAMALI (krediyi sadece backend service_role yazar). Sadece kendi satırını SELECT edebilmeli:
--       USING (kullanici_id = auth.uid())
--  * ilanlar / ihale_sonuclari: authenticated+anon için sadece SELECT policy olmalı,
--    INSERT/UPDATE/DELETE policy OLMAMALI (scraper service_role ile yazar).
--
-- Eğer kredi_hareketleri'nde authenticated için bir INSERT policy görürsen VEYA rls_acik=false ise:
--    -> Kullanıcı kendine bedava kredi yazabilir. Canlıya almadan MUTLAKA kapat:
--       alter table public.kredi_hareketleri enable row level security;
--       drop policy if exists "<gevşek insert policy adı>" on public.kredi_hareketleri;
--       -- sadece okuma bırak:
--       create policy kredi_hareketleri_select_own on public.kredi_hareketleri
--         for select to authenticated using (kullanici_id = auth.uid());
