-- ekap_ihale_id geçmiş backfill'i — KAZIMA YOK, elimizdeki veriden (23 Tem 2026).
--
-- BULUNUŞ: #4 (belge erişimi) için gereken EKAP iç hash'i, `ihale_sonuclari.tum_teklifler`
-- içinde `sozlesme_bilgi.ihaleId` olarak ZATEN duruyordu. Yani "geçmiş satırlar için ayrı bir
-- liste turu gerekir" varsayımı YANLIŞMIŞ: 336.289 ihalenin hash'i bedava, tek UPDATE ile geliyor.
--
-- ⚠️ JSON AYRIŞTIRMA KULLANILMIYOR: `tum_teklifler` jsonb içine ÇİFT KODLANMIŞ bir metin
-- (jsonb_typeof = 'string', 539.203/539.203) ve 720 satır eski 15.000 karakter kırpmasından
-- bozuk. `::jsonb` cast'i o satırlarda tüm sorguyu düşürüyor. Hash sabit 64-hane hex olduğu
-- için regex ile çekmek hem bozuk satırlarda da çalışıyor hem de cast'ten hızlı.
UPDATE public.ilanlar i
SET ekap_ihale_id = k.hash
FROM (
    SELECT DISTINCT ON (s.ilan_id)
           s.ilan_id,
           substring(s.tum_teklifler #>> '{}' from '"ihaleId": ?"([0-9a-f]{64})"') AS hash
    FROM public.ihale_sonuclari s
    WHERE s.ilan_id IS NOT NULL
      AND substring(s.tum_teklifler #>> '{}' from '"ihaleId": ?"([0-9a-f]{64})"') IS NOT NULL
    ORDER BY s.ilan_id, s.sonuc_tarihi DESC NULLS LAST
) k
WHERE i.id = k.ilan_id
  AND i.ekap_ihale_id IS NULL;
