"""
ai_ortak.py — sağlayıcı-bağımsız TEK metin/chat arayüzü (DeepSeek ↔ Gemini).

NEDEN VAR (29 Tem kararı): Gemini servis hesabı öldü (401 UNAUTHENTICATED — "service
account is deleted or disabled") ve fiyat/performans nedeniyle METİN işleri DeepSeek'e
taşınıyor. Her çağrı yerine ayrı bir DeepSeek istemcisi kopyalamak yerine (teklif_ai.py'de
zaten bir tane vardı) tüm metin üretimi/sınıflandırma bu tek kapıdan geçer.

⛔ BU KATMAN YALNIZ **CHAT/METİN** İÇİNDİR. Şunlar buraya TAŞINMAZ:
  · EMBEDDING  → embed_ortak.py (models/gemini-embedding-001, 768 boyut) AYNEN kalır.
    Vektör uzayı değişirse ilanlar.embedding (vector(768) + hnsw) ve uygun_firmalar_v3 /
    semantik eşleme RPC'leri bozulur.
  · GÖRSEL/VISION → analyzer.py (taranmış PDF) ve ekap_scraper.py (CAPTCHA) Gemini'de kalır.
    DeepSeek'in metin API'si görüntü kabul etmez; taşınırsa o akış SESSİZCE ölür.

MİMARİ
------
  ai_metin(sistem, kullanici, ...) -> str | None      # sade: metin ya da None
  ai_cagir(sistem, kullanici, ...) -> dict            # {basari, metin, hata, saglayici}

  Sağlayıcı sırası env ile: AI_SAGLAYICI ∈ {'deepseek' (öntanım), 'gemini'}.
  BİRİNCİ sağlayıcı anahtarsızsa ya da hata verirse İKİNCİye düşülür; ikisi de yoksa
  basari=False + metin=None döner ve çağıran taraf ESKİSİ GİBİ sessizce atlar
  (geriye uyum: yeni env değişkeni tanımlı değilse hiçbir şey çökmez).

  Gemini yolu gemini_ortak.py üzerinden gider (tembel istemci + gürültülü boş-yanıt teşhisi).
  `google-genai` kurulu değilse ya da anahtar yoksa import HATASI DEĞİL, sadece "bu sağlayıcı
  yok" olarak işlenir — import fonksiyon içinde, çünkü api.py bu modülü dolaylı olarak
  top-level import ediyor ve SDK yokluğu tüm API'yi düşürmemeli.

DeepSeek JSON MODU (json_mod=True)
----------------------------------
  OpenAI-uyumlu `response_format={"type": "json_object"}` DESTEKLENİYOR (api-docs.deepseek.com).
  İKİ TUZAK — ikisi de burada kapatıldı:
    1) Prompt'ta "json" KELİMESİ geçmek ZORUNDA (system ya da user), yoksa model boş/serbest
       metin dönebiliyor. `_json_kelimesi_garanti()` geçmiyorsa sisteme kısa bir not ekler.
    2) max_tokens düşükse JSON ORTADAN kesilir ve ayrıştırma patlar — çağıran taraf
       max_tokens'ı beklenen çıktıya göre vermeli. finish_reason='length' geldiğinde
       log'a UYARI düşer (sessiz kırpılma bu projede daha önce veri kaybettirdi).
  DeepSeek'te `json_schema` (katı şema) YOK — yalnız serbest json_object var. "Sadece numara
  döndür" tipi işler (ai_kategori_backfill) için json_object + net format örneği yeterli.

Kullanım:
    from ai_ortak import ai_metin, ai_cagir

    metin = ai_metin("Sen bir analistsin.", "Şu veriyi yorumla: ...", max_tokens=700)
    if metin is None:
        ...  # AI yok/hata — eskisi gibi atla

    s = ai_cagir(SISTEM, PROMPT, max_tokens=1200, json_mod=True)
    if s["basari"]:
        veri = json.loads(s["metin"])

Env: AI_SAGLAYICI · DEEPSEEK_API_KEY · DEEPSEEK_MODEL (öntanım 'deepseek-chat') ·
     DEEPSEEK_URL (öntanım https://api.deepseek.com/chat/completions) · GEMINI_API_KEY ·
     GEMINI_MODEL (gemini_ortak okur).
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

VARSAYILAN_SAGLAYICI = "deepseek"
BILINEN_SAGLAYICILAR = ("deepseek", "gemini")

DEEPSEEK_VARSAYILAN_MODEL = "deepseek-chat"
DEEPSEEK_VARSAYILAN_URL = "https://api.deepseek.com/chat/completions"

# Yeniden denenebilir HTTP durumları. Kalıcı hatalarda (401 anahtar, 400 istek biçimi)
# tekrar denemek anlamsız — hemen yedek sağlayıcıya düşülür.
_GECICI_DURUMLAR = {408, 409, 425, 429, 500, 502, 503, 504}


# ── küçük yardımcılar ──────────────────────────────────────────────────────────
def _env(ad: str, ontanim: str = "") -> str:
    """Env'i ÇAĞRI ANINDA okur (modül import anında değil): cron `source .env` ile
    değişkenleri sonradan yükleyebiliyor, ayrıca test/otomasyonda monkeypatch mümkün olsun."""
    return (os.environ.get(ad) or ontanim).strip()


def deepseek_anahtar_var() -> bool:
    return bool(_env("DEEPSEEK_API_KEY"))


def gemini_anahtar_var() -> bool:
    return bool(_env("GEMINI_API_KEY"))


def ai_hata_logla(nerede: str, mesaj) -> str:
    """
    Hatayı stderr'e GÜRÜLTÜLÜ basar (flush'lı — cron log'unda tamponda kalmasın) ve mesajı döner.
    gemini_ortak.gemini_hata_logla ile aynı üslup: bu projede sessiz cron arızası 3 kez yaşandı,
    o yüzden hiçbir AI hatası yutulmaz.
    """
    if isinstance(mesaj, Exception):
        metin = f"{type(mesaj).__name__}: {mesaj}"
    else:
        metin = str(mesaj)
    print(f"  ✗ AI hatası ({nerede}): {metin[:400]}", file=sys.stderr, flush=True)
    return metin


def saglayici_sirasi() -> list:
    """
    [birincil, yedek] döner. AI_SAGLAYICI tanımsız/bilinmeyen ise 'deepseek' birincil olur
    (geriye uyum: env yoksa kod çökmez, öntanıma düşer).
    """
    birincil = _env("AI_SAGLAYICI", VARSAYILAN_SAGLAYICI).lower() or VARSAYILAN_SAGLAYICI
    if birincil not in BILINEN_SAGLAYICILAR:
        print(f"  ⚠ ai_ortak: bilinmeyen AI_SAGLAYICI='{birincil}' — "
              f"'{VARSAYILAN_SAGLAYICI}' kullanılıyor", file=sys.stderr, flush=True)
        birincil = VARSAYILAN_SAGLAYICI
    yedek = "gemini" if birincil == "deepseek" else "deepseek"
    return [birincil, yedek]


def _json_kelimesi_garanti(sistem: str, kullanici: str) -> tuple:
    """
    DeepSeek json_object modu prompt'ta "json" kelimesini ŞART koşuyor; yoksa model
    boş/serbest metin dönebiliyor. Geçmiyorsa sisteme kısa bir not ekler (semantiği bozmaz).
    """
    if "json" in (sistem or "").lower() or "json" in (kullanici or "").lower():
        return sistem, kullanici
    not_metni = "Yanıtını SADECE geçerli bir JSON nesnesi olarak ver (json), başka metin yazma."
    return ((sistem + "\n" + not_metni).strip() if sistem else not_metni), kullanici


# ── DeepSeek (OpenAI-uyumlu) ───────────────────────────────────────────────────
def _deepseek_cagir(sistem: str, kullanici: str, max_tokens: int, json_mod: bool,
                    temperature: float, model: str, zaman_asimi: int, deneme: int,
                    dusunme: bool = False) -> dict:
    """DeepSeek chat completion. Döner: {basari, metin, hata}.

    ⛔ DÜŞÜNME TUZAĞI (29 Tem, canlı ölçümle bulundu): deepseek-v4-* VARSAYILAN OLARAK
    reasoning yapıyor ve düşünme token'ları `max_tokens` bütçesinden HARCANIYOR. Küçük
    bütçelerde bütçenin tamamı düşünmeye gidiyor, `content` BOŞ ve `finish_reason='length'`
    dönüyor — yani iş sessizce sıfır satır yazıyor. (Ölçüm: max_tokens=64 istekte
    completion_tokens=45'in 38'i reasoning_tokens.) Bu, Gemini'deki `thinking_budget=0`
    tuzağının birebir aynısı.
    ÇALIŞAN KAPATMA: `"thinking": {"type": "disabled"}` → reasoning_tokens=None.
    ÇALIŞMAYANLAR (denendi): `reasoning_effort:"none"|"minimal"` → 400 (yalnız high/low/medium
    kabul ediliyor, yani hepsi düşünür); `enable_thinking:false` → sessizce YOK SAYILIYOR
    (reasoning_tokens=21 gelmeye devam etti).
    """
    anahtar = _env("DEEPSEEK_API_KEY")
    if not anahtar:
        return {"basari": False, "metin": None, "hata": "DEEPSEEK_API_KEY eksik (.env)"}

    if json_mod:
        sistem, kullanici = _json_kelimesi_garanti(sistem, kullanici)

    mesajlar = []
    if sistem:
        mesajlar.append({"role": "system", "content": sistem})
    mesajlar.append({"role": "user", "content": kullanici})

    govde = {
        "model": model or _env("DEEPSEEK_MODEL", DEEPSEEK_VARSAYILAN_MODEL),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "messages": mesajlar,
    }
    if json_mod:
        # DeepSeek yalnız serbest json_object destekliyor (json_schema YOK).
        govde["response_format"] = {"type": "json_object"}
    if not dusunme:
        # Düşünmeyi kapat — yoksa max_tokens bütçesi reasoning'e gider, content boş döner.
        govde["thinking"] = {"type": "disabled"}

    url = _env("DEEPSEEK_URL", DEEPSEEK_VARSAYILAN_URL)
    son_hata = "DeepSeek: bilinmeyen hata"
    json_geri_dus = False  # model json_object'i tanımadı → response_format'sız BİR kez daha dene
    for k in range(max(1, deneme)):
        gecici = False
        try:
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"},
                json=govde,
                timeout=zaman_asimi,
            )
        except Exception as e:
            son_hata = f"DeepSeek ağ hatası: {type(e).__name__}: {str(e)[:180]}"
            gecici = True
        else:
            if r.status_code == 200:
                try:
                    secim = (r.json().get("choices") or [{}])[0]
                    metin = ((secim.get("message") or {}).get("content") or "").strip()
                    bitis = secim.get("finish_reason")
                except Exception as e:
                    return {"basari": False, "metin": None,
                            "hata": f"DeepSeek yanıtı ayrıştırılamadı: {type(e).__name__}: {str(e)[:150]}"}
                if not metin:
                    # DeepSeek dokümanı bunu açıkça uyarıyor: ara sıra boş content dönebiliyor.
                    son_hata = f"DeepSeek boş yanıt döndü (finish_reason={bitis})"
                    gecici = True
                else:
                    if bitis == "length":
                        # Sessiz kırpılma: JSON modunda ayrıştırma patlar, düz metinde cümle yarıda kalır.
                        print(f"  ⚠ DeepSeek yanıtı max_tokens={max_tokens} sınırında KESİLDİ "
                              f"(finish_reason=length) — çıktı eksik olabilir", file=sys.stderr, flush=True)
                    return {"basari": True, "metin": metin, "hata": None}
            elif r.status_code in _GECICI_DURUMLAR:
                son_hata = f"DeepSeek {r.status_code}: {r.text[:180]}"
                gecici = True
            else:
                # Kalıcı (401/403/400 ...) — tekrar denemek israf, doğrudan yedeğe düşülsün.
                # TEK İSTİSNA: modelin json_object modunu tanımaması da 400 döndürür. Gemini
                # yedeği ÖLÜ olduğu için bu durumda iş tümden dururdu (gece kategori backfill'i
                # sıfır satır yazar). Çağıran taraflar zaten çıplak/```json çitli yanıtı
                # ayrıştırabiliyor (ai_kategori_backfill._json_ayikla, analyzer.json_parse_et)
                # → response_format'ı düşürüp BİR kez daha dene. Çıktı sözleşmesi prompt'ta
                # zaten yazılı olduğundan bu geri düşüş biçimi bozmaz.
                if json_mod and r.status_code == 400 and "response_format" in govde:
                    json_geri_dus = True
                    son_hata = f"DeepSeek 400 (json_object reddedildi): {r.text[:180]}"
                    break
                return {"basari": False, "metin": None,
                        "hata": f"DeepSeek {r.status_code}: {r.text[:180]}"}

        if not gecici or k == max(1, deneme) - 1:
            break
        bekle = min(2 ** k * 5, 60)
        print(f"  ⚠ {son_hata[:120]}; {bekle}s bekle (tekrar {k + 1}/{max(1, deneme) - 1})",
              file=sys.stderr, flush=True)
        time.sleep(bekle)

    if json_geri_dus:
        print(f"  ⚠ {son_hata[:140]} — response_format'sız tekrar deneniyor "
              f"(JSON biçimi prompt'tan gelecek)", file=sys.stderr, flush=True)
        return _deepseek_cagir(sistem, kullanici, max_tokens, False,
                               temperature, model, zaman_asimi, deneme, dusunme)

    return {"basari": False, "metin": None, "hata": son_hata}


# ── Gemini (yedek yol — gemini_ortak üzerinden) ────────────────────────────────
def _gemini_config(types, sistem: str, temperature: float, max_tokens: int,
                   json_mod: bool, dusunme: bool):
    """
    GenerateContentConfig kurar. `thinking_budget=0` ÖNTANIM: gemini-2.5-* düşünme AÇIKken
    tüm çıktı bütçesini "thoughts"a harcayıp METNİ BOŞ bırakabiliyor (gemini_ortak._bos_neden
    bunu raporluyor) — bu katmandaki işler basit metin/sınıflandırma, düşünmeye ihtiyaç yok.
    SDK sürümü ThinkingConfig'i tanımıyorsa (requirements.txt'teki httpx üçgeni notu: pip
    sessizce eski google-genai'ye düşebiliyor) alan sessizce atlanır, çağrı yine de kurulur.
    """
    alanlar = {"temperature": temperature}
    if max_tokens:
        alanlar["max_output_tokens"] = max_tokens
    if sistem:
        alanlar["system_instruction"] = sistem
    if json_mod:
        alanlar["response_mime_type"] = "application/json"
    if not dusunme:
        try:
            alanlar["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except Exception:
            pass
    try:
        return types.GenerateContentConfig(**alanlar)
    except Exception:
        alanlar.pop("thinking_config", None)
        return types.GenerateContentConfig(**alanlar)


def _gemini_cagir(sistem: str, kullanici: str, max_tokens: int, json_mod: bool,
                  temperature: float, model: str, dusunme: bool) -> dict:
    """Gemini chat (yalnız METİN). Döner: {basari, metin, hata}."""
    if not gemini_anahtar_var():
        return {"basari": False, "metin": None, "hata": "GEMINI_API_KEY eksik (.env)"}
    try:
        # Import FONKSİYON İÇİNDE: google-genai kurulu değilse bu modülün import'u ölmemeli
        # (api.py dolaylı olarak top-level import ediyor — tüm API düşerdi).
        from google.genai import types

        from gemini_ortak import (VARSAYILAN_MODEL, gemini_hata_logla, istemci_al,
                                  yanit_metni)
    except Exception as e:
        return {"basari": False, "metin": None,
                "hata": f"Gemini SDK/modülü yüklenemedi: {type(e).__name__}: {str(e)[:150]}"}

    kullanilan_model = model or VARSAYILAN_MODEL
    try:
        cfg = _gemini_config(types, sistem, temperature, max_tokens, json_mod, dusunme)
        try:
            resp = istemci_al().models.generate_content(
                model=kullanilan_model, contents=kullanici, config=cfg)
        except Exception as e:
            # Bazı modeller thinking_budget=0'ı reddediyor → düşünme ayarı olmadan BİR kez daha dene.
            if dusunme or "think" not in str(e).lower():
                raise
            print(f"  ⚠ Gemini düşünme ayarı reddedildi ({str(e)[:80]}) — ayarsız tekrar deneniyor",
                  file=sys.stderr, flush=True)
            cfg = _gemini_config(types, sistem, temperature, max_tokens, json_mod, dusunme=True)
            resp = istemci_al().models.generate_content(
                model=kullanilan_model, contents=kullanici, config=cfg)

        metin, bos_neden = yanit_metni(resp)
        if not metin:
            gemini_hata_logla("ai_ortak/boş yanıt", bos_neden)
            return {"basari": False, "metin": None, "hata": f"Gemini boş yanıt döndü ({bos_neden})"}
        return {"basari": True, "metin": metin, "hata": None}
    except Exception as e:
        return {"basari": False, "metin": None, "hata": gemini_hata_logla("ai_ortak", e)}


# ── Genel arayüz ───────────────────────────────────────────────────────────────
def ai_cagir(sistem: str, kullanici: str, max_tokens: int = 700, json_mod: bool = False,
             temperature: float = 0.4, model: str = None, zaman_asimi: int = 60,
             deneme: int = 1, dusunme: bool = False, nerede: str = "ai_cagir") -> dict:
    """
    Sağlayıcı-bağımsız metin üretimi.

    sistem      : sistem rolü metni (boş bırakılabilir — o zaman system mesajı gönderilmez)
    kullanici   : asıl prompt
    max_tokens  : çıktı üst sınırı. JSON modunda CÖMERT ver: kısa tutulursa yanıt ortadan
                  kesilir (DeepSeek finish_reason='length') ve ayrıştırma patlar.
    json_mod    : True ise DeepSeek `response_format=json_object`, Gemini
                  `response_mime_type=application/json` ile çağrılır.
    model       : sağlayıcının öntanım modelini ezmek için (normalde None bırakın — env'den gelir)
    deneme      : GEÇİCİ hatalarda (429/5xx/ağ) DeepSeek tekrar sayısı. ÖNTANIM 1 =
                  "eskisi gibi tek deneme" (mevcut çağrı yerlerinin davranışı değişmesin);
                  backfill gibi toplu işler 3-6 verebilir.
    dusunme     : yalnız Gemini yolunda — False (öntanım) düşünme bütçesini kapatır.

    Döner: {"basari": bool, "metin": str|None, "hata": str|None, "saglayici": str|None}
    """
    if not (kullanici or "").strip():
        return {"basari": False, "metin": None, "hata": "Boş prompt", "saglayici": None}

    hatalar = []
    for sira_no, saglayici in enumerate(saglayici_sirasi()):
        # ⚠ Model ezmesi YALNIZ BİRİNCİL sağlayıcıya uygulanır. `model` çağıran tarafın
        # (ör. ai_kategori_backfill'in AI_KATEGORI_MODEL'i) birincil sağlayıcıya göre
        # seçtiği bir addır; yedeğe düşerken aynı adı taşımak "deepseek-*" adını Gemini'ye
        # (ya da tersi) gönderip 400/404 üretir ve YEDEK YOLU DA ÖLDÜRÜR. Yedekte
        # sağlayıcının kendi öntanım modeli kullanılır.
        kullanilacak_model = model if sira_no == 0 else None
        if saglayici == "deepseek":
            sonuc = _deepseek_cagir(sistem, kullanici, max_tokens, json_mod,
                                    temperature, kullanilacak_model, zaman_asimi, deneme,
                                    dusunme)
        else:
            sonuc = _gemini_cagir(sistem, kullanici, max_tokens, json_mod,
                                  temperature, kullanilacak_model, dusunme)
        if sonuc["basari"]:
            sonuc["saglayici"] = saglayici
            if hatalar:
                # Yedeğe düşüldü — sessiz kalmasın, birincil sağlayıcının arızası log'da görünsün.
                print(f"  ↩ {nerede}: '{saglayici}' yedeğine düşüldü ({hatalar[0][:120]})",
                      file=sys.stderr, flush=True)
            return sonuc
        hatalar.append(f"{saglayici}: {sonuc['hata']}")

    hata = " | ".join(hatalar) if hatalar else "AI sağlayıcı yok"
    ai_hata_logla(nerede, hata)
    return {"basari": False, "metin": None, "hata": hata, "saglayici": None}


def ai_metin(sistem: str, kullanici: str, max_tokens: int = 700, json_mod: bool = False,
             temperature: float = 0.4, model: str = None, zaman_asimi: int = 60,
             deneme: int = 1, dusunme: bool = False, nerede: str = "ai_metin"):
    """
    ai_cagir'ın sade hâli: metni döner, HER TÜRLÜ başarısızlıkta None.
    (Anahtar yoksa da None — çağıran taraf eskisi gibi sessizce o adımı atlar.)
    """
    return ai_cagir(sistem, kullanici, max_tokens=max_tokens, json_mod=json_mod,
                    temperature=temperature, model=model, zaman_asimi=zaman_asimi,
                    deneme=deneme, dusunme=dusunme, nerede=nerede)["metin"]


def ai_durum() -> dict:
    """Teşhis için: hangi sağlayıcı birincil, hangi anahtarlar TANIMLI (değer basmaz)."""
    sira = saglayici_sirasi()
    return {
        "birincil": sira[0],
        "yedek": sira[1],
        "deepseek_anahtar": deepseek_anahtar_var(),
        "deepseek_model": _env("DEEPSEEK_MODEL", DEEPSEEK_VARSAYILAN_MODEL),
        "gemini_anahtar": gemini_anahtar_var(),
    }


if __name__ == "__main__":
    # Teşhis: `python ai_ortak.py` — anahtar DEĞERİ basmaz, yalnız var/yok bilgisi.
    d = ai_durum()
    print(f"birincil={d['birincil']} yedek={d['yedek']} "
          f"deepseek_anahtar={'var' if d['deepseek_anahtar'] else 'YOK'} "
          f"model={d['deepseek_model']} "
          f"gemini_anahtar={'var' if d['gemini_anahtar'] else 'YOK'}")
