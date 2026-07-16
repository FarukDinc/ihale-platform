-- ============================================================================
-- migration_ozet_mv_paketi.sql — Sayfa-açılışı aggregate'lerinin MV paketi (16 Tem 2026)
--
-- Kök neden (canlıda ölçüldü, kullanıcı "her yer bekletiyor" şikayeti):
-- her sayfa açılışında 355K-529K satır üzerinde CANLI GROUP BY çalışıyordu:
--   sonuc_ozet()        4.0sn  (sonuclananlar açılışı; count DISTINCT kazanan_firma)
--   kategori_sayim()    2.1sn  (sektorler + dashboard)
--   il_sayim()          1.7sn  (ANASAYFA haritası + js/harita.js)
--   il_firma_dagilimi() 1.6sn  (harita + firma-analiz)
--   yuklenici_ozet()    1.6sn  (firmalar + firma-analiz istatistik kartları)
--   il_sektor_ozet()    ~1sn   (bugünkü MV'li hali bile 238K satırı her çağrıda grupluyor)
-- Ayrıca timeout günlerinde RPC hatası sektorler.html'i 256K-satırlık, index.html'i
-- 13-istekli client fallback'ine düşürüyordu (asıl felaket yolu).
--
-- Çözüm (bugün idare_ozet_mv + il_sektor_firma_mv ile kanıtlanan desen):
-- çıktılar minik MV'lerde ÖNCEDEN hesaplanır; RPC'ler AYNI İMZAYLA MV'den okur
-- (frontend değişikliği YOK). Veri yalnız gece scraper turunda değiştiği için
-- run_scraper.sh sonundaki REFRESH zinciri tazeliği korur.
-- Tek satırlık özet MV'lerinde REFRESH CONCURRENTLY'nin kolon-bazlı UNIQUE index
-- şartı için sabit id=1 kolonu var (expression index CONCURRENTLY'ye SAYILMAZ).
-- CREATE OR REPLACE FUNCTION proconfig'i sıfırladığından timeout ALTER'ları
-- fonksiyon tanımlarından SONRA yeniden konur.
--
-- analiz_pivot(text,text,text,text,text,int): parametrik/dinamik olduğundan MV'ye
-- alınamaz → bilinen açık iş (hafıza: statement-timeout-edge) burada kapanır:
-- ALTER SET statement_timeout='20s' (rekabet_ozet deseni; büyük firmada sessiz
-- kaybolan kırılım kartı yavaş-ama-çalışır olur).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ozet_mv_paketi.sql
-- Idempotent. ÖNKOŞUL: il_sektor_firma_mv mevcut olmalı (migration_harita_firma_mv.sql).
-- ============================================================================

-- ── 1) il_sektor_ozet: 238K satırlık MV'yi her çağrıda gruplamak yerine 3.1K'lık mini-MV
CREATE MATERIALIZED VIEW IF NOT EXISTS public.il_sektor_ozet_mv AS
SELECT il, kategori,
       count(*)::bigint      AS firma_adet,
       sum(sozlesme)::bigint AS sozlesme_adet,
       sum(toplam_bedel)     AS toplam_bedel
FROM public.il_sektor_firma_mv
GROUP BY il, kategori;
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_ozet_mv_pk
  ON public.il_sektor_ozet_mv (il, kategori);
GRANT SELECT ON public.il_sektor_ozet_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.il_sektor_ozet()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
           'il', il, 'kategori', kategori, 'firma_adet', firma_adet,
           'sozlesme_adet', sozlesme_adet, 'toplam_bedel', toplam_bedel)), '[]'::jsonb)
  FROM public.il_sektor_ozet_mv;
$$;
ALTER FUNCTION public.il_sektor_ozet() SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_ozet() TO anon, authenticated, service_role;

-- ── 2) kategori_sayim (sektorler + dashboard): ~42 satır
CREATE MATERIALIZED VIEW IF NOT EXISTS public.kategori_sayim_mv AS
SELECT COALESCE(kategori, 'Diğer') AS kategori,
       count(*)::bigint AS toplam,
       (count(*) FILTER (WHERE durum = 'aktif'))::bigint AS aktif
FROM public.ilanlar
GROUP BY COALESCE(kategori, 'Diğer');
CREATE UNIQUE INDEX IF NOT EXISTS idx_kategori_sayim_mv_pk
  ON public.kategori_sayim_mv (kategori);
GRANT SELECT ON public.kategori_sayim_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.kategori_sayim()
RETURNS TABLE (kategori TEXT, toplam BIGINT, aktif BIGINT)
LANGUAGE sql STABLE
AS $$
  SELECT kategori, toplam, aktif
  FROM public.kategori_sayim_mv
  ORDER BY toplam DESC;
$$;

-- ── 3) il_sayim (anasayfa haritası): 81 satır
CREATE MATERIALIZED VIEW IF NOT EXISTS public.il_sayim_mv AS
SELECT il, count(*)::bigint AS adet
FROM public.ilanlar
WHERE il IS NOT NULL
GROUP BY il;
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sayim_mv_pk
  ON public.il_sayim_mv (il);
GRANT SELECT ON public.il_sayim_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.il_sayim()
RETURNS TABLE (il TEXT, adet BIGINT)
LANGUAGE sql STABLE
AS $$
  SELECT il, adet FROM public.il_sayim_mv;
$$;

-- ── 4) il_firma_dagilimi (harita + firma-analiz): 81 satır, kaynak yukleniciler
--     (yukleniciler'i gece yuklenici_yenile doldurur; REFRESH zinciri ondan SONRA koşar)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.il_firma_dagilimi_mv AS
SELECT il, count(*)::bigint AS adet, sum(COALESCE(toplam_ciro, 0)) AS toplam_ciro
FROM public.yukleniciler
WHERE il IS NOT NULL AND btrim(il) <> ''
GROUP BY il;
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_firma_dagilimi_mv_pk
  ON public.il_firma_dagilimi_mv (il);
GRANT SELECT ON public.il_firma_dagilimi_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.il_firma_dagilimi()
RETURNS TABLE (il text, adet bigint, toplam_ciro numeric)
LANGUAGE sql STABLE
AS $$
  SELECT il, adet, toplam_ciro FROM public.il_firma_dagilimi_mv;
$$;

-- ── 5) yuklenici_ozet (firmalar istatistik kartları): tek satır
CREATE MATERIALIZED VIEW IF NOT EXISTS public.yuklenici_ozet_mv AS
SELECT 1 AS id,
       count(*)::bigint AS toplam,
       sum(COALESCE(toplam_sozlesme_sayisi, 0)) AS toplam_sozlesme,
       sum(COALESCE(toplam_ciro, 0)) AS toplam_ciro,
       (count(*) FILTER (WHERE ortak_girisim IS TRUE))::bigint AS ortak_sayisi
FROM public.yukleniciler;
CREATE UNIQUE INDEX IF NOT EXISTS idx_yuklenici_ozet_mv_pk
  ON public.yuklenici_ozet_mv (id);
GRANT SELECT ON public.yuklenici_ozet_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.yuklenici_ozet()
RETURNS TABLE (toplam bigint, toplam_sozlesme numeric, toplam_ciro numeric, ortak_sayisi bigint)
LANGUAGE sql STABLE
AS $$
  SELECT toplam, toplam_sozlesme, toplam_ciro, ortak_sayisi FROM public.yuklenici_ozet_mv;
$$;

-- ── 6) sonuc_ozet (sonuclananlar istatistik kartları — 4sn'lik şampiyon): tek satır
CREATE MATERIALIZED VIEW IF NOT EXISTS public.sonuc_ozet_mv AS
SELECT 1 AS id,
       count(*)::bigint AS toplam,
       sum(COALESCE(kazanan_teklif, sozlesme_bedeli)) AS toplam_bedel,
       round(avg(kazanan_teklif_farki_yuzde)
             FILTER (WHERE kazanan_teklif_farki_yuzde IS NOT NULL
                       AND abs(kazanan_teklif_farki_yuzde) <= 100), 1) AS ort_tenzilat,
       count(DISTINCT kazanan_firma)::bigint AS farkli_firma
FROM public.ihale_sonuclari
WHERE kazanan_firma IS NOT NULL AND kazanan_firma <> '';
CREATE UNIQUE INDEX IF NOT EXISTS idx_sonuc_ozet_mv_pk
  ON public.sonuc_ozet_mv (id);
GRANT SELECT ON public.sonuc_ozet_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.sonuc_ozet()
RETURNS TABLE (toplam bigint, toplam_bedel numeric, ort_tenzilat numeric, farkli_firma bigint)
LANGUAGE sql STABLE
AS $$
  SELECT toplam, toplam_bedel, ort_tenzilat, farkli_firma FROM public.sonuc_ozet_mv;
$$;

-- ── 7) analiz_pivot: büyük firmalarda 57014 → rekabet_ozet deseniyle timeout payı
ALTER FUNCTION public.analiz_pivot(text, text, text, text, text, int)
  SET statement_timeout = '20s';

ANALYZE public.il_sektor_ozet_mv, public.kategori_sayim_mv, public.il_sayim_mv,
        public.il_firma_dagilimi_mv, public.yuklenici_ozet_mv, public.sonuc_ozet_mv;

NOTIFY pgrst, 'reload schema';

-- Kontrol
SELECT (SELECT count(*) FROM public.il_sektor_ozet_mv)   AS ozet_grup,
       (SELECT count(*) FROM public.kategori_sayim_mv)   AS kategori,
       (SELECT count(*) FROM public.il_sayim_mv)         AS il,
       (SELECT count(*) FROM public.il_firma_dagilimi_mv) AS il_firma,
       (SELECT toplam FROM public.yuklenici_ozet_mv)     AS yuklenici_toplam,
       (SELECT toplam FROM public.sonuc_ozet_mv)         AS sonuc_toplam;
SELECT * FROM public.kategori_sayim() LIMIT 3;
SELECT * FROM public.sonuc_ozet();
