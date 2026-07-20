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
# Üst üste bu kadar dt_no GEÇİCİ hatayla çekilemezse turu durdur: EKAP'ı dövme, blok/kesinti
# olasılığında kibarca çekil. Çekilemeyen satırlar damgalanmadığı için sonraki gece tekrar denenir.
ARDISIK_HATA_SINIRI = 8

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


def secim_cek(client, n, offset=0):
    """Sıradaki n adet denenmemiş dt_no (+ token'ları). Damgalanan satırlar sorgudan
    düştüğü için ilerleme kısmen kendiliğinden olur (ai_kategori_backfill.py deseni);
    ancak GEÇİCİ hata alıp DAMGALANMAYAN satırlar NULL kalır ve offset'siz sorguda aynı
    tur içinde tekrar tekrar seçilir (poison satırda TAKILMA). Bu yüzden çağıran taraf,
    o tur damgalanmayan satır sayısını `offset` ile geçirir → pencere ileri kayar,
    çekilemeyen satırlar bu turda atlanır (bir sonraki gece yeniden denenir)."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                   params={"select": "dt_no,dt_ihale_token,dt_idare_token", "dt_ihale_token": "not.is.null",
                           "kazanan_denendi": "is.null", "durum": _durum_filtre(),
                           "order": "dt_no", "limit": str(n), "offset": str(offset)},
                   headers=_headers())
    r.raise_for_status()
    return r.json()


def dt_detay_getir(havuz, dt_ihale_token, dt_idare_token):
    """dtDetayGetir çağırır. Dönüş: (veri, damgalanabilir).

      · 200 + JSON  → (json, True)   : detay geldi (0..N sözleşme); satır işlendi,
                                        artık 'denendi' damgalanabilir.
      · gerçek 404  → (None, True)   : EKAP bu DT için detay SUNMUYOR (kalıcı yok);
                                        boşuna tekrar denememek için damgalanabilir.
      · GEÇİCİ hata → (None, False)  : blok/kesinti (403/407/429/5xx), ağ/TLS/timeout,
                                        proxy düşüşü, 200-ama-JSON-değil. DAMGALAMA —
                                        satır NULL kalsın, sonraki tur tekrar denesin.

    KRİTİK (eski hata): önceki sürüm HER non-200 ve HER istisnada None döndürüp çağıran
    tarafın satırı yine de damgalamasına yol açıyordu; geçici bir 403/timeout ile
    damgalanan satır bir daha SEÇİLMEDİĞİ için KALICI kayboluyordu. Artık gerçek 404 ile
    geçici hatayı ayırıyoruz; yalnız gerçek 404 damgalanabilir.

    İstek proxy havuzundan çıkan sıradaki IP ile gider (istek başına rotasyon).
    Blok kodları ist.yanit() ile, ağ/TLS istisnaları `with` bloğundan sızarak havuza
    bildirilir ki bozuk/bloklu IP karantinaya alınsın. httpx DIŞI istisnalar (özellikle
    havuzun 'TÜM IP DÜŞTÜ' / 'SAĞLAYICI ARIZASI' RuntimeError emniyet supapları) BİLEREK
    yakalanmaz — üst seviyeye çıkıp turu durdurmalılar."""
    try:
        with havuz.istek() as ist:
            r = ist.client.get(ARAMA_ENDPOINT, params={
                "metot": "dtDetayGetir", "idareId": dt_idare_token, "dogrudanTeminId": dt_ihale_token,
            })
            # 404 = "bu DT için detay yok" (uygulama yanıtı), IP sorunu DEĞİL.
            # ist.yanit() yalnız gerçek blok kodlarında (403/407/429/5xx) cezalandırır;
            # düz `!= 200 → basarisiz()` havuzu 404 seliyle kendi kendine öldürüyordu.
            ist.yanit(r)
            if r.status_code == 200:
                try:
                    return r.json(), True
                except ValueError:
                    # 200 ama gövde JSON değil → EKAP ara-katman/hata sayfası olabilir.
                    # IP sağlıklı olabilir (ucu cezalandırma), ama veriyi güvenilir sayma:
                    # geçici kabul et, DAMGALAMA.
                    return None, False
            if r.status_code == 404:
                return None, True  # gerçekten detay yok — kalıcı, damgalanabilir
            # 403/407/429/5xx ve diğer beklenmeyen kodlar → geçici, DAMGALAMA.
            return None, False
    except httpx.HTTPError:
        # Ağ/TLS/timeout/proxy düşüşü: havuz istisnayı `with`ten görüp ucu cezalandırdı.
        # Geçici say, DAMGALAMA. (RuntimeError'ı YUTMUYORUZ — bilinçli olarak yalnız
        # httpx.HTTPError yakalanır ki havuzun emniyet supapları üste çıksın.)
        return None, False


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
                veri, damgalanabilir = dt_detay_getir(havuz, row["dt_ihale_token"], row["dt_idare_token"])
                satirlar = sozlesmeleri_cikar(row["dt_no"], veri)
                if satirlar:
                    for s in satirlar:
                        print(f"   {row['dt_no']}: {s['kazanan_firma']!r} — {s['kazanan_bedel']} TL ({s['sozlesme_tarihi']})")
                elif not damgalanabilir:
                    print(f"   {row['dt_no']}: GEÇİCİ HATA (çekilemedi — canlıda damgalanmaz, tekrar denenir)")
                else:
                    print(f"   {row['dt_no']}: sözleşme verisi yok/boş (veri={('yok/404' if veri is None else 'boş liste')})")
            print("\n(dry-run — yazma/işaretleme yapılmadı)")
            return

        kalan = args.limit
        # damgalanan  : gerçekten işlenip 'denendi' damgalanan dt_no (200 veya gerçek 404)
        # cekilemeyen : GEÇİCİ hatayla çekilemeyen dt_no — DAMGALANMADI, sonraki turda denenir
        # offset      : damgalanmayan satırlar NULL kaldığı için sorgudan düşmez; onları bu tur
        #               tekrar seçmemek için pencereyi bu kadar ileri kaydırırız (TAKILMA önleme)
        # ardisik_hata: üst üste kaç dt_no geçici hata aldı (başarı sıfırlar) — tavanı aşınca dur
        damgalanan = kazanim_sayisi = istek = cekilemeyen = 0
        offset = ardisik_hata = 0
        dur = False
        while kalan > 0 and not dur:
            batch = secim_cek(client, min(args.batch, kalan), offset)
            if not batch:
                break
            tum_satirlar, dt_no_listesi = [], []
            for row in batch:
                veri, damgalanabilir = dt_detay_getir(havuz, row["dt_ihale_token"], row["dt_idare_token"])
                istek += 1
                if not damgalanabilir:
                    # GEÇİCİ hata (blok/ağ/TLS/timeout/proxy/200-ama-JSON-değil): DAMGALAMA.
                    # Satır NULL kalır; offset ile bu tur atlanır, sonraki gece tekrar denenir.
                    cekilemeyen += 1
                    ardisik_hata += 1
                    if ardisik_hata >= ARDISIK_HATA_SINIRI:
                        dur = True   # o ana dek toplananları yaz, sonra turu durdur
                        break
                    continue
                ardisik_hata = 0
                tum_satirlar.extend(sozlesmeleri_cikar(row["dt_no"], veri))
                dt_no_listesi.append(row["dt_no"])
                # Elle sleep YOK: hız sınırı artık havuzda (IP başına soğuma +
                # küresel tavan). Burada ayrıca beklemek ikisini üst üste bindirirdi.
            try:
                # Checkpoint (isaretle) YALNIZ veri yazıldıktan SONRA: yazma patlarsa
                # damgalama da atlanır, satırlar sonraki turda yeniden denenir.
                yaz_sonuclar(client, tum_satirlar)
                isaretle(client, dt_no_listesi, zaman)
            except httpx.HTTPError as e:
                print(f"  ✗ Yazma hatası ({str(e)[:120]}) — tur durduruluyor (işaretlenmeyenler sonraki turda).")
                break
            damgalanan += len(dt_no_listesi)
            kazanim_sayisi += len(tum_satirlar)
            if dur:
                print(f"  ✗ {ardisik_hata} ardışık dt_no çekilemedi (geçici hata) — EKAP'ı dövmemek için "
                      f"tur durduruldu; damgalanmayanlar sonraki gece tekrar denenecek.")
                break
            # Bu partide damgalanmayan (geçici hata) satır sayısı kadar pencereyi ilerlet.
            offset += len(batch) - len(dt_no_listesi)
            kalan -= len(batch)
            print(f"   … {damgalanan} dt_no damgalandı, {kazanim_sayisi} sözleşme kaydı yazıldı, "
                  f"{cekilemeyen} çekilemedi ({istek} EKAP isteği)")

        if cekilemeyen:
            print(f"\n⚠ Tur bitti (EKSİK): {damgalanan} dt_no damgalandı, {kazanim_sayisi} sözleşme kaydı "
                  f"(kazanan+bedel) yazıldı, {cekilemeyen} dt_no ÇEKİLEMEDİ (geçici hata — damgalanmadı, "
                  f"sonraki turda tekrar denenecek), {istek} EKAP isteği.")
        else:
            print(f"\n✓ Bitti: {damgalanan} dt_no işlendi, {kazanim_sayisi} sözleşme kaydı (kazanan+bedel) "
                  f"yazıldı, {istek} EKAP isteği (CAPTCHA/Gemini kullanılmadı).")

    # Hangi IP'ler kullanıldı, kaçı düştü, ne kadar hız sınırı beklendi —
    # blok yiyip yemediğimizi buradan görüyoruz.
    havuz.ozet_yaz()
    havuz.kapat()


if __name__ == "__main__":
    main()
