-- ============================================================
-- İhalePlatform — kik_kararlar tablosu (hiç oluşturulmamıştı)
--
-- backend/kik_backfill.py bu tabloya upsert() atıyor, kik-kararlar.html
-- bundan select() yapıyor — ikisi de kod olarak hazırdı ama tablo hiç
-- migration edilmemişti (sadece Python script'in docstring'i "kik_kararlar
-- tablosuna kaydeder" diyordu, gerçek DDL hiçbir yerde yoktu).
--
-- NOT: KİK kaynağı ayrıca IP-bloklu (302 redirect, cron logunda her gece
-- "0 eklendi") — bu migration sadece tabloyu var eder, kaynak-engeli
-- ÇÖZMEZ (o Playwright gerektiren ayrı bir iş, bkz. YAPILACAKLAR.md Faz E4).
-- Bu haliyle sayfa en azından hata vermeden "kayıt yok" gösterir.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kik_kararlar_tablo.sql
-- ============================================================

create table if not exists public.kik_kararlar (
  id            uuid primary key default gen_random_uuid(),
  karar_no      text not null,
  karar_tarihi  date,
  karar_turu    text,
  sonuc         text,
  baslik        text,
  idare         text,
  ihale_konusu  text,
  ozet          text,
  kaynak_url    text,
  ham_veri      jsonb,
  olusturulma   timestamptz default now()
);

create unique index if not exists kik_kararlar_karar_no_key on public.kik_kararlar(karar_no);
create index if not exists kik_kararlar_tarih_idx on public.kik_kararlar(karar_tarihi desc);

alter table public.kik_kararlar enable row level security;

create policy "kararlar_herkese_acik" on public.kik_kararlar for select using (true);

grant select on public.kik_kararlar to anon, authenticated;
grant all on public.kik_kararlar to service_role;

-- Kontrol
select count(*) from public.kik_kararlar;
