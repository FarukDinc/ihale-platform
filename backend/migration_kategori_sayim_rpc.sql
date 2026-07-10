-- ============================================================
-- İhalePlatform — kategori_sayim() RPC (performans)
--
-- sektorler.html bu RPC'yi zaten çağırıyordu (defensif try/catch ile — RPC
-- yoksa 38K satırı 1000'erlik sayfalarla (~38 istek) manuel sayıyordu).
-- RPC hiç oluşturulmamıştı. il_sayim() ile aynı desen.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kategori_sayim_rpc.sql
-- ============================================================

create or replace function public.kategori_sayim()
returns table(kategori text, toplam bigint, aktif bigint)
language sql
stable
as $$
  select coalesce(kategori, 'Diğer') as kategori,
         count(*) as toplam,
         count(*) filter (where durum = 'aktif') as aktif
  from public.ilanlar
  group by coalesce(kategori, 'Diğer');
$$;

grant execute on function public.kategori_sayim() to anon, authenticated;

-- Kontrol
select * from kategori_sayim() order by toplam desc limit 5;
