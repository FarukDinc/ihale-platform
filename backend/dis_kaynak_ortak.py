# -*- coding: utf-8 -*-
"""
dis_kaynak_ortak.py — Cloudflare arkasındaki DIŞ (uluslararası) ihale kaynakları için
ORTAK yardımcı(lar). Şimdilik tek iş: FlareSolverr üzerinden HTML/XML çekmek.

NEDEN FlareSolverr: ADB ve AfDB, Cloudflare "managed challenge" ile korunuyor; düz
httpx/curl/cloudscraper 403 alır (keşifte kanıtlandı). FlareSolverr (Docker,
127.0.0.1:8191, --restart unless-stopped) BAŞ GÖRÜNMEZ Chromium ile challenge'ı çözer
ve çözülmüş HTML'i döndürür. Kanıt: AfDB RSS → 200 (~20 KB), ADB liste → 200 (~115 KB).

⚠️ FlareSolverr YAVAŞ (~3-8 sn/istek — Chromium render). Backfill'de sayfa başı BEKLE;
   gece cron'da AZ sayfa çek. Aynı anda TEK ağır FlareSolverr işi (proxy havuzu dersiyle
   aynı temkin — ama bu FlareSolverr; EKAP PROXY HAVUZUYLA İLGİSİ YOK, ona dokunma).

Env: FLARESOLVERR_URL (öntanım http://127.0.0.1:8191/v1) — sunucu taşımada değişebilir.
"""

import os

import httpx

# Sunucu taşımada değişebilir → env'den okunur (öntanım yerel Docker).
FLARESOLVERR_URL = os.environ.get("FLARESOLVERR_URL", "http://127.0.0.1:8191/v1")


def fs_cek(url, timeout=90, max_timeout_ms=60000):
    """Cloudflare arkasındaki bir URL'yi FlareSolverr ile çeker → çözülmüş HTML/XML metni.

    `max_timeout_ms`: FlareSolverr'ın challenge'ı çözmek için beklediği azami süre (ms).
    `timeout`: bizim httpx okuma süremiz (sn) — FlareSolverr yavaş olduğu için ondan büyük
    olmalı (öntanım 90 sn > 60 sn).

    Cloudflare 403'ünü FlareSolverr KENDİ İÇİNDE çözer → çağırana 403 SIZMAZ; ya çözülmüş
    gövde döner ya da RuntimeError. Hata (servis erişilemez / status != ok / geçersiz JSON)
    → RuntimeError yükseltir; çağıran yakalayıp retry/atlar (ungm/afdb deseni).
    """
    try:
        r = httpx.post(FLARESOLVERR_URL,
                       json={"cmd": "request.get", "url": url, "maxTimeout": max_timeout_ms},
                       timeout=timeout)
    except Exception as e:
        raise RuntimeError(f"FlareSolverr erişilemedi ({FLARESOLVERR_URL}): "
                           f"{type(e).__name__}: {str(e)[:120]}")
    try:
        d = r.json()
    except Exception:
        raise RuntimeError(f"FlareSolverr JSON değil (HTTP {r.status_code}): {r.text[:120]}")
    if d.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr: {d.get('message') or d.get('status')}")
    return (d.get("solution") or {}).get("response", "") or ""
