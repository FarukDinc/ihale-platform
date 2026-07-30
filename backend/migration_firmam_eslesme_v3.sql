-- ============================================================
-- MADDE 6 (v3) — Eşleşme sıralaması: KATMANLI sektör-öncelikli (31 Tem 2026)
-- ------------------------------------------------------------
-- KULLANICI: "daha önce iş aldığım il doğru referans değil" (firma çok ilde çalışmışsa hep
--   tutuyor → gürültü). Sıralama SEKTÖR bazlı olmalı. Öncelik:
--     Sektör+Kurum > Sektör+İl > Sektör > Kurum > İl.
-- ÇÖZÜM: KESİN KATMAN skoru — sektör 100, kurum(idare) 30, il 10 → toplamlar katmanları
--   çakışmadan verir (130/110/100/30/10). Bedel-yakınlığı ARTIK sıralama katmanı DEĞİL,
--   yalnız AYNI katman içinde ikincil tiebreaker (ln oranı). ±%500 hard bant KALDIRILDI
--   (sektör-öncelik istendiği için; uygunsuz ölçek zaten tiebreaker'da dibe düşer).
-- Sektör = kategori EŞLEŞMESİ VEYA başlık konu-kelimesi (yanlış sınıflanmış ilanları da yakalar).
-- İl gerekçede YALNIZ tek sinyalse gösterilir (sektör matchlerinde il etiketi kalkar).
--
-- İmza AYNI → CREATE OR REPLACE, frontend değişmez.
-- Çalıştır (mevcut fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firmam_eslesme_v3.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_icin_acik_ihaleler(
  p_yuklenici_id uuid, p_limit int DEFAULT 12, p_bant numeric DEFAULT 3)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE AS $$
  WITH firma AS (
    SELECT
      (SELECT array_agg(k) FROM (
         SELECT i.kategori k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL
         GROUP BY i.kategori ORDER BY count(*) DESC LIMIT 5) t)          AS kategoriler,
      (SELECT array_agg(DISTINCT i.il) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.il IS NOT NULL)       AS iller,
      (SELECT array_agg(k) FROM (
         SELECT i.idare k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.idare IS NOT NULL
         GROUP BY i.idare ORDER BY count(*) DESC LIMIT 8) t)             AS idareler,
      (SELECT string_agg(i2.baslik,' ') FROM (
         SELECT i3.baslik FROM public.ihale_sonuclari s2 JOIN public.ilanlar i3 ON i3.id=s2.ilan_id
         WHERE s2.yuklenici_id=p_yuklenici_id LIMIT 50) i2)              AS basliklar,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))
         FROM public.ihale_sonuclari s WHERE s.yuklenici_id=p_yuklenici_id) AS bedel
  ),
  aday AS (
    SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
           i.yaklasik_maliyet_min, i.yaklasik_maliyet_max, i.tahmini_bedel, i.son_teklif_tarihi,
           (i.kategori = ANY(f.kategoriler))                                          AS m_kat,
           EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(f.basliklar) t
                   WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%')            AS m_kelime,
           (f.idareler IS NOT NULL AND i.idare = ANY(f.idareler))                     AS m_idare,
           (i.il = ANY(f.iller))                                                      AS m_il,
           f.bedel AS fbedel
    FROM public.ilanlar i, firma f
    WHERE i.durum='aktif'
      AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
      AND ( i.kategori = ANY(f.kategoriler)
         OR (f.idareler IS NOT NULL AND i.idare = ANY(f.idareler))
         OR i.il = ANY(f.iller)
         OR EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(f.basliklar) t
                    WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%') )
  )
  SELECT id, baslik, idare, il, kategori,
         yaklasik_maliyet_min::numeric, yaklasik_maliyet_max::numeric, tahmini_bedel::numeric,
         son_teklif_tarihi::timestamptz,
         ( (CASE WHEN m_kat OR m_kelime THEN 100 ELSE 0 END)
         + (CASE WHEN m_idare THEN 30 ELSE 0 END)
         + (CASE WHEN m_il    THEN 10 ELSE 0 END) )::numeric                          AS skor,
         NULLIF(concat_ws(' · ',
           CASE WHEN m_kat OR m_kelime THEN 'Uzmanlık alanınız' END,
           CASE WHEN m_idare THEN 'sık çalıştığınız idare' END,
           CASE WHEN m_il AND NOT (m_kat OR m_kelime) AND NOT m_idare THEN 'çalıştığınız il' END
         ), '')                                                                        AS eslesme_nedeni
  FROM aday
  ORDER BY
    ( (CASE WHEN m_kat OR m_kelime THEN 100 ELSE 0 END)
    + (CASE WHEN m_idare THEN 30 ELSE 0 END)
    + (CASE WHEN m_il THEN 10 ELSE 0 END) ) DESC,
    -- aynı katman içinde: bedel-yakınlığı (0-1) yüksek olan önce
    (CASE WHEN fbedel IS NULL OR fbedel<=0 THEN 0
          ELSE 1 - LEAST(abs(ln(GREATEST(
                 COALESCE(NULLIF(yaklasik_maliyet_max,0),NULLIF(tahmini_bedel,0),1),1)::numeric/fbedel))
                 /ln(GREATEST(p_bant,1.0001)),1) END) DESC,
    son_teklif_tarihi ASC NULLS LAST
  LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT baslik, kategori, skor, eslesme_nedeni FROM firma_icin_acik_ihaleler(
--     (SELECT id FROM yukleniciler WHERE ad ILIKE '%ÜNTES%' LIMIT 1), 8, 3);
