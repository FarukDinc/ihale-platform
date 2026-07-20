-- =============================================================================
-- migration_rfq_bayat.sql — Backlog #23 (20 Tem 2026)
-- Süresi dolan RFQ'lar sonsuza dek "açık" görünüyor (doğrudan kullanıcı şikâyeti).
--
-- SORUN: satinalma_talepleri.durum kolonu MANUEL ('acik'|'kapali'|'iptal') — alıcı
-- kazanan seçmedikçe 'acik' kalır. son_teklif_tarihi geçse bile hiçbir iş bu
-- kolonu bayatlatmıyor. Sonuç: haritanın "Açık RFQ" sayacı, il pinleri, tooltip'i
-- ve il panelindeki "açık RFQ'lar" listesi süresi dolmuş talepleri açık sayıyordu.
--
-- ⚠️ TUZAK — son_teklif_tarihi NULLABLE:
--   Çıplak `son_teklif_tarihi >= now()` yazmak NULL satırları SESSİZCE eler
--   (NULL >= now() → NULL → WHERE'de false). Süresiz/tarih girilmemiş RFQ'lar
--   haritadan tamamen kaybolurdu. Doğru kalıp her yerde:
--       (son_teklif_tarihi IS NULL OR son_teklif_tarihi >= now())
--   Aynı kural frontend'de PostgREST diliyle:
--       .or('son_teklif_tarihi.gte.<nowIso>,son_teklif_tarihi.is.null')
--   (ozel-ihaleler.html "Güncel" sekmesi zaten bu kalıptaydı — tek doğru yüzey oydu;
--    harita ve il_rfq_dagilimi ona hizalanıyor.)
--
-- NEDEN durum KOLONUNU UPDATE ETMİYORUZ: "bayat" zamana bağlı bir türev; gece
-- UPDATE'i iki çalıştırma arasında yine yanlış gösterir ve alıcının kendi
-- 'kapali' kararını ezme riski taşır. Türev daima sorgu anında hesaplanır.
-- (bkz. migration_il_sayim_aktif.sql — aynı gerekçeyle MV değil canlı sorgu.)
-- =============================================================================

-- 1) il_rfq_dagilimi — harita choropleth + pin + "Açık RFQ" KPI'sinin tek kaynağı.
--    İmza DEĞİŞMİYOR (p_kategori text DEFAULT NULL); CREATE OR REPLACE ile gövde
--    güncelleniyor, frontend çağrıları (parametresiz ve p_kategori'li) bozulmaz.
CREATE OR REPLACE FUNCTION public.il_rfq_dagilimi(p_kategori text DEFAULT NULL)
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT il, count(*)::bigint
  FROM public.satinalma_talepleri
  WHERE durum = 'acik'
    AND (son_teklif_tarihi IS NULL OR son_teklif_tarihi >= now())  -- ⚠️ NULL-güvenli
    AND il IS NOT NULL AND btrim(il) <> ''
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY il;
$$;

-- Yetki: önce PUBLIC'ten temizle, sonra dar GRANT (varsayılan ayrıcalık yüzünden
-- fonksiyonlar doğuştan PUBLIC-EXECUTE doğar). anon erişimi KORUNUYOR — harita
-- misafire açık ve dönen alanlar (il, adet) maskeli kolon içermiyor.
REVOKE ALL     ON FUNCTION public.il_rfq_dagilimi(text) FROM public;
GRANT  EXECUTE ON FUNCTION public.il_rfq_dagilimi(text) TO anon, authenticated, service_role;

-- 2) "Açık + süresi dolmamış" taraması için indeks. Tablo bugün küçük ama filtre
--    artık her harita yüklemesinde ve e-Satınalma köprü rozetinde koşuyor.
--    Partial DEĞİL: son_teklif_tarihi IS NULL satırları da kapsamalı.
CREATE INDEX IF NOT EXISTS idx_satinalma_durum_son_teklif
  ON public.satinalma_talepleri (durum, son_teklif_tarihi);

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA (uygulamadan sonra, ANON key ile):
--   -- Süresi dolmuş RFQ artık dağılımda YOK, tarihsiz olan HÂLÂ VAR:
--   curl -s -X POST https://ihaleglobal.com/rest/v1/rpc/il_rfq_dagilimi \
--     -H "apikey: <anon>" -H "Content-Type: application/json" -d '{}'
--   -- SQL tarafı çapraz kontrol (service ile):
--   SELECT durum,
--          count(*) FILTER (WHERE son_teklif_tarihi IS NULL)              AS tarihsiz,
--          count(*) FILTER (WHERE son_teklif_tarihi >= now())             AS suresi_var,
--          count(*) FILTER (WHERE son_teklif_tarihi <  now())             AS bayat
--     FROM public.satinalma_talepleri GROUP BY durum;
--   -- "bayat" sütunundaki durum='acik' satırları artık haritada sayılmamalı;
--   -- "tarihsiz" satırlar sayılmaya DEVAM etmeli (NULL tuzağı regresyon testi).
--
-- FRONTEND EŞLENİĞİ (bu migration'la birlikte gider):
--   harita.html          — il paneli "açık RFQ'lar" listesine NULL-güvenli filtre,
--                          ilike → eq-listesi (önlem; gözlenmiş hata değil), ?katman=rfq
--   ozel-ihaleler.html   — kapalı/bayat kayıt "● Açık" basmıyor + harita köprüsü
--   ihalelerim.html      — "Açtıklarım" kartında "⏹ Süresi doldu" rozeti
-- =============================================================================
