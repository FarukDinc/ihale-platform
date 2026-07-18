# -*- coding: utf-8 -*-
"""
dt_kazanan_scraper.py — Doğrudan Temin kazanan firma + bedel backfill.

BULGU (18 Tem 2026, canlı doğrulandı): DT sonuç sayfası (DogrudanTeminDetay.aspx)
CAPTCHA korumalı SANILIYORDU (bkz. hafıza dt-kazanan-captcha) ama Angular'ın verisini
çektiği ASIL JSON API'si (YeniIhaleAramaData.ashx?metot=dtDetayGetir) TAMAMEN AÇIK —
kimliksiz düz GET, hiç CAPTCHA çözmeden %100 başarıyla çalışıyor (dtAra/dtEnum ile
aynı sınıf: sayfa CAPTCHA'lı, altındaki API değil). Gemini/CAPTCHA-çözme GEREKMİYOR.

Akış: dogrudan_temin_ilanlari'nda durum "sonuç" grubunda + dt_ihale_token/dt_idare_token
dolu (ekap_dogrudan_temin_scraper.py retrofit sonrası doldurur, migration_dt_kazanan.sql
şart) + kazanan_denendi NULL satırları seçer; her biri için dtDetayGetir çağırıp
SozlesmeBilgisiList[]'i (bir dt_no'da BİRDEN FAZLA kalem olabilir) dogrudan_temin_sonuclari'na
yazar, ardından kazanan_denendi damgalar — bir daha seçilmez (idempotent,
ai_kategori_backfill.py ile AYNI "her satır ömründe bir kez" tasarımı, burada token
maliyeti sıfır olsa da EKAP'a gereksiz tekrar istek atmamak için aynı disiplin korunur).

ÖNKOŞUL: dt_ihale_token/dt_idare_token yalnız retrofit SONRASI scrape edilen satırlarda
dolu. Tarihsel ~1.48M satırın E10/E11'ini almak için önce TAM yeniden-tarama gerekir:
    python ekap_dogrudan_temin_scraper.py --reset --max-pages <büyük>
(CAPTCHA yok, yalnız zaman alır — ~11.6K sayfa × 128 kayıt.)

Kullanım:
  python dt_kazanan_scraper.py --dry-run              # birkaç dt_no çek, YAZMA, örnek göster
  python dt_kazanan_scraper.py --limit 500             # 500 dt_no işle (nightly cron için tipik)
  python dt_kazanan_scraper.py --limit 100000          # büyük backfill turu

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import os
import ssl
import sys
import time
from datetime import datetime, timezone

import httpx
from proxy_havuz import havuz_al, ekap_ssl_baglami
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ekap_sonuc_scraper import bedel_parse, tarih_iso  # normalize_ad ileride yuklenici_id linkleme turu için

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

EKAP_BASE = "https://ekap.kik.gov.tr"
ARAMA_ENDPOINT = f"{EKAP_BASE}/EKAP/Ortak/YeniIhaleAramaData.ashx"
BATCH_VARSAYILAN = 200
CHUNK = 60  # tek PATCH/POST'ta kaç kayıt (dt_no ~11 char, UUID'lerden çok daha kısa — geniş marj)

# dogrudan-temin.html DURUM_GRUP.sonuc ile BİREBİR — kazanan/bedel bekleyebileceğimiz TEK durum grubu.
DURUM_SONUC = ["Sonuç Duyurusu Yayımlanmış", "Doğrudan Temin Sonuçlandırıldı", "Sonuç Bilgileri Gönderildi"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")


def ssl_ctx():
    """EKAP eski/zayıf TLS cipher — modern OpenSSL varsayılanıyla handshake başarısız olur
    (aynı çözüm ekap_dogrudan_temin_scraper.py/ekap_sonuc_backfill.py'de de var)."""
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _durum_filtre():
    return f"in.({','.join(DURUM_SONUC)})"


def kuyruk_say(client):
    """Denenmemiş + token'ı olan + durumu sonuç grubunda olan dt_no sayısı."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                   params={"select": "dt_no", "dt_ihale_token": "not.is.null",
                           "kazanan_denendi": "is.null", "durum": _durum_filtre(), "limit": "1"},
                   headers={**_headers(), "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"})
    if r.status_code >= 300:
        return -1
    cr = r.headers.get("content-range", "*/0")
    try:
        return int(cr.split("/")[-1])
    except (ValueError, IndexError):
        return -1


def secim_cek(client, n):
    """Sıradaki n adet denenmemiş dt_no (+ token'ları). İşaretlenen satırlar sorgudan
    düştüğü için her çağrı offset'siz SONRAKİ grubu döndürür (ai_kategori_backfill.py deseni)."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                   params={"select": "dt_no,dt_ihale_token,dt_idare_token", "dt_ihale_token": "not.is.null",
                           "kazanan_denendi": "is.null", "durum": _durum_filtre(),
                           "order": "dt_no", "limit": str(n)},
                   headers=_headers())
    r.raise_for_status()
    return r.json()


def dt_detay_getir(havuz, dt_ihale_token, dt_idare_token):
    """dtDetayGetir çağırır. Hata/beklenmeyen yanıtta None (satır yine de 'denendi'
    işaretlenir — EKAP'ın kalıcı biçimde veri sunmadığı satırları sonsuza dek tekrar
    denemeyelim; gerçek ağ hatalarında script zaten üst seviyede duracak).

    İstek proxy havuzundan çıkan sıradaki IP ile gider (istek başına rotasyon).
    Başarısızlık havuza bildirilir ki bozuk/bloklu IP karantinaya alınsın —
    aksi halde ölü bir IP tüm turu sessizce boşa çıkarırdı."""
    try:
        with havuz.istek() as ist:
            r = ist.client.get(ARAMA_ENDPOINT, params={
                "metot": "dtDetayGetir", "idareId": dt_idare_token, "dogrudanTeminId": dt_ihale_token,
            })
            if r.status_code != 200:
                # 4xx/5xx: bu IP bloklanmış olabilir → cezalandır, tur devam etsin
                ist.basarisiz()
                return None
            return r.json()
    except Exception:
        # Ağ/TLS hatası: havuz zaten istisnayı görüp ucu cezalandırdı
        return None


def sozlesmeleri_cikar(dt_no, veri):
    """dtDetayGetir JSON'ından dogrudan_temin_sonuclari satırlarını üretir (0..N kalem)."""
    detay = (veri or {}).get("dogrudanTeminDetayResult") or {}
    sozlesmeler = (detay.get("SozlesmeBilgileri") or {}).get("SozlesmeBilgisiList") or []
    zaman = datetime.now(timezone.utc).isoformat()
    satirlar = []
    for s in sozlesmeler:
        satirlar.append({
            "dt_no": dt_no,
            "enc_sozlesme_id": s.get("EncSozlesmeID") or None,
            "kazanan_firma": (s.get("IstekliAdi") or "").strip() or None,
            "kazanan_bedel": bedel_parse(s.get("SozlesmeBedeli")),
            "sozlesme_tarihi": tarih_iso(s.get("SozlesmeTarihi")),
            "en_yuksek_teklif": bedel_parse(s.get("EnYuksekTeklif")),
            "en_dusuk_teklif": bedel_parse(s.get("EnDusukTeklif")),
            "sozlesme_mi": s.get("SozlesmeMi") if isinstance(s.get("SozlesmeMi"), bool) else None,
            "guncellenme": zaman,
        })
    return satirlar


def yaz_sonuclar(client, satirlar):
    """enc_sozlesme_id dolu satırlar upsert (idempotent); nadir NULL'lı eski kayıtlar
    dedup anahtarı olmadığından düz INSERT (kazanan_denendi ile zaten bir daha denenmez)."""
    if not satirlar:
        return
    dolu = [s for s in satirlar if s["enc_sozlesme_id"]]
    bos = [s for s in satirlar if not s["enc_sozlesme_id"]]
    for i in range(0, len(dolu), CHUNK):
        r = client.post(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_sonuclari",
                        headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
                        params={"on_conflict": "enc_sozlesme_id"}, json=dolu[i:i + CHUNK])
        r.raise_for_status()
    for i in range(0, len(bos), CHUNK):
        r = client.post(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_sonuclari",
                        headers={**_headers(), "Prefer": "return=minimal"}, json=bos[i:i + CHUNK])
        r.raise_for_status()


def isaretle(client, dt_no_listesi, zaman):
    """Tüm işlenen dt_no'ları (sözleşme bulunsun/bulunmasın) denendi damgalar."""
    for i in range(0, len(dt_no_listesi), CHUNK):
        idliste = ",".join(dt_no_listesi[i:i + CHUNK])
        r = client.patch(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                         params={"dt_no": f"in.({idliste})"}, json={"kazanan_denendi": zaman},
                         headers={**_headers(), "Prefer": "return=minimal"})
        r.raise_for_status()


def main():
    ap = argparse.ArgumentParser(description="DT kazanan/bedel backfill (dtDetayGetir — CAPTCHA gerekmez)")
    ap.add_argument("--limit", type=int, default=500, help="Bu turda işlenecek azami dt_no (öntanım 500)")
    ap.add_argument("--batch", type=int, default=BATCH_VARSAYILAN, help="Sorgu başına dt_no (öntanım 200)")
    ap.add_argument("--rpm", type=int, default=0, help="Dakika başına azami EKAP isteği (0=sınırsız; kibarlık için ~120 önerilir)")
    ap.add_argument("--dry-run", action="store_true", help="Birkaç dt_no çek, YAZMA; örnek sonuçları göster")
    args = ap.parse_args()

    if args.limit <= 0 or args.batch <= 0:
        print("✗ --limit ve --batch pozitif olmalı")
        sys.exit(1)
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın, yerel .env ölü)")
        sys.exit(1)

    zaman = datetime.now(timezone.utc).isoformat()

    # EKAP istekleri proxy havuzundan (istek başına IP rotasyonu + hız sınırı);
    # Supabase istekleri doğrudan gider — kendi sunucumuz, proxy'ye sokmanın anlamı yok.
    # --rpm havuzun KÜRESEL tavanını belirler; IP başına soğuma .env'den gelir
    # (PROXY_IP_ARALIK_SN). PROXY_LIST boşsa havuz direkt moda düşer ve yalnız
    # hız sınırı uygulanır — scraper kodu iki durumda da aynı.
    havuz = havuz_al(kuresel_rpm=(args.rpm if args.rpm > 0 else None),
                     ssl_baglami=ekap_ssl_baglami())

    with httpx.Client(timeout=60) as client:

        kuyruk = kuyruk_say(client)
        if kuyruk < 0:
            print("✗ Kuyruk sayımı başarısız — muhtemelen migration_dt_kazanan.sql uygulanmamış.\n"
                  "  Önce çalıştırın: docker exec -i supabase-db psql -U postgres -d postgres "
                  "< backend/migration_dt_kazanan.sql")
            sys.exit(1)
        print(f"→ Kuyruk (token'lı + denenmemiş + sonuç durumunda): {kuyruk} dt_no")

        if args.dry_run:
            batch = secim_cek(client, min(args.batch, 5))
            if not batch:
                print("  Kuyruk boş — dt_ihale_token dolu satır yok (retrofit sonrası ilk scrape turunu bekleyin).")
                return
            for row in batch:
                veri = dt_detay_getir(havuz, row["dt_ihale_token"], row["dt_idare_token"])
                satirlar = sozlesmeleri_cikar(row["dt_no"], veri)
                if satirlar:
                    for s in satirlar:
                        print(f"   {row['dt_no']}: {s['kazanan_firma']!r} — {s['kazanan_bedel']} TL ({s['sozlesme_tarihi']})")
                else:
                    print(f"   {row['dt_no']}: sözleşme verisi yok/boş (veri={('yok' if veri is None else 'boş liste')})")
            print("\n(dry-run — yazma/işaretleme yapılmadı)")
            return

        kalan = args.limit
        islenen = kazanim_sayisi = istek = 0
        while kalan > 0:
            batch = secim_cek(client, min(args.batch, kalan))
            if not batch:
                break
            tum_satirlar, dt_no_listesi = [], []
            for row in batch:
                veri = dt_detay_getir(havuz, row["dt_ihale_token"], row["dt_idare_token"])
                istek += 1
                tum_satirlar.extend(sozlesmeleri_cikar(row["dt_no"], veri))
                dt_no_listesi.append(row["dt_no"])
                # Elle sleep YOK: hız sınırı artık havuzda (IP başına soğuma +
                # küresel tavan). Burada ayrıca beklemek ikisini üst üste bindirirdi.
            try:
                yaz_sonuclar(client, tum_satirlar)
                isaretle(client, dt_no_listesi, zaman)
            except httpx.HTTPError as e:
                print(f"  ✗ Yazma hatası ({str(e)[:120]}) — tur durduruluyor (işaretlenmeyenler sonraki turda).")
                break
            islenen += len(batch)
            kazanim_sayisi += len(tum_satirlar)
            kalan -= len(batch)
            print(f"   … {islenen} dt_no işlendi, {kazanim_sayisi} sözleşme kaydı yazıldı ({istek} EKAP isteği)")

        print(f"\n✓ Bitti: {islenen} dt_no işlendi, {kazanim_sayisi} sözleşme kaydı (kazanan+bedel) yazıldı, "
              f"{istek} EKAP isteği (CAPTCHA/Gemini kullanılmadı).")

    # Hangi IP'ler kullanıldı, kaçı düştü, ne kadar hız sınırı beklendi —
    # blok yiyip yemediğimizi buradan görüyoruz.
    havuz.ozet_yaz()
    havuz.kapat()


if __name__ == "__main__":
    main()
