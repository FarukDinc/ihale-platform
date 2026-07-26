#!/usr/bin/env python3
"""Sonuç (durum=5) EKAP listesinde TARİH FİLTRESİ çalışıyor mu + hangi alan adı?
Amaç: yıl bazında tam-kapsama backfill için doğru parametreyi bulmak.
Hafif: yalnız totalCount okur (paginationTake=1), ~10 istek."""
import asyncio, sys
from ekap_sonuc_backfill import post, LISTE_EP, async_havuz_al, ekap_ssl_baglami

ADAYLAR = [
    # (etiket, ek parametreler)  — 2017 yılını hedefle
    ("filtresiz", {}),
    ("ihaleTarihi",   {"ihaleTarihiBaslangic": "01.01.2017", "ihaleTarihiBitis": "31.12.2017"}),
    ("sozlesmeTarihi",{"sozlesmeTarihiBaslangic": "01.01.2017", "sozlesmeTarihiBitis": "31.12.2017"}),
    ("sonucTarihi",   {"sonucTarihiBaslangic": "01.01.2017", "sonucTarihiBitis": "31.12.2017"}),
    ("ilanTarihi",    {"ilanTarihiBaslangic": "01.01.2017", "ilanTarihiBitis": "31.12.2017"}),
    ("baslangicTarihi",{"baslangicTarihi": "01.01.2017", "bitisTarihi": "31.12.2017"}),
    ("ISO_ihaleTarihi",{"ihaleTarihiBaslangic": "2017-01-01", "ihaleTarihiBitis": "2017-12-31"}),
]

async def main():
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    for etiket, ek in ADAYLAR:
        body = {"searchText": "", "paginationSkip": 0, "paginationTake": 1,
                "ihaleDurumIdList": [5], "searchType": "GirdigimGibi", **ek}
        try:
            veri = await post(havuz, LISTE_EP, body)
            tc = veri.get("totalCount") if veri else None
        except Exception as e:
            tc = f"HATA {type(e).__name__}"
        print(f"  {etiket:22} totalCount = {tc}")
        await asyncio.sleep(0.5)

asyncio.run(main())
