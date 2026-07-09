"""
Firma adı normalizasyonu — ÖNCELİK 10 Faz B1.

Aynı firma EKAP'ta farklı yazımlarla geçebiliyor ("ABC İNŞAAT A.Ş.", "Abc Inşaat A.Ş",
"ABC İNŞ. TAAH. A.Ş.") — bunları TEK bir `normalize_ad` anahtarında birleştirmek,
`yukleniciler` tablosunun (Faz B2) ve firma-analiz sayfasının (Faz C2) doğruluğu için şart.

SQL tarafında AYNI mantığın PL/pgSQL karşılığı `migration_yuklenici_agg.sql`'deki
`normalize_firma()` fonksiyonudur — ikisi senkron tutulmalı (biri değişirse diğeri de).
"""

import re
import unicodedata

# Sık geçen firma eki/kısaltmaları — noktalama/boşluk farklarından bağımsız tekilleştirmek için
# kaldırılır. SQL normalize_firma() ile AYNI küme olmalı (migration_yuklenici_agg.sql).
# Not: noktalama önce temizlendiği için (bkz. normalize_ad) burada tam-kelime kalıpları yeterli.
_EKLER = [
    r"\bA\s*Ş\b", r"\bLTD\b", r"\bŞT[İI]\b",
    r"\bANON[İI]M\b", r"\bL[İI]M[İI]TED\b", r"\bŞ[İI]RKET[İI]?\b",
    r"\bKOLLEKT[İI]F\b", r"\bKOMAND[İI]T\b",
    r"\bT[İI]C\b", r"\bSAN\b", r"\b[İI]NŞ\b", r"\bTAAH\b",
    r"\bVE\b", r"\bT[İI]CARET\b", r"\bSANAY[İI]\b", r"\b[İI]NŞAAT\b", r"\bTAAHHÜT\b",
]
_EKLER_RE = re.compile("|".join(_EKLER), re.IGNORECASE)

_TR_UPPER_MAP = str.maketrans({"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç"})


def mojibake_duzelt(s: str | None) -> str | None:
    if not s:
        return s
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        if any(c in fixed for c in "çğıöşüÇĞİÖŞÜ"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s


def ortak_girisim_mi(ad: str) -> bool:
    """'İŞ ORTAKLIĞI' / 'ORTAK GİRİŞİM' / iki firmayı '-' ile ayıran kalıpları tespit eder."""
    if not ad:
        return False
    u = ad.upper()
    return "İŞ ORTAKLIĞI" in u or "ORTAK GİRİŞİM" in u or "İŞ ORTAKLIĞ" in u or " - " in ad


def ortaklari_ayir(ad: str) -> list[str]:
    """Ortak girişim adından, mümkünse, tekil firma adlarını ayırır (best-effort)."""
    if not ad:
        return []
    parcalar = re.split(r"\s*-\s*|\s*/\s*", ad)
    parcalar = [p.strip() for p in parcalar if p.strip()]
    return parcalar if len(parcalar) > 1 else [ad]


def normalize_ad(ham_ad: str | None) -> str | None:
    """
    Firma adını tekil bir anahtara indirger: mojibake düzelt → TR-locale büyük harf →
    yaygın ekleri kaldır → noktalama/fazla boşluk temizle.
    SQL karşılığıyla (migration_yuklenici_agg.sql) davranışça aynı olmalı.
    """
    if not ham_ad:
        return None
    ad = mojibake_duzelt(ham_ad) or ham_ad
    ad = ad.strip()
    if not ad:
        return None
    # TR-locale büyük harfe çevirme (Python'ın varsayılan .upper() İ/I ayrımını doğru yapmaz)
    ad = ad.translate(_TR_UPPER_MAP).upper()
    ad = unicodedata.normalize("NFC", ad)
    # Önce noktalama temizliği (SQL normalize_firma() ile aynı sıra) — böylece "A.Ş" → "A Ş"
    # olur ve tam-kelime ek kuralları da yakalar.
    ad = re.sub(r"[.,\-–—()]+", " ", ad)
    ad = _EKLER_RE.sub(" ", ad)
    ad = re.sub(r"\s+", " ", ad).strip()
    return ad or None


if __name__ == "__main__":
    ornekler = [
        "ABC İnşaat A.Ş.",
        "ABC İNŞ. TAAH. SAN. VE TİC. A.Ş",
        "Abc Inşaat Anonim Şirketi",
        "XYZ Ltd. Şti.",
        "DEMİR YAPI İNŞAAT - ÇELİK METAL İŞ ORTAKLIĞI",
    ]
    for o in ornekler:
        print(f"{o!r:55} → {normalize_ad(o)!r} (ortak_girisim={ortak_girisim_mi(o)})")
