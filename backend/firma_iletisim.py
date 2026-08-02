# -*- coding: utf-8 -*-
"""
Firma İletişim Bilgileri — Gemini (google-genai) + Google Search GROUNDING.

Kullanıcı 1 kredi ile bir firmanın iletişim bilgilerini (telefon/e-posta/adres/web/yetkili)
WEB'DEN derletir. DeepSeek DEĞİL Gemini: `google_search` aracı GERÇEK web araması yapıp
kaynak (grounding) döndürür → uydurma riski düşer, doğrulanabilir (SPIKE ile kanıtlandı:
gemini-3.1-flash-lite 2.1s'de gerçek telefon/adres + 4 kaynak döndürdü, bulamadığı alanı null bıraktı).

⚠️ UYDURMA YASAK: model yalnız arama sonuçlarında GÖRDÜĞÜNÜ yazar; bulamazsa alanı null bırakır.
   Sonuç kullanıcıya DAİMA "AI tarafından Google'dan derlendi, KESİN DEĞİLDİR, doğrulayın" + kaynak
   linkleriyle sunulur (uyarı metni frontend'de). Bu modül veriyi + kaynakları döndürür.

Cache: sonuç api.py'de ai_yorumlari (varlik_tip='firma_iletisim') tablosuna KALICI yazılır — aynı
firma tekrar istenirse Gemini'ye GİTMEDEN döner (kota/maliyet tasarrufu; iletişim bilgisi nadir değişir).

Neden ai_ortak DEĞİL: ai_ortak metin/chat kapısıdır (grounding YOK, DeepSeek birincil). Bu özellik
Gemini'ye + google_search aracına SIKI bağlı olduğu için doğrudan gemini_ortak istemcisini kullanır.
"""
import json
import os
import re

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

AI_MAX_TOKEN = 1500  # grounding + JSON + özet için cömert (spike'ta ~180 token yetti, güvenli üst sınır)

_PROMPT = """'{firma}' adlı Türkiye'de kayıtlı şirketin GÜNCEL İLETİŞİM BİLGİLERİNİ bulmak için web'de ARAMA YAP.
Güncel ve doğru veriye ulaşmak için MUTLAKA web aramasına dayan; ezberden/tahminle yanıt verme.
Şu alanları döndür (bulamadığın alanı null bırak, ASLA UYDURMA):
telefon, eposta, adres, web_sitesi, yetkili_kisi.
Yalnızca arama sonuçlarında GERÇEKTEN gördüğün bilgileri yaz; emin değilsen null bırak.
Kısa bir 'ozet' cümlesi ekle (şirketin ne yaptığı ve bilgilerin hangi kaynaktan geldiği).
Yanıtı SADECE şu JSON formatında ver, başka hiçbir metin ekleme:
{{"telefon":null,"eposta":null,"adres":null,"web_sitesi":null,"yetkili_kisi":null,"ozet":""}}"""


def _json_ayikla(metin: str):
    """Model çıktısından JSON nesnesini çıkar (markdown ``` çiti / etraf metni toleranslı)."""
    if not metin:
        return None
    t = metin.strip()
    t = re.sub(r"^```(?:json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1 or j < i:
        return None
    try:
        return json.loads(t[i:j + 1])
    except (ValueError, TypeError):
        return None


def firma_iletisim_getir(firma_adi: str) -> dict:
    """
    Döner: {"basari": bool,
            "veri": {telefon,eposta,adres,web_sitesi,yetkili_kisi,ozet}|None,
            "kaynaklar": [{"baslik":.., "uri":..}],
            "hata": str|None}
    """
    firma_adi = (firma_adi or "").strip()
    if not firma_adi:
        return {"basari": False, "veri": None, "kaynaklar": [], "hata": "Firma adı boş."}

    try:
        from google.genai import types
        from gemini_ortak import istemci_al, VARSAYILAN_MODEL, yanit_metni
    except Exception as e:
        return {"basari": False, "veri": None, "kaynaklar": [],
                "hata": f"Gemini SDK yüklenemedi: {type(e).__name__}: {str(e)[:150]}"}

    try:
        cfg = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,
            max_output_tokens=AI_MAX_TOKEN,
        )
        resp = istemci_al().models.generate_content(
            model=VARSAYILAN_MODEL, contents=_PROMPT.format(firma=firma_adi), config=cfg)

        metin, bos = yanit_metni(resp)
        if not metin:
            return {"basari": False, "veri": None, "kaynaklar": [],
                    "hata": f"Gemini boş yanıt: {bos}"}

        veri = _json_ayikla(metin)
        if not isinstance(veri, dict):
            return {"basari": False, "veri": None, "kaynaklar": [],
                    "hata": "Yanıt JSON olarak ayrıştırılamadı."}

        # Grounding kaynaklarını çıkar (title = alan adı; uri = google yönlendirme linki)
        kaynaklar, gorulen = [], set()
        for c in (getattr(resp, "candidates", None) or []):
            gm = getattr(c, "grounding_metadata", None)
            for ch in (getattr(gm, "grounding_chunks", None) or []):
                web = getattr(ch, "web", None)
                uri = getattr(web, "uri", None) if web else None
                if not uri:
                    continue
                baslik = getattr(web, "title", "") or "kaynak"
                if baslik in gorulen:
                    continue
                gorulen.add(baslik)
                kaynaklar.append({"baslik": baslik, "uri": uri})

        return {"basari": True, "veri": veri, "kaynaklar": kaynaklar[:6], "hata": None}

    except Exception as e:
        try:
            from gemini_ortak import gemini_hata_logla
            return {"basari": False, "veri": None, "kaynaklar": [],
                    "hata": gemini_hata_logla("firma_iletisim_getir", e)}
        except Exception:
            return {"basari": False, "veri": None, "kaynaklar": [],
                    "hata": f"{type(e).__name__}: {str(e)[:150]}"}


if __name__ == "__main__":
    import sys
    ad = sys.argv[1] if len(sys.argv) > 1 else "REC ULUSLARARASI İNŞAAT YATIRIM SANAYİ VE TİCARET ANONİM ŞİRKETİ"
    s = firma_iletisim_getir(ad)
    print(json.dumps(s, ensure_ascii=False, indent=2))
