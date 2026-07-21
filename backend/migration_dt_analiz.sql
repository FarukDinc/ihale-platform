-- =============================================================================
-- migration_dt_analiz.sql — YAPILACAKLAR_v2 V2-6 (21 Tem 2026)
-- Doğrudan Temin (DT) için AYRI analiz yüzeyi: dt-analiz.html'i besleyen tek RPC.
--
-- KARAR (kullanıcı, 21 Tem): İhale analiz sayfaları (rekabet/kurum/firma) DT'yi bilinçle
-- DIŞLIYOR ("kapsam rozeti"). Kullanıcı DT için AYRI bir analiz sayfası istedi → dt-analiz.html
-- + bu RPC. İhale ile DT verisi ASLA toplanmaz (ölçek/kavram farkı: DT'de usul/tenzilat/
-- yaklaşık-maliyet YOK; onun yerine dogrudan_temin_sonuclari.kazanan_bedel var).
--
-- MİMARİ — neden MV + canlı ikili yol:
--   dogrudan_temin_ilanlari 1,49M satır. Filtresiz tam aggregate CANLI ölçüldü = ~5,2 sn
--   (statement_timeout ~3s'i AŞAR — count(DISTINCT) pahalı). Tek tek GROUP BY'lar ~500ms,
--   sonuç JOIN'i 80ms. Çözüm:
--     • dt_analiz_mv — filtresiz TAM özeti tek satır jsonb olarak tutar, GECE REFRESH edilir.
--       Varsayılan sayfa yüklemesi (filtre yok) MV'den ANINDA döner.
--     • Filtre (il/kategori/tür) seçilince alt-küme küçük → CANLI hesaplanır (indeksli, hızlı),
--       plpgsql sarmalayıcı statement_timeout'u 15s'e çıkarır (emniyet; pratikte <1s).
--   DRY: hem MV hem canlı yol AYNI _dt_ozet_json(p_il,p_kategori,p_tur) fonksiyonunu kullanır.
--
-- MASKE: RPC yalnız AGGREGATE döndürür (idare adları kamu bilgisi; kazanan_firma DÖNMEZ,
--   sadece bedel istatistiği). authenticated'a GRANT, anon'a KAPALI (sayfa Pro-gated).
-- =============================================================================

-- 1) Ortak hesaplayıcı — filtreli/filtresiz TAM DT özetini jsonb üretir.
--    SECURITY DEFINER: tabloyu tam tarayıp yalnız aggregate döndürür (satır sızıntısı yok).
CREATE OR REPLACE FUNCTION public._dt_ozet_json(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL
) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH f AS (
    SELECT dt_no, tur, il, kategori, idare, idare_tur, tarih
    FROM public.dogrudan_temin_ilanlari
    WHERE (p_il IS NULL OR il = p_il)
      AND (p_kategori IS NULL OR kategori = p_kategori)
      AND (p_tur IS NULL OR tur = p_tur)
  ),
  son AS (
    SELECT s.kazanan_bedel
    FROM public.dogrudan_temin_sonuclari s
    JOIN f ON f.dt_no = s.dt_no
    WHERE s.kazanan_bedel > 0
  )
  SELECT jsonb_build_object(
    'toplam',       (SELECT count(*) FROM f),
    'sonuclanan',   (SELECT count(*) FROM son),
    'ort_bedel',    (SELECT round(avg(kazanan_bedel)) FROM son),
    'medyan_bedel', (SELECT round(percentile_cont(0.5) WITHIN GROUP (ORDER BY kazanan_bedel)) FROM son),
    'tur', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
            FROM (SELECT tur AS k, count(*) AS n FROM f WHERE tur IS NOT NULL AND btrim(tur)<>'' GROUP BY tur ORDER BY count(*) DESC LIMIT 10) t),
    'il', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
           FROM (SELECT il AS k, count(*) AS n FROM f WHERE il IS NOT NULL AND btrim(il)<>'' GROUP BY il ORDER BY count(*) DESC LIMIT 15) t),
    'kategori', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT kategori AS k, count(*) AS n FROM f WHERE kategori IS NOT NULL AND btrim(kategori)<>'' GROUP BY kategori ORDER BY count(*) DESC LIMIT 15) t),
    'idare', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
              FROM (SELECT idare AS k, count(*) AS n FROM f WHERE idare IS NOT NULL AND btrim(idare)<>'' GROUP BY idare ORDER BY count(*) DESC LIMIT 12) t),
    'idare_tur', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
                  FROM (SELECT idare_tur AS k, count(*) AS n FROM f WHERE idare_tur IS NOT NULL AND btrim(idare_tur)<>'' GROUP BY idare_tur ORDER BY count(*) DESC LIMIT 12) t),
    'trend', (SELECT coalesce(jsonb_object_agg(ay, n), '{}'::jsonb)
              FROM (SELECT to_char(date_trunc('month', tarih), 'YYYY-MM') AS ay, count(*) AS n
                    FROM f WHERE tarih >= (now() - interval '24 months') GROUP BY 1) t),
    'bedel_bant', (SELECT jsonb_build_object(
        'b0', count(*) FILTER (WHERE kazanan_bedel < 50000),
        'b1', count(*) FILTER (WHERE kazanan_bedel >= 50000    AND kazanan_bedel < 200000),
        'b2', count(*) FILTER (WHERE kazanan_bedel >= 200000   AND kazanan_bedel < 1000000),
        'b3', count(*) FILTER (WHERE kazanan_bedel >= 1000000  AND kazanan_bedel < 5000000),
        'b4', count(*) FILTER (WHERE kazanan_bedel >= 5000000)
      ) FROM son)
  );
$$;

-- 2) MV — filtresiz TAM özet (tek satır). `id=1` sabit kolonu + UNIQUE index: gece
--    REFRESH ... CONCURRENTLY için ŞART (diğer DT MV'leriyle aynı desen, okuma kilidi yok).
DROP MATERIALIZED VIEW IF EXISTS public.dt_analiz_mv;
CREATE MATERIALIZED VIEW public.dt_analiz_mv AS
  SELECT 1 AS id, public._dt_ozet_json(NULL, NULL, NULL) AS ozet;
CREATE UNIQUE INDEX IF NOT EXISTS dt_analiz_mv_pk ON public.dt_analiz_mv (id);

-- 3) Genel RPC — sayfa bunu çağırır. Filtre yoksa MV'den ANINDA; varsa CANLI (timeout bump).
-- Fonksiyon-seviyesi SET statement_timeout: STABLE fonksiyonda gövde içi `SET LOCAL` YASAK
-- ("SET is not allowed in a non-volatile function"). Bunun yerine CREATE ... SET cümlesiyle
-- fonksiyon çağrısı boyunca timeout'u 15s'e çıkarıyoruz (çağıranın ~3s tavanını ezer, filtreli
-- canlı yol emniyeti). MV yolu zaten anında döner.
CREATE OR REPLACE FUNCTION public.dt_analiz_ozet(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = public SET statement_timeout = '15s' AS $$
BEGIN
  IF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL) THEN
    RETURN (SELECT ozet FROM public.dt_analiz_mv);   -- filtresiz: MV'den anında
  END IF;
  RETURN public._dt_ozet_json(p_il, p_kategori, p_tur);  -- filtreli: canlı (küçük alt-küme)
END;
$$;

-- 4) Yetki: fonksiyonlar doğuştan PUBLIC-EXECUTE doğar → temizle, yalnız authenticated'a ver.
--    anon'a KAPALI (dt-analiz.html Pro-gated; rekabet_ozet/kurum_ozet ile aynı maske politikası).
REVOKE ALL ON FUNCTION public._dt_ozet_json(text, text, text) FROM public;
REVOKE ALL ON FUNCTION public.dt_analiz_ozet(text, text, text) FROM public;
GRANT EXECUTE ON FUNCTION public.dt_analiz_ozet(text, text, text) TO authenticated, service_role;
-- _dt_ozet_json doğrudan çağrılmaz (yalnız MV + wrapper kullanır); anon/authenticated'a VERME.

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- GECE REFRESH: dt_analiz_mv filtresiz özeti ~5s'de yeniden hesaplar. Diğer DT MV'leriyle
-- (dt_kategori_sayim_mv, dt_idare_ozet_mv) aynı yere eklenmeli:
--   REFRESH MATERIALIZED VIEW public.dt_analiz_mv;
--
-- DOĞRULAMA (authenticated key ile — anon 403/permission denied almalı):
--   -- Filtresiz (MV, anında):
--   curl -s -X POST https://ihaleglobal.com/rest/v1/rpc/dt_analiz_ozet \
--     -H "apikey: <anon>" -H "Authorization: Bearer <user_jwt>" \
--     -H "Content-Type: application/json" -d '{}'
--   -- Filtreli (canlı):  -d '{"p_il":"ANKARA"}'
-- =============================================================================
