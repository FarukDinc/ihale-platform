-- Yüklenici VKN'lerini devir/tasfiye kayıtlarından çıkar (24 Tem 2026).
--
-- KAYNAK: EKAP sözleşme DEVRİ olan ihalelerde `tasfiyeTransferList` içinde devreden/devralan
-- firmanın RESMÎ vergi numarası yayımlanıyor:
--   "istekli": {"adSoyadUnvan": "AL-KA İNŞAAT ... A.Ş.", "vergiNo": "0470581401"}
-- Bu alan bugüne dek hiç okunmuyordu. Genel firma evreninde EKAP VKN yayımlamıyor
-- (bkz. [[vkn-yok-beyan-rozet]]) — bu, elimizdeki TEK resmî VKN kaynağı.
--
-- ⛔ REGEX kullanılıyor, ::jsonb cast DEĞİL: tum_teklifler jsonb'ye çift kodlanmış ve
-- 720 satır eski 15.000 karakter kırpmasından bozuk → cast tüm sorguyu düşürür
-- (bkz. [[tum-teklifler-gizli-veri]]).
--
-- ÖLÇÜM: 2.168 çift → 1.472 benzersiz VKN → 1.184 firma eşleşti (%80).
-- ⚠️ ÇAKIŞMA GUARD'I: aynı firmaya birden çok farklı VKN eşleşen 1 kayıt var —
-- hangisinin doğru olduğu bilinemez, o firma ATLANIR (yanlış VKN yazmaktansa boş bırak).

ALTER TABLE public.yukleniciler ADD COLUMN IF NOT EXISTS vkn_kaynak text;
COMMENT ON COLUMN public.yukleniciler.vkn_kaynak IS
  'VKN nereden geldi: ekap_devir = sözleşme devri kaydından (resmî), null = yok';

WITH ham AS (
  SELECT (regexp_matches(tum_teklifler #>> '{}',
           '"adSoyadUnvan": ?"([^"]+)", ?"vergiNo": ?"([0-9]{10,11})"', 'g')) AS m
  FROM public.ihale_sonuclari
  WHERE tum_teklifler #>> '{}' LIKE '%vergiNo%'
),
cift AS (SELECT DISTINCT m[1] AS unvan, m[2] AS vkn FROM ham),
esles AS (
  SELECT y.id, c.vkn
  FROM cift c
  JOIN public.yukleniciler y ON public.normalize_firma(c.unvan) = y.normalize_ad
),
tekil AS (                       -- yalnız TEK VKN'ye eşleşen firmalar (çakışanlar elenir)
  SELECT id, min(vkn) AS vkn
  FROM esles GROUP BY id HAVING count(DISTINCT vkn) = 1
)
UPDATE public.yukleniciler y
SET vergi_no = t.vkn, vkn_kaynak = 'ekap_devir'
FROM tekil t
WHERE y.id = t.id AND y.vergi_no IS DISTINCT FROM t.vkn;

-- Doğrulama
SELECT count(*) AS vkn_dolu, count(*) FILTER (WHERE vkn_kaynak='ekap_devir') AS devirden
FROM public.yukleniciler WHERE vergi_no IS NOT NULL;
