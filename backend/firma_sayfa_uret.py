"""
Faz E3 — SEO Firma Sayfaları

`yukleniciler`'deki (toplam_sozlesme_sayisi >= EŞİK) firmalar için statik, indexlenebilir
HTML sayfaları üretir: firma/<slug>.html. Her sayfa gerçek <title>/<meta description>/JSON-LD
içerir (client-side render değil — arama motoru ilk yüklemede içeriği görür), ve tam
etkileşimli (pivot/AI) analiz için firma-analiz.html?firma=<ad>'a yönlendiren bir CTA taşır.
"Özet public, derinlik PRO" stratejisi — bkz. YAPILACAKLAR.md Faz E3.

Sadece PUBLIC REST API'yi (anon key) okur — production'a hiçbir yazma yapmaz, bu yüzden
yerel makineden güvenle çalıştırılabilir. Ürettiği dosyalar `firma/` klasörüne ve
`sitemap-firmalar.xml`/`robots.txt`'e yazılır — normal repo dosyaları, `git add` + commit
ile eklenir, VDS'e `git pull` sonrası canlı olur (ekstra nginx/DB değişikliği GEREKMEZ,
site zaten her yolu uzantısız `.html` olarak sunuyor).

Kullanım: python firma_sayfa_uret.py [--esik 3] [--max 5000]
"""

import argparse
import html
import os
import re
import unicodedata
from datetime import datetime, timezone

from urllib.parse import quote

import httpx

SUPABASE_URL = "https://ihaleglobal.com"
# Public anon key — js/api.js'de zaten frontend'e gömülü, gizli değil.
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgzMzUwMDE1LCJleHAiOjE5NDEwMzAwMTV9.sRB61a8oNXwzSKL9No8gt7cmkmnkoQstT0ZtHIxl1Hs"

REPO_KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRMA_DIZIN = os.path.join(REPO_KOK, "firma")

TR_HARF = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
    "İ": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})


def slug_uret(ad: str) -> str:
    s = ad.translate(TR_HARF).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    return s[:80] or "firma"


def para_formatla(n):
    if not n:
        return "—"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f} milyar ₺"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} milyon ₺"
    if n >= 1_000:
        return f"{n/1_000:.0f} bin ₺"
    return f"{n} ₺"


def tarih_formatla(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except Exception:
        return s[:10]


def firmalari_cek(esik: int, max_kayit: int):
    firmalar = []
    with httpx.Client(timeout=30.0) as c:
        off = 0
        while len(firmalar) < max_kayit:
            r = c.get(
                f"{SUPABASE_URL}/rest/v1/yukleniciler",
                params={
                    "select": "ad,normalize_ad,il,toplam_sozlesme_sayisi,toplam_ciro,"
                               "ilk_sozlesme_tarihi,son_sozlesme_tarihi,sektor,kategori",
                    "toplam_sozlesme_sayisi": f"gte.{esik}",
                    "order": "toplam_sozlesme_sayisi.desc",
                    "limit": "1000",
                    "offset": str(off),
                },
                headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"},
            )
            r.raise_for_status()
            sayfa = r.json()
            if not sayfa:
                break
            firmalar.extend(sayfa)
            if len(sayfa) < 1000:
                break
            off += 1000
    return firmalar[:max_kayit]


SAYFA_SABLON = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{baslik}</title>
<meta name="description" content="{aciklama}" />
<link rel="canonical" href="{canonical}" />
<meta property="og:type" content="website" />
<meta property="og:title" content="{baslik}" />
<meta property="og:description" content="{aciklama}" />
<meta property="og:url" content="{canonical}" />
<link rel="stylesheet" href="../css/style.css" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<script type="application/ld+json">{jsonld}</script>
<style>
  .fk-wrap {{ max-width: 760px; margin: 64px auto; padding: 0 24px; }}
  .fk-eyebrow {{ font-size: 12px; font-weight: 700; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 10px; }}
  .fk-ad {{ font-family: var(--font-display); font-size: 30px; font-weight: 800; color: var(--white); margin-bottom: 8px; line-height: 1.25; }}
  .fk-meta {{ color: var(--muted); font-size: 14px; margin-bottom: 28px; }}
  .fk-kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 14px; margin-bottom: 28px; }}
  .fk-kpi {{ background: var(--navy-mid); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; }}
  .fk-kpi-label {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; }}
  .fk-kpi-val {{ font-size: 20px; font-weight: 800; color: var(--amber); }}
  .fk-chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }}
  .fk-chip {{ background: var(--navy-mid); border: 1px solid var(--border); color: var(--off-white); font-size: 12px; padding: 5px 12px; border-radius: 20px; }}
  .fk-cta {{ background: var(--navy-mid); border: 1px solid var(--border); border-radius: 14px; padding: 24px; text-align: center; }}
  .fk-cta p {{ color: var(--muted); font-size: 14px; margin-bottom: 16px; }}
  .fk-breadcrumb {{ font-size: 13px; color: var(--muted); margin-bottom: 24px; }}
  .fk-breadcrumb a {{ color: var(--muted); }}
  .fk-breadcrumb a:hover {{ color: var(--amber); }}
</style>
</head>
<body>

<nav class="landing-nav">
  <div class="nav-inner">
    <a href="/" class="logo"><span class="logo-dot"></span>İhale<span>Global</span></a>
    <ul class="nav-links">
      <li><a href="/firmalar">Firmalar Dizini</a></li>
      <li><a href="/ihaleler">İhaleler</a></li>
      <li><a href="/idareler">İdareler</a></li>
    </ul>
    <div class="nav-cta">
      <a href="/login" class="btn btn-ghost">Giriş Yap</a>
      <a href="/login" class="btn btn-primary">Ücretsiz Başla</a>
    </div>
  </div>
</nav>

<div class="fk-wrap">
  <div class="fk-breadcrumb"><a href="/">Ana Sayfa</a> / <a href="/firmalar">Firmalar</a> / {ad_kisa}</div>
  <div class="fk-eyebrow">🏢 Firma Profili</div>
  <h1 class="fk-ad">{ad}</h1>
  <div class="fk-meta">{ozet_cumle}</div>

  <div class="fk-kpi-grid">
    <div class="fk-kpi"><div class="fk-kpi-label">Toplam Sözleşme</div><div class="fk-kpi-val">{sozlesme_sayisi}</div></div>
    <div class="fk-kpi"><div class="fk-kpi-label">Toplam Ciro</div><div class="fk-kpi-val">{ciro}</div></div>
    <div class="fk-kpi"><div class="fk-kpi-label">İlk İş</div><div class="fk-kpi-val" style="font-size:15px;">{ilk_is}</div></div>
    <div class="fk-kpi"><div class="fk-kpi-label">Son İş</div><div class="fk-kpi-val" style="font-size:15px;">{son_is}</div></div>
  </div>

  {sektor_blok}

  <div class="fk-cta">
    <p>Rakip karşılaştırması, yıllık trend, idare/sektör kırılımı ve AI destekli rekabet
      analizi için {ad_kisa} firmasının tam profiline göz atın.</p>
    <a class="btn btn-primary" href="/firma-analiz?firma={ad_encoded}">📊 Detaylı Analizi Gör →</a>
  </div>
</div>

<footer>
  <div class="container">
    <div class="footer-bottom">
      <p>© {yil} İhaleGlobal. Tüm hakları saklıdır.</p>
      <p style="font-size:12px;">Veriler EKAP kamu ihale ilanlarından derlenmiştir, resmi teyit için EKAP'a başvurunuz.</p>
    </div>
  </div>
</footer>

</body>
</html>
"""


def sayfa_uret(f: dict) -> tuple[str, str]:
    ad = (f.get("ad") or f.get("normalize_ad") or "").strip()
    slug = slug_uret(f.get("normalize_ad") or ad)
    canonical = f"https://ihaleglobal.com/firma/{slug}"
    sozlesme_sayisi = f.get("toplam_sozlesme_sayisi") or 0
    ciro = f.get("toplam_ciro") or 0
    il = f.get("il") or ""
    sektorler = [s for s in (f.get("sektor") or f.get("kategori") or []) if s]

    ozet_cumle = f"{ad}, EKAP kayıtlarına göre {sozlesme_sayisi} kamu ihalesi kazanmış" \
                 + (f", {il} merkezli" if il else "") + " bir yüklenicidir."
    aciklama = (
        f"{ad} firmasının kamu ihale geçmişi: {sozlesme_sayisi} sözleşme, "
        f"toplam {para_formatla(ciro)} ciro" + (f", {il}" if il else "") + ". "
        f"EKAP kamu ihale verilerinden derlenmiştir."
    )
    baslik = f"{ad} — İhale Geçmişi ve Firma Analizi | İhaleGlobal"

    sektor_blok = ""
    if sektorler:
        chips = "".join(f'<span class="fk-chip">{html.escape(s)}</span>' for s in sektorler[:12])
        sektor_blok = f'<div class="fk-chips">{chips}</div>'

    jsonld = (
        '{"@context":"https://schema.org","@type":"Organization","name":' + _json_str(ad)
        + (',"address":{"@type":"PostalAddress","addressLocality":' + _json_str(il) + ',"addressCountry":"TR"}' if il else "")
        + '}'
    )

    ad_encoded = quote(ad)

    html_out = SAYFA_SABLON.format(
        baslik=html.escape(baslik),
        aciklama=html.escape(aciklama),
        canonical=canonical,
        ad_kisa=html.escape(ad[:40]),
        ad=html.escape(ad),
        ozet_cumle=html.escape(ozet_cumle),
        sozlesme_sayisi=sozlesme_sayisi,
        ciro=para_formatla(ciro),
        ilk_is=tarih_formatla(f.get("ilk_sozlesme_tarihi")),
        son_is=tarih_formatla(f.get("son_sozlesme_tarihi")),
        sektor_blok=sektor_blok,
        ad_encoded=ad_encoded,
        yil=datetime.now().year,
        jsonld=jsonld,
    )
    return slug, html_out


def _json_str(s: str) -> str:
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esik", type=int, default=3, help="min. toplam_sozlesme_sayisi")
    ap.add_argument("--max", type=int, default=5000, help="üretilecek maksimum sayfa")
    args = ap.parse_args()

    print(f"→ yukleniciler çekiliyor (toplam_sozlesme_sayisi >= {args.esik})...")
    firmalar = firmalari_cek(args.esik, args.max)
    print(f"  {len(firmalar)} firma bulundu.")

    os.makedirs(FIRMA_DIZIN, exist_ok=True)

    gorulmus_slug = {}
    urls = []
    for f in firmalar:
        if not (f.get("ad") or f.get("normalize_ad")):
            continue
        slug, sayfa = sayfa_uret(f)
        if slug in gorulmus_slug:
            gorulmus_slug[slug] += 1
            slug = f"{slug}-{gorulmus_slug[slug]}"
        else:
            gorulmus_slug[slug] = 0
        with open(os.path.join(FIRMA_DIZIN, f"{slug}.html"), "w", encoding="utf-8") as fh:
            fh.write(sayfa)
        urls.append(f"https://ihaleglobal.com/firma/{slug}")

    print(f"✓ {len(urls)} statik firma sayfası yazıldı → {FIRMA_DIZIN}")

    # sitemap-firmalar.xml
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append(f"  <url><loc>{u}</loc><lastmod>{simdi}</lastmod><changefreq>weekly</changefreq></url>")
    sitemap.append("</urlset>")
    sitemap_yolu = os.path.join(REPO_KOK, "sitemap-firmalar.xml")
    with open(sitemap_yolu, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sitemap))
    print(f"✓ sitemap-firmalar.xml yazıldı ({len(urls)} URL) → {sitemap_yolu}")


if __name__ == "__main__":
    main()
