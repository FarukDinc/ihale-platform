-- ilanlar maliyet sıralaması için indeks (23 Tem 2026 — büyüyen tablo timeout'u).
--
-- SORUN: ihaleler.html + dashboard.html "Yak. Maliyet ↓/↑" sıralaması
-- `yaklasik_maliyet_min DESC NULLS LAST` gönderiyor; eşleşen indeks yoktu → Geçmiş sekmesinde
-- (etkin_tarih<now ~1,9M satır) tam sıralama 3s+ → anon timeout (misafirde o sıralama 500).
-- Güncel sekmede sorun yok (son_teklif_tarihi>=now ~4K satır). DT'deki tarih NULLS LAST
-- hatasıyla AYNI SINIF; tablo büyüdükçe daha çok sıralama alanı bu tuzağa düşüyor.
--
-- Ölçüm: Geçmiş+maliyet 3010ms → 106ms; filtresiz 3118ms → 64ms.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_maliyet_nl
    ON public.ilanlar USING btree (yaklasik_maliyet_min DESC NULLS LAST);
