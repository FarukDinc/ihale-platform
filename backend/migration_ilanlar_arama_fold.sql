-- ============================================================================
-- migration_ilanlar_arama_fold.sql
-- 10. bug (14 Tem tespit): ihaleler.html ANA arama sunucu-side ILIKE Turkce
-- karakter katlamiyor. Kullanici "insaat" yazinca "INSAAT/insaat" iceren ~2000
-- ihalenin HICBIRI donmuyor (ampirik: baslik ILIKE %insaat% -> 0,
-- %INSAAT% -> 1998).
--
-- COZUM: frontend trFold() ile BIREBIR ayni katlamayi yapan IMMUTABLE bir SQL
-- fonksiyonu (tr_fold) + katlanmis birlesik arama kolonu (arama_fold, generated
-- STORED) + pg_trgm GIN indeks. Frontend arama terimini de trFold'layip
-- arama_fold uzerinde ILIKE ile sorgular. Boylece her iki taraf da ayni
-- normal forma indirgenir, eslesme dogru olur.
--
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrar calistirmak zararsiz.
--
-- ┌─ DIKKAT (STORAGE) ────────────────────────────────────────────────────────┐
-- │ arama_fold, ilan_metni (~ort 6.7KB/satir) dahil 5 alani birlestirir.       │
-- │ ~90K satir icin: generated kolon ~+600MB tablo, trigram GIN indeks ~1-2GB. │
-- │ VDS diski (158G) icin sorun degil ama CREATE INDEX birkac dk surer + ADD   │
-- │ COLUMN GENERATED tabloyu bir kez yeniden yazar (kisa ACCESS EXCLUSIVE lock).│
-- │ Gunduz calistirilmali (gece 02:00 UTC scraper turundan once/sonra degil).  │
-- └────────────────────────────────────────────────────────────────────────────┘
-- ============================================================================

-- 1) Trigram eklentisi (leading-wildcard %x% ILIKE'i indeksleyebilmek icin)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2) Turkce katlama fonksiyonu — frontend trFold() ile BIREBIR:
--    I/I/i -> i, S/s -> s, G/g -> g, U/u -> u, O/o -> o, C/c -> c, sonra lower().
--    translate() ile 1:1 karakter esleme (kesin IMMUTABLE), ardindan lower().
--    Turkce ozel harfler translate ile onceden katlandigi icin lower()'in
--    locale-bagimli I/i davranisi devreye girmez -> JS toLowerCase ile ozdes.
CREATE OR REPLACE FUNCTION tr_fold(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT lower(translate(coalesce(s, ''),
    'İIıŞşĞğÜüÖöÇç',
    'iiissgguuoocc'));
$$;

-- 3) Birlesik katlanmis arama kolonu (generated STORED).
--    Frontend arama .or(baslik,idare,okas,isin_yapilacagi_yer,ilan_metni) ile
--    tam paritede kalmasi icin ayni 5 alan birlestiriliyor.
ALTER TABLE ilanlar
  ADD COLUMN IF NOT EXISTS arama_fold text
  GENERATED ALWAYS AS (
    tr_fold(
      coalesce(baslik, '')              || ' ' ||
      coalesce(idare, '')               || ' ' ||
      coalesce(okas, '')                || ' ' ||
      coalesce(isin_yapilacagi_yer, '') || ' ' ||
      coalesce(ilan_metni, '')
    )
  ) STORED;

-- 4) Trigram GIN indeks — arama_fold ILIKE '%terim%' hizli calissin.
--    CONCURRENTLY DEGIL: bu dosya psql ile tek transaction disinda calisir,
--    ADD COLUMN zaten tabloyu yeniden yazdigindan ekstra concurrency kazanci yok.
CREATE INDEX IF NOT EXISTS idx_ilanlar_arama_fold_trgm
  ON ilanlar USING gin (arama_fold gin_trgm_ops);

-- 5) PostgREST sema onbellegini tazele (yeni kolon anon/authenticated'a gorunsun;
--    kolon tablonun mevcut SELECT grant'ini miras alir, ek grant gerekmez).
NOTIFY pgrst, 'reload schema';

-- Dogrulama (elle):
--   SELECT tr_fold('İNŞAAT'), tr_fold('Prefabrik BİNA');  -- -> 'insaat', 'prefabrik bina'
--   SELECT count(*) FROM ilanlar WHERE arama_fold ILIKE '%insaat%';  -- ~1998+ olmali
