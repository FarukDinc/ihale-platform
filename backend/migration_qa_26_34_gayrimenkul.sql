-- ============================================================================
-- migration_qa_26_34_gayrimenkul.sql — 26-34: kategori misassignment (irtifak/taşınmaz → İnşaat)
--   (2 Ağu 2026). Sınıflandırıcı "…tesis edilecektir" gibi kelimeler yüzünden taşınmaz
--   irtifak/kira/satış ihalelerini İnşaat'a atıyordu. Kod tarafı düzeltildi
--   (kategori_siniflandir.py yüksek öncelik ön-kontrol). Bu migration MEVCUT açık-net
--   yanlış kayıtları düzeltir: İnşaat etiketli + tür Kiraya Verme/Satış + başlıkta
--   irtifak/intifa VEYA taşınmaz+(kira|satış|tahsis). tr_fold ile locale-güvenli (İ/ı tuzağı yok).
--   Hedefli + dar → yanlış-pozitif düşük. Idempotent (düzelenler artık İnşaat değil).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_34_gayrimenkul.sql
-- ============================================================================
\pset pager off
\echo '26-34: reklasifiye edilecek (İnşaat -> Gayrimenkul) kayıt sayısı:'
SELECT count(*) FROM public.ilanlar
 WHERE kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
   AND tur IN ('Kiraya Verme','Satış')
   AND ( public.tr_fold(baslik) LIKE '%irtifak%'
      OR public.tr_fold(baslik) LIKE '%intifa hakki%'
      OR ( public.tr_fold(baslik) LIKE '%tasinmaz%'
           AND ( public.tr_fold(baslik) LIKE '%kira%' OR public.tr_fold(baslik) LIKE '%satis%'
              OR public.tr_fold(baslik) LIKE '%tahsis%' ) ) );

UPDATE public.ilanlar SET kategori = 'Gayrimenkul - Arsa Satışı - Kantin'
 WHERE kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
   AND tur IN ('Kiraya Verme','Satış')
   AND ( public.tr_fold(baslik) LIKE '%irtifak%'
      OR public.tr_fold(baslik) LIKE '%intifa hakki%'
      OR ( public.tr_fold(baslik) LIKE '%tasinmaz%'
           AND ( public.tr_fold(baslik) LIKE '%kira%' OR public.tr_fold(baslik) LIKE '%satis%'
              OR public.tr_fold(baslik) LIKE '%tahsis%' ) ) );

\echo '--- KONTROL: örnek (artık Gayrimenkul olmalı) ---'
SELECT kategori, tur, left(baslik,55) baslik FROM public.ilanlar
 WHERE tur IN ('Kiraya Verme','Satış') AND public.tr_fold(baslik) LIKE '%irtifak%' LIMIT 8;
