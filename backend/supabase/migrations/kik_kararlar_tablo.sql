-- KİK Kamu İhale Kurumu Uyuşmazlık Kararları tablosu
-- Çalıştır: Supabase Dashboard > SQL Editor veya psql

create table if not exists public.kik_kararlar (
  id              uuid default gen_random_uuid() primary key,
  karar_no        text unique not null,        -- örn. "2024/UH.I-1234"
  karar_tarihi    date,
  karar_turu      text,                         -- uyusmazlik | inceleme | duzenleyici
  sonuc           text,                         -- iptal | kabul | red | diger
  baslik          text,
  idare           text,
  ihale_konusu    text,
  ozet            text,
  kaynak_url      text,
  ham_veri        jsonb,
  olusturulma     timestamptz default now(),
  guncelleme      timestamptz default now()
);

-- İndeksler
create index if not exists kik_kararlar_tarih_idx    on public.kik_kararlar(karar_tarihi desc);
create index if not exists kik_kararlar_sonuc_idx    on public.kik_kararlar(sonuc);
create index if not exists kik_kararlar_tur_idx      on public.kik_kararlar(karar_turu);
create index if not exists kik_kararlar_idare_idx    on public.kik_kararlar using gin(to_tsvector('turkish', coalesce(idare,'')));
create index if not exists kik_kararlar_baslik_idx   on public.kik_kararlar using gin(to_tsvector('turkish', coalesce(baslik,'') || ' ' || coalesce(ihale_konusu,'') || ' ' || coalesce(ozet,'')));

-- RLS
alter table public.kik_kararlar enable row level security;
create policy "herkes okuyabilir" on public.kik_kararlar for select using (true);
