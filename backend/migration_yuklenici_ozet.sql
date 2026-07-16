-- firmalar.html server-side rewrite için: 35K yukleniciler artık client'a inmesin.
-- Global özet (istatistik kartları) tek RPC'de; sıralama kolonlarına index.
CREATE OR REPLACE FUNCTION public.yuklenici_ozet()
RETURNS TABLE(toplam bigint, toplam_sozlesme numeric, toplam_ciro numeric, ortak_sayisi bigint)
LANGUAGE sql STABLE
AS $$
  SELECT count(*)::bigint,
         sum(COALESCE(toplam_sozlesme_sayisi, 0)),
         sum(COALESCE(toplam_ciro, 0)),
         count(*) FILTER (WHERE ortak_girisim IS TRUE)::bigint
  FROM public.yukleniciler;
$$;
GRANT EXECUTE ON FUNCTION public.yuklenici_ozet() TO anon, authenticated, service_role;

-- Sıralama/filtre indexleri (ORDER BY + LIMIT'i seq-scan+sort'tan kurtarır)
CREATE INDEX IF NOT EXISTS idx_yuk_ciro     ON public.yukleniciler (toplam_ciro DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_yuk_sozlesme ON public.yukleniciler (toplam_sozlesme_sayisi DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_yuk_sontarih ON public.yukleniciler (son_sozlesme_tarihi DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_yuk_il       ON public.yukleniciler (il);
ANALYZE public.yukleniciler;
NOTIFY pgrst, 'reload schema';
