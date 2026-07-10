-- Bültenler (kayıtlı arama + e-posta aboneliği)
create table if not exists public.bultenler (
  id            uuid default gen_random_uuid() primary key,
  kullanici_id  uuid references auth.users(id) on delete cascade not null,
  ad            text not null,
  filtre        jsonb not null default '{}',
  -- filtre örnek: {"kelime":"beton","il":"İSTANBUL","tur":"Yapım","usul":"","min_bedel":1000000}
  frekans       text not null default 'gunluk',  -- gunluk | haftalik
  email_aktif   boolean not null default true,
  son_gonderim  timestamptz,
  olusturulma   timestamptz default now(),
  guncelleme    timestamptz default now()
);

create index if not exists bultenler_kullanici_idx on public.bultenler(kullanici_id);
create index if not exists bultenler_frekans_idx   on public.bultenler(frekans) where email_aktif = true;

alter table public.bultenler enable row level security;

-- Kullanıcı kendi bültenlerini CRUD yapabilir
create policy "kullanici kendi bultenlerini okur"   on public.bultenler for select using (auth.uid() = kullanici_id);
create policy "kullanici kendi bultenini olusturur" on public.bultenler for insert with check (auth.uid() = kullanici_id);
create policy "kullanici kendi bultenini gunceller" on public.bultenler for update using (auth.uid() = kullanici_id);
create policy "kullanici kendi bultenini siler"     on public.bultenler for delete using (auth.uid() = kullanici_id);

-- Service role (backend) tüm bültenleri okuyabilir/güncelleyebilir
create policy "service_role tam erisim" on public.bultenler using (true) with check (true);

grant all on public.bultenler to service_role, anon, authenticated;
