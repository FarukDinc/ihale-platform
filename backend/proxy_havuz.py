"""
İhaleGlobal — Proxy Havuzu (istek başına rotasyon)

NEDEN YAZILDI
─────────────
Eski `proxy_config.rastgele_proxy_url()` script başına BİR KEZ çağrılıyordu.
Sonuç: 50.000 istekli bir backfill turu baştan sona TEK bir IP üzerinden akıyor,
100 IP'lik havuzun 99'u boşta duruyordu. Üstelik bunlar shared datacenter IP'leri
(başka Webshare müşterileriyle paylaşılıyor) — tek bir tanesine yüklenmek, VDS'in
kendi temiz IP'sini kullanmaktan daha risliydi.

Bu modül üç şeyi birden yapar:
  1) İSTEK BAŞINA rotasyon  — her istek havuzdan sıradaki IP'ye gider
  2) IP BAŞINA soğuma       — aynı IP arka arkaya dövülmez (varsayılan 3 sn arayla)
  3) KÜRESEL hız tavanı     — 100 IP'ye yayılsa da EKAP toplam yükü görür; tavan
                              bilinçli bir nezaket sınırıdır, teknik zorunluluk değil

Ayrıca bozuk/bloklu IP'leri kendiliğinden devre dışı bırakır: üst üste hata veren
IP karantinaya alınır, ısrarla hata veriyorsa havuzdan tamamen düşer.

BAĞLANTI HAVUZU
───────────────
httpx istemcisi proxy'yi KURULUM anında bağlar; istek başına proxy değiştirmek için
ya her istekte yeni istemci açmak (pahalı, TLS el sıkışması tekrarlanır) ya da her
proxy için bir istemci tutup aralarında dolaşmak gerekir. İkincisi seçildi: 100
istemci açılır, her biri kendi IP'sine keep-alive bağlantı tutar.

KULLANIM (senkron)
──────────────────
    from proxy_havuz import havuz_al

    havuz = havuz_al()                    # PROXY_LIST boşsa "direkt mod"a düşer
    for sayfa in range(1000):
        with havuz.istek() as ist:        # sırası gelen IP'yi bekler ve verir
            try:
                r = ist.client.get(URL, params=..., timeout=30)
                r.raise_for_status()
            except Exception:
                ist.basarisiz()           # bu IP'yi cezalandır, tur devam etsin
                continue
    havuz.ozet_yaz()

.env (VDS'te backend/.env):
    PROXY_KULLANICI=...          # 100 proxy için ORTAK
    PROXY_SIFRE=...
    PROXY_LIST=ip1:port1,ip2:port2,...     # Webshare → Proxy → Proxy List indirmesi
    PROXY_IP_ARALIK_SN=3.0       # aynı IP iki isteği arası en az bu kadar (varsayılan 3)
    PROXY_KURESEL_RPM=600        # tüm havuzun toplam istek/dk tavanı (varsayılan 600)

PROXY_LIST boşsa modül "direkt mod"da çalışır: aynı arayüz, proxy'siz tek istemci,
yalnız küresel hız tavanı uygulanır. Yani scraper kodu her iki durumda da aynıdır.
"""

from __future__ import annotations

import os
import random
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Ayarlar ───────────────────────────────────────────────────────────────────
PROXY_KULLANICI = os.environ.get("PROXY_KULLANICI", "").strip()
PROXY_SIFRE     = os.environ.get("PROXY_SIFRE", "").strip()
_LISTE_HAM      = os.environ.get("PROXY_LIST", "")

IP_ARALIK_SN    = float(os.environ.get("PROXY_IP_ARALIK_SN", "3.0"))
KURESEL_RPM     = int(os.environ.get("PROXY_KURESEL_RPM", "600"))

# Tüm proxy IP'leri düştüğünde VDS'in kendi IP'sine geçilsin mi? VARSAYILAN: HAYIR.
# 20 Tem: kullanıcı talimatı "VDS IP'sine düşmek YASAK" (proxy 402 krizinde verildi).
# Bu başlıkta yedek mekanizması onaylanmıştı ama o onay 402 durumundan ÖNCEYDİ.
# Çakışan iki talimatın güvenli kesişimi: mekanizma dursun, kendiliğinden devreye
# GİRMESİN. Bilinçli açmak isteyen PROXY_DIREKT_YEDEK=1 verir.
DIREKT_YEDEK_IZIN = os.environ.get("PROXY_DIREKT_YEDEK", "0").strip() in ("1", "true", "evet")

# "Bu IP ile sorun var" diyen HTTP kodları — yalnızca bunlar ucu cezalandırır.
#   403 Forbidden / 407 Proxy Auth / 429 Too Many Requests → doğrudan blok sinyali
#   5xx                                                    → proxy ya da uç sunucu arızası
# 404/400/422 BİLEREK DIŞARIDA: bunlar uygulama yanıtıdır ("kayıt yok", "geçersiz
# parametre"), proxy sağlıklıdır. Cezalandırılırsa havuz kendi kendini yer.
BLOK_KODLARI = frozenset({403, 407, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524})

# Bir IP üst üste kaç hata verirse karantinaya alınır / tamamen düşürülür
KARANTINA_ESIGI = 3
KARANTINA_SN    = 120.0
OLUM_ESIGI      = 3          # kaç kez karantinaya girerse havuzdan atılır

# Tanınabilir kimlik: engellenmek istemiyorsak kim olduğumuzu saklamamalıyız.
# EKAP tarafı bir sorun görürse bizi tanıyıp ulaşabilmeli.
#
# SADECE ASCII — HTTP başlık değerleri latin-1'e kodlanır; Türkçe karakter (ı, ş, ğ…)
# koyulursa httpx istemciyi kurarken UnicodeEncodeError ile ölür. İlk sürümde
# "toplayıcı" yazılmıştı ve modül hiç çalışmadı; test yakaladı.
VARSAYILAN_UA = os.environ.get(
    "SCRAPER_USER_AGENT",
    "IhaleGlobal/1.0 (+https://ihaleglobal.com; public procurement data collector)",
)


@dataclass
class _Uc:
    """Havuzdaki tek bir proxy ucu (ya da direkt mod için tek sanal uç)."""
    etiket: str                       # 'ip:port' ya da 'direkt'
    url: str | None                   # httpx proxy url'i; direkt modda None
    client: httpx.Client | None = None
    son_kullanim: float = 0.0
    ardisik_hata: int = 0
    karantina_bitis: float = 0.0
    karantina_sayisi: int = 0
    olu: bool = False
    istek: int = 0
    hata: int = 0

    def musait_mi(self, simdi: float) -> bool:
        if self.olu or simdi < self.karantina_bitis:
            return False
        return (simdi - self.son_kullanim) >= IP_ARALIK_SN

    def hazir_zamani(self) -> float:
        """Bu ucun tekrar kullanılabilir olacağı en erken an."""
        return max(self.son_kullanim + IP_ARALIK_SN, self.karantina_bitis)


@dataclass
class _Kiralama:
    """`with havuz.istek() as ist:` bloğunun verdiği nesne."""
    client: httpx.Client
    etiket: str
    _uc: _Uc
    _basarisiz: bool = field(default=False, repr=False)

    def basarisiz(self) -> None:
        """Bu isteğin başarısız olduğunu bildirir → uç cezalandırılır."""
        self._basarisiz = True

    def yanit(self, r) -> None:
        """
        HTTP yanıtına bakıp ucu cezalandırıp cezalandırmayacağına KENDİSİ karar verir.
        `if r.status_code != 200: basarisiz()` YAZMAYIN — bunu kullanın.

        NEDEN: 404 bir blok sinyali DEĞİL, "böyle kayıt yok" demektir. Uygulama
        seviyesindeki bu yanıtları proxy hatası saymak havuzu kendi kendine yok eder:
        ekap_sonuc_scraper ihale başına 5 detay ucu deniyor ve hepsi 404 dönüyor —
        ardışık 9 tanesi (KARANTINA_ESIGI × OLUM_ESIGI) bir IP'yi düşürür, 100 IP
        birkaç yüz istekte tükenir. Kazıma da durur, sebebi de anlaşılmaz.

        Yalnızca gerçekten "bu IP ile sorun var" diyen kodlar cezalandırılır.
        """
        if r.status_code in BLOK_KODLARI:
            self._basarisiz = True


def ekap_ssl_baglami():
    """
    EKAP eski/zayıf TLS cipher kullanıyor; modern OpenSSL varsayılanıyla handshake
    başarısız olur. Aynı çözüm dt_kazanan_scraper / ekap_dogrudan_temin_scraper /
    ekap_sonuc_backfill içinde de vardı — havuz istemcileri de bunu kullanmazsa
    her istek TLS aşamasında ölür.
    """
    import ssl
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class ProxyHavuzu:
    def __init__(self, ip_aralik_sn: float | None = None, kuresel_rpm: int | None = None,
                 ssl_baglami=None):
        self.ip_aralik_sn = IP_ARALIK_SN if ip_aralik_sn is None else ip_aralik_sn
        self.kuresel_rpm = KURESEL_RPM if kuresel_rpm is None else kuresel_rpm
        self.ssl_baglami = ssl_baglami
        self._kilit = threading.Lock()
        self._son_kuresel = 0.0
        self._sira = 0
        self._toplam_istek = 0
        self._toplam_hata = 0
        self._bekleme_sn = 0.0
        self._direkt_yedek: _Uc | None = None   # tüm IP'ler düşerse buraya çekiliriz

        liste = [p.strip() for p in _LISTE_HAM.split(",") if p.strip()]
        yapilandirilmis = bool(liste and PROXY_KULLANICI and PROXY_SIFRE)

        if yapilandirilmis:
            random.shuffle(liste)          # her koşuda farklı sırayla başla
            self.uclar = [
                _Uc(etiket=hp, url=f"http://{PROXY_KULLANICI}:{PROXY_SIFRE}@{hp}")
                for hp in liste if ":" in hp
            ]
            self.direkt_mod = False
        else:
            # Proxy yapılandırılmamış → tek sanal uç, doğrudan bağlantı.
            self.uclar = [_Uc(etiket="direkt", url=None)]
            self.direkt_mod = True

    # ── iç yardımcılar ────────────────────────────────────────────────────────
    def _client(self, uc: _Uc) -> httpx.Client:
        if uc.client is None:
            uc.client = httpx.Client(
                proxy=uc.url,
                headers={"User-Agent": VARSAYILAN_UA},
                timeout=30.0,
                follow_redirects=True,
                verify=self.ssl_baglami if self.ssl_baglami is not None else True,
            )
        return uc.client

    def _kuresel_bekle(self, simdi: float) -> float:
        """Küresel rpm tavanı için beklenecek süre."""
        if self.kuresel_rpm <= 0:
            return 0.0
        aralik = 60.0 / self.kuresel_rpm
        gecen = simdi - self._son_kuresel
        return max(0.0, aralik - gecen)

    def _sonraki_uc(self) -> tuple[_Uc, float]:
        """Sırası gelen ucu ve beklenmesi gereken süreyi döndürür (kilit altında)."""
        simdi = time.monotonic()
        canli = [u for u in self.uclar if not u.olu]
        if not canli:
            # TÜM IP'LER DÜŞTÜ → DİREKT MODA GERİ ÇEKİL (eskiden RuntimeError atıyordu).
            #
            # Gerekçe: 18/19 Tem gecesi havuzun 100 IP'sinin 100'ü düştü (300 karantina).
            # Havuz istisna atınca scraper'lar ÇÖKTÜ — yani proxy sorunu, veri akışının
            # tamamen durmasına dönüştü. Oysa VDS'in kendi IP'si çalışıyordu.
            # Proxy bir DAYANIKLILIK aracı; onun arızası kazımayı durdurmamalı.
            #
            # Sessiz değil GÜRÜLTÜLÜ düşüyoruz: tüm trafiğin VDS IP'sine dönmesi
            # operatörün bilmesi gereken bir davranış değişikliği.
            if not DIREKT_YEDEK_IZIN:
                raise RuntimeError(
                    "TÜM PROXY IP'LERİ DÜŞTÜ ve direkt yedek KAPALI.\n"
                    "  Kazıma durduruldu — istekler VDS IP'sinden GİTMEYECEK (kullanıcı talimatı).\n"
                    "  Muhtemel sebepler: Webshare 402/kota, suistimal bayrağı, subnet engeli.\n"
                    "  Tek uçla teşhis: curl -x http://KULLANICI:SIFRE@IP:PORT https://api.ipify.org\n"
                    "  Bilinçli olarak VDS IP'sine düşmek istiyorsanız: PROXY_DIREKT_YEDEK=1"
                )
            if self._direkt_yedek is None:
                self._direkt_yedek = _Uc(etiket="direkt-yedek", url=None)
                print("\n" + "!" * 68, flush=True)
                print("! TÜM PROXY IP'LERİ DÜŞTÜ — DİREKT BAĞLANTIYA GERİ ÇEKİLİYOR", flush=True)
                print("! Bundan sonraki istekler VDS'in KENDİ IP'sinden gidecek.", flush=True)
                print("! Kazıma durmuyor ama risk dağıtımı YOK. Proxy'leri kontrol edin.", flush=True)
                print("!" * 68 + "\n", flush=True)
            uc = self._direkt_yedek
            bekle = max(uc.hazir_zamani() - simdi, self._kuresel_bekle(simdi), 0.0)
            return uc, bekle
        n = len(canli)
        # round-robin: sıradan başlayıp müsait ilk ucu al
        for i in range(n):
            uc = canli[(self._sira + i) % n]
            if uc.musait_mi(simdi):
                self._sira = (self._sira + i + 1) % n
                return uc, self._kuresel_bekle(simdi)
        # hiçbiri müsait değil → en erken hazır olanı bekle
        uc = min(canli, key=lambda u: u.hazir_zamani())
        bekle = max(uc.hazir_zamani() - simdi, self._kuresel_bekle(simdi))
        return uc, bekle

    # ── genel arayüz ──────────────────────────────────────────────────────────
    @contextmanager
    def istek(self):
        """
        Sırası gelen ucu kiralar. Gerekirse bekler (IP soğuması + küresel tavan).
        Blok içinde `ist.basarisiz()` çağrılırsa ya da istisna çıkarsa uç cezalanır.
        """
        with self._kilit:
            uc, bekle = self._sonraki_uc()
        if bekle > 0:
            time.sleep(bekle)
            self._bekleme_sn += bekle

        simdi = time.monotonic()
        uc.son_kullanim = simdi
        uc.istek += 1
        self._toplam_istek += 1
        self._son_kuresel = simdi

        kiralama = _Kiralama(client=self._client(uc), etiket=uc.etiket, _uc=uc)
        hata_olustu = False
        try:
            yield kiralama
        except Exception:
            hata_olustu = True
            raise
        finally:
            if hata_olustu or kiralama._basarisiz:
                self._cezalandir(uc)
            else:
                uc.ardisik_hata = 0

    def _cezalandir(self, uc: _Uc) -> None:
        with self._kilit:
            uc.hata += 1
            self._toplam_hata += 1
            uc.ardisik_hata += 1
            if uc.ardisik_hata >= KARANTINA_ESIGI:
                uc.karantina_sayisi += 1
                uc.ardisik_hata = 0
                # direkt-yedek düşürülemez: düşerse gidecek hiçbir yer kalmaz.
                if uc.karantina_sayisi >= OLUM_ESIGI and not self.direkt_mod and uc.etiket != "direkt-yedek":
                    uc.olu = True
                    if uc.client:
                        try: uc.client.close()
                        except Exception: pass
                        uc.client = None
                    print(f"    ⛔ proxy düşürüldü: {uc.etiket} "
                          f"({uc.hata} hata, {uc.karantina_sayisi} karantina)", flush=True)
                else:
                    uc.karantina_bitis = time.monotonic() + KARANTINA_SN
                    # direkt-yedek sürekli hata veriyorsa (hedef bizi gerçekten
                    # sınırlıyordur) geri çekilmesi DOĞRU, ama aynı satırı her 3
                    # istekte bir basmasın — log'u boğuyor.
                    if uc.etiket != "direkt-yedek" or uc.karantina_sayisi == 1:
                        print(f"    ⏸ proxy karantinada {KARANTINA_SN:.0f}sn: {uc.etiket}", flush=True)

    def ozet_yaz(self) -> None:
        canli = [u for u in self.uclar if not u.olu]
        kullanilan = [u for u in self.uclar if u.istek > 0]
        mod = "DİREKT (proxy yapılandırılmamış)" if self.direkt_mod else f"{len(self.uclar)} IP"
        print(f"\n── Proxy havuzu özeti ──")
        print(f"   mod            : {mod}")
        print(f"   toplam istek   : {self._toplam_istek}")
        print(f"   hatalı istek   : {self._toplam_hata}")
        print(f"   kullanılan IP  : {len(kullanilan)} / {len(self.uclar)} (canlı {len(canli)})")
        print(f"   hız sınırı bekl: {self._bekleme_sn:.0f} sn")
        if self._direkt_yedek is not None:
            print(f"   ⚠ DİREKT YEDEK: {self._direkt_yedek.istek} istek VDS IP'sinden gitti "
                  f"(tüm proxy IP'leri düşmüştü)")
        if not self.direkt_mod and kullanilan:
            en_cok = max(kullanilan, key=lambda u: u.istek)
            print(f"   en çok yüklenen: {en_cok.etiket} ({en_cok.istek} istek)")
            olu = [u.etiket for u in self.uclar if u.olu]
            if olu:
                print(f"   düşen IP'ler   : {', '.join(olu[:10])}" + (" …" if len(olu) > 10 else ""))

    def kapat(self) -> None:
        for u in self.uclar:
            if u.client:
                try: u.client.close()
                except Exception: pass
                u.client = None


class AsyncProxyHavuzu(ProxyHavuzu):
    """
    Async scraper'lar için (httpx.AsyncClient) aynı havuz.

    Zamanlama mantığı (round-robin, IP soğuması, küresel tavan, karantina) taban
    sınıftan AYNEN gelir — tek fark istemci tipi ve beklemenin `asyncio.sleep` ile
    yapılması. `time.sleep` async bir döngüde tüm event loop'u dondururdu.

    KULLANIM
        from proxy_havuz import async_havuz_al, ekap_ssl_baglami
        havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
        async with havuz.istek() as ist:
            r = await ist.client.get(URL, params=...)
            if r.status_code != 200:
                ist.basarisiz()
        await havuz.kapat()
    """

    def _client(self, uc: _Uc):
        if uc.client is None:
            uc.client = httpx.AsyncClient(
                proxy=uc.url,
                headers={"User-Agent": VARSAYILAN_UA},
                timeout=30.0,
                follow_redirects=True,
                verify=self.ssl_baglami if self.ssl_baglami is not None else True,
            )
        return uc.client

    @asynccontextmanager
    async def istek(self):
        import asyncio
        with self._kilit:
            uc, bekle = self._sonraki_uc()
        if bekle > 0:
            await asyncio.sleep(bekle)
            self._bekleme_sn += bekle

        simdi = time.monotonic()
        uc.son_kullanim = simdi
        uc.istek += 1
        self._toplam_istek += 1
        self._son_kuresel = simdi

        kiralama = _Kiralama(client=self._client(uc), etiket=uc.etiket, _uc=uc)
        hata_olustu = False
        try:
            yield kiralama
        except Exception:
            hata_olustu = True
            raise
        finally:
            if hata_olustu or kiralama._basarisiz:
                self._cezalandir(uc)
            else:
                uc.ardisik_hata = 0

    async def kapat(self) -> None:
        for u in self.uclar:
            if u.client:
                try:
                    await u.client.aclose()
                except Exception:
                    pass
                u.client = None


_havuz: ProxyHavuzu | None = None
_async_havuz: AsyncProxyHavuzu | None = None


def havuz_al(ip_aralik_sn: float | None = None, kuresel_rpm: int | None = None,
             ssl_baglami=None) -> ProxyHavuzu:
    """Süreç genelinde tek havuz (bağlantılar yeniden kullanılsın)."""
    global _havuz
    if _havuz is None:
        _havuz = ProxyHavuzu(ip_aralik_sn=ip_aralik_sn, kuresel_rpm=kuresel_rpm,
                             ssl_baglami=ssl_baglami)
        n = len(_havuz.uclar)
        if _havuz.direkt_mod:
            print("⚠ PROXY_LIST boş — DİREKT bağlantı (tüm istekler VDS IP'sinden). "
                  "Riski yaymak için backend/.env'e PROXY_LIST ekleyin.", flush=True)
        else:
            tavan = min(_havuz.kuresel_rpm, int(60.0 / _havuz.ip_aralik_sn * n)) if _havuz.ip_aralik_sn > 0 else _havuz.kuresel_rpm
            print(f"→ Proxy havuzu: {n} IP · IP başına ≥{_havuz.ip_aralik_sn:.1f}sn · "
                  f"küresel tavan {_havuz.kuresel_rpm}/dk (etkin ~{tavan}/dk)", flush=True)
    return _havuz


def async_havuz_al(ip_aralik_sn: float | None = None, kuresel_rpm: int | None = None,
                   ssl_baglami=None) -> AsyncProxyHavuzu:
    """Async scraper'lar için süreç genelinde tek havuz."""
    global _async_havuz
    if _async_havuz is None:
        _async_havuz = AsyncProxyHavuzu(ip_aralik_sn=ip_aralik_sn, kuresel_rpm=kuresel_rpm,
                                        ssl_baglami=ssl_baglami)
        n = len(_async_havuz.uclar)
        if _async_havuz.direkt_mod:
            print("⚠ PROXY_LIST boş — DİREKT bağlantı (tüm istekler VDS IP'sinden). "
                  "Riski yaymak için backend/.env'e PROXY_LIST ekleyin.", flush=True)
        else:
            print(f"→ Proxy havuzu (async): {n} IP · IP başına ≥{_async_havuz.ip_aralik_sn:.1f}sn · "
                  f"küresel tavan {_async_havuz.kuresel_rpm}/dk", flush=True)
    return _async_havuz


if __name__ == "__main__":
    # Hızlı öz-test: gerçek istek atmadan sıralama/soğuma davranışını gösterir.
    h = havuz_al()
    print(f"uç sayısı: {len(h.uclar)} · direkt mod: {h.direkt_mod}")
    bas = time.monotonic()
    for i in range(5):
        with h.istek() as ist:
            print(f"  istek {i+1} → {ist.etiket}  (t+{time.monotonic()-bas:.2f}sn)")
    h.ozet_yaz()
    h.kapat()
