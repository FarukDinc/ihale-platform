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

SAĞLAYICI (29 Tem): iki metin işi de artık ai_ortak.ai_cagir üzerinden gidiyor — birincil
DeepSeek, yedek Gemini (AI_SAGLAYICI ile ters çevrilebilir). Gemini servis hesabı 401
UNAUTHENTICATED verdiği için doğrudan Gemini çağrıları buradan kaldırıldı. Prompt'lar,
ayrıştırma ve dönüş sözleşmesi ({basari, metin/kapsam/neden/yontem, hata}) AYNEN korundu;
değişen tek şey taşıma katmanı.

Env: DEEPSEEK_API_KEY / DEEPSEEK_MODEL (birincil) · GEMINI_API_KEY (yedek) — bkz. ai_ortak.py.
"""

import json
import os

from dotenv import load_dotenv

from ai_ortak import ai_cagir

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Prompt'un "rol" kısmı sistem mesajına taşındı (metin BİREBİR aynı) — OpenAI-uyumlu
# sağlayıcılarda system/user ayrımı talimatlara daha iyi uyulmasını sağlıyor.
_TASLAK_SISTEM = (
    "Sen bir kamu ihalesi teklif metni yazarısın. Sana verilen GERÇEK verilere dayanarak bir "
    "teknik teklif taslağı yazacaksın. Uydurma teknik detay/sertifika/proje adı EKLEME — sadece "
    "verilen firma bilgilerini ve genel iyi-uygulama ifadelerini kullan."
)

# ── UV-1: İLAN METNİ / ŞARTNAME OKUMA (1 Ağu) ────────────────────────────────
# Teknik şartname İNDİRME EKAP'ta sertleşti (406 — Playwright gerekir, ertelendi). Ama ilan_metni
# ZATEN çekili (%75,8 kapsam, ~4K char, iş tanımı+kalem+idare içerir). AI bunu okuyup ihaleye ÖZGÜ
# {kapsam, kalemler, konu kelimeleri} çıkarır → benzer-ihale eşleştirmesi ve teklif bandı iyileşir
# (yaklaşık maliyet/il-tenzilat yoksa "band veremiyorum" yerine metinden çıkarım). Sağlayıcı-bağımsız
# (ai_ortak, env AI_SAGLAYICI). UYDURMA YASAK: yalnız metinde açıkça geçeni çıkarır, yoksa null.
_SARTNAME_SISTEM = (
    "Sen kamu ihale ilan ve şartname analistisin. Verilen ihale ilan metnini oku ve SADECE metinde "
    "AÇIKÇA yazan bilgiyi yapılandırılmış JSON olarak çıkar. Metinde OLMAYAN hiçbir şeyi UYDURMA — "
    "bilinmiyorsa null ya da boş liste bırak. Yalnız geçerli JSON döndür, başka açıklama yazma."
)


def _sartname_prompt(metin: str, meta: dict = None) -> tuple:
    """(sistem, kullanici) döndürür — sartname_oku ve sağlayıcı-kıyas harness'i AYNI prompt'u kullansın."""
    meta = meta or {}
    bilgi = ""
    if meta.get("baslik"):
        bilgi += f"Başlık: {meta['baslik']}\n"
    if meta.get("kategori"):
        bilgi += f"Mevcut kategori tahmini: {meta['kategori']}\n"
    kullanici = (
        bilgi + "\nİHALE İLAN METNİ:\n" + (metin or "")[:8000] + "\n\n"
        "Şu JSON şemasıyla çıkar (metinde olmayan alanı null/boş bırak):\n"
        '{"kapsam": "1-2 cümle: tam olarak ne alınıyor/yaptırılıyor",'
        ' "is_turu": "yapım|hizmet|mal|danışmanlık|bilinmiyor",'
        ' "kalemler": [{"ad": "kalem adı", "miktar": "sayı ya da null", "birim": "adet/m2/kg/ay/... ya da null"}],'
        ' "konu_kelimeler": ["benzer ihale eşleştirmesi için 5-10 kısa anahtar kelime"],'
        ' "tahmini_buyukluk_notu": "ölçek/büyüklük ipucu ya da null",'
        ' "yaklasik_maliyet_ipucu": "metinde açıkça geçen bedel/parasal limit ya da null"}'
    )
    return _SARTNAME_SISTEM, kullanici


def sartname_oku(metin: str, meta: dict = None) -> dict:
    """İlan metninden yapılandırılmış kapsam çıkarır (ai_ortak, env sağlayıcı).
    Döner: {"basari", "veri"(dict)|None, "saglayici", "hata"}."""
    if not metin or len(metin) < 100:
        return {"basari": False, "veri": None, "hata": "ilan metni yok/çok kısa", "saglayici": None}
    sistem, kullanici = _sartname_prompt(metin, meta)
    r = ai_cagir(sistem, kullanici, max_tokens=1000, json_mod=True, temperature=0.2, nerede="sartname_oku")
    if not r.get("basari") or not r.get("metin"):
        return {"basari": False, "veri": None, "hata": r.get("hata") or "AI boş yanıt", "saglayici": r.get("saglayici")}
    try:
        veri = json.loads(r["metin"])
    except (ValueError, TypeError) as e:
        return {"basari": False, "veri": None, "hata": f"JSON ayrıştırılamadı: {str(e)[:60]}", "saglayici": r.get("saglayici")}
    return {"basari": True, "veri": veri, "saglayici": r.get("saglayici"), "hata": None}


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

    return f"""İHALE:
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
        # max_tokens CÖMERT: üç bölümlü (KAPSAM/NEDEN/YONTEM) uzun metin — kısa tutulursa
        # yanıt ortadan kesilir ve ### ayrıştırması eksik bölüm döndürür.
        sonuc = ai_cagir(_TASLAK_SISTEM, prompt, max_tokens=2500,
                         nerede="teklif_taslak_uret")
        # Boş/hatalı yanıtı sessizce "veri yok" saymıyoruz: neden ai_ortak tarafında log'a düşer.
        if not sonuc["basari"]:
            return {"basari": False, "hata": f"AI yanıt üretemedi ({sonuc['hata']}).",
                    "kapsam": None, "neden": None, "yontem": None}
        metin = sonuc["metin"]

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
        return {"basari": False, "hata": f"{type(e).__name__}: {e}",
                "kapsam": None, "neden": None, "yontem": None}


# ═══════════════════════════════════════════════════════════════════════════════
# AI FİYAT/TEKLİF STRATEJİSİ
# ───────────────────────────────────────────────────────────────────────────────
# Taslak yazarından (yukarıda) AYRI bir iş: bu ihale için ne kadar teklif vermeli
# sorusuna, BENZER geçmiş ihalelerin GERÇEK tenzilat istatistiğiyle (analiz_pivot,
# tek-lot filtreli) grounded bir FİYAT BANDI önerir. Ucuz model yeter — ağır muhakeme
# yok, sadece SQL sayılarını Türkçe öneriye çevirmek.
# KVKK: yalnız kamuya açık ihale meta + toplu tenzilat gider; PII/gizli veri gitmez.
# Taşıma: ai_ortak.ai_cagir (birincil DeepSeek, yedek Gemini). Buradaki eski yerel
# DeepSeek istemcisi (_deepseek) ai_ortak._deepseek_cagir'a TAŞINDI — tek kopya kaldı.
# ═══════════════════════════════════════════════════════════════════════════════

_STRATEJI_SISTEM = (
    "Sen İhaleGlobal'de bir kamu ihale TEKLİF/FİYAT DANIŞMANISIN. Sana verilen GERÇEK "
    "istatistiklere (SQL'den, tek-lotlu sonuçlanmış ihalelerden) SADIK KAL; sayı uydurma. "
    "Kesin sonuç değil, VERİ TEMELLİ bir tahmin sunduğunu belirt. Yanıt Türkçe, kısa "
    "(4-6 cümle), düz metin (başlık/madde/markdown yok)."
)


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
    # max_tokens=700: eski _deepseek varsayılanıyla aynı (istenen çıktı 4-6 cümle).
    return ai_cagir(_STRATEJI_SISTEM, _strateji_prompt(ihale, kirilimlar),
                    max_tokens=700, nerede="teklif_strateji_uret")
