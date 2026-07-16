-- Denetim #7: kurum-analiz.html (+ idareler) ilanlar.idare üzerinde çift-joker ILIKE yapıyor ama index yoktu
-- → her kurum görüntülemede 256K satır full seq scan. Trigram GIN index ILIKE'ı indexlenebilir yapar.
-- (pg_trgm zaten arama_fold için etkin.) Not: client-side yükleme (idare'nin tüm ilanları) hâlâ var ama
-- idare boyutuyla sınırlı; ideal tam çözüm çok-boyutlu breakdown RPC (ertelendi).
CREATE INDEX IF NOT EXISTS idx_ilanlar_idare_trgm
  ON public.ilanlar USING gin (idare gin_trgm_ops);
ANALYZE public.ilanlar;
