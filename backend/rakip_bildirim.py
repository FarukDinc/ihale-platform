"""
Faz E1 — Rakip Takibi: gece cron'da ekap_sonuc_backfill.py'den SONRA çalışır.
Son taramada (scrape_tarihi >= şimdi - PENCERE_SAAT) yeni yazılan ihale_sonuclari
satırlarını, takip_firmalar'daki kullanıcıların takip ettiği firma adlarıyla
karşılaştırır; eşleşme varsa bildirimler'e kayıt açar VE (bildirim_email tercihi
açıksa) hemen e-posta gönderir — idare_bildirim.py ile aynı desen.

Eşleştirme firma_normalize.normalize_ad() ile YAPILIYOR (ham iki-yönlü substring DEĞİL) —
"ABC İNŞAAT A.Ş." (takip edilen) ile "ABC İnşaat Ltd. Şti." (kazanan) gibi sadece şirket
eki farklı olan yazımların da eşleşmesi için (bkz. firma_normalize.py, aynı normalizasyon
yukleniciler tablosunda ve firma-analiz.html'de de kullanılıyor).

DB tarafı: backend/migration_takip_firmalar.sql (takip_firmalar tablosu, UYGULANMADI —
bkz. YAPILACAKLAR.md). Migration uygulanmadan bu script 404/42P01 ile sessizce çıkar
(cron'u çökertmez).

SMS HENÜZ YOK — hiçbir SMS sağlayıcı entegrasyonu yok, ayrı iş.

Kullanım: python rakip_bildirim.py
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY (backend/.env)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from firma_normalize import normalize_ad
from notify import auth_email_map, resend_gonder, para_fmt, tarih_fmt

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL     = os.environ.get("SITE_URL", "https://ihaleglobal.com")
# Pencere yalnızca AYNI turda yeni yazılan sonuç satırlarını kapsamalı (yaş ~saatler). 26h idi;
# ~24h cron ile örtüşüp aynı kazanımı ardışık iki gece bildiriyordu (mükerrer e-posta). Bkz.
# idare_bildirim.py aynı düzeltme. (Kalıcı çözüm: bildirimler'de (kullanici_id,ilan_id,tur) dedup.)
PENCERE_SAAT = 20


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def esleşiyor(firma_ad: str, kazanan: str) -> bool:
    # Çıplak iki-yönlü substring ('MERT' → 'DEMERT YAPI') alakasız firmalarda yanlış
    # bildirim üretiyordu. Kelime-tabanlı: tam eşitlik VEYA kısa adın TÜM kelimeleri
    # uzun adda tam kelime olarak geçmeli.
    a, b = normalize_ad(firma_ad), normalize_ad(kazanan)
    if not a or not b:
        return False
    if a == b:
        return True
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return False
    kucuk, buyuk = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    # Tek kelimelik çok kısa adlarda (<3 harf) aşırı-eşleşmeyi engelle
    if len(kucuk) == 1 and len(next(iter(kucuk))) < 3:
        return False
    return kucuk.issubset(buyuk)


def email_html(kullanici_adi, kazanan, kazanimlar):
    """Takip edilen firmanın yeni kazandığı ihaleler için basit HTML e-posta."""
    satirlar = ""
    for k in kazanimlar:
        satirlar += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600;color:#111827;margin-bottom:4px;">{k['baslik']}</div>
            <div style="font-size:13px;color:#6b7280;">
              Kazanan teklif: {para_fmt(k.get('kazanan_teklif'))} · Sonuç tarihi: {tarih_fmt(k.get('sonuc_tarihi'))}
            </div>
          </td>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;text-align:right;vertical-align:middle;">
            <a href="{SITE_URL}/ihale-detay?id={k['ilan_id']}"
               style="display:inline-block;background:#f59e0b;color:#1a1a1a;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">
              Detay →
            </a>
          </td>
        </tr>""" if k.get("ilan_id") else f"""
        <tr>
          <td colspan="2" style="padding:16px;border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600;color:#111827;">{k['baslik']}</div>
            <div style="font-size:13px;color:#6b7280;">Kazanan teklif: {para_fmt(k.get('kazanan_teklif'))}</div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Inter,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <tr>
          <td style="background:#0A1628;padding:24px 32px;">
            <span style="font-size:22px;font-weight:800;color:white;">İhale<span style="color:#F0A500;">Global</span></span>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 32px 12px;border-bottom:1px solid #e5e7eb;">
            <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#111827;">
              🏆 Takip Ettiğiniz Firma Yeni Bir İhale Kazandı
            </h1>
            <p style="margin:0;font-size:14px;color:#6b7280;">
              Merhaba {kullanici_adi}, <strong>{kazanan}</strong> {len(kazanimlar)} yeni ihale kazandı.
            </p>
          </td>
        </tr>
        <tr><td><table width="100%" cellpadding="0" cellspacing="0">{satirlar}</table></td></tr>
        <tr>
          <td style="padding:24px 32px;text-align:center;border-top:1px solid #e5e7eb;">
            <a href="{SITE_URL}/firma-analiz?firma={quote(kazanan, safe='')}"
               style="display:inline-block;background:#0A1628;color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;">
              Firmanın Tüm Geçmişini Gör →
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
              Bu e-postayı almak istemiyorsanız
              <a href="{SITE_URL}/bildirimler" style="color:#f59e0b;">bildirim tercihlerinizi güncelleyin</a>.
              <br>© 2026 İhaleGlobal
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)

    esik = (datetime.now(timezone.utc) - timedelta(hours=PENCERE_SAAT)).isoformat()

    with httpx.Client(timeout=60.0) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/ihale_sonuclari",
            params={
                "select": "id,ilan_id,kazanan_firma,kazanan_teklif,sonuc_tarihi",
                "scrape_tarihi": f"gte.{esik}",
                "kazanan_firma": "not.is.null",
                "limit": "5000",
            },
            headers=_headers(),
        )
        if r.status_code == 404 or r.status_code == 400:
            print(f"  [rakip_bildirim] ihale_sonuclari/scrape_tarihi henüz yok ({r.status_code}) — atlanıyor.")
            return
        if r.status_code >= 300:
            print(f"✗ ihale_sonuclari sorgu hatası: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        sonuclar = r.json()

        r2 = c.get(
            f"{SUPABASE_URL}/rest/v1/takip_firmalar",
            params={"select": "kullanici_id,firma_ad"},
            headers=_headers(),
        )
        if r2.status_code == 404:
            print("  [rakip_bildirim] takip_firmalar tablosu henüz yok (migration_takip_firmalar.sql uygulanmadı) — atlanıyor.")
            return
        if r2.status_code >= 300:
            print(f"✗ takip_firmalar sorgu hatası: {r2.status_code} {r2.text[:200]}")
            sys.exit(1)
        takipler = r2.json()

        if not sonuclar or not takipler:
            print(f"  [rakip_bildirim] {len(sonuclar)} yeni sonuç, {len(takipler)} takip — eşleşecek bir şey yok.")
            return

        ilan_ids = list({s["ilan_id"] for s in sonuclar if s.get("ilan_id")})
        ilan_map = {}
        if ilan_ids:
            r3 = c.get(
                f"{SUPABASE_URL}/rest/v1/ilanlar",
                params={"select": "id,baslik", "id": f"in.({','.join(ilan_ids)})"},
                headers=_headers(),
            )
            if r3.status_code < 300:
                ilan_map = {i["id"]: i.get("baslik") for i in r3.json()}

        # kullanici_id -> {kazanan_firma: [sonuc, sonuc, ...]} — bildirim + e-posta gruplaması için
        eslesmeler = {}
        for sonuc in sonuclar:
            kazanan = sonuc.get("kazanan_firma") or ""
            if not kazanan:
                continue
            eslesen_kullanicilar = {t["kullanici_id"] for t in takipler if esleşiyor(t["firma_ad"], kazanan)}
            for kid in eslesen_kullanicilar:
                eslesmeler.setdefault(kid, {}).setdefault(kazanan, []).append(sonuc)

        if not eslesmeler:
            print(f"  [rakip_bildirim] {len(sonuclar)} yeni sonuç tarandı, eşleşme yok.")
            return

        kullanici_ids = list(eslesmeler.keys())
        r4 = c.get(
            f"{SUPABASE_URL}/rest/v1/profil",
            params={"select": "user_id,firma_adi,bildirim_email", "user_id": f"in.({','.join(kullanici_ids)})"},
            headers=_headers(),
        )
        if r4.status_code >= 300:
            # Sessizce {} dönmek e-postaları bastırıp 'başarılı' raporlar (bkz. takip_firmalar 403 dersi) — uyar.
            print(f"    ⚠ profil sorgusu başarısız ({r4.status_code}): {r4.text[:150]} — e-posta tercihleri okunamadı, e-posta atlanacak")
        profil_map = {p["user_id"]: p for p in r4.json()} if r4.status_code < 300 else {}
        email_map = auth_email_map() if any(profil_map.get(k, {}).get("bildirim_email") for k in kullanici_ids) else {}

        gonderildi = 0
        eposta_sayisi = 0
        for kid, firma_gruplari in eslesmeler.items():
            for kazanan, kazanimlar in firma_gruplari.items():
                baslik = ilan_map.get(kazanimlar[0].get("ilan_id")) or "bir ihale"
                icerik = (
                    f"Takip ettiğiniz \"{kazanan}\" firması {len(kazanimlar)} yeni ihale kazandı."
                    if len(kazanimlar) > 1
                    else f"Takip ettiğiniz \"{kazanan}\" firması \"{baslik}\" işini kazandı."
                )
                bildirim = {
                    "kullanici_id": kid,
                    # baslik NOT NULL — eskiden dict'e HİÇ eklenmiyordu (yalnız icerik içinde
                    # kullanılıyordu) → her yazımda 23502 NOT NULL ihlali, bildirim düşüyordu
                    # (21 Tem gece cron'unda yakalandı; nadir tetiklendiği için gözden kaçmış).
                    "baslik": (f"🏆 {kazanan} ihale kazandı")[:120],
                    "tur": "rakip_hareketi",
                    "icerik": icerik,
                    "aksiyon_url": f"/firma-analiz?firma={quote(kazanan, safe='')}",
                    "okundu": False,
                }
                rb = c.post(f"{SUPABASE_URL}/rest/v1/bildirimler", json=bildirim, headers=_headers())
                if rb.status_code < 300:
                    gonderildi += 1
                else:
                    print(f"    ✗ bildirim yazma hatası ({kid}): {rb.status_code} {rb.text[:150]}")

                profil = profil_map.get(kid) or {}
                if profil.get("bildirim_email"):
                    email = email_map.get(str(kid))
                    if email:
                        kullanici_adi = profil.get("firma_adi") or email.split("@")[0]
                        subject = f"🏆 {kazanan} yeni bir ihale kazandı — İhaleGlobal"
                        kazanimlar_zengin = [{**k, "baslik": ilan_map.get(k.get("ilan_id")) or "bir ihale"} for k in kazanimlar]
                        if resend_gonder(email, subject, email_html(kullanici_adi, kazanan, kazanimlar_zengin)):
                            eposta_sayisi += 1

        print(f"✓ rakip_bildirim: {len(sonuclar)} yeni sonuç tarandı, {gonderildi} bildirim, {eposta_sayisi} e-posta gönderildi.")


if __name__ == "__main__":
    main()
