#!/bin/bash
# Gece scraper turu — VDS cron (GitHub Actions'in yerini alir)
cd /opt/ihale-platform/backend
set -a
source /opt/ihale-platform/backend/.env
set +a
export EKAP_BELGE_LINK=1
VENV=/opt/ihale-platform/backend/venv/bin
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Scraper baslatiliyor ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ekap_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] !!! UYARI: EKAP SCRAPER BAŞARISIZ (exit≠0) — bayat veri riski, bildirim/bülten atlanmalı" >> /opt/ihale-platform/logs/scraper.log
fi
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Bildirimler ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python notify.py >> /opt/ihale-platform/logs/scraper.log 2>&1
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Bitti ===" >> /opt/ihale-platform/logs/scraper.log

$VENV/python kik_backfill.py --gun 3 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python bulten_gonder.py >> /opt/ihale-platform/logs/scraper.log 2>&1

# ÖNCELİK 10 Faz A1/B2 — sonuç verisi taraması + firma sözlüğü tazeleme (9 Tem 2026)
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Sonuc backfill ===" >> /opt/ihale-platform/logs/scraper.log
# Gecelik: EKAP sonuç listesinin BAŞINDAN (en yeni) tara — yeni sonuçlanan ihaleler burada belirir.
# --no-checkpoint ile paylaşılan checkpoint'i ilerletmez (deep --backfill onu kullanmaya devam eder).
$VENV/python ekap_sonuc_backfill.py --tum-kayitlar --max-pages 50 --start-skip 0 --no-checkpoint >> /opt/ihale-platform/logs/scraper.log 2>&1
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Yuklenici tazeleme ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python yuklenici_yenile_calistir.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python rakip_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python ilan_embed_uret.py --max 300 >> /opt/ihale-platform/logs/scraper.log 2>&1
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Dogrudan Temin listesi ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ekap_dogrudan_temin_scraper.py --max-pages 20 >> /opt/ihale-platform/logs/scraper.log 2>&1
# DT kazanan/bedel backfill — 18 Tem bulgusu: dtDetayGetir CAPTCHA'sız açık API, Gemini/token
# maliyeti YOK. --limit 2000/--rpm 300: günlük yeni "sonuç" durumuna geçenleri rahat karşılar.
# BİRİKMİŞ ~1.3M kayıtlık geçmiş kuyruk BU satırla temizlenmez — ayrı, yüksek --limit'li tek
# seferlik arka plan turu gerekir (bkz. YAPILACAKLAR.md). Migration uygulanmadıysa sessizce
# exit 1 verir (kuyruk_say hata mesajı loga düşer, turu bozmaz).
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === DT kazanan/bedel backfill ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python dt_kazanan_scraper.py --limit 2000 --rpm 300 >> /opt/ihale-platform/logs/scraper.log 2>&1
# ilan.gov.tr (Basın İlan Kurumu) gazete İHALE ilanları — EKAP'ta olmayan (2886 satış/kira vb.) eklenir
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === ilan.gov.tr ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ilan_gov_scraper.py --max-pages 40 >> /opt/ihale-platform/logs/scraper.log 2>&1
# TED Europa uluslararası ihaleler (ayrı tablo, Türkçe'ye çevrilerek)
# 20 Tem düzeltmesi (Backlog #19): eski satır `--max-pages 6 --limit 50` idi = koşu başına 300
# kayıt tavanı. TED tek günde ~1.545 cn-standard ilan yayımlıyor (16 Tem ölçümü), yani günün
# ~%19'u alınıyor, gerisi kayboluyordu. Yeni `--gun 2`: bugün + dünü TAM çeker (sorgu artık
# publication-date ile pencerelenip totalNoticeCount'a kadar sayfalanıyor).
# Çeviri atlama ölçütü "DB'de var mı" DEĞİL, "gerçekten çevrilmiş mi" (baslik <> orijinal_baslik):
# böylece kotaya takılıp çevrilemeyen başlık ertesi gece kendiliğinden yeniden denenir. Ayrıca
# zaten çevrili satırlar upsert gövdesine baslik/kategori KOYMADAN gider (Türkçe başlık ezilmesin).
# --rpm varsayılanı 15 (free tier); gecelik çağrı ~52-103 olduğu için hız sınırı şart.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === TED uluslararasi ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ted_scraper.py --gun 2 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python georgia_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
# Kamu kurumu kaynakları (EKAP dışı, ANA ilanlar tablosuna kaynak='dmo'/'jandarma' ile yazar —
# 16 Tem'de ayrı kamu_ihaleleri'nden buraya taşındı, İhaleler ekranında rozetle görünür): DMO + Jandarma
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Kamu kurumu (DMO/Jandarma) ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python dmo_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python jandarma_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
# Kalkınma Ajansları (ka.gov.tr, kaynak='ka') — e-Satınalma sayfasında "Kalkınma Ajansı" rozetiyle
$VENV/python ka_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
# Durum bayatlama — son teklif tarihi geçmiş 'aktif' ilanları 'kapandi' yapar.
# TÜM scraperlardan SONRA olmalı: jandarma/dmo/ilan_gov upsert'leri durum:'aktif' ile
# eski kaydı yeniden açabiliyor; bu adım cron sonunda net durumu düzeltir. Bildirim/MV
# adımlarından ÖNCE ki bayat ilanlara bildirim gitmesin, sayaçlar doğru tazelensin.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Durum bayatlama ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.ilan_durum_bayatlat() AS kapatilan;" >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python idare_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1
# AI kategori backfill — kelime kurallarının çözemediği 'Diğer' ilanları Gemini ile kanonik kategoriye
# oturtur. Her satır YALNIZCA BİR KEZ (ai_kategori_denendi damgası) → idempotent, token israfı yok.
# --limit 400 + --rpm 15: günlük yeni Diğer'leri + birikmiş kuyruktan biraz karşılar, free tier'a sığar.
# MV tazelemeden ÖNCE koşar ki harita/sektör/kategori MV'leri yeni kategorileri aynı gece yansıtsın.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === AI kategori backfill ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ai_kategori_backfill.py --limit 400 --rpm 15 >> /opt/ihale-platform/logs/scraper.log 2>&1
# Sektör-bazlı bildirim: günün yeni ilan/RFQ'ları → sektörü eşleşen firmalara (taksonomi hizalı, dedup'lı).
# p_gun=1 → yalnız bugünkü yeni kayıtlar (retroaktif spam yok); dedup tekrar üretmez.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Sektor bildirim ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.yeni_ilan_bildirim_uret(1) AS ilan, public.yeni_rfq_bildirim_uret(1) AS rfq;" >> /opt/ihale-platform/logs/scraper.log 2>&1
# ── TÜRETİLMİŞ KOLON TAZELEME ────────────────────────────────────────────────
# İkisi de migration'da BİR KEZ dolduruldu ama gece işine bağlanmamıştı; yani her
# gece taranan yeni kayıtlar bu kolonlarda NULL/bayat kalıyordu — kapsam artmıyor,
# AZALIYORDU. MV tazelemelerinden ÖNCE koşmalılar: lot_sayisi tenzilat
# ortalamalarını, idare_tur ise idare özetini besliyor.
#
# 1) idare_tur — ilanlar + dogrudan_temin_ilanlari'na idare türünü (belediye/
#    üniversite/bakanlık…) denormalize eder. 19 Tem ölçümü: DT %23, ihaleler %12,5
#    kapsam. "İdare Türü" filtresi (ihaleler.html + dogrudan-temin.html) buna bağlı;
#    tazelenmezse yeni ilanlar filtreye HİÇ yakalanmaz.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Idare turu tazeleme ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.idare_tur_tazele();" >> /opt/ihale-platform/logs/scraper.log 2>&1
# 2) lot_sayisi — her sonuç satırına ihalesinin kısım sayısını yazar. Tenzilat
#    yüzeyleri "lot_sayisi = 1 değilse gösterme" kuralıyla çalışıyor (bkz.
#    migration_sonuc_lot_sayisi.sql); bayatlarsa yeni çok-kısımlı ihaleler yine
#    sahte %95 tenzilat üretir — 18 Tem'de kapatılan hatanın geri gelmesi demek.
#    20 Tem: satır-içi tam tablo GROUP BY (538K satır/gece) yerine hedefli fonksiyon
#    (migration_lot_gece.sql): yalnız NULL satır içeren ihale gruplarını yeniden
#    sayar (≤~5K satır/gece, kardeş satır düzeltmesi dahil). Sonuç backfill'inden
#    SONRA, MV tazelemelerinden ÖNCE koşmalı (analiz MV'leri lot_sayisi okur).
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Lot sayisi tazeleme ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.lot_sayisi_tazele() AS lot_tazeleme;" >> /opt/ihale-platform/logs/scraper.log 2>&1

# İdareler Dizini özeti — gece verisi değiştikten sonra MV tazele (idareler.html
# idare_dizin_json() ile bunu okur; CONCURRENTLY = okumalar bloklanmaz).
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Idare ozet MV ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_ozet_mv;" >> /opt/ihale-platform/logs/scraper.log 2>&1
# Harita il×sektör×firma MV'si — sonuç backfill'inden sonra tazele (harita.html
# il_sektor_ozet + il_sektor_firmalar bunu okur; normalize_firma maliyeti nedeniyle dakikalar sürebilir).
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Harita sektor MV ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_sektor_firma_mv;" >> /opt/ihale-platform/logs/scraper.log 2>&1
# Sayfa-açılışı özet MV paketi (migration_ozet_mv_paketi.sql) — il_sektor_ozet_mv
# il_sektor_firma_mv'den türediği için ondan SONRA; yukleniciler-kaynaklılar da
# yuklenici_yenile'den sonra koşmuş olur. Hepsi küçük (~sn mertebesi).
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Ozet MV paketi ===" >> /opt/ihale-platform/logs/scraper.log
# NOT: her REFRESH ayrı -c'de — tek -c içinde noktalı virgülle birleştirilirse psql
# hepsini TEK örtük transaction'da yollar ve CONCURRENTLY transaction içinde çalışmaz.
docker exec -i supabase-db psql -U postgres -d postgres \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_sektor_ozet_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.kategori_sayim_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_sayim_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_firma_dagilimi_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.yuklenici_ozet_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.sonuc_ozet_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.ihale_kelime_idf;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.dt_kategori_sayim_mv;" \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.dt_idare_ozet_mv;" >> /opt/ihale-platform/logs/scraper.log 2>&1

# ── Türetilmiş alanlar: etkin_tarih + idare_tur ────────────────────────────────────
# İKİSİ DE UCUZ (yalnız DEĞİŞEN satırları yazar, IS DISTINCT FROM) ve MV'lerden ÖNCE
# koşmalı: MV'ler bu kolonları okuyabilir.
#   etkin_tarih  : ihalelerin %95'inde üç tarih alanı da boş (sonuç-backfill kayıtları);
#                  sıralama/filtre için bağlı sonuç kaydının tarihinden türetilir.
#                  ilan_tarihi'ye YAZILMAZ — sonuç tarihi ≠ ilan tarihi (veri çarpıtmaz).
#   idare_tur    : EKAP/DETSİS eşlemesinden (idare_tur tablosu) ilanlar + DT'ye taşınır.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Turetilmis alanlar (etkin_tarih + idare_tur) ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres   -c "SELECT public.etkin_tarih_tazele();"   -c "SELECT public.idare_tur_tazele();" >> /opt/ihale-platform/logs/scraper.log 2>&1

# ── İdare hiyerarşisi: eşleme → kapanış → sayaçlar ────────────────────────────────
# SIRA ZORUNLU ve bu üçü de 20 Tem'e kadar cron'da HİÇ YOKTU — yani her gece eklenen
# ilanların detsis_no'su NULL kalıyor, ağaç sayaçları bayatlıyordu.
#   1) ilan_detsis_esle     : yeni ilan/DT satırlarına detsis_no yazar (idare_tur üzerinden,
#                             bu yüzden idare_tur_tazele'den SONRA gelmeli)
#   2) idare_kapanis_uret   : ağaç değiştiyse ata-torun tablosunu yeniden üretir (~312K satır)
#   3) REFRESH ...sayim_mv  : kendi/toplam sayaçları; (1) ve (2) bitmeden çalıştırılırsa
#                             bir önceki günün rakamlarını gösterir
# CONCURRENTLY: benzersiz indeks var (idx_idare_hiy_sayim_pk), gece okumaları kilitlenmesin.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Idare hiyerarsisi ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres   -c "SELECT * FROM public.ilan_detsis_esle();"   -c "SELECT public.idare_kapanis_uret() AS kapanis_satiri;" >> /opt/ihale-platform/logs/scraper.log 2>&1
docker exec -i supabase-db psql -U postgres -d postgres   -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_hiyerarsi_sayim_mv;" >> /opt/ihale-platform/logs/scraper.log 2>&1
#   4) idare_bagsiz_mv     : Kurum Ağacı'nın "Bağlantısız Kurumlar" dalı (detsis_no'su
#                            NULL kalan idareler) — (1)'den SONRA gelmeli ki gece
#                            eşlenen idareler bağlantısız listesinden düşsün.
#                            (migration_kurum_agaci_bagsiz.sql uygulanana kadar bu
#                            satır log'a "does not exist" yazar, zincir etkilenmez)
docker exec -i supabase-db psql -U postgres -d postgres   -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_bagsiz_mv;" >> /opt/ihale-platform/logs/scraper.log 2>&1

# ── İdare türü boşluk alarmı ───────────────────────────────────────────────────────
# İhalede görünüp idare_tur eşlemesinde KARŞILIĞI OLMAYAN idareler = yeni açılan/ad
# değiştiren birimler. Sessizce "sınıfsız" kalmasınlar diye log'a düşer; sayı büyürse
# ekap_detsis_cek.py --tara --devam ile eşleme tazelenir.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Idare turu bosluk raporu ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -tAc   "SELECT 'eksik idare: ' || (public.idare_tur_bosluk(20)->>'eksik_idare_sayisi') || ' | etkilenen ihale: ' || (public.idare_tur_bosluk(20)->>'eksik_ihale_sayisi');"   >> /opt/ihale-platform/logs/scraper.log 2>&1

# ── ilan_metni backfill (geçmiş kalem listeleri) — EN SONDA, BİLEREK ────────────────
# Geçmiş ~340K ilan kompakt üretilmişti (ilan_metni=NULL, eski managed-Supabase limiti).
# EKAP sonuçlanmış listesini sayfalayıp eksikleri doldurur → eşleştirme motoru + site içi
# arama (arama_fold ÜRETİLMİŞ kolonu ilan_metni'yi içerir) zenginleşir.
# NEDEN EN SONDA: EKAP üçüncü taraf; yoğun tarama IP bloğu riski taşır. Kritik gece işleri
# (scraper/bildirim/MV) ÖNCE bitsin ki olası blok o geceki ana veri akışını vurmasın.
# YAVAŞ & GÜVENLİ (kullanıcı kararı): 200 sayfa/gece (~20K kayıt tarama, ~%67 isabet),
# eşzamanlılık 2 + istek arası uyku + checkpoint ile devam + ardışık hatada kendini durdurma.
# Kabaca 25-35 gecede tamamlanır. Blok görülmezse --max-pages artırılabilir.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === ilan_metni backfill ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ilan_metni_backfill.py --max-pages 200 --eszamanli 2 >> /opt/ihale-platform/logs/scraper.log 2>&1
