-- ============================================================================
-- migration_uygun_firmalar_v3_1.sql (17 Tem 2026) — v3 devamı, 3 iş:
--
--  1) PERFORMANS: tr_fold(baslik) üzerinde trigram GIN indeksi.
--     v3'ün konu-kelimesi eşleşmesi (tr_fold(baslik) LIKE '%gida%') indekssiz seq
--     scan yapıyor; authenticated rolün ~3s statement_timeout'unda ölebilir
--     (bilinen kalıp: timeout bump değil İFADE İNDEKSİ çözer — analiz_pivot dersi).
--     Şüphe: ihale-detay'da "Uygun Firmalar" kutusunun hiç görünmemesi.
--
--  2) benzer_ihaleler: AÇIK İHALE ŞARTI — son teklif tarihi geçmiş aday elenir
--     (son_teklif NULL ise kalır: yargılanamaz). Canlı doğrulamada 4/4 benzerin
--     tarihi geçmişti; davet otomasyonu kapalı ihaleye davet atamaz.
--
--  3) ilan_durum_bayatlat(): son teklif tarihi geçmiş 'aktif' ilanları 'kapandi'
--     yapar (gece cron, run_scraper.sh — TÜM scraperlardan SONRA koşmalı çünkü
--     jandarma/dmo/ilan_gov upsert'leri durum:'aktif' ile ESKİ kaydı yeniden
--     açabiliyor; cron sonunda bayatlama net durumu düzeltir). 'kapandi' değeri
--     kurum_ozet'in "aktif olmayan" sözleşmesiyle uyumlu; detay rozeti zaten
--     gun<0'da "Kapandı" gösteriyor. Sonuç gelirse ekap_sonuc_backfill
--     'sonuclandi'ya çevirir (kapandi → sonuclandi geçişi doğal).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_uygun_firmalar_v3_1.sql
-- İdempotent. NOT: CREATE INDEX ilk seferde tablo boyutuna göre 1-2 dk sürebilir.
-- ============================================================================

-- ── 1) Konu-eşleşmesi indeksi ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ilanlar_baslik_fold_trgm
  ON public.ilanlar USING gin (tr_fold(baslik) gin_trgm_ops);

ANALYZE public.ilanlar;

-- ── 2) benzer_ihaleler: açık ihale şartı (imza aynı, gövde güncel) ─────────
CREATE OR REPLACE FUNCTION public.benzer_ihaleler(
  p_id       uuid,
  p_kategori text    DEFAULT NULL,
  p_bedel    numeric DEFAULT NULL,
  p_limit    int     DEFAULT 4,
  p_bant     numeric DEFAULT 5
)
RETURNS TABLE (
  id                   uuid,
  baslik               text,
  il                   text,
  yaklasik_maliyet_min numeric,
  yaklasik_maliyet_max numeric,
  tahmini_bedel        numeric,
  son_teklif_tarihi    timestamptz,
  kategori             text,
  benzerlik            numeric
)
LANGUAGE sql STABLE
AS $$
  WITH src AS (
    SELECT i.baslik, i.il, i.embedding
    FROM public.ilanlar i
    WHERE i.id = p_id
  ),
  aday AS (
    SELECT
      i.id            AS a_id,
      i.baslik        AS a_baslik,
      i.il            AS a_il,
      i.yaklasik_maliyet_min::numeric AS a_min,
      i.yaklasik_maliyet_max::numeric AS a_max,
      i.tahmini_bedel::numeric AS a_tahmini,
      i.son_teklif_tarihi::timestamptz AS a_son,
      i.kategori      AS a_kategori,
      i.embedding     AS a_emb,
      COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
               NULLIF(i.tahmini_bedel, 0))              AS a_bedel,
      s.baslik        AS s_baslik,
      s.il            AS s_il,
      s.embedding     AS s_emb
    FROM public.ilanlar i
    CROSS JOIN src s
    WHERE i.durum = 'aktif'
      AND i.id <> p_id
      -- AÇIK İHALE ŞARTI: son teklif tarihi geçmişse gösterme (durum bayat kalmış
      -- olabilir — bkz. ilan_durum_bayatlat). Tarihi NULL olan kalır.
      AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
      -- KONU eşleşmesi ŞART: kanonik kategori VEYA başlık kelimesi VEYA semantik
      -- yakınlık. Üçü de yoksa sonuç BOŞ döner (dayanak yoksa gösterme kuralı) —
      -- jenerik kategori/tür doldurması YOK.
      AND ( (p_kategori IS NOT NULL AND i.kategori = p_kategori)
         OR EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(s.baslik) t
                    WHERE tr_fold(i.baslik) LIKE '%' || t.kelime || '%')
         OR (s.embedding IS NOT NULL AND i.embedding IS NOT NULL
             AND (i.embedding <=> s.embedding) < 0.45) )
      -- ÖLÇEK BANDI ŞART: aday bedeli biliniyorsa bant dışıysa ELENİR
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
                       NULLIF(i.tahmini_bedel, 0)) IS NULL
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
                       NULLIF(i.tahmini_bedel, 0))
              BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
  )
  SELECT
    a.a_id, a.a_baslik, a.a_il, a.a_min, a.a_max, a.a_tahmini, a.a_son, a.a_kategori,
    round((
      (CASE WHEN a.s_emb IS NOT NULL AND a.a_emb IS NOT NULL
            THEN (1 - (a.a_emb <=> a.s_emb)) * 60
            ELSE similarity(tr_fold(a.a_baslik), tr_fold(a.s_baslik)) * 60 END)
      + (CASE WHEN p_kategori IS NOT NULL AND a.a_kategori = p_kategori THEN 15 ELSE 0 END)
      + (CASE WHEN a.a_il = a.s_il THEN 8 ELSE 0 END)
      + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
              WHEN a.a_bedel IS NULL THEN -5
              ELSE 10 * (1 - LEAST(abs(ln(GREATEST(a.a_bedel, 1) / p_bedel)) / ln(p_bant), 1)) END)
    )::numeric, 1) AS benzerlik
  FROM aday a
  ORDER BY benzerlik DESC
  LIMIT p_limit;
$$;

-- (CREATE OR REPLACE mevcut ACL'leri korur; yine de açıkça sabitle)
REVOKE EXECUTE ON FUNCTION public.benzer_ihaleler(uuid, text, numeric, int, numeric) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.benzer_ihaleler(uuid, text, numeric, int, numeric) TO anon, authenticated, service_role;

-- ── 3) Durum bayatlama (gece cron) ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ilan_durum_bayatlat()
RETURNS bigint
LANGUAGE sql VOLATILE
AS $$
  WITH kapat AS (
    UPDATE public.ilanlar
       SET durum = 'kapandi'
     WHERE durum = 'aktif'
       AND son_teklif_tarihi IS NOT NULL
       AND son_teklif_tarihi < now()
    RETURNING 1
  )
  SELECT count(*) FROM kapat;
$$;

-- Yalnız bakım/cron içindir — API rollerinden çağrılamaz
REVOKE EXECUTE ON FUNCTION public.ilan_durum_bayatlat() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ilan_durum_bayatlat() TO service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM ilanlar WHERE durum='aktif' AND son_teklif_tarihi < now();  -- bayat sayısı
--   SELECT public.ilan_durum_bayatlat();                                             -- kapatır, sayıyı döner
--   SELECT baslik, il, son_teklif_tarihi, benzerlik
--     FROM benzer_ihaleler('5a450f6d-92ff-4d16-ba56-6fcddbb355c3', NULL, 809000, 4);
--     -- artık yalnız son teklifi GEÇMEMİŞ (veya tarihi bilinmeyen) gıda ihaleleri
--   EXPLAIN ANALYZE SELECT * FROM ihaleye_uygun_firmalar(NULL,'ANKARA',809000,8,'10 KISIM 13 KALEM GIDA MADDESİ');
--     -- idx_ilanlar_baslik_fold_trgm kullanmalı, toplam süre < 1s olmalı
