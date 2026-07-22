-- ilanlar.kaynak CHECK kısıtı DMO ve Jandarma kaynaklarını içermiyordu.
--
-- SORUN (22 Tem tespit): ka_scraper.py DMO'yu kaynak='dmo', Jandarma'yı kaynak='jandarma'
-- ile public.ilanlar'a upsert ediyor. Ama `ilanlar_kaynak_check` yalnızca
-- ['ekap','ozel','uluslararasi','ilan_gov'] değerlerine izin veriyordu → her DMO/Jandarma
-- satırı 23514 (check_violation) veriyor. PostgREST toplu POST'u all-or-nothing olduğu için
-- TEK kötü satır tüm DMO/Jandarma batch'ini düşürüyor → bu iki kaynak ilanlar'a HİÇ yazılamıyor
-- (canlı: kaynak IN ('dmo','jandarma') → 0 satır). Gece cron her gün "✗ upsert hatası: 400"
-- basıp devam ediyordu (sessize yakın kayıp). ka_scraper'ın KA kısmı kamu_ihaleleri'ne yazdığı
-- için etkilenmiyordu.
--
-- ÇÖZÜM: allow-list'e 'dmo' ve 'jandarma' ekle. Yalnız izin genişletir; mevcut veriyi etkilemez.

ALTER TABLE public.ilanlar DROP CONSTRAINT IF EXISTS ilanlar_kaynak_check;
ALTER TABLE public.ilanlar ADD CONSTRAINT ilanlar_kaynak_check
  CHECK (kaynak = ANY (ARRAY['ekap','ozel','uluslararasi','ilan_gov','dmo','jandarma']));
