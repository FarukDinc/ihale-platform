# SUNUCU TAŞIMA RUNBOOK — Mevcut VDS → Dedicated VT#2

> Oluşturuldu: 2 Ağu 2026 · Canlı sunucudan salt-okunur tespitle dolduruldu.
> Yürütme: SSH'ı Claude sürer. Yeni kutu = tam yetki. Eski kutu (canlı) = sadece okuma + son dump; yıkıcı/cutover komutları önce kullanıcıya gösterilir.

## 0. Mevcut durum (kaynak: `ssh ihale` = root@195.85.207.126)
- **Kaynak kutu:** 11 GB RAM (swap 2/2 DOLU — RAM açlığı), 5 vCPU, 158 GB disk %48, `/var/lib/docker` = **31 GB**.
- **Hedef kutu:** Dedicated VT#2 — 256 GB RAM, 2 TB SSD, 2x E5-2650v2. (Erişim gelince: `Host ihale2`.)
- **Taşınacak DB:** ihale `postgres` = **21 GB** (dump `ihaleglobal_YYYY-MM-DD.sql.gz` ≈ 2.3 GB) · fasonda `postgres` = **104 MB** (dump ≈ 7 MB). Gece 04:00/05:15 otomatik.
- **25 container:** `supabase-*` (12) + `fasonda-*` (12) + `flaresolverr`.
- **Compose:** `/opt/supabase/docker/` ve `/opt/fasonda/` (override + nginx/pg overlay'leri). App repoları: `/opt/ihale-platform` (66 .py backend), `/opt/fasonda-platform`.
- **Cron (root):** `run_scraper.sh` 02:00 · `sonuc_watchdog.sh` + `ilan_metni_watchdog.sh` */20 · `ihale_yedek.sh` 04:00 · `fasonda_yedek.sh` 05:15 · `taslak_senkron.sh` 05:30 · `sitemap_uret.sh` 05:45.
- **Systemd:** `ihale-api.service` (FastAPI 127.0.0.1:8080, AKTİF) · `ihale-docker-user-drops.service` (origin iptables oneshot) · `dt-yayin.service` **FAILED** (DT backfill, göçten bağımsız — sonra bak).
- **Domainler (Cloudflare):** ihaleglobal.com (+www) · fasonda.com (+www, *.fasonda.com wildcard).
- **Sırlar (kullanıcı elle taşır, chat'e YAZILMAZ):** `/opt/supabase/.env` (385) · `/opt/fasonda/.env` (385) · `/opt/ihale-platform/backend/.env` (19) · `/opt/fasonda-platform/backend/.env` · `.env.webshare`.

## Yöntem kararı
Fiziksel volume kopyası DEĞİL → **taze Supabase kurulumu + mantıksal restore** (dump'lar zaten mantıksal, sürüm-esnek, Supabase bootstrap'ı rolleri/şemayı temiz kurar). Config rsync/git ile, sırlar elle, DB `.sql.gz` restore ile, Storage objeleri volume rsync ile.

---

## FAZ 1 — Yeni kutu tabanı (yeni root erişimi gelince · eski kutu canlı · KESİNTİSİZ)
0. **Sipariş:** OS = **Ubuntu 24.04 LTS (kesinleşti)** + root SSH. Günlük İmaj Yedekleme (250₺, harici) dahil. KVM talep-üzerine (7/24, varsayılan kapalı) — sadece SSH/ağ kopması için break-glass. ⚠️ 24.04 sistem Python 3.12 → Faz 3'te scraper venv yeniden kurulurken paket sürüm bump'larına hazır ol.
1. SSH config'e `Host ihale2` ekle (IP + key). Bağlantı testi.
2. OS güncel + Docker + docker compose + git + rsync + ufw/iptables kur.
3. **Origin sertleştirme iskeleti:** `ihale-docker-user-drops` systemd oneshot'ı yeni kutuya taşı (Kong/Postgres portları dış arayüzde kapalı — sadece Cloudflare). Studio 127.0.0.1'e çekili.
   ⚠️ **KİLİTLENME KORUMASI:** SSH portu **22'yi ASLA** public'te kapatma — yalnız Kong (8000/8443) + Postgres (5432). Kuralları **ikinci bir SSH oturumu açıkken** uygula; kilitlenirsen sağlayıcıdan KVM iste (talep-üzerine, gecikme). Bare-metal'de snapshot rollback YOK.
4. Dizin yapısı: `/opt/supabase`, `/opt/fasonda`, `/opt/ihale-platform`, `/opt/fasonda-platform` (repo'ları git clone / rsync — **volume'ler hariç**).

## FAZ 2 — Postgres tuning (EN KRİTİK — yoksa 256 GB boş durur)
5. Yeni stack `.env`/compose'ta PG config: `shared_buffers≈64GB`, `effective_cache_size≈192GB`, `work_mem` yükselt, `maintenance_work_mem≈8GB`, `max_parallel_workers(_per_gather)` 32 thread'e göre (zayıf tek-thread'i paralel sorguyla telafi et).
6. PG major sürümünü eski kutuyla eşle (pg15/pg17 overlay — önce eski `supabase-db` sürümünü doğrula).

## FAZ 3 — Stack ayağa kaldır + veri restore (eski kutu canlı · KESİNTİSİZ)
7. **Sırları kullanıcı taşır** → yeni `/opt/supabase/.env`, `/opt/fasonda/.env`, backend `.env`'ler.
8. `docker compose up -d` (önce supabase, sonra fasonda). 24 container healthy olana kadar bekle.
9. **DB restore (dünün dump'ı ile ön-yükleme):** `ihaleglobal_*.sql.gz` → yeni `supabase-db`; `fasonda_*.sql.gz` → yeni `fasonda-db`. (Dump türünü doğrula: pg_dump mı pg_dumpall mı → restore komutu ona göre.)
10. **Storage objeleri:** eski `supabase-storage`/`fasonda-storage` volume (veya S3/rustfs backend) → yeni kutuya rsync.
11. **FlareSolverr:** `docker run -d --name flaresolverr -p 127.0.0.1:8191:8191 -e LOG_LEVEL=warning --restart unless-stopped ghcr.io/flaresolverr/flaresolverr:latest`
12. **Backend + cron + systemd:** repo pull, venv kur, `ihale-api.service` + origin oneshot + crontab (7 satır) yeni kutuda kur. Cron'ları cutover'a kadar PASİF tut (çift yazma olmasın).

## FAZ 4 — Doğrulama (eski kutu hâlâ canlı · IP ile test, DNS değişmeden)
13. Yeni kutuya `/etc/hosts` veya doğrudan IP ile: her v1 sayfası açılıyor mu · misafir maskesi (anon curl'de idare/kazanan '***') · origin kapalı (Kong/Postgres dışarıdan erişilemez) · scraper dry-run OK · DeepSeek + embedding çalışıyor.
14. ⚠️ **Webshare proxy:** yeni sunucu IP'sini sağlayıcıda beyaz listeye ekle (IP-auth ise), yoksa detay-ağır scraper'lar (sonuç/DT kazanan) cutover sonrası patlar.

## FAZ 5 — CUTOVER (tek kesinti penceresi ≈ 30-45 dk · düşük trafik saati, ör. 04:30)
15. Cloudflare TTL'i düşür (ör. 60 sn) — cutover'dan ~1 saat önce.
16. Eski kutuda scraper/cron/API'yi durdur (yazma kes).
17. **Son taze dump** eski kutuda (`pg_dump | gzip`) → yeni kutuya kopyala (2.3 GB, ~5 dk) → yeni DB'ye restore (gün-içi delta'yı yakala).
18. Son storage delta rsync.
19. **Cloudflare A kayıtları** ihaleglobal.com + fasonda.com → yeni IP. Origin Cert (Full strict) yeni kutuda hazır.
20. Yeni kutuda cron'ları AKTİF et. İzle.

## FAZ 6 — Cutover sonrası
21. Doğrulama listesini (Faz 4) canlı domain üzerinde tekrarla.
22. Gece cron 24 adım hatasız · iki backfill akıyor · watchdog'lar çalışıyor.
23. Eski kutu 2-3 gün geri-dönüş için beklesin; sağlamsa iptal.
23b. **⭐ DT GEÇMİŞ BACKFILL (yeni kutuda çalıştır — göç bunun İÇİN de değerli):** DT arşivi eksik —
    44.829 kurumun **%76'sında yalnız 2025+ DT var** (ölçüm 4 Ağu). Kapsam yaşlandıkça çöküyor:
    2025 1,47M → 2024 305K (%20) → 2023 195K → 2022 116K → 2021 ve öncesi ~0. Kök: page/date-slice
    backfill güncel sayfaları çekip eskiye inmeden durdu (checkpoint sayfa 3). **Eski (zayıf) kutuda
    denendi ama İMKÂNSIZ:** 60 dk'da sadece sayfa 150, proxy timeout + upsert-500 (DB darboğazı) seli,
    ilk sayfalar dupe. Yeni kutu (256GB RAM, /dev/shm sınırı yok, hızlı DB) bunu **10x+ hızlı** yapar.
    Komut: `ekap_dogrudan_temin_scraper.py --bas 01.01.YYYY --bit 31.12.YYYY --max-pages 20000` yıl yıl
    (2024→2016); PARALEL dilim = 30-100x ama Webshare eşzamanlı-soket sınırına dikkat (bkz [[proxy-havuzu]]).
    Webshare IP-beyazlistesi yeni kutu IP'siyle güncel olmalı (Faz 4-14). **Cutover ÖNCESİ eski kutuda BAŞLATMA**
    (göç dump'ını kirletir + kesilir; idempotent ama boşa iş).
24. **OFF-SITE YEDEK (bare-metal'de snapshot YOK):** ✅ KARAR (2 Ağu) — siparişte **Günlük İmaj Yedekleme** (**250 TL/ay**) seçildi; açıklama "güvenli **harici** depolama" = **off-site TEYİT EDİLDİ** ✅. Restore yolu/hızını cutover öncesi netleştir. **Gece `pg_dump` (ihale_yedek/fasonda_yedek) yine de SÜRSÜN** — en taşınabilir restore yolu + göç seed'i; sağlayıcı yedeği "tüm sunucu" katmanı, pg_dump "DB" katmanı. (DIY rclone→B2 elendi.)

---
**Not:** Bu runbook eski kutuya (VT#2) taşımanın yanı sıra ileride VT#2 → VT#8 sıçraması için de şablon; her adım tekrar çalıştırılabilir olacak şekilde yazıldı. Kesinti sadece Faz 5.
