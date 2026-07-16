# -*- coding: utf-8 -*-
"""
Ticaret sektör kırılımını TAZELE + İNCELT — js/ticaret-tr-veri.js
==================================================================
Mevcut js/ticaret-tr-veri.js'in ÜLKE TOPLAMLARINA dokunmadan (onlar Comtrade 2025),
yalnızca SEKTÖR kırılımını yeniler: WITS 16 grubu (2023) yerine Comtrade HS fasıllarını
(2-digit) çekip **21 standart HS bölümüne** toplulaştırır — TradeMap benzeri, taze.

Neden ayrı script: Comtrade preview çağrı başına 500 satır + 1s'de 429 rate-limit.
AG2 hepsi-birden 500'e kırpılıyor → fasıl-fasıl (her fasıl ~200 partner < 500) döngü,
5s aralık + 429 backoff. Tek yıl (sektör YoY yok; ülke-toplam YoY korunur).

Çalıştırma (python izni + Comtrade erişimi yeterli; EKAP/proxy GEREKMEZ):
  python backend/ticaret_sektor_yenile.py
Süre ~16 dk (194 çağrı × 5s). Bittiğinde js/ticaret-tr-veri.js güncellenir.
"""
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
VERI = ROOT / "js" / "ticaret-tr-veri.js"
COMTRADE = ("https://comtradeapi.un.org/public/v1/preview/C/A/HS"
            "?reporterCode=792&period={yil}&flowCode={akis}&cmdCode={ch}"
            "&motCode=0&partner2Code=0&customsCode=C00")
PARTNER_REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"

# HS fasıl (2-digit) → 21 standart bölüm. key=fasıl aralığı, label=Türkçe.
BOLUMLER = [
    ("01-05", "Hayvansal Ürünler",              range(1, 6)),
    ("06-14", "Bitkisel Ürünler",               range(6, 15)),
    ("15",    "Hayvansal/Bitkisel Yağlar",       range(15, 16)),
    ("16-24", "Hazır Gıda, İçecek, Tütün",       range(16, 25)),
    ("25-27", "Mineral Ürünler & Yakıtlar",      range(25, 28)),
    ("28-38", "Kimya Sanayi Ürünleri",           range(28, 39)),
    ("39-40", "Plastik & Kauçuk",                range(39, 41)),
    ("41-43", "Ham Deri & Post",                 range(41, 44)),
    ("44-46", "Ağaç & Ahşap Ürünler",            range(44, 47)),
    ("47-49", "Kağıt & Karton",                  range(47, 50)),
    ("50-63", "Tekstil & Konfeksiyon",           range(50, 64)),
    ("64-67", "Ayakkabı & Şapka",                range(64, 68)),
    ("68-70", "Taş, Çimento & Cam",              range(68, 71)),
    ("71",    "Kıymetli Taş, Metal & Mücevher",  range(71, 72)),
    ("72-83", "Adi Metaller & Ürünleri",         range(72, 84)),
    ("84-85", "Makine & Elektrik-Elektronik",    range(84, 86)),
    ("86-89", "Ulaşım Araçları",                 range(86, 90)),
    ("90-92", "Optik, Ölçü & Tıbbi Cihaz",       range(90, 93)),
    ("93",    "Silah & Mühimmat",                range(93, 94)),
    ("94-96", "Mobilya, Oyuncak & Muhtelif",     range(94, 97)),
    ("97",    "Sanat Eseri & Antika",            range(97, 98)),
]
FASIL_BOLUM = {}   # '84' -> '84-85'
for key, _ad, rng in BOLUMLER:
    for c in rng:
        FASIL_BOLUM[f"{c:02d}"] = key
TUM_FASILLAR = [f"{c:02d}" for c in range(1, 98) if c != 77]  # 77 boş/rezerve


def indir(url, deneme=4, bekle=20.0):
    for i in range(deneme):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "ihaleglobal-veri/1.0"}), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    · 429 — {bekle:.0f}s bekle (deneme {i+1})"); time.sleep(bekle); continue
            if e.code == 400:
                return None  # o fasıl/yıl için veri yok
            time.sleep(3.0)
        except Exception:
            time.sleep(3.0)
    return None


def yil_bul(un2iso):
    """Sektör detayının bulunduğu en güncel yılı bul (2024'ten geriye)."""
    for yil in (2024, 2023, 2022):
        d = indir(COMTRADE.format(yil=yil, akis="X", ch="84"))
        if d and d.get("data"):
            return yil
        time.sleep(5.0)
    return 2023


def fasil_cek(yil, akis, ch):
    d = indir(COMTRADE.format(yil=yil, akis=akis, ch=ch))
    return d.get("data", []) if d else []


def main():
    print("→ Mevcut ticaret-tr-veri.js yükleniyor…")
    metin = VERI.read_text(encoding="utf-8")
    veri = json.loads(re.search(r"window\.TICARET_TR = (.*);", metin, re.S).group(1))
    print(f"  {len(veri['ulkeler'])} ülke (toplamlar korunacak).")

    print("→ Comtrade partner referansı (UN kodu → ISO3)…")
    ref = indir(PARTNER_REF)
    un2iso = {r["PartnerCode"]: r.get("PartnerCodeIsoAlpha3") for r in ref.get("results", []) if r.get("PartnerCodeIsoAlpha3")}

    yil = yil_bul(un2iso)
    print(f"→ Sektör yılı: {yil}. {len(TUM_FASILLAR)} fasıl × 2 akış çekiliyor (~{len(TUM_FASILLAR)*2*5//60} dk)…")

    # {iso3: {bolum_key: {'X': usd, 'M': usd}}}
    sektor = {}
    n = 0
    for ch in TUM_FASILLAR:
        bolum = FASIL_BOLUM.get(ch)
        for akis in ("X", "M"):
            n += 1
            rows = fasil_cek(yil, akis, ch)
            for r in rows:
                iso = un2iso.get(r.get("partnerCode"))
                v = r.get("primaryValue")
                if not iso or not v:
                    continue
                b = sektor.setdefault(iso, {}).setdefault(bolum, {"X": 0.0, "M": 0.0})
                b[akis] += float(v)
            if n % 20 == 0:
                print(f"  … {n}/{len(TUM_FASILLAR)*2} çağrı ({ch}/{akis})")
            time.sleep(5.0)

    # Yeni sektörler haritayla (allowlist) sınırlı ülkelere yaz
    sektor_label = {k: ad for k, ad, _ in BOLUMLER}
    yazilan = 0
    for iso, ulke in veri["ulkeler"].items():
        s = sektor.get(iso)
        if not s:
            ulke.pop("s", None)
            continue
        yeni = {}
        for key in sektor_label:
            b = s.get(key)
            if b and (b["X"] or b["M"]):
                # [ihr_güncel, ihr_önceki=0, ith_güncel, ith_önceki=0] — tek yıl, YoY yok
                yeni[key] = [round(b["X"]), 0, round(b["M"]), 0]
                yazilan += 1
        if yeni:
            ulke["s"] = yeni
        else:
            ulke.pop("s", None)

    veri["sektorler"] = sektor_label
    veri["sektor_yil"] = yil
    veri["sektor_onceki_yil"] = yil - 1
    veri["kaynak"] = "UN Comtrade (toplam + HS sektör)"

    js = ("// Otomatik üretildi — backend/ticaret_verisi_cek.py + ticaret_sektor_yenile.py (elle düzenleme).\n"
          "// Kaynak: UN Comtrade (ülke toplamları + HS fasıl→bölüm sektör kırılımı). Atıf zorunlu.\n"
          "window.TICARET_TR = " + json.dumps(veri, ensure_ascii=False, separators=(",", ":")) + ";\n")
    VERI.write_text(js, encoding="utf-8")
    print(f"✓ Yazıldı: {VERI}  ({VERI.stat().st_size/1024:.0f} KB, {len(sektor_label)} bölüm, "
          f"{yazilan} sektör-satırı, yıl {yil})")


if __name__ == "__main__":
    main()
