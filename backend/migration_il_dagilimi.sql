-- Harita choropleth için il bazında firma yoğunluğu (yukleniciler). Client 53K satırı çekemez → RPC.
CREATE OR REPLACE FUNCTION public.il_firma_dagilimi()
RETURNS TABLE(il text, adet bigint, toplam_ciro numeric)
LANGUAGE sql STABLE
AS $$
  SELECT il, count(*)::bigint, sum(COALESCE(toplam_ciro, 0))
  FROM public.yukleniciler
  WHERE il IS NOT NULL AND btrim(il) <> ''
  GROUP BY il;
$$;
GRANT EXECUTE ON FUNCTION public.il_firma_dagilimi() TO anon, authenticated, service_role;

-- Açık RFQ'ların il dağılımı (pin sayısı için — az satır ama tutarlı olsun)
CREATE OR REPLACE FUNCTION public.il_rfq_dagilimi()
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT il, count(*)::bigint
  FROM public.satinalma_talepleri
  WHERE durum = 'acik' AND il IS NOT NULL AND btrim(il) <> ''
  GROUP BY il;
$$;
GRANT EXECUTE ON FUNCTION public.il_rfq_dagilimi() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
