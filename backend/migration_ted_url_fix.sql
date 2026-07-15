-- TED notice URL formatı düzeltmesi: /en/notice/{pub} 404 veriyor; doğru format /en/notice/-/detail/{pub}.
-- publication_no'dan yeniden kurar (idempotent — tekrar çalıştırmak güvenli).
UPDATE public.uluslararasi_ihaleler
   SET orijinal_url = 'https://ted.europa.eu/en/notice/-/detail/' || publication_no
 WHERE kaynak = 'ted'
   AND publication_no IS NOT NULL;
