# -*- coding: utf-8 -*-
"""
ai_kategori_backfill.py — JENERİK kova ilanlarını Gemini ile 41 kanonik kategoriye oturtur.

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

MALİYET (yaklaşık, gemini-2.5-flash): ~5K girdi + ~0.4K çıktı tokeni/istek. 100K satır tek-seferlik
temizlik ≈ birkaç $ (bir kez). Günlük cron (yeni Diğer'ler, ~birkaç istek) fiilen ücretsiz kotaya sığar.

KULLANIM:
  python ai_kategori_backfill.py --dry-run              # 1 paketi sınıflandır, YAZMA, kuyruk+maliyet projeksiyonu
  python ai_kategori_backfill.py --limit 500            # 500 satır işle (nightly cron için tipik)
  python ai_kategori_backfill.py --limit 100000         # birikmiş kuyruğu boşalt (paid key önerilir)
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY (backend/.env).
     AI_KATEGORI_MODEL (öntanım gemini-2.5-flash), AI_FIYAT_GIRDI/AI_FIYAT_CIKTI (USD/1M, projeksiyon için).
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
from google import genai
from google.genai import types

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import KANONIK_KATEGORILER

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

MODEL = os.environ.get("AI_KATEGORI_MODEL", "gemini-2.5-flash")
BATCH_VARSAYILAN = 50
CHUNK = 60  # tek PATCH'te kaç UUID (id ~36 char; 60×~40≈2.4KB URL, nginx 414 altı — kategori_backfill ile aynı)
# Yaklaşık fiyat (USD / 1M token) — SADECE rapor/projeksiyon için; sağlayıcı güncellerse env'den ez.
FIYAT_GIRDI_1M = float(os.environ.get("AI_FIYAT_GIRDI", "0.30"))
FIYAT_CIKTI_1M = float(os.environ.get("AI_FIYAT_CIKTI", "2.50"))

# Numaralı kategori bloğu bir kez kurulur (prompt'ta sabit).
_KATEGORI_BLOK = "\n".join(f"{i + 1}) {k}" for i, k in enumerate(KANONIK_KATEGORILER))


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _client_al():
    # embed_ortak.py ile aynı güncel SDK (google.genai). Eski google.generativeai artık desteklenmiyor.
    return genai.Client(api_key=GEMINI_API_KEY)


# response_mime_type=json → model geçerli JSON döndürmeye zorlanır (fence-strip'e gerek yok).
# temperature=0 → deterministik, tutarlı sınıflandırma.
# thinking_budget=0 → gemini-2.5-flash'ın varsayılan AÇIK düşünme modu kapatılır: 1-41 numara seçimi gibi
# basit bir görev için gereksiz "thoughts" tokeni harcanmasın (bu tokenler çıktı fiyatından faturalanır ve
# thinking açıksa raporlanan $ maliyeti gerçeğin altında kalırdı — 16 Tem incelemesinde bulundu).
_URETIM_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json", temperature=0,
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)


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
    ile karıştırılırsa migration eksikliği gibi gerçek sorunlar fark edilmeden geçerdi)."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/ilanlar",
                   params={**_KUYRUK_FILTRE, "select": "id", "limit": "1"},
                   headers={**_headers(), "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"})
    if r.status_code >= 300:
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


def _cagir_retry(client_ai, prompt, deneme=6):
    """generate_content'i üstel backoff ile dener. 503 (model aşırı yük) GEÇİCİdir — daha çok/uzun
    denenir (6 deneme, 120s'e kadar backoff) ki tek bir demand-spike koca turu öldürmesin.
    Kalıcı hata (kota/anahtar) → None (tur durur)."""
    for k in range(deneme):
        try:
            return client_ai.models.generate_content(model=MODEL, contents=prompt, config=_URETIM_CONFIG)
        except Exception as e:
            if k == deneme - 1:
                print(f"  ✗ Gemini kalıcı hata ({str(e)[:120]}) — tur durduruluyor.")
                return None
            bekle = min(2 ** k * 5, 120)
            print(f"  ⚠ Gemini hata ({str(e)[:80]}); {bekle}s bekle (tekrar {k + 1}/{deneme - 1})")
            time.sleep(bekle)
    return None


def siniflandir(client_ai, batch):
    """Paketi sınıflandırır. Döner: (atamalar {id: kategori_str}, usage).
    (None, None) YALNIZCA resp is None (gerçek API hard-fail, TOKEN HARCANMADI) için — main() bunu görünce
    işaretlemeden durur, sonraki tur bedavaya tekrar dener. Yanıt ALINDI ama ayrıştırılamadıysa/beklenmeyen
    biçimdeyse (JSON hatası, güvenlik filtresi vb.) TOKEN ZATEN HARCANDI → boş atamalarla ({}, usage) döner,
    main() paketin TÜMÜNÜ yine de 'denendi' damgalar (aksi halde aynı 'zehirli' paket her turda yeniden
    seçilip yeniden faturalanır ve kuyruktaki sonraki satırlar hiç işlenmezdi — 16 Tem incelemesinde bulundu)."""
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

    resp = _cagir_retry(client_ai, prompt)
    if resp is None:
        return None, None  # gerçek hard-fail (kota/anahtar) — token harcanmadı, bedava retry

    usage = getattr(resp, "usage_metadata", None)
    try:
        data = json.loads(resp.text or "")
    except (json.JSONDecodeError, TypeError):
        print(f"  ⚠ JSON ayrıştırılamadı (yanıt: {str(getattr(resp, 'text', ''))[:100]!r}) "
              f"— bu paket 'denendi' işaretlenip atlanacak (token harcandı, tekrar denenmeyecek).")
        return {}, usage
    if not isinstance(data, dict):
        print("  ⚠ Beklenen JSON nesnesi gelmedi — bu paket 'denendi' işaretlenip atlanacak.")
        return {}, usage

    atamalar = {}
    for i, b in enumerate(batch):
        try:
            no = int(data.get(str(i + 1), 0))
        except (ValueError, TypeError):
            no = 0
        if 1 <= no <= len(KANONIK_KATEGORILER):
            atamalar[b["id"]] = KANONIK_KATEGORILER[no - 1]
    return atamalar, usage


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
    """(girdi, çıktı) tokeni. Çıktı, candidates + thoughts'u kapsar (thinking_budget=0 olsa da bazı
    modeller birkaç 'thoughts' tokeni yazabilir; ikisi de çıktı fiyatından faturalanır — dahil etmezsek
    rapor edilen $ gerçek harcamanın altında kalır)."""
    gt = usage.prompt_token_count or 0
    ct = (usage.candidates_token_count or 0) + (getattr(usage, "thoughts_token_count", 0) or 0)
    return gt, ct


def main():
    ap = argparse.ArgumentParser(description="AI kategori backfill (jenerik kovalar → 41 kanonik)")
    ap.add_argument("--limit", type=int, default=500, help="Bu turda işlenecek azami satır (öntanım 500)")
    ap.add_argument("--batch", type=int, default=BATCH_VARSAYILAN, help="İstek başına başlık (öntanım 50)")
    ap.add_argument("--rpm", type=int, default=0, help="Dakika başına azami istek (0=sınırsız; free tier için ~15)")
    ap.add_argument("--dry-run", action="store_true", help="1 paketi sınıflandır, YAZMA; kuyruk+maliyet projeksiyonu")
    args = ap.parse_args()

    if args.limit <= 0 or args.batch <= 0:
        print("✗ --limit ve --batch pozitif olmalı (negatif/sıfır PostgREST'e geçersiz limit gönderir)")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın, yerel .env ölü)")
        sys.exit(1)
    if not GEMINI_API_KEY:
        print("✗ GEMINI_API_KEY eksik (.env)")
        sys.exit(1)

    client_ai = _client_al()
    zaman = datetime.now(timezone.utc).isoformat()
    bekle_s = 60.0 / args.rpm if args.rpm > 0 else 0.0

    with httpx.Client(timeout=60) as client:
        kuyruk = kuyruk_say(client)
        if kuyruk < 0:
            print("✗ Kuyruk sayımı başarısız (HTTP hatası) — muhtemelen migration_ai_kategori.sql henüz "
                  "uygulanmamış (ai_kategori_denendi kolonu yok) ya da SUPABASE_URL yanlış/erişilemez.\n"
                  "  Önce çalıştırın: docker exec -i supabase-db psql -U postgres -d postgres "
                  "< backend/migration_ai_kategori.sql")
            sys.exit(1)
        print(f"→ Kuyruk (denenmemiş jenerik: {', '.join(_JENERIK_KOVALAR)}): {kuyruk} satır | model={MODEL}")

        if args.dry_run:
            batch = secim_cek(client, args.batch)
            if not batch:
                print("  Kuyruk boş — sınıflanacak satır yok.")
                return
            atamalar, usage = siniflandir(client_ai, batch)
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
                print(f"\n→ Bu istek: {gt} girdi + {ct} çıktı tokeni ≈ ${_maliyet(gt, ct):.4f}")
                print(f"→ Tüm kuyruk projeksiyonu (~{istek_tahmini} istek): "
                      f"≈ ${_maliyet(gt * istek_tahmini, ct * istek_tahmini):.2f} (tek seferlik, yaklaşık)")
            print("\n(dry-run — yazma/işaretleme yapılmadı)")
            return

        kalan = args.limit
        islenen = siniflanan = girdi_tok = cikti_tok = istek = 0
        while kalan > 0:
            batch = secim_cek(client, min(args.batch, kalan))
            if not batch:
                break
            atamalar, usage = siniflandir(client_ai, batch)
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
            print(f"  {istek} istek · {girdi_tok} girdi + {cikti_tok} çıktı tokeni ≈ ${_maliyet(girdi_tok, cikti_tok):.4f}")


if __name__ == "__main__":
    main()
