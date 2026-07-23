-- DT liste sıralaması için tarih DESC NULLS LAST indeksi (23 Tem 2026 — CANLI HATA düzeltmesi).
--
-- SORUN: dogrudan-temin.html `.order('tarih', {ascending:false, nullsFirst:false})` gönderiyor
-- = `tarih DESC NULLS LAST`. Mevcut indeks `idx_dt_ilanlari_tarih` ise `tarih DESC` (=NULLS FIRST).
-- NULLS konumu uyuşmadığı için planlayıcı indeksi KULLANAMIYOR → 2M satır Parallel Seq Scan + Sort
-- = 4485ms. Anon statement_timeout 3s → 57014, MİSAFİRDE DT SAYFASI "0 kayıt" gösteriyordu.
-- (2024 backfill tabloyu 1,5M→2,08M büyütünce süre 3s eşiğini aştı; sinsi biçimde canlıya çıktı.)
--
-- Aynı NULLS FIRST/LAST hata sınıfı daha önce ilanlar Sonuç sekmesinde de yaşandı.
--
-- ÇÖZÜM: sorguyla BİREBİR eşleşen indeks. Ölçüm: 4485ms → 1,3ms (index scan), REST 0,17sn.
-- CONCURRENTLY: backfill yazarken tabloyu kilitlemesin (bu dosya migration olarak da tutulur;
-- CONCURRENTLY transaction bloğunda çalışmaz, tek başına koşturulmalı).
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_tarih_nl
    ON public.dogrudan_temin_ilanlari USING btree (tarih DESC NULLS LAST);
