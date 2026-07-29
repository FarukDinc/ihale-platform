"""
İhale AI Analiz Runner
- Supabase'den ilan_metni olan ama yapay_zeka_ozeti olmayan ihaleleri çeker
- AI ile analiz eder (ilan_metni metin → hızlı; belgeler PDF → ağır mod)
- Sonucu yapay_zeka_ozeti, analiz_tarihi, analiz_pdf_turu kolonlarına yazar

SAĞLAYICI (29 Tem): Gemini servis hesabı 401 UNAUTHENTICATED verdiği için METİN analizi
ai_ortak'a taşındı (birincil DeepSeek, yedek Gemini — env AI_SAGLAYICI ile ters çevrilir).
  · analiz_et (ilan_metni)      → ai_ortak.ai_metin      [TAŞINDI]
  · pdf_analiz_et_gemini (--pdf) → Gemini File API/Vision [AYNEN KALDI — DeepSeek'in metin
    API'si PDF/görüntü kabul etmez, taşınsaydı bu akış sessizce ölürdü]
PROMPT_TMPL ve "### başlıklı markdown" çıktı sözleşmesi DEĞİŞMEDİ.

Geriye uyum: google-genai kurulu değilse ya da GEMINI_API_KEY boşsa script artık ÖLMEZ —
sadece --pdf (Vision) yolu devre dışı kalır; metin analizi DeepSeek ile sürer.

Kullanım:
    python analiz_runner.py              # limit=20, aktif ihaleler
    python analiz_runner.py --limit 5   # 5 ihale
    python analiz_runner.py --ikn 2026/123456  # tek ihale (IKN ile)
    python analiz_runner.py --id abc123  # tek ihale (Supabase ID ile)
    python analiz_runner.py --yenile    # daha önce analiz edilmişleri de yenile
    python analiz_runner.py --pdf       # ilan_metni yetersizse belgeleri Vision'a ver (Gemini)
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

# Metin analizi sağlayıcı-bağımsız tek kapıdan geçer (DeepSeek ↔ Gemini).
from ai_ortak import ai_durum, ai_metin

# ── SDK kontrolleri ───────────────────────────────────────
# google-genai artık YALNIZ --pdf (Vision) yolu için gerekli. Metin analizi ai_ortak
# üzerinden gittiğinden SDK yokluğu scripti ÖLDÜRMEZ, sadece PDF modunu kapatır.
try:
    from google import genai
    from google.genai import types as gtypes
    GENAI_VAR = True
except ImportError:
    genai = gtypes = None
    GENAI_VAR = False

try:
    from supabase import create_client
except ImportError:
    print("✗ supabase kurulu değil: pip install supabase")
    sys.exit(1)

if not SUPA_URL or not SUPA_SERVICE:
    print("✗ SUPABASE_URL veya SUPABASE_SERVICE_KEY boş")
    sys.exit(1)

# Eskiden burada "GEMINI_API_KEY boşsa çık" vardı; artık HİÇBİR sağlayıcı anahtarı yoksa
# çıkıyoruz (fail-fast korundu ama Gemini'ye özel değil — DeepSeek tek başına yeter).
_AI = ai_durum()
if not (_AI["deepseek_anahtar"] or _AI["gemini_anahtar"]):
    print("✗ AI anahtarı yok — .env içinde DEEPSEEK_API_KEY (ya da GEMINI_API_KEY) tanımlayın")
    sys.exit(1)

sb = create_client(SUPA_URL, SUPA_SERVICE)

# Yalnız Vision (PDF) yolunun modeli — metin dalının modelini ai_ortak/env belirler.
VISION_MODEL = "gemini-2.5-flash"
_gemini = None


def gemini_istemci():
    """
    Vision (PDF) yolu için TEMBEL Gemini istemcisi. Modül seviyesinde kurmak, anahtar
    yokken --pdf kullanılmasa bile scripti import anında çökertirdi (yeni SDK'da
    Client(api_key="") doğrudan hata fırlatıyor). Eksiklikte RuntimeError → çağıran
    fonksiyonun except dalı yakalar ve o ihaleyi atlar.
    """
    global _gemini
    if _gemini is None:
        if not GENAI_VAR:
            raise RuntimeError("google-genai kurulu değil: pip install google-genai")
        if not GEMINI_KEY:
            raise RuntimeError("GEMINI_API_KEY boş — PDF/Vision analizi Gemini'ye bağlı")
        _gemini = genai.Client(api_key=GEMINI_KEY)
    return _gemini

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
    """
    İlan METNİNİ analiz et, formatlanmış markdown döndür (sağlayıcı: ai_ortak → DeepSeek/Gemini).
    Görüntü yok, saf metin → taşınabilir dal. Hata/boş yanıtta None döner ve nedeni ai_ortak
    stderr'e basar (sessiz yutma yok); çağıran taraf eskisi gibi "analiz üretilemedi" sayar.
    """
    metin_kisaltilmis = ilan_metni[:40000]  # token limiti
    prompt = PROMPT_TMPL.format(ilan_metni=metin_kisaltilmis)
    # sistem="": eski çağrıda system_instruction yoktu, prompt tek parça gidiyordu.
    # max_tokens/temperature eski Gemini config'iyle BİREBİR aynı (4096 / 0.2) — çıktı
    # sözleşmesi (### başlıklı markdown) korunsun diye json_mod KAPALI.
    # zaman_asimi=180: 40.000 karakterlik girdi + uzun markdown çıktı 60sn'yi aşabilir.
    # deneme=3: toplu/gece işi — 429/5xx/ağ hatasında satır kaybetmek yerine tekrar dene.
    return ai_metin(
        "", prompt,
        max_tokens=4096, temperature=0.2,
        zaman_asimi=180, deneme=3, nerede="analiz_runner/ilan_metni",
    )

def pdf_analiz_et_gemini(pdf_url: str) -> str | None:
    """
    Storage URL'den PDF indir ve Gemini File API ile analiz et.
    ⛔ GEMİNİ'DE KALIR: girdi ham PDF, DeepSeek'in metin API'si görüntü/dosya kabul etmez.
    """
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
            dosya = gemini_istemci().files.upload(
                file=f,
                config={"mime_type": "application/pdf", "display_name": "ihale.pdf"},
            )

        # İşlenene kadar bekle
        for _ in range(30):
            durum = gemini_istemci().files.get(name=dosya.name)
            if durum.state.name == "ACTIVE":
                break
            time.sleep(2)

        prompt = PROMPT_TMPL.format(ilan_metni="[PDF dosyası Gemini'ye gönderildi, içeriği oku ve analiz et]")
        resp = gemini_istemci().models.generate_content(
            model=VISION_MODEL,
            contents=[prompt, gtypes.Part.from_uri(file_uri=dosya.uri, mime_type="application/pdf")],
            config=gtypes.GenerateContentConfig(temperature=0.2, max_output_tokens=4096),
        )
        return (resp.text or "").strip() or None

    except Exception as e:
        print(f"  ✗ PDF analiz hata: {e}")
        return None
    finally:
        try:
            gemini_istemci().files.delete(name=dosya.name)
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
    # Model ADI değil sağlayıcı basılıyor: metin dalı artık env'e göre DeepSeek ya da Gemini.
    print(f"İhale AI Analiz Runner — metin: {_AI['birincil']} (yedek: {_AI['yedek']})")
    print(f"Limit: {args.limit} | Yenile: {args.yenile} | PDF: {args.pdf}")
    if args.pdf and not (GENAI_VAR and GEMINI_KEY):
        # Sessiz arıza yok: --pdf istendi ama Vision yolu kurulamaz durumda.
        print("  ⚠ --pdf istendi ama Gemini yolu kapalı "
              f"({'google-genai kurulu değil' if not GENAI_VAR else 'GEMINI_API_KEY boş'}) "
              "— PDF adımı atlanacak")
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
