"""
Kurum (İdare) Takibi — gece cron'da run_scraper.sh'in ANA taramasından SONRA çalışır.
Son taramada (olusturulma >= şimdi - PENCERE_SAAT) yeni yazılan ilanlar satırlarını,
takip_idareler'daki kullanıcıların takip ettiği idare adlarıyla karşılaştırır;
eşleşme varsa bildirimler'e kayıt açar VE (bildirim_email tercihi açıksa) hemen
e-posta gönderir — rakip_bildirim.py'nin (Faz E1) aynı deseni, idare için.

Yeni ihale fırsatı zaman-hassas olduğundan (notify.py'nin ertesi gün özet
e-postasını beklemeden) e-posta buradan anlık gönderilir.

DB tarafı: backend/migration_takip_idareler.sql (takip_idareler tablosu, UYGULANMADI
olabilir — bkz. YAPILACAKLAR.md). Migration uygulanmadan bu script 404/42P01 ile
sessizce çıkar (cron'u çökertmez).

Kullanım: python idare_bildirim.py
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY (backend/.env)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from notify import auth_email_map, resend_gonder, para_fmt, tarih_fmt

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL     = os.environ.get("SITE_URL", "https://ihaleglobal.com")
# Pencere yalnızca AYNI turda (bu run'ın scraper'ının) yeni yazdığı satırları kapsamalı —
# idare_bildirim ana taramadan hemen sonra çalışır, o satırlar en fazla ~2 saatlik. 26h idi;
# ~24h cron ile 2h örtüşüp aynı ihaleyi ARDIŞIK İKİ GECE bildiriyordu (mükerrer e-posta). 20h
# same-run satırları rahat kapsar, önceki gecenin (~24h) satırlarını dışlar.
PENCERE_SAAT = 20


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def email_html(kullanici_adi, idare, ilanlar):
    """Takip edilen idarenin yeni ilanları için basit HTML e-posta."""
    satirlar = ""
    for i in ilanlar:
        satirlar += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600;color:#111827;margin-bottom:4px;">{i['baslik']}</div>
            <div style="font-size:13px;color:#6b7280;">
              Son teklif: {tarih_fmt(i.get('son_teklif_tarihi'))} ·
              Tahmini: {para_fmt(i.get('yaklasik_maliyet_min'))}
            </div>
          </td>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;text-align:right;vertical-align:middle;">
            <a href="{SITE_URL}/ihale-detay?id={i['id']}"
               style="display:inline-block;background:#f59e0b;color:#1a1a1a;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">
              Detay →
            </a>
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
              🔔 Takip Ettiğiniz Kurum Yeni İhale Yayınladı
            </h1>
            <p style="margin:0;font-size:14px;color:#6b7280;">
              Merhaba {kullanici_adi}, <strong>{idare}</strong> {len(ilanlar)} yeni ihale yayınladı.
            </p>
          </td>
        </tr>
        <tr><td><table width="100%" cellpadding="0" cellspacing="0">{satirlar}</table></td></tr>
        <tr>
          <td style="padding:24px 32px;text-align:center;border-top:1px solid #e5e7eb;">
            <a href="{SITE_URL}/kurum-analiz?kurum={idare}"
               style="display:inline-block;background:#0A1628;color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;">
              Kurumun Tüm İhalelerini Gör →
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
            f"{SUPABASE_URL}/rest/v1/ilanlar",
            params={
                "select": "id,baslik,idare,son_teklif_tarihi,yaklasik_maliyet_min",
                "olusturulma": f"gte.{esik}",
                "limit": "5000",
            },
            headers=_headers(),
        )
        if r.status_code in (404, 400):
            print(f"  [idare_bildirim] ilanlar/olusturulma sorgusu başarısız ({r.status_code}) — atlanıyor.")
            return
        if r.status_code >= 300:
            print(f"✗ ilanlar sorgu hatası: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        yeni_ilanlar = r.json()

        r2 = c.get(
            f"{SUPABASE_URL}/rest/v1/takip_idareler",
            params={"select": "kullanici_id,idare_ad"},
            headers=_headers(),
        )
        if r2.status_code == 404:
            print("  [idare_bildirim] takip_idareler tablosu henüz yok (migration uygulanmadı) — atlanıyor.")
            return
        if r2.status_code >= 300:
            print(f"✗ takip_idareler sorgu hatası: {r2.status_code} {r2.text[:200]}")
            sys.exit(1)
        takipler = r2.json()

        if not yeni_ilanlar or not takipler:
            print(f"  [idare_bildirim] {len(yeni_ilanlar)} yeni ilan, {len(takipler)} takip — eşleşecek bir şey yok.")
            return

        # kullanici_id -> takip edilen idare adları (küçük harfe çevrilmiş, karşılaştırma için)
        kullanici_idareler = {}
        for t in takipler:
            kullanici_idareler.setdefault(t["kullanici_id"], set()).add((t["idare_ad"] or "").strip().lower())

        # kullanici_id -> {idare_ad: [ilan, ilan, ...]}
        eslesmeler = {}
        for ilan in yeni_ilanlar:
            idare = (ilan.get("idare") or "").strip()
            if not idare:
                continue
            idare_lower = idare.lower()
            for kid, takip_edilenler in kullanici_idareler.items():
                if idare_lower in takip_edilenler:
                    eslesmeler.setdefault(kid, {}).setdefault(idare, []).append(ilan)

        if not eslesmeler:
            print(f"  [idare_bildirim] {len(yeni_ilanlar)} yeni ilan tarandı, eşleşme yok.")
            return

        # E-posta tercihi açık kullanıcıları çek (sadece eşleşenler için)
        kullanici_ids = list(eslesmeler.keys())
        r3 = c.get(
            f"{SUPABASE_URL}/rest/v1/profil",
            params={"select": "user_id,firma_adi,bildirim_email", "user_id": f"in.({','.join(kullanici_ids)})"},
            headers=_headers(),
        )
        if r3.status_code >= 300:
            # Sessizce {} dönmek e-postaları bastırıp 'başarılı' raporlar (bkz. takip_firmalar 403 dersi) — uyar.
            print(f"    ⚠ profil sorgusu başarısız ({r3.status_code}): {r3.text[:150]} — e-posta tercihleri okunamadı, e-posta atlanacak")
        profil_map = {p["user_id"]: p for p in r3.json()} if r3.status_code < 300 else {}
        email_map = auth_email_map() if any(profil_map.get(k, {}).get("bildirim_email") for k in kullanici_ids) else {}

        bildirim_sayisi = 0
        eposta_sayisi = 0
        for kid, idare_gruplari in eslesmeler.items():
            for idare, ilanlar in idare_gruplari.items():
                icerik = (
                    f"\"{idare}\" {len(ilanlar)} yeni ihale yayınladı."
                    if len(ilanlar) > 1
                    else f"\"{idare}\" yeni bir ihale yayınladı: {ilanlar[0]['baslik'][:60]}"
                )
                bildirim = {
                    "kullanici_id": kid,
                    # baslik NOT NULL — rakip_bildirim.py ile aynı eksiklik (23502); dict'e
                    # hiç eklenmiyordu. Bu script çalışırsa aynı hatayı verirdi.
                    "baslik": (f"📢 {idare} yeni ihale")[:120],
                    "tur": "kurum_takip",
                    "icerik": icerik,
                    "aksiyon_url": f"/kurum-analiz?kurum={quote(idare, safe='')}",
                    "okundu": False,
                }
                rb = c.post(f"{SUPABASE_URL}/rest/v1/bildirimler", json=bildirim, headers=_headers())
                if rb.status_code < 300:
                    bildirim_sayisi += 1
                else:
                    print(f"    ✗ bildirim yazma hatası ({kid}): {rb.status_code} {rb.text[:150]}")

                profil = profil_map.get(kid) or {}
                if profil.get("bildirim_email"):
                    email = email_map.get(str(kid))
                    if email:
                        kullanici_adi = profil.get("firma_adi") or email.split("@")[0]
                        subject = f"🔔 {idare} yeni ihale yayınladı — İhaleGlobal"
                        if resend_gonder(email, subject, email_html(kullanici_adi, idare, ilanlar)):
                            eposta_sayisi += 1

        print(f"✓ idare_bildirim: {len(yeni_ilanlar)} yeni ilan tarandı, {bildirim_sayisi} bildirim, {eposta_sayisi} e-posta gönderildi.")


if __name__ == "__main__":
    main()
