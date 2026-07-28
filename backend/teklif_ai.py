"""
AI Teklif Taslağı — Faz D4 (AI teklif workflow bağlantısı).

İlke (analyzer.py/firma_ai_yorum.py ile aynı): ham LLM çağrısı değil, GERÇEK veriyi
(ihale detayı + firmanın kendi profili + aynı idare/kategoride geçmişte kazanan firmaların
ortalama tenzilat davranışı — analiz_pivot RPC'sinden) prompt'a gömen bir yapı. AI sadece
bu verileri akıcı teklif metnine çeviriyor; "piyasa farkında" olması hedefleniyor
(bkz. YAPILACAKLAR.md D4: "benzer işleri geçmişte X,Y firmaları %Z tenzilatla aldı").

Kullanım (api.py içinden):
    from teklif_ai import teklif_taslak_uret
    sonuc = teklif_taslak_uret(ilan=ilan_dict, firma_profil=profil_dict, piyasa_baglami=[...])

Env: GEMINI_API_KEY (backend/.env) — analyzer.py ile aynı konfigürasyon.

SDK: google-genai (Backlog #34). Eski google.generativeai bırakıldı. İstemci gemini_ortak
üzerinden TEMBEL kurulur — api.py bu modülü top-level import ettiği için, anahtar yokken
modül seviyesinde Client() kurmak tüm API'yi import anında çökertirdi.
"""

import json
import os

import requests
from dotenv import load_dotenv

from gemini_ortak import VARSAYILAN_MODEL, gemini_hata_logla, istemci_al, yanit_metni

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def _prompt_olustur(ilan: dict, firma_profil: dict, piyasa_baglami: list) -> str:
    ihale_json = json.dumps({
        "baslik": ilan.get("baslik"),
        "idare": ilan.get("idare"),
        "il": ilan.get("il"),
        "kategori": ilan.get("kategori"),
        "tur": ilan.get("tur"),
        "isin_yapilacagi_yer": ilan.get("isin_yapilacagi_yer"),
        "ilan_ozeti": (ilan.get("ilan_metni") or "")[:3000],
    }, ensure_ascii=False, indent=2, default=str)

    firma_json = json.dumps({
        "firma_adi": firma_profil.get("firma_adi"),
        "yillik_ciro_tl": firma_profil.get("yillik_ciro_tl"),
        "calisma_illeri": firma_profil.get("calisma_illeri"),
        "referanslar": firma_profil.get("referanslar"),
    }, ensure_ascii=False, indent=2, default=str)

    piyasa_metni = "Bu idare/sektörde geçmiş sonuçlanan iş kaydı bulunamadı."
    if piyasa_baglami:
        # ort_tenzilat yalnız TEK KISIMLI ihalelerden hesaplanır (analiz_pivot FILTER lot_sayisi=1);
        # kısımlı ihalelerde EKAP kısım bazlı yaklaşık maliyet vermediğinden tenzilat bilinemez → NULL.
        # AI'ya "%None" gitmesin: tenzilat yoksa satırdan tamamen çıkar.
        satirlar = [
            f"- {p.get('grup_deger')}: {p.get('ihale_sayisi')} iş"
            + (f", ortalama tenzilat %{p.get('ort_tenzilat')}" if p.get("ort_tenzilat") is not None else "")
            for p in piyasa_baglami[:5]
        ]
        piyasa_metni = "Bu idare/sektörde geçmişte kazanan firmalar ve ortalama tenzilatları:\n" + "\n".join(satirlar)

    return f"""Sen bir kamu ihalesi teklif metni yazarısın. Aşağıdaki GERÇEK verilere dayanarak bir
teknik teklif taslağı yazacaksın. Uydurma teknik detay/sertifika/proje adı EKLEME — sadece verilen
firma bilgilerini ve genel iyi-uygulama ifadelerini kullan.

İHALE:
{ihale_json}

TEKLİF VEREN FİRMA:
{firma_json}

PİYASA BAĞLAMI (bu idare/sektörde geçmiş sonuçlar — sadece farkındalık için, teklif fiyatı YAZMA):
{piyasa_metni}

Üç ayrı bölüm yaz, HER BİRİ SADECE düz metin (madde işareti kullanabilirsin ama markdown başlık
kullanma), ve yanıtını TAM OLARAK şu formatta ver (her etiket kendi satırında, aralarında ### ayıracı):

KAPSAM:
<işin teknik kapsamına dair 3-5 cümle/madde — ilana özgü, idare/iş adını kullan>
###
NEDEN:
<firmanın bu işi neden en iyi şekilde yapabileceğine dair 2-4 cümle — firma profilindeki bilgilere
dayan, veri yoksa genel güven verici ama abartısız ifade kullan>
###
YONTEM:
<işin yürütülme yöntemine dair kısa fazlı bir plan (mobilizasyon/uygulama/teslim gibi), 3-5 madde>"""


def teklif_taslak_uret(ilan: dict, firma_profil: dict, piyasa_baglami: list) -> dict:
    """Döner: {"basari": bool, "kapsam": str, "neden": str, "yontem": str, "hata": str|None}"""
    if not ilan:
        return {"basari": False, "hata": "İhale bilgisi eksik.", "kapsam": None, "neden": None, "yontem": None}
    try:
        prompt = _prompt_olustur(ilan, firma_profil or {}, piyasa_baglami or [])
        response = istemci_al().models.generate_content(model=VARSAYILAN_MODEL, contents=prompt)
        # Boş yanıtı sessizce "veri yok" saymıyoruz: güvenlik bloğu/token limiti nedeni log'a düşsün.
        metin, bos_neden = yanit_metni(response)
        if not metin:
            gemini_hata_logla("teklif_taslak_uret/boş yanıt", bos_neden)
            return {"basari": False, "hata": f"Gemini boş yanıt döndü ({bos_neden}).",
                    "kapsam": None, "neden": None, "yontem": None}

        bolumler = {"kapsam": "", "neden": "", "yontem": ""}
        for parca in metin.split("###"):
            parca = parca.strip()
            for anahtar, etiket in (("kapsam", "KAPSAM:"), ("neden", "NEDEN:"), ("yontem", "YONTEM:")):
                if parca.upper().startswith(etiket):
                    bolumler[anahtar] = parca[len(etiket):].strip()

        if not any(bolumler.values()):
            return {"basari": False, "hata": "Yanıt formatı ayrıştırılamadı.", "kapsam": None, "neden": None, "yontem": None}

        return {"basari": True, "hata": None, **bolumler}
    except Exception as e:
        # google.genai.errors.APIError de Exception türevi — mevcut yakalama korunuyor.
        return {"basari": False, "hata": gemini_hata_logla("teklif_taslak_uret", e),
                "kapsam": None, "neden": None, "yontem": None}


# ═══════════════════════════════════════════════════════════════════════════════
# AI FİYAT/TEKLİF STRATEJİSİ — DeepSeek (OpenAI-uyumlu API)
# ───────────────────────────────────────────────────────────────────────────────
# Taslak yazarından (Gemini, yukarıda) AYRI bir iş: bu ihale için ne kadar teklif
# vermeli sorusuna, BENZER geçmiş ihalelerin GERÇEK tenzilat istatistiğiyle (analiz_pivot,
# tek-lot filtreli) grounded bir FİYAT BANDI önerir. Ucuz model yeter (deepseek-chat) —
# ağır muhakeme yok, sadece SQL sayılarını Türkçe öneriye çevirmek.
# KVKK: yalnız kamuya açık ihale meta + toplu tenzilat gider; PII/gizli veri gitmez.
# Env: DEEPSEEK_API_KEY (zorunlu) · DEEPSEEK_MODEL (öntanım 'deepseek-chat').
# ═══════════════════════════════════════════════════════════════════════════════

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

_STRATEJI_SISTEM = (
    "Sen İhaleGlobal'de bir kamu ihale TEKLİF/FİYAT DANIŞMANISIN. Sana verilen GERÇEK "
    "istatistiklere (SQL'den, tek-lotlu sonuçlanmış ihalelerden) SADIK KAL; sayı uydurma. "
    "Kesin sonuç değil, VERİ TEMELLİ bir tahmin sunduğunu belirt. Yanıt Türkçe, kısa "
    "(4-6 cümle), düz metin (başlık/madde/markdown yok)."
)


def _deepseek(sistem: str, kullanici: str, max_tokens: int = 700) -> dict:
    """DeepSeek chat completion (OpenAI-uyumlu). Döner: {basari, metin, hata}."""
    if not DEEPSEEK_API_KEY:
        return {"basari": False, "metin": None, "hata": "DEEPSEEK_API_KEY eksik (.env)"}
    try:
        r = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL, "temperature": 0.4, "max_tokens": max_tokens, "stream": False,
                "messages": [
                    {"role": "system", "content": sistem},
                    {"role": "user", "content": kullanici},
                ],
            },
            timeout=60,
        )
        if r.status_code != 200:
            return {"basari": False, "metin": None, "hata": f"DeepSeek {r.status_code}: {r.text[:180]}"}
        metin = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
        if not metin:
            return {"basari": False, "metin": None, "hata": "DeepSeek boş yanıt döndü"}
        return {"basari": True, "metin": metin, "hata": None}
    except Exception as e:
        return {"basari": False, "metin": None, "hata": f"DeepSeek hata: {e}"}


def _strateji_prompt(ihale: dict, kirilimlar: dict) -> str:
    veri = json.dumps(
        {"acik_ihale": ihale, "benzer_gecmis_tenzilat": kirilimlar},
        ensure_ascii=False, indent=2, default=str,
    )
    return f"""VERİ:
{veri}

Bu AÇIK ihale için firmaya bir TEKLİF/FİYAT STRATEJİSİ öner:
- Benzer geçmiş ihalelerde ortalama tenzilat yüzdesi ne? Kırılımlar: "il" = ihalenin ilindeki
  gerçekleşen ortalama tenzilat (EN ÖNEMLİ referans), "genel" = Türkiye geneli taban.
  İl verisi genelden sapıyorsa bunu yorumla.
- Buna göre yaklaşık maliyetin (yaklasik_maliyet_max/min) yaklaşık yüzde kaç ALTINA teklif vermek
  rekabetçi olur — somut bir TEKLİF BANDI (₺ alt – ₺ üst) ver.
- Rekabet yoğunluğu (ort_katilimci) yüksekse daha agresif, düşükse daha ihtiyatlı olmayı belirt.
- ÖNEMLİ: ort_tenzilat null ise o kırılımda tenzilat HESAPLANAMIYOR demektir — null'u "düşük tenzilat"
  sanma; tenzilat verisi yoksa onu belirt ya da o kırılımı atla.
Sadece öneri metnini yaz."""


def teklif_strateji_uret(ihale: dict, kirilimlar: dict) -> dict:
    """
    ihale: {baslik, kategori, il, tur, yaklasik_maliyet_min/max, tahmini_bedel}
    kirilimlar: {"kategori": [analiz_pivot satırı], "il": [...]} — ort_tenzilat/ort_bedel/
                ihale_sayisi/ort_katilimci içerir.
    Döner: {basari, metin, hata}
    """
    if not ihale:
        return {"basari": False, "metin": None, "hata": "İhale verisi yok"}
    if not any((kirilimlar or {}).values()):
        return {"basari": False, "metin": None,
                "hata": "Benzer geçmiş tenzilat verisi bulunamadı."}
    return _deepseek(_STRATEJI_SISTEM, _strateji_prompt(ihale, kirilimlar))
