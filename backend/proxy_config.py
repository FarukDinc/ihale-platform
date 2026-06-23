"""
İhalePlatform — Rotating Proxy Yapılandırması
EKAP IP blokajını önlemek için Webshare proxy entegrasyonu

Webshare.io:
    https://proxy.webshare.io → kayıt ol
    Dashboard → Proxy → Residential → Liste kopyala
    Aylık ~$10 ile başlar, Türkiye IP'leri var

.env'e ekle:
    PROXY_KULLANICI=webshare_kullanici
    PROXY_SIFRE=webshare_sifre
    PROXY_HOST=proxy.webshare.io
    PROXY_PORT=80
"""

import os
import random
from dotenv import load_dotenv

load_dotenv()

# ── Proxy Yapılandırması ──────────────────────────────────
PROXY_KULLANICI = os.environ.get("PROXY_KULLANICI", "")
PROXY_SIFRE     = os.environ.get("PROXY_SIFRE", "")
PROXY_HOST      = os.environ.get("PROXY_HOST", "proxy.webshare.io")
PROXY_PORT      = os.environ.get("PROXY_PORT", "80")

# Webshare rotating endpoint — her istekte yeni IP
PROXY_URL = f"http://{PROXY_KULLANICI}:{PROXY_SIFRE}@{PROXY_HOST}:{PROXY_PORT}"


def playwright_proxy_ayarlari() -> dict | None:
    """
    Playwright için proxy ayarları döndürür.
    Proxy yoksa None döner (geliştirme ortamı).
    """
    if not PROXY_KULLANICI or not PROXY_SIFRE:
        print("  ⚠️  Proxy ayarı yok — direkt bağlantı kullanılıyor")
        return None

    return {
        "server":   f"http://{PROXY_HOST}:{PROXY_PORT}",
        "username": PROXY_KULLANICI,
        "password": PROXY_SIFRE
    }


def requests_proxy_ayarlari() -> dict | None:
    """
    requests kütüphanesi için proxy ayarları.
    PDF indirme vs. için.
    """
    if not PROXY_KULLANICI or not PROXY_SIFRE:
        return None

    return {
        "http":  PROXY_URL,
        "https": PROXY_URL
    }
