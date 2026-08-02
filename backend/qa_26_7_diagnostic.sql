-- ============================================================================
-- qa_26_7_diagnostic.sql — 26-7/UV-4 idare ad-ortası boşluk TEŞHİSİ (READ-ONLY)
--   (2 Ağu 2026). idare adları EKAP KAYNAĞINDA sabit-genişlik wrap boşluğuyla bozuk
--   ("ANFA ANKARA ALTINPAR K İŞL.LTD.ŞTİ."). Kör boşluk-silme meşru boşlukları bozar →
--   önce GÜVENLİ dedup sinyali: boşluksuz-folded aynı ama ham farklı = bozuk↔temiz çift.
--   SADECE SELECT. Çıktıyı Claude'a yapıştır → remap stratejisi tasarlanacak.
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/qa_26_7_diagnostic.sql
-- ============================================================================
\pset pager off

\echo '=== 26-7a: boşluksuz-folded AYNI, ham FARKLI idare varyantları (bozuk↔temiz çiftler) ==='
WITH n AS (
  SELECT DISTINCT idare, regexp_replace(public.tr_fold(idare), '\s', '', 'g') AS anahtar
    FROM public.ilanlar WHERE idare IS NOT NULL AND idare <> ''
)
SELECT anahtar, count(*) AS varyant_sayisi, string_agg(idare, '  ||  ' ORDER BY length(idare)) AS varyantlar
  FROM n GROUP BY anahtar HAVING count(*) > 1
 ORDER BY varyant_sayisi DESC, anahtar LIMIT 40;

\echo ''
\echo '=== 26-7b: kaç anahtar birden çok varyanta sahip (toplam etki) ==='
WITH n AS (
  SELECT DISTINCT idare, regexp_replace(public.tr_fold(idare), '\s', '', 'g') AS anahtar
    FROM public.ilanlar WHERE idare IS NOT NULL AND idare <> ''
)
SELECT count(*) AS coklu_varyant_anahtar,
       sum(v-1) AS birlestirilebilir_fazla_varyant
  FROM (SELECT anahtar, count(*) v FROM n GROUP BY anahtar HAVING count(*)>1) x;

\echo ''
\echo '=== 26-7c: mid-word tek-büyük-harf token içeren idare örnekleri (wrap imzası) ==='
SELECT DISTINCT idare FROM public.ilanlar
 WHERE idare ~ '[a-zçğıöşü] [A-ZÇĞİÖŞÜ] ' OR idare ~ ' [A-ZÇĞİÖŞÜ] [a-zçğıöşü]'
 ORDER BY idare LIMIT 25;

\echo ''
\echo '=== 26-7d: aynı sorun DT tarafında (dogrudan_temin_ilanlari.idare) ==='
WITH n AS (
  SELECT DISTINCT idare, regexp_replace(public.tr_fold(idare), '\s', '', 'g') AS anahtar
    FROM public.dogrudan_temin_ilanlari WHERE idare IS NOT NULL AND idare <> ''
)
SELECT count(*) AS coklu_varyant_anahtar_dt
  FROM (SELECT anahtar FROM n GROUP BY anahtar HAVING count(*)>1) x;
