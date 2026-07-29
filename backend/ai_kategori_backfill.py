# -*- coding: utf-8 -*-
"""
ai_kategori_backfill.py — JENERİK kova ilanlarını AI ile 41 kanonik kategoriye oturtur.

SAĞLAYICI (29 Tem): Gemini servis hesabı öldü (401 UNAUTHENTICATED) → metin/sınıflandırma
işleri ai_ortak.py üzerinden DeepSeek'e taşındı. Bu dosya artık Gemini SDK'sını doğrudan
ÇAĞIRMAZ; tek kapı `ai_ortak.ai_cagir`. Anahtar varsa Gemini otomatik YEDEK olarak kalır.
(Bu dosyada embedding/görsel çağrısı YOKTU — tek çağrı türü metin sınıflandırmaydı.)

NEDEN: Eşleştirme motorunun (uygun-firma/benzer-ihale) asıl körlüğü OKAS değil (OKAS %2,8) —
ilanların %58'i "Mal Alımı"/"Hizmet Alımı"/"Diğer" JENERİK kovada; bunlar EKAP'ın satınalma
TÜRÜ, sektör değil → "konusu ne?" sorusuna cevap vermiyor. Bu katman başlığa (varsa OKAS'a)
bakıp iş-dostu kanonik sektöre atar (site filtresi/harita/sektör bildirimi + eşleştirme zenginleşir).
17 Tem'de kapsam 'Diğer'den → tüm jenerik kovalara genişletildi (bkz. migration_ai_kategori_jenerik.sql).

TASARIM (maliyet güvenliği):
  • Her satır ömründe YALNIZCA BİR KEZ AI'a gider. Sonuç yazıldıktan sonra ilanlar.ai_kategori_denendi
    damgalanır (bkz. migration_ai_kategori.sql) → satır bir daha ASLA seçilmez. Kaç kez çalıştırırsan
    çalıştır aynı satıra ikinci kez token harcanmaz (idempotent).
  • AI serbest metin DEĞİL, 1..41 arası NUMARA döndürür; numara KANONIK_KATEGORILER dizinine eşlenir →
    yazılan değer daima geçerli bir filtre seçeneğidir. 0/kararsız → satır 'Diğer' kalır ama denendi işaretlenir.
  • --limit ile üst sınır; paket başına 50 başlık (tek istek) → ~2K istek/100K satır.

⛔ ÇIKTI SÖZLEŞMESİ DOKUNULMAZ: prompt metni ve "başlık no → kategori no" JSON biçimi
   sağlayıcı geçişinde HARFİ HARFİNE korundu. Numaralandırma kayarsa ayrıştırma sessizce
   yanlış kategori yazar (veriyi BOZAN hata). Numara doğrulaması (1..41 aralık kontrolü)
   ikinci savunma hattıdır: aralık dışı/çöp yanıt kategori YAZDIRAMAZ, satır jenerik kalır.

MALİYET (yaklaşık, DeepSeek V4-Flash $0.14/M girdi · $0.28/M çıktı): ~5K girdi + ~0.4K çıktı
tokeni/istek ≈ $0.0008/istek. 173K satırlık birikmiş kuyruk (~3.5K istek) ≈ $3 (tek seferlik).
Günlük cron (--limit 400 → ~8 istek) fiilen bedava.
⚠ Token sayıları TAHMİNİdir (bkz. _tahmini_tok): ai_ortak sağlayıcı-bağımsız olduğu için
  usage_metadata dönmüyor. Rapor edilen $ FATURA DEĞİL, tavan/projeksiyon içindir.

KULLANIM:
  python ai_kategori_backfill.py --dry-run              # 1 paketi sınıflandır, YAZMA, kuyruk+maliyet projeksiyonu
  python ai_kategori_backfill.py --limit 500            # 500 satır işle (nightly cron için tipik)
  python ai_kategori_backfill.py --limit 100000         # birikmiş kuyruğu boşalt
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env).
     AI sağlayıcı anahtarları ai_ortak'tan: DEEPSEEK_API_KEY / GEMINI_API_KEY, AI_SAGLAYICI, DEEPSEEK_MODEL.
     AI_KATEGORI_MODEL (İSTEĞE BAĞLI model ezmesi — boşsa sağlayıcının öntanımı kullanılır),
     AI_FIYAT_GIRDI/AI_FIYAT_CIKTI (USD/1M, projeksiyon için).
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ai_ortak import ai_cagir, ai_durum, saglayici_sirasi
from kategori_siniflandir import KANONIK_KATEGORILER

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Model ezmesi İSTEĞE BAĞLI. Boşsa None → ai_ortak sağlayıcının kendi env'inden seçer
# (DEEPSEEK_MODEL / GEMINI_MODEL). Eskiden burada 'gemini-2.5-flash' ÖNTANIMLIYDI; o sabit
# DeepSeek'e gönderilse 400 döndürürdü — bkz. _model_sec() güvenlik ağı.
_MODEL_EZME = os.environ.get("AI_KATEGORI_MODEL", "").strip() or None
BATCH_VARSAYILAN = 50
CHUNK = 60  # tek PATCH'te kaç UUID (id ~36 char; 60×~40≈2.4KB URL, nginx 414 altı — kategori_backfill ile aynı)
# Yaklaşık fiyat (USD / 1M token) — SADECE rapor/projeksiyon için; sağlayıcı güncellerse env'den ez.
# Öntanım DeepSeek V4-Flash (29 Tem): $0.14/M girdi, $0.28/M çıktı. (Gemini yedeğine düşülürse
# rapor edilen $ hafif düşük kalır; tavan yine de bir üst sınır uygular.)
FIYAT_GIRDI_1M = float(os.environ.get("AI_FIYAT_GIRDI", "0.14"))
FIYAT_CIKTI_1M = float(os.environ.get("AI_FIYAT_CIKTI", "0.28"))

# Günlük harcama defteri: {"2026-07-23": 0.4213, ...}. Aynı günde birden fazla tur
# (cron + elle) koşulsa bile tavan GÜN TOPLAMINA uygulanır — tek tur değil.
# ⚠ Dosya adı BİLEREK 'gemini' kaldı: yeniden adlandırmak DeepSeek'e geçiş günü defteri
# sıfırlar ve o gün tavan iki kez harcanabilirdi. İçerik sağlayıcıdan bağımsızdır.
HARCAMA_DEFTER = os.path.join(os.path.dirname(__file__), ".gemini_gunluk_harcama.json")


def _bugun():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def harcama_oku(gun=None):
    gun = gun or _bugun()
    try:
        with open(HARCAMA_DEFTER) as f:
            return float(json.load(f).get(gun, 0.0))
    except Exception:
        return 0.0


def harcama_ekle(usd):
    """Bugünün toplamına ekle. 14 günden eski kayıtları temizler (defter küçük kalsın)."""
    gun = _bugun()
    try:
        with open(HARCAMA_DEFTER) as f:
            d = json.load(f)
    except Exception:
        d = {}
    d[gun] = round(d.get(gun, 0.0) + usd, 6)
    # eski günleri at
    from datetime import timedelta
    esik = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    d = {k: v for k, v in d.items() if k >= esik}
    with open(HARCAMA_DEFTER, "w") as f:
        json.dump(d, f)
    return d[gun]

# Numaralı kategori bloğu bir kez kurulur (prompt'ta sabit).
_KATEGORI_BLOK = "\n".join(f"{i + 1}) {k}" for i, k in enumerate(KANONIK_KATEGORILER))


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


_model_onbellek = []  # [deger] — uyarı paket başına DEĞİL, tur başına bir kez basılsın


def _model_sec():
    """AI_KATEGORI_MODEL ezmesini YALNIZ aktif sağlayıcıya aitse uygular, aksi halde None.

    Geriye uyum güvenlik ağı: eski .env/cron satırlarında bu değişken 'gemini-2.5-flash'
    YAZILI kalmış olabilir. Onu olduğu gibi DeepSeek'e yollamak 400 döndürür ve tur ölür →
    yabancı sağlayıcıya ait model adını sessizce değil, UYARIYLA yok say."""
    if _model_onbellek:
        return _model_onbellek[0]
    if not _MODEL_EZME:
        _model_onbellek.append(None)
        return None
    birincil = saglayici_sirasi()[0]
    ad = _MODEL_EZME.lower()
    yabanci = ("gemini" in ad and birincil != "gemini") or ("deepseek" in ad and birincil != "deepseek")
    if yabanci:
        print(f"  ⚠ AI_KATEGORI_MODEL='{_MODEL_EZME}' aktif sağlayıcı '{birincil}' ile uyumsuz "
              f"— yok sayılıyor, sağlayıcının öntanım modeli kullanılacak.", file=sys.stderr, flush=True)
        _model_onbellek.append(None)
        return None
    _model_onbellek.append(_MODEL_EZME)
    return _MODEL_EZME


# Üretim ayarları (sağlayıcı-bağımsız):
#   json_mod=True   → DeepSeek response_format=json_object / Gemini response_mime_type=application/json.
#   temperature=0   → deterministik, tutarlı sınıflandırma (eski davranışla aynı).
#   dusunme=False   → YALNIZ Gemini yedeğinde etkili: thinking_budget=0 ile "thoughts" tokeni harcanmaz
#                     (1-41 numara seçimi için düşünmeye gerek yok; thoughts çıktı fiyatından faturalanır).
#                     DeepSeek'te düşünme bayrağı YOK — karşılığı düşük temperature + kısa max_tokens.
_URETIM_TEMP = 0.0
# Çıktı bütçesi: paket başına ~1 kısa JSON girdisi ("50": 41,) ≈ 8-10 token. CÖMERT ver —
# max_tokens yetmezse DeepSeek yanıtı ORTADAN keser (finish_reason=length), JSON ayrıştırma
# patlar ve paket 'denendi' damgalanıp boşa gider (ai_ortak bunu uyarı olarak loglar).
def _cikti_butcesi(batch_boyu):
    return max(400, batch_boyu * 14 + 200)


def _tahmini_tok(metin):
    """Kaba token tahmini: ~3 karakter/token (Türkçe sondan eklemeli → İngilizceden yoğun).

    NEDEN TAHMİN: ai_ortak sağlayıcı-bağımsız tek arayüz olduğu için usage_metadata dönmüyor.
    Bu sayı YALNIZCA maliyet projeksiyonu ve --gunluk-usd tavanı içindir, FATURA DEĞİLDİR.
    Kasten hafif YÜKSEK tutuldu: tavan erken durur (aşım riski yerine erken duruş)."""
    return max(1, len(metin or "") // 3)


def _json_ayikla(metin):
    """Yanıtı JSON'a çevirir. Sözleşmeyi DEĞİŞTİRMEZ — yalnız ```json ... ``` çitini soyar.

    json_object/response_mime_type ikisi de temiz JSON vaat eder, ama sağlayıcı arada çit
    ekleyebiliyor; çiti soymak ayrıştırmayı sağlamlaştırır, numaralandırmaya DOKUNMAZ.
    (Yanlış kategori yazma riski yok: numaralar aşağıda ayrıca 1..41 aralığında doğrulanıyor.)"""
    s = (metin or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return json.loads(s)


# DMO/Jandarma satırları hariç: kategori_backfill.py bu kaynakları başlık-kelime tahmininin ezmesini
# istemediği için ATLIYOR (kategorileri scrape anında DMO_KATEGORI_MAP ile otoriter atanır — bkz. o dosyanın
# guard'ı). AI backfill de aynı ilkeye uymalı: bir DMO satırı bilerek haritalanmamış karışık bir kovadan
# (ör. "Diğer İhale İlanları") 'Diğer' kaldıysa, bu BELİRSİZLİĞİN kendisidir — AI'ın tek bir kanoniğe
# zorlaması kategori_backfill'in koruduğu şeyi arkadan dolanıp bozardı (16 Tem incelemesinde bulundu).
_KAYNAK_HARIC = "not.in.(dmo,jandarma)"
# JENERİK kovalar: EKAP'ın satınalma-türü etiketleri (sektör değil) → AI ile kanoniğe oturtulacak.
# migration_ai_kategori_jenerik.sql'deki kuyruk indeksinin predicate'iyle BİREBİR aynı liste olmalı
# (aksi halde seçim indeks kullanamaz). 'İnşaat & Yapım' burada YOK — o legacy etiket migration'da
# deterministik olarak kanoniğe birleştirildi (AI'sız).
_JENERIK_KOVALAR = ("Diğer", "Mal Alımı", "Hizmet Alımı")
# PostgREST in.() — Türkçe/boşluklu değerler çift-tırnakla sarılır (virgül/boşluk ayracıyla karışmasın).
_KATEGORI_FILTRE = "in.(" + ",".join(f'"{k}"' for k in _JENERIK_KOVALAR) + ")"
# secim_cek'in uyguladığı TÜM filtrelerle BİREBİR aynı olmalı — aksi halde kuyruk_say hiç 0'a inmeyen
# satırları da sayar (ör. başlıksız jenerik) ve dry-run maliyet projeksiyonu şişer (16 Tem incelemesinde bulundu).
_KUYRUK_FILTRE = {"kategori": _KATEGORI_FILTRE, "ai_kategori_denendi": "is.null",
                  "baslik": "not.is.null", "kaynak": _KAYNAK_HARIC}


def kuyruk_say(client):
    """Denenmemiş + gerçekten işlenebilir JENERİK-kova satır sayısı (kuyruk boyu) — secim_cek ile aynı filtre.
    Hata durumunda -1 döner (content-range yokluğunu SESSİZCE 0'a yorumlamaz — bir HTTP hatası "kuyruk boş"
    ile karıştırılırsa migration eksikliği gibi gerçek sorunlar fark edilmeden geçerdi).

    ⚠ 29 Tem BULGU: bu fonksiyon başarısız olunca eskiden "migration uygulanmamış" diye SABİT bir
    teşhis basılıyordu. Kolon canlıda DOĞRULANDI (PostgREST: order=ai_kategori_denendi.desc → 42501
    'permission denied', 42703 DEĞİL; kontrol: uydurma kolon 42703 döndü) → migration UYGULANMIŞ.
    Yani o mesaj yanlış yönlendiriyordu. Artık gerçek HTTP durumu + gövde basılıyor; en olası
    gerçek sebep count=exact'in ifade zaman aşımına takılması (filtre eşleşmesi ~184K satır,
    anon ölçümünde 1.8s — 3s tavanının kenarı) ya da /rest/v1 hız limiti."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/ilanlar",
                   params={**_KUYRUK_FILTRE, "select": "id", "limit": "1"},
                   headers={**_headers(), "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"})
    if r.status_code >= 300:
        print(f"  ✗ Kuyruk sayımı HTTP {r.status_code}: {r.text[:300]}", file=sys.stderr, flush=True)
        return -1
    cr = r.headers.get("content-range", "*/0")
    try:
        return int(cr.split("/")[-1])
    except (ValueError, IndexError):
        return -1


def secim_cek(client, n):
    """Sıradaki n adet denenmemiş JENERİK-kova satırı (id, baslik, okas). İşlenen satırlar
    damgalandığı/yeniden-kategorize edildiği için her çağrı offset'siz SONRAKİ grubu döndürür."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/ilanlar",
                   params={**_KUYRUK_FILTRE, "select": "id,baslik,okas", "order": "id", "limit": str(n)},
                   headers=_headers())
    r.raise_for_status()
    return r.json()


def siniflandir(batch):
    """Paketi sınıflandırır. Döner: (atamalar {id: kategori_str}, (girdi_tok, cikti_tok)).
    (None, None) YALNIZCA AI çağrısı hard-fail ettiğinde (her iki sağlayıcı da başarısız) — main() bunu
    görünce işaretlemeden durur, sonraki tur tekrar dener. Yanıt ALINDI ama ayrıştırılamadıysa/beklenmeyen
    biçimdeyse (JSON hatası, güvenlik filtresi vb.) TOKEN ZATEN HARCANDI → boş atamalarla ({}, tok) döner,
    main() paketin TÜMÜNÜ yine de 'denendi' damgalar (aksi halde aynı 'zehirli' paket her turda yeniden
    seçilip yeniden faturalanır ve kuyruktaki sonraki satırlar hiç işlenmezdi — 16 Tem incelemesinde bulundu).

    ⛔ PROMPT METNİ SAĞLAYICI GEÇİŞİNDE HARFİ HARFİNE KORUNDU. Tamamı `kullanici` rolüne gider,
    `sistem` BİLEREK boş: sistem/kullanıcı diye bölmek modelin numaralandırmayı yorumlayışını
    değiştirebilir ve çıktı sözleşmesi sessizce kayabilirdi. (ai_ortak'ın json_mod'u prompt'ta
    "json" kelimesi arar; metinde "JSON biçiminde" geçtiği için ek not ENJEKTE EDİLMEZ — prompt
    bayt bayt aynı kalır.)"""
    satir_blok = "\n".join(
        f'{i + 1}) {(b.get("baslik") or "").strip()[:180]}' + (f'  [OKAS: {b["okas"]}]' if b.get("okas") else "")
        for i, b in enumerate(batch)
    )
    prompt = f"""Türkiye kamu ihale başlıklarını sınıflandıran bir asistansın. Aşağıda NUMARALI KATEGORİLER
ve NUMARALI İHALE BAŞLIKLARI var. Her başlık için en uygun TEK kategori numarasını seç.
Başlık hangi mal/hizmete dair belirsizse veya hiçbir kategori uymuyorsa 0 ver — ASLA uydurma, zorlama.

KATEGORİLER:
{_KATEGORI_BLOK}

BAŞLIKLAR:
{satir_blok}

Yanıtı SADECE şu JSON biçiminde ver (başka metin yok): başlık numarası → kategori numarası.
Örnek: {{"1": 30, "2": 0, "3": 12}}"""

    # deneme=6: geçici hatalarda (429/5xx/ağ) üstel backoff — tek bir yoğunluk dalgası koca turu
    # öldürmesin (eski _cagir_retry ile aynı sayı). Birincil sağlayıcı tümden düşerse ai_ortak
    # otomatik olarak yedeğe (Gemini) geçer ve bunu log'a düşer.
    s = ai_cagir("", prompt, max_tokens=_cikti_butcesi(len(batch)), json_mod=True,
                 temperature=_URETIM_TEMP, model=_model_sec(), deneme=6,
                 nerede="ai_kategori_backfill")
    if not s["basari"]:
        print(f"  ✗ AI kalıcı hata ({str(s['hata'])[:160]}) — tur durduruluyor.")
        return None, None  # hard-fail — işaretleme yok, sonraki tur aynı satırları tekrar dener

    tok = (_tahmini_tok(prompt), _tahmini_tok(s["metin"]))
    try:
        data = _json_ayikla(s["metin"])
    except (json.JSONDecodeError, TypeError):
        print(f"  ⚠ JSON ayrıştırılamadı (yanıt: {str(s['metin'])[:100]!r}) "
              f"— bu paket 'denendi' işaretlenip atlanacak (token harcandı, tekrar denenmeyecek).")
        return {}, tok
    if not isinstance(data, dict):
        print("  ⚠ Beklenen JSON nesnesi gelmedi — bu paket 'denendi' işaretlenip atlanacak.")
        return {}, tok

    atamalar = {}
    for i, b in enumerate(batch):
        try:
            no = int(data.get(str(i + 1), 0))
        except (ValueError, TypeError):
            no = 0
        if 1 <= no <= len(KANONIK_KATEGORILER):
            atamalar[b["id"]] = KANONIK_KATEGORILER[no - 1]
    return atamalar, tok


def yaz_kategoriler(client, atamalar):
    """Sınıflanan id'leri kategoriye göre gruplayıp toplu PATCH'ler."""
    grp = defaultdict(list)
    for _id, kat in atamalar.items():
        grp[kat].append(_id)
    for kat, ids in grp.items():
        for i in range(0, len(ids), CHUNK):
            idliste = ",".join(ids[i:i + CHUNK])
            r = client.patch(f"{SUPABASE_URL}/rest/v1/ilanlar",
                             params={"id": f"in.({idliste})"}, json={"kategori": kat},
                             headers={**_headers(), "Prefer": "return=minimal"})
            r.raise_for_status()


def isaretle(client, ids, zaman):
    """Tüm işlenen id'leri (sınıflansın/kalsın) denendi damgalar → tekrar seçilmezler."""
    for i in range(0, len(ids), CHUNK):
        idliste = ",".join(ids[i:i + CHUNK])
        r = client.patch(f"{SUPABASE_URL}/rest/v1/ilanlar",
                         params={"id": f"in.({idliste})"}, json={"ai_kategori_denendi": zaman},
                         headers={**_headers(), "Prefer": "return=minimal"})
        r.raise_for_status()


def _maliyet(gt, ct):
    return gt / 1e6 * FIYAT_GIRDI_1M + ct / 1e6 * FIYAT_CIKTI_1M


def _usage_tok(usage):
    """(girdi, çıktı) tokeni. Artık siniflandir'dan gelen TAHMİNİ 2'li demet (bkz. _tahmini_tok).
    Eskiden Gemini usage_metadata nesnesiydi; ai_ortak sağlayıcı-bağımsız olduğu için gerçek
    sayaç dönmüyor. Eski nesne biçimi de kabul edilir (elle/eski çağrı yerleri kırılmasın)."""
    if isinstance(usage, (tuple, list)):
        return int(usage[0] or 0), int(usage[1] or 0)
    gt = getattr(usage, "prompt_token_count", 0) or 0
    ct = ((getattr(usage, "candidates_token_count", 0) or 0)
          + (getattr(usage, "thoughts_token_count", 0) or 0))
    return gt, ct


def main():
    ap = argparse.ArgumentParser(description="AI kategori backfill (jenerik kovalar → 41 kanonik)")
    ap.add_argument("--limit", type=int, default=500, help="Bu turda işlenecek azami satır (öntanım 500)")
    ap.add_argument("--batch", type=int, default=BATCH_VARSAYILAN, help="İstek başına başlık (öntanım 50)")
    ap.add_argument("--rpm", type=int, default=0, help="Dakika başına azami istek (0=sınırsız; free tier için ~15)")
    ap.add_argument("--gunluk-usd", type=float, default=0.0,
                    help="GÜNLÜK harcama tavanı USD (0=sınırsız). Bugünün toplamı bu sınıra ulaşınca "
                         "tur bir sonraki istekten ÖNCE temiz durur. Defter: .gemini_gunluk_harcama.json")
    ap.add_argument("--dry-run", action="store_true", help="1 paketi sınıflandır, YAZMA; kuyruk+maliyet projeksiyonu")
    args = ap.parse_args()

    if args.limit <= 0 or args.batch <= 0:
        print("✗ --limit ve --batch pozitif olmalı (negatif/sıfır PostgREST'e geçersiz limit gönderir)")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın, yerel .env ölü)")
        sys.exit(1)
    # Geriye uyum: yeni env yoksa çökme YOK. DEEPSEEK_API_KEY tanımsızsa ai_ortak Gemini'ye düşer;
    # yalnızca HİÇBİR sağlayıcı anahtarı yoksa durulur (aksi halde tur boşuna kuyruğu tarardı).
    durum = ai_durum()
    if not (durum["deepseek_anahtar"] or durum["gemini_anahtar"]):
        print("✗ AI anahtarı yok — DEEPSEEK_API_KEY ya da GEMINI_API_KEY gerekli (backend/.env)")
        sys.exit(1)

    zaman = datetime.now(timezone.utc).isoformat()
    bekle_s = 60.0 / args.rpm if args.rpm > 0 else 0.0

    with httpx.Client(timeout=60) as client:
        kuyruk = kuyruk_say(client)
        if kuyruk < 0:
            # ⚠ Eskiden burada SABİT olarak "migration uygulanmamış" yazıyordu. 29 Tem'de canlıda
            # doğrulandı: ai_kategori_denendi kolonu VAR (PostgREST 42501 döndü, 42703 değil) →
            # o teşhis YANLIŞ yönlendiriyordu. Gerçek durum kodu/gövde yukarıda basıldı; ona bakın.
            print("✗ Kuyruk sayımı başarısız — yukarıdaki HTTP durumu/gövdesine bakın. Olası sebepler:\n"
                  "  · count=exact ifade zaman aşımı (jenerik kuyruk ~184K satır, 3s tavanının kenarında)\n"
                  "  · /rest/v1 hız limiti (429) ya da SUPABASE_URL yanlış/erişilemez\n"
                  "  · 42703 (kolon yok) görürseniz O ZAMAN migration eksiktir: "
                  "backend/migration_ai_kategori_jenerik.sql")
            sys.exit(1)
        model_adi = _model_sec() or (durum["deepseek_model"] if durum["birincil"] == "deepseek"
                                     else "sağlayıcı öntanımı")
        print(f"→ Kuyruk (denenmemiş jenerik: {', '.join(_JENERIK_KOVALAR)}): {kuyruk} satır | "
              f"sağlayıcı={durum['birincil']} (yedek: {durum['yedek']}) | model={model_adi}")

        if args.dry_run:
            batch = secim_cek(client, args.batch)
            if not batch:
                print("  Kuyruk boş — sınıflanacak satır yok.")
                return
            atamalar, usage = siniflandir(batch)
            if atamalar is None:
                print("  (AI çağrısı başarısız — yukarıdaki hataya bakın)")
                return
            print(f"\n→ DRY-RUN örnek ({len(batch)} başlık, {len(atamalar)} tanesi sınıflandı):")
            for b in batch:
                kat = atamalar.get(b["id"], "· jenerik kalır ·")
                print(f"   {kat[:42]:<44} ← {(b.get('baslik') or '')[:60]}")
            if usage:
                gt, ct = _usage_tok(usage)
                istek_tahmini = (kuyruk + args.batch - 1) // args.batch if kuyruk > 0 else 0
                print(f"\n→ Bu istek: ~{gt} girdi + ~{ct} çıktı tokeni (TAHMİNİ) ≈ ${_maliyet(gt, ct):.4f}")
                print(f"→ Tüm kuyruk projeksiyonu (~{istek_tahmini} istek): "
                      f"≈ ${_maliyet(gt * istek_tahmini, ct * istek_tahmini):.2f} (tek seferlik, yaklaşık)")
            print("\n(dry-run — yazma/işaretleme yapılmadı)")
            return

        # Günlük tavan: bugüne kadar (bu tur dahil değil) ne harcandı?
        gun_baslangic = harcama_oku()
        if args.gunluk_usd > 0:
            print(f"→ Günlük tavan: ${args.gunluk_usd:.2f} · bugün şu ana kadar: ${gun_baslangic:.4f}")
            if gun_baslangic >= args.gunluk_usd:
                print(f"✋ Günlük tavana zaten ulaşılmış (${gun_baslangic:.4f} ≥ ${args.gunluk_usd:.2f}) — "
                      f"bu tur hiç istek atmadan çıkıyor. Kuyruk: {kuyruk} satır.")
                return

        kalan = args.limit
        islenen = siniflanan = girdi_tok = cikti_tok = istek = 0
        while kalan > 0:
            # Tavan kontrolü — SONRAKİ istekten ÖNCE. Bu turun o ana kadarki maliyeti + gün başı
            # birikimi tavanı aşacaksa dur (istek atmadan → aşım yok).
            if args.gunluk_usd > 0:
                simdiki_gun_toplam = gun_baslangic + _maliyet(girdi_tok, cikti_tok)
                if simdiki_gun_toplam >= args.gunluk_usd:
                    print(f"   ✋ Günlük tavana ulaşıldı (${simdiki_gun_toplam:.4f} ≥ ${args.gunluk_usd:.2f}) "
                          f"— tur durduruluyor. Kalan kuyruk sonraki güne.")
                    break
            batch = secim_cek(client, min(args.batch, kalan))
            if not batch:
                break
            atamalar, usage = siniflandir(batch)
            if atamalar is None:
                break  # gerçek hard-fail (kota/anahtar) — işaretlemeden dur; sonraki tur aynı satırları bedava dener
            istek += 1
            if usage:
                gt, ct = _usage_tok(usage)
                girdi_tok += gt
                cikti_tok += ct
            try:
                if atamalar:
                    yaz_kategoriler(client, atamalar)
                isaretle(client, [b["id"] for b in batch], zaman)  # sınıflanan+kalan HEPSİ damgalanır
            except httpx.HTTPError as e:
                print(f"  ✗ Yazma hatası ({str(e)[:120]}) — tur durduruluyor (işaretlenmeyenler sonraki turda).")
                break
            islenen += len(batch)
            siniflanan += len(atamalar)
            kalan -= len(batch)
            if islenen % 500 == 0 or len(batch) < args.batch:
                print(f"   … {islenen} işlendi, {siniflanan} sınıflandı")
            if bekle_s:
                time.sleep(bekle_s)

        print(f"\n✓ Bitti: {islenen} işlendi, {siniflanan} kanonik kategoriye atandı, "
              f"{islenen - siniflanan} jenerik kaldı (denendi işaretli).")
        if istek:
            tur_maliyet = _maliyet(girdi_tok, cikti_tok)
            print(f"  {istek} istek · ~{girdi_tok} girdi + ~{cikti_tok} çıktı tokeni (TAHMİNİ) "
                  f"≈ ${tur_maliyet:.4f}")
            # Bu turun maliyetini günlük deftere işle → sonraki tur (aynı gün) tavanı bilerek başlar.
            gun_toplam = harcama_ekle(tur_maliyet)
            print(f"  📒 Bugünkü toplam AI harcaması (tahmini): ${gun_toplam:.4f}"
                  + (f" / ${args.gunluk_usd:.2f} tavan" if args.gunluk_usd > 0 else ""))


if __name__ == "__main__":
    main()
