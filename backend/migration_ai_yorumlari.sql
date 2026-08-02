-- ============================================================
-- ai_yorumlari — AI Yorum Modülü cache (1 Ağu 2026)
-- ------------------------------------------------------------
-- Grounded AI yorumları (kurum/firma/ihale) için CACHE. TUTARLILIK ilkesi: yorum, grounding
-- verisinin HASH'iyle saklanır → veri değişmedikçe AYNI yorum döner (aynı kullanıcı hep aynı
-- yorumu görür + AI maliyeti yok). Hash materyal-değişimde döner (kaba imza: hacim kovası +
-- tekrar-kazananlar + usul), gece küçük dalgalanmada YENİDEN üretmez.
-- anon-KAPALI (premium/kredili özellik). API service_role ile okur/yazar.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_yorumlari (
  varlik_tip     text NOT NULL,        -- 'kurum' | 'firma' | 'ihale'
  varlik_anahtar text NOT NULL,        -- kurum: idare adı · firma: normalize_ad · ihale: ilan id
  yorum          text,
  veri_hash      text,
  uretildi       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (varlik_tip, varlik_anahtar)
);

-- anon GÖRMESİN (premium). authenticated de doğrudan okumasın — yorum API (service_role) üzerinden gider.
REVOKE ALL ON public.ai_yorumlari FROM anon, authenticated;
GRANT ALL ON public.ai_yorumlari TO service_role;

-- RLS aç + hiçbir anon/authenticated policy yok → yalnız service_role erişir (kredili endpoint).
ALTER TABLE public.ai_yorumlari ENABLE ROW LEVEL SECURITY;
