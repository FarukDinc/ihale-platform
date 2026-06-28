"""
İhale AI Analiz Runner
- Supabase'den ilan_metni olan ama yapay_zeka_ozeti olmayan ihaleleri çeker
- Gemini ile analiz eder (ilan_metni metin → hızlı; belgeler PDF → ağır mod)
- Sonucu yapay_zeka_ozeti, analiz_tarihi, analiz_pdf_turu kolonlarına yazar

Kullanım:
    python analiz_runner.py              # limit=20, aktif ihaleler
    python analiz_runner.py --limit 5   # 5 ihale
    python analiz_runner.py --ikn 2026/123456  # tek ihale (IKN ile)
    python analiz_runner.py --id abc123  # tek ihale (Supabase ID ile)
    python analiz_runner.py --yenile    # daha önce analiz edilmişleri de yenile
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import re
import time
import argparse
import textwrap
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_KEY   = os.environ.get("GEMINI_API_KEY", "")
SUPA_URL     = os.environ.get("SUPABASE_URL", "")
SUPA_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── SDK kontrolleri ───────────────────────────────────────
try:
    from google import genai
    from google.genai import types as gtypes
except ImportError:
    print("✗ google-genai kurulu değil: pip install google-genai")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("✗ supabase kurulu değil: pip install supabase")
    sys.exit(1)

if not GEMINI_KEY:
    print("✗ GEMINI_API_KEY boş — .env dosyasını kontrol edin")
    sys.exit(1)

if not SUPA_URL or not SUPA_SERVICE:
    print("✗ SUPABASE_URL veya SUPABASE_SERVICE_KEY boş")
    sys.exit(1)

sb      = create_client(SUPA_URL, SUPA_SERVICE)
gemini  = genai.Client(api_key=GEMINI_KEY)
MODEL   = "gemini-2.5-flash"

# ── Prompt ───────────────────────────────────────────────
PROMPT_TMPL = """
Sen bir kamu ihalesi uzmanısın. Aşağıdaki ihale ilanını Türkçe olarak analiz et.

Çıktı formatı kesinlikle aşağıdaki yapıda olsun (başlık satırları ### ile):

### ÖZET
(İhalenin konusu, hangi ürün/hizmet/yapım işi olduğu — 2-3 cümle)

### KİLİT BİLGİLER
- İhale Türü: …
- Yaklaşık Maliyet: …
- İşin Süresi: …
- İşin Yeri: …
- Teklif Usulü: …

### GİRİŞ ENGELLERİ
(Ciro şartı, iş deneyimi, sertifika, belge gereksinimleri — varsa madde madde)

### MALİ YÜKÜMLÜLÜKLER
(Geçici teminat, kesin teminat, avans, fiyat farkı, ödeme süresi)

### RİSKLER VE UYARILAR
(Kırmızı alarm tetikleyen maddeler, sözleşme riskleri — varsa madde madde)

### FIRSATLAR
(Firmaya avantaj sağlayan maddeler — varsa)

### TAVSİYE
(GİR / DÜŞÜN / GIRME — 1-2 cümle gerekçe)

---
İHALE İLANI:
{ilan_metni}
"""

def analiz_et(ilan_metni: str, baslik: str) -> str | None:
    """Gemini ile ilan metnini analiz et, formatlanmış markdown döndür."""
    metin_kisaltilmis = ilan_metni[:40000]  # token limiti
    prompt = PROMPT_TMPL.format(ilan_metni=metin_kisaltilmis)
    try:
        resp = gemini.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
            ),
        )
        return (resp.text or "").strip() or None
    except Exception as e:
        print(f"  ✗ Gemini hata: {e}")
        return None

def pdf_analiz_et_gemini(pdf_url: str) -> str | None:
    """Storage URL'den PDF indir ve Gemini File API ile analiz et."""
    import tempfile, requests
    try:
        print(f"  → PDF indiriliyor: {pdf_url[:60]}...")
        r = requests.get(pdf_url, timeout=30, stream=True)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        for chunk in r.iter_content(8192):
            tmp.write(chunk)
        tmp.close()

        print("  → Gemini File API'ye yükleniyor...")
        with open(tmp.name, "rb") as f:
            dosya = gemini.files.upload(
                file=f,
                config={"mime_type": "application/pdf", "display_name": "ihale.pdf"},
            )

        # İşlenene kadar bekle
        for _ in range(30):
            durum = gemini.files.get(name=dosya.name)
            if durum.state.name == "ACTIVE":
                break
            time.sleep(2)

        prompt = PROMPT_TMPL.format(ilan_metni="[PDF dosyası Gemini'ye gönderildi, içeriği oku ve analiz et]")
        resp = gemini.models.generate_content(
            model=MODEL,
            contents=[prompt, gtypes.Part.from_uri(file_uri=dosya.uri, mime_type="application/pdf")],
            config=gtypes.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
        )
        return (resp.text or "").strip() or None

    except Exception as e:
        print(f"  ✗ PDF analiz hata: {e}")
        return None
    finally:
        try:
            gemini.files.delete(name=dosya.name)
        except Exception:
            pass
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

def ihaleleri_cek(limit: int, yenile: bool, tek_ikn: str | None, tek_id: str | None) -> list:
    """Analiz edilecek ihaleleri Supabase'den çek."""
    q = sb.table("ilanlar").select("id,ikn,ekap_id,baslik,ilan_metni,belgeler")
    if tek_id:
        q = q.eq("id", tek_id)
    elif tek_ikn:
        q = q.eq("ikn", tek_ikn)
    else:
        if not yenile:
            q = q.is_("yapay_zeka_ozeti", "null")
        q = q.eq("durum", "aktif")
        q = q.limit(limit)
    res = q.execute()
    return res.data or []

_INDEX_HATA_GOSTERILDI = False

def supabase_kaydet(ihale_id: str, ozet: str, pdf_turu: str):
    """Analiz sonucunu Supabase'e yaz."""
    global _INDEX_HATA_GOSTERILDI
    simdi = datetime.now(timezone.utc).isoformat()
    try:
        sb.table("ilanlar").update({
            "yapay_zeka_ozeti": ozet,
            "analiz_tarihi":    simdi,
            "analiz_pdf_turu":  pdf_turu,
        }).eq("id", ihale_id).execute()
    except Exception as e:
        if "idx_ilanlar_analiz" in str(e) or "54000" in str(e):
            if not _INDEX_HATA_GOSTERILDI:
                print()
                print("=" * 60)
                print("  ⚠️  SUPABASE INDEX HATASI — DÜZELTME GEREKLİ")
                print("=" * 60)
                print("  Supabase SQL Editor'da şunu çalıştır:")
                print("  DROP INDEX IF EXISTS idx_ilanlar_analiz;")
                print("  (backend/migration_fix_analiz_index.sql dosyası)")
                print("=" * 60)
                print()
                _INDEX_HATA_GOSTERILDI = True
            raise Exception(f"INDEX HATASI — migration_fix_analiz_index.sql çalıştır")
        raise

def main():
    parser = argparse.ArgumentParser(description="İhale AI Analiz Runner")
    parser.add_argument("--limit",  type=int, default=20, help="Kaç ihale (varsayılan: 20)")
    parser.add_argument("--ikn",    type=str, help="Tek ihale — IKN numarası")
    parser.add_argument("--id",     type=str, help="Tek ihale — Supabase UUID")
    parser.add_argument("--yenile", action="store_true", help="Daha önce analiz edilmişleri de yenile")
    parser.add_argument("--pdf",    action="store_true", help="belgeler içindeki PDF'leri de dene")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"İhale AI Analiz Runner — {MODEL}")
    print(f"Limit: {args.limit} | Yenile: {args.yenile} | PDF: {args.pdf}")
    print(f"{'='*60}\n")

    ihaleler = ihaleleri_cek(args.limit, args.yenile, args.ikn, args.id)
    print(f"{len(ihaleler)} ihale bulundu\n")

    basarili = hata = 0
    for i, ihale in enumerate(ihaleler, 1):
        ikn    = ihale.get("ikn") or ihale.get("ekap_id") or ihale.get("id")[:8]
        baslik = (ihale.get("baslik") or "")[:60]
        print(f"[{i}/{len(ihaleler)}] {ikn} — {baslik}")

        ozet     = None
        pdf_turu = "ilan_metni"

        # 1. İlan metni varsa → tercih
        ilan_metni = ihale.get("ilan_metni") or ""
        if ilan_metni and len(ilan_metni) > 100:
            print("  → ilan_metni ile analiz ediliyor...")
            ozet = analiz_et(ilan_metni, baslik)

        # 2. PDF modu — belgeler varsa ve ilan_metni yetersiz
        if not ozet and args.pdf:
            belgeler = ihale.get("belgeler") or []
            for belge in (belgeler if isinstance(belgeler, list) else []):
                storage_url = belge.get("storage_url") if isinstance(belge, dict) else None
                if storage_url:
                    print(f"  → PDF analiz: {belge.get('tur','?')}")
                    ozet = pdf_analiz_et_gemini(storage_url)
                    pdf_turu = "pdf_vision"
                    if ozet:
                        break

        if ozet:
            try:
                supabase_kaydet(ihale["id"], ozet, pdf_turu)
                print(f"  ✓ Kaydedildi ({len(ozet)} karakter, kaynak: {pdf_turu})")
                basarili += 1
            except Exception as e:
                print(f"  ✗ Supabase kayıt hatası: {e}")
                hata += 1
        else:
            print("  ⚠ Analiz üretilemedi (ilan_metni yok/kısa, PDF modu kapalı)")
            hata += 1

        # Rate limit — API kota koruması
        if i < len(ihaleler):
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"Tamamlandı: {basarili} başarılı, {hata} hata")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
