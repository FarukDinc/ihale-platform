# -*- coding: utf-8 -*-
"""
Türkiye dış ticaret verisi toplayıcı → js/ticaret-tr-veri.js
=============================================================
Uluslararası ihaleler dünya haritasındaki "Türkiye ile Ticaret" katmanını besler.
Trade Map (ITC) ToS gereği KULLANILMAZ (bkz. YAPILACAKLAR 16 Tem fizibilite notu);
aynı verinin serbest/anahtarsız kaynakları kullanılır:

  1. UN Comtrade public preview API (anahtarsız, atıfla kullanım serbest):
     ülke bazlı TOPLAM ihracat/ithalat, en güncel yıl + önceki yıl (YoY için).
     motCode=0 & partner2Code=0 & customsCode=C00 → temiz ülke-başı tek satır.
  2. Dünya Bankası WITS SDMX API (anahtarsız, açık veri):
     16 HS-aralığı ürün grubu (sektör filtresi) × ülke, ISO-A3 kodlu.
     Değerler bin USD → burada USD'ye çevrilir.

Çıktı: js/ticaret-tr-veri.js  →  window.TICARET_TR = {...}
Harita kodlarıyla (js/dunya-harita.js, ISO-A3) eşleşmeyen bölgeler atılır.

Çalıştırma (yılda 1-2 kez yeterli, cron GEREKMEZ):
  python backend/ticaret_verisi_cek.py
"""
import json
import re
import sys
import time
import datetime
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CIKTI = ROOT / "js" / "ticaret-tr-veri.js"
HARITA_JS = ROOT / "js" / "dunya-harita.js"

COMTRADE_URL = ("https://comtradeapi.un.org/public/v1/preview/C/A/HS"
                "?reporterCode=792&period={yil}&flowCode={akis}&cmdCode=TOTAL"
                "&motCode=0&partner2Code=0&customsCode=C00")
COMTRADE_REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
WITS_URL = ("https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade"
            "/reporter/TUR/year/{yil}/partner/ALL/product/all/indicator/{gosterge}?format=JSON")

# WITS HS-aralığı grupları → Türkçe etiket (sadece bunlar alınır; Total/manuf gibi
# üst-küme agregatları sektör filtresinde mükerrer sayım yaratacağı için atlanır)
SEKTORLER = {
    "01-05_Animal":    "Hayvansal Ürünler",
    "06-15_Vegetable": "Bitkisel Ürünler",
    "16-24_FoodProd":  "Gıda Ürünleri",
    "25-26_Minerals":  "Mineraller",
    "27-27_Fuels":     "Yakıtlar",
    "28-38_Chemicals": "Kimyasallar",
    "39-40_PlastiRub": "Plastik & Kauçuk",
    "41-43_HidesSkin": "Deri & Post",
    "44-49_Wood":      "Ahşap & Kağıt",
    "50-63_TextCloth": "Tekstil & Konfeksiyon",
    "64-67_Footwear":  "Ayakkabı",
    "68-71_StoneGlas": "Taş, Cam & Seramik",
    "72-83_Metals":    "Metaller",
    "84-85_MachElec":  "Makine & Elektrik-Elektronik",
    "86-89_Transport": "Ulaşım Araçları",
    "90-99_Miscellan": "Diğer İmalat",
}


def indir(url, deneme=3, bekle=2.0):
    """URL'yi JSON olarak indir; geçici hatalarda tekrar dene."""
    son_hata = None
    for i in range(deneme):
        try:
            istek = urllib.request.Request(url, headers={"User-Agent": "ihaleglobal-veri/1.0"})
            with urllib.request.urlopen(istek, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — ağ hatasında retry
            son_hata = e
            time.sleep(bekle * (i + 1))
    raise RuntimeError(f"İndirilemedi: {url} — {son_hata}")


def harita_kodlari():
    """js/dunya-harita.js içindeki geçerli ISO-A3 kodları (allowlist)."""
    icerik = HARITA_JS.read_text(encoding="utf-8")
    return set(re.findall(r'"kod":"([A-Z]{3})"', icerik))


def comtrade_yil_bul(baslangic):
    """En güncel veri yılını bul (deneyerek): >=50 ülke satırı dönen ilk yıl."""
    for yil in range(baslangic, baslangic - 4, -1):
        try:
            d = indir(COMTRADE_URL.format(yil=yil, akis="X"))
            if len(d.get("data", [])) >= 50:
                return yil, d
        except RuntimeError:
            continue
    raise RuntimeError("Comtrade'de kullanılabilir yıl bulunamadı")


def comtrade_topla(yil):
    """{un_kod: {X: deger, M: deger}} — bir yılın ihracat+ithalat toplamları."""
    sonuc = {}
    for akis in ("X", "M"):
        d = indir(COMTRADE_URL.format(yil=yil, akis=akis))
        for r in d.get("data", []):
            kod = r.get("partnerCode")
            v = r.get("primaryValue")
            if kod is None or not v:
                continue
            sonuc.setdefault(kod, {})[akis] = float(v)
        time.sleep(1.0)  # anahtarsız preview — nazik ol
    return sonuc


def wits_yil_bul(baslangic):
    for yil in range(baslangic, baslangic - 4, -1):
        try:
            d = indir(WITS_URL.format(yil=yil, gosterge="XPRT-TRD-VL"))
            if d.get("dataSets"):
                return yil, d
        except RuntimeError:
            continue
    raise RuntimeError("WITS'te kullanılabilir yıl bulunamadı")


def wits_coz(d):
    """WITS SDMX JSON → {iso3: {urun_kodu: usd}} (bin USD → USD)."""
    boyutlar = d["structure"]["dimensions"]["series"]
    eksen = {b["id"]: [v["id"] for v in b["values"]] for b in boyutlar}
    sonuc = {}
    for anahtar, seri in d["dataSets"][0]["series"].items():
        idx = [int(x) for x in anahtar.split(":")]
        kayit = dict(zip([b["id"] for b in boyutlar], idx))
        iso3 = eksen["PARTNER"][kayit["PARTNER"]]
        urun = eksen["PRODUCTCODE"][kayit["PRODUCTCODE"]]
        if urun not in SEKTORLER:
            continue
        gozlem = seri.get("observations", {}).get("0")
        if not gozlem or gozlem[0] is None:
            continue
        sonuc.setdefault(iso3, {})[urun] = float(gozlem[0]) * 1000.0  # bin USD → USD
    return sonuc


def wits_topla(yil):
    """{iso3: {urun: {X: usd, M: usd}}}"""
    sonuc = {}
    for akis, gosterge in (("X", "XPRT-TRD-VL"), ("M", "MPRT-TRD-VL")):
        d = indir(WITS_URL.format(yil=yil, gosterge=gosterge))
        for iso3, urunler in wits_coz(d).items():
            for urun, v in urunler.items():
                sonuc.setdefault(iso3, {}).setdefault(urun, {})[akis] = v
        time.sleep(1.0)
    return sonuc


def main():
    simdi = datetime.date.today()
    gecerli = harita_kodlari()
    print(f"Harita ISO-A3 kod sayısı: {len(gecerli)}")

    # ── UN kod → ISO3 eşlemesi ──
    ref = indir(COMTRADE_REF)
    un2iso, un2a2 = {}, {}
    for r in ref.get("results", []):
        a3 = r.get("PartnerCodeIsoAlpha3")
        if a3:
            un2iso[r["PartnerCode"]] = a3
            un2a2[r["PartnerCode"]] = r.get("PartnerCodeIsoAlpha2") or ""

    # ── Comtrade toplamları: güncel yıl + önceki yıl ──
    yil, _ = comtrade_yil_bul(simdi.year - 1)
    print(f"Comtrade güncel yıl: {yil}")
    guncel = comtrade_topla(yil)
    onceki = comtrade_topla(yil - 1)

    # ── WITS sektör kırılımı: güncel + önceki ──
    wyil, _ = wits_yil_bul(simdi.year - 2)
    print(f"WITS sektör yılı: {wyil}")
    ws_guncel = wits_topla(wyil)
    ws_onceki = wits_topla(wyil - 1)

    # ── Birleştir (harita kodu allowlist'iyle) ──
    ulkeler = {}
    dunya = {"ihr": [guncel.get(0, {}).get("X"), onceki.get(0, {}).get("X")],
             "ith": [guncel.get(0, {}).get("M"), onceki.get(0, {}).get("M")]}

    for un_kod, akislar in guncel.items():
        iso3 = un2iso.get(un_kod)
        if not iso3 or iso3 not in gecerli:
            continue
        o = onceki.get(un_kod, {})
        ulkeler[iso3] = {
            "a2": un2a2.get(un_kod, ""),
            "ihr": [round(akislar.get("X", 0)), round(o.get("X", 0))],
            "ith": [round(akislar.get("M", 0)), round(o.get("M", 0))],
        }

    sektor_n = 0
    for iso3, urunler in ws_guncel.items():
        if iso3 not in gecerli:
            continue
        hedef = ulkeler.setdefault(iso3, {"a2": "", "ihr": [0, 0], "ith": [0, 0]})
        s = {}
        for urun in SEKTORLER:
            g = urunler.get(urun, {})
            o = ws_onceki.get(iso3, {}).get(urun, {})
            dortlu = [round(g.get("X", 0)), round(o.get("X", 0)),
                      round(g.get("M", 0)), round(o.get("M", 0))]
            if any(dortlu):
                s[urun] = dortlu
                sektor_n += 1
        if s:
            hedef["s"] = s

    veri = {
        "guncelleme": simdi.isoformat(),
        "yil": yil, "onceki_yil": yil - 1,
        "sektor_yil": wyil, "sektor_onceki_yil": wyil - 1,
        "kaynak": "UN Comtrade & Dünya Bankası WITS",
        "dunya": dunya,
        "sektorler": SEKTORLER,
        "ulkeler": ulkeler,
    }

    js = ("// Otomatik üretildi — backend/ticaret_verisi_cek.py (elle düzenleme).\n"
          "// Kaynak: UN Comtrade (toplamlar) + Dünya Bankası WITS (sektör grupları). Atıf zorunlu.\n"
          "window.TICARET_TR = " + json.dumps(veri, ensure_ascii=False, separators=(",", ":")) + ";\n")
    CIKTI.write_text(js, encoding="utf-8")
    print(f"Yazıldı: {CIKTI}  ({CIKTI.stat().st_size/1024:.0f} KB, "
          f"{len(ulkeler)} ülke, {sektor_n} sektör-satırı)")


if __name__ == "__main__":
    sys.exit(main())
