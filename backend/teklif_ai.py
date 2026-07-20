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
"""

import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.5-flash")


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
        response = _model.generate_content(prompt)
        metin = (response.text or "").strip()
        if not metin:
            return {"basari": False, "hata": "Gemini boş yanıt döndü.", "kapsam": None, "neden": None, "yontem": None}

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
        return {"basari": False, "hata": str(e), "kapsam": None, "neden": None, "yontem": None}
