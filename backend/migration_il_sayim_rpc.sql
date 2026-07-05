-- Anasayfa haritası hız iyileştirmesi — il bazlı sayımı server-side yap
-- Supabase SQL Editor'da çalıştır: https://supabase.com/dashboard/project/lpgelwfoarhouollhwur/sql/new
--
-- SORUN: index.html haritası il sayımlarını çıkarmak için ilanlar tablosundan
--   13 ayrı istekle ~12.700 satırı tarayıcıya çekiyordu (GROUP BY'ı JS yapıyordu).
--   Her açılışta yavaş + gereksiz ~200KB transfer.
-- ÇÖZÜM: tek RPC ile GROUP BY il -> 81 satır döner, harita anında yüklenir.
--
-- Güvenlik: SECURITY INVOKER (varsayılan) — çağıranın RLS'iyle çalışır. anon zaten
--   ilanlar'ı okuyabildiği (ilanlar_public_read policy) için sayım doğru döner.

create or replace function public.il_sayim()
returns table(il text, adet bigint)
language sql
stable
as $$
  select il, count(*)::bigint as adet
  from public.ilanlar
  where il is not null
  group by il
$$;

grant execute on function public.il_sayim() to anon, authenticated;

-- Doğrulama (birkaç il sayısı gelmeli):
-- select * from public.il_sayim() order by adet desc limit 5;
