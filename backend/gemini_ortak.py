"""
Gemini (google-genai) ortak yardımcıları — Backlog #34 SDK migrasyonu.

Eski `google.generativeai` SDK'sı "support ended" durumda; File API'si canlıda zaten
kırık (bkz. analyzer.py'deki uzun not: upload_file'ın discovery uç noktası "API key not
valid" veriyor, aynı anahtarla generate_content çalışıyor). Tüm çağrı yerleri yeni
`google-genai` SDK'sına taşındı. Bu modül migrasyonun iki ORTAK tuzağını tek yerde toplar:

  1) TEMBEL istemci. Eski SDK'da `genai.configure(api_key="")` sessizce geçerdi; yeni
     SDK'da `genai.Client(api_key="")` doğrudan ValueError fırlatır. İstemciyi modül
     seviyesinde kurmak, GEMINI_API_KEY yokken api.py'ı IMPORT ANINDA çökertirdi
     (api.py teklif_ai + firma_ai_yorum'u top-level import ediyor → tüm API düşerdi).
     `istemci_al()` istemciyi ilk çağrıda kurar ve tekrar kullanır.

  2) GÜRÜLTÜLÜ boş-yanıt teşhisi. Bu projede sessiz cron arızası 3 kez yaşandı, o yüzden
     "boş yanıt"ı olduğu gibi yutmuyoruz: Gemini bir güvenlik bloğu, token limiti ya da
     düşünme bütçesi tükenmesi durumunda metni BOŞ döndürür. Sadece `resp.text or ""`
     yazılırsa bu "veri yok" gibi görünür ve hata log'a hiç düşmez. `yanit_metni()` boş
     yanıtın gerçek nedenini (block_reason / finish_reason / bloklanan güvenlik kategorisi)
     çağırana metin olarak geri verir.

Kullanım:
    from gemini_ortak import istemci_al, yanit_metni, gemini_hata_logla

    resp = istemci_al().models.generate_content(model="gemini-2.5-flash", contents=prompt)
    metin, bos_neden = yanit_metni(resp)
    if not metin:
        gemini_hata_logla("firma_yorum", bos_neden)
"""

import os
import sys

from dotenv import load_dotenv
from google import genai

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Proje genelinde kullanılan üretim modeli (analiz_runner.py / ai_kategori_backfill.py ile aynı).
VARSAYILAN_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_istemci = None


def anahtar_var() -> bool:
    """GEMINI_API_KEY tanımlı mı — istemci kurmayı denemeden kontrol etmek için."""
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def istemci_al() -> genai.Client:
    """
    Paylaşılan google-genai istemcisi (tembel kurulur, süreç boyunca tek örnek).
    Anahtar yoksa RuntimeError fırlatır — çağıran taraf bunu kendi hata dalında yakalar.
    Bilerek ImportError/ValueError yerine RuntimeError: mevcut `except Exception` blokları
    zaten yakalıyor, ama mesaj artık "no api key" yerine hangi env değişkeni olduğunu söylüyor.
    """
    global _istemci
    if _istemci is None:
        anahtar = os.environ.get("GEMINI_API_KEY", "").strip()
        if not anahtar:
            raise RuntimeError("GEMINI_API_KEY boş — backend/.env dosyasını kontrol edin")
        _istemci = genai.Client(api_key=anahtar)
    return _istemci


def _bos_neden(resp) -> str:
    """Boş yanıtın nedenini SDK yanıtından çıkarır (hepsi opsiyonel alan, getattr ile korunuyor)."""
    parcalar = []

    geri_bildirim = getattr(resp, "prompt_feedback", None)
    if geri_bildirim is not None:
        if getattr(geri_bildirim, "block_reason", None):
            parcalar.append(f"prompt bloklandı: {geri_bildirim.block_reason}")
        if getattr(geri_bildirim, "block_reason_message", None):
            parcalar.append(str(geri_bildirim.block_reason_message))

    for aday in (getattr(resp, "candidates", None) or []):
        if getattr(aday, "finish_reason", None):
            # MAX_TOKENS / SAFETY / RECITATION burada görünür — sessiz kesilmenin ana kaynağı.
            parcalar.append(f"finish_reason={aday.finish_reason}")
        if getattr(aday, "finish_message", None):
            parcalar.append(f"finish_message={aday.finish_message}")
        bloklu = [
            f"{getattr(r, 'category', '?')}={getattr(r, 'probability', '?')}"
            for r in (getattr(aday, "safety_ratings", None) or [])
            if getattr(r, "blocked", None)
        ]
        if bloklu:
            parcalar.append("bloklanan güvenlik kategorileri: " + ", ".join(bloklu))

    kullanim = getattr(resp, "usage_metadata", None)
    if kullanim is not None and getattr(kullanim, "thoughts_token_count", None):
        # gemini-2.5-* düşünme AÇIKken tüm çıktı bütçesini "thoughts"a harcayıp metni boş bırakabilir.
        parcalar.append(f"düşünme tokeni={kullanim.thoughts_token_count}")

    return "; ".join(str(p) for p in parcalar) if parcalar else "SDK neden bildirmedi"


def yanit_metni(resp) -> tuple[str, str | None]:
    """
    (metin, bos_neden) döner. Metin doluysa bos_neden None'dır.

    Yeni SDK'da `.text`, aday/parça yokken None döner (eski SDK ValueError fırlatıyordu);
    ayrıca çok-parçalı bloklu yanıtlarda erişimin kendisi istisna üretebiliyor. Her iki
    durumu da neden metnine çeviriyoruz ki çağıran "boş" ile "bloklandı"yı ayırabilsin.
    """
    try:
        metin = (resp.text or "").strip()
    except Exception as e:
        return "", f".text okunamadı: {type(e).__name__}: {e}"
    if metin:
        return metin, None
    return "", _bos_neden(resp)


def gemini_hata_logla(nerede: str, hata) -> str:
    """
    Hatayı stderr'e GÜRÜLTÜLÜ basar (flush'lı — cron log'unda tamponda kalmasın) ve
    kısaltılmış mesajı döndürür. Sessiz yutma yasak: bu projede cron'un sessizce 0 kayıt
    yazması 3 kez yaşandı, o yüzden her AI hatası log'da görünür olmalı.
    """
    if isinstance(hata, Exception):
        mesaj = f"{type(hata).__name__}: {hata}"
        # google.genai.errors.APIError ailesinde HTTP durumu ayrı alanda duruyor (429/503 ayrımı için).
        durum = getattr(hata, "status", None)
        kod = getattr(hata, "code", None)
        if durum or kod:
            mesaj = f"[{kod or ''}{'/' if (kod and durum) else ''}{durum or ''}] {mesaj}"
    else:
        mesaj = str(hata)
    print(f"  ✗ Gemini hatası ({nerede}): {mesaj[:400]}", file=sys.stderr, flush=True)
    return mesaj
