"""
İhaleGlobal — Rotating Proxy Yapılandırması
EKAP IP blokajını önlemek için Webshare proxy entegrasyonu

Webshare.io:
    https://proxy.webshare.io → kayıt ol
    Dashboard → Proxy → Proxy List → İndir (100 IP:port, ortak kullanıcı/şifre)
    Alınan plan: Shared Datacenter, 100 proxy (Türkiye), 250GB/ay, ~$3/ay

NOT (14 Tem test): Webshare'in paylaşımlı "rotating gateway" endpoint'i
(p.webshare.io:80) bu planda AÇIK DEĞİL ("The proxy you are connecting is
not in your list." hatası) — bu plan sadece 100 sabit IP:port'un DOĞRUDAN
kullanımını destekliyor. Rotasyon bu yüzden istemci tarafında yapılıyor:
PROXY_LIST'ten her script çalıştırmasında rastgele 1 IP seçilir.

.env'e ekle:
    PROXY_KULLANICI=webshare_kullanici       (100 proxy için ORTAK)
    PROXY_SIFRE=webshare_sifre               (100 proxy için ORTAK)
    PROXY_LIST=ip1:port1,ip2:port2,...       (Webshare "Proxy List" indirmesinden)

PROXY_LIST boşsa/yoksa tüm proxy fonksiyonları None döner (proxy'siz direkt
bağlantı) — script'ler proxy yokken de sorunsuz çalışmaya devam eder.
"""

import os
import random
from dotenv import load_dotenv

load_dotenv()

# ── Proxy Yapılandırması ──────────────────────────────────
PROXY_KULLANICI = os.environ.get("PROXY_KULLANICI", "")
PROXY_SIFRE     = os.environ.get("PROXY_SIFRE", "")

# PROXY_LIST: "ip1:port1,ip2:port2,..." (Webshare Proxy List indirmesi, ip:port:user:pass
# formatından user/pass ayıklanmış hali — hepsi PROXY_KULLANICI/PROXY_SIFRE'yi paylaşır).
_PROXY_LIST_RAW = os.environ.get("PROXY_LIST", "")
PROXY_LIST = [p.strip() for p in _PROXY_LIST_RAW.split(",") if p.strip()]


def _rastgele_ip_port() -> tuple[str, str] | None:
    """PROXY_LIST'ten rastgele bir (ip, port) çifti seçer. Liste boşsa None."""
    if not PROXY_LIST or not PROXY_KULLANICI or not PROXY_SIFRE:
        return None
    secilen = random.choice(PROXY_LIST)
    ip, _, port = secilen.partition(":")
    if not ip or not port:
        return None
    return ip, port


def rastgele_proxy_url() -> str | None:
    """
    'http://kullanici:sifre@ip:port' formatında rastgele bir proxy URL'i döndürür.
    Her çağrıda (script başına genelde 1 kez) 100'lük havuzdan yeni bir IP seçilir —
    bloklanan bir IP varsa script'i yeniden başlatmak farklı bir IP'ye düşürür.
    Proxy yapılandırılmamışsa None (çağıran taraf direkt bağlantıya düşer).
    """
    secim = _rastgele_ip_port()
    if not secim:
        return None
    ip, port = secim
    return f"http://{PROXY_KULLANICI}:{PROXY_SIFRE}@{ip}:{port}"


def playwright_proxy_ayarlari() -> dict | None:
    """
    Playwright için proxy ayarları döndürür (rastgele seçilmiş 1 IP).
    Proxy yoksa None döner (geliştirme ortamı / proxy yapılandırılmamış).
    """
    secim = _rastgele_ip_port()
    if not secim:
        print("  ⚠️  Proxy ayarı yok — direkt bağlantı kullanılıyor")
        return None
    ip, port = secim
    return {
        "server":   f"http://{ip}:{port}",
        "username": PROXY_KULLANICI,
        "password": PROXY_SIFRE
    }


def requests_proxy_ayarlari() -> dict | None:
    """
    requests kütüphanesi için proxy ayarları (rastgele seçilmiş 1 IP).
    PDF indirme vs. için.
    """
    url = rastgele_proxy_url()
    if not url:
        return None
    return {
        "http":  url,
        "https": url
    }
