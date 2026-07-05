-- ============================================================================
-- KRİTİK GÜVENLİK DÜZELTMESİ — kredi tablolarını salt-okur yap
-- Supabase SQL Editor'da çalıştır: https://supabase.com/dashboard/project/lpgelwfoarhouollhwur/sql/new
-- ----------------------------------------------------------------------------
-- SORUN (4 Tem 2026 denetimi, onaylandı):
--   kullanici_krediler ve kredi_hareketleri tablolarındaki policy'ler cmd=ALL,
--   WITH CHECK boş → INSERT/UPDATE için USING'e (auth.uid()=kullanici_id) düşüyor.
--   Sonuç: giriş yapmış kullanıcı KENDİ kredi satırını UPDATE edebiliyor.
--   kalan_kredi hesaplanan kolon ama kaynağı toplam_kredi yazılabilir →
--   kullanıcı toplam_kredi'yi şişirip kendine bedava kredi verebilir (İyzico bypass).
--
-- NEDEN GÜVENLİ:
--   Krediyi backend payment.py SERVICE_ROLE anahtarıyla yazıyor; service_role
--   RLS'i tamamen bypass eder → aşağıdaki kısıtlama ödemeyi/kredi yüklemeyi
--   ETKİLEMEZ. Frontend krediyi yalnızca SELECT ediyor. Düşüm backend'de.
-- ============================================================================

-- RLS'in açık olduğundan emin ol (idempotent — zaten açık)
alter table public.kullanici_krediler enable row level security;
alter table public.kredi_hareketleri  enable row level security;

-- Gevşek ALL policy'lerini kaldır
drop policy if exists kredi_kendi   on public.kullanici_krediler;
drop policy if exists hareket_kendi on public.kredi_hareketleri;

-- Yerine SADECE OKUMA (kendi satırı) policy'leri koy
create policy kredi_select_own on public.kullanici_krediler
  for select to public using (auth.uid() = kullanici_id);

create policy hareket_select_own on public.kredi_hareketleri
  for select to public using (auth.uid() = kullanici_id);

-- ============================================================================
-- DOĞRULAMA: çalıştırdıktan sonra iki policy de cmd=SELECT görünmeli
select tablename, policyname, cmd, with_check
from pg_policies
where schemaname = 'public'
  and tablename in ('kullanici_krediler','kredi_hareketleri')
order by tablename;
-- Beklenen: her tablo için tek satır, cmd = SELECT.
-- Artık kullanıcı kendi kredisini OKUyabilir ama DEĞİŞTİREMEZ; backend service_role yazmaya devam eder.
-- ============================================================================
