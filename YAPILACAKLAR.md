# Ä°halePlatform â€” YapÄ±lacaklar Listesi

> ## 🔗 23 TEM — FASONDA KÖPRÜSÜ (bilgi notu, ihaleglobal'de değişiklik YOK)
> fasonda.com paneli, ihaleglobal PUBLIC REST'inden read-only ilan çekiyor (anon key, güvenli
> kolonlar: baslik/kategori/il/son_teklif; idare maskesi geçerli). /rest/v1 2r/s limitine bu
> istekler de dahil (panel başına 1 istek). Köprü detayı: C:\fasonda_platform\js\kopru.js.

> ## 🏭 22 TEM — MaaS/FASONDA AYRI PROJEYE TAŞINDI
> Kullanıcı kararı: fasonda.com KESİN marka; proje ihaleglobal'den AYRI çalışır. Yeni repo:
> **`C:\fasonda_platform`** (kendi YAPILACAKLAR.md + FASONDA_PLAN.md orada). Bu dosya artık
> YALNIZ ihaleglobal işleri içindir; fasonda işleri buraya YAZILMAZ.

> ## 🌐 21 TEM — MaaS DOMAIN ARAŞTIRMASI (yeni talep, araştırıldı)
> Kullanıcı MaaS (fason üretim ağı) projesi için boşta .com domain istedi. RDAP (Verisign
> resmi kayıt sorgusu, 404=boşta) ile ~40 aday tarandı; boşta olanlar konuşmada raporlandı.
> Satın alma kararı + ödeme kullanıcıda (parola/ödeme paneline ben giremem).
> **GÜNCELLEME:** kullanıcının domaini zaten VAR: **fasonda.com**. Uluslararası tur (71 aday tarandı):
> boşta en iyiler = capacityradar.com, rfqmap.com, turkforge.com, manuradar.com, fabtoria.com;
> ayrıca fasondo.com / fasonhq.com / fasonapp.com boşta (typo/yardımcı koruma adayı).
> **Önerim:** global dahil TEK marka fasonda.com (façon kökü Batı'da sezgisel; Xometry/Fictiv
> emsali uydurma-marka sınıfı çalışıyor; tek domain = SEO/marka gücü bölünmez). fasondo typo-koruma opsiyonel.

> ## âœ… SESSÄ°Z-KAYIP DÃœZELTMELERÄ° â€” 8 SCRAPER MERGE+DEPLOY (20 Tem gece)
> KullanÄ±cÄ±nÄ±n "aynÄ± hata baÅŸka scraper'larda da var mÄ±" sezgisi doÄŸrulandÄ±: denetim 8
> dosyada **14 hata** buldu (4 kritik), hepsi paralel worktree'de dÃ¼zeltildi, adversarial
> incelendi, `main`'e birleÅŸti, VDS'e deploy edildi. Ã‡akÄ±ÅŸma YOK (her dosya ayrÄ±).
> - `dt_kazanan_scraper` (kritik): geÃ§ici hata alan satÄ±r artÄ±k damgalanmÄ±yor (tuple dÃ¶nÃ¼ÅŸ
>   + None sayacÄ±); **DT kazanan %7,9 darboÄŸazÄ±nÄ±n parÃ§asÄ± buydu.**
> - `ekap_dogrudan_temin_scraper` (kritik): upsert False dÃ¶nÃ¼ÅŸÃ¼ kontrol ediliyor.
>   âš ï¸ Ä°nceleme YENÄ° hata yakaladÄ±: ilk dÃ¼zeltme kalÄ±cÄ± 4xx'te SONSUZ TAKILMA yaratÄ±yordu
>   â†’ onarÄ±m backfill'deki "partiyi bÃ¶l, zehirli kaydÄ± izole et" yaklaÅŸÄ±mÄ±yla Ã§Ã¶zdÃ¼ (8 senaryo test).
> - `ekap_sonuc_backfill` (kritik): `GeciciHata` tipi â€” 403/429/5xx artÄ±k raise ediyor,
>   eÅŸleÅŸen ilan atlanmÄ±yor, Ã¶lÃ¼ emniyet dalÄ± Ã§alÄ±ÅŸÄ±r oldu.
> - `ekap_sonuc_scraper` (kritik): checkpoint artÄ±k VERÄ°DEN SONRA (Ã¶nce yaz, sonra iÅŸaretle).
> - `ilan_metni_backfill`, `ted_scraper`, `ekap_detsis_cek`, `ilan_gov_scraper`: boÅŸ-liste/
>   kÄ±sa-parti/tavan teyidi + hata sayacÄ± + dÃ¼rÃ¼st Ã¶zet.
> - Kod deploy = sonraki gece cron'u otomatik alÄ±r. **Ä°ki KURTARMA migration'Ä±** (opsiyonel,
>   kullanÄ±cÄ± onayÄ±): `migration_dt_kazanan_kurtarma.sql` (yanlÄ±ÅŸ damgalÄ±larÄ± yeniden kuyruÄŸa),
>   `migration_sonuc_checkpoint_kurtarma.sql`.
>
> ## âœ… ROTATING ISP PROXY + ASYNC dt_kazanan â€” /24 THROTTLE Ã‡Ã–ZÃœLDÃœ (21 Tem)
> **KullanÄ±cÄ± TÃ¼rkiye ISP proxy aldÄ± (10 GB), /24 throttle'Ä± kÃ¶kten Ã§Ã¶zdÃ¼.**
> - **`proxy_havuz.py` rotating gateway modu** (`PROXY_ROTATING_GATEWAY=1`): tek endpoint
>   (`152.232.134.118:2810`) her istekte farklÄ± Ã§Ä±kÄ±ÅŸ IP dÃ¶ndÃ¼rÃ¼yor (test: 60 istek â†’ 44
>   benzersiz IP, 12 farklÄ± /8 bloÄŸu). Endpoint AZAMI_UC sanal uca Ã§oÄŸaltÄ±lÄ±r, IP-soÄŸumasÄ±
>   kapatÄ±lÄ±r. Geriye uyumlu (varsayÄ±lan kapalÄ±). `.env` gÃ¼ncellendi (eski Webshare yedeklendi).
> - **`dt_kazanan_scraper.py` SENKRONâ†’ASYNC** (`ekap_detsis` deseni: Semaphore + gather):
>   senkron ~20/dk â†’ **async ~483/dk (~24Ã—)**. 5 sessiz-kayÄ±p mantÄ±ÄŸÄ± korundu (adversarial
>   inceleme async yarÄ±ÅŸ hatasÄ± yakaladÄ± â†’ istek-Ã¶ncesi devre-kesici gate ile dÃ¼zeltildi).
>   `DT_KAZANAN_ESZAMANLI` (Ã¶ntanÄ±m 24) + `DT_KAZANAN_ARDISIK_HATA` (Ã¶ntanÄ±m 8, rotating iÃ§in
>   40 â€” sabit-IP mantÄ±ÄŸÄ± rotating'de turu erken durduruyordu) env'e alÄ±ndÄ±.
> - **â–¶ï¸ KOÅUYOR:** `--limit 500000 --rpm 2000`, 40 iÅŸÃ§i, ARDISIK 40. 672K kuyruk **~23 saat**.
>   MonitÃ¶rlÃ¼. Bandwidth tahmini ~4-5 GB (10 GB kota iÃ§inde â€” Ä°ZLE).
> - â­ dt_kazanan bitince â†’ token backfill'e dÃ¶n (rotating proxy ile, checkpoint 6778, kalan %42).
> - âš ï¸ AÃ‡IK: rotating modda cezalandÄ±rma sanal uÃ§larÄ± Ã¶ldÃ¼rebiliyor (gw16 dÃ¼ÅŸtÃ¼) â€” ideal
>   deÄŸil ama 40'tan birkaÃ§Ä± Ã¶lse 30+ kalÄ±r. Gerekirse rotating'de cezalandÄ±rmayÄ± kapat.
>
> ## ğŸ”´ EKAP /24 THROTTLE â€” BÃœYÃœK BACKFILL'LER TIKANDI (21 Tem, teÅŸhis edildi â€” YUKARIDA Ã‡Ã–ZÃœLDÃœ)
> **KÃ–K NEDEN: hafÄ±zadaki "tek /24 proxy" riski GERÃ‡EKLEÅTÄ°.** TÃ¼m 100 Webshare IP'si tek
> `166.88.110.0/24` bloÄŸunda. BugÃ¼n saatlerce sÃ¼ren token backfill + dt_kazanan `--rpm 500`
> burst'Ã¼ EKAP'Ä± bloÄŸu rate-limit'e almaya itti. KanÄ±t: dt_kazanan ilk 1.200 isteÄŸi hÄ±zlÄ±
> attÄ±, sonra sÃ¼rÃ¼nmeye baÅŸladÄ± (`--rpm 200`'e dÃ¼ÅŸÃ¼rÃ¼nce bile 100sn'de 0 sÃ¶zleÅŸme). Proxy
> havuzu SAÄLAM (GetListByParameters sondajÄ± 1,2s), ama dtDetayGetir'e yoÄŸun istekten sonra
> EKAP throttle uyguluyor.
> **BugÃ¼n Ã¼retilen deÄŸer (throttle'a raÄŸmen):** token %42,3â†’%57,5; DT sonuÃ§ 117.384â†’**120.725**
> (+3.341). Backfill'ler DURDURULDU (EKAP'Ä± dÃ¶vmek throttle'Ä± uzatÄ±r). Checkpoint'ler gÃ¼vende:
> token bf = sayfa 6778; dt_kazanan = kazanan_denendi damgasÄ± (1398 dt_no iÅŸlendi).
> **KÄ°LÄ°T GÃ–ZLEM:** gece cron dt_kazanan `--limit 2000 --rpm 300`'Ã¼ SORUNSUZ koÅŸuyor (04:44,
> 1877 sÃ¶zleÅŸme) â€” dÃ¼ÅŸÃ¼k hacim + kÄ±sa tur EKAP'Ä± yormuyor. Sorun BÃœYÃœK hacmin tek seferde
> agresif Ã§ekilmesi.
> **KARAR GEREK (kullanÄ±cÄ±):**
> (A) **Proxy Ã§eÅŸitliliÄŸi** â€” Webshare panelinden farklÄ± /24 bloklarÄ±ndan IP al (KALICI Ã§Ã¶zÃ¼m;
>     /24 riski kalkar, bÃ¼yÃ¼k backfill'ler mÃ¼mkÃ¼n). GerekÃ§e IP *sayÄ±sÄ±* deÄŸil Ã‡EÅÄ°TLÄ°LÄ°ÄÄ°.
>     KullanÄ±cÄ±nÄ±n hesabÄ± gerekli.
> (B) EKAP throttle'Ä±nÄ±n geÃ§mesini bekle (saatler), sonra DÃœÅÃœK tempoda (--rpm 150, --limit
>     parÃ§alÄ±) yeniden dene â€” yavaÅŸ ama proxysiz.
> (C) Gece cron'un doÄŸal temposuna bÄ±rak (her gece 2000) â€” ama 675K kuyruk iÃ§in aylar.
>
> ## âš ï¸ TOKEN BACKFILL â€” EKAP DERÄ°N OFFSET YAVAÅLAMASI (21 Tem, Ã¶lÃ§Ã¼ldÃ¼)
> Token backfill %42,3 â†’ **%57,5** geldi (sayfa 6777, skip ~865K). Ama sayfa 6775+ EKAP
> "read timeout" veriyor; scraper retry + 60sn bekleme ile geÃ§iyor (dayanÄ±klÄ±, checkpoint'li,
> 0 kalÄ±cÄ± kayÄ±p). HÄ±z 36 â†’ ~2-3 sayfa/dk dÃ¼ÅŸtÃ¼. Kalan ~4.900 sayfa bu tempoda 2-3 GÃœN.
> KÃ¶k neden bizim tarafÄ±mÄ±z deÄŸil â€” EKAP `GetListByParameters` derin offset'te (skip>~865K)
> yavaÅŸlÄ±yor (hafÄ±za: [[dt-kazanan-captcha]] / derin sayfalama dersi).
> **KARAR VERÄ°LDÄ° (21 Tem): seÃ§enek (c) â€” dt_kazanan Ã¶ne alÄ±ndÄ±.** Token backfill DURAKLATILDI
> (checkpoint **6778**'de gÃ¼vende, `.dt_scraper_checkpoint.json`), sÄ±ralÄ±-koÅŸma dersine uyularak
> dt_kazanan'a temiz EKAP eriÅŸimi verildi. `dt_kazanan_scraper --limit 500000 --rpm 500` koÅŸuyor;
> kuyruk **675.571** (464K kurtarma + token backfill'in eklediÄŸi yeni token'lÄ±lar). dtDetayGetir
> tekil Ã§aÄŸrÄ± â†’ derin-offset yavaÅŸlamasÄ± YOK. ~22 saat, DT kazananÄ± %7,9'dan yÃ¼kseltecek.
> MonitÃ¶rlÃ¼ (`dt_kazanan_tur.log`, iÅŸaret `dt_kazanan_tur_tamam`).
> â­ dt_kazanan bitince â†’ token backfill'e DÃ–N (checkpoint 6778'den devam, kalan token'sÄ±zlarÄ±
>    doldur) VEYA (b) alternatif strateji araÅŸtÄ±r (derin offset hÃ¢lÃ¢ yavaÅŸsa).
>
> ## â–¶ï¸ TOKEN BACKFILL KOÅUYOR + KURTARMA UYGULANDI (20 Tem gece)
> - **Ä°fade indeksi UYGULANDI:** `idx_ilanlar_idare_norm_expr` + DT'si CONCURRENTLY kuruldu.
>   `idare_tur_tazele` Ã¶lÃ§Ã¼ldÃ¼: **25 dk â†’ 3m40s** (~7x). Gece cron'u artÄ±k dakikalar sÃ¼rer.
> - **Backfill sonrasÄ± zincir doÄŸrulandÄ±:** detsis kapsamasÄ± `ilanlar` **%92,7 â†’ %97,1**
>   (340K yeni backfill ilanÄ± da eÅŸleÅŸti), `idare_tur` **%99,8 dolu**.
> - **DT kazanan kurtarma UYGULANDI:** 16.719 yanlÄ±ÅŸ-damgalÄ± satÄ±r geri aÃ§Ä±ldÄ± â†’
>   token'lÄ±+sonuÃ§lanmÄ±ÅŸ+denenmemiÅŸ kuyruk **464.581**.
> - **SonuÃ§-checkpoint kurtarma UYGULANMADI:** NO-OP (scrape_log boÅŸ) + bozuk ekap_id join;
>   ABORT guard'landÄ±.
> - **â–¶ï¸ TOKEN BACKFILL BAÅLADI:** `ekap_dogrudan_temin --backfill --max-pages 7000`,
>   checkpoint 4965'ten devam. **4966 duvarÄ± AÅILDI** (dÃ¼zeltilmiÅŸ scraper zehirli kaydÄ±
>   izole edip geÃ§ti â€” 4966/4967/4968 sorunsuz). ~6.700 sayfa, birkaÃ§ saat. 860K token'sÄ±z
>   DT'nin E10/E11'ini dolduracak. MonitÃ¶rlÃ¼ (`logs/dt_token_bf.log`, iÅŸaret `dt_token_bf_tamam`).
> - â­ SIRADAKÄ° (token bf bitince): `dt_kazanan_scraper --limit 500000 --rpm 300` â€” 464K+
>   token'lÄ± kuyruÄŸu iÅŸler, DT kazanan %7,9'dan yÃ¼kselir.
>
> ## ğŸ¯ DT KAZANAN DARBOÄAZI â€” TAM ANATOMÄ° (20 Tem gece, canlÄ± Ã¶lÃ§Ã¼m)
> "DT kazanan neden %7,9?" sorusunun kesin cevabÄ±. `dogrudan_temin_ilanlari` = 1.490.644:
>
> | Dilim | Adet | Not |
> |---|---|---|
> | SonuÃ§lanmÄ±ÅŸ (kazananÄ± olmalÄ±) | 1.395.038 (%93,6) | hedef evren |
> | **Token YOK** | **860.297** | kazanan Ã‡EKÄ°LEMEZ â€” token ÅŸart |
> | â”” bunlardan sonuÃ§lanmÄ±ÅŸ | **817.376** | asÄ±l kayÄ±p: deÄŸerli ama eriÅŸilemez |
> | Token VAR | 630.347 | Ã§ekilebilir |
> | â”” `kazanan_denendi` iÅŸaretli | yalnÄ±z 129.800 | ~500K token'lÄ±-ama-DENENMEMÄ°Å |
> | `dogrudan_temin_sonuclari` (Ã§ekilmiÅŸ kazanan) | 117.384 (%7,9) | mevcut Ã§Ä±ktÄ± |
>
> **KÃ–K NEDEN â€” iki katmanlÄ±:**
> 1. **Token boÅŸluÄŸu:** `dt_ihale_token`/`dt_idare_token` (=E10/E11), DT listeleme API'sinden
>    geliyor ama **18 Tem'den Ã–NCE atlanÄ±yordu** (`ekap_dogrudan_temin_scraper.py:172`).
>    KanÄ±t: token'sÄ±z 860K'nÄ±n en yeni kazÄ±masÄ± **17 Tem**, `yayin_tarihi` de NULL (o da E8,
>    aynÄ± gÃ¼n eklendi). Bu kayÄ±tlar bir daha listelenmediÄŸi iÃ§in token'sÄ±z kaldÄ±.
> 2. **Ä°ÅŸleme boÅŸluÄŸu:** token'lÄ± 630K'nÄ±n yalnÄ±z 129K'sÄ± denenmiÅŸ â€” ve `dt_kazanan_scraper`'da
>    bulunan B6 hatasÄ± (geÃ§ici hata alan satÄ±r kalÄ±cÄ± `kazanan_denendi` damgalanÄ±yor) bu dÃ¼ÅŸÃ¼k
>    oranÄ±n bir parÃ§asÄ± olabilir.
>
> **Ã‡Ã–ZÃœM PLANI (SIRALI â€” paralel verim 10x dÃ¼ÅŸÃ¼rÃ¼r):**
> - Ã–N KOÅUL: `ekap_dogrudan_temin_scraper` + `dt_kazanan_scraper` B6 dÃ¼zeltmeleri (ÅŸu an
>   sessiz-kayÄ±p workflow'unda) MERGE olmalÄ± â€” yoksa backfill yine sessizce kaybeder.
> - **AdÄ±m 1 â€” Token backfill:** `ekap_dogrudan_temin_scraper --backfill` tam koÅŸusu.
>   merge-duplicates ile 860K token'sÄ±zÄ±n E10/E11'ini doldurur. Tarih hedeflemesi YOK
>   (`yayin_tarihi` NULL) â†’ baÅŸtan sona gitmeli (~6.700 sayfa Ã— ~1,5sn â‰ˆ 3-4 saat).
> - **AdÄ±m 2 â€” Kazanan backfill:** `dt_kazanan_scraper --limit 900000`. Token dolunca
>   ~1,3M sonuÃ§lanmÄ±ÅŸ DT'nin kazananÄ± Ã§ekilebilir hale gelir (ÅŸimdi 117K).
> - AdÄ±m 1 bitmeden AdÄ±m 2'yi koÅŸma (token yoksa boÅŸa gider).

> ## âš¡ ACÄ°L PERF: `idare_tur_tazele()` her gece ~25 dk CPU yakÄ±yor (20 Tem, Ã¶lÃ§Ã¼ldÃ¼)
> 340K backfill sonrasÄ± zincirde bu fonksiyon **24+ dakika** aktif kaldÄ± (CPU-bound, kilit
> beklemiyor). KÃ¶k neden: iki UPDATE de `WHERE t.idare_norm = idare_normalize(i.idare)` â€”
> JOIN koÅŸulunda satÄ±r-baÅŸÄ± fonksiyon Ã§aÄŸrÄ±sÄ±, **ifade indeksi YOK** â†’ 1,9M + 1,49M satÄ±rda
> tam tarama. Fonksiyon `statement_timeout='1800s'` (30 dk) ile korunmuÅŸ, yani yavaÅŸlÄ±k
> biliniyormuÅŸ. Ã‡Ã–ZÃœM (zincir bitince, CONCURRENTLY):
> `CREATE INDEX CONCURRENTLY idx_ilanlar_idare_norm_expr ON ilanlar (public.idare_normalize(idare));`
> ve DT iÃ§in aynÄ±sÄ±. âš ï¸ `idare_normalize` IMMUTABLE olmalÄ± (ifade indeksi ÅŸart koÅŸar) â€”
> deÄŸilse Ã¶nce onu IMMUTABLE iÅŸaretle. KalÄ±cÄ± Ã§Ã¶zÃ¼m backlog #31 (`idare_norm` STORED generated
> column) ama ifade indeksi migration'sÄ±z-ÅŸema-deÄŸiÅŸikliksiz ilk adÄ±m.

> # ğŸ§­ GÃœNCEL BACKLOG (20 Tem akÅŸam â€” TAM TARAMA + CANLI DOÄRULAMA SONRASI)
> Bu blok, 5.195 satÄ±rÄ±n tamamÄ±nÄ±n 6 paralel okuyucuyla taranÄ±p Ã§Ä±kan **227 aday aÃ§Ä±k
> maddenin 232 kapanÄ±ÅŸ kanÄ±tÄ±yla Ã§apraz-elenmesi** sonucudur. AÅŸaÄŸÄ±dakiler **gerÃ§ekten
> aÃ§Ä±k** olanlar; kalanÄ± canlÄ±da kapanmÄ±ÅŸ ama dosyada iÅŸaretlenmemiÅŸ kayÄ±tlardÄ±.
>
> **âš ï¸ DOSYA HÄ°JYENÄ° â€” bir sonraki oturum bunu yapsÄ±n:** en sÄ±k bayatlama kalÄ±bÄ±
> "migration X VDS'e uygulanmalÄ±" (deploy edilince eski satÄ±r [x] yapÄ±lmÄ±yor; 6 Ã¶rnek).
> SatÄ±r ~2500'Ã¼n altÄ± **%80 bayat** ve orada ters-kronoloji kuralÄ± da bozuk (8 Tem bloÄŸu
> 10 Tem'in Ã¼stÃ¼nde). Managed-Supabase dÃ¶nemi maddeleri ("SQL Editor'dan koÅŸ") toptan
> geÃ§ersiz. â†’ 2500 altÄ±nÄ± `YAPILACAKLAR_ARSIV.md`'ye taÅŸÄ±.
>
> ## ğŸ¯ EÅLEÅTÄ°RME KAPSAMI â€” Ã–LÃ‡ÃœLDÃœ VE KAPANDI (20 Tem gece)
> `paginationTake` 1â†’300 deÄŸiÅŸikliÄŸinin sonucu **canlÄ± DB'de doÄŸrulandÄ±**:
>
> | Tablo | Toplam | detsis_no dolu | Kapsama |
> |---|---|---|---|
> | `ilanlar` | 1.618.303 | 1.500.896 | **%92,7** (Ã¶nce ~%32) |
> | `dogrudan_temin_ilanlari` | 1.490.644 | 982.046 | **%65,9** |
>
> Zincir Ã§Ä±ktÄ±sÄ±: **39.333** idare eÅŸleÅŸmesi yazÄ±ldÄ± (`kaynak='ekap-detsis'`),
> `ilan_detsis_esle` 1.406.872 ihale + 72.681 DT satÄ±rÄ± gÃ¼ncelledi, kapanÄ±ÅŸ tablosu
> 312.259 satÄ±r, MV tazelendi, `dt_kazanan` otomatik yeniden baÅŸladÄ± (yazÄ±yor:
> 1.000 dt_no â†’ 1.032 sÃ¶zleÅŸme).
>
> HiyerarÅŸi sayaÃ§larÄ± da buna paralel bÃ¼yÃ¼dÃ¼ (eski deÄŸerler â†’ yeni):
> `Ä°Ã‡Ä°ÅLERÄ° BAKANLIÄI` ihale 4.010 â†’ **49.313**, DT 49.106 â†’ **54.251**;
> `EMNÄ°YET GENEL MÃœDÃœRLÃœÄÃœ` ihale 1.203 â†’ **15.148**, DT 26.835 â†’ **30.138**.
>
> **âœ… DT BOÅLUÄUNUN KÃ–K NEDENÄ° BULUNDU (20 Tem gece, Ã¶lÃ§Ã¼ldÃ¼):** DT %65,9'da kalÄ±yor
> Ã§Ã¼nkÃ¼ eÅŸleÅŸmeyen 508.598 satÄ±rÄ±n idare adÄ± **boÅŸ deÄŸil** (0 boÅŸ) â€” adlar `idare_tur`
> tablosunda **var** (31.325 tekil addan 29.075'i, yani %92,8) ama **hepsi
> `kaynak='kural'` ve `detsis_no` NULL** â†’ `ilan_detsis_esle()`'nin yazacaÄŸÄ± numara yok.
>
> Sebep YAPISAL, eÅŸleÅŸtirme hatasÄ± DEÄÄ°L: DETSÄ°S taramasÄ± idare adlarÄ±nÄ± EKAP'Ä±n
> **ihale arama** API'sinden (`GetListByParameters`) topluyor. YalnÄ±zca doÄŸrudan temin
> yapan, hiÃ§ ihaleye Ã§Ä±kmayan kurumlar o API'de HÄ°Ã‡ gÃ¶rÃ¼nmÃ¼yor â†’ DETSÄ°S eÅŸleÅŸmesi
> hiÃ§ oluÅŸmuyor, sadece kural motorundan *tÃ¼r* etiketi alÄ±yorlar.
> EÅŸleÅŸmeyenlerin tepesi bunu birebir doÄŸruluyor: belediye ÅŸirketleri (EKDAÄ A.Å. 4.463,
> BELTUR A.Å. 3.321, ANET A.Å. 3.006, HARBEL A.Å. 2.778, SANBEL Ltd. 2.543), hastane
> baÅŸhekimlikleri ve "SatÄ±n Alma Åube MÃ¼dÃ¼rlÃ¼ÄŸÃ¼" tipi alt birimler â€” Ã§ok DT alÄ±p az ihale
> yapan birimler.
>
> **â­ SEÃ‡ENEKLER (karar gerek):** (a) DT tarafÄ±nda idare-bazlÄ± bir EKAP uÃ§ noktasÄ± varsa
> aynÄ± `idareIdâ†’ad` taramasÄ±nÄ± DT iÃ§in tekrarla; (b) belediye ÅŸirketini ana belediyeye
> baÄŸla (yaklaÅŸÄ±k, hiyerarÅŸi aÄŸacÄ±nda "baÄŸlÄ± ÅŸirket" dalÄ±); (c) sÄ±nÄ±rÄ± kabul et ve
> arayÃ¼zde kapsama rozetiyle dÃ¼rÃ¼stÃ§e gÃ¶ster. KalÄ±cÄ± Ã§Ã¶zÃ¼m hÃ¢lÃ¢ `idareIdHash` (backlog #30).
>
> ## âœ… 20 TEM AKÅAM â€” BU OTURUMDA KAPANANLAR (8 iÅŸ paralel worktree'de Ã¼retildi,
> ## adversarial incelemeden geÃ§ti, `main`'e birleÅŸtirildi, push edildi)
> TamamÄ± **kodda hazÄ±r**; migration'lar VDS'te UYGULANMADI (DB yazma onayÄ± gerekiyor).
> - #3 **Kurum AÄŸacÄ± UI** â†’ `kurum-analiz.html` (idareler.html zaten oraya redirect'miÅŸ).
>   Tembel dallar, kendi/toplam ihale+DT rozetleri, kapsama ÅŸeridi, **BaÄŸlantÄ±sÄ±z
>   Kurumlar ayrÄ± dal**, arama+yol aÃ§ma. Ä°nceleme 414-riski buldu (`in.()` URL'i) â†’
>   kÃ¶k nedenden Ã§Ã¶zÃ¼ldÃ¼: sunucu-taraflÄ± `idare_dal_son_ihaleler` RPC'si.
> - #4 **HiyerarÅŸi filtresi** (ihale+DT) â€” `SETOF` dÃ¶nen RPC'ler; PostgREST fonksiyona
>   tablo gibi davrandÄ±ÄŸÄ± iÃ§in mevcut filtre/sÄ±ralama/sayfalama kodu DEÄÄ°ÅMEDÄ°.
>   Filtre seÃ§ilmedikÃ§e eski sorgu yolu korunur â†’ migration'sÄ±z da sayfa kÄ±rÄ±lmaz.
> - #5 **`ekap_scraper` â†’ proxy havuzu**, `EKAP_HAVUZ=0` kaÃ§Ä±ÅŸ kapÄ±sÄ±yla. Ä°nceleme
>   ayrÄ± bir hata yakaladÄ±: `EKAP_DETAY_LIMIT` yalnÄ±z detay Ã§ekimini sÄ±nÄ±rlÄ±yordu ama
>   yazma tÃ¼m listeyi kapsÄ±yordu â†’ limitli tur mevcut kayÄ±tlarÄ± NULL'la eziyordu.
> - #6 **`stat-kazanim` teÅŸhisi:** kart DT sayÄ±sÄ±nÄ± `dogrudan_temin_sonuclari`'ndan
>   (79.337 derlenmiÅŸ kayÄ±t) alÄ±p 1,39M'lik listeye gÃ¶tÃ¼rÃ¼yordu. SayaÃ§ artÄ±k kartÄ±n
>   tÄ±klama hedefiyle AYNI evrenden (`DT_DURUM_SONUC`) sayÄ±yor.
> - #7 **Dashboard alt yarÄ±sÄ± mod-farkÄ±ndalÄ±klÄ±** (`ilanlariYukle`/`enIyiEslesmeler`/
>   `sonGorulenler`); DT'de olmayan alanlar (bedel filtresi, maliyet sÄ±ralamasÄ±)
>   dÃ¼rÃ¼stÃ§e devre dÄ±ÅŸÄ±.
> - #8 **`satinalma_talepleri.olusturan_user_id`** â€” kolon anon select'inden Ã§Ä±karÄ±ldÄ±
>   (yalnÄ±z `isOwner` iÃ§in kullanÄ±lÄ±yormuÅŸ, misafirde zaten iÅŸlevsiz) + REVOKE migration'Ä±.
>   **SIRA: Ã¶nce frontend deploy, sonra REVOKE.**
> - #9 **`ilanlar_sonuc` Ã¶lÃ¼ JOIN kÃ¶k nedeni KESÄ°NLEÅTÄ°:** `ihale_sonuclari`'nÄ± dolduran
>   tek yazar `ekap_sonuc_backfill.py` `ekap_id`'yi HÄ°Ã‡ yazmÄ±yor; gerÃ§ek anahtar
>   `(ilan_id, kisim_no)` ve `ilan_id = ilanlar.id` UUID FK. TeÅŸhis + dÃ¼zeltme SQL'i yazÄ±ldÄ±.
> - **`lot_sayisi` gece adÄ±mÄ±:** gÃ¶rev tarifi bayatmÄ±ÅŸ (c021157 ile eklenmiÅŸ) ama satÄ±r-iÃ§i
>   TAM TABLO GROUP BY'dÄ± â€” her gece ~538K satÄ±r yeniden sayÄ±lÄ±yordu; hedefli fonksiyona taÅŸÄ±ndÄ±.
>
> **+ PlandÄ±ÅŸÄ± ama canlÄ±yÄ± etkileyen GERÃ‡EK HATA dÃ¼zeltildi (`d2d8f98`):** misafirde
> dashboard'un iki widget'Ä± SESSÄ°ZCE boÅŸ kalÄ±yordu (`ilanlar.idare`/`ekap_id` anon'a kapalÄ±;
> biri select'e VEYA WHERE'e girince PostgREST tÃ¼m sorguyu 42501 ile reddediyor, try/catch
> hatayÄ± yutuyordu). DÃ¼zeltme 18 Tem'de yapÄ±lmÄ±ÅŸ ama **hiÃ§ birleÅŸtirilmemiÅŸ** eski bir
> worktree'de kalmÄ±ÅŸtÄ± â€” paralel-oturum kaybÄ±nÄ±n somut Ã¶rneÄŸi. TarayÄ±cÄ±da gerÃ§ek misafir
> oturumuyla doÄŸrulandÄ±: yeni select 200 / eski select 401, tablo 10 satÄ±r doluyor.
> AyrÄ±ca `boot sÄ±rasÄ±` dÃ¼zeltildi: `uyeMi` artÄ±k maskeli kolona dokunan HER sorgudan Ã¶nce set ediliyor.
>
> âš ï¸ **AÃ‡IK â€” DEPLOY EDÄ°LMEDÄ° (20 Tem, doÄŸrulandÄ±):** `d2d8f98` `origin/main`'e push'landÄ± ama
> **VDS hÃ¢lÃ¢ eski dosyayÄ± servis ediyor**, yani canlÄ±da misafir dashboard'u HÃ‚LÃ‚ bozuk.
> KanÄ±t (anon curl, kimlik gerekmez):
> ```
> curl -s https://ihaleglobal.com/dashboard.html | grep -n "uyeKolon\|idare.ilike"
> # canlÄ± 1265: select'te kosulsuz "ekap_id, ..., idare"   â†’ misafirde 42501
> # canlÄ± 1271: kosulsuz .or(...idare.ilike...)            â†’ misafirde 42501
> # "uyeMi = !!session" â†’ 0 eslesme (boot sirasi duzeltmesi de yok)
> ```
> Kalan tek adÄ±m (VDS'te, SSH sÄ±nÄ±flandÄ±rÄ±cÄ± bizi blokluyor â†’ **kullanÄ±cÄ± koÅŸmalÄ±**):
> ```
> ssh ihale "cd /opt/ihale-platform && git pull origin main"
> ```
> Deploy sonrasÄ± aynÄ± curl `uyeKolon`'u gÃ¶rmeli; ardÄ±ndan giriÅŸsiz tarayÄ±cÄ±da alt tablo
> hatasÄ±z dolmalÄ±. **DERS:** "tarayÄ±cÄ±da doÄŸrulandÄ±" â‰  "canlÄ±da dÃ¼zeldi" â€” commit'in
> kendisi frontend'i deploy ETMEZ, ayrÄ± `git pull` ÅŸart (bkz. migration-uygulandi-mi-denetimi).
>
> **Temizlik:** 8 workflow worktree'si + 3 eski worktree kaldÄ±rÄ±ldÄ±, `git worktree list`
> artÄ±k yalnÄ±z `main`. Ã–lÃ¼ `api.js` script tag'i 2 sayfadan silindi (`af2b895`).
> NOT: `claude/happy-gauss-ce4605` dalÄ±nda 1 birleÅŸmemiÅŸ commit gÃ¶rÃ¼nÃ¼r â€” iÃ§eriÄŸi yeni
> koda UYARLANARAK uygulandÄ±, dal yalnÄ±zca kayÄ±t olarak duruyor.
>
> ## ğŸ“Š VERÄ° ENVANTERÄ° (20 Tem gece â€” "her ÅŸey Ã§ekildi mi?" denetimi)
> **Cevap: HAYIR.** Denetim anÄ±nda **hiÃ§bir scraper Ã§alÄ±ÅŸmÄ±yordu** ve Ã¼Ã§ hat sessizce durmuÅŸtu.
>
> | Kaynak | Ã‡ekilen | Eksik | Durum |
> |---|---|---|---|
> | Ä°hale ilanlarÄ± | 1.618.303 | ~341K (2012 yarÄ±m + 2011 + 2010) | â–¶ï¸ koÅŸuyor |
> | DT duyurularÄ± | 1.490.644 | â€” | âœ… |
> | Ä°hale sonuÃ§larÄ± | 538.064 (ihalelerin %20,7'si) | â€” | durdu |
> | **DT kazananlarÄ±** | 117.384 (**%7,9**) | 464.581 token'lÄ± + **817.376 token'sÄ±z** | â¸ï¸ |
> | DT token | 630.347 (%42,3) | ~860K | â¸ï¸ sayfa-4966 duvarÄ± |
> | KÄ°K kararlarÄ± | 97 â†’ **179** | geÃ§miÅŸ yÄ±llar | âœ… blokaj Ã§Ã¶zÃ¼ldÃ¼ |
> | UluslararasÄ± (TED) | 1.249 | Ã§ok bÃ¼yÃ¼k | â–¶ï¸ koÅŸuyor |
> | Ä°lan metni | 16.362 (**%1,0**) | 1,6M | â¸ï¸ hiÃ§ koÅŸmadÄ± |
> | Embedding | 5.539 (%0,3) | 1,6M | â¸ï¸ |
> | AI kategori | %71,8 | ~456K | kÄ±smi |
>
> ### ğŸ”´ BACKFILL'DE Ä°KÄ° GERÃ‡EK HATA BULUNDU VE DÃœZELTÄ°LDÄ°
> 1. **Zehirli kayÄ±t (`bdc967e`)** â€” 2012'de skipâ‰ˆ47.000 sabit HTTP 500 veriyor, backfill
>    8 ardÄ±ÅŸÄ±k hatada duruyordu. **Sondajla kanÄ±tlandÄ±:** aynÄ± offset `take=200` ile OK,
>    `take=500/1000` ile HATA; `skip=100.000 take=1000` ile OK. Yani ne offset derinliÄŸi ne
>    sayfa boyutu â€” o aralÄ±ktaki TEK BÄ°R kayÄ±t EKAP'Ä±n yanÄ±tÄ±nÄ± bozuyor.
>    â†’ Hata alÄ±nca parti 4'e bÃ¶lÃ¼nerek kÃ¼Ã§Ã¼lÃ¼yor (1000â†’250â†’62â†’â€¦), zehirli kayÄ±t dar pencereye
>    sÄ±kÄ±ÅŸÄ±yor; `take=1`'de bile patlarsa O KAYIT atlanÄ±p sayÄ±lÄ±yor. Sonra boyut geri tÄ±rmanÄ±yor.
> 2. **BoÅŸ liste = SESSÄ°Z VERÄ° KAYBI (`bee3e0a`)** â€” 1. dÃ¼zeltme zehirli bÃ¶lgeyi geÃ§ti, ama
>    hemen ardÄ±ndan EKAP boÅŸ liste dÃ¶ndÃ¼rdÃ¼ ve koddaki koÅŸulsuz `if not lst: break` yÄ±lÄ±
>    "bitti" sayÄ±p 2011'e geÃ§ti. **2012 checkpoint'i 47.062/166.242'de kaldÄ±, 119.180 kayÄ±t
>    sessizce dÃ¼ÅŸtÃ¼ ve log "tamam" izlenimi verdi.** â†’ ArtÄ±k boÅŸ listede `skip >= toplam` mÄ±
>    diye bakÄ±lÄ±yor; deÄŸilse DELÄ°K olarak gÃ¼rÃ¼ltÃ¼lÃ¼ loglanÄ±p atlanÄ±yor, checkpoint yazÄ±lÄ±yor.
>
> ### âœ… Ä°HALE BACKFILL + TED TAMAMLANDI (20 Tem gece)
> - **Ä°hale backfill BÄ°TTÄ°:** 254.416 satÄ±r gÃ¶nderildi, 31 dk. `ilanlar` 1.618.303 â†’
>   **1.958.302** (+340K). 2012/2011/2010 checkpoint'te TAM. 2012'de ~8 daÄŸÄ±nÄ±k zehirli
>   kayÄ±t uyarlamalÄ± kÃ¼Ã§Ã¼ltmeyle tek tek izole edilip atlandÄ± (119K deÄŸil, sadece 8 kayÄ±p).
> - **TED BÄ°TTÄ°:** 7.831 ihale upsert, `uluslararasi_ihaleler` 1.249 â†’ **7.909** (6,3x).
>   Sayfalama dÃ¼zeltmesi devasa aÃ§Ä±ÄŸÄ± kapattÄ±. (Gemini 6.660 baÅŸlÄ±k Ã§evirdi â€” kota yakÄ±ldÄ±.)
> - **Backfill sonrasÄ± zincir KOÅUYOR:** idare_tur_tazele â†’ etkin_tarih â†’ ilan_detsis_esle â†’
>   kapanÄ±ÅŸ â†’ lot â†’ MV refresh. 340K yeni ihalenin detsis/tÃ¼r/durumu iÅŸleniyor.
>
> ### â­ SIRADAKÄ° VERÄ° Ä°ÅLERÄ° (paralel scraper verimi 10x dÃ¼ÅŸÃ¼rdÃ¼ÄŸÃ¼ iÃ§in SIRALI)
> 1. ~~Ä°hale backfill~~ âœ… + zincir koÅŸuyor
> 2. **DT token hattÄ±** â€” asÄ±l darboÄŸaz: 817.376 sonuÃ§lanmÄ±ÅŸ duyuruda token YOK, o yÃ¼zden
>    kazanan Ã§ekilemiyor. Derin sayfalama duvarÄ±na takÄ±lÄ±yor; il/tarih dilimlemesi denenmeli.
> 3. DT kazananlarÄ± (464.581 token'lÄ± kuyruk)
> 4. `ilan_metni` (%1,0) â€” eÅŸleÅŸtirme iÃ§in "en deÄŸerli veri iÅŸi" diye iÅŸaretlenmiÅŸti
> 5. KÄ°K geÃ§miÅŸ yÄ±llarÄ± (blokaj Ã§Ã¶zÃ¼ldÃ¼, artÄ±k Ã§ekilebilir)
> âš ï¸ TED Ã§evirisi Gemini kotasÄ± yakÄ±yor (7 gÃ¼nde 6.660 baÅŸlÄ±k) â€” geniÅŸ backfill'de maliyet gÃ¶zet.
>
> ## â¸ï¸ TEK BEKLEYEN MIGRATION: `migration_dt_arama.sql` â€” BAKIM PENCERESÄ° Ä°STER
> DT'ye `baslik_fold` + `arama_fold` generated kolonlarÄ± + trigram GIN indeksleri ekliyor.
> **MALÄ°YET (dosyanÄ±n kendi notu):** 1,49M satÄ±rda `ADD COLUMN GENERATED` tabloyu yeniden
> yazar â†’ **3-8 dk ACCESS EXCLUSIVE kilit**, o sÃ¼re boyunca DT'ye dokunan HER sorgu bekler;
> ardÄ±ndan kolon baÅŸÄ±na 8-20 dk `CREATE INDEX CONCURRENTLY` (o kÄ±sÄ±m kilitlemez).
> Yani gÃ¼ndÃ¼z uygulanÄ±rsa DT yÃ¼zeyleri birkaÃ§ dakika donar. **DÃ¼ÅŸÃ¼k trafikli saatte
> koÅŸulmalÄ±.** O zamana kadar DT aramasÄ± `trAramaKalibi` joker yedeÄŸiyle Ã§alÄ±ÅŸÄ±yor
> (kayÄ±p yok, sadece indeks yerine seq-scan).
> Migration kendi GRANT'larÄ±nÄ± doÄŸru yÃ¶netiyor: `baslik_fold` anon+Ã¼ye, `arama_fold`
> YALNIZ Ã¼ye (iÃ§inde `idare` geÃ§tiÄŸi iÃ§in misafire verilirse maskeli kurum adÄ± trigram
> aramasÄ±yla harf harf geri okunabilirdi) â€” doÄŸrulama bloÄŸunda negatif test var.
>
> ## âœ… BACKLOG TURU 2 â€” 8 Ä°Å BÄ°RLEÅTÄ° (20 Tem gece)
> 8 iÅŸ izole worktree'de Ã¼retildi, adversarial incelendi, `main`'e birleÅŸtirildi, deploy
> edildi. **5 Ã§akÄ±ÅŸma elle Ã§Ã¶zÃ¼ldÃ¼** â€” hepsi "iki taraf da haklÄ±" tipiydi:
> - `ihaleler.html`: benim `trAramaKalibi` (TR katlama) + onlarÄ±n `prDeger` (PostgREST
>   or() gramerine enjeksiyon kaÃ§Ä±ÅŸÄ±) â†’ **ikisi birleÅŸtirildi**, sÄ±ra: Ã¶nce katla sonra kaÃ§Ä±r.
> - `ted_scraper.py`: iki dal da `gemini_cevir`'i deÄŸiÅŸtirmiÅŸ (biri yeni SDK'ya taÅŸÄ±mÄ±ÅŸ,
>   diÄŸeri tuple sÃ¶zleÅŸmesi + backoff eklemiÅŸ) â†’ yeni SDK gÃ¶vdesi tuple dÃ¶necek ÅŸekilde
>   birleÅŸtirildi; Ã§aÄŸrÄ± yeri `cevrilmis, basarili = ...` bekliyordu, kontrol edildi.
> - `kik-kararlar` / `dogrudan-temin` / `uluslararasi`: onlarÄ±n sunucu-taraflÄ± Ã§Ã¶zÃ¼mÃ¼
>   (fold kolonu / RPC) benim istemci geÃ§ici Ã§Ã¶zÃ¼mÃ¼mden Ã¼stÃ¼ndÃ¼ â†’ **onlarÄ±nki alÄ±ndÄ±**,
>   ama **yedek yollarÄ±na benim TR katlamam eklendi** (migration uygulanmadan da kayÄ±p olmasÄ±n).
>
> **Ek olarak bulunan gerÃ§ek hatalar (ajanlar kapsam dÄ±ÅŸÄ±nda yakaladÄ±):**
> - `ihaleler.html` GeÃ§miÅŸ sekmesinde `count=exact` + ILIKE â†’ **57014 timeout, HTTP 500**
>   (Ã¶lÃ§Ã¼ldÃ¼: 3,4-4,6 sn). `PLANLI_SAYIM_SEKMELERI` ile GeÃ§miÅŸ de `count=planned`'a alÄ±ndÄ±.
> - `ihaleler.html`'de **11 filtre alanÄ±nÄ±n handler'Ä± yokmuÅŸ** â€” kullanÄ±cÄ± filtreyi
>   deÄŸiÅŸtiriyor, liste deÄŸiÅŸmiyordu (yalnÄ±z "Filtrele" dÃ¼ÄŸmesiyle uygulanÄ±yordu).
> - `genai` SDK migrasyonu **yarÄ±m kalmÄ±ÅŸmÄ±ÅŸ** â€” 4 dosya hÃ¢lÃ¢ eski SDK'daymÄ±ÅŸ, taÅŸÄ±ndÄ±.
> - TED'de iki kÃ¶k neden: `--max-pages 6` sert tavanÄ± + tarih penceresi eksikliÄŸi.
> - KÄ°K teÅŸhisi: backlog'daki "302/401/406 IP-bloklu" tanÄ±sÄ± **BAYAT** â€” o URL'ler
>   12 Tem'de terk edilmiÅŸ, satÄ±r gÃ¼ncellenmemiÅŸ.
>
> ## âœ… MIGRATION'LAR UYGULANDI (20 Tem gece, kullanÄ±cÄ± onayÄ±yla â€” 8 dosya)
> Hepsi `ON_ERROR_STOP=1` ile, tek tek, nesne-bazlÄ± doÄŸrulanarak koÅŸuldu.
>
> | Migration | SonuÃ§ |
> |---|---|
> | `migration_temizlik_20tem` | âœ… idare_tur yÃ¼zeyi anon'dan REVOKE + `idx_ilanlar_olusturulma` |
> | `migration_idare_dal_ihaleler` | âœ… `idare_dal_son_ihaleler` |
> | `migration_kurum_agaci_bagsiz` | âœ… `idare_bagsiz_mv` + 2 RPC |
> | `migration_dt_detsis_grant` | âœ… **YENÄ° â€” aÅŸaÄŸÄ±daki tÄ±kanmayÄ± Ã§Ã¶zmek iÃ§in yazÄ±ldÄ±** |
> | `migration_hiyerarsifiltre` | âœ… (ilk denemede kendi guard'Ä±yla durdu, grant sonrasÄ± geÃ§ti) |
> | `migration_lot_gece` | âœ… `lot_sayisi_tazele()` â†’ `{"guncellenen": 0}` |
> | `migration_satinalma_revoke` | âœ… **user_id ifÅŸasÄ± KAPANDI** (anon artÄ±k 42501) |
> | `migration_sonucjoin_fix` | âœ… **Ã¶lÃ¼ JOIN onarÄ±ldÄ±** â€” 0 â†’ **537.988 sonuÃ§lu satÄ±r** |
>
> ### ğŸ”´ SÃœREÃ‡TE Ã‡IKAN Ä°KÄ° GERÃ‡EK SORUN
> 1. **`DT.detsis_no` hiÃ§ GRANT edilmemiÅŸti** â€” `migration_hiyerarsifiltre` kendi doÄŸrulama
>    bloÄŸuyla uygulanmayÄ± REDDETTÄ° ve iÅŸlemi geri aldÄ± (guard tam olarak iÅŸini yaptÄ±).
>    KÃ¶k neden bu projede **DÃ–RDÃœNCÃœ** kez aynÄ±: kolon-GRANT'lar sonradan eklenen kolonlara
>    geniÅŸlemiyor. `ilanlar.detsis_no` Ã¼yeye aÃ§Ä±ktÄ±, DT'deki kardeÅŸi unutulmuÅŸtu.
>    â†’ `migration_dt_detsis_grant.sql` yazÄ±ldÄ± (politika `ilanlar` ile birebir: Ã¼yeye aÃ§Ä±k,
>    misafire kapalÄ±), uygulandÄ±, hiyerarÅŸi filtresi sonra geÃ§ti.
> 2. **PostgREST ÅŸema Ã¶nbelleÄŸi `NOTIFY` ile tazelenmedi** â€” migration'lar geÃ§mesine raÄŸmen
>    yeni RPC'lerin hepsi `PGRST202 "no matches were found in the schema cache"` veriyordu.
>    â†’ `supabase-rest` restart, ardÄ±ndan **`supabase-kong` restart** (bayat upstream dersi).
>    Sonra tÃ¼mÃ¼ tanÄ±ndÄ±. **KURAL: yeni RPC ekleyen migration sonrasÄ± `NOTIFY`'a GÃœVENME,
>    `docker restart supabase-rest && docker restart supabase-kong` yap ve REST'ten doÄŸrula.**
>
> ### ğŸ” `ilanlar_sonuc` teÅŸhisi (kesin sonuÃ§)
> `ihale_sonuclari.ekap_id` **538.064 satÄ±rÄ±n hepsinde NULL** (scraper o kolonu hiÃ§ yazmÄ±yor),
> `ilan_id` %100 dolu. Eski join `i.ekap_id = s.ekap_id` â†’ **0 eÅŸleÅŸme**. DoÄŸru join
> `s.ilan_id = i.id` â†’ 538.064 satÄ±r / 335.397 ihale. View `CREATE OR REPLACE` ile onarÄ±ldÄ±
> (grant'lar korundu), sona `kisim_no` + `lot_sayisi` eklendi. Kardinalite artÄ±k kÄ±sÄ±m bazlÄ±
> (1.820.970 satÄ±r) â€” bu BÄ°LÄ°NÃ‡LÄ°; view'Ä± okuyan tÃ¼ketici yok.
>
> ### âœ… Uygulama sonrasÄ± doÄŸrulama
> - 9 yeni nesnenin **9'u** canlÄ±da (`to_regclass`/`to_regproc`).
> - Frontend RPC parametre adlarÄ± DB imzalarÄ±yla **birebir** uyuÅŸuyor.
> - Anon maske regresyonu temiz: `ilanlar`, `ilanlar_sonuc`, `dogrudan_temin_sonuclari`,
>   `idare_hiyerarsi`, `satinalma_talepleri`, `idare_bagsiz_mv` â†’ **hepsi 401**.
> - 10 canlÄ± sayfa 200 dÃ¶nÃ¼yor.
>
> â­ **KALAN TEK MIGRATION Ä°ÅÄ°:** Ã¶deme atomikliÄŸi (`migration_payment_atomik.sql`) â€” hÃ¢lÃ¢
> kullanÄ±cÄ± kararÄ±nda, `payment.py` dÃ¼zenlemesi + API restart gerektiriyor.
>
> ## ğŸ§¹ SESSÄ°Z HATA SÃœPÃœRGESÄ° (20 Tem gece) â€” 25 sayfa, 5 desen, Ã§ok-ajanlÄ±
> KullanÄ±cÄ±nÄ±n kendi bulduÄŸu 3 hatanÄ±n (DT kartlarÄ±, il dropdown, misafir dashboard) ait
> olduÄŸu desenler tÃ¼m sayfalarda arandÄ±; her bulgu **canlÄ± anon API ile** doÄŸrulandÄ±.
> **20 doÄŸrulanmÄ±ÅŸ bulgu**; 9'u dÃ¼zeltilip yayÄ±na alÄ±ndÄ±.
>
> **DESENLER (yeni sayfa yazarken kontrol listesi):**
> D1 1000-satÄ±r tavanÄ± Â· D2 maskeli kolon misafir yolunda Â· D3 mod kavram karÄ±ÅŸmasÄ± Â·
> D4 TÃ¼rkÃ§e ILIKE Â· D5 yutulan hata / asÄ±lÄ± "YÃ¼kleniyor..."
>
> ### âœ… DÃ¼zeltilip canlÄ±ya alÄ±ndÄ±
> - **`ihaleler.html` SAYFALAMA TAMAMEN Ã–LÃœYDÃœ (`711fe1b`)** â€” repoda olmayan `#sb-count`
>   elemanÄ±na yazÄ±m TypeError fÄ±rlatÄ±yor, async fonksiyonda kimse catch etmediÄŸi iÃ§in
>   sessizce yutuluyor ve **bir alt satÄ±rdaki `paginasyonOlustur()` hiÃ§ Ã§alÄ±ÅŸmÄ±yordu.**
>   1,6M kayÄ±tta kullanÄ±cÄ± 2. sayfaya geÃ§emiyordu. CanlÄ±: 0 â†’ **11 sayfa butonu**.
> - **TR arama kaybÄ± 4 yÃ¼zeyde** â€” `ihaleler` misafir dalÄ± (0â†’166), `dogrudan-temin`
>   (72â†’7.075; Ã¶lÃ§Ã¼m: "mÃ¼dÃ¼rlÃ¼ÄŸÃ¼" 126.777 vs "mudurlugu" 72 = **1760x**), `kik-kararlar`
>   (0â†’61), `uluslararasi` (89â†’207). Ã‡Ã¶zÃ¼m: `js/main.js` â†’ `trAramaKalibi()`.
> - **`dokumanlar.html` misafirde tamamen Ã¶lÃ¼ydÃ¼** â€” `ekap_id`+`idare` select'te â†’ 42501.
> - **1000-satÄ±r tavanÄ±** â€” `uluslararasi` dropdown 33â†’34; `dogrudan-temin` il yedek yolu
>   69â†’81 (`js/main.js` â†’ `TR_ILLER_BUYUK` kanonik liste).
> - `takipte.html` asÄ±lÄ± "YÃ¼kleniyor..." Â· `bildirimler.html` yutulan hata.
>
> ### â­ DÃ¼zeltilmeyi bekleyen (backlog turu 2 aynÄ± dosyalara dokunduÄŸu iÃ§in beklemede)
> - `ihale-detay.html:673` misafire "AI analizi yapÄ±lmadÄ±" diyor â€” oysa analiz VAR, kolon
>   maskeli (satÄ±r 808'de aynÄ± tuzak iÃ§in doÄŸru mesaj yazÄ±lmÄ±ÅŸ, burada unutulmuÅŸ).
> - `ihale-detay.html:824` `uygunFirmalarYukle` misafirde koÅŸulsuz Ã§aÄŸrÄ±lÄ±yor â†’ garanti 42501.
> - `ozel-ihaleler.html` 275/276/383/397 â€” geo RPC misafirde Ã¶lÃ¼yor + hata/boÅŸ aynÄ± dala
>   dÃ¼ÅŸÃ¼yor + 2 yerde TR ILIKE.
> - `rekabet-analizi.html` 356/613 Â· `firma-analiz.html:1080` Â· `kurum-analiz.html:1528` â€”
>   hata "kayÄ±t yok" gibi gÃ¶steriliyor, 4 panel kalÄ±cÄ± "YÃ¼kleniyor..."da kalabiliyor.
>
> ## ğŸ”´ GÃœVENLÄ°K
> 1. **Secret rotasyonu (satÄ±r 809):** JWT_SECRET + Google client secret + Resend SMTP
>    key sohbette ifÅŸa oldu. 17 Tem rotasyonu ESKÄ° ifÅŸayÄ± kapattÄ± â€” bunlar SONRAKÄ°.
> 2. **`authenticated` rolÃ¼ hÃ¢lÃ¢ tablo-geneli SELECT (806).** anon'da 3 kez yaÅŸanan
>    "sonradan eklenen kolon" delik sÄ±nÄ±fÄ±nÄ±n Ã¼ye-rolÃ¼ versiyonu; hiÃ§ denetlenmedi.
> 3. **API_EXTERNAL_URL hÃ¢lÃ¢ `http://195.85.207.126:8000` (810)** â€” GoTrue e-posta
>    linkleri Ã§Ä±plak IP'ye gidiyor (kÄ±rÄ±k UX + phishing gÃ¶rÃ¼nÃ¼mÃ¼). Restart paketine dahil.
> 4. `satinalma_talepleri.olusturan_user_id` misafire GERÃ‡EK UUID dÃ¶ndÃ¼rÃ¼yor (curl ile
>    Ã¶lÃ§Ã¼ldÃ¼). Frontend + REVOKE **birlikte**; ters sÄ±ra sayfayÄ± kÄ±rar.
>
> ## ğŸŸ  VERÄ° / SCRAPER
> 5. **DT geÃ§miÅŸ backfill paketi:** checkpoint'i 11.600-12.500 arasÄ± sondajla doÄŸru
>    sayfaya al, sonra `--backfill`. Scraper'a "X yeni / Y gÃ¼ncellendi" log ayrÄ±mÄ± ekle
>    (yanÄ±ltÄ±cÄ± log 17 sayfalÄ±k boÅŸ turu "baÅŸarÄ±lÄ±" gÃ¶stermiÅŸti). **SIRALI koÅŸ.**
> 6. `ekap_ihale_backfill` bitince: eÅŸleÅŸmeyen durum metinleri loglarÄ±nÄ± oku â†’
>    `ilan_durum_bayatlat()`. "iptal" durumu eklenmeden Ã–NCE arayÃ¼z sekmeleri hazÄ±r olmalÄ±.
> 7. Backfill sonrasÄ± idare_tur turu (`--detsis-yeniden --tazele-atla` + `idare_tur_tazele()`);
>    kalan ~827 sÄ±nÄ±fsÄ±z ada **hedefli kural â€” AI Ã–NERME**.
> 8. `ilan_metni_backfill` 402 krizinden beri hiÃ§ koÅŸmadÄ±, teyit yok (kapsama %4,5;
>    artÄ±rmak eÅŸleÅŸtirme iÃ§in en deÄŸerli veri iÅŸi).
> 9. âœ… **KIRPMA DÃœZELTÄ°LDÄ° (`6e40794`)** â€” dize yerine VERÄ° kÃ¼Ã§Ã¼ltÃ¼lÃ¼yor, Ã§Ä±ktÄ± her koÅŸulda
>    geÃ§erli JSON (`tum_teklifler_paketle`, 3 yÃ¼kte test edildi).
>    **Neden sessiz kalmÄ±ÅŸtÄ±:** kolon `jsonb` ama yÃ¼k *nesne* deÄŸil *dize* olarak yazÄ±lÄ±yor
>    (`jsonb_typeof='string'`, Ã§ift kodlama) â†’ Postgres iÃ§eriÄŸi hiÃ§ ayrÄ±ÅŸtÄ±rmÄ±yor, bozuk
>    metni kabul ediyor. Nesne yazÄ±lsaydÄ± insert ilk gÃ¼n hata verirdi.
>    â­ KALAN: canlÄ±da **720** bozuk satÄ±r (725 deÄŸil, Ã¶lÃ§Ã¼ldÃ¼) yeniden Ã§ekilmeli:
>    `SELECT ilan_id, kisim_no FROM ihale_sonuclari WHERE jsonb_typeof(tum_teklifler)='string'
>    AND right(btrim(tum_teklifler #>> '{}'),1) <> '}';`
>    â­ AYRICA: Ã§ift kodlamanÄ±n kendisi ayrÄ± bir borÃ§ â€” 538K satÄ±r *dize* tutuyor, ileride
>    firma olayÄ± madenlemek iÃ§in `#>>'{}'`+parse gerekecek. TÃ¼ketici olmadÄ±ÄŸÄ± iÃ§in
>    tek migration'la nesneye Ã§evrilebilir (karar gerek).
> 10. Kirlenen 1.297 `ilanlar.usul` satÄ±rÄ± (ham i18n anahtarÄ±) â€” Accept-Language dÃ¼zeldi,
>     yeniden Ã§ekilmeli/NULL'lanmalÄ±.
> 11. âœ… **`il` MOJIBAKE KAPANDI â€” Ã¶lÃ§Ã¼ldÃ¼, sorun YOK.** CanlÄ±: `il ~ '[?]'` â†’ **0 satÄ±r**,
>     kÃ¼Ã§Ã¼k harfli â†’ 0, 83 tekil deÄŸer (81 il + `''` + tekil bozuk `Ä°ZMIR`). Sonraki scraper
>     turlarÄ± sessizce dÃ¼zeltmiÅŸ. Sentezin "Ã¶nce Ã¶lÃ§" ÅŸÃ¼phesi haklÄ± Ã§Ä±ktÄ± â€” `mojibake_fix.py`
>     KOÅULMAMALI, koÅŸulacak veri yok.
> 12. Kategori kalanlarÄ±: 17.502 kanonik-dÄ±ÅŸÄ± satÄ±r + 67K OKAS'sÄ±z "DiÄŸer" + K1 AI
>     kuyruÄŸunun (153K) bitiÅŸi doÄŸrulanmadÄ±.
> 13. DTâ†’`yukleniciler` `normalize_firma` eÅŸleme turu â€” firma-analiz DT kapsamÄ±nÄ±n Ã¶nkoÅŸulu.
>     **DT cirosunu Ä°HALE cirosuna KARIÅTIRMA** kararÄ± korunacak.
> 14. **KÄ°K karar akÄ±ÅŸÄ± bloke** (302/401/406, cron her gece 0) â€” sayfa 97 kararla donmuÅŸ.
> 15. DT aramasÄ±nda TÃ¼rkÃ§e Ä°/Ä± katlamasÄ± yok + `dogrudan_temin_ilanlari.baslik` trigram
>     indeksi eksik (1,48M satÄ±rda seq-scan). Tek migration'da Ã§Ã¶zÃ¼lÃ¼r.
> 16. Ã‡ok kÄ±sÄ±mlÄ± sonuÃ§larda yalnÄ±z `sozlesmeBilgiList[0]` kaydediliyor â€” `lot_sayisi`
>     kuralÄ± semptomu maskeledi, **veri hÃ¢lÃ¢ eksik** (dÃ¼ÅŸÃ¼k aciliyet, bÃ¼yÃ¼k iÅŸ).
> 17. **21 Tem sabahÄ±:** `scraper.log`'da "=== Idare turu tazeleme ===" ve
>     "=== Lot sayisi tazeleme ===" satÄ±rlarÄ± gÃ¶rÃ¼lmeli (c021157, henÃ¼z hiÃ§ koÅŸmadÄ±).
> 18. EKAP firma kazÄ±ma hattÄ± (roster/VKN/yasaklÄ±/olay) â€” EKAP'sÄ±z kÄ±smÄ± ÅŸimdi yapÄ±labilir.
> 19. UluslararasÄ±: TED 300-kayÄ±t limit ÅŸÃ¼phesi, GÃ¼rcistan pagination, CPV-50 fallback artefaktÄ±.
>
> ## ğŸŸ¡ ARAYÃœZ
> 20. **Arama Commit 2:** `ihaleler.html`'in 3 handler'sÄ±z filtre alanÄ± + `sayacIstekNo`
>     yarÄ±ÅŸ korumasÄ±. Ã–NCE `f-idare` ILIKE gecikmesini Ã–LÃ‡ (57014 riski).
> 21. **Analiz Faz A:** parasal kartlara "yalnÄ±z ihaleler" rozeti + "N ihale Ã¼zerinden"
>     paydasÄ±. (DT parasal birleÅŸtirme **REDDEDÄ°LDÄ° â€” tekrar Ã¶nerme.**)
> 22. **Analiz Faz B:** `ihale_butce_mv` (ilan_id bazÄ±nda DISTINCT â€” `yaklasik_maliyet`
>     kÄ±sÄ±m bazlÄ± DEÄÄ°L, dÃ¼z SUM **35x ÅŸiÅŸirir**) + gece REFRESH + anon GRANT.
>     En yÃ¼ksek regresyon riskli iÅŸ.
> 23. **RFQ kÃ¶prÃ¼sÃ¼ + bayatlatma:** sÃ¼resi dolan RFQ'lar sonsuza dek "aÃ§Ä±k" gÃ¶rÃ¼nÃ¼yor
>     (doÄŸrudan kullanÄ±cÄ± ÅŸikÃ¢yeti). `>= now()` Ã§Ä±plak YAZMA â€” kolon nullable.
> 24. `idare_tur` kaynak rozeti ("kural"=Ã§Ä±karÄ±m vs "ekap-detsis"=resmÃ®).
> 25. P1.5 idareler dizini tÃ¼r bazlÄ± gezinme â€” sert filtre %67,7 sessiz kayÄ±p riski,
>     kapsama rozeti ÅART.
> 26. GoTrue TÃ¼rkÃ§e e-posta ÅŸablonu â€” **satÄ±r 1776'daki DÃœZELTÄ°LMÄ°Å komut** kullanÄ±lmalÄ±
>     (ilk yazÄ±lan komut Google OAuth bloÄŸunu SÄ°LÄ°YORDU).
> 27. KÃ¼Ã§Ã¼k UI borÃ§larÄ±: OKAS linki kapalÄ± ihalede boÅŸ sekme + `ozel-ihaleler` geo RPC
>     hÃ¢lÃ¢ v2 (Â±%500 bant yok) + `theme.js` version parametresi yok.
> 28. CSS birleÅŸtirme â€” **bilinÃ§li EN SONA** (`.toolbar` 4 sayfada 3 farklÄ±).
> 29. `index.html` mini harita satÄ±r-iÃ§i kopyasÄ± `harita.js`'e taÅŸÄ±nmalÄ±.
>
> ## ğŸ”µ ALTYAPI / EÅLEÅTÄ°RME
> 30. **`idareIdHash` kalÄ±cÄ± eÅŸleÅŸtirme anahtarÄ±** (14/14 test hazÄ±r) â€” `paginationTake=300`
>     ara Ã§Ã¶zÃ¼mdÃ¼, ad deÄŸiÅŸince yine kÄ±rÄ±lÄ±r.
> 31. `idare_norm` iki tabloda STORED generated column â€” gece `idare_tur_tazele()` 10 dk
>     CPU yiyor. Yeni kolona **GRANT SELECT ÅART** (yoksa misafirde 42501).
> 32. EÅŸleÅŸtirme sÄ±Ã§ramasÄ±: embedding-firma dalÄ± + Ã§evre-il komÅŸuluk + `ilan_metni[:1200]`.
> 33. Bildirim olgunlaÅŸtÄ±rma: gÃ¼nde ~50 bildirim riskine e-posta digest + gÃ¼nlÃ¼k cap.
> 34. KÃ¼Ã§Ã¼k borÃ§lar: `proxy_config.py` emekliye, sayfa 1000â†’5000 deÄŸerlendirmesi,
>     `google.genai` SDK migrasyonu (mevcut SDK "support ended").
> 35. Temizlik: 3 eski worktree (awesome-jang, brave-knuth, great-blackburn) + `stash@{0}`.
>     **`wf_*` worktree'lerine DOKUNMA** (Ã§alÄ±ÅŸan workflow'a ait).
> 36. Sidebar hÃ¢lÃ¢ her sayfada inline â€” nav deÄŸiÅŸikliÄŸi 20+ dosyaya dokunuyor.
> 37. DÃ¼ÅŸÃ¼k Ã¶ncelik kuyruÄŸu: `kazanan_teklif_farki` uÃ§ deÄŸerleri (-993%) AVG'yi bozuyor
>     (iÃ§lerinde en deÄŸerlisi), run_scraper adÄ±m-timeout'u, i18n, OKAS dropdown, vb.
>
> ## â¸ï¸ SENÄ°N KARARINI BEKLEYENLER (Ã¶zet â€” tam liste ve seÃ§enekler iÃ§in oturum kaydÄ±na bak)
> - **payment.py atomiklik paketi** â€” migration YAZILI ama **canlÄ±da YOK** (doÄŸrulandÄ±):
>   iyzico mÃ¼kerrer webhook â†’ Ã§ift kredi, kupon TOCTOU, lost-update. Migration inert.
> - Analizlerde varsayÄ±lan mod "TÃ¼mÃ¼" mÃ¼ "Ä°haleler" mi (DT 1,49M ihaleyi 555K eziyor).
> - "TÃ¼mÃ¼" modunda ortak tarih penceresi (DT 2025-26, ihale 2011'e uzanÄ±yor).
> - `kamu_ihaleleri.idare` misafire aÃ§Ä±k kalsÄ±n mÄ±.
> - Ham tablolarÄ±n anon SELECT'i (SEO â†” veri koruma dengesi).
> - Ticaret "her Ã¼lke" kapsamÄ± + Comtrade API key kaydÄ± (senin elinde).
> - Ä°yzico lisans + merchant credentials + hosted checkout (PCI: modal ham kart alÄ±yor).
> - Webshare tek /24 riski â€” panelden blok Ã§eÅŸitliliÄŸi talebi.
> - SMS/WhatsApp/Telegram landing'de vaat edildi, backend yok.
> - Firma kimlik doÄŸrulama (Ã¼cretli API) â€” rozet doÄŸrulamasÄ±z GÃ–STERÄ°LMEMELÄ°.
> - B2B davet e-postasÄ± iÃ§in KVKK/Ä°YS avukat teyidi.
> - Mimari/SEO: `app.` subdomain ayrÄ±mÄ± + prerender.
> - 24 TÃ¼rkÃ§e-harf mÃ¼kerrer firma grubu birleÅŸtirme (reÃ§ete hazÄ±r).
> - Embedding backfill hÄ±zÄ± (300/gece â‰ˆ 47+ gece).
> - Senin el testlerin: ihale-detay giriÅŸli gÃ¶rÃ¼nÃ¼m, "Kurumu Takip Et" e-posta ucu,
>   bozuk link URL'si, `farukdinc890` geÃ§ici parolasÄ± (`GeciciTest123!`) deÄŸiÅŸtir.

> # ğŸ“‹ 18â€“20 TEMMUZ OTURUM Ã–ZETÄ° â€” YAPILANLAR ve SIRADAKÄ°LER
> Bu blok tek oturuma dÃ¶nebilmek iÃ§in yazÄ±ldÄ±. Detaylar aÅŸaÄŸÄ±daki tarihli kayÄ±tlarda.
>
> ## âœ… TAMAMLANDI (canlÄ±da, doÄŸrulandÄ±)
>
> **Dashboard & DT arayÃ¼zÃ¼**
> - Tek global mod seÃ§ici (TÃ¼mÃ¼/Ä°haleler/DoÄŸrudan Temin) â€” tÃ¼m widget'lar tek noktadan
> - 9 baÄŸlantÄ±nÄ±n tamamÄ± mod-farkÄ±ndalÄ±klÄ± (`modLinkKur`): bir taraf 0 â†’ doÄŸrudan git,
>   ikisi de dolu â†’ seÃ§im popup'Ä±. `kurumlar-link` hiÃ§ atanmÄ±yordu, o da dÃ¼zeldi
> - **DT DetaylÄ± Ara paneli**: idare (Ã¼yeye Ã¶zel) / durum / tarih aralÄ±ÄŸÄ± / dokÃ¼manlÄ± +
>   hÄ±zlÄ± tarih Ã§ipleri + aktif filtre Ã§ipleri + "neden bazÄ± filtreler yok" notu
> - DT takip mekanizmasÄ± (â˜†/â˜…) + `takipte.html`'e DT bÃ¶lÃ¼mÃ¼
> - `dogrudan-temin.html` URL parametreleri: `sekme, ara, tur, durum, dokuman, detayli,
>   tarihBas, tarihBit, idare, il, kategori, dt_no`
>
> **GÃ¼venlik â€” anon maskeleme denetimi (61 nesne, Ã§ok-ajanlÄ±)**
> - **Ä°KÄ° KÃ–K NEDEN**: (A) varsayÄ±lan ayrÄ±calÄ±k â†’ yeni tablo/MV doÄŸuÅŸtan anon-aÃ§Ä±k,
>   REVOKE ÅŸart; (B) view'lar sahip-yetkisiyle Ã§alÄ±ÅŸÄ±r â†’ taban tablo maskesi uygulanmaz
> - KapatÄ±lanlar: `ilanlar_sonuc` (**KRÄ°TÄ°K, 356.904 satÄ±rda idare/ekap_id/ikn aÃ§Ä±ktÄ±**),
>   `dt_idare_ozet_mv` (38.105 idare adÄ±), `kamu_ihaleleri`, `kik_kararlar.ham_veri`,
>   `dogrudan_temin_sonuclari`, `dt_takipler`
>
> **Performans**
> - DT `kategori`/`tur` filtreleri **20-38 sn â†’ indeksli** (`migration_dt_index.sql`)
> - `ilanlar_sonuc` view'Ä±nÄ±n bozuk LEFT JOIN'i tespit edildi (356K satÄ±rÄ±n tamamÄ±nda NULL)
>
> **Proxy havuzu (`proxy_havuz.py` â€” YENÄ°)**
> - Ä°stek baÅŸÄ±na IP rotasyonu (eskiden script baÅŸÄ±na TEK IP, 99'u boÅŸta) â†’ **2,65x hÄ±z**
> - IP baÅŸÄ±na soÄŸuma, kÃ¼resel hÄ±z tavanÄ±, otomatik karantina, saÄŸlayÄ±cÄ±-arÄ±zasÄ±nda
>   erken durma, log seli kesme, `PROXY_AZAMI_UC` ile soket bÃ¼tÃ§esi
> - Direkt yedek **varsayÄ±lan KAPALI** ("VDS IP'si yasak" talimatÄ±)
> - **6 scraper baÄŸlandÄ±**: dt_kazanan, ekap_dogrudan_temin, kik_backfill,
>   ekap_sonuc_backfill, ekap_sonuc_scraper, ilan_metni_backfill
> - `ekap_scraper.post()` iki tipi de kabul eder (AsyncClient | havuz) â€” Ã§alÄ±ÅŸma-anÄ± ayrÄ±mÄ±
>
> **Ä°dare hiyerarÅŸisi (YENÄ°, uÃ§tan uca Ã§alÄ±ÅŸÄ±yor)**
> - `idare_hiyerarsi` (87.528 dÃ¼ÄŸÃ¼m) + `idare_ata_torun` kapanÄ±ÅŸ tablosu (312.259 satÄ±r)
>   + `idare_hiyerarsi_sayim_mv` + 4 RPC
> - KullanÄ±cÄ±nÄ±n Ã¶rneÄŸi birebir doÄŸrulandÄ±:
>   `ADANA Ä°L EMNÄ°YET (kendi 5 / toplam 12) â†’ EMNÄ°YET GENEL MD (1.203) â†’ Ä°Ã‡Ä°ÅLERÄ° (4.010)`
>   DT tarafÄ±: EGM **26.835**, Ä°Ã§iÅŸleri **49.106**
> - `run_scraper.sh`'e 3 eksik adÄ±m eklendi (`ilan_detsis_esle`, `idare_kapanis_uret`,
>   MV refresh) â€” hiÃ§biri cron'da yoktu, her gece kapsama eriyordu
>
> ## ğŸ”œ SIRADAKÄ°LER (18-20 Tem oturumunun listesi â€” GÃœNCELÄ° Ä°Ã‡Ä°N EN ÃœSTTEKÄ° BACKLOG'A BAK)
>
> 1. **EÅŸleÅŸtirme kapsamÄ± %32 â†’ ~%90.** âœ… KOD DÃœZELTÄ°LDÄ° + TARAMA KOÅUYOR (20 Tem
>    akÅŸam, commit `edbca81`): `paginationTake=300`, her farklÄ± yazÄ±m ayrÄ± satÄ±r,
>    jenerik yazÄ±m Ã§akÄ±ÅŸmasÄ±nda en Ã§ok kullanan kurum kazanÄ±r. 200'lÃ¼k deneme:
>    264 eÅŸleÅŸme / 59 kurumda Ã§oklu yazÄ±m â€” beklenen davranÄ±ÅŸ birebir doÄŸrulandÄ±.
>    VDS'te tam zincir arka planda: tara â†’ yaz â†’ ilan_detsis_esle â†’ kapanÄ±ÅŸ â†’ MV
>    refresh â†’ dt_kazanan otomatik yeniden baÅŸlar (`logs/detsis_tarama.log`,
>    bitiÅŸ iÅŸareti `logs/detsis_zincir_tamam`). ESKÄ° take=1 checkpoint SÄ°LÄ°NDÄ°
>    (uyumsuz). Bitince kapsama %'si DOÄRULANMALI (ilanlar.detsis_no dolu oranÄ±).
>    KalÄ±cÄ± Ã§Ã¶zÃ¼m hÃ¢lÃ¢ aÃ§Ä±k: `idareIdHash` (ada bakmayan kararlÄ± anahtar, 14/14 test).
> 2. **Backfill'leri SIRALI koÅŸtur.** Ã–lÃ§Ã¼m: tek scraper 100 uÃ§la **22.000 kayÄ±t/saat**,
>    iki scraper 40'ar uÃ§la **2.000/saat**. Paralel Ã§alÄ±ÅŸtÄ±rmak eÅŸzamanlÄ± baÄŸlantÄ±
>    bÃ¼tÃ§esini doldurup ters teper. Kuyruk 485K â†’ sÄ±ralÄ± koÅŸuda ~22 saat.
> 3. **`idareler.html` aÄŸaÃ§ arayÃ¼zÃ¼** â€” RPC'ler hazÄ±r (`idare_agac_dallar/yol/ara/
>    alt_agac_detsis`). AÄŸaÃ§ta "BaÄŸlantÄ±sÄ±z Kurumlar" (%20) AYRI DAL olarak gÃ¶sterilmeli,
>    gizlenirse veri eksik sanÄ±lÄ±r. Kapsama oranÄ± her dÃ¼ÄŸÃ¼mde yazÄ±lmalÄ±.
> 4. **Ä°hale/DT aramasÄ±na hiyerarÅŸi filtresi** â€” "bu kurum ve altÄ±ndakiler".
> 5. **`ekap_scraper` havuza baÄŸlanmasÄ±** â€” yol aÃ§Ä±k ama hÄ±z tavanÄ± ayarÄ± gerek
>    (ÅŸu an 8 paralel Ã— 2-3 istek â‰ˆ 20-60 istek/sn, havuz tavanÄ± 600/dk = 10/sn).
> 6. `stat-kazanim` sayÄ±/hedef evreni uyuÅŸmuyor (78K vs 1,39M).
> 7. Dashboard alt yarÄ±sÄ± mod-farkÄ±ndalÄ±ksÄ±z (`ilanlariYukle`, `sonGorulenlerYukle`,
>    `enIyiEslesmelerYukle`).
> 8. `satinalma_talepleri.olusturan_user_id` â€” `ozel-ihale-detay.html:265` ile BÄ°RLÄ°KTE
>    dÃ¼zeltilmeli, tek baÅŸÄ±na REVOKE sayfayÄ± kÄ±rar.
> 9. `ilanlar_sonuc` view'Ä±nÄ±n bozuk LEFT JOIN'i (`i.ekap_id = s.ekap_id` hiÃ§ eÅŸleÅŸmiyor).
> 10. **ÃœrÃ¼n kararÄ± bekliyor:** `kamu_ihaleleri.idare` misafire aÃ§Ä±k bÄ±rakÄ±ldÄ±
>     (`ozel-ihaleler.html` onu hem gÃ¶sterip hem aratÄ±yor). Politikaya uyum istenirse
>     REVOKE deÄŸil, sayfaya uyeMi dalÄ± + dar select.
> 11. **AÃ§Ä±k risk:** Webshare 100 IP'nin 100'Ã¼ tek `166.88.110.0/24` bloÄŸunda.
>     Paket bÃ¼yÃ¼tme gerekirse gerekÃ§e IP *sayÄ±sÄ±* deÄŸil **Ã§eÅŸitliliÄŸi**.
> 12. VDS'te Ã§ekirdek gÃ¼ncellemesi bekliyor (`System restart required`). Restart sonrasÄ±
>     **kong'u da yeniden baÅŸlat** (bayat upstream = 502).
>
> ## ğŸ—„ CANLI DAÄITIM DURUMU (20 Tem sonu, doÄŸrulandÄ±)
> Sonraki oturum "acaba uygulandÄ± mÄ±?" diye zaman kaybetmesin diye tek tek sorgulandÄ±:
>
> | Nesne | CanlÄ± |
> |---|---|
> | `idare_hiyerarsi` (87.528 dÃ¼ÄŸÃ¼m) | âœ… |
> | `idare_ata_torun` (312.259 satÄ±r) | âœ… |
> | `idare_hiyerarsi_sayim_mv` | âœ… |
> | `idare_agac_dallar/yol/ara/alt_agac_detsis` RPC | âœ… |
> | `idx_dt_ilanlari_kategori_tarih` | âœ… |
> | `idx_dt_ilanlari_tur_tarih` | âœ… (**20 Tem sonunda fark edildi â€” EKSÄ°KTÄ°**) |
| `dt_il_sayim` + `idx_dogrudan_temin_ilanlari_il` | âœ… (kanÄ±t aranÄ±yordu â€” **var**, mini harita fallback'te DEÄÄ°L) |
| `kredi_yukle_atomik` / `kupon_kullan_atomik` | âŒ **YOK â€” Ã¶deme atomikliÄŸi hiÃ§ uygulanmamÄ±ÅŸ** |
| `idx_ilanlar_analiz_tarihi` | âŒ yok |
| `idx_ilanlar_olusturulma` | âŒ yok (`migration_temizlik_20tem.sql` bekliyor) |

**20 Tem akÅŸam TAM NESNE DENETÄ°MÄ°:** 105 migration dosyasÄ±ndan 176 nesne Ã§Ä±karÄ±ldÄ±,
canlÄ± `pg_class`/`pg_proc` ile karÅŸÄ±laÅŸtÄ±rÄ±ldÄ± â†’ **165 var, 11 yok**. 11'in 8'i sahte
alarm (dosyalar bayat: `takip`â†’`takipler`, `bildirimler_*_idx`â†’`idx_bildirim_okunmamis`,
`idx_ilanlar_ai_kategori_kuyruk`â†’`_jenerik`). YukarÄ±daki 3'Ã¼ gerÃ§ek.
YÃ¶ntem tekrarlanabilir: migration'lardan `CREATE`'leri Ã§Ä±kar + canlÄ± katalogla diff'le.

**MASKELEME DENETÄ°MÄ° (anon curl, 20 Tem akÅŸam):** Ã§ekirdek saÄŸlam â€” `ilanlar.idare`,
`ilanlar_sonuc.idare`, DT kazanan, `dt_idare_ozet_mv`, `idare_hiyerarsi` hepsi 42501.
Yeni `idare_hiyerarsi` tablosu doÄŸru REVOKE edilmiÅŸ (ders uygulanmÄ±ÅŸ).
âš ï¸ **YENÄ° Ã–LÃ‡ÃœM TUZAÄI: HTTP 200 â‰  ifÅŸa.** `idare_tur` tablosu 200 dÃ¶ndÃ¼ ama RLS
satÄ±rlarÄ± kesip `[]` veriyor. GerÃ§ek test **dÃ¶nen veri**, durum kodu deÄŸil.
GerÃ§ekten veri sÄ±zdÄ±ran tek uÃ§: `satinalma_talepleri.olusturan_user_id`.

**DEPLOY MEKANÄ°ZMASI:** nginx frontend'i doÄŸrudan git checkout'undan servis ediyor
(`root /opt/ihale-platform`) â†’ **deploy = VDS'te `git pull`**. 20 Tem akÅŸam izlenen
HTML/JS dosyalarÄ±nda repoâ†”canlÄ± sapmasÄ± YOK.
>
> **DERS:** `migration_dt_index.sql`'i yazÄ±p komutu verdim ama uygulandÄ±ÄŸÄ±nÄ± hiÃ§
> DOÄRULAMADIM. Kategori indeksi oluÅŸmuÅŸ, tÃ¼r indeksi oluÅŸmamÄ±ÅŸtÄ± â€” DT'de tÃ¼r filtresi
> gÃ¼nlerce 38 saniye sÃ¼rdÃ¼. Elle kurulunca **38 sn â†’ 1,35 sn**.
> Kural: migration yazmak â‰  uygulanmÄ±ÅŸ olmak. `to_regclass`/`to_regprocedure` ile
> nesne bazÄ±nda teyit et, "komutu verdim" yeterli deÄŸil.
>
> ## ğŸ§¹ TEMÄ°ZLÄ°K
> - VDS'te bÄ±rakÄ±lan teÅŸhis dosyalarÄ± silindi: `backend/havuz_test.py`, `backend/detay_test.py`
> - **Paralel oturum Ã§akÄ±ÅŸmasÄ±:** `proxy_havuz.py`'deki baÄŸlantÄ±-sÄ±nÄ±rÄ± deÄŸiÅŸikliÄŸim,
>   paralel oturumun `e38ae4e fix(usul): stash Ã§atÄ±ÅŸmasÄ± Ã§Ã¶zÃ¼ldÃ¼` commit'inin iÃ§ine
>   karÄ±ÅŸtÄ±. Kod canlÄ±da ve doÄŸru, sadece commit atfÄ± yanlÄ±ÅŸ â€” geÃ§miÅŸ yeniden yazÄ±lmadÄ±
>   (push edilmiÅŸti, Ã¼stÃ¼ne inÅŸa edilmiÅŸ olabilir). Bkz. hafÄ±za `parallel-sessions-same-tree`.
>
> ## âš ï¸ Ã–LÃ‡ÃœM TUZAKLARI (bu oturumda 4 yanlÄ±ÅŸ teÅŸhise yol aÃ§tÄ±)
> - `kuyruk_say()` 1,49M satÄ±rda `count=exact` â†’ **ilk Ã§Ä±ktÄ± ~100 sn sonra**
> - Scraper 200'lÃ¼k partiler â†’ **parti baÅŸÄ±na ~260 sn**; 90 sn'lik pencere "0 ilerleme" gÃ¶sterir
> - Python Ã§Ä±ktÄ± tamponu â†’ `-u` olmadan log yanÄ±ltÄ±r
> - `olusturulma` yalnÄ±z YENÄ° satÄ±rda deÄŸiÅŸir; hafta sonu 0 ilan **normaldir**
> - SÃ¼reÃ§ baÅŸlatma: **`setsid --fork` ÅŸart**; `nohup setsid &` ssh kapanÄ±nca sessizce Ã¶lÃ¼r


> ## ğŸ”§ 20 TEMMUZ â€” PROXY TEÅHÄ°S TURU: 4 YANLIÅ TEÅHÄ°S, 3 GERÃ‡EK BULGU
> Webshare 402'si Ã§Ã¶zÃ¼ldÃ¼kten sonra backfill'ler yine yazmadÄ±. TeÅŸhis uzun sÃ¼rdÃ¼ ve
> bu turda **dÃ¶rt kez yanlÄ±ÅŸ yÃ¶ne saptÄ±m**; kayda geÃ§iyorum Ã§Ã¼nkÃ¼ desen tekrar edebilir.
>
> ### âœ… DOÄRULANAN (Ã¶lÃ§Ã¼mle)
> - Proxy'ler saÄŸlÄ±klÄ±: VDS'ten `curl -x` â†’ HTTP 200, 1,2 sn
> - Havuz saÄŸlÄ±klÄ±: VDS'te izole test `dtEnum` 5/5, `dtDetayGetir` gerÃ§ek token'larla 5/5
> - Scraper Ã§alÄ±ÅŸÄ±yor: bir parti iÅŸledi (+200 denendi, +203 sonuÃ§ yazÄ±ldÄ±)
> - Token scraper yazÄ±yor: 629.886 â†’ 630.063
>
> ### ğŸ”´ GERÃ‡EK BULGULAR
> 1. **EÅŸzamanlÄ± baÄŸlantÄ± bÃ¼tÃ§esi.** Ä°ki scraper aynÄ± anda koÅŸunca 2Ã—100 = **240 aÃ§Ä±k
>    soket** oldu ve istekler "read timeout" vermeye baÅŸladÄ±. Tek scraper koÅŸarken aynÄ±
>    proxy'ler 1,2 sn'de yanÄ±t veriyordu. â†’ `PROXY_AZAMI_UC=40` eklendi: havuz yine
>    100 IP'den karÄ±ÅŸÄ±k sÄ±rayla seÃ§er (rotasyon bozulmaz) ama aynÄ± anda en fazla 40
>    soket tutar. Ã–lÃ§Ã¼m: 240 â†’ 153.
> 2. **`setsid --fork` ÅART.** `nohup setsid ... &` ile baÅŸlatÄ±lan sÃ¼reÃ§ ssh kapanÄ±nca
>    **traceback bÄ±rakmadan** Ã¶lÃ¼yor. Bu tek baÅŸÄ±na iki yanlÄ±ÅŸ teÅŸhise yol aÃ§tÄ±.
> 3. **EKAP derin sayfalamada yavaÅŸlÄ±yor.** Token backfill'i sayfa ~4959-4961'de
>    Ä±srarla timeout alÄ±yor; erken sayfalar sorunsuzdu. Bizim tarafÄ±mÄ±z deÄŸil.
>
> ### âš ï¸ Ã–LÃ‡ÃœM TUZAKLARI (yanlÄ±ÅŸ teÅŸhislerin asÄ±l sebebi)
> - `kuyruk_say()` 1,49M satÄ±rda `count=exact` yapÄ±yor â†’ **ilk Ã§Ä±ktÄ± ~100 saniye** sonra
>   geliyor. Bu sÃ¼rede sÃ¼reÃ§ "uyuyor" gÃ¶rÃ¼nÃ¼yor ve log boÅŸ â€” "asÄ±ldÄ±" sanÄ±lÄ±yor.
> - Scraper 200'lÃ¼k partiler hÃ¢linde iÅŸaretliyor â†’ **parti baÅŸÄ±na ~260 saniye**.
>   90-100 saniyelik Ã¶lÃ§Ã¼m pencereleri bir partiyi bile kapsamÄ±yor, "0 ilerleme" gÃ¶steriyor.
> - Python Ã§Ä±ktÄ±yÄ± tamponluyor; `-u` olmadan log yanÄ±ltÄ±cÄ±.
> - `olusturulma` sadece YENÄ° satÄ±rlarda deÄŸiÅŸir; upsert'lerde donuk kalÄ±r. Hafta sonu
>   ilan yayÄ±mlanmadÄ±ÄŸÄ± iÃ§in "iki gÃ¼ndÃ¼r sÄ±fÄ±r" **normaldi** â€” gece hattÄ± hiÃ§ bozulmamÄ±ÅŸtÄ±.
>
> ### â­ AÃ‡IK
> - [x] ~~SÃ¼rdÃ¼rÃ¼lebilir verim Ã¶lÃ§Ã¼mÃ¼~~ â†’ 20 Tem akÅŸam durumu: `dt_token` sayfa 4966
>       duvarÄ±nda dÃ¶nÃ¼yordu (derin sayfalama, EKAP tarafÄ±) â†’ DURDURULDU, boÅŸa soket
>       yiyordu. `dt_kazanan` saÄŸlÄ±klÄ±ydÄ± (800 dt_no/~15dk) â†’ DETSÄ°S taramasÄ± iÃ§in
>       DURDURULDU, zincir sonunda otomatik yeniden baÅŸlar. `ekap_ihale_backfill`
>       sayfa=1000 ile ~0,1 istek/sn â€” soket yÃ¼kÃ¼ ihmal edilebilir, KOÅMAYA DEVAM
>       (2026â†’2010, toplam 1,96M; 20 Tem 12:15 itibarÄ±yla 2017'de, ~110 kayÄ±t/sn).
> - [ ] `ilan_metni_backfill` havuza baÄŸlandÄ± ama 402 dÃ¶neminden beri hiÃ§ koÅŸmadÄ±, teyit yok.
> - [x] EÅŸleÅŸtirme ara Ã§Ã¶zÃ¼mÃ¼ (`paginationTake=1` â†’ `300`) UYGULANDI â€” bkz. SIRADAKÄ°LER #1.
> - [ ] `ekap_scraper` hÃ¢lÃ¢ havuza baÄŸlÄ± deÄŸil (post() artÄ±k iki tipi de kabul ediyor,
>       yolu aÃ§Ä±k).


> # ğŸ“Œ OTURUM DEVRÄ° â€” 20 TEM (tek oturuma dÃ¶nÃ¼ÅŸ)
> KullanÄ±cÄ± paralel oturumlarÄ± kapatÄ±p tek oturuma dÃ¶nÃ¼yor. **Bu blok, daÄŸÄ±nÄ±k
> oturumlarÄ±n birleÅŸik durumudur â€” yeni oturum Ä°LK BUNU okusun.**
>
> ## ğŸŸ¢ ÅU AN CANLI DURUM (Ã¶lÃ§Ã¼ldÃ¼, tahmin deÄŸil)
> | | |
> |---|---|
> | `ilanlar` | **795.173** (backfill akÄ±yor, saatlik bÃ¼yÃ¼yor) |
> | `durum='aktif'` | 13.444 (sabit â€” dÃ¼zeltme tutuyor) |
> | gerÃ§ekten aÃ§Ä±k (`son_teklif_tarihi > now()`) | **4.676** |
> | `dogrudan_temin_ilanlari` | 1.490.644 |
> | VDS HEAD | `e2bdff4` (yerel = origin = VDS, senkron) |
>
> ## âš™ï¸ ÅU AN KOÅAN Ä°Å â€” DOKUNMA
> `ekap_ihale_backfill.py` â€” nohup, PID canlÄ±, **2018 yÄ±lÄ±nda %66**, ~112 kayÄ±t/sn.
> Kalan yÄ±llar: 2018 â†’ 2011. Checkpoint: `backend/ihale_backfill_checkpoint.json`
> (yÄ±l bazÄ±nda `skip`). Durdurup baÅŸlatmak gÃ¼venli, kaldÄ±ÄŸÄ± yerden devam eder.
> Log: `/opt/ihale-platform/logs/ihale_backfill.log`
>
> âš ï¸ **SSH ile baÅŸlatÄ±rken `nohup ... &` YETMEZ** â€” stdin yÃ¶nlendirilmezse ssh
> kanalÄ± kapanmaz ve yerel gÃ¶rev saatlerce "running" gÃ¶rÃ¼nÃ¼r (bu oturumda oldu).
> `ssh -f` veya `nohup ... </dev/null >log 2>&1 &` ya da `systemd-run` kullan.
>
> **BittiÄŸinde Ä°LK Ä°Å** â€” eÅŸleÅŸmeyen EKAP durum metinlerini oku:
> ```bash
> ssh ihale "grep -A25 'ESLESMEYEN DURUM METINLERI' /opt/ihale-platform/logs/ihale_backfill.log | tail -30"
> ssh ihale "docker exec -i supabase-db psql -U postgres -d postgres -c 'SELECT public.ilan_durum_bayatlat();'"
> ```
>
> ## âœ… BU OTURUMDA YAPILANLAR
>
> **DoÄŸrudan Temin (kullanÄ±cÄ±nÄ±n bildirdiÄŸi 5 hata) â€” hepsi canlÄ±da**
> - Haritadan `?il=` ile gelince **GÃ¼ncel** sekmesi aÃ§Ä±lÄ±yor (TÃ¼mÃ¼ deÄŸil)
> - Sekme sayaÃ§larÄ± **filtreye duyarlÄ±** (Ankara 96K â†’ 6K; imza cache'i: sekme
>   deÄŸiÅŸimi 0 sorgu, filtre deÄŸiÅŸimi 3)
> - Kartlar tÄ±klanabilir â†’ **yeni `dt-detay.html`** (stretched-link; maskeleme korundu)
> - Filtre paneli ihaleler.html Ã¶lÃ§Ã¼leriyle eÅŸlendi
> - SÄ±ralama etiketi dÃ¼zeltildi (*sÄ±ralama zaten vardÄ±, etiket yanlÄ±ÅŸtÄ±*)
> - `yayin_tarihi` etiketi: sonuÃ§lananlarda "SonuÃ§ duyurusu" (E8 o anki duyurunun tarihi)
>
> **Ä°haleler kategori filtresi (`fea35b3`)** â€” 48 seÃ§eneÄŸin **43'Ã¼ sÄ±fÄ±r kayÄ±t**
> dÃ¶ndÃ¼rÃ¼yordu (`<option>`larda `value` yoktu â†’ tarayÄ±cÄ± metni gÃ¶nderiyordu).
> `js/kategoriler.js`'ten runtime dolduruluyor; kanonik-dÄ±ÅŸÄ± deÄŸerler "(eski)"
> etiketiyle korunuyor (kayÄ±tlÄ± aramalar sessizce boÅŸalmasÄ±n).
>
> **GÃ¼venlik (`e9bc6e1`)** â€” `dogrudan_temin_ilanlari` Ã¼zerinde `authenticated`
> tablo-geneli SELECT'i vardÄ± â†’ her Ã¼ye `dt_ihale_token`/`dt_idare_token` Ã§ekebiliyordu.
> 18 kolon GRANT, 2 token kapalÄ±. `has_column_privilege` ile doÄŸrulandÄ± (`f | t`).
>
> **Analiz ekseni (`2556169`)** â€” `rekabet_ozet`+`kurum_ozet` trend ekseni
> `ilan_tarihi` (%4,27 dolu) â†’ `etkin_tarih`. 24 ay penceresinde **110.548 â†’ 185.408 (+%68)**.
> Etiketler "Trend" â†’ "Hareket" (335K kayÄ±tta bu SONUÃ‡ tarihi, "ilan trendi" demek yanlÄ±ÅŸtÄ±).
>
> **Sahte "aktif" ihaleler (`9d14ef6`, `790618c`)** â€” `durum='aktif'` **183.677 â†’ 13.444**.
> KÃ¶k neden `durum_donustur()`'un blanket `return "aktif"`i; artÄ±k tanÄ±nmayan durumda
> tarihten tÃ¼retiliyor. 178.906 satÄ±r bayatlatÄ±ldÄ±, MV tazelendi, backfill dÃ¼zeltilmiÅŸ
> kodla yeniden baÅŸlatÄ±ldÄ± ve kanÄ±tlandÄ± (yeni kayÄ±tlar `kapali` dÃ¼ÅŸÃ¼yor, `aktif` sabit).
>
> **Cron (`c021157`)** â€” `idare_tur_tazele()` + `lot_sayisi` gece iÅŸine baÄŸlandÄ±
> (ikisi de migration'da bir kez doldurulup unutulmuÅŸtu â†’ kapsam azalÄ±yordu).
>
> **Arama Commit 1 (`e2bdff4`)** â€” `js/api.js:98,111` tanÄ±msÄ±z `UI.bildirim_goster()`
> Ã§aÄŸÄ±rÄ±yordu (UI yalnÄ±z `js/ui.js`'te, api.js yÃ¼kleyen 6 sayfanÄ±n hiÃ§biri onu
> yÃ¼klemiyordu) â†’ **Ã§alÄ±ÅŸma anÄ±nda ReferenceError**. Somut zarar: firma-analiz'de
> 402 "kredi bitti" uyarÄ±sÄ± kullanÄ±cÄ±ya hiÃ§ ulaÅŸmÄ±yor, yerine catch dalÄ± yanÄ±ltÄ±cÄ±
> "Bu Ã¶zellik yakÄ±nda aktif olacak" gÃ¶steriyordu. BaÄŸÄ±msÄ±z `bildirimGoster()` eklendi.
> **7 Ã¶lÃ¼ dosya silindi** (1.164 satÄ±r) â€” 4 mercekten doÄŸrulandÄ±, Ã§eliÅŸki yok;
> `git log -S` gÃ¶sterdi ki HTML'den kaldÄ±rÄ±lmamÄ±ÅŸlar, HÄ°Ã‡ eklenmemiÅŸler.
> Ä°ki tuzak yakalandÄ±: (a) sÄ±nÄ±f adÄ± `toast` olsaydÄ± iki sayfanÄ±n kendi
> `.toast{opacity:0}` kuralÄ± mesajÄ± **gÃ¶rÃ¼nmez** yapardÄ± â†’ `ig-api-toast`;
> (b) giriÅŸ animasyonu `requestAnimationFrame`'e baÄŸlÄ±ydÄ±, arka plan sekmesinde
> askÄ±ya alÄ±nÄ±p bildirim opacity:0'da takÄ±lÄ±yordu â†’ animasyon kaldÄ±rÄ±ldÄ±.
> `api.js?v=goog1 â†’ ?v=bldr1` (6 sayfa) â€” bumplanmasa dÃ¼zeltme Ã¶nbellek yÃ¼zÃ¼nden
> kullanÄ±cÄ±ya ULAÅMAZDI, yerel testte bizzat yaÅŸandÄ±.
>
> ## ğŸ”œ SIRADAKÄ° Ä°Å â€” kuyruk (gerekÃ§eli sÄ±ra)
> Detaylar iÃ§in aÅŸaÄŸÄ±daki **"Ä°KÄ°NCÄ° TUR KARARLARI"** bloÄŸuna bak; her madde
> dosya/satÄ±r seviyesinde oturtuldu ve adversaryal doÄŸrulamadan geÃ§ti.
> | # | Ä°ÅŸ | Not |
> |---|---|---|
> | ~~1~~ | ~~**Arama Commit 1**~~ | âœ… **YAPILDI** (`e2bdff4`) â€” yukarÄ± bak |
> | 2 | **RFQ kÃ¶prÃ¼sÃ¼** | 16 Tem kararÄ± BOZULMAYACAK; e-SatÄ±nalma â†’ `harita?katman=rfq` linki + rozet + bayatlama filtresi. âš ï¸ Ã‡Ä±plak `>= now()` YAZMA (kolon nullable). |
> | 3 | **Analiz Faz A** | Parasal kartlara "yalnÄ±z ihaleler" rozeti + payda. DT parasal birleÅŸtirme **REDDEDÄ°LDÄ°** (kapsama %5,24 + `yaklasik_maliyet` kolonu YOK). |
> | 4 | **Arama Commit 2** | `ihaleler.html`'in 3 handler'sÄ±z alanÄ±. Ã–nce ILIKE gecikmesini Ã¶lÃ§. |
> | 5 | **Ä°dare aÄŸacÄ±** | **Proxy'siz baÅŸlanabilir** â€” loader EKAP'a hiÃ§ istek atmÄ±yor. âš ï¸ AdÄ±m 1 ve 2 aynÄ± iÅŸlemde: `--kapanis` + `REFRESH ... idare_hiyerarsi_sayim_mv` (yoksa boÅŸ aÄŸaÃ§ render eder). |
> | 6 | **Ticaret** | CanlÄ± tabloya PK takasÄ± YAPMA â†’ ayrÄ± `dis_ticaret_dunya` tablosu. |
> | 7 | **Analiz Faz B** | `ihale_butce_mv` (`ilan_id` DISTINCT). âš ï¸ `ihale_sonuclari.yaklasik_maliyet` kÄ±sÄ±m bazlÄ± deÄŸil, SUM 35x ÅŸiÅŸiyor. |
>
> ## â“ SENÄ°N KARARINI BEKLEYENLER (veriyle Ã§Ã¶zÃ¼lemeyen 5 madde)
> 1. **"TÃ¼mÃ¼" varsayÄ±lan mÄ±?** DT (1,49M) ihaleyi (555K) ~3:1 eziyor â†’ varsayÄ±lan
>    "TÃ¼mÃ¼" olursa kÄ±rÄ±lÄ±m grafikleri fiilen DT grafiÄŸine dÃ¶ner.
> 2. **"TÃ¼mÃ¼"de ortak tarih penceresi?** DT pratikte 2025-26, ihale 2011'e uzanÄ±yor.
> 3. **RFQ'lar `ihaleler.html`'de de gÃ¶rÃ¼nsÃ¼n mÃ¼?** (kamu ilanÄ± + Ã¶zel RFQ tek listede)
> 4. **RFQ bayatlatma: RPC filtresi mi, cron adÄ±mÄ± mÄ±?** Ä°kincisi daha doÄŸru, prod cron deÄŸiÅŸikliÄŸi.
> 5. **Ticaret "her Ã¼lke" ne demek?** (a) her Ã¼lke Ã— DÃœNYA â€” planlanan; (b) tam ikili
>    matris â‰ˆ 4,8 milyar satÄ±r, uygulanamaz.
>
> ## âš ï¸ TEK OTURUMA DÃ–NERKEN â€” TEMÄ°ZLÄ°K
> - **3 worktree aÃ§Ä±k**: `.claude/worktrees/` altÄ±nda `awesome-jang`, `brave-knuth`,
>   `great-blackburn`. `git worktree list` ile gÃ¶r, gereksizleri `git worktree remove`.
> - **1 stash var**: `stash@{0} "onceki oturumdan kalan yerel degisiklikler"` â€”
>   baÅŸka bir oturumun `usul_donustur` i18n iÅŸi. Ä°Ã§eriÄŸine bak, gerekmiyorsa `git stash drop`.
> - BugÃ¼n **iki kez** paralel oturum Ã§akÄ±ÅŸmasÄ± yaÅŸandÄ± (biri `ekap_scraper.py`'de merge
>   conflict, biri commit'in baÅŸka oturuma sÃ¼pÃ¼rÃ¼lmesi). Tek oturuma dÃ¶nmek doÄŸru karar.
>
> ## ğŸ§­ BU OTURUMUN Ä°KÄ° DERSÄ° (tekrarlanmasÄ±n)
> 1. **Bayat migration dosyasÄ± okumak canlÄ±yÄ± bozdu.** `migration_uygun_firmalar_v3_1.sql`
>    `'kapandi'` diyor ama `v3_3` onu `'kapali'`ya dÃ¼zeltmiÅŸ; ben v3_1'e dayanÄ±nca
>    CHECK constraint reddetti ve backfill Ã§Ã¶ktÃ¼. **Migration okurken aynÄ± nesnenin daha
>    yeni sÃ¼rÃ¼mÃ¼ var mÄ± diye bak; canlÄ± tanÄ±mÄ± `pg_proc`'tan doÄŸrula.**
> 2. **Adversaryal doÄŸrulama iki kez canlÄ± hatayÄ± Ã¶nledi.** `kpi.aktif`'i
>    `durum='aktif'`e Ã§evirecektim â†’ 34x ÅŸiÅŸerdi. Ticaret'te canlÄ± tabloya PK takasÄ±
>    Ã¶nerilmiÅŸti â†’ sessiz veri kaybÄ±. Riskli deÄŸiÅŸikliklerde "Ã§Ã¼rÃ¼t" turu ÅŸart.

> ## âœ… 20 TEM â€” Ã‡Ã–ZÃœLDÃœ: SAHTE "AKTÄ°F" Ä°HALELER (kÃ¶k neden + temizlik + doÄŸrulama)
> **SonuÃ§:** `durum='aktif'` **183.677 â†’ 13.444**; gerÃ§ekten aÃ§Ä±k 4.765.
> Bayatlatma 178.906 satÄ±r kapattÄ±, `idare_ozet_mv` tazelendi.
> KÃ¶k neden dÃ¼zeltildi (`durum_donustur`, commit `9d14ef6`+`790618c`), backfill
> dÃ¼zeltilmiÅŸ kodla yeniden baÅŸlatÄ±ldÄ± ve **kanÄ±tlandÄ±**: yeni kayÄ±tlar `kapali`
> olarak dÃ¼ÅŸÃ¼yor (190.564 â†’ 193.301), `aktif` sabit kalÄ±yor (13.444).
>
> ### KÃ¶k neden â€” `ekap_scraper.py durum_donustur()`
> EÅŸleÅŸmeyen HER EKAP durum metni `return "aktif"` ile aktif sayÄ±lÄ±yordu.
> `ekap_ihale_backfill.py` bunu 1,6M geÃ§miÅŸ ihalede Ã§aÄŸÄ±rÄ±yordu.
> **DÃ¼zeltme kÃ¶rlemesine `"kapali"` DEÄÄ°L** â€” canlÄ± scraper aynÄ± fonksiyonu
> kullanÄ±yor, tanÄ±nmayan bir metin gerÃ§ek aktif ihaleyi gizlerdi. ArtÄ±k tarihten
> tÃ¼retiliyor: tanÄ±nmayan + geÃ§miÅŸ â†’ `kapali`, tanÄ±nmayan + gelecek â†’ `aktif`,
> tarih yok â†’ eski davranÄ±ÅŸ. TanÄ±nan metinler HÄ°Ã‡ deÄŸiÅŸmedi. Test 14/14.
>
> ### âš ï¸ BENÄ°M HATAM â€” 2 saatlik backfill kesintisi
> Ä°lk dÃ¼zeltmede `'kapandi'` dÃ¶ndÃ¼rdÃ¼m. `ilanlar_durum_check` yalnÄ±z
> `('taslak','aktif','kapali','iptal','sonuclandi')` kabul ediyor â†’
> PostgREST **400** â†’ backfill 2021'de Ã§Ã¶ktÃ¼. Sebep: `migration_uygun_firmalar_v3_1.sql`
> dosyasÄ±nÄ± okudum, orada `'kapandi'` yazÄ±yor â€” ama **v3_3 bunu zaten dÃ¼zeltmiÅŸ**
> ("Bayatlama 'kapandi' deÄŸil 'kapali' yazmalÄ± â€” v3.1'deki ERROR'un dÃ¼zeltmesi").
> **DERS: migration dosyasÄ± okurken aynÄ± nesnenin daha yeni sÃ¼rÃ¼mÃ¼ var mÄ± diye bak;
> canlÄ± tanÄ±mÄ± `pg_proc`'tan doÄŸrula.** Koda uyarÄ± dÃ¼ÅŸÃ¼ldÃ¼.
>
> ### ğŸ”µ AÃ‡IK â€” eÅŸleme kanÄ±tla tamamlanacak
> EKAP'Ä±n geÃ§miÅŸ ihaleler iÃ§in hangi durum metinlerini dÃ¶ndÃ¼rdÃ¼ÄŸÃ¼nÃ¼ hÃ¢lÃ¢
> BÄ°LMÄ°YORUZ. `BILINMEYEN_DURUMLAR` sayacÄ± + `bilinmeyen_durum_raporu()` eklendi;
> backfill turu bitince eÅŸleÅŸmeyen metinleri sÄ±klÄ±kla yazdÄ±racak:
> ```bash
> ssh ihale "grep -A25 'ESLESMEYEN DURUM METINLERI' /opt/ihale-platform/logs/ihale_backfill.log | tail -30"
> ```
> O Ã§Ä±ktÄ± gÃ¶rÃ¼lÃ¼nce `durum_donustur` eÅŸlemesi tamamlanmalÄ± (`iptal` sabiti
> constraint'te VAR ama hiÃ§bir arayÃ¼z onu beklemiyor â€” eklenirse o kayÄ±tlar tÃ¼m
> sekmelerden sessizce dÃ¼ÅŸer, Ã¶nce arayÃ¼z hazÄ±rlanmalÄ±).
>
> <details><summary>Orijinal hata kaydÄ± (referans)</summary>
>
> ## ğŸ”´ 20 TEM â€” CANLI HATA: 163.464 GEÃ‡MÄ°Å Ä°HALE "AKTÄ°F" GÃ–RÃœNÃœYOR
> P0.3 migration'Ä± uygulanÄ±rken ortaya Ã§Ä±ktÄ± (migration'Ä±n kendisi saÄŸlam, bu AYRI bir hata).
>
> ### Ã–lÃ§Ã¼m (canlÄ±, backfill akarken â€” rakamlar bÃ¼yÃ¼yor)
> | | |
> |---|---|
> | `durum='aktif'` diyor | **168.322** |
> | â”” son teklif tarihi GEÃ‡MÄ°Å | **163.464** â† yanlÄ±ÅŸ |
> | â”” gerÃ§ekten aÃ§Ä±k | 4.856 |
> | â”” tarihi BOÅ (asla kapanmaz) | 2 |
> | `kapandi` | **0** |
>
> ### KÃ¶k neden â€” Ä°KÄ° parÃ§a
> **1) `ekap_scraper.py:675 durum_donustur()` varsayÄ±lanÄ± "aktif":**
> ```python
> if "aÃ§Ä±k" in d or "devam" in d or "katÄ±lÄ±m" in d: return "aktif"
> if "sonuÃ§land" in d or "tamamland" in d: return "sonuclandi"
> return "aktif"        # â† eÅŸleÅŸmeyen HER durum aktif sayÄ±lÄ±yor
> ```
> `ekap_ihale_backfill.py:142` bunu 1,6M geÃ§miÅŸ kayÄ±tta Ã§aÄŸÄ±rÄ±yor. EKAP'Ä±n
> geÃ§miÅŸ ihaleler iÃ§in dÃ¶ndÃ¼rdÃ¼ÄŸÃ¼ durum metinleri bu iki kalÄ±ba uymuyor â†’
> 2011 tarihli ihale "aktif" yazÄ±lÄ±yor. **GerÃ§ek metinlerin ne olduÄŸunu BÄ°LMÄ°YORUZ**
> (loglanmÄ±yor) â€” bu yÃ¼zden eÅŸlemeyi tahminle geniÅŸletmek YANLIÅ olur.
>
> **2) `ilan_durum_bayatlat()` (migration_uygun_firmalar_v3_1.sql:119)** yalnÄ±z
> `son_teklif_tarihi IS NOT NULL` olanlarÄ± kapatÄ±yor â†’ tarihi olmayan kayÄ±t
> sonsuza dek 'aktif' kalÄ±r. Åu an bu yalnÄ±z **2 kayÄ±t**, ihmal edilebilir.
>
> ### Etkilenen yÃ¼zeyler
> `durum='aktif'` sayan her yer: `idare_ozet_mv` (idareler dizinindeki "aktif"
> sÃ¼tunu), `kurum_ozet`'in `durum` kÄ±rÄ±lÄ±m grafiÄŸi.
> âœ… ETKÄ°LENMEYEN: `kurum_ozet.kpi.aktif` ve `il_sayim_aktif()` â€” ikisi de tarih
> tabanlÄ±, doÄŸru 4.856 gÃ¶steriyorlar. (P0.3'te kpi.aktif'i `durum='aktif'`e
> Ã§evirecektim, adversaryal doÄŸrulama bunu Ã§Ã¼rÃ¼ttÃ¼ â€” Ã§evirseydik 34x ÅŸiÅŸerdi.)
>
> ### Ã‡Ã–ZÃœM â€” sÄ±rayla
> **a) ÅÄ°MDÄ° (gÃ¼venli, kalÄ±cÄ±):** backfill upsert'i `resolution=ignore-duplicates`
> kullanÄ±yor, yani mevcut satÄ±rlarÄ± EZMÄ°YOR â†’ bayatlatmanÄ±n kapattÄ±ÄŸÄ± satÄ±rlar
> geri aÃ§Ä±lmaz. 163.464 kaydÄ± dÃ¼zeltir:
> ```bash
> docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.ilan_durum_bayatlat() AS kapatilan;"
> docker exec -i supabase-db psql -U postgres -d postgres -c "REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_ozet_mv;"
> ```
> **b) BACKFILL BÄ°TÄ°NCE tekrar koÅŸtur** â€” yeni gelen satÄ±rlar yine 'aktif' olarak
> dÃ¼ÅŸÃ¼yor. (Gece cron'u zaten Ã§aÄŸÄ±rÄ±yor; backfill gece de sÃ¼rÃ¼yorsa sabah tekrar.)
>
> **c) KALICI (ayrÄ± iÅŸ, Ã–NCE VERÄ° TOPLA):** `durum_donustur`'un blanket
> `return "aktif"`i toplu geÃ§miÅŸ yÃ¼klemede yanlÄ±ÅŸ yÃ¶nde hata veriyor â€”
> "fÄ±rsat var" demek, "yok" demekten daha zararlÄ±. AMA varsayÄ±lanÄ± kÃ¶rlemesine
> `"kapandi"` yapmak da riskli: canlÄ± scraper aynÄ± fonksiyonu kullanÄ±yor, tanÄ±nmayan
> bir durum metni gerÃ§ek aktif ihaleyi gizler.
> **DoÄŸru sÄ±ra:** Ã¶nce `ihaleDurumAciklama`'nÄ±n eÅŸleÅŸmeyen deÄŸerlerini LOGLA
> (backfill'e birkaÃ§ satÄ±r), gerÃ§ek metinleri gÃ¶r, sonra eÅŸlemeyi tamamla.
> Tahminle geniÅŸletme.
>
> </details>

> ## âœ… 20 TEM â€” PROXY Ã‡ALIÅIYOR, BLOKE Ä°ÅLER SERBEST
> KullanÄ±cÄ± teyit etti. AÅŸaÄŸÄ±daki Ã¼Ã§ iÅŸ 402 yÃ¼zÃ¼nden duruyordu; komutlar hazÄ±r.
> **Hepsi uzun sÃ¼rer â†’ `systemd-run` ile arka planda baÅŸlat, cron ile Ã‡AKIÅTIRMA**
> (gece turu 03:00; `PROXY_KURESEL_RPM` sÃ¼reÃ§ baÅŸÄ±na uygulanÄ±yor, iki sÃ¼reÃ§ toplam
> yÃ¼kÃ¼ iki katÄ±na Ã§Ä±karÄ±r â€” bkz. 18 Tem notu).
>
> ### 1) DT geÃ§miÅŸ yÄ±llar â€” `yayin_tarihi` hÃ¢lÃ¢ kayÄ±tlarÄ±n ~%1'inde dolu
> ```bash
> ssh ihale
> cd /opt/ihale-platform/backend
> systemctl reset-failed dt-yayin 2>/dev/null
> systemd-run --unit=dt-yayin --working-directory=/opt/ihale-platform/backend \
>   /opt/ihale-platform/backend/venv/bin/python ekap_dogrudan_temin_scraper.py \
>   --backfill --max-pages 12000
> # Ä°lerleme:  journalctl -u dt-yayin -f
> # Checkpoint'ten devam eder (--reset KOYMA, yoksa baÅŸtan tarar).
> ```
>
> ### 2) DETSÄ°S tam tarama â€” idare hiyerarÅŸisi SAYAÃ‡LARININ Ã¶n koÅŸulu
> ```bash
> systemd-run --unit=detsis-tara --working-directory=/opt/ihale-platform/backend \
>   /opt/ihale-platform/backend/venv/bin/python ekap_detsis_cek.py --tara --devam
> # Bitince:  venv/bin/python ekap_detsis_cek.py --yaz
> # 85.062 istek â€” uzun sÃ¼rer. --devam checkpoint'ten devam eder.
> ```
> âš ï¸ `--yaz` BÄ°TMEDEN `ilan_detsis_esle()` Ã§aÄŸÄ±rma (boÅŸ `detsis_no` Ã¼zerinde 1,85M
> satÄ±r boÅŸuna dÃ¶ner). SÄ±ra: `--tara` â†’ `--yaz` â†’ `ilan_detsis_esle()` â†’
> `REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_hiyerarsi_sayim_mv;`
>
> ### 3) 1,6M geÃ§miÅŸ ihale backfill â€” Ã–NCE DOÄRULAMA gerekiyor
> DÃ¼z sayfalama 1,9M kayÄ±tta Ã§Ã¶kÃ¼yor; plan **81 il Ã— 4 tÃ¼r = 324 dilim**.
> BaÅŸlatmadan Ã¶nce `ihaleIlIdList` + `ihaleTuruIdList` alanlarÄ±nÄ±n gerÃ§ekten
> filtrelediÄŸini **0 < sonuÃ§ < toplam** Ã¶lÃ§Ã¼tÃ¼yle doÄŸrula.
> âš ï¸ "0 sonuÃ§ = filtre Ã§alÄ±ÅŸtÄ±" tuzaÄŸÄ± â€” bkz. `ekap-detsis-idare-tur` hafÄ±za notu.
>
> **Not:** Ä°dare aÄŸacÄ± ARAYÃœZ iÅŸi bu Ã¼Ã§Ã¼nÃ¼ BEKLEMEZ â€” `idare_hiyerarsi_yukle.py`
> EKAP'a hiÃ§ istek atmÄ±yor, aÄŸaÃ§ 15,42 MB olarak diskte hazÄ±r (bkz. Ä°kinci Tur, madde 5).

> ## ğŸ” 20 TEM â€” OTURUM DEVRÄ° (paralel oturum kapatÄ±ldÄ±, tek kuyruÄŸa dÃ¶nÃ¼lÃ¼yor)
> Bu blok, ikinci bir oturumun yaptÄ±klarÄ±nÄ± ve bÄ±raktÄ±ÄŸÄ± iÅŸleri devreder.
> âš ï¸ Ä°ki oturum aynÄ± aÄŸaÃ§ta Ã§alÄ±ÅŸtÄ±: `ekap_scraper.py`, `ekap_ihale_backfill.py`
> ve bu dosya iki taraftan dÃ¼zenlendi. Bundan sonra TEK kuyruk.
>
> ### âŒ BU OTURUMUN AÃ‡TIÄI HATA (Ã¼stteki ğŸ”´ P0'Ä±n kaynaÄŸÄ±)
> `ekap_ihale_backfill.py`'yi yazarken `durum_donustur()`'un Ã§Ä±ktÄ±sÄ±nÄ±
> DOÄRULAMADAN kullandÄ±m â†’ blanket `return "aktif"` 1,6M geÃ§miÅŸ kayda uygulandÄ±,
> **163.464 sahte "aktif"** Ã¼retti. DiÄŸer oturum yakalayÄ±p dÃ¼zeltti (`9d14ef6`,
> `790618c`). Ders: aynÄ± gÃ¼n `Accept-Language`'Ä± Ã¶lÃ§erek yakalamÄ±ÅŸtÄ±m; `durum`
> alanÄ±na aynÄ± titizliÄŸi gÃ¶stermedim. **Yeni bir alan haritalarken dÃ¶nÃ¼ÅŸtÃ¼rÃ¼cÃ¼nÃ¼n
> Ã§Ä±ktÄ±sÄ±nÄ± canlÄ± Ã¶rnekle doÄŸrula â€” imzasÄ±na gÃ¼venme.**
>
> ### âœ… TAMAMLANANLAR
> | iÅŸ | sonuÃ§ |
> |---|---|
> | `etkin_tarih` arayÃ¼z entegrasyonu | GeÃ§miÅŸ sekmesi 11.712 â†’ **346.926** |
> | Ä°dare tÃ¼rÃ¼ kural motoru (5 hata) | 1.832.259 satÄ±r sÄ±nÄ±flÄ±, kalan %0,84 |
> | `Accept-Language` eksikliÄŸi | 6 scraper'da dÃ¼zeltildi (aÅŸaÄŸÄ±da detay) |
> | Anasayfa bÃ¼tÃ§e KPI'si | 1000 satÄ±rda kesiliyordu â†’ **25,0 â†’ 88,9 milyar TL** |
> | GeÃ§miÅŸ sekmesinde Ã¶lÃ¼ filtreler | `esik_katsayi` gizlendi, bedel/OKAS uyarÄ± |
> | `ekap_ihale_backfill.py` | yazÄ±ldÄ±, koÅŸuyor (2026-2023 tamam) |
>
> ### ğŸ”¬ Ã–LÃ‡ÃœLEN API GERÃ‡EKLERÄ° (tahmin deÄŸil â€” tekrar Ã¶lÃ§me)
> **Ä°hale listesi (`GetListByParameters`):**
> - Derin sayfalama Ã‡Ã–KMÃœYOR: `paginationSkip=1.900.000` â†’ 2,4sn. *("dÃ¼z sayfalama
>   1,9M'de Ã§Ã¶ker" varsayÄ±mÄ±m YANLIÅTI â€” bÃ¶lÃ¼mleme mimarisi gereksizmiÅŸ.)*
> - `paginationTake` 5000'e kadar Ã§alÄ±ÅŸÄ±yor (5000 kayÄ±t / 18,8sn / 4,44 MB)
> - SÄ±ralama tarih azalan: skip=0 â†’ 2026, skip=1,9M â†’ 2011
> - `iknYili` **TEKÄ°L int** yÄ±l filtresi Ã§alÄ±ÅŸÄ±yor; `iknYilList`/`iknYilIdList`/
>   `yilList` YOK SAYILIYOR (toplam dÃ¶ndÃ¼rÃ¼rler)
> - KayÄ±t baÅŸÄ±na ~1,01 KB â†’ 1.958.053 kayÄ±t â‰ˆ **1,88 GB**
> - `ihaleIlIdList=[6]` â†’ 0 dÃ¶ndÃ¼; ID doÄŸrulanmadÄ±, il bÃ¶lÃ¼mlemesi KULLANILMADI
>
> **âš ï¸ `Accept-Language: tr-TR` ÅART.** Yoksa EKAP aÃ§Ä±klama alanlarÄ±nÄ± Ã§evirmeden
> dÃ¶ndÃ¼rÃ¼r: `usul='TENDER_SEARCH.MAIN.PAGEITEM.TENDER_TYPE TENDER_SEARCH.ENUM'`,
> `durum='Tender Canceled'`. CanlÄ± etkisi: `ilanlar.usul`'de **1.297 satÄ±r** ham
> i18n anahtarÄ±yla yazÄ±lmÄ±ÅŸ. YALNIZ bu baÅŸlÄ±k iÅŸe yarÄ±yor â€” `lang`, `culture`,
> `X-Culture` denendi, hiÃ§biri etkilemiyor.
>
> **DT listesi (`dtAra`):**
> - Ham yanÄ±ttaki `sp = 69788` alanÄ± **sayfa sayÄ±sÄ± DEÄÄ°L** (40.000. sayfa boÅŸ).
>   Ne olduÄŸu bilinmiyor â€” bu alandan Ã§Ä±karÄ±m YAPMA.
> - Liste sonu: 20.000 dolu (28.03.2024), 25.000 ve 30.000 boÅŸ â†’
>   **son 20.000-25.000 arasÄ± â‰ˆ 2,6-3,2M kayÄ±t**
> - Bizde 1.490.644 â†’ kapsam **%47-58**, eksik ~1-1,7M
> - Sayfa 4942 / 8000 / 11000 sondajÄ±: **%100 zaten bizde**. Yani
>   `.dt_scraper_checkpoint.json` (4952) kapsamÄ±mÄ±zÄ±n GERÄ°SÄ°NDE â€”
>   `--backfill` oradan koÅŸarsa saatlerce hiÃ§bir ÅŸey eklemez.
> - Derin sayfalar Ã§ok yavaÅŸ: 12.000/13.000/15.000 zaman aÅŸÄ±mÄ±na uÄŸradÄ±
>
> ### ğŸ“‹ DEVREDÄ°LEN Ä°ÅLER
> - [ ] **DT checkpoint'i doÄŸru yere al.** KapsamÄ±mÄ±z â‰ˆ sayfa 11.646'ya kadar.
>       Yeni verinin baÅŸladÄ±ÄŸÄ± sayfayÄ± 11.600-12.500 aralÄ±ÄŸÄ±nda sondajla bul,
>       `.dt_scraper_checkpoint.json`'Ä± oraya yaz, sonra `--backfill` koÅŸ.
>       âš ï¸ Åu anki 4952 deÄŸeriyle koÅŸmak KAYNAK Ä°SRAFI.
> - [ ] **DT scraper loglamasÄ± yanÄ±ltÄ±cÄ±** â€” "128 kayÄ±t upsert edildi" diyor ama
>       kaÃ§Ä±nÄ±n YENÄ° olduÄŸunu sÃ¶ylemiyor. BugÃ¼n 17 sayfa boyunca hiÃ§bir ÅŸey
>       eklemeden "baÅŸarÄ±lÄ±" gÃ¶rÃ¼ndÃ¼. `Prefer: return=representation` veya
>       Ã¶ncesi/sonrasÄ± sayÄ±mla "X yeni / Y gÃ¼ncellendi" ayrÄ±mÄ± ekle.
> - [ ] **Ä°hale backfill bitince: yeni idare adlarÄ±.** 1,6M kayÄ±t binlerce yeni
>       idare adÄ± getiriyor, eÅŸleme tablosunda yoklar â†’ `idare_tur` NULL kalÄ±r.
>       ```bash
>       python idare_tur_kural_backfill.py --detsis-yeniden --tazele-atla
>       # sonra psql ile: SELECT public.idare_tur_tazele();   (~10 dk)
>       ```
> - [ ] **Kirlenen 1.297 `usul` satÄ±rÄ±** â€” `Accept-Language` dÃ¼zeldiÄŸine gÃ¶re
>       yeniden Ã§ekilebilir veya NULL'lanabilir.
> - [ ] **`ekap_ihale_backfill.py` sayfa boyutu** ÅŸu an 1000 (~145 kayÄ±t/sn).
>       5000 de Ã§alÄ±ÅŸÄ±yor ve toplam istek sayÄ±sÄ±nÄ± 1958 â†’ 392'ye dÃ¼ÅŸÃ¼rÃ¼r;
>       hÄ±z benzer, istek sayÄ±sÄ± 5 kat az. Sonraki turda deÄŸerlendirilebilir.
>
> ### âš ï¸ TEKRARLAYAN OPERASYON TUZAKLARI (bu oturumda 3 kez dÃ¼ÅŸÃ¼ldÃ¼)
> - `pgrep -f '<script>'` / `pkill -f '<script>'` **kendi komut satÄ±rÄ±nla eÅŸleÅŸir**
>   â†’ sÃ¼reÃ§ bitse de "Ã§alÄ±ÅŸÄ±yor" sanÄ±rsÄ±n; `pkill` SSH oturumunu dÃ¼ÅŸÃ¼rÃ¼r.
>   Kullan: `ps -eo cmd | grep -c '[p]ython x'`
> - Uzun Ã§Ä±ktÄ±yÄ± `| tail -N` ile borulamak Ã§Ä±ktÄ±yÄ± TAMPONLAR â€” iÅŸ bitene kadar
>   hiÃ§bir ÅŸey gÃ¶rÃ¼nmez. Ä°lerleme izlenecekse boruyu kaldÄ±r.
> - Arka plan Python'da `python -u` kullan, yoksa TTY olmayan Ã§Ä±ktÄ± tamponlanÄ±r
>   (DT scraper 6 dakika "sessiz" gÃ¶rÃ¼ndÃ¼, aslÄ±nda Ã§alÄ±ÅŸÄ±yordu).

> ## âœ… 20 TEM â€” Ä°DARE TÃœRÃœ: 813K SINIFSIZ SATIR KURALLA KAPATILDI (AI'sÄ±z)
> **Ã–lÃ§Ã¼len durum:** ilanlar 241.508 (%68) + DT 571.424 (%38) = **812.932 satÄ±r**
> `idare_tur IS NULL`. Sebep ad yokluÄŸu DEÄÄ°L â€” 241.508'in yalnÄ±z **1**'inde ad boÅŸ.
>
> **KÃ¶k neden:** `idare_tur` tablosu SADECE DETSÄ°S'ten dolduruldu (28.566 kayÄ±t) ve
> `idare_tur_tazele()` TAM EÅÄ°TLÄ°K ile join ediyor:
> `WHERE t.idare_norm = public.idare_normalize(i.idare)`. DETSÄ°S'te olmayan ad
> eÅŸleÅŸemez â€” **belediye ÅŸirketleri (A.Å./Ltd.Åti.) DETSÄ°S'te zaten YOK**, onlar
> devlet organizasyonu deÄŸil sermaye ÅŸirketi.
>
> `migration_idare_tur.sql` bunu Ã¶ngÃ¶rmÃ¼ÅŸtÃ¼: `kaynak` kolonunda `'kural'` hazÄ±r
> duruyordu ("BoÅŸluk asla sÄ±nÄ±fsÄ±z kalmaz: kural/AI ile GEÃ‡Ä°CÄ° sÄ±nÄ±flanÄ±r").
>
> ### Kural motorunda bulunan 3 GERÃ‡EK hata (Ã¶lÃ§Ã¼lerek)
> 1. **SÃ¶zcÃ¼k sÄ±nÄ±rÄ± yok** â€” `_eslesir()` ham alt-dize arÄ±yordu:
>    `'a s'` â†’ "satÄ±n **ALMA S**ube" iÃ§inde eÅŸleÅŸti â†’ `belediye_sirket`
>    (ONCELIK'te BÄ°RÄ°NCÄ° olduÄŸu iÃ§in gÃ¼Ã§lÃ¼ kalÄ±ba dÃ¼ÅŸmeyen HER adÄ± Ã§alÄ±yordu;
>    "ankara su" bile eÅŸleÅŸir). `'il mudurlugu'` â†’ "s**Ä°CÄ°L MÃœDÃœRLÃœÄÃœ**".
>    Kod zaten `_KISALTMA_TUZAK` iÃ§in `\b` kullanÄ±yordu â†’ tÃ¼mÃ¼ne yayÄ±ldÄ±.
> 2. **TaÅŸra eki merkezi ezmeli** â€” "KARAYOLLARI GM **5. BÃ–LGE MÃœDÃœRLÃœÄÃœ**" â†’
>    `bakanlik_merkez` idi. TaÅŸranÄ±n karÅŸÄ±lÄ±ÄŸÄ± `'karayollari n bolge mudurlugu'`,
>    literal "n" yer tutucusu â€” "5" ile asla eÅŸleÅŸmez. `_tasra_ezmesi()` eklendi.
>    âš ï¸ KÄ°T'e UYGULANMAZ (TCDD 3. BÃ¶lge hÃ¢lÃ¢ KÄ°T'tir).
> 3. **Ãœst kurum zinciri anahtar sÃ¶zcÃ¼kten gÃ¼Ã§lÃ¼** â€” "NÄ°LÃœFER Ä°LÃ‡E MEM ... **ÅEHÄ°T
>    JANDARMA ER** EYÃœP GÃœRSOY ORTAOKULU" â†’ `guvenlik` idi. Åehit/baÄŸÄ±ÅŸÃ§Ä± adÄ± TÃœR
>    deÄŸil ANMA bilgisi. 67 ad Â· 287 satÄ±r etkilenmiÅŸti. `_UST_ZINCIR` eklendi.
>
> Regresyon paketi 20/20 (gerÃ§ek jandarma/ceza infaz/Ã¼niversite kayÄ±tlarÄ± Ã§alÄ±nmÄ±yor).
>
> ### `backend/idare_tur_kural_backfill.py` (yeni)
> EÅŸleÅŸmeyen adlarÄ± kuralla sÄ±nÄ±flar, `kaynak='kural'` ile yazar, tazeler.
> - **Ã–nuÃ§uÅŸ**: `fold()` â‰¡ SQL `idare_normalize()` deÄŸilse DURDURUR. Bu kontrol
>   olmadan 40K satÄ±r yazÄ±lÄ±r, tazele 0 dÃ¶ner, sebebi anlaÅŸÄ±lmaz. (300 Ã¶rnek, 0 sapma.)
> - `kaynak='elle'` satÄ±rlara DOKUNMAZ (insan dÃ¼zeltmesi korunur).
> - `--detsis-yeniden` var olan satÄ±rÄ±n tÃ¼rÃ¼nÃ¼ yeniden hesaplar ama **kaynak
>   etiketini KORUR** â€” tÃ¼r hesabÄ±nÄ±n dÃ¼zeltilmesi kaydÄ±n kÃ¶kenini deÄŸiÅŸtirmez.
> - Normalize Ã§akÄ±ÅŸmasÄ± (`'TÄ°C.A.Å.'` â†” `'TÄ°C. A.Å.'`) norm bazÄ±nda tekilleÅŸtirilir;
>   yoksa PostgreSQL 21000 "ON CONFLICT DO UPDATE cannot affect row a second time".
>
> ### SonuÃ§ (3 turda, hepsi Ã¶lÃ§Ã¼ldÃ¼)
> ```
> baÅŸlangÄ±Ã§ (yalnÄ±z DETSÄ°S)     1.034.616 satÄ±r sÄ±nÄ±flÄ± Â· 812.932 sÄ±nÄ±fsÄ±z
> kural backfill #1             1.818.147 satÄ±r sÄ±nÄ±flÄ± Â·  29.704 sÄ±nÄ±fsÄ±z
> kurallar dÃ¼zeltilip geniÅŸletildi (--detsis-yeniden ile tam yenileme):
>   54.305 tekil ad â†’ 53.478 Ã§Ã¶zÃ¼ldÃ¼ Â· 1.832.259 satÄ±r
>   KALAN: 827 ad Â· 15.591 satÄ±r (%0,84)
> idare_tur tablosu: 28.566 â†’ 53.478+ eÅŸleme
> ```
> **AI'a hiÃ§ gerek olmadÄ±.** Kalan 15.591 satÄ±rÄ±n tamamÄ± jenerik alt birim adÄ±
> (`DESTEK HÄ°ZMETLERÄ° MÃœDÃœRLÃœÄÃœ` 2.309, `SATIN ALMA DAÄ°RESÄ° BAÅKANLIÄI`,
> `Ä°ÅLETME VE Ä°ÅTÄ°RAKLER MÃœDÃœRLÃœÄÃœ`, `BÃ–LGE KOORDÄ°NATÃ–RLÃœÄÃœ`). Bunlar addan
> Ã§Ä±karÄ±lamaz â€” hangi kuruma baÄŸlÄ± olduklarÄ± bilgisi adÄ±n Ä°Ã‡Ä°NDE YOK. AI'a
> sorulsa uydurmaktan baÅŸka bir ÅŸey yapamaz. DoÄŸru Ã§Ã¶zÃ¼m DETSÄ°S hiyerarÅŸisi,
> o da EKAP kazÄ±masÄ± gerektiriyor (proxy 402 ile bloke). **AI Ã–NERME.**
>
> ### `migration_idare_tur_tazele_fix.sql`
> Backfill eÅŸlemeleri YAZDI ama `idare_tur_tazele()` **57014 statement timeout**
> yedi â†’ kolonlar boÅŸ kaldÄ±. Ä°ki sebep: (a) `dogrudan_temin_ilanlari`'nda ifade
> indeksi YOK (migration yalnÄ±z `ilanlar`'a koymuÅŸ, 1,49M satÄ±rda satÄ±r-baÅŸÄ±
> fonksiyon), (b) fonksiyonun kendi timeout'u yok. Ä°kisi de dÃ¼zeltildi
> (`SET statement_timeout = '1800s'`, SECURITY DEFINER + service_role kÄ±sÄ±tlÄ±
> olduÄŸu iÃ§in gÃ¼venli).
>
> ### Bulunan 5 hata sÄ±nÄ±fÄ± (hepsi eÅŸleÅŸtirme SEMANTÄ°ÄÄ°, kural iÃ§eriÄŸi deÄŸil)
> 1. **SÃ¶zcÃ¼k sÄ±nÄ±rÄ± yok** â€” `'a s'` "satÄ±n **ALMA S**ube"de eÅŸleÅŸti; `belediye_sirket`
>    ONCELIK'te birinci olduÄŸu iÃ§in gÃ¼Ã§lÃ¼ kalÄ±ba dÃ¼ÅŸmeyen HER adÄ± Ã§alÄ±yordu
> 2. **`'karayollari n bolge mudurlugu'`** â€” literal "n" yer tutucusu, hiÃ§bir sayÄ±yla eÅŸleÅŸmez
> 3. **Åehit adÄ± taÅŸÄ±yan okullar** `guvenlik`e gidiyordu (Ã¼st kurum zinciri ezildi)
> 4. **ÅapkalÄ± harf sÃ¶zcÃ¼ÄŸÃ¼ kÄ±rÄ±yor** â€” `MÄ°LLÃ`â†’`mill`, `HÃ‚KÄ°MLER`â†’`h kimler`
> 5. **Kural dosyasÄ±nda dÃ¼zyazÄ±/liste kalÄ±plar** â€” `'...ispark istac kiptas isbak
>    belbim burulas...'` tek dize hÃ¢line gelmiÅŸ, hiÃ§biri eÅŸleÅŸmiyordu
>
> â›” **`fold()` SQL `tr_fold()` ile BAYT BAYT aynÄ± kalmalÄ±** â€” `idare_norm` join
> anahtarÄ±nÄ± o Ã¼retiyor. DeÄŸiÅŸirse 53K eÅŸlemenin anahtarÄ± bayatlar ve tazele
> SESSÄ°ZCE 0 dÃ¶ner. EÅŸleÅŸtirme iyileÅŸtirmesi ayrÄ± `fold_kural()` katmanÄ±nda yapÄ±ldÄ±.
> Backfill Ã¶nuÃ§uÅŸu bu baÄŸÄ± her koÅŸuda doÄŸruluyor.
>
> ### Eski kalan-801 analizi (tarihsel â€” artÄ±k 827 ad / 15.591 satÄ±r)
> TanÄ±mlanabilir kÃ¼meler: TCMB ÅŸubeleri, TTK, Ä°STON, ESHOT, `KONYA B.B. SU KANAL
> Ä°DARESÄ°` (B.B. kÄ±saltmasÄ± tanÄ±nmÄ±yor), GÄ±da Kontrol LaboratuvarlarÄ±, Veteriner
> Kontrol EnstitÃ¼leri, Sulama Birlikleri, Liman Ä°ÅŸletme MÃ¼dÃ¼rlÃ¼kleri, Milli Emlak
> Åeflikleri. GerÃ§ekten Ã§Ã¶zÃ¼lemeyen tek grup jenerik alt birim adlarÄ±
> (`DESTEK HÄ°ZMETLERÄ° SERVÄ°SÄ°-2`, `MARMARA BÃ–LGE KOORDÄ°NATÃ–RLÃœÄÃœ`) â€” bunlar ad'dan
> Ã§Ä±karÄ±lamaz, hiyerarÅŸi gerekir; kod zaten BÄ°LÄ°NÃ‡LÄ° olarak `bilinmiyor` dÃ¶nÃ¼yor.
>
> - [ ] Migration sonrasÄ± doÄŸrula: `ilanlar` NULL ~0, DT NULL ~29K
> - [ ] Kalan 801 ada hedefli kural yaz, `--detsis-yeniden` ile bir kez koÅŸ
>       (kural motoru 3 kez dÃ¼zeldi â†’ DETSÄ°S satÄ±rlarÄ±nÄ±n tÃ¼rÃ¼ de bayat)
> - [ ] ArayÃ¼zde `kaynak` ayrÄ±mÄ±: 'kural' tÃ¼rÃ¼ Ã§Ä±karÄ±mdÄ±r, 'ekap-detsis' resmÃ®.
>       Filtre iÃ§in yeterli ama "kesin" diye sunulmamalÄ±.
>
> ### âš ï¸ PERFORMANS BULGUSU: gece tazelemesi ~10 dk sÃ¼rÃ¼yor
> `idare_tur_tazele()` Ã¶lÃ§Ã¼ldÃ¼: postgres %124 CPU'da **7+ dakika** iÅŸlemci zamanÄ±.
> Sebep join koÅŸulunun satÄ±r baÅŸÄ±na fonksiyon Ã§aÄŸÄ±rmasÄ± â€”
> `t.idare_norm = public.idare_normalize(d.idare)` â†’ 1,49M satÄ±rda tr_fold +
> 2 regexp_replace. Ä°fade indeksi bunu KURTARMIYOR: `IS DISTINCT FROM` koÅŸulu her
> satÄ±rÄ±n okunmasÄ±nÄ± gerektirdiÄŸi iÃ§in planlayÄ±cÄ± seq scan + hash join seÃ§iyor.
> `run_scraper.sh` bunu HER GECE Ã§aÄŸÄ±rÄ±yor â†’ her gece ~10 dk boÅŸa CPU.
>
> **Ã‡Ã¶zÃ¼m (yapÄ±lmadÄ±):** `idare_norm`'u iki tabloda da STORED generated column
> yapmak â†’ join dÃ¼z eÅŸitliÄŸe dÃ¶ner, fonksiyon Ã§aÄŸrÄ±sÄ± sÄ±fÄ±rlanÄ±r.
> ```sql
> ALTER TABLE public.ilanlar ADD COLUMN idare_norm text
>   GENERATED ALWAYS AS (public.idare_normalize(idare)) STORED;
> CREATE INDEX ON public.ilanlar (idare_norm);
> ```
> âš ï¸ 1,85M satÄ±ra kolon eklemek tabloyu yeniden yazar â€” bakÄ±m penceresi ister.
> âš ï¸ `idare_normalize` IMMUTABLE olmak zorunda (Ã¶yle) yoksa generated column reddedilir.
> âš ï¸ Yeni kolon kolon-GRANT'a GÄ°RMEZ â†’ misafirde 42501, `GRANT SELECT (idare_norm)` ÅŸart.

> # ğŸ¯ Ä°Å KUYRUÄU â€” TEK KAYNAK (20 Tem 2026)
> **KullanÄ±cÄ± kararÄ±:** *"eksikleri not al yapÄ±lacaklar md ye, oradan ilerleriz.
> Ã§ift taraftan ilerlemek doÄŸru olmuyor Ã§Ã¼nkÃ¼."* â†’ Yeni iÅŸ talebi geldiÄŸinde Ã–NCE
> buraya yazÄ±lÄ±r, sonra uygulanÄ±r. SÄ±radaki iÅŸ **buradan** seÃ§ilir, sohbetten deÄŸil.
> BaÅŸka bir oturum aynÄ± maddeye dokunuyor olabilir: baÅŸlamadan `git log --oneline -5`.
>
> AÅŸaÄŸÄ±daki maddelerin hepsi **koda oturtuldu** (dosya/satÄ±r/RPC + Ã¶nkoÅŸul + risk).
> Belirsiz madde, ikinci bir oturumun aynÄ± iÅŸi farklÄ± ÅŸekilde yapmasÄ±na davetiyedir.
>
> ---
>
> ## ğŸ”´ P0 â€” CANLI HATALAR (kullanÄ±cÄ± ÅŸu an gÃ¶rÃ¼yor)
>
> ### âœ… P0.1 Ã‡Ã–ZÃœLDÃœ (20 Tem, commit `fea35b3`) â€” ihaleler.html kategori filtresi
> 49 hardcode `<option>` kaldÄ±rÄ±ldÄ±, dropdown `js/kategoriler.js`'ten runtime
> dolduruluyor (`kategoriDropdownDoldur`). `js/kategoriler.js` bu sayfaya Ä°LK KEZ
> eklendi (yÃ¼klÃ¼ deÄŸildi). Geri uyum: `kategoriSecimGarantiEt()` â€” kanonik-dÄ±ÅŸÄ±
> deÄŸer gelirse "(eski)" etiketiyle seÃ§enek eklenip korunuyor; iki Ã§aÄŸrÄ± noktasÄ±
> (`?kategori=` URL parametresi + kayÄ±tlÄ± arama yÃ¼kleyicisi), yoksa kullanÄ±cÄ±nÄ±n
> kayÄ±tlÄ± filtresi sessizce "tÃ¼m kategoriler"e dÃ¶nerdi.
> **Ek Ã¶lÃ§Ã¼m:** kanonik olmayan 17.502 satÄ±rÄ±n **aktif kaydÄ± SIFIR** (hepsi geÃ§miÅŸte)
> â†’ GÃ¼ncel sekmesi iÃ§in kanonik liste %100 yeterli.
> DoÄŸrulama: tÃ¼mÃ¼ 4.952 / SaÄŸlÄ±k 265 / Ä°nÅŸaat 1.145 / Odun-KÃ¶mÃ¼r 43 (birbirinden
> farklÄ± gerÃ§ek sonuÃ§lar), konsol temiz.
> ğŸ”µ Kalan kÃ¼Ã§Ã¼k iÅŸ: o 17.502 geÃ§miÅŸ satÄ±rÄ±n kanonik adlara taÅŸÄ±nmasÄ±
> (`ai_kategori_backfill.py` yalnÄ±z 'DiÄŸer'i hedefliyor, bunlara dokunmuyor).
>
> <details><summary>Orijinal hata kaydÄ± (referans)</summary>
>
> ### P0.1 Â· ihaleler.html kategori filtresinin %90'Ä± Ã¶lÃ¼ â€” Ã–LÃ‡ÃœLDÃœ
> `#f-kategori` (ihaleler.html:520) **48 seÃ§enek** hardcode ediyor ve `<option>`larda
> **`value` attribute'u YOK** â†’ tarayÄ±cÄ± seÃ§enek METNÄ°NÄ° gÃ¶nderiyor. CanlÄ±
> `ilanlar.kategori` ise `js/kategoriler.js`'teki 41 kanonik adÄ± taÅŸÄ±yor.
> REST ile tek tek Ã¶lÃ§Ã¼ldÃ¼: **43 seÃ§enek 0 kayÄ±t** dÃ¶ndÃ¼rÃ¼yor. Ã‡alÄ±ÅŸan yalnÄ±z 5 eski deÄŸer:
> `Ä°nÅŸaat Malzemeleri` 10.025 Â· `Mal AlÄ±mÄ±` 5.976 Â· `Hizmet AlÄ±mÄ±` 1.395 Â·
> `Ä°nÅŸaat & YapÄ±m` 345 Â· `DanÄ±ÅŸmanlÄ±k` 285.
> Ã–lÃ¼ Ã¶rnekler: SaÄŸlÄ±k, TÄ±bbi Cihazlar, BT EkipmanlarÄ±, YazÄ±lÄ±m, Enerji, GÄ±da & Ä°Ã§ecekâ€¦
> **Ã‡Ã–ZÃœM:** select'i `js/kategoriler.js`'ten runtime doldur (dogrudan-temin.html:973
> `kategorileriYukle()` bunu ZATEN doÄŸru yapÄ±yor â€” deseni oradan al).
> **DÄ°KKAT:** kayÄ±tlÄ± aramalarda/URL'de eski kategori deÄŸerleri kalmÄ±ÅŸ olabilir; geÃ§iÅŸ
> eÅŸlemesi dÃ¼ÅŸÃ¼nÃ¼lmeli yoksa kullanÄ±cÄ±nÄ±n kayÄ±tlÄ± filtresi sessizce boÅŸalÄ±r.
>
> </details>
>
> ### P0.2 Â· SÃ¼resi dolan RFQ'lar sonsuza dek "aÃ§Ä±k" kalÄ±yor
> `ilan_durum_bayatlat()` YALNIZ `public.ilanlar`'Ä± gÃ¼nceller; `satinalma_talepleri`'ne
> hiÃ§ dokunmuyor. `il_rfq_dagilimi` de sadece `durum='acik'` bakÄ±yor, tarih filtresi yok.
> Åu an 3 RFQ'nun da tarihi gelecekte olduÄŸu iÃ§in gÃ¶rÃ¼nmÃ¼yor ama zaman geÃ§tikÃ§e harita
> ve e-SatÄ±nalma "aÃ§Ä±k fÄ±rsat" diye bayat kayÄ±t gÃ¶sterecek.
> **Ã‡Ã–ZÃœM (biri):** `il_rfq_dagilimi`'ye `son_teklif_tarihi >= now()` ekle **veya**
> `run_scraper.sh`'e RFQ bayatlatma adÄ±mÄ± koy. Ä°lki daha ucuz, ikincisi daha doÄŸru
> (liste ekranlarÄ± da dÃ¼zelir).
>
> ---
>
> ## ğŸŸ  P1 â€” KULLANICI TALEPLERÄ° (19-20 Tem, sÄ±rayla)
>
> ### P1.1 Â· Analizlere "TÃ¼mÃ¼ / Ä°haleler / DoÄŸrudan Temin" ayrÄ±mÄ±
> *"analiz kÄ±sÄ±mlarÄ±nÄ± da ayÄ±racaÄŸÄ±z, ayÄ±rÄ±p sÄ±ralamamÄ±z gerekiyor, diÄŸer tÃ¼rlÃ¼
> doÄŸrudan teminleri sÄ±ralayamÄ±yoruz."*
>
> **Mevcut durum:** Analiz sayfalarÄ±nÄ±n **hiÃ§birinde** DT verisi YOK. `rekabet_ozet`,
> `kurum_ozet`, `analiz_pivot`, `idare_dizin_json`, `kategori_sayim` â€” hepsinin gÃ¶vdesi
> `FROM public.ilanlar` / `ihale_sonuclari`. DT'ye tek referans sol menÃ¼ linki.
> **Referans uygulama elimizde:** `dashboard.html:818` `dashModSec()` Ã¼Ã§lÃ¼ mod seÃ§ici
> (tumu/ihale/dt) Ã§alÄ±ÅŸÄ±yor ve tÃ¼m widget'larÄ± sÃ¼rÃ¼yor. Bunu `js/mod-secici.js`'e
> Ã§Ä±kar, 4 sayfada kopyalama.
>
> **Ä°ki hÄ±zda ilerle:**
> - **UCUZ (saf frontend, backend deÄŸiÅŸikliÄŸi SIFIR):**
>   `sektorler.html:336` â†’ `dt_kategori_sayim()` ZATEN var, dÃ¶nÃ¼ÅŸ ÅŸekli `kategori_sayim`
>   ile birebir aynÄ±. `kurum-analiz.html:1029` â†’ `dt_idare_sayim()` var (âš ï¸ jsonb vs SETOF
>   ÅŸekil farkÄ± normalize edilmeli; ikisi de anon'a KAPALI, misafir dalÄ± korunmalÄ±).
> - **PAHALI (yeni RPC + Ã¼rÃ¼n kararÄ±):**
>   `kurum-analiz.html:856` (`kurum_ozet`), `rekabet-analizi.html:352` (`rekabet_ozet`),
>   `kurum-analiz.html:893` (`analiz_pivot`) â€” DT karÅŸÄ±lÄ±ÄŸÄ± YOK, yazÄ±lmalÄ±.
>
> **ğŸš§ ÃœRÃœN KARARI GEREKÄ°YOR â€” ÅŸema asimetrisi:** `dogrudan_temin_ilanlari`'nda
> `yaklasik_maliyet`, `usul`, `son_teklif_tarihi` **YOK**. Yani "TÃ¼mÃ¼" modunda ihale
> sayÄ±sÄ± artar ama toplam bÃ¼tÃ§e artmaz â†’ KPI'lar kendi iÃ§inde tutarsÄ±z olur.
> Karar: bu kartlar "TÃ¼mÃ¼"de gizlensin mi, yoksa *"parasal veriler yalnÄ±z ihalelerden"*
> notu mu taÅŸÄ±sÄ±n? **Sessizce 0 gÃ¶stermek yanÄ±ltÄ±cÄ± olur, o seÃ§enek yok.**
>
> **â›” firma-analiz.html KAPSAM DIÅI bÄ±rakÄ±lmalÄ±:** DT sonuÃ§larÄ±nda `yuklenici_id`
> BÄ°LEREK boÅŸ (`migration_dt_kazanan.sql:63`), firma geÃ§miÅŸi gÃ¼venilir Ã§ekilemez.
> Ã–nce DTâ†’yukleniciler normalize_firma eÅŸleme turu gerekir.
> Ek kÄ±sÄ±t: DT kazanan/bedel kapsamasÄ± ~%1,3.
>
> ### P1.2 Â· e-SatÄ±nalma RFQ'larÄ± haritada gÃ¶rÃ¼nmÃ¼yor
> *"e-satÄ±nalmada girilen aÃ§Ä±k ihaleler haritada aÃ§Ä±k RFQ da gÃ¶rÃ¼nmÃ¼yor."*
>
> **âš ï¸ Ã–NCE TEÅHÄ°S â€” veri/RPC SAÄLAM, sorun hangi ekrana baktÄ±ÄŸÄ±nda:**
> `il_rfq_dagilimi` prod'da 200 dÃ¶nÃ¼yor, anon'a aÃ§Ä±k, 3 aÃ§Ä±k RFQ veriyor
> (Ankara/Ä°stanbul/Kocaeli). `harita.html`'de tarayÄ±cÄ±da **doÄŸru Ã§iziliyor** (3 pin,
> "AÃ§Ä±k RFQ" KPI = 3). Tablo/durum eÅŸleÅŸmesi tam (`ozel-ihaleler.html:331` `durum:'acik'`
> â†” fonksiyon `WHERE durum='acik'`), MV deÄŸil (tazeleme gecikmesi yok).
>
> ÃœÃ§ ayrÄ± olasÄ±lÄ±k, **hangisi olduÄŸu kullanÄ±cÄ±dan teyit edilmeli:**
> 1. **dashboard/index haritasÄ±** â†’ `js/harita.js`'te RFQ **hiÃ§ yok**: satÄ±r 85 `MOD_BASLIK`
>    3 modlu, satÄ±r 176 `Promise.all` yalnÄ±z `il_sayim_aktif` + `dt_il_sayim_aktif`.
>    âš ï¸ Ama `firma-analiz.html:1430`'da kayÄ±t var: *"karar 16 Tem: RFQ katmanÄ± yalnÄ±z
>    e-SatÄ±nalma haritasÄ±nda kalÄ±r"* â†’ bu **bilinÃ§li bir karardÄ±**, geri alÄ±nacaksa teyit ÅŸart.
> 2. **harita.html** â†’ katman VAR ama varsayÄ±lan deÄŸil (`aktifKatman='firma'`, satÄ±r 242).
>    Bu kod hatasÄ± deÄŸil **keÅŸfedilebilirlik** sorunu; Ã§Ã¶zÃ¼mÃ¼ tamamen farklÄ±
>    (varsayÄ±lanÄ± 'rfq' yap veya dÃ¼ÄŸmeye sayÄ± rozeti koy).
> 3. **ihaleler.html** â†’ `satinalma_talepleri` hiÃ§ geÃ§miyor; "da/de" ifadesi RFQ'larÄ±n
>    ana ihale listesinde de olmamasÄ±na iÅŸaret ediyor olabilir.
>
> **Ä°L ANAHTARI TUZAÄI:** `il_rfq_dagilimi` **Title case** ('Ä°stanbul') dÃ¶ndÃ¼rÃ¼yor,
> `js/harita.js:65` `ilAnahtar()` ise BÃœYÃœK HARF varsayÄ±yor. Normalize edilmezse sayÄ±lar
> sessizce 0 gÃ¶rÃ¼nÃ¼r (bkz. [[ilike-tr-locale-tuzagi]]). `harita.html:203` `fold()` kopyalanmalÄ±.
> **Ã–LÃ‡EK:** 3 RFQ'ya karÅŸÄ± 4.654 aktif ihale + 95.695 DT â†’ ortak choropleth'e katmak
> RFQ'yu gÃ¶rÃ¼nmez kÄ±lar; AYRI katman/pin muamelesi doÄŸru.
>
> ### P1.3 Â· Ticaret analizi: her Ã¼lkenin verisi + arama geliÅŸtirme
> *"her Ã¼lkenin verisini Ã§ekmek avantajlÄ± olabilir, tek sefer Ã§ekerizâ€¦ ileride
> konÅŸimento verileri ile de kÄ±yaslayacaÄŸÄ±z."*
>
> **ğŸ”´ EN KRÄ°TÄ°K RÄ°SK â€” SESSÄ°Z VERÄ° KAYBI:** `reporterCode=792` (TÃ¼rkiye) iki script'e de
> GÃ–MÃœLÃœ (`ticaret_hs_cek.py:43`, `ticaret_backfill.py:62`) ve **hiÃ§bir tabloda raportÃ¶r
> kolonu yok**. `on_conflict=(ulke_iso3,hs6,yon,yil)` olduÄŸu iÃ§in sadece reporterCode'u
> deÄŸiÅŸtirip Ã§alÄ±ÅŸtÄ±rmak **Almanya'nÄ±n verisini TÃ¼rkiye'nin Ã¼zerine yazar â€” hata vermez,
> log "baÅŸarÄ±lÄ±" der.** SIRA ÅART: Ã¶nce migration (raportor kolonu + PK), sonra script.
>
> **HACÄ°M â€” tam kÃ¼p UYGULANAMAZ:** 176Ã—176Ã—HS6 â‰ˆ yÄ±lda 30M satÄ±r; 26 yÄ±l â‰ˆ 600M satÄ±r
> â‰ˆ 120 GB (VDS'te yer yok). Comtrade **500 Ã§aÄŸrÄ±/gÃ¼n** kotasÄ±yla tek bir veri-yÄ±lÄ±
> **8,5 gÃ¼n** sÃ¼rer. "Tek sefer Ã§ekeriz" tam kÃ¼pte gerÃ§ekÃ§i deÄŸil.
> **UCUZ ALTERNATÄ°F (asÄ±l istenen bu):** (A) her raportÃ¶r Ã— partner=DÃ¼nya(0) Ã— AG6
> â†’ 26 yÄ±l ~624 Ã§aÄŸrÄ± (~1,5 gÃ¼n); (B) ayna istatistik (reporter=X, partner=TR) â‰ˆ aynÄ± maliyet.
>
> **KONÅÄ°MENTO Ä°Ã‡Ä°N ÅÄ°MDÄ°DEN ALINMALI:** `ticaret_hs_cek.py:134` yalnÄ±z `primaryValue`
> alÄ±yor, **`netWgt`/`qty` atÄ±lÄ±yor**. KonÅŸimento tonaj bazlÄ± â†’ sonradan eklemek tÃ¼m
> kotayÄ± ikinci kez harcamak demek. Tek seferlik Ã§ekimde MUTLAKA alÄ±nmalÄ±.
>
> **â° ZAMAN BOMBASI (veri geniÅŸletmeden Ã–NCE dÃ¼zelt):** `migration_hs_hiyerarsi.sql:34`
> `ticaret_hs_kalem` "gÃ¼ncel/Ã¶nceki"yi `max(yil)`/`min(yil)` ile buluyor. 3. yÄ±l eklenir
> eklenmez "Ã¶nceki" = EN ESKÄ° yÄ±l olur, tÃ¼m DeÄŸiÅŸim% deÄŸerleri sessizce yanlÄ±ÅŸlanÄ±r
> (aynÄ± desen satÄ±r 63 ve 92'de de var; frontend'de de gÃ¶mÃ¼lÃ¼: `ticaret-analiz.html:626`).
> Bu, tenzilat-Ã§ok-lot hatasÄ±yla **aynÄ± sÄ±nÄ±f sessiz bozulma**.
>
> **ARAMA Ä°YÄ°LEÅTÄ°RME (en yÃ¼ksek getiri):** `ticaret-analiz.html:788` HS aramasÄ±
> `kod.startsWith(q)` â†’ '471' yazÄ±nca 8471 bulunamÄ±yor; 930 KB `hs-kodlar.js` client'a
> iniyor. Sunucu-taraflÄ± HS arama RPC'si + `tr_fold` + trigram indeks.
>
> ### P1.4 Â· Arama ekranlarÄ±nÄ± birleÅŸtir (ihaleciler.com deseni)
> *"arama ekranlarÄ±nÄ± deÄŸiÅŸtireceÄŸiz, bÃ¶yle olmaz Ã§ok karÄ±ÅŸÄ±k."*
>
> **ORTAK BÄ°LEÅEN HÄ°Ã‡ YOK.** `css/style.css` (827 satÄ±r) tamamen landing-page stili â€”
> tek bir filtre/tablo/sekme bileÅŸeni yok. 8 gerÃ§ek arama ekranÄ± ~103 KB inline `<style>`
> taÅŸÄ±yor; 18 CSS kuralÄ± 8 sayfada byte-byte aynÄ±. `js/ui.js` (307 satÄ±r) ve
> `js/ihaleler.js` (157 satÄ±r) **hiÃ§bir sayfadan Ã§aÄŸrÄ±lmÄ±yor â€” Ã¶lÃ¼ kod.**
>
> **AsÄ±l "karÄ±ÅŸÄ±klÄ±k" kaynaÄŸÄ± = uygulama modeli tutarsÄ±zlÄ±ÄŸÄ±:**
> `ihaleler.html` TEK barda **4 farklÄ± davranÄ±ÅŸ** barÄ±ndÄ±rÄ±yor: tarih+sÄ±ralama anÄ±nda Â·
> Ä°l/Kategori/TÃ¼r/Usul/Kaynak/bedel butonla Â· ana kutu yalnÄ±z Enter Â· topbar 400 ms canlÄ±.
> `kik-kararlar.html` yalnÄ±z-manuel AMA aynÄ± "SonuÃ§" filtresi ikinci kez anÄ±nda-uygulanan
> Ã§ip olarak da var (iki kontrol aynÄ± alanÄ± yÃ¶netiyor, birbirinden habersiz).
> Debounce: 6 sayfada **4 farklÄ± deÄŸer** (250/300/350/400 ms).
> "SÄ±fÄ±rla": ihaleler'de 2 tane, 4 sayfada hiÃ§ yok.
> Ä°simlendirme: aynÄ± iÅŸlev iÃ§in 6 farklÄ± sÄ±nÄ±f ÅŸemasÄ± (`.filter-bar` / `.toolbar` /
> `.arama-panel` / `.rfq-filtre` / `.filtre-bar` / `.dz-toolbar` / `.iz-ara`);
> `.result-count` ve `.results-count` tek harf farkla iki ayrÄ± sÄ±nÄ±f.
>
> **REFERANS = `dogrudan-temin.html`** (tek dÃ¼ÅŸÃ¼nÃ¼lmÃ¼ÅŸ ekran: anÄ±nda uygulama + aktif
> filtre Ã§ipleri + `f-dt-` Ã¶nekli id'ler + "neden bu filtre yok" aÃ§Ä±klamasÄ±).
> **EN KÃ–TÃœ = `ihaleler.html`** (en Ã§ok trafik alan sayfa; P0.1 buradan Ã§Ä±ktÄ±).
>
> ### P1.5 Â· Ä°dareler dizinini kurumlara gÃ¶re sÄ±nÄ±flandÄ±r
> *"kurumlar DETSÄ°S'ten tam Ã§ekildikten ve aÄŸaca gÃ¶re yerleÅŸtirildikten SONRAKÄ° iÅŸ o."*
>
> **âœ… Ã–NEMLÄ° DÃœZELTME â€” altyapÄ± sanÄ±landan Ã‡OK Ä°LERÄ°DE.** Bu oturumda "migration'lar
> prod'a uygulanmamÄ±ÅŸ" dedim, **YANLIÅTI**. AyÄ±rt etme kuralÄ±: `42501` = nesne VAR +
> yetki yok Â· `42703` = gerÃ§ekten yok. Ã–lÃ§Ã¼m:
> `ilanlar.detsis_no` â†’ 42501 (**VAR**) Â· `dogrudan_temin_ilanlari.detsis_no` â†’ 42501 (**VAR**) Â·
> `idare_hiyerarsi` â†’ 42501 (**VAR**) Â· `idare_ata_torun` â†’ 42501 (**VAR**) Â·
> `hiyerarsi_yolu` â†’ 42703 (yok â€” ve GEREKSÄ°ZLEÅTÄ°, yerine kapanÄ±ÅŸ tablosu geldi) Â·
> kontrol `boyle_bir_kolon_yok` â†’ 42703.
> âš ï¸ Bu yanlÄ±ÅŸ okumayla hareket edilirse uygulanmÄ±ÅŸ migration'lar tekrar koÅŸturulur ve
> 19 Tem'deki **ACCESS EXCLUSIVE kilit olayÄ± (canlÄ± site tÄ±kandÄ±)** tekrarlanÄ±r.
>
> **GERÃ‡EK DARBOÄAZ ÅŸema deÄŸil VERÄ° + ARAYÃœZ:**
> - `idare_tur` kapsamasÄ± **%32,3** (356.904 ihalenin 241.508'i sÄ±nÄ±fsÄ±z). YÃ¼kseltmenin
>   TEK yolu `ekap_detsis_cek.py --tara` (85.062 istek) â†’ **proxy 402 ile BLOKE**.
> - ArayÃ¼z **%0**: hiÃ§bir HTML/JS `idare_agac_*` / `detsis_no` Ã§aÄŸÄ±rmÄ±yor.
>   Ä°ÅŸ yeri `kurum-analiz.html:1029` (idareler.html oraya yÃ¶nlendiriyor), ÅŸu an dÃ¼z liste.
> - `run_scraper.sh`'te `idare_tur_tazele()` VAR ama `idare_kapanis_uret()`,
>   `ilan_detsis_esle()`, `REFRESH idare_hiyerarsi_sayim_mv` **YOK** â†’ sayaÃ§lar bayatlar.
>
> **SIRA BAÄIMLILIÄI SERT** (bozulursa hata VERMEZ, sayaÃ§lar 0 Ã§Ä±kar â€” sessiz baÅŸarÄ±sÄ±zlÄ±k):
> `idare_hiyerarsi yÃ¼kle` â†’ `idare_kapanis_uret()` â†’ `idare_tur.detsis_no doldur (--tara)`
> â†’ `ilan_detsis_esle()` â†’ `REFRESH idare_hiyerarsi_sayim_mv`. Her adÄ±mdan sonra satÄ±r say.
>
> **Ä°ÅE BAÅLAMADAN psql ile Ã¶lÃ§** (anon'dan okunamÄ±yor, ayrÄ± onay gerekir):
> ```sql
> SELECT count(*) FROM idare_hiyerarsi;                    -- 87.528 bekleniyor
> SELECT count(*) FROM idare_ata_torun;                    -- ~312.259 bekleniyor
> SELECT count(*) FILTER (WHERE detsis_no IS NOT NULL), count(*) FROM ilanlar;
> SELECT count(*) FILTER (WHERE detsis_no IS NOT NULL) FROM idare_tur;  -- ASIL BELÄ°RLEYÄ°CÄ°
> ```
> **%67,7 SESSÄ°Z KAYIP RÄ°SKÄ°:** hiyerarÅŸi/tÃ¼r filtresi SERT uygulanÄ±rsa 241.508 sÄ±nÄ±fsÄ±z
> ihale listeden sessizce dÃ¼ÅŸer. "SÄ±nÄ±flanmamÄ±ÅŸlarÄ± da gÃ¶ster" varsayÄ±lanÄ± veya kapsama
> rozeti ÅŸart. AyrÄ±ca 87.528 dÃ¼ÄŸÃ¼mÃ¼n **%20'si "BaÄŸlantÄ±sÄ±z Kurumlar" (-999999)** altÄ±nda,
> bakanlÄ±ÄŸa yuvarlanamaz â†’ arayÃ¼zde AYRI DAL olarak dÃ¼rÃ¼stÃ§e gÃ¶sterilmeli.
> **SIZINTI ADAYI:** `idare_tur` tablosu ve `idare_tur_liste()` anon'a **200** dÃ¶nÃ¼yor
> (satÄ±r gelmiyor Ã§Ã¼nkÃ¼ RLS engelliyor) â€” bu [[anon-maske-iki-kok-neden]] kÃ¶k neden A deseni.
> RLS tek katman olarak bÄ±rakÄ±lmamalÄ±, aÃ§Ä±k REVOKE eklenmeli.
>
> ---
>
> ## ğŸŸ¡ P2 â€” BLOKE / BEKLEYEN
> - **Proxy 402** â€” en Ã¼stteki blokaj. DT tam tarama, 1,6M backfill, DETSÄ°S `--tara`
>   hepsi buna baÄŸlÄ±. KullanÄ±cÄ± aksiyonu (Ã¶deme/kota).
> - **`authenticated` rolÃ¼ hÃ¢lÃ¢ her tabloda tablo-geneli SELECT.** 20 Tem taramasÄ±
>   token dÄ±ÅŸÄ±nda kimlik-benzeri kolon bulmadÄ±, ama o tablolara eklenecek yeni hassas
>   kolon otomatik olarak tÃ¼m Ã¼yelere aÃ§Ä±lÄ±r. AyrÄ± denetim iÅŸi.
> - **Secret rotasyonu** â€” JWT_SECRET + Google client secret (sohbette ifÅŸa oldu).
> - **`API_EXTERNAL_URL`** hÃ¢lÃ¢ `http://195.85.207.126:8000` â†’ GoTrue e-posta linkleri.
> - **`ekap_sonuc_backfill.py:310`** `json.dumps(...)[:15000]` kÄ±rpmasÄ± 725 satÄ±rda JSON bozuyor.
> - **`idx_ilanlar_olusturulma`** â€” "Sisteme Yeni DÃ¼ÅŸen" sÄ±ralamasÄ±nÄ±n Ã¶n koÅŸulu; indeks yok.
> - **Gece koÅŸusu doÄŸrulamasÄ±** â€” `=== Idare turu tazeleme ===` + `=== Lot sayisi tazeleme ===`
>   satÄ±rlarÄ± logda gÃ¶rÃ¼lmeli (20 Tem'de eklendi, henÃ¼z koÅŸmadÄ±).
>
> ---
>
> # ğŸ”¬ Ä°KÄ°NCÄ° TUR KARARLARI (20 Tem) â€” P1 maddelerinin NÄ°HAÄ° hÃ¢li
> YukarÄ±daki P1.1â€“P1.5 **ilk turdur**. Her tavsiye ayrÄ± bir ajana *Ã§Ã¼rÃ¼tÃ¼lmek Ã¼zere*
> verildi ve **Ã¼Ã§Ã¼ dÃ¼zeltildi**. Ã‡eliÅŸmede dÃ¼zeltilen bir tavsiyeyi savunma â€” aÅŸaÄŸÄ±sÄ± geÃ§erli.
> AyrÄ±ca aÃ§Ä±k kalan iki karar **veriyle Ã§Ã¶zÃ¼ldÃ¼**, kullanÄ±cÄ±ya sorulmasÄ±na gerek kalmadÄ±.
>
> ## ğŸ”´ YENÄ° P0.3 â€” ANALÄ°Z RPC'LERÄ° VERÄ°NÄ°N %4'ÃœNÃœ GÃ–RÃœYOR (canlÄ±da YANLIÅ)
> `rekabet_ozet` ve `kurum_ozet` trend eksenini `ilan_tarihi` ile kuruyor.
> **BaÄŸÄ±msÄ±z Ã¶lÃ§Ã¼ldÃ¼ (canlÄ± REST):** `ilan_tarihi` 15.245/357.207 = **%4,27** dolu Â·
> `etkin_tarih` 351.883 = **%98,51** Â· `son_teklif_tarihi` 16.669 = %4,67 Â·
> `durum='aktif'` = **4.954**.
> Yani trend/KPI grafikleri verinin yirmide birine dayanÄ±yor ve `kpi.aktif` yanlÄ±ÅŸ tabanda.
> **Bu, 5 maddenin hepsinden Ã¶nce gelir** â€” yeni Ã¶zellik deÄŸil, mevcut yanlÄ±ÅŸÄ±n dÃ¼zeltmesi.
> DÃ¼zeltme: iki RPC'nin eksenini `etkin_tarih`'e taÅŸÄ±, `kpi.aktif`'i `durum='aktif'` tabanÄ±na al.
>
> ## 1) Analiz "TÃ¼mÃ¼ / Ä°haleler / DT" â€” parasal birleÅŸtirme REDDEDÄ°LDÄ°
> **VERÄ°YLE Ã‡Ã–ZÃœLDÃœ:** DT bedel kapsamasÄ± **78.109/1.490.644 = %5,24** (yÄ±l kÄ±rÄ±lÄ±mÄ±:
> 2026 %9,17 Â· 2025 %0,30 â†’ birleÅŸtirme yapay sÄ±Ã§rama Ã¼retirdi). AyrÄ±ca
> `dogrudan_temin_sonuclari.yaklasik_maliyet` â†’ **42703 (kolon YOK)**; elde yalnÄ±z
> `kazanan_bedel` = *sÃ¶zleÅŸme bedeli* var â†’ yaklaÅŸÄ±k maliyetle toplamak **kategori hatasÄ±**.
> KazÄ±ma ilerlese bile bu gerekÃ§e kalÄ±cÄ±. â†’ **DT parasal kartlara KATILMAYACAK**,
> kartlar "yalnÄ±zca ihaleler" rozeti + "N ihale Ã¼zerinden" paydasÄ± taÅŸÄ±yacak.
>
> **âš ï¸ Ã‡ELÄ°ÅMEDE Ã‡IKAN YENÄ° HATA:** `ihale_sonuclari.yaklasik_maliyet` %98,6 dolu AMA
> **kÄ±sÄ±m bazlÄ± deÄŸil** â€” Ã§ok kÄ±sÄ±mlÄ± ihalede aynÄ± deÄŸer her satÄ±ra kopyalanmÄ±ÅŸ.
> KanÄ±t: `ilan_id 56e4dc72` â†’ 35 kÄ±sÄ±m, SUM 808.746.995 vs gerÃ§ek 23.107.057 = **35,0x ÅŸiÅŸme**.
> `lot_sayisi=1` filtresiyle Ã§Ã¶zmek de YANLIÅ: 530.440 â†’ 283.438 (**%46 kayÄ±p**, en bÃ¼yÃ¼k
> ihaleler dÃ¼ÅŸer; ymâ‰¥10M bandÄ± 139.634 â†’ 43.545 = ~3,2x sapma).
> **DoÄŸru yol: `ilan_id` bazÄ±nda DISTINCT** (ayrÄ± `ihale_butce_mv`, Faz B).
>
> **Faz A (SQL yok, bir oturum):** rozet + payda + `etkin_tarih` ekseni + `kpi.aktif`.
> Mod anahtarÄ±nda sayÄ±m/kÄ±rÄ±lÄ±m kartlarÄ± DT'yi kapsar; **idare kÄ±rÄ±lÄ±mÄ± misafirde DT
> dalÄ±nÄ± DIÅLAR** (`dogrudan_temin_ilanlari.idare` anonda 42501); `usul` ve `durum`
> kartlarÄ± "TÃ¼mÃ¼"de gizlenir (DT'de usul kolonu yok, durum deÄŸerleri ayrÄ±k).
> **Faz B (ayrÄ± commit):** `ihale_butce_mv` + gece REFRESH + anon GRANT.
> âš ï¸ Faz B'yi doÄŸrudan `ihale_sonuclari`'na baÄŸlama: `rekabet_ozet` dÃ¼z `LANGUAGE sql
> STABLE` (Ã§aÄŸÄ±ran yetkisiyle koÅŸar) â†’ misafirde rekabet-analizi **komple 42501** olur.
> `kurum_ozet` SECURITY DEFINER olduÄŸu iÃ§in etkilenmez â€” bu asimetri tuzak.
>
> ## 2) RFQ â€” 16 Tem kararÄ± BOZULMAYACAK, bu keÅŸfedilebilirlik hatasÄ±
> **VERÄ°YLE Ã‡Ã–ZÃœLDÃœ:** veri/RPC saÄŸlam, `harita.html`'de doÄŸru Ã§iziliyor.
> `satinalma_talepleri` 3 kayÄ±t, Ã¼Ã§Ã¼ `durum='acik'`, en yakÄ±nÄ± **26 gÃ¼n sonra** bayatlÄ±yor.
> `ozel-ihaleler.html`'de kullanÄ±cÄ±ya harita vaadi verilmiyor (tek referans satÄ±r 313'teki
> "Ä°l zorunludur" notu) â†’ ÅŸikÃ¢yetin Ã§ekirdeÄŸi **kÃ¶prÃ¼ yokluÄŸu**.
> **Ä°lk adÄ±m (bir oturum):**
> 1. `ozel-ihaleler.html:337` baÅŸarÄ± mesajÄ±na + liste baÅŸlÄ±ÄŸÄ±na
>    `ğŸ—ºï¸ AÃ§Ä±k talepleri haritada gÃ¶r (N)` â†’ `harita?katman=rfq`
> 2. `harita.html`: `?katman=rfq` + `?il=` derin linkini kabul et (mevcut `?sektor=` bloÄŸu yanÄ±na).
>    **`aktifKatman='firma'` varsayÄ±lanÄ± KALSIN** (53.897 firma vs 3 RFQ)
> 3. RFQ butonuna rozet â€” **yalnÄ±z sayÄ± > 0 iken** (41 kategori Ã— 3 RFQ â†’ Ã§oÄŸu sektÃ¶rde "0" yazardÄ±)
> 4. `il_rfq_dagilimi`'ye bayatlama filtresi â€” **Ã‡IPLAK `>= now()` YAZMA**:
>    `AND (son_teklif_tarihi IS NULL OR son_teklif_tarihi >= now())`. Kolon nullable ve
>    `ozel-ihaleler.html:377` listesi tarihsizleri gÃ¶steriyor; Ã§Ä±plak filtre haritayla listeyi
>    ters yÃ¶nde ayÄ±rÄ±rdÄ±. `durum` ekseni de hizalanmalÄ± (RPC `='acik'`, liste `!='iptal'`).
> 5. Yorum dÃ¼ÅŸ: `acik_adres`, `olusturan_vkn`, `ilce` anonda **42501** â€” RFQ kartÄ±nÄ± bu
>    kolonlarla zenginleÅŸtiren misafirde sayfayÄ± Ã¶ldÃ¼rÃ¼r.
>
> ## 3) Ticaret â€” canlÄ± tabloya PK TAKASI YAPILMAYACAK
> **Ã‡ELÄ°ÅME BUNU TERSÄ°NE Ã‡EVÄ°RDÄ°.** Ä°lk tur "raportor kolonu + PK deÄŸiÅŸtir" diyordu;
> canlÄ± `dis_ticaret_hs` (780.386 satÄ±r) Ã¼zerinde PK/indeks takasÄ±, `CREATE OR REPLACE`
> ile yeni imza eklemenin **PGRST203** Ã¼retmesi, yeni imzada GRANT olmamasÄ± (**42883**) ve
> `DROP INDEX CONCURRENTLY`nin virgÃ¼llÃ¼ liste kabul etmemesi yÃ¼zÃ¼nden riskli.
> â†’ **DiÄŸer raportÃ¶rler AYRI tabloya: `public.dis_ticaret_dunya`.** CanlÄ± tabloya sÄ±fÄ±r dokunuÅŸ.
>
> **Ã–lÃ§Ã¼len fÄ±rsat:** Comtrade `reporterCode` **virgÃ¼llÃ¼ liste kabul ediyor** (5 raportÃ¶r
> tek Ã§aÄŸrÄ±da doÄŸrulandÄ±) ve `flowCode=X,M` Ã§alÄ±ÅŸÄ±yor â€” mevcut 4 script X ve M'yi ayrÄ±
> Ã§ekiyor, yani **Ã§aÄŸrÄ±larÄ±n %50'si israf**. `netWgt` 500/500, `qty` 498/500 dolu geliyor
> ama kod atÄ±yor â†’ konÅŸimento kÄ±yasÄ± iÃ§in **ÅŸimdi alÄ±nmalÄ±**, sonradan Ã§ekmek kotayÄ± ikinci kez yakar.
> **â° `ticaret_hs_fasil`'Ä±n yÄ±l penceresi WHERE'siz** (`max(yil)` tÃ¼m tablodan) â€” ikinci
> raportÃ¶rÃ¼n 2025 satÄ±rÄ± girerse TR fasÄ±l tablosu boÅŸalÄ±r. AyrÄ± tablo bu tuzaÄŸÄ± da atlatÄ±yor.
> **26 yÄ±l backfill YAPILMAYACAK**; Ã¶nce tek-yÄ±l pilotu, sonuÃ§ gÃ¶rÃ¼lÃ¼nce karar.
>
> ## 4) Arama/filtre â€” SIRA TERSÄ°NE Ã‡EVRÄ°LDÄ°: Ã¶nce davranÄ±ÅŸ, CSS en son
> **Ã‡ELÄ°ÅME DÃœZELTTÄ°.** Ã–lÃ§Ã¼m CSS birleÅŸtirmenin ÅŸikÃ¢yete dokunmadÄ±ÄŸÄ±nÄ± gÃ¶sterdi:
> 8 sayfa inline CSS **91.206 B**, ortak kabuk yalnÄ±z %21, **%79'u sayfaya Ã¶zel** â€”
> filtre CSS'i zaten hiÃ§bir sayfada ortak deÄŸil.
> AsÄ±l ÅŸikÃ¢yet **davranÄ±ÅŸ tutarsÄ±zlÄ±ÄŸÄ±**: `ihaleler.html` tek baÅŸÄ±na 4 model barÄ±ndÄ±rÄ±yor
> (5 kontrol anÄ±nda Â· topbar 400ms Â· `f-arama` Enter Â· `f-idare`/`f-esik-katsayi`/`f-okas`
> **hiÃ§ handler'Ä± yok**, yalnÄ±z butonla).
> **Commit 1 (sÄ±fÄ±r gÃ¶rsel risk):** `js/api.js:98,111` `UI.bildirim_goster()` Ã§aÄŸÄ±rÄ±yor ama
> `UI` yalnÄ±z `js/ui.js`'te ve api.js yÃ¼kleyen 6 sayfanÄ±n hiÃ§biri onu yÃ¼klemiyor â†’
> yerel `bildirimGoster()` koy. **7 Ã¶lÃ¼ dosya sil** (1.164 satÄ±r / 48.777 B: ui.js,
> dashboard.js, ihale-detay.js, ihaleler.js, fiyatlandirma.js, profil.js, auth.js â€”
> HTML referansÄ± 0, dinamik import 0). `ihale-detay.html` + `profil.html`'den gereksiz
> api.js script tag'ini kaldÄ±r.
> **Commit 2:** `ihaleler.html`'in 3 handler'sÄ±z alanÄ±na handler ekle (metin 350ms debounce,
> select/date anÄ±nda, Enter debounce atlar) + `sayacIstekNo` yarÄ±ÅŸ korumasÄ±.
> âš ï¸ Ã–nce ILIKE gecikmesini Ã–LÃ‡ â€” `f-idare` her tuÅŸta sunucu ILIKE'Ä±, 57014 baskÄ±sÄ± var.
> **CSS en sona:** `css/kabuk.css` ayrÄ±, `css/arama.css` yalnÄ±z filtre kurallarÄ±, `.ara-*`
> ad alanÄ±. `.toolbar` 4 sayfada 3 farklÄ± deÄŸer taÅŸÄ±yor â€” naif taÅŸÄ±ma **harita.html'i bozar**.
> Pilot sÄ±rasÄ±: uluslararasi â†’ sektorler â†’ kik-kararlar â†’ â€¦ â†’ ihaleler (en son).
>
> ## 5) Ä°dare aÄŸacÄ± â€” PROXY OLMADAN BAÅLANABÄ°LÄ°R
> **VERÄ°YLE Ã‡Ã–ZÃœLDÃœ:** `idare_hiyerarsi_yukle.py` EKAP'a **0 istek** atÄ±yor
> (`httpx` yalnÄ±z SUPABASE_URL'e; `proxy_havuz` importu bile yok) â†’
> `detsis_agaci.json` **15,42 MB / 87.528 kayÄ±t** diskte hazÄ±r. **Proxy yalnÄ±z SAYAÃ‡LARI blokluyor.**
> **âš ï¸ Ã‡ELÄ°ÅMENÄ°N YAKALADIÄI ZORUNLU ADIM:** `idare_kapanis_uret()` MV'yi **REFRESH ETMÄ°YOR**,
> loader da etmiyor; `idare_agac_dallar` **yalnÄ±zca** `idare_hiyerarsi_sayim_mv`'den okuyor â†’
> REFRESH atlanÄ±rsa arayÃ¼z **boÅŸ aÄŸaÃ§** render eder. AdÄ±m 1 ve 2 aynÄ± iÅŸlemde olmalÄ±.
> **âš ï¸ TEÅHÄ°S KURALI DÃœZELTMESÄ°:** boÅŸ gÃ¶vdeyle Ã§aÄŸrÄ±lan `idare_agac_yol`/`_ara`/
> `idare_alt_agac_detsis` **PGRST202** dÃ¶nÃ¼yor (zorunlu parametreleri var) â€” bu
> "fonksiyon yok" DEMEK DEÄÄ°L. YanlÄ±ÅŸ alarm Ã¼retmesin.
> **SÄ±ra:** loader `--kapanis` â†’ **MV REFRESH CONCURRENTLY** â†’ `kurum-analiz.html:378`'e
> "Liste | AÄŸaÃ§" sekmesi (mevcut liste bloÄŸuna DOKUNMA, kardeÅŸ div) â†’ sayaÃ§ sÃ¼tunlarÄ±nÄ±
> **bayrakla KAPALI baÅŸlat** (0 gÃ¶stermek "bu kurumun hiÃ§ ihalesi yok" yalanÄ±) â†’
> `LIMIT 500` kÄ±rpmasÄ±nÄ± yÃ¼zeye Ã§Ä±kar â†’ "BaÄŸlantÄ±sÄ±z Kurumlar" (%20, 17.329 dÃ¼ÄŸÃ¼m) **ayrÄ±
> dal olarak gÃ¶ster, gizleme** â†’ `run_scraper.sh`'e `idare_kapanis_uret()` + MV REFRESH.
> `ilan_detsis_esle()`'yi cron'a **EKLEME** (boÅŸ `detsis_no` Ã¼zerinde 1,85M satÄ±r boÅŸuna dÃ¶ner).
> â›” `migration_idare_agac_rpc.sql`'i **TEKRAR KOÅMA** â€” iÃ§inde ALTER TABLE var,
> 19 Tem'de ACCESS EXCLUSIVE canlÄ± `ilanlar` okumalarÄ±nÄ± tÄ±kadÄ±. Åema zaten uygulanmÄ±ÅŸ.
>
> ---
>
> ## ğŸ“‹ UYGULAMA SIRASI (gerekÃ§eli)
> | # | Ä°ÅŸ | Neden bu sÄ±rada |
> |---|---|---|
> | 1 | **P0.3 Analiz ekseni** (`etkin_tarih` + `kpi.aktif`) | CanlÄ±da YANLIÅ olan tek ÅŸey; %4,27 â†’ %98,51 |
> | 2 | **Arama Commit 1** (api.js + 7 Ã¶lÃ¼ dosya) | GerÃ§ek kusur, sÄ±fÄ±r gÃ¶rsel risk, baÄŸÄ±msÄ±z |
> | 3 | **RFQ kÃ¶prÃ¼sÃ¼** (4 adÄ±m) | KullanÄ±cÄ± ÅŸikÃ¢yeti doÄŸrudan bu; 26 gÃ¼n sonra bayatlama aynÄ± sÃ¼rÃ¼mde kapanmalÄ± |
> | 4 | **Analiz Faz A** (rozet + payda + mod anahtarÄ±) | Saf frontend, SQL riski yok |
> | 5 | **Arama Commit 2** (ihaleler 3 handler) | "Ã‡ok karÄ±ÅŸÄ±k"Ä±n merkezi; Ã¶nce ILIKE Ã¶lÃ§Ã¼mÃ¼ |
> | 6 | **Ä°dare aÄŸacÄ±** 1-7 | En bÃ¼yÃ¼k Ã¼rÃ¼n kazancÄ±, proxy'siz biter; ama en Ã§ok yeni kod |
> | 7 | **Ticaret** ayrÄ± tablo + script | CanlÄ±ya sÄ±fÄ±r dokunuÅŸ; Ã¼rÃ¼n deÄŸeri onay bekliyor |
> | 8 | **Analiz Faz B** (`ihale_butce_mv`) | En yÃ¼ksek regresyon riski (misafir 42501 + timeout) |
> | 9 | Ä°dare sayaÃ§larÄ± / Ticaret pilot | Proxy 402'ye + onaya baÄŸlÄ±, takvime konamaz |
>
> MantÄ±k: **canlÄ± hata â†’ ucuz kullanÄ±cÄ± deÄŸeri â†’ doÄŸruluk â†’ yeni yÃ¼zey â†’ riskli altyapÄ± â†’ bloke iÅŸ.**
> CSS birleÅŸtirme bilinÃ§li olarak sonda: Ã¶lÃ§Ã¼m, kullanÄ±cÄ±nÄ±n ÅŸikÃ¢yetine dokunmadÄ±ÄŸÄ±nÄ± gÃ¶sterdi.
>
> ## â“ GERÃ‡EKTEN KULLANICI KARARI OLANLAR (veriyle Ã§Ã¶zÃ¼lemeyenler)
> 1. **"TÃ¼mÃ¼" varsayÄ±lan mÄ± olacak?** DT (1.490.644) ihaleyi (357.207) **4:1** eziyor â†’
>    varsayÄ±lan "TÃ¼mÃ¼" olursa tÃ¼m kÄ±rÄ±lÄ±m grafikleri fiilen DT grafiÄŸine dÃ¶ner.
> 2. **"TÃ¼mÃ¼"de ortak tarih penceresi?** DT pratikte 2025-2026, ihale 2010'a uzanÄ±yor.
> 3. **RFQ'lar `ihaleler.html`'de de gÃ¶rÃ¼nsÃ¼n mÃ¼?** Kamu ilanÄ± + Ã¶zel RFQ tek listede karÄ±ÅŸsÄ±n mÄ±?
> 4. **RFQ bayatlatma: RPC filtresi mi, cron adÄ±mÄ± mÄ±?** Ä°kincisi daha doÄŸru (listeleri de
>    dÃ¼zeltir) ama **prod cron deÄŸiÅŸikliÄŸi** â†’ ayrÄ± onay.
> 5. **Ticaret "her Ã¼lke" ne demek?** (a) her Ã¼lke Ã— DÃœNYA (partner=0) â€” planlanan;
>    (b) tam ikili matris â‰ˆ **4,8 milyar satÄ±r**, uygulanamaz.

> ## ~~ğŸ›‘ 20 TEM â€” PROXY HAVUZU DÃœÅTÃœ (402)~~ â†’ Ã‡Ã–ZÃœLDÃœ, tarihsel kayÄ±t
> **Bu blok ARTIK GEÃ‡ERSÄ°Z** â€” proxy'ler aynÄ± gÃ¼n geri geldi (100/100 canlÄ±, 0 hata),
> gÃ¼ncel durum iÃ§in yukarÄ±daki "âœ… PROXY Ã‡ALIÅIYOR" bloÄŸuna bak. AÅŸaÄŸÄ±sÄ± yalnÄ±z
> teÅŸhis reÃ§etesi olarak duruyor.
>
> âš ï¸ **KalÄ±cÄ± ders (ayrÄ±, hÃ¢lÃ¢ geÃ§erli):** havuz dÃ¼ÅŸtÃ¼ÄŸÃ¼nde scraper VDS IP'sine
> geri Ã§ekiliyordu â€” 19 Tem gecesi + 20 Tem 02:00 koÅŸusunda **her seferinde ~1.100
> istek Ã¼retim IP'sinden** gitti (havuz Ã¶zetindeki "âš  DÄ°REKT YEDEK" satÄ±rÄ±).
> Bu, kullanÄ±cÄ±nÄ±n aÃ§Ä±k talimatÄ±nÄ± ihlal ediyordu. `PROXY_DIREKT_YEDEK` korumasÄ±
> 20 Tem 10:25'te eklendi, **varsayÄ±lan KAPALI** â€” artÄ±k havuz dÃ¼ÅŸerse kazÄ±ma
> durur, VDS IP'sine dÃ¼ÅŸmez. Bu davranÄ±ÅŸÄ± geri aÃ§ma.
>
> Webshare uÃ§larÄ±nÄ±n **tamamÄ± `402 Payment Required`** dÃ¶nÃ¼yordu (httpx CONNECT
> aÅŸamasÄ±nda; `curl -x` de baÄŸlanamÄ±yor â†’ exit 56). 19 Tem'deki "government sites"
> doÄŸrulamasÄ± ayrÄ± bir olaydÄ± ve Ã§Ã¶zÃ¼lmÃ¼ÅŸtÃ¼ â€” bu **kota/Ã¶deme** kaynaklÄ± yeni bir durum.
>
> **KullanÄ±cÄ± aksiyonu gerekiyor** (Ã¶deme/hesap bilgisi giremem): Webshare panelinde
> bandwidth kotasÄ± + abonelik durumuna bakÄ±lmalÄ±.
>
> **Bloke olan iÅŸler:** 2. madde (1,6M geÃ§miÅŸ ihale tam backfill), 3. madde (DT geÃ§miÅŸ
> yÄ±llar â€” checkpoint sayfa 4925'te, `--backfill` ile devam eder).
>
> **Yeniden baÅŸlarken doÄŸrulama:**
> ```bash
> ssh ihale "cd /opt/ihale-platform/backend && set -a && . ./.env && set +a && \
>   HP=\$(echo \$PROXY_LIST|cut -d, -f1) && \
>   curl -s --max-time 20 -x http://\$PROXY_KULLANICI:\$PROXY_SIFRE@\$HP https://api.ipify.org"
> ```
>
> ### 1,6M backfill iÃ§in bÃ¶lÃ¼mleme kararÄ± (araÅŸtÄ±rma sonucu)
> DÃ¼z sayfalama 1,9M kayÄ±tta Ã§Ã¶ker â†’ dilimlemek ÅŸart. **YÄ±l alanÄ± bundle'da bulunamadÄ±**
> (arama modeli lazy-load chunk'ta, `main.*.js` iÃ§inde yok; `Lookup/GetIKNYil` endpoint'i
> aÄŸ kaydÄ±nda var ama alan adÄ± doÄŸrulanmadÄ±). **YÄ±l aramaya gerek yok:** bundle'dan
> doÄŸrulanmÄ±ÅŸ `ihaleIlIdList` + `ihaleTuruIdList` ile **81 il Ã— 4 tÃ¼r = 324 dilim**
> (~6.000 kayÄ±t/dilim) sayfalama derinliÄŸi sorununu Ã§Ã¶zer. Proxy aÃ§Ä±lÄ±nca Ã¶nce bu iki
> alanÄ±n filtrelediÄŸi **0 < sonuÃ§ < toplam** Ã¶lÃ§Ã¼tÃ¼yle doÄŸrulanmalÄ±
> (âš ï¸ "0 sonuÃ§ = filtre Ã§alÄ±ÅŸtÄ±" tuzaÄŸÄ± â€” bkz. `ekap-detsis-idare-tur` hafÄ±za notu).

> ## âœ… 20 TEM â€” ETKÄ°N TARÄ°H: 335K GEÃ‡MÄ°Å Ä°HALE ARAYÃœZE AÃ‡ILDI (canlÄ±da doÄŸrulandÄ±)
> **Sorun:** 356.904 ihalenin 340.538'inde (%95) ilan/teklif/ihale tarihi BOÅ (sonuÃ§
> backfill'inden gelen kayÄ±tlar). Sekme Ã¶lÃ§Ã¼tÃ¼ `son_teklif_tarihi` olduÄŸu iÃ§in bunlar
> **ne GÃ¼ncel'de ne GeÃ§miÅŸ'te** gÃ¶rÃ¼nÃ¼yordu â€” yalnÄ±z SonuÃ§ sekmesinden eriÅŸilebiliyordu.
>
> **`backend/migration_etkin_tarih.sql`** (uygulandÄ±): `etkin_tarih` + `etkin_tarih_kaynak`
> kolonlarÄ±, `etkin_tarih_tazele()`, DESC indeks, misafir kolon-GRANT'Ä±.
> Ä°lk doldurma: `{"kendi_tarihi": 16368, "sonuctan_turetilen": 335212}` â†’ 351.580 dolu,
> 5.324 boÅŸ (bunlarÄ±n baÄŸlÄ± sonuÃ§ kaydÄ± da yok).
>
> âš ï¸ **`ilan_tarihi`'ye YAZILMADI** â€” sonuÃ§ tarihi â‰  ilan tarihi; boÅŸ alanÄ± doldurmak
> "bu ihale ÅŸu tarihte ilan edildi" diye yanlÄ±ÅŸ bilgi Ã¼retirdi. AyrÄ± eksen + kaynak etiketi.
>
> **`ihaleler.html`** (commit `4c45cb9`): GeÃ§miÅŸ kapsamÄ± ve sekme sayacÄ± `etkin_tarih`'e
> geÃ§ti (**11.712 â†’ 346.926**, Ã¶lÃ§Ã¼ldÃ¼), GeÃ§miÅŸ'te varsayÄ±lan sÄ±ralama `etkin_tarih DESC`,
> tarih aralÄ±ÄŸÄ± filtresi GeÃ§miÅŸ'te `etkin_tarih`'e uygulanÄ±yor, kart yalnÄ±z sonuÃ§tan
> tÃ¼retilmiÅŸ tarihi **"SonuÃ§lanma"** diye etiketliyor. Fallback sorgu kolu da gÃ¼ncellendi.
> CanlÄ± doÄŸrulama: sekme "GeÃ§miÅŸ (346.9K)"; 2022 filtresinde kart
> `SONUÃ‡LANMA | 30 Ara 2022 | SON TEKLÄ°F | â€”`.
>
> `run_scraper.sh` gece `etkin_tarih_tazele()` Ã§aÄŸÄ±rÄ±yor â†’ yeni sonuÃ§lar otomatik iÅŸlenir.

> ## ğŸ›ï¸ YARIN (20 TEM) â€” Ä°DARE HÄ°YERARÅÄ°SÄ°: HEM Ä°HALELER HEM DOÄRUDAN TEMÄ°N
> KullanÄ±cÄ±nÄ±n 19 Tem'deki talebi: *"yarÄ±n idareler kÄ±smÄ± yapacaÄŸÄ±z, doÄŸrudan temin ve
> ihaleler kÄ±smÄ±na onu da ekleyeceÄŸiz."* Yani bu iÅŸ TEK sayfalÄ±k deÄŸil â€” **iki liste
> sayfasÄ±nÄ±n ortak filtresi** olarak tasarlanmalÄ±.
>
> **Hedef:** idareleri bakanlÄ±ktan aÅŸaÄŸÄ± doÄŸru sÄ±nÄ±flandÄ±rÄ±p (bakanlÄ±k â†’ baÄŸlÄ± kurum â†’
> il mÃ¼dÃ¼rlÃ¼ÄŸÃ¼ â†’ daire) **Ã¶zelden genele** filtreleme/sÄ±ralama. Referans: ihaleciler.com
> bu ÅŸekilde Ã§ekiyor.
>
> ### âš ï¸ BU BÃ–LÃœM BAYAT â€” GÃœNCEL DURUM Ä°Ã‡Ä°N DOSYANIN EN ÃœSTÃœNDEKÄ° **P1.5**'E BAK
> AÅŸaÄŸÄ±daki "uygulama BAÅLAMADI" ifadesi 19 Tem'de yazÄ±ldÄ± ve **artÄ±k doÄŸru deÄŸil**:
> o tarihten sonra hiyerarÅŸi tablosu + kapanÄ±ÅŸ tablosu + sayaÃ§ MV'si + 4 aÄŸaÃ§ RPC'si
> yazÄ±ldÄ± ve **prod'a uygulandÄ±** (20 Tem'de `42501` probuyla doÄŸrulandÄ±).
> Madde 2'deki `hiyerarsi_yolu` kolonu ise mimari deÄŸiÅŸiklikle **gereksizleÅŸti**
> (yerine `idare_ata_torun` kapanÄ±ÅŸ tablosu geldi). Kalan gerÃ§ek eksik: veri kapsamasÄ±
> (%32,3, proxy 402 ile bloke) ve arayÃ¼z (%0).
>
> **AraÅŸtÄ±rma TAMAM (18 Tem), ~~uygulama BAÅLAMADI~~ â†’ ÅŸema uygulandÄ±, veri+arayÃ¼z eksik.**
> Kaynak: EKAP DETSÄ°S aÄŸacÄ± â€”
> `DetsisAgaci` 87.528 kayÄ±t, eÅŸleÅŸtirme anahtarÄ± **`idareKodList=[idareId]`**.
> Detaylar + 3 tuzak (idareKod â‰  detsisNo Â· 0-sonuÃ§ â‰  filtre Ã§alÄ±ÅŸtÄ± Â· ad-join ambigÃ¼)
> iÃ§in bkz. hafÄ±za notu `ekap-detsis-idare-tur`.
>
> ### Uygulama sÄ±rasÄ± (Ã¶neri)
> 1. DETSÄ°S aÄŸacÄ±nÄ± yerel tabloya aynala (BFS ile tam aÄŸaÃ§) â†’ `detsis_agaci`
> 2. `ilanlar.detsis_no` + `hiyerarsi_yolu` kolonlarÄ± (DT tarafÄ±nda da aynÄ±sÄ±)
> 3. Her iki sayfaya ortak "Ä°dare TÃ¼rÃ¼ / Ãœst Kurum" filtresi â€” **tek bileÅŸen, iki sayfa**
> 4. `idareler.html`'de aÄŸaÃ§ gÃ¶rÃ¼nÃ¼mÃ¼ (drill-down)
>
> âš ï¸ DT tarafÄ±nda idare filtresi ÅU AN Ã¼yelere Ã¶zel (misafirde maskeli) â€” hiyerarÅŸi
> filtresi eklenirken bu ayrÄ±m korunmalÄ±, yoksa maskeleme delinir.

> ## âœ… 19 TEMMUZ â€” DOÄRUDAN TEMÄ°N: 5 DÃœZELTME (hepsi yerelde doÄŸrulandÄ±)
> KullanÄ±cÄ±nÄ±n haritadan `?il=ANKARA` ile DT'ye gelip gÃ¶rdÃ¼ÄŸÃ¼ Ã¼Ã§ hata + iki istek.
>
> ### 1. Haritadan gelince yanlÄ±ÅŸ sekme â€” `dogrudan-temin.html`
> `?il=` bloÄŸu sekmeyi `'tumu'`ya Ã§ekiyordu (harita TOPLAM sayarken doÄŸruydu). Harita
> 18 Tem'de AKTÄ°F sayÄ±ma geÃ§ince popup "6K" derken liste 115K gÃ¶steriyordu â†’ `'guncel'`.
>
> ### 2. Sekme sayaÃ§larÄ± global sayÄ±yordu â€” asÄ±l ÅŸikÃ¢yet
> Ankara seÃ§iliyken "GÃ¼ncel 96K" yazÄ±yordu (Ã¼lke geneli). ArtÄ±k **aktif filtrelerin
> kapsamÄ±nda** sayÄ±lÄ±yor: Ankara â†’ 6K/109K/115K, liste 6.291. Uygulama:
> - `filtreleriUygula(query, {sekmeUygula})` â€” sekme kapsamÄ± opsiyonel oldu
> - `sekmeSayaclariYukle()` â€” **imza cache'i** (sekme deÄŸiÅŸimi sorgu ATMAZ: Ã¶lÃ§Ã¼ldÃ¼,
>   sekme=1 istek / filtre=4 istek) + yarÄ±ÅŸ korumasÄ± + `sayimYapilabilirMi()` kapÄ±sÄ±
> - `istatistikYukle`'den 2 gereksiz sorgu kalktÄ± (aÃ§Ä±lÄ±ÅŸta 6â†’4 head-count)
> - âš ï¸ Panelden **tek ham durum** seÃ§ilince sekme kapsamÄ± hiÃ§ uygulanmÄ±yor (mevcut
>   bilinÃ§li davranÄ±ÅŸ) â†’ Ã¼Ã§ sekme de AYNI listeyi gÃ¶sterir, bu yÃ¼zden Ã¼Ã§ sayaÃ§ da
>   aynÄ± rakamÄ± yazÄ±yor. FarklÄ± yazmak yalan olurdu.
> - Topbar sayacÄ±na **"(tÃ¼m veri)"** eklendi â€” o global kalÄ±yor, karÄ±ÅŸmasÄ±n.
>
> ### 3. DT kartlarÄ± tÄ±klanamÄ±yordu â†’ **YENÄ° `dt-detay.html`**
> Kart `<a>` ile SARILMADI (iÃ§inde `<a class="dt-idare">` + `<button>` var â†’ iÃ§ iÃ§e
> anchor); "stretched link" deseni: mutlak konumlu `.dt-kart-link` + etkileÅŸimli
> Ã¶ÄŸeler `z-index:2`. DoÄŸrulandÄ±: kart gÃ¶vdesi linke, yÄ±ldÄ±z yÄ±ldÄ±za gidiyor.
> Sayfa: baÅŸlÄ±k/rozetler/takip/paylaÅŸ Â· duyuru bilgileri Â· **sonuÃ§ kartÄ±**
> (`dogrudan_temin_sonuclari`, Ã§ok kalemliyse toplam) Â· EKAP notu Â· ilgili aramalar.
> - Maskeleme korundu: `idare` ve `kazanan_firma` yalnÄ±z Ã¼yeye; misafirde `ğŸ”’ ***`
>   (gizli pencerede doÄŸrulandÄ±, konsolda 42501 YOK). `select('*')` ve token kolonlarÄ±
>   ASLA seÃ§ilmiyor.
> - `<meta robots="noindex,follow">` â€” 1,49M kayÄ±t Ã— URL crawl patlamasÄ±nÄ± Ã¶nler.
> - `dashboard.html` (2) + `takipte.html` (1) derin linkleri yeni sayfaya Ã§evrildi.
>
> ### 4. DT "DetaylÄ± Ara" paneli ihaleler.html gÃ¶rÃ¼nÃ¼mÃ¼ne getirildi
> Sadece GÃ–RSEL dil taÅŸÄ±ndÄ±, davranÄ±ÅŸ korundu (DT anÄ±nda uyguluyor, ihaleler butonla â€”
> DT'ninki daha iyi). Ã–lÃ§Ã¼lerle doÄŸrulandÄ±: panel 16px 20px/radius 10px, etiket
> 11px/600/.08em, input radius 6px, gridâ†’flex, Ã§ipler 20px radius. `Filtrele` butonu
> ve idare kutusuna Enter desteÄŸi eklendi. **HiÃ§bir id deÄŸiÅŸmedi** (6 URL bloÄŸu +
> 6 fonksiyon bu id'leri okuyor).
>
> ### 5. ihaleler.html sÄ±ralama â€” istenen zaten VARDI, etiket yanlÄ±ÅŸtÄ±
> "En Yeni" seÃ§eneÄŸi zaten `ilan_tarihi DESC` yapÄ±yordu â†’ **"Ä°lan Tarihi â†“ (Yeni â†’ Eski)"**
> olarak aÃ§Ä±k yazÄ±ldÄ±. "Son Teklif â†‘" â†’ "(YakÄ±n â†’ Uzak)".
> ğŸ”µ Ä°STENÄ°RSE AÅŸama 2: "Sisteme Yeni DÃ¼ÅŸen" (`olusturulma DESC`) â€” **Ã–N KOÅUL**
> `CREATE INDEX CONCURRENTLY idx_ilanlar_olusturulma`; indeks YOK, onsuz timeout eder.
>
> ### ğŸ” YAN BULGU â€” `yayin_tarihi` (E8) etiketi yanÄ±ltÄ±cÄ±ydÄ±, dÃ¼zeltildi
> CanlÄ± veriyle Ã¶lÃ§Ã¼ldÃ¼ (1000 + 500 kayÄ±t Ã¶rneklem): E8, kaydÄ±n **o anki** duyurusunun
> yayÄ±m tarihi. Aktif kayÄ±tlarda `yayin > ihale` oranÄ± **%0** (doÄŸru), sonuÃ§lananlarda
> **%58** â€” Ã§Ã¼nkÃ¼ orada E8 = SONUÃ‡ duyurusunun tarihi. Hepsine "YayÄ±n" demek yanlÄ±ÅŸtÄ±;
> artÄ±k sonuÃ§lananlarda "SonuÃ§ duyurusu" / "SonuÃ§ Duyurusu Tarihi" yazÄ±yor.
> **Veri hatalÄ± DEÄÄ°L, etiket hatalÄ±ydÄ±** â€” E8 eÅŸleÅŸmesi doÄŸru.
>
> ### ğŸ”´ AÃ‡IK KALAN (bu oturumdan)
> - ğŸŸ¡ **TOKEN AÃ‡IÄI â€” migration YAZILDI, prod'a UYGULANMADI:**
>       `backend/migration_dt_token_authenticated.sql` (commit `e9bc6e1`).
>       `dogrudan_temin_ilanlari` Ã¼zerinde `GRANT SELECT ... TO authenticated` tablo
>       geneliydi â†’ `dt_ihale_token`/`dt_idare_token` her Ã¼yeye aÃ§Ä±ktÄ±.
>       `migration_dt_kazanan.sql:24-26` yorumu aksini varsayÄ±yordu (YANLIÅ).
>       Migration kendi kendini doÄŸruluyor, baÅŸarÄ±sÄ±zsa COMMIT etmiyor. Ã‡alÄ±ÅŸtÄ±r:
>       `docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_token_authenticated.sql`
>       Sonra dosya sonundaki **curl doÄŸrulamalarÄ±nÄ± atlama** (Ã¶zellikle B ÅŸÄ±kkÄ±:
>       Ã¼ye token'Ä±yla token kolonu Ã§ekmeyi dene, 401 gelmeli).
> - [ ] DT tam taramasÄ± hÃ¢lÃ¢ eksik (`yayin_tarihi` kayÄ±tlarÄ±n ~%1'inde dolu) â€” proxy
>       402'den dÃ¼ÅŸtÃ¼; baÅŸka oturum `7f25615` ile direkt-mod geri Ã§ekilmesi ekledi.
> - âœ… `lot_sayisi` + `idare_tur` gece tazelemesi `run_scraper.sh`'e eklendi (`c021157`).
>
> ### âœ… 19 TEM EK â€” Ä°KÄ° MIGRATION PROD'A UYGULANDI + CANLI DOÄRULANDI
> 1. **`migration_dt_token_authenticated.sql`** â€” `authenticated`a 18 kolon GRANT
>    (2 token hariÃ§). Ãœyeler artÄ±k `dt_ihale_token`/`dt_idare_token` Ã§ekemiyor.
> 2. **`migration_idare_tur_anon_grant.sql`** â€” CANLI HATA kapatÄ±ldÄ±: yeni "Ä°dare
>    TÃ¼rÃ¼" filtresi misafirde 42501 verip listeyi Ã¶ldÃ¼rÃ¼yordu (kolon-GRANT sonradan
>    eklenen kolona geniÅŸlemiyor; WHERE'de kullanmak da SELECT yetkisi ister).
>
> CanlÄ± curl doÄŸrulamasÄ± (9/9 geÃ§ti): token'lar 401 Â· `idare_tur` 200 Â·
> `idare`/`kazanan_firma` maskesi 401 Â· misafir liste akÄ±ÅŸÄ± 200.
> TarayÄ±cÄ±: `?il=ANKARA` â†’ GÃ¼ncel sekmesi, 6K/109K/115K, liste 6.290, kart linki
> `dt-detay?dt_no=â€¦`, idare maskeli, konsol temiz.
>
> ### ğŸŸ¡ Ä°DARE TÃœRÃœ FÄ°LTRESÄ° â€” KAPSAM UYARISI (Ã¶lÃ§Ã¼ldÃ¼ 19 Tem)
> `idare_tur` dolu oranÄ±: **DT %23** (345.453/1.490.644) Â· **Ä°haleler %12,5**
> (44.569/356.904). 14 seÃ§eneÄŸin hepsinde veri VAR (Ã¶lÃ¼ seÃ§enek yok) ama filtre
> uygulandÄ±ÄŸÄ±nda sÄ±nÄ±flandÄ±rÄ±lmamÄ±ÅŸ kayÄ±tlar sessizce dÃ¼ÅŸÃ¼yor. Gece tazelemesi
> artÄ±k baÄŸlÄ± (`c021157`) â†’ kapsam her gece artacak. Kapsam yÃ¼kselene kadar
> dropdown'a "sÄ±nÄ±flandÄ±rÄ±lmÄ±ÅŸ kayÄ±tlar" ipucu dÃ¼ÅŸÃ¼nÃ¼lebilir.

> ## ğŸŒ™ 18 TEMMUZ AKÅAMI â€” GECE TARAMASI BEKLENÄ°YOR (sabah kaldÄ±ÄŸÄ±mÄ±z yer burasÄ±)
> Proxy havuzuna **4 scraper'Ä±n 3'Ã¼** baÄŸlandÄ± ve push edildi: `kik_backfill`,
> `ekap_sonuc_backfill` (async), `ekap_sonuc_scraper` (async). Hepsi gerÃ§ek EKAP/KÄ°K'e
> karÅŸÄ± 100 proxy ile doÄŸrulandÄ±. `dt_kazanan_scraper` + `ekap_dogrudan_temin_scraper`
> zaten baÄŸlÄ±ydÄ±.
>
> **`ekap_scraper` BÄ°LEREK BEKLETÄ°LDÄ°.** GerekÃ§e: (1) Ã¼Ã§ deÄŸiÅŸikliÄŸi tek gecede izole test
> etmek, suÃ§luyu ayÄ±rt edebilmek; (2) ana ilan akÄ±ÅŸÄ± ondan geliyor, en riskli dosya â€”
> diÄŸerleri saÄŸlam Ã§Ä±ktÄ±ktan sonra ellenmeli; (3) doÄŸru hÄ±z tavanÄ±nÄ± tahminle deÄŸil bu
> gecenin Ã¶lÃ§Ã¼mÃ¼yle koymak.
>
> ### ğŸ”´ `ekap_scraper` Ä°Ã‡Ä°N Ã‡Ã–ZÃœLMESÄ° GEREKEN Ä°KÄ° SORUN
> 1. **`post()` dÄ±ÅŸarÄ±dan import ediliyor** â€” `ilan_metni_backfill.py:44` ve
>    `ekap_ilan_metni_sonda.py:27` `from ekap_scraper import post` yapÄ±p ona
>    `httpx.AsyncClient` geÃ§iriyor. Ä°lk parametrenin anlamÄ± deÄŸiÅŸirse o iki script
>    **Ã§alÄ±ÅŸma anÄ±nda** (import anÄ±nda deÄŸil) `AttributeError: 'AsyncClient' object has
>    no attribute 'istek'` ile kÄ±rÄ±lÄ±r. Ya Ã§alÄ±ÅŸma-anÄ± tip ayrÄ±mÄ± (`hasattr(x,'istek')`)
>    ya da ayrÄ± bir `post_havuz()` adÄ± gerekiyor.
> 2. **HÄ±z regresyonu** â€” ÅŸu an 8 paralel Ã— ihale baÅŸÄ±na 2-3 istek â‰ˆ 20-60 istek/sn.
>    Havuzun varsayÄ±lan tavanÄ± 600/dk = 10/sn, yani baÄŸlanÄ±rsa gece taramasÄ± YAVAÅLAR.
>    Bu dosyaya ayrÄ± `kuresel_rpm` verilmeli â€” rakam bu gecenin loglarÄ±ndan Ã§Ä±kacak.
>
> ### â˜€ï¸ SABAH Ä°LK Ä°Å â€” bu komutun Ã§Ä±ktÄ±sÄ±na bakÄ±lacak
> ```
> ssh ihale "cd /opt/ihale-platform/logs && echo '=== HAVUZ OZETLERI ==='; grep -A7 'Proxy havuzu ozeti' scraper.log | tail -40; echo '=== KARANTINA/DUSEN ==='; grep -c karantina scraper.log; grep -c 'proxy d' scraper.log; echo '=== HATALAR ==='; grep -iE 'NameError|Traceback|hata:' scraper.log | tail -15"
> ```
> BakÄ±lacaklar: kaÃ§ IP karantinaya girdi/dÃ¼ÅŸtÃ¼ Â· gerÃ§ek verim Â· `NameError` var mÄ±
> (Ã¼Ã§ scraperde de closure/NameError tuzaÄŸÄ± vardÄ±, kapatÄ±ldÄ± ama gece koÅŸusu asÄ±l testtir).
>
> ### âš ï¸ BÄ°LÄ°NEN: kÃ¼resel tavan SÃœREÃ‡ BAÅINA
> `PROXY_KURESEL_RPM=600` her Python sÃ¼reci iÃ§in ayrÄ± uygulanÄ±yor, makine geneli deÄŸil.
> Elle baÅŸlatÄ±lan `dt_kazanan_scraper --limit 50000` gece cron'uyla Ã§akÄ±ÅŸÄ±rsa EKAP'a giden
> toplam yÃ¼k 1200/dk'ya Ã§Ä±kar. KullanÄ±cÄ± kararÄ±: **bÄ±rakÄ±ldÄ±** (100 IP'ye yayÄ±lÄ±yor,
> IP baÅŸÄ±na dk'da 12 istek â€” kabul edilebilir). Makine geneli tavan gerekirse dosya
> tabanlÄ± bir kilit/sayaÃ§ gerekir.


> ## ğŸŒ 18 TEMMUZ â€” PROXY HAVUZU: Ä°STEK BAÅINA IP ROTASYONU (CANLI, 2,65x HIZLANMA Ã–LÃ‡ÃœLDÃœ)
> KullanÄ±cÄ±: "bÃ¼tÃ¼n scrap'i VDS IP'ine bÄ±rakma, 100 IP'yi de kullan, riski yay ve daha hÄ±zlÄ± Ã§ek."
>
> **BULUNAN KÃ–K SORUN:** `proxy_config.rastgele_proxy_url()` script baÅŸÄ±na BÄ°R KEZ Ã§aÄŸrÄ±lÄ±yordu â†’
> 50.000 istekli tur baÅŸtan sona TEK IP'den akÄ±yor, havuzun 99'u boÅŸta. Ãœstelik EKAP'a dokunan
> 7 scriptten yalnÄ±z 2'si proxy kullanÄ±yordu. Yani "100 IP aldÄ±k" ama fiilen 1 IP Ã§alÄ±ÅŸÄ±yordu.
>
> **`backend/proxy_havuz.py` (YENÄ°):** istek baÅŸÄ±na round-robin rotasyon Â· IP baÅŸÄ±na soÄŸuma (3sn) Â·
> kÃ¼resel hÄ±z tavanÄ± (600/dk, nezaket sÄ±nÄ±rÄ±) Â· otomatik karantina (3 hataâ†’120sn, 3 karantinaâ†’dÃ¼ÅŸÃ¼r) Â·
> tanÄ±nabilir User-Agent Â· PROXY_LIST boÅŸsa "direkt mod" (aynÄ± arayÃ¼z, kod bozulmaz).
> BaÄŸlantÄ± havuzu: proxy baÅŸÄ±na bir httpx istemcisi (keep-alive korunur; istek baÅŸÄ±na yeni istemci
> aÃ§mak TLS el sÄ±kÄ±ÅŸmasÄ±nÄ± tekrarlardÄ±).
>
> **`backend/proxy_list_hazirla.py` (YENÄ°):** Webshare `ip:port:kullanÄ±cÄ±:ÅŸifre` dosyasÄ±nÄ± .env
> satÄ±rlarÄ±na Ã§evirir (`--env-yaz` ile yerinde gÃ¼nceller, yedek alarak). Webshare IP'leri periyodik
> tazelediÄŸi iÃ§in tekrar kullanÄ±labilir. SÄ±rlarÄ± ekrana basmaz.
>
> ### ğŸ“Š CANLI SONUÃ‡ (Ã¶lÃ§Ã¼ldÃ¼, tahmin deÄŸil)
> | | Ã–nce (tek IP, --rpm 300) | Sonra (100 IP, 600/dk) |
> |---|---|---|
> | yazma hÄ±zÄ± | ~138 satÄ±r/dk | **~367 satÄ±r/dk** |
> | saatlik | ~8.300 | **~22.000** |
> EKAP dtAra testi: 6 istek â†’ 6 farklÄ± proxy â†’ 6/6 HTTP 200. dtAra sayfasÄ± **55 KB** Ã¶lÃ§Ã¼ldÃ¼ â†’
> tÃ¼m 1,49M DT kaydÄ± â‰ˆ **640 MB**, Webshare 250GB/ay kotasÄ±nÄ±n binde Ã¼Ã§Ã¼. **Kota ve IP sayÄ±sÄ±
> sorun deÄŸil** â€” sorun kullanmÄ±yor olmamÄ±zdÄ±.
>
> ### ğŸ”´ AÃ‡IK RÄ°SK â€” IP Ã‡EÅÄ°TLÄ°LÄ°ÄÄ°
> - [ ] **100 IP'nin 100'Ã¼ tek /24 bloÄŸunda** (`166.88.110.0/24`). EKAP subnet bazlÄ± engellerse
>       hepsi BÄ°RDEN dÃ¼ÅŸer; daÄŸÄ±tÄ±m gÃ¶rÃ¼ndÃ¼ÄŸÃ¼nden zayÄ±f. Paket bÃ¼yÃ¼tmek iÃ§in ilk gerÃ§ek gerekÃ§e bu:
>       IP *sayÄ±sÄ±* deÄŸil **Ã§eÅŸitliliÄŸi** gerekiyor. Webshare'de farklÄ± bloklardan IP alÄ±nabiliyor mu bak.
> - [ ] **Lokasyon doÄŸrulanmadÄ±:** kod yorumunda "TÃ¼rkiye" yazÄ±yor ama blok Ã¶yle gÃ¶rÃ¼nmÃ¼yor.
>       TR kamu sitesini yurtdÄ±ÅŸÄ± datacenter IP'lerinden taramak daha dikkat Ã§ekicidir â€” panelden teyit et.
>
> ### â­ AÃ‡IK â€” KALAN SCRAPER'LAR
> - [ ] `ekap_scraper`, `ekap_sonuc_scraper`, `ekap_sonuc_backfill`, `kik_backfill` hÃ¢lÃ¢ DÄ°REKT
>       gidiyor. Havuza baÄŸlanacak. Her birinin istemci kurulumu farklÄ±; aynÄ± turda dÃ¶rdÃ¼nÃ¼ birden
>       deÄŸiÅŸtirip test etmeden gece hattÄ±nÄ± riske atmamak iÃ§in ayrÄ±ldÄ±.
> - [ ] `proxy_config.py` artÄ±k Ã¶lÃ¼ sayÄ±lÄ±r (yalnÄ±z `ekap_firma_probe` kullanÄ±yor) â€” havuza geÃ§ir, sonra sil.
>
> ### âš ï¸ TESTTE YAKALANAN 3 HATA (hepsi VDS'te de patlardÄ±)
> 1. User-Agent'ta TÃ¼rkÃ§e "toplayÄ±cÄ±" â†’ HTTP baÅŸlÄ±klarÄ± latin-1'e kodlanÄ±r, httpx istemci kurarken
>    UnicodeEncodeError. ModÃ¼l hiÃ§ Ã§alÄ±ÅŸmadÄ±. Saf ASCII'ye Ã§evrildi.
> 2. EKAP eski/zayÄ±f TLS cipher istiyor (`DEFAULT@SECLEVEL=1`) â†’ havuz istemcileri bunu kullanmasa
>    her istek TLS'te Ã¶lÃ¼rdÃ¼. `ekap_ssl_baglami()` eklendi.
> 3. `with httpx.Client(...) as client:` bloÄŸu kaldÄ±rÄ±lÄ±nca `enum_haritalari(client)` / `upsert(client)`
>    NameError verecekti â€” client Supabase iÃ§in geri kondu, enum havuza taÅŸÄ±ndÄ±.
>
> ### ğŸ–¥ VDS DURUMU (18 Tem, giriÅŸ banner'Ä±ndan)
> Disk **14,7% / 157 GB** (â‰ˆ134 GB boÅŸ) Â· RAM %26 Â· swap %0 â†’ **bÃ¼yÃ¼tmeye gerek yok.**
> AÃ§Ä±k: `*** System restart required ***` (Ã§ekirdek gÃ¼ncellemesi) + 15 paket gÃ¼ncellemesi (3 gÃ¼venlik).
> Restart sonrasÄ± **kong'u da yeniden baÅŸlat** (bkz. studio-3000-exposure: bayat upstream = 502).


> ## âš¡ 18 TEMMUZ â€” DT DETAYLI ARA + MOD-FARKINDALIK HATA SINIFI (KOD CANLI, indeks migration'Ä± BEKLÄ°YOR)
> KullanÄ±cÄ± bir hata bildirdi ("TÃ¼mÃ¼'de 2 yazÄ±yor, tÄ±klayÄ±nca 0 ihale Ã§Ä±kÄ±yor") ve bir eksik
> istedi ("DT'yi de ihaleler gibi detaylÄ± aramaya sokmak lazÄ±m, aksi halde Ã§ok yetersiz").
> Bildirilen hata tek bir Ã¶rnekmiÅŸ â€” **aynÄ± sÄ±nÄ±ftan 6 tane daha** Ã§Ä±ktÄ±.
>
> **MOD-FARKINDALIK HATA SINIFI.** Kart baÄŸlantÄ±larÄ± sayÄ±mlardan Ã–NCE, `if (modIhale)` dalÄ±nda
> kuruluyordu. `tumu` modunda `modIhale` de `true` olduÄŸu iÃ§in kartlar BÄ°RLEÅÄ°K sayÄ± gÃ¶sterip
> linki koÅŸulsuz ihaleler'e veriyordu. DoÄŸru hedef ancak hangi tarafta kaÃ§ kayÄ±t olduÄŸu
> bilinince seÃ§ilebilir. Politika `modLinkKur()` iÃ§inde tek yere alÄ±ndÄ±:
> bir taraf 0 â†’ doÄŸrudan dolu tarafa; ikisi de dolu â†’ seÃ§im popup'Ä±; sayÄ± bilinmiyorsa
> (trend barlarÄ± â€” `.limit` doygunluÄŸu var) sayÄ±sÄ±z popup.
> DÃ¼zeltilenler: `stat-eklendi`, `kpi-card-aktif`, `kpi-card-buyuk`, `stat-kazanim`,
> `trend-link`, `kategori-link`, `son-eklenen-link`, `kurumlar-link` (bu sonuncusu HÄ°Ã‡ atanmÄ±yordu).
>
> **DT DETAYLI ARA** (`dogrudan-temin.html`): idare (Ã¼yeye Ã¶zel) / durum / tarih aralÄ±ÄŸÄ± /
> dokÃ¼manlÄ± + hÄ±zlÄ± tarih Ã§ipleri + aktif filtre Ã§ipleri + "Neden bazÄ± filtreler yok?" notu.
> DT'de karÅŸÄ±lÄ±ÄŸÄ± olmayan hiÃ§bir alan uydurulmadÄ±; yaklaÅŸÄ±k maliyet, ihale usulÃ¼, sÄ±nÄ±r deÄŸer,
> OKAS, kazanan firma/bedel ve yayÄ±n tarihi (%1 dolu) iÃ§in gerekÃ§eler panele yazÄ±ldÄ±.
> Yeni URL parametreleri: `sekme, ara, tur, durum, dokuman, detayli, tarihBas, tarihBit`.
>
> **`takipte.html`'e DT bÃ¶lÃ¼mÃ¼** â€” dashboard kartÄ± ihale+DT sayarken sayfada DT yoktu
> (kart "5", liste 3). KullanÄ±cÄ± "kartÄ± daraltma, sayfayÄ± tamamla" dedi.
>
> ### ğŸ”´ YOL AÃ‡ILAN HATALAR (hepsi kapatÄ±ldÄ±, ders niteliÄŸinde)
> - **`durum` seÃ§imi statement timeout Ã¼retiyordu (57014).** Panelden durum seÃ§ilince sekmenin
>   grup filtresiyle AND'leniyordu â†’ "GÃ¼ncel sekmesi + SonuÃ§ durumu" Ã§eliÅŸkisi. PlanlayÄ±cÄ±
>   Ã§eliÅŸkiyi eleyemeyip 1,49M satÄ±rda sayÄ±ma giriyordu. Tek durum seÃ§imi artÄ±k sekme kuralÄ±nÄ± ezer.
> - **`?tarihBas` Ã§ift uygulanÄ±yordu** â€” hem modÃ¼l deÄŸiÅŸkenine hem panel alanÄ±na yazÄ±lÄ±yordu,
>   Ã§ipler Ã§ift gÃ¶rÃ¼nÃ¼yordu. Tek durum kaynaÄŸÄ± = panel alanÄ±.
> - **`?idare=` sessizce YANLIÅ sonuÃ§ veriyordu** â€” serbest arama kutusuna yazÄ±lÄ±yordu, misafirde
>   arama yalnÄ±z `baslik`'te Ã§alÄ±ÅŸtÄ±ÄŸÄ± iÃ§in kurum adÄ± baÅŸlÄ±kta geÃ§miyorsa liste boÅŸ Ã§Ä±kÄ±yordu.
> - **"Toplam KazanÄ±m" misafirde DT'yi hiÃ§ saymÄ±yordu** â€” bugÃ¼nkÃ¼ maskeleme dÃ¼zeltmesinin yan
>   etkisi: `.not('kazanan_firma','is',null)` WHERE'de de yetki istediÄŸi iÃ§in 42501 dÃ¶nÃ¼yor,
>   Supabase client hata nesnesi dÃ¶ndÃ¼rdÃ¼ÄŸÃ¼ iÃ§in count `null` â†’ sayaÃ§ SESSÄ°ZCE 0. `kazanan_bedel`
>   (anon'a aÃ§Ä±k, aynÄ± kaydÄ± iÅŸaret eder) ile deÄŸiÅŸtirildi. **Ders: maskeli kolonu WHERE'de
>   kullanan her sayaÃ§ sessizce sÄ±fÄ±rlanÄ±r â€” hata gÃ¶rÃ¼nmez.**
>
> ### â­ AÃ‡IK
> - [ ] **`backend/migration_dt_index.sql` VDS'te uygulanmalÄ±.** CanlÄ±da Ã¶lÃ§Ã¼ldÃ¼: `kategori` â†’
>       HTTP 522 / ~20 sn, `tur` â†’ 38 sn (kÄ±yas: indeksli `il` 1,6 sn). Bu, detaylÄ± aramadan
>       BAÄIMSIZ mevcut bir hata â€” mevcut dropdown'lar da bu yÃ¼zden yavaÅŸ.
> - [ ] **`stat-kazanim` sayÄ±/hedef evreni uyuÅŸmuyor:** sayÄ± `dogrudan_temin_sonuclari`'ndan
>       (kapsam ~%1,8 â€” 26.214/1,49M), hedef durum-bazlÄ± sonuÃ§ listesi (1,39M). Backfill
>       kapsamÄ± yÃ¼kselince yeniden deÄŸerlendir. Åimdilik yalnÄ±z `dt` modundaki yanlÄ±ÅŸ sayfa hatasÄ± kapatÄ±ldÄ±.
> - [ ] **`BÃ¼yÃ¼k Ä°hale (â‚º43M+)` kavram karÄ±ÅŸÄ±mÄ±** â€” ihalede yaklaÅŸÄ±k maliyet, DT'de kazanan bedel.
>       KullanÄ±cÄ± kararÄ±: backfill bitene kadar bekletilecek.
> - [ ] **`satinalma_talepleri.olusturan_user_id`** (bkz. anon denetimi maddesi) ve
>       **`ilanlar_sonuc` view'Ä±nÄ±n bozuk LEFT JOIN'i** hÃ¢lÃ¢ aÃ§Ä±k.
> - [ ] Dashboard alt yarÄ±sÄ± (`ilanlariYukle`, `sonGorulenlerYukle`, `enIyiEslesmelerYukle`)
>       mod-farkÄ±ndalÄ±klÄ± DEÄÄ°L â€” DT modunda hÃ¢lÃ¢ ihale gÃ¶steriyor. Ya DT'lileÅŸtir ya da
>       bÃ¶lÃ¼m baÅŸlÄ±ÄŸÄ±na "yalnÄ±z ihaleler" notu koy.
> - [ ] `(tur, tarih DESC)` sonrasÄ± `baslik` trigram indeksi â€” serbest arama hÃ¢lÃ¢ seq-scan.

> ## ğŸ”´ 18 TEMMUZ â€” ANON MASKELEME DENETÄ°MÄ°: 2 KÃ–K NEDEN, 5 NESNE KAPATILDI (migration'lar VDS'te BEKLÄ°YOR)
> DT migration'larÄ± canlÄ±ya alÄ±ndÄ±ktan **sonra** yapÄ±lan doÄŸrulamada, kendi yazdÄ±ÄŸÄ±m maskelemenin
> etkisiz olduÄŸu Ã§Ä±ktÄ±. Oradan baÅŸlayan denetim (61 nesne, Ã§ok-ajanlÄ±, her bulgu ayrÄ± ajanla
> Ã§Ã¼rÃ¼tmeye Ã§alÄ±ÅŸÄ±ldÄ±) Ã¶nceden var olan daha bÃ¼yÃ¼k bir deliÄŸi de ortaya Ã§Ä±kardÄ±.
>
> **KÃ–K NEDEN A â€” varsayÄ±lan ayrÄ±calÄ±k kalÄ±ntÄ±sÄ±.** Self-hosted Supabase'de
> `ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES TO anon` yÃ¼rÃ¼rlÃ¼kte. Bu yÃ¼zden `public`
> ÅŸemasÄ±nda **yeni oluÅŸturulan her tablo VE materialized view doÄŸuÅŸtan tablo-geneli anon SELECT
> yetkisi alÄ±r.** SonuÃ§: sadece `GRANT SELECT (kolon listesi) ... TO anon` yazmak **maskeleme
> YAPMAZ** â€” kolon-GRANT yetkiyi daraltmaz, ekler. Ã–nce `REVOKE SELECT ... FROM anon` ÅŸart.
> DoÄŸru kalÄ±p `migration_anon_maske.sql`'de zaten vardÄ±; yeni dosyalara taÅŸÄ±nmadÄ±.
> Maskeleme **opt-in**: o dosyada adÄ± geÃ§meyen tablo korunmuyor.
>
> **KÃ–K NEDEN B â€” view sahip-yetkisi (daha sinsi).** PG view'larÄ± varsayÄ±lan olarak
> `security_invoker` DEÄÄ°L; view'i sorgulayanÄ±n deÄŸil **sahibinin** yetkisiyle Ã§alÄ±ÅŸÄ±r. Bu yÃ¼zden
> taban tablodaki kolon-REVOKE'larÄ± view Ã¼zerinden **hiÃ§ uygulanmaz**. `ilanlar`'da maskeleme
> kusursuz Ã§alÄ±ÅŸÄ±rken aynÄ± kolonlar `ilanlar_sonuc` view'Ä±ndan serbestÃ§e okunuyordu.
>
> **`backend/migration_dt_anon_fix.sql`** (benim aÃ§tÄ±ÄŸÄ±m delikler):
> - `dt_idare_ozet_mv` â€” KRÄ°TÄ°K, aktif sÄ±zÄ±ntÄ±ydÄ±. 38.105 satÄ±r idare adÄ± misafire aÃ§Ä±ktÄ± ve
>   bilinÃ§li kapattÄ±ÄŸÄ±m `dt_idare_sayim()` RPC'sini tamamen baypas ediyordu. KardeÅŸ nesne
>   `idare_ozet_mv` aynÄ± sorguda 401 dÃ¶nÃ¼yor â†’ kalÄ±p farkÄ± buradan yakalandÄ±.
> - `dogrudan_temin_sonuclari` â€” YÃœKSEK ama **latent**: `kazanan_firma`/`yuklenici_id`/
>   `enc_sozlesme_id` aÃ§Ä±ktÄ±, tablo 0 satÄ±r olduÄŸu iÃ§in henÃ¼z sÄ±zÄ±ntÄ± yok. **Kazanan/bedel
>   backfill'i BU DÃœZELTMEDEN Ã–NCE koÅŸulursa anÄ±nda aktif sÄ±zÄ±ntÄ±ya dÃ¶ner.**
> - `dt_takipler` â€” ORTA. Yetki fazlalÄ±ÄŸÄ±; RLS satÄ±rlarÄ± filtrelediÄŸi iÃ§in fiili ifÅŸa yok.
> - Kaynak migration'lara da REVOKE eklendi ki sÄ±fÄ±rdan kurulumda delik geri gelmesin.
>
> **`backend/migration_anon_maske_v2.sql`** (Ã¶nceden var olanlar, benim deÄŸil):
> - `ilanlar_sonuc` â€” **KRÄ°TÄ°K, 356.904 satÄ±r.** `idare`/`ekap_id`/`ikn` view Ã¼zerinden aÃ§Ä±ktÄ±
>   (kÃ¶k neden B). Frontend kullanÄ±mÄ± SIFIR â†’ dÃ¼z REVOKE hiÃ§bir sayfayÄ± bozmuyor.
> - `kamu_ihaleleri` â€” YÃœKSEK, 172 satÄ±r. Tablo tamamen aÃ§Ä±ktÄ±, anon `idare` Ã¼zerinde
>   filtreleyebiliyordu. GRANT listesi `ozel-ihaleler.html:389-397`'den birebir tÃ¼retildi
>   (WHERE'de kullanÄ±lan kolon iÃ§in de SELECT yetkisi gerekir â€” filtre kolonlarÄ± dahil).
> - `kik_kararlar` â€” ORTA, 97 satÄ±r. `ham_veri` jsonb'si frontend hiÃ§ kullanmadÄ±ÄŸÄ± halde aÃ§Ä±ktÄ±.
>   Kritik deÄŸil Ã§Ã¼nkÃ¼ iÃ§indeki `uzmanTCKN` 97/97 satÄ±rda BOÅ.
>
> ### â­ AÃ‡IK â€” SIRADAKÄ°
> - [ ] **VDS'te uygula** (ikisi de bekliyor; ilk deneme yanlÄ±ÅŸ dizinde koÅŸuldu):
>       `cd /opt/ihale-platform && git pull` sonra `migration_dt_anon_fix.sql` +
>       `migration_anon_maske_v2.sql`. Sonra dosyalarÄ±n sonundaki doÄŸrulama curl'leri.
> - [ ] **`kamu_ihaleleri.idare` â€” Ã¼rÃ¼n kararÄ± bekliyor.** Politika idare'yi misafire kapalÄ±
>       sayÄ±yor ama `ozel-ihaleler.html` misafire aÃ§Ä±k ve KA listesinde idare adÄ±nÄ± hem gÃ¶sterip
>       hem aratÄ±yor. Kapatmak sayfayÄ± iÅŸlevsiz bÄ±rakÄ±r â†’ ÅŸimdilik **bilerek aÃ§Ä±k** bÄ±rakÄ±ldÄ±.
>       Politikaya birebir uyum istenirse doÄŸru iÅŸ REVOKE deÄŸil, sayfaya uyeMi dalÄ± + dar select.
> - [ ] **`satinalma_talepleri.olusturan_user_id`** â€” DÃœÅÃœK. Tek baÅŸÄ±na REVOKE edilemez:
>       `ozel-ihale-detay.html:265` `guvenliKolonlar` dizesi kolonu anon select'ine sabit yazÄ±yor.
>       Ã–nce HTML'den Ã§Ä±kar, sonra REVOKE. Ters sÄ±ra sayfayÄ± "Ä°hale bulunamadÄ±"ya dÃ¼ÅŸÃ¼rÃ¼r.
> - [ ] **`ilanlar_sonuc` view'Ä±nÄ±n LEFT JOIN'i BOZUK** (denetimde yan bulgu, gÃ¼venlikten ayrÄ±):
>       `i.ekap_id = s.ekap_id` hiÃ§ eÅŸleÅŸmiyor â†’ `ihale_sonuclari` kaynaklÄ± tÃ¼m kolonlar
>       356.904 satÄ±rÄ±n TAMAMINDA NULL (`yuklenici_ad`/`sozlesme_bedeli`/`sonuc_tur` count=0).
>       View fiilen yarÄ±m Ã§alÄ±ÅŸÄ±yor. AyrÄ± iÅŸ.
> - [ ] **Yeni tablo eklerken kontrol listesi:** REVOKE + kolon-GRANT yaz, sonra
>       `migration_dt_anon_fix.sql` sonundaki "anon'a tablo-geneli yetkisi kalan nesneler"
>       denetim sorgusunu koÅŸ. Ã‡Ä±kan her satÄ±r bilinÃ§li bir karar olmalÄ±.

> ## ğŸŒ 18 TEMMUZ â€” DASHBOARD: TEK GLOBAL MOD SEÃ‡Ä°CÄ° (TÃ¼mÃ¼/Ä°haleler/DT) + DT-TAKÄ°P MEKANÄ°ZMASI (KOD HAZIR+CANLI DOÄRULANDI, migration'lar VDS'te bekliyor)
> KullanÄ±cÄ± Ã¶nceki turdaki harita mod-dÃ¼ÄŸmesini beÄŸendi ama "her widget'ta ayrÄ± ayrÄ± seÃ§tirmek yersiz â€”
> en Ã¼stte TEK seÃ§tirmelisin" dedi + "TÃ¼mÃ¼ + haritada tÄ±klama" ikilemine "kÃ¼Ã§Ã¼k popup" Ã¶nerimi onayladÄ± +
> kiÅŸisel liste widget'larÄ±nÄ± (Takip/YaklaÅŸan/BÃ¼ltenler/EÅŸleÅŸme/GÃ¶rÃ¼ntÃ¼lenen) da "ÅŸimdi kapsama al" dedi.
> - **"Merhaba, X" baÅŸlÄ±ÄŸÄ±nÄ±n altÄ±na** 3 pill-dÃ¼ÄŸme (ğŸ—ºï¸TÃ¼mÃ¼/ğŸ“‹Ä°haleler/âš¡DoÄŸrudan Temin) â€” TEK kontrol noktasÄ±.
>   `window.dashModSec(mod)` tÃ¼m mod-farkÄ±ndalÄ±klÄ± widget'larÄ± yeniden Ã§izer + `haritaModSec` kÃ¶prÃ¼sÃ¼yle
>   haritayÄ± da senkronlar (harita artÄ±k KENDÄ° 3 dÃ¼ÄŸmesini kaybetti, redundant'tÄ± â€” global'e baÄŸlandÄ±).
> - **Mod-farkÄ±ndalÄ±klÄ± hale getirilenler:** gÃ¼nlÃ¼k-strip (BugÃ¼n Eklendi/Son Teklif/KazanÄ±m), 4 KPI kartÄ±
>   (Aktif/7GÃ¼n/BÃ¼yÃ¼k Ä°hale/Takipteki), trend (7 gÃ¼n), Kategori DaÄŸÄ±lÄ±mÄ±, En Aktif Kurumlar, Son Eklenenler,
>   YaklaÅŸan Son Tarihler. **DT'nin karÅŸÄ±lÄ±ÄŸÄ± olmayan kavramlar UYDURULMADI** â€” "7 GÃ¼n Ä°Ã§inde Bitecek" ve
>   "BugÃ¼n Son Teklif" DT-only modda dÃ¼rÃ¼stÃ§e "â€”" gÃ¶sterir (DT'de sabit teklif-bitiÅŸ tarihi kavramÄ± yok,
>   duyuru bazlÄ±). "BÃ¼yÃ¼k Ä°hale (â‚º43M+)" artÄ±k GERÃ‡EK `dogrudan_temin_sonuclari.kazanan_bedel`'den okuyor â€”
>   bugÃ¼nkÃ¼ DT-kazanan backfill'iyle DOÄRUDAN baÄŸlantÄ±lÄ±, veri geldikÃ§e otomatik dolacak (ÅŸu an 0, dÃ¼rÃ¼st).
> - `backend/migration_dashboard_dt_ozet.sql` (YENÄ°): `dt_kategori_sayim_mv`/`dt_idare_ozet_mv` +
>   RPC'leri â€” mevcut `kategori_sayim`/`idare_sayim` (materialized view deseni, canlÄ± GROUP BY 350K+ satÄ±rda
>   yavaÅŸ/timeout riskliydi) BÄ°REBÄ°R aynÄ± desen, DT'nin 1.48M satÄ±rÄ± iÃ§in tekrarlandÄ±. `idare` kimlik-benzeri
>   olduÄŸu iÃ§in `dt_idare_sayim` da (idare_sayim gibi) anon'a KAPALI. `run_scraper.sh`'nin gece REFRESH
>   zincirine eklendi.
> - **DT-Takip mekanizmasÄ± (yeni kapsam, "ÅŸimdi kapsama al" kararÄ±):** `js/takip.js`'e `window.TakipDT`
>   eklendi â€” mevcut `Takip` ile AYNI API ÅŸekli (liste/var/toggle/sayi/syncFromDB), AYRI depolama
>   (localStorage `dt_takip` + Supabase `dt_takipler` tablosu). `takipler.ilan_id`'nin muhtemel FK'sine
>   karÄ±ÅŸmamak iÃ§in (farklÄ± tablo/anahtar tipi) BÄ°LEREK ayrÄ± tablo â€” kod tabanÄ±nÄ±n tekrarlayan "DT'yi ayrÄ±
>   tut" deseniyle tutarlÄ±. `dogrudan-temin.html`'e â˜†/â˜… takip butonu eklendi (kart baÅŸÄ±na, giriÅŸ ÅŸartsÄ±z â€”
>   misafir localStorage'da tutar, `ihaleler.html`'deki `takibeAl` ile aynÄ± basitlik).
>   `backend/migration_dashboard_dt_ozet.sql` iÃ§inde `dt_takipler` tablosu + RLS (kullanÄ±cÄ± yalnÄ±z kendi
>   satÄ±rÄ±nÄ± gÃ¶rÃ¼r/yazar/siler, anon hiÃ§ yazamaz).
> - **AyrÄ± DT detay sayfasÄ± YOK (bilinÃ§li, kapsam kararÄ±)** â€” `dogrudan-temin.html`'e `?dt_no=` (liste TEK
>   kayda daralÄ±r) ve `?kategori=` URL parametreleri eklendi; "Son Eklenen"/"YaklaÅŸan Son Tarihler"
>   widget'larÄ± DT Ã¶ÄŸelerini bu URL'lerle bu sayfaya yÃ¶nlendirir (yeni bir sayfa mimarisi kurmadan
>   pratik bir "detay gÃ¶rÃ¼nÃ¼mÃ¼" ikamesi).
> - **KiÅŸisel widget'lardan kapsam dÄ±ÅŸÄ± bÄ±rakÄ±lanlar (zaman kÄ±sÄ±tÄ±, aÃ§Ä±kÃ§a not dÃ¼ÅŸÃ¼lÃ¼yor):** KayÄ±tlÄ±
>   Aramalar (BÃ¼ltenlerim â€” saved-search alerts, "mod" kavramÄ±na doÄŸal uymuyor), En Ä°yi EÅŸleÅŸmeler
>   (profil-uyum skorlama motoru DT'ye henÃ¼z uzanmÄ±yor), Son GÃ¶rÃ¼ntÃ¼lenenler (view-history, DT detay
>   sayfasÄ± olmadÄ±ÄŸÄ± iÃ§in iz sÃ¼recek bir yer yok). Bunlar ihale-only kaldÄ± â€” istenirse ayrÄ± iÅŸ.
> - **ğŸ› Yol Ã¼stÃ¼ 2 bug (kendi test sÃ¼recimde bulundu, dÃ¼zeltildi):**
>   1. `js/harita.js`'in ilk Ã§izimi HEP 'toplam' modunda baÅŸlÄ±yordu, dashboard'un global moduna bakmÄ±yordu
>      (kullanÄ±cÄ± Ã¶nce "DT" seÃ§ip sonra haritaya inerse harita yanlÄ±ÅŸ modda aÃ§Ä±lÄ±rdÄ±). KÃ¶k neden ikili:
>      (a) harita.js `window.aktifDashMod`'u okumuyordu â†’ eklendi; (b) dashboard.html'de `let aktifDashMod`
>      ÃœST-SEVÄ°YE bildirimi `window` Ã¶zelliÄŸi OLUÅTURMAZ (JS'in bilinen bir tuzaÄŸÄ± â€” `var` oluÅŸturur, `let`/
>      `const` oluÅŸturmaz) â†’ `window.aktifDashMod = 'tumu'` ÅŸeklinde AÃ‡IKÃ‡A global yapÄ±ldÄ±.
>   2. `yaklaÅŸanBitisYukle()`'nin YENÄ° yazdÄ±ÄŸÄ±m DT dalÄ± `idare` kolonunu select ediyordu â€” `idare` DT
>      tablosunda da anon'a KAPALI (migration_anon_maske.sql) â†’ misafir kullanÄ±cÄ±da TÃœM sorgu 42501 ile
>      Ã§Ã¶kÃ¼yor, "Aktif takip ilanÄ± bulunamadÄ±" diye YANLIÅ boÅŸ durum gÃ¶steriyordu. `idare` select'ten
>      Ã§Ä±karÄ±ldÄ±, `il` ile deÄŸiÅŸtirildi.
>   **Bu ikinci bug'Ä± ararken PRE-EXISTING (benim yazmadÄ±ÄŸÄ±m) bir bulgu daha Ã§Ä±ktÄ±:** aynÄ± hata dashboard.html'in
>   3 ayrÄ± yerinde (`ilanlariYukle`, `enIyiEslesmelerYukle`, `yaklaÅŸanBitisYukle`'nin Ä°HALE dalÄ±) `ilanlar.idare`/
>   `ekap_id` iÃ§in de var â€” misafir kullanÄ±cÄ±larda bu 3 widget da hep boÅŸ/kÄ±rÄ±k. Kapsam dÄ±ÅŸÄ± tutulup
>   `spawn_task` ile ayrÄ± gÃ¶reve dÃ¼ÅŸÃ¼rÃ¼ldÃ¼ (task_7a0462ae).
> - **DoÄŸrulama:** yerel statik sunucu + zorla-render tekniÄŸiyle uÃ§tan uca test edildi. TÃ¼mÃ¼ modu canlÄ±
>   `kpi-aktif=100.708` (ihale+DT toplamÄ±) dÃ¶ndÃ¼; Ä°hale modu `kpi-aktif=4.656`/`kpi-buyuk=846` â€” kullanÄ±cÄ±nÄ±n
>   PAYLAÅTIÄI orijinal ekran gÃ¶rÃ¼ntÃ¼sÃ¼ndeki sayÄ±larla BÄ°REBÄ°R eÅŸleÅŸti (regresyonsuz doÄŸrulama). DT modu
>   `kpi-aktif=96.052`, `kpi-buyuk=0` (backfill henÃ¼z yok, dÃ¼rÃ¼st), `kpi-yaklasan`/`hdr-songun`="â€”" (doÄŸru).
>   `dogrudan-temin.html?dt_no=X` liste tek kayda daraldÄ±, â˜†â†’â˜… takip toggle + localStorage doÄŸrulandÄ±,
>   dashboard'da o kayÄ±t "YaklaÅŸan Son Tarihler"de gÃ¶rÃ¼ndÃ¼ (fix sonrasÄ±). Konsol hatasÄ±z (tÃ¼m turlar).
> - **DEPLOY (VDS):** `git pull` â†’ `docker exec -i supabase-db psql ... < backend/migration_dashboard_dt_ozet.sql`
>   (dt_kategori_sayim/dt_idare_sayim RPC'leri + dt_takipler tablosu iÃ§in) â€” migration Ã¶ncesi de sayfa
>   Ã‡Ã–KMEZ, o widget'lar sadece boÅŸ/hata durumunda kalÄ±r (zaten canlÄ±da bÃ¶yle test edildi).
> - **Cache-bust notu (ders â€” bir Ã¶nceki turda da yaÅŸanmÄ±ÅŸtÄ±):** `js/harita.js` `?v=2`â†’`?v=3`, `js/takip.js`
>   TÃœM 8 sayfada `?v=rot1`â†’`?v=2` yÃ¼kseltildi (CF `max-age=14400` â€” bump edilmezse yeni kod saatlerce
>   Ã¶nbellekte takÄ±lÄ± kalÄ±r, buton/Ã¶zellik "Ã§alÄ±ÅŸmÄ±yor" gibi gÃ¶rÃ¼nÃ¼r).

> ## ğŸ’° 18 TEMMUZ â€” DT KAZANAN/BEDEL: "CAPTCHA ARKASINDA" SANILIYORDU, AÃ‡IK Ã‡IKTI (KOD HAZIR+CANLI DOÄRULANDI, backfill VDS'te bekliyor)
> KullanÄ±cÄ± dashboard "BÃ¼yÃ¼k Ä°hale" kartÄ± tartÄ±ÅŸmasÄ±nda hafÄ±zadaki eski karar hatÄ±rlattÄ±: "kazanan bedelini
> capctcha arkasÄ±ndan Ã§ekebilmemiz lazÄ±m, Gemini ile Ã§Ã¶zeceÄŸini sÃ¶ylemiÅŸtin â€” Ã¶yle ilerlesene". Ã–nce mevcut
> reÃ§eteyi (hafÄ±za: dt-kazanan-captcha) doÄŸrulamak iÃ§in canlÄ± prob yapÄ±ldÄ± â€” **BEKLENMEDÄ°K, Ã‡OK DAHA Ä°YÄ° bir
> sonuÃ§ Ã§Ä±ktÄ±: CAPTCHA hiÃ§ gerekmiyor.**
> - **KanÄ±t zinciri (canlÄ±, adÄ±m adÄ±m):** dtAra liste yanÄ±tÄ±nda E10(dogrudanTeminId)/E11(IdareId) gerÃ§ek
>   token'larÄ± Ã§ekildi â†’ `DogrudanTeminDetay.aspx` sayfasÄ± gerÃ§ekten CAPTCHA'lÄ± (doÄŸrulandÄ±) â†’ ama sayfanÄ±n
>   Angular kontrolcÃ¼sÃ¼ (`dtDetay.js`) veriyi **AYRI, KORUMASIZ bir JSON API'den** Ã§ekiyor:
>   `YeniIhaleAramaData.ashx?metot=dtDetayGetir&idareId=E11&dogrudanTeminId=E10` â†’ bu endpoint **kimliksiz
>   dÃ¼z GET ile, hiÃ§ CAPTCHA Ã§Ã¶zÃ¼lmeden** Ã§alÄ±ÅŸÄ±yor (dtAra/dtEnum ile aynÄ± sÄ±nÄ±f aÃ§Ä±k uÃ§ nokta â€” sayfa
>   korumalÄ±, API deÄŸil). **15 gerÃ§ek kayÄ±tta canlÄ± test: 0 CAPTCHA, 13 dolu kazanan+bedel, 2 boÅŸ (henÃ¼z
>   sonuÃ§lanmamÄ±ÅŸ), 0 hata.** JSON: `SozlesmeBilgileri.SozlesmeBilgisiList[].{IstekliAdi,SozlesmeBedeli,
>   SozlesmeTarihi,EnYuksekTeklif,EnDusukTeklif,EncSozlesmeID}` â€” bir dt_no'da BÄ°RDEN FAZLA kalem olabilir.
> - **Bu, Ã¶nceki maliyet/kÄ±sÄ±t varsayÄ±mÄ±nÄ± tamamen geÃ§ersiz kÄ±lÄ±yor** â€” Gemini/CAPTCHA-Ã§Ã¶zme altyapÄ±sÄ±
>   GEREKMÄ°YOR, asÄ±l kÄ±sÄ±t artÄ±k yalnÄ±z HACÄ°M (aÅŸaÄŸÄ±da).
> - `backend/migration_dt_kazanan.sql` (YENÄ°): `dogrudan_temin_ilanlari`'na `dt_ihale_token`/`dt_idare_token`
>   (E10/E11 â€” anon+authenticated'a KAPALI, yalnÄ±z service_role; frontend'in hiÃ§ ihtiyacÄ± yok, sÄ±zarsa
>   herkes bizim keÅŸfimizi kopyalayÄ±p toplu eriÅŸim kurabilirdi) + `dt_ilan_var_mi`/`dt_dosya_var_mi` +
>   `kazanan_denendi` (ai_kategori_backfill ile aynÄ± "bir kez dene" damgasÄ±) + `idx_dt_ilanlari_durum` +
>   kuyruk partial index. **YENÄ° tablo** `dogrudan_temin_sonuclari` (enc_sozlesme_id UNIQUEâ†’idempotent
>   upsert; anon-maske ihale_sonuclari ile AYNI ilke: kazanan_firma/yuklenici_id kapalÄ±, bedel/tarih aÃ§Ä±k).
>   `migration_anon_maske.sql`'in dinamik "idare hariÃ§ hepsi" DT kolon-listesine token'lar da eklendi
>   (ileride o dosya tekrar koÅŸulursa yanlÄ±ÅŸlÄ±kla aÃ§Ä±lmasÄ±nlar diye).
> - `backend/ekap_dogrudan_temin_scraper.py`: retrofit â€” E10/E11/E13/E14 artÄ±k ATILMIYOR, saklanÄ±yor
>   (Ã¶nceden `kayit_donustur()` bunlarÄ± okuyup Ã§Ã¶pe atÄ±yordu â€” kod zaten "ihtiyaÃ§ olursa Ã§Ã¶zÃ¼lÃ¼r" notunu
>   taÅŸÄ±yordu, bugÃ¼n o gÃ¼n oldu).
> - `backend/dt_kazanan_scraper.py` (YENÄ°): token'lÄ±+denenmemiÅŸ+durum="sonuÃ§ grubu" dt_no'larÄ± seÃ§er, dÃ¼z
>   GET ile dtDetayGetir Ã§aÄŸÄ±rÄ±r, `bedel_parse`/`tarih_iso` (ekap_sonuc_scraper.py'den REUSE, `bedel_parse`
>   "TRY" son eki iÃ§in kÃ¼Ã§Ã¼k bir dÃ¼zeltme aldÄ±) ile ayrÄ±ÅŸtÄ±rÄ±p yazar + `kazanan_denendi` damgalar.
>   --dry-run/--limit/--batch/--rpm, ai_kategori_backfill.py ile aynÄ± CLI/hata-mesajÄ± disiplini.
> - `run_scraper.sh`: gece `dt_kazanan_scraper.py --limit 2000 --rpm 300` eklendi (gÃ¼nlÃ¼k artÄ±mÄ± karÅŸÄ±lar).
>   YOL ÃœSTÃœ: DMO/Jandarma'nÄ±n artÄ±k ANA ilanlar'a yazdÄ±ÄŸÄ±nÄ± belirten stale yorum da dÃ¼zeltildi (16 Tem'de
>   kod deÄŸiÅŸmiÅŸti ama bu dosyadaki aÃ§Ä±klama eski kalmÄ±ÅŸtÄ±).
> - **DoÄŸrulama:** tÃ¼m parÃ§a CANLI EKAP'a karÅŸÄ± test edildi (yerel .env Ã¶lÃ¼ managed DB'yi gÃ¶sterdiÄŸi iÃ§in
>   Supabase yazma testi yapÄ±lamadÄ± â€” script'in kendi HTTP/parse mantÄ±ÄŸÄ± gerÃ§ek 15 kayÄ±tla doÄŸrulandÄ±,
>   syntax+argparse+bedel_parse edge-case'leri ayrÄ±ca test edildi).
> - **KALAN â€” HACÄ°M (kullanÄ±cÄ± VDS'te Ã§alÄ±ÅŸtÄ±racak):**
>   1. `python ekap_dogrudan_temin_scraper.py --reset --max-pages <bÃ¼yÃ¼k>` â€” tarihsel ~1.48M satÄ±rÄ±n
>      E10/E11'ini geri kazanmak iÃ§in TAM yeniden-tarama (CAPTCHA yok, ~11.6K sayfa, saatler sÃ¼rebilir).
>   2. `docker exec -i supabase-db psql ... < backend/migration_dt_kazanan.sql`
>   3. `python dt_kazanan_scraper.py --dry-run` â†’ rakamlar makulse bÃ¼yÃ¼k `--limit`li arka plan turu
>      (nohup, gÃ¼nler sÃ¼rebilir â€” ~1,3M "sonuÃ§" durumlu kayÄ±t, hÄ±zÄ± --rpm ile kendileri ayarlar).
> - **KasÄ±tlÄ± YAPILMADI:** `dogrudan_temin_sonuclari.yuklenici_id` linkleme + `yukleniciler`e DT cirosu
>   katma â€” eski tasarÄ±m kararÄ± ("Ä°HALE cirosuna karÄ±ÅŸtÄ±rma, ayrÄ± dt_* sayaÃ§") hÃ¢lÃ¢ geÃ§erli, ayrÄ± iÅŸ.
> - Bu veri geldikÃ§e dashboard "BÃ¼yÃ¼k Ä°hale" kartÄ± DT modunda da gerÃ§ek sayÄ± gÃ¶sterebilir hale gelecek
>   (aÅŸaÄŸÄ±daki dashboard mod-seÃ§ici iÅŸi bu veriye bel baÄŸlamadan "â€”" ile baÅŸlayabilir, veri akÄ±nca otomatik dolar).

> ## ğŸšª 18 TEMMUZ â€” SIDEBAR HESAP MENÃœSÃœ + Ã‡IKIÅ YAP (âœ… CANLI, 715adf5)
> Saha bulgusu: kullanÄ±cÄ± profiline girdikten sonra **hiÃ§bir yerde Ã§Ä±kÄ±ÅŸ seÃ§eneÄŸi yoktu** â€” oturum kapatÄ±lamÄ±yordu.
> - **YapÄ±ldÄ±:** sol-alt kullanÄ±cÄ± bloÄŸu (avatar/ad/plan) artÄ±k tÄ±klanÄ±nca **hesap menÃ¼sÃ¼** aÃ§Ä±yor (â‹® gÃ¶stergesi eklendi).
>   GiriÅŸli: âš™ï¸ Profil & Ayarlar Â· ğŸ’³ Abonelik Â· ğŸšª **Ã‡Ä±kÄ±ÅŸ Yap**. Misafir: ğŸ”‘ GiriÅŸ Yap Â· âœ¨ Ãœcretsiz KayÄ±t Ol.
> - **Ã‡Ä±kÄ±ÅŸ:** `sb.auth.signOut()` + `localStorage.removeItem('ihale_token')` â†’ `/`. Legacy token DA temizleniyor;
>   kalÄ±rsa login sayfasÄ± kendini "giriÅŸli" sanÄ±p dashboard'a geri atÄ±yordu (bkz. [[iki-auth-sistemi-bounce]]).
> - **MenÃ¼ DOM'da `body`'ye fixed eklenir** â€” sidebar'Ä±n `overflow-y:auto`'su absolute popover'Ä± kÄ±rpÄ±yordu.
> - **DERS (konumlandÄ±rma):** sidebar mobilde `display:none` olduÄŸundan satÄ±rÄ±n rect'i 0Ã—0 gelir; `bottom`'u
>   ondan hesaplayÄ±nca menÃ¼ ekran DIÅINA (top:-92) dÃ¼ÅŸÃ¼yordu. Guard eklendi (gÃ¶rÃ¼nmÃ¼yorsa aÃ§ma) + yukarÄ±
>   sÄ±ÄŸmazsa altÄ±na Ã§evirme + sol kenar viewport'a kÄ±rpma. CanlÄ± Ã¶lÃ§Ã¼m: menÃ¼ satÄ±rÄ±n tam Ã¼stÃ¼nde, tamamen ekran iÃ§inde.
> - **DERS (cache-bust):** ilk sweep `js/sidebar-user.js?v=2?v=rot1` gibi **Ã§ift query** Ã¼retti â€” baÅŸka oturumun
>   koyduÄŸu `?v=rot1` rakam olmadÄ±ÄŸÄ± iÃ§in `(\?v=\d+)?` desenine takÄ±lmamÄ±ÅŸtÄ±. Desen `(\?[^"'\s>]*)?` yapÄ±lÄ±p
>   20 sayfa tek `?v=3`'e normalize edildi. Script `max-age=14400` (4sa) ile servis edildiÄŸinden bu ÅART.

> ## ğŸ—ºï¸ 18 TEMMUZ â€” ANASAYFA MÄ°NÄ° HARÄ°TASI: TOPLAM/Ä°HALE/DT MOD SEÃ‡Ä°CÄ° EKLENDÄ° (KOD HAZIR+DOÄRULANDI, migration VDS'te bekliyor)
> **Ek (aynÄ± gÃ¼n, kullanÄ±cÄ± isteÄŸi):** "Ã¼stte seÃ§me butonu â€” firma isterse DT isterse ihale gÃ¶rsÃ¼n" â€” aÅŸaÄŸÄ±daki
> tÄ±kla-seÃ§ popup'Ä±n YANINA, widget baÅŸlÄ±ÄŸÄ±na 3 pill-dÃ¼ÄŸme eklendi: **ğŸ—ºï¸ TÃ¼mÃ¼ / ğŸ“‹ Ä°haleler / âš¡ DoÄŸrudan Temin**.
> `js/harita.js`: veri (ihale+DT sayÄ±mÄ±, 3 quantile eÅŸik seti) TEK SEFER Ã§ekiliyor; `window.haritaModSec(mod)`
> mevcut Leaflet katmanÄ±nÄ± yeniden fetch YAPMADAN yeniden stiller/baÄŸlar â€” 'TÃ¼mÃ¼'de eski toplam-renk+popup
> davranÄ±ÅŸÄ± aynen kalÄ±r, 'Ä°haleler'/'DoÄŸrudan Temin' seÃ§ilince renk YALNIZ o metriÄŸe gÃ¶re olur ve tÄ±klama
> ARTIK POPUP AÃ‡MAZ, doÄŸrudan ilgili sayfaya gider (`layer.off('click')` + mod'a Ã¶zel `bindTooltip`/`bindPopup`
> veya `unbindPopup()`+`on('click',...)`). Legend baÅŸlÄ±ÄŸÄ± + widget alt yazÄ±sÄ± + dÃ¼ÄŸme aktif-durumu mod'a gÃ¶re.
> **ğŸ› Yol Ã¼stÃ¼ bug (kendi test sÃ¼recimde bulundu, dÃ¼zeltildi):** docblock yorumunda `.il-popup*/.harita-mod-btn`
> yazarken `*/` JS blok-yorumunu ERKEN KAPATTI â†’ geri kalan yorum metni kod olarak parse edilmeye Ã§alÄ±ÅŸÄ±lÄ±p
> `SyntaxError: Unexpected token '.'` ile TÃœM script Ã§Ã¶kÃ¼yordu (harita hiÃ§ Ã§izilmiyordu). `/*` `*/` sayaÃ§
> kontrolÃ¼yle teÅŸhis edildi, boÅŸluk eklenerek dÃ¼zeltildi. **DERS:** yorum metninde `*/` alt dizesi geÃ§en
> herhangi bir ifade (Ã¶r. "A*/B" gibi kÄ±saltma) JS blok yorumunu kÄ±rar â€” CSS/regex Ã¶rnekleri yazarken dikkat.
> AyrÄ±ca bu turda **Read tool'un bir kez bayat/Ã¶nbelleklenmiÅŸ iÃ§erik dÃ¶ndÃ¼rdÃ¼ÄŸÃ¼** gÃ¶zlemlendi (dosya doÄŸru
> haldeyken eski hali gÃ¶sterdi) â€” ÅŸÃ¼pheli bir "dosya deÄŸiÅŸti" bildirimi gÃ¶rÃ¼lÃ¼rse Bash `cat`/`git diff` ile
> DOÄRUDAN diskten Ã§apraz-doÄŸrulama yapÄ±lmalÄ±, Read'e kÃ¶rÃ¼ kÃ¶rÃ¼ne gÃ¼venilmemeli.
> DoÄŸrulama: yerel statik sunucu (python http.server, .claude/launch.json'daki "ihale-platform" config) +
> zorla-render tekniÄŸiyle (IntersectionObserver mock'lanÄ±p modÃ¼l yeniden eval edildi â€” bu sandbox'ta gerÃ§ek
> scroll-tetiklemesi hiÃ§ Ã§alÄ±ÅŸmÄ±yor) 3 modun HEPSÄ° canlÄ± veriyle test edildi: legend/alt-yazÄ±/dÃ¼ÄŸme-aktifliÄŸi
> her modda doÄŸru deÄŸiÅŸti; 'dt' modunda bir ile tÄ±klama gerÃ§ekten `dogrudan-temin?il=KONYA`'ya yÃ¶nlendirdi
> (test sunucusu .html uzantÄ±sÄ±z route'u 404'ledi â€” nginx'li canlÄ±da sorun olmaz, python http.server kÄ±sÄ±tÄ±).

> ## ğŸ—ºï¸ 18 TEMMUZ â€” ANASAYFA MÄ°NÄ° HARÄ°TASI: Ä°HALE+DT TOPLAM RENK + AYRI HOVER SAYIMI + TIKLA-SEÃ‡ POPUP (KOD HAZIR, migration VDS'te bekliyor)
> KullanÄ±cÄ± talebi: dashboard.html'deki "TÃ¼rkiye Ä°hale HaritasÄ±" widget'Ä± yalnÄ±z `ilanlar` sayÄ±sÄ±nÄ± gÃ¶steriyordu.
> DÃ¼nya ticaret haritasÄ±ndaki ihracat/ithalat ayrÄ±mÄ±yla AYNI FÄ°KÄ°R uygulandÄ±: renk=TOPLAM, hover=AYRI, tÄ±k=SEÃ‡Ä°M.
> - `backend/migration_dt_il_sayim.sql` (YENÄ°): `il_sayim()` deseninin `dogrudan_temin_ilanlari` (1.48M satÄ±r,
>   `ilanlar`'Ä±n 4 katÄ±) karÅŸÄ±lÄ±ÄŸÄ± â€” `idx_dogrudan_temin_ilanlari_il` partial indeks + `dt_il_sayim()` RPC
>   (`ALTER FUNCTION SET statement_timeout='20s'` gÃ¼vence payÄ±, Statement Timeout Edge dersiyle tutarlÄ±).
> - `js/harita.js`: `ilSayimGetir()` parametrik hale geldi (rpcAdi/tabloAdi) â†’ hem ihale hem DT sayÄ±mÄ±nÄ±
>   paralel Ã§eker; renk artÄ±k `ihale+dt` TOPLAMINDAN (quantile eÅŸikli); hover tooltip'i ğŸ“‹ Ä°hale / âš¡ DT'yi
>   AYRI satÄ±rlarda + toplamÄ± gÃ¶sterir; tÄ±klama artÄ±k DOÄRUDAN yÃ¶nlendirmiyor â€” Leaflet popup'Ä± iki buton
>   sunuyor ("ğŸ“‹ GÃ¼ncel Ä°haleler" â†’ `ihaleler?il=X`, "âš¡ DoÄŸrudan Temin" â†’ `dogrudan-temin?il=X`), sayÄ±sÄ± 0
>   olan seÃ§enek gÃ¶rsel olarak pasif (disabled, tÄ±klanamaz). RPC yoksa (migration henÃ¼z koÅŸmadÄ±ysa) sayfalÄ±
>   fallback'e sessizce dÃ¼ÅŸer â€” DT iÃ§in CANLIDA TEST EDÄ°LDÄ° (81/81 il kapsÄ±yor, hatasÄ±z).
> - `dogrudan-temin.html`: `?il=` URL parametresi desteÄŸi YOKTU (yalnÄ±z `?idare=` vardÄ±) â€” eklendi.
>   `illeriYukle()` artÄ±k `await`'lenip TAMAMLANDIKTAN sonra param okunuyor (yarÄ±ÅŸ durumu Ã¶nlendi) +
>   `ilSecimGarantiEt()` â€” il, son-5000-kayÄ±t Ã¶rnekleminde yoksa `<option>`'Ä± elle ekleyip seÃ§iyor (haritadan
>   nadir-DT'li bir ile tÄ±klanÄ±rsa dropdown sessizce boÅŸa dÃ¼ÅŸmesin diye).
> - `dashboard.html`: `.il-popup*` + `.leaflet-popup-content-wrapper` karanlÄ±k tema CSS'i (`.il-tooltip` ile
>   aynÄ± "sayfa kendi CSS'ini saÄŸlar" kuralÄ± â€” harita.js modÃ¼lÃ¼ CSS enjekte etmiyor); widget alt yazÄ±sÄ±
>   gÃ¼ncellendi.
> - **DoÄŸrulama:** canlÄ± REST API'ye karÅŸÄ± uÃ§tan uca test edildi (bu sandbox'ta Leaflet/SVG pixel-render
>   gÃ¶rÃ¼lemedi â€” tarayÄ±cÄ± Ã¶nizlemesi bu oturumda `window.innerWidth=0` raporluyor, sayfa/CSS'ten baÄŸÄ±msÄ±z bir
>   ortam kÄ±sÄ±tÄ±; kod mantÄ±ÄŸÄ± bunun yerine gerÃ§ek veriyle doÄŸrulandÄ±): `il_sayim` RPC âœ“, `dt_il_sayim` RPC
>   henÃ¼z yok (beklenen â€” migration deploy edilmedi) â†’ fallback yolu canlÄ± test edildi (81 il, hatasÄ±z);
>   popup HTML Ã¼retimi Ankara/Ä°zmir/Van iÃ§in doÄŸru sayÄ±+URL-encode ile doÄŸrulandÄ±; `dogrudan-temin.html?il=VAN`
>   filtreyi doÄŸru uyguladÄ± (aktifSekme=tumu, VAN kaydÄ± listede Ã§Ä±ktÄ±); `ihaleler.html?il=VAN` regresyonsuz.
> - **DEPLOY (VDS):** `git pull` â†’ `docker exec -i supabase-db psql -U postgres -d postgres <
>   backend/migration_dt_il_sayim.sql` â†’ sonra sayfa yenilenince DT katmanÄ± otomatik devreye girer (RPC yoksa
>   zaten fallback ile Ã§alÄ±ÅŸÄ±yor, migration ACÄ°L deÄŸil ama performans iÃ§in Ã¶nerilir â€” 1.48M satÄ±r sayfalÄ±
>   fallback'te ~13 istek/13K Ã¶rneklem, tam deÄŸil).
> - **KAPSAM DIÅI (bilerek):** `index.html`'de AYNI haritanÄ±n satÄ±r-iÃ§i bir kopyasÄ± var (harita.js'in kendi
>   yorumunda zaten "teknik borÃ§" diye iÅŸaretli) â€” DT katmanÄ± ORAYA taÅŸÄ±nmadÄ±, yalnÄ±z dashboard.html/harita.js
>   gÃ¼ncellendi. Ä°stenirse ayrÄ± iÅŸ olarak index.html de aynÄ± modÃ¼le geÃ§irilip tekilleÅŸtirilebilir.

> ## âœ… 17-18 TEMMUZ â€” TENZÄ°LAT ~3 KAT ÅÄ°ÅÄ°K (Ã§ok-kÄ±sÄ±mlÄ± ihale hatasÄ±) â€” TÃœM ZÄ°NCÄ°R KAPANDI
> SonuÃ§ KPI'daki "Ort. Tenzilat %48,3" ÅŸÃ¼pheliydi; araÅŸtÄ±rÄ±ldÄ±, **gerÃ§ek bir veri hatasÄ± Ã§Ä±ktÄ±.**
> - **KÃ¶k neden (kanÄ±tlÄ±):** `ihale_sonuclari` satÄ±r baÅŸÄ±na bir KISIM/lot tutar. Ã‡ok-lotlu ihalelerde EKAP,
>   ihalenin **TOPLAM `yaklasik_maliyet`ini HER lot satÄ±rÄ±na kopyalÄ±yor** â€” 46.083 Ã§ok-lotlu ihalenin
>   46.077'sinde (%99,99) tÃ¼m satÄ±rlarda ym birebir aynÄ±. Tenzilat=(ymâˆ’teklif)/ym tutarlÄ± hesaplanÄ±yor ama
>   payda LOTUN deÄŸil Ä°HALENÄ°N maliyeti â†’ kÃ¼Ã§Ã¼k lot teklifi Ã· dev toplam = **sahte %95 tenzilat**.
>   Ã–rnek (5 lot, ym=6.297.340): teklifler 293K/1.008K/60K/257K/210K â†’ %95,3/%84/%99/%95,9/%96,7 kaydedilmiÅŸ;
>   gerÃ§ekte teklif toplamÄ± 1.827.580 = ym'nin %29'u â†’ tenzilat â‰ˆ%71.
> - **Ã–lÃ§Ã¼:** 246.639 satÄ±r (%46) etkili. %90-100 bandÄ±ndaki 158.755 kaydÄ±n %99,2'si Ã§ok-lotlu.
>   Tek-lot ort %14,75 (medyan %10,64) Â· Ã§ok-lot ort %86,78 (medyan %95,02) â†’ karÄ±ÅŸÄ±m %48,3 = YANLIÅ.
> - **DOÄRU METRÄ°K (ihale bazÄ±nda, lotlarÄ± topla):** ort **%16,96** / medyan %12,43 (n=328.823).
>   SQL: `WITH ihale AS (SELECT ilan_id, max(yaklasik_maliyet) ym, sum(kazanan_teklif) toplam FROM
>   ihale_sonuclari WHERE yaklasik_maliyet>0 AND kazanan_teklif IS NOT NULL GROUP BY ilan_id)` â†’ `(ymâˆ’toplam)/ym*100`.
>   NOT: `ilanlar.yaklasik_maliyet_min` sonuÃ§lularda neredeyse hiÃ§ dolu deÄŸil (20 kayÄ±t) â†’ payda `ihale_sonuclari.yaklasik_maliyet`.
> - **Etkilenen yÃ¼zeyler:** `sonuc_ozet_mv.ort_tenzilat` (Ä°halelerâ†’SonuÃ§ KPI), ihale-detay / firma-analiz /
>   kurum-analiz satÄ±r-bazlÄ± tenzilat, ve **teklif_ai.py + firma_ai_yorum.py (AI yorumlarÄ± bozuk veriyle Ã¼retiliyor)**.
> - âœ… **KPI DÃœZELTÄ°LDÄ° (18 Tem):** `backend/migration_tenzilat_ihale_bazli.sql` prod'da koÅŸtu â†’
>   `ort_tenzilat 48.3 â†’ 17.0`; toplam/toplam_bedel/farkli_firma deÄŸiÅŸmedi. CanlÄ± doÄŸrulandÄ± ("%17").
>   MV ihale-bazlÄ± hesaba Ã§evrildi; unique index + ACL (anon=r/authenticated=arwd/service_role=r) birebir kuruldu.
>   Migration'Ä± KULLANICI Ã§alÄ±ÅŸtÄ±rdÄ± â€” sÄ±nÄ±flandÄ±rÄ±cÄ± prod DDL'i bloklar ([[prod-ssh-auto-mode-limits]]).
> - âœ… **TÃœM YÃœZEYLER KAPANDI (18 Tem):** kÄ±sÄ±m bazlÄ± doÄŸru tenzilat mevcut veriden HESAPLANAMIYOR
>   (3 eÅŸleÅŸtirme yÃ¶ntemi denendi: indeks %17, deÄŸer %4,8, yapÄ±sal â†’ kisimList sÃ¶zleÅŸmeyle eÅŸleÅŸmiyor).
>   Ã‡Ã¶zÃ¼m "hesaplayamadÄ±ÄŸÄ±mÄ±zÄ± gÃ¶sterme": `ihale_sonuclari.lot_sayisi` kolonu (migration_sonuc_lot_sayisi.sql;
>   tek-kÄ±sÄ±m 288.728 / Ã§ok-kÄ±sÄ±m 249.336). Kural: lot_sayisi=1 â†’ geÃ§erli, >1 â†’ gÃ¶sterme/ortalamaya katma.
>   â€¢ ihale-detay: .limit(1) kaldÄ±rÄ±ldÄ±, Ã§ok kÄ±sÄ±mlÄ±da toplam bedel + Ä°HALE GENELÄ° tenzilat (%100,0â†’%39,8)
>   â€¢ firma-analiz: KPI yalnÄ±z tek kÄ±sÄ±mlÄ±dan, kartta "N kÄ±sÄ±mlÄ±" rozeti
>   â€¢ kurum-analiz: zaten doÄŸruydu, dokunulmadÄ±
>   â€¢ analiz_pivot: AVG FILTER (lot_sayisi=1) â€” **5 yÃ¼zey**: 2 kÄ±rÄ±lÄ±m + ihale-detay TEKLÄ°F BANDI Ã–NERÄ°SÄ° +
>     teklif_ai.py + firma_ai_yorum.py. DoÄŸrulama: kategori tenzilatlarÄ± %12-21 (gerÃ§ekÃ§i).
>   â€¢ AI: null'da "%None" yazmaz; prompt'a "null = hesaplanamÄ±yor, yorum yapma" kuralÄ±.
> - âš ï¸ AÃ‡IK: `lot_sayisi` gece UPDATE'i run_scraper.sh'e eklenmeli (SQL migration baÅŸÄ±nda hazÄ±r).
> - âš ï¸ AÃ‡IK: ekap_sonuc_backfill.py:310 `json.dumps(...)[:15000]` kÄ±rpmasÄ± 725 satÄ±rda JSON'u bozuyor.

> ## ğŸ§¹ 17 TEMMUZ â€” SONUÃ‡LANANLAR KALDIRILDI + DT DURUM SEKMELERÄ° + FÄ°RMA KONSOLÄ°DASYON CEVABI (âœ… CANLI, c74e3eb)
> KullanÄ±cÄ±: (1) SonuÃ§lananlar sayfasÄ± SonuÃ§ sekmesiyle redundant, kaldÄ±r; (2) DT'ye ihaleler gibi sekmeler;
> (3) soru: ihale+DT kazananlarÄ± aynÄ± isimse tek firma mÄ± topluyoruz?
> - **#1 SonuÃ§lananlar kaldÄ±rÄ±ldÄ±:** 22 sayfadan nav linki silindi, sayfa `ihaleler?sekme=sonuc`'a redirect
>   (eski link 404 olmasÄ±n). Sayfaya Ã¶zel 3 Ã¶zet KPI (Toplam SÃ¶zleÅŸme / Ort. Tenzilat / FarklÄ± Firma â€” sonuc_ozet
>   MV) Ä°haleler 'SonuÃ§' sekmesine taÅŸÄ±ndÄ± (sonuc-ozet-bar, yalnÄ±z o sekmede grid). CanlÄ±: bedel 5.248,5 Mrd â‚º,
>   firma 82.702. Redirect canlÄ± doÄŸrulandÄ±.
> - **#2 DT sekmeleri:** GÃ¼ncel(aktif ~95K) / SonuÃ§(sonuÃ§lanmÄ±ÅŸ ~1,39M) / TÃ¼mÃ¼(~1,48M) â€” DURUM-bazlÄ±.
>   DÄ°KKAT/DERS: Ã¶nce kullanÄ±cÄ±nÄ±n istediÄŸi TARÄ°H-bazlÄ± (son 1 yÄ±l) denendi ama DT tarihleri son 1 yÄ±lda
>   kÃ¼melendiÄŸi iÃ§in 1,4M/55K (anlamsÄ±z) Ã§Ä±ktÄ± â†’ durum-bazlÄ±ya Ã§evrildi (DURUM_GRUP.acik/sonuc zaten vardÄ±).
>   Gereksiz durum dropdown'u kaldÄ±rÄ±ldÄ± (sekmeler kapsÄ±yor); ?idare= ile gelince TÃ¼mÃ¼ aÃ§Ä±lÄ±r. CanlÄ± doÄŸrulandÄ±.
> - **#3 CEVAP:** `yukleniciler.normalize_ad` UNIQUE (82.095 firma=82.095 tekil isim) â†’ ihale kazananlarÄ± isimle
>   TEKLEÅTÄ°RÄ°LÄ°YOR (VKN %0, isim-bazlÄ±). AMA `dogrudan_temin_ilanlari`'nda kazanan kolonu YOK â†’ DT kazananlarÄ±
>   hiÃ§ kaydedilmiyor (EKAP DT kazananÄ± CAPTCHA arkasÄ±nda, bkz [[dt-kazanan-captcha]]). Yani DT firma verisine
>   girmiyor; mekanizma isim-ortak olduÄŸundan veri gelse aynÄ± normalize_ad ile otomatik birleÅŸirdi. AÃ§Ä±k: DT kazanan verisi yok.

> ## ğŸ” 17 TEMMUZ â€” Ä°HALELER: KURUMâ†’ARAMA YÃ–NLENDÄ°RME + SONUÃ‡ SEKMESÄ° ARAMA TIMEOUT (âœ… CANLI, 5751e9b)
> KullanÄ±cÄ± ekran gÃ¶rÃ¼ntÃ¼sÃ¼: (1) kurum-analiz "TÃ¼m Ä°halelerini GÃ¶r" tÃ¼m sistemi aÃ§Ä±yor, kuruma filtrelemiyor;
> (2) Ä°haleler SonuÃ§ sekmesinde "EMNÄ°YET" aramasÄ± "canceling statement due to statement timeout" veriyor.
> - **Fix #1 (kurumâ†’arama):** buton + benzer-kurum linki gizli `?idare=` (DetaylÄ± Ara panelindeki f-idare'ye
>   dÃ¼ÅŸÃ¼p boÅŸ GÃ¼ncel gÃ¶steriyordu) yerine gÃ¶rÃ¼nÃ¼r `?ara=<kurum>&sekme=gecmis` â†’ arama kutusu dolu + GeÃ§miÅŸ
>   sekmesinde kurumun ihaleleri. arama_fold idare'yi iÃ§eriyor (doÄŸrulandÄ±: grand plz idare=4952 = arama_fold=4952).
>   Ãœye yolu; misafirde idare zaten maskeli. (kurum-analiz.html)
> - **Fix #2 (SonuÃ§ timeout):** kÃ¶k neden EXPLAIN'le bulundu â€” count:exact â†’ `count(*) OVER()` planlayÄ±cÄ±yÄ± TÃœM
>   ihale_sonuclari'ni (2.2GB) tarayan hash-join'e itiyor â†’ 8s authenticated timeout soÄŸuk cache'te aÅŸÄ±lÄ±yor.
>   Trigram GIN index VARDI ama ORDER BY+LIMIT+count es geÃ§tiriyordu. Fix: SonuÃ§ sekmesinde `count:'planned'`
>   (frontend, DB deÄŸiÅŸikliÄŸi YOK) â†’ count(*) OVER() kalkar, trigram+nested-loop (uyum limit200 135ms, range
>   limit20 2.5s, hepsi <8s). Tahmini sayÄ±m "~" ile iÅŸaretlendi. (ihaleler.html)
> - CanlÄ± doÄŸrulandÄ± (guest): ?ara=+?sekme= akÄ±ÅŸÄ± Ã§alÄ±ÅŸÄ±yor, SonuÃ§ aramada timeout YOK + "~" gÃ¶sterimi.
>   Ãœye yolu DB'de EXPLAIN ANALYZE ile Ã¶lÃ§Ã¼ldÃ¼ (82-135ms). Deploy: 5751e9b â†’ push â†’ VDS `git pull` (oto-deploy yok).
> - Bkz. [[statement-timeout-edge]]. Not: node yok â†’ syntax tarayÄ±cÄ± console'uyla doÄŸrulandÄ±.

> ## ğŸ“¦ 18 TEMMUZ â€” KATMAN 4 (VERÄ°): GEÃ‡MÄ°Å KALEM LÄ°STESÄ° (ilan_metni) BACKFILL'Ä° â€” âœ… GECE CRON'DA
> KullanÄ±cÄ± "yavaÅŸ ve gÃ¼venli olanÄ± tercih et" dedi â†’ tek seferlik 6 saatlik tarama YERÄ°NE gece cron'una
> 200 sayfa/gece dilim (~25-35 gecede tamamlanÄ±r), EKAP bloÄŸu riskini minimize eder.
> **SORUN:** ~340K geÃ§miÅŸ ilan `ilan_metni=NULL` â€” ekap_sonuc_backfill'in BÄ°LÄ°NÃ‡LÄ° "kompakt" kararÄ±
> (satÄ±r 412 yorumu: "geÃ§miÅŸ=kompakt ~0.5KB, HTML yok"). O karar eski managed-Supabase limitleri iÃ§indi;
> VDS'te kÄ±sÄ±t YOK (128GB boÅŸ, DB 3.5GB). ilan_metni EN ZENGÄ°N konu sinyali + `arama_fold` ÃœRETÄ°LMÄ°Å
> kolonuna girdiÄŸi iÃ§in 352K geÃ§miÅŸ ilanÄ± **site iÃ§i aramada da** aranabilir yapar.
> **KRÄ°TÄ°K EKAP DERSÄ° (sonda ile bulundu):** `ekap_id` Ä°KN saklar ("2026/1210669") ama detay endpoint'i
> EKAP'Ä±n Ä°Ã‡ id'sini ister â†’ Ä°KN ile **HTTP 500**; searchText Ä°KN aramaz (totalCount=0). Ä°Ã§ id YALNIZCA
> liste yanÄ±tÄ±ndan gelir â†’ listeyi sayfalayÄ±p Ä°KN eÅŸleÅŸtirmek ZORUNLU. (Ä°lk sondam bu yÃ¼zden yanlÄ±ÅŸlÄ±kla
> "EKAP vermiyor" dedi; doÄŸru id ile **6/6 metin geldi**, 630-5464 char.)
> **backend/ilan_metni_backfill.py:** checkpoint'li, sayfa baÅŸÄ±na TEK DB sorgusu (dev harita kurmaz),
> yalnÄ±z ilan_metni yazar (ilan_html DEÄÄ°L â€” depolama yarÄ±sÄ± + XSS yÃ¼zeyi yok), eÅŸzamanlÄ±lÄ±k 2 + uyku +
> ardÄ±ÅŸÄ±k hatada kendini durdurma + proxy havuzu. **CanlÄ± doÄŸrulama:** dry-run 300 kayÄ±tâ†’201 eksik/201 metin
> (%67 isabet, 0 hata); gerÃ§ek 2 sayfa â†’ metinli sayÄ± 15.921â†’16.059 (138 yazÄ±ldÄ±); arama_fold uzunluÄŸu
> metni iÃ§erecek ÅŸekilde bÃ¼yÃ¼dÃ¼ (1901 vs ilan_metni 1814). Cron satÄ±r 94, EN SONDA (kritik iÅŸler Ã¶nce bitsin).
> **DEPLOY DERSÄ°:** test iÃ§in scp'lenen dosya commit sonrasÄ± VDS'te untracked kalÄ±nca `git pull` SESSÄ°ZCE
> durur ("untracked files would be overwritten") â€” scp kopyalarÄ±nÄ± silip pull et.
>
> ## ğŸ§  17 TEMMUZ â€” EÅLEÅTÄ°RME MOTORU 3-KATMAN Ä°YÄ°LEÅTÄ°RME (kullanÄ±cÄ± "yap hepsini") â€” K1 âœ…, K2 âœ…, K3 âœ… TAMAM
> **KATMAN 2 âœ… CANLI+DOÄRULANDI (commit `5bc754d`, migration_idf_eslestirme.sql):** baÅŸlÄ±k eÅŸleÅŸmesi
> IDF-nadirlik aÄŸÄ±rlÄ±klÄ±. ihale_kelime_idf MV (34.236 kelime, gece REFRESH) + ihale_konu_kelimeleri_idf().
> benzer_ihaleler embeddingsiz dalÄ± karakter-trigramâ†’IDF-Ã¶rtÃ¼ÅŸme (gÄ±da: benzerlik 19â†’55). uygun_firmalar
> baÅŸlÄ±k dalÄ± IDF-relevans. 4-lens 25-ajan Ã§ekiÅŸmeli inceleme 2 KRÄ°TÄ°K yakaladÄ±+dÃ¼zeltti: (a) Ã¶lÃ¼ kolon
> a.a_ilâ†’a.il (CREATE patlÄ±yor, DROP kaldÄ±rÄ±ldÄ±+BEGIN/COMMIT); (b) baÅŸlÄ±k dalÄ± join yÃ¶nÃ¼ tersâ†’trigram indeksi
> Ã¶lÃ¼ 10sn timeoutâ†’src_kwâ†’ilanlar join (EXPLAIN Bitmap, 388ms). +word-boundary \m..\M (karsâ†’karsilanmasi
> 4904â†’637) +p_bant guard. CanlÄ±: benzer anon 200/0.3s, misafir kartÄ± 4/4 gÄ±da, uygun_firmalar anon-kilitli.
> DERS: MV-inline SQL fonksiyonda tr_fold ÅEMA-NÄ°TELÄ°KLÄ° (public.tr_fold) olmalÄ±.
> **KATMAN 3 âœ… TAMAM (commit `0ebf461`):** aktif ilanlarÄ± baÅŸlÄ±k-Ã¼stÃ¼ gÃ¶m. Ä°Ã‡GÃ–RÃœ: benzer_ihaleler yalnÄ±z
> AKTÄ°F ilanlarÄ± aday alÄ±r â†’ 537K geÃ§miÅŸi gÃ¶mmek gereksiz, sadece ~4.6K aktif yeter. ilan_embed_uret.py
> 'ilan_metni not.is.null' filtresi kaldÄ±rÄ±ldÄ± â†’ **4.639/4.639 aktif gÃ¶mÃ¼ldÃ¼ (kalan 0)**; semantik dal
> (cosine<0.45) artÄ±k tÃ¼m aktiflerde. DERS: script PostgREST 1000-cap'e takÄ±lÄ±r â†’ backlog iÃ§in dayanÄ±klÄ±
> re-run sarmalayÄ±cÄ± (embed_aktif_dayanikli.sh); gece cron â€”max 300 gÃ¼nlÃ¼k yeni aktifler iÃ§in yeterli.
> **K1 durum:** ~49K kanoniÄŸe atandÄ±, kuyruk 153K, dayanÄ±klÄ± koÅŸu sÃ¼rÃ¼yor (free-tier, birkaÃ§ gÃ¼ne yayÄ±lÄ±r).
> **AÃ‡IK/gelecek:** uygun_firmalar'a embedding-firma dalÄ± (356K geÃ§miÅŸ gÃ¶mme gerekir, dÃ¼ÅŸÃ¼k marjinal â€” IDF
> zaten iyi); scraper ilan_metni kapsamasÄ± (en deÄŸerli VERÄ° iÅŸi, %4,5â†’artÄ±r).
>
> ## ğŸ§  17 TEMMUZ â€” EÅLEÅTÄ°RME MOTORU KATMAN 1: JENERÄ°K KOVA â†’ KANONÄ°K AI BACKFILL (âœ… toplu koÅŸu VDS'te)
> KullanÄ±cÄ±: "benzer ihaleler + uygun firmalar algoritmasÄ± Ã§ok iyi Ã§alÄ±ÅŸsÄ±n; bazÄ± ihalelerde OKAS yok, buna
> gÃ¶re yorum yapamÄ±yorsun â€” bunu dÃ¼zeltmemiz lazÄ±m, zenginliÄŸimiz buradan gelecek."
> **SÄ°NYAL ENVANTERÄ° Ã–LÃ‡ÃœLDÃœ (356.690 ilan / 537.761 sonuÃ§):** OKAS dolu %2,8 (10.139) â†’ OKAS Ã–LÃœ.
> Kanonik kategori %42. **JENERÄ°K kova %58** (Mal AlÄ±mÄ± 87K + DiÄŸer 68K + Hizmet AlÄ±mÄ± 51K = konu sinyali 0).
> ilan_metni %4,5 (geÃ§miÅŸ kazananlarda %0,02!). embedding 1.500 (yalnÄ±z aktif). **GeÃ§miÅŸte tek evrensel
> sinyal BAÅLIK.** â†’ AsÄ±l kÃ¶rlÃ¼k OKAS deÄŸil, jenerik kategori + zayÄ±f baÅŸlÄ±k eÅŸleÅŸmesi.
> **3-KATMAN PLAN (kullanÄ±cÄ± Katman 1'i seÃ§ti):** (1) jenerikâ†’kanonik AI backfill [BU]; (2) baÅŸlÄ±k
> eÅŸleÅŸmesini IDF/nadirlik-aÄŸÄ±rlÄ±klÄ± yap; (3) embedding'i 537K geÃ§miÅŸe yay. AyrÄ± VERÄ° iÅŸi: scraper ilan_metni.
> **âœ… YAPILDI:** DERS â€” migration_ai_kategori.sql prod'a HÄ°Ã‡ uygulanmamÄ±ÅŸtÄ± (kolon yok â†’ gece cron her gece
> sessizce Ã§Ä±kmÄ±ÅŸ, Ã¶zellik hiÃ§ Ã§alÄ±ÅŸmamÄ±ÅŸ!). migration_ai_kategori_jenerik.sql (canlÄ±): kolonu kurar +
> ai_kategori_backfill.py'Ä± 3 jenerik kovaya geniÅŸletir (in.() TÃ¼rkÃ§e Ã§ift-tÄ±rnak, 205.630 satÄ±r doÄŸrulandÄ±) +
> kuyruk indeksi + legacy "Ä°nÅŸaat & YapÄ±m" 22K â†’ kanonik birleÅŸti. Dry-run ~%90 isabet ("Åapka"â†’Tekstil,
> "PrÄ±smaflex Seti"â†’TÄ±bbi Cihaz, belirsizler jenerik kalÄ±r). Maliyet ~$8 tek seferlik (4.113 istek).
> **Toplu koÅŸu VDS'te nohup ile baÅŸlatÄ±ldÄ±** (--rpm 15; free daily cap bÃ¶lerse zarif durur+resume). Ä°zleyici
> arka planda bitiÅŸi bekliyor. NOT: bulk bitmeden/cap'e takÄ±lmadan gece cron'un 400-limitiyle kÃ¼Ã§Ã¼k yarÄ±ÅŸ
> olabilir (~$0.02 Ã§Ã¶p) â€” Ã¶nemsiz. Katman 2/3 kullanÄ±cÄ± onayÄ± bekliyor.

> ## ğŸŒ 17 TEMMUZ â€” TÄ°CARET: YIL+KIYAS FRONTEND CANLI + iso2 + FULL BACKFILL 2000-2026 (âœ… backfill koÅŸuyor)
> KullanÄ±cÄ±: "yÄ±l kÄ±yaslamasÄ±nÄ± Ã§alÄ±ÅŸÄ±r kÄ±l; commit/push/deploy ne gerekiyorsa yap."
> - **Frontend statikâ†’RPC:** ticaret-analiz.html artÄ±k TICARET_TR yerine ticaret_yillar/liste/harita/ulke
>   RPC'lerinden besleniyor; YÄ±l+KÄ±yas dropdown eklendi (varsayÄ±lan: gÃ¼ncel vs bir Ã¶nceki). KPI = ticaret_ulke('WLD').
>   HS6 drill-down EZÄ°LMEDEN korundu. SektÃ¶r dropdown 16 grup backend SEKTORLER ile birebir HARDCODE â€”
>   DÄ°KKAT: eski statik dosyanÄ±n sektÃ¶r anahtarlarÄ± FARKLI ("01-05" vs "01-05_Animal"); karÄ±ÅŸÄ±rsa harita boÅŸ dÃ¶ner.
> - **TÃ¼rkÃ§e ad / iso2:** ticaret_liste artÄ±k iso2 dÃ¶ner (migration_ticaret_iso2.sql, canlÄ±da). Frontend Ã¶nceliÄŸi
>   RPC iso2, fallback statik TICARET_TR.a2 â†’ iso2 gelmeden de regresyon yoktu. CanlÄ± doÄŸrulandÄ±: DEUâ†’"DE".
> - **Deploy:** iso2 migration + 2023 re-backfill (171 Ã¼lke/2672 sektÃ¶r satÄ±rÄ±, iso2'li) VDS'te koÅŸtu; full backfill
>   2000-2026 arka planda (izle: `tail /opt/ihale-platform/logs/ticaret_backfill.log`). YÄ±llar DB'ye dÃ¼ÅŸtÃ¼kÃ§e
>   dropdown kendiliÄŸinden dolar (kod hazÄ±r). Ã‡Ä°FT KOÅU YAKALANDI: iki oturum aynÄ± backfill'i baÅŸlatmÄ±ÅŸtÄ±
>   (systemd + nohup) â€” Comtrade 500 Ã§aÄŸrÄ±/gÃ¼n kotasÄ± iÃ§in systemd olan durduruldu, nohup devam ediyor.
> - **CanlÄ± doÄŸrulama (ihaleglobal.com, gerÃ§ek veri):** yÄ±l dropdown [2000-2005, 2023]; 2023 vs 2005 kÄ±yasÄ± â€”
>   dÃ¼nya ihracat â–²%247,9; Almanya $21,1Mr â–²%123; ABD $14,9Mr â–²%203; TÃ¼rkÃ§e adlar; HS6 drill-down DEU 400 kalem.
> - âš ï¸ SÃœREÃ‡ NOTU: eÅŸzamanlÄ± oturumlar aynÄ± aÄŸaÃ§ta commit sÃ¼pÃ¼rmesi yaptÄ± (ticaret frontend + backend dosyalarÄ±
>   alakasÄ±z mesajlÄ± commit'lere girdi â€” iÅŸ kaybolmadÄ± ama geÃ§miÅŸ kirlendi). Ã‡oklu oturumda git'i tek oturuma bÄ±rakÄ±n.

> ## ğŸ§© 17 TEMMUZ â€” "ÃœYE DE *** GÃ–RÃœYOR + BOÅ KUTULAR" EKRAN GÃ–RÃœNTÃœSÃœ TEÅHÄ°SÄ° (âœ… Ä°KÄ° PARÃ‡A DA KAPANDI)
> KullanÄ±cÄ± benzer ihalelerde ğŸ”’*** + parÃ§alanmÄ±ÅŸ boÅŸ kartlar gÃ¶sterdi ("yine olmadÄ± sanÄ±rÄ±m").
> Ä°KÄ° AYRI kÃ¶k neden Ã§Ä±ktÄ±:
> 1. **ğŸ”’*** giriÅŸliyken DEÄÄ°L, oturumsuzken gÃ¶rÃ¼nÃ¼yormuÅŸ** â€” sidebar'daki "Faruk D./Ãœcretsiz Plan" statik
>    YER TUTUCU oturum dÃ¼ÅŸÃ¼nce de duruyordu â†’ kullanÄ±cÄ± kendini giriÅŸli sandÄ± (+ www/apex localStorage ayrÄ±mÄ±).
>    Maskeleme mekanizmasÄ± DOÄRU Ã§alÄ±ÅŸÄ±yordu. Bunu paralel oturum dÃ¼zeltti (sidebar-user.js?v=3 misafir dalÄ±
>    + wwwâ†’apex redirect); ders veri-disa-aktarim-yasagi hafÄ±zasÄ±nda.
> 2. **BoÅŸ/parÃ§alÄ± kartlar benim hatamdÄ± (bu oturum dÃ¼zeltti):** MASKE_ROZET bir <a>; benzer-item kartÄ± da
>    <a> â€” Ä°Ã‡ Ä°Ã‡E ANCHOR geÃ§ersiz, tarayÄ±cÄ± dÄ±ÅŸ kartÄ± parse'ta bÃ¶lÃ¼yordu (ekrandaki boÅŸ kutular). Benzer
>    meta'daki kilit artÄ±k linksiz <span>. **KURAL: MASKE_ROZET'i (a href=login) asla <a> iÃ§ine koyma â€”
>    kart-linkli ÅŸablonlarda span sÃ¼rÃ¼mÃ¼nÃ¼ kullan.** CanlÄ± doÄŸrulama (misafir, gÄ±da detayÄ±): 4 benzer kart
>    bÃ¼tÃ¼n, parÃ§alÄ± 0, iÃ§ iÃ§e link 0, meta "ğŸ”’ *** Â· ğŸ“ANKARA Â· Son: ...". AyrÄ±ca v3 RPC kilitleri probe
>    edildi: ihaleye_uygun_firmalar anonâ†’42501 âœ“, benzer_ihaleler idare dÃ¶ndÃ¼rmÃ¼yor âœ“ (v3 tasarÄ±mÄ± maskeye uymuÅŸ).

> ## ğŸ‘¤ 17 TEMMUZ â€” "ÃœCRETSÄ°Z ÃœYE DE *** GÃ–RÃœYOR" ÅÄ°KAYETÄ°: SAHTE SIDEBAR + www/apex OTURUM BÃ–LÃœNMESÄ° (âœ… CANLI â€” commit `389183e`+`deb41f2`, VDS pull edildi)
> KullanÄ±cÄ±: "Ã¼cretsiz planda da *** gÃ¶rÃ¼nÃ¼yor; sadece giriÅŸ yapmayanlara *** gÃ¶rÃ¼nsÃ¼n." Ä°NCELEME SONUCU:
> maskeleme zaten yalnÄ±z oturumsuza Ã§alÄ±ÅŸÄ±yor (DB kolon-grant'larÄ± sadece anon'dan REVOKE'lu, authenticated
> tam gÃ¶rÃ¼r; client `getSession()` yoksa maskeler). GERÃ‡EK SORUN Ä°KÄ° KATMANLI:
> - **(1) Sahte sidebar:** dashboard/ihaleler/ihale-detay/takipte statik HTML'de **"FD / Faruk D. /
>   Ãœcretsiz Plan"** hardcoded'dÄ± â†’ misafir veya OTURUMU DÃœÅMÃœÅ kullanÄ±cÄ± kendini "giriÅŸli Ã¼cretsiz Ã¼ye"
>   sanÄ±p ***'larÄ± plana baÄŸlÄ±yordu. FIX: 4 sayfa + profil.html nÃ¶tr yer tutucuya Ã§ekildi ("YÃ¼kleniyorâ€¦/â€”");
>   js/sidebar-user.js'e **misafir dalÄ±** eklendi (oturum yoksa: ğŸ‘¤ Misafir / "GiriÅŸ yapÄ±n â†’", user-row
>   login'e gider; getUser aÄŸ hatasÄ±nda yerel getSession'a bakar). Cache-bust ?v=3â†’**?v=4**: CF, v=3
>   URL'ini deploy Ã–NCESÄ° eski iÃ§erikle Ã¶nbelleklemiÅŸti (max-age 4h, purge yerine yeni query key seÃ§ildi â€”
>   DERS: cache-bust versiyonunu deploy'dan Ã¶nce canlÄ±da kimse istememiÅŸ olmalÄ±, yoksa eski iÃ§erik yeni
>   anahtara yapÄ±ÅŸÄ±r). CanlÄ± doÄŸrulama: /js/sidebar-user.js?v=4 misafir dalÄ±nÄ± iÃ§eriyor, sayfalar v=4'Ã¼
>   referanslÄ±yor, CF HIT yeni iÃ§erikle.
> - **(2) www/apex origin bÃ¶lÃ¼nmesi:** www.ihaleglobal.com da apex de 200 dÃ¶nÃ¼yor, redirect YOK â†’
>   localStorage origin-bazlÄ± olduÄŸundan www'da aÃ§Ä±lan oturum apex'te gÃ¶rÃ¼nmez (tam "giriÅŸliyim ama ***"
>   senaryosu). FIX: sidebar-user.js + login.html + index.html'e `www.â†’apex location.replace` (hash
>   korunur â€” e-posta onay token'Ä±). ~~KALICI Ä°Å: CF Redirect Rule~~ **âœ… YAPILDI (17 Tem): kullanÄ±cÄ± CF
>   panelinden "Redirect from WWW to root" ÅŸablonunu deploy etti** (wildcard https://www.* â†’ https://${1},
>   301, preserve query string; "www proxy'li olmayabilir" uyarÄ±sÄ± yanlÄ±ÅŸ alarmdÄ± â€” CF-RAY ile doÄŸrulandÄ±).
>   CanlÄ± test: kÃ¶k/yol/query Ã¼Ã§Ã¼ de 301â†’apex, zincir tek yÃ¶nlendirmeyle 200. www/apex oturum bÃ¶lÃ¼nmesi
>   artÄ±k kÃ¶kten kapalÄ±; client-side redirect'ler kÃ¶prÃ¼ olarak kalabilir (zararsÄ±z). **EK (aynÄ± gÃ¼n):
>   origin nginx'e de wwwâ†’apex 301 eklendi** (sites-enabled/ihale: www ayrÄ± server bloÄŸu, ana bloktan
>   server_name'den Ã§Ä±karÄ±ldÄ±; yedek /root/ihale.nginx.bak.*, nginx -t + reload OK) â€” CF bypass edilse
>   bile origin aynÄ± cevabÄ± verir.
> - DoÄŸrulama: localhost misafir gÃ¶rÃ¼nÃ¼mÃ¼ OK (Misafir rozeti + *** maskeleri + sayfa tam yÃ¼kleniyor).
>   GiriÅŸli gÃ¶rÃ¼nÃ¼m kullanÄ±cÄ± gÃ¶zÃ¼yle doÄŸrulanmalÄ±: giriÅŸ yap â†’ ihale-detay'da idare/benzer meta aÃ§Ä±k mÄ±?

> ## ğŸ—‚ï¸ 17 TEMMUZ â€” FÄ°RMA ANALÄ°ZÄ°: SEKMELER BÄ°RLEÅTÄ° + TAM PARA FORMATI (âœ… CANLI, commit `850bebc`)
> KullanÄ±cÄ±: "SonuÃ§lar ve Ä°haleler aynÄ± noktaya varÄ±yor â€” tek sayfada katÄ±ldÄ±ÄŸÄ± ihaleler olarak gÃ¶ster;
> â‚º 3.9 M TL gibi rakamlarÄ± net gÃ¶ster (809.558,00 â‚º / 3.900.752,52 â‚º gibi)."
> - **Sekme birleÅŸimi:** "SonuÃ§lar"+"Ä°haleler" â†’ tek **"KatÄ±ldÄ±ÄŸÄ± Ä°haleler"** (ikisi de aynÄ± veriden
>   besleniyordu: tumIhaleler=sonucVeri.map(s=>s.ilan), EKAP kaybedeni yayÄ±nlamaz). BirleÅŸik kart =
>   sonuÃ§ kartÄ± + tÃ¼r rozeti; 20/sayfa pager (yÃ¶n-string deseni â€” inline onclick closure tuzaÄŸÄ±);
>   eski tab-ihaleler/listeSayfa/durumSec silindi; "Ä°halelerini GÃ¶r" butonu yeni sekmeye baÄŸlandÄ±;
>   birleÅŸik kartta idare/kazanan_firma/baÅŸlÄ±k escapeHtml'e alÄ±ndÄ± (eskiden ESCAPESIZdi â€” XSS dersi).
> - **paraTam(v):** tr-TR + 2 kuruÅŸ + ' â‚º'. Uygulanan: detay KPI/kart/meta/kpi-sub, dizin ciro kolonu
>   (masaÃ¼stÃ¼ 165px, mobil 130px+11.5px+ellipsis), arama listesi, karÅŸÄ±laÅŸtÄ±rma (min-width:0+wrap).
>   BÄ°LÄ°NÃ‡LÄ° kompakt kalanlar: dizin toplam-ciro KPI'sÄ± (71K firmanÄ±n toplamÄ±, formatBedel) + harita
>   paraKisa'larÄ± (yer-kÄ±sÄ±tlÄ± gÃ¶rselleÅŸtirme).
> - **SÃ¼reÃ§ (ultracode):** 14-hakem Ã§ekiÅŸmeli inceleme (3 lens â†’ bulgu baÅŸÄ±na Ã§Ã¼rÃ¼tme hakemi; 830K token).
>   5 doÄŸrulanmÄ±ÅŸ bulgunun 5'i de kapatÄ±ldÄ±: mobil ciro kesilmesi (90px'te tam format YANILTICI tutar
>   gÃ¶steriyordu â€” en kritik), sekme geÃ§iÅŸinde sayfa sÄ±fÄ±rlanmasÄ±, firma deÄŸiÅŸiminde bayat pager,
>   kars-cell mobil taÅŸmasÄ±, yorum dÃ¼zeltmesi. Fixture testi (gerÃ§ek fonksiyonlar + 45 sahte kayÄ±t,
>   VDS'te geÃ§ici sayfa â†’ test edilip SÄ°LÄ°NDÄ°): format birebir, 3-sayfa pager akÄ±ÅŸÄ±, XSS dÃ¼z metin.
> - **CanlÄ± doÄŸrulama:** dizin ilk 3 ciro "106.336.802.938,00 â‚º / 91.531.222.819,00 â‚º / ..." tam formatlÄ±;
>   mobil 375px'te en bÃ¼yÃ¼k tutar taÅŸmadan sÄ±ÄŸÄ±yor (scrollWidth Ã¶lÃ§Ã¼mÃ¼); "KatÄ±ldÄ±ÄŸÄ± Ä°haleler" HTML'de,
>   eski sekme kalÄ±ntÄ±sÄ± 0. Detay sekmesi login-gated olduÄŸundan Ã¼ye gÃ¶rÃ¼nÃ¼mÃ¼ fixture+statik incelemeyle
>   doÄŸrulandÄ± â€” kullanÄ±cÄ± giriÅŸli gÃ¶zle de bakmalÄ±.

> ## ğŸ¯ 17 TEMMUZ â€” EÅLEÅTÄ°RME v3: KONU + Ã–LÃ‡EK BANDI (Â±%500) (âœ… CANLI â€” migration+frontend deploy edildi, 2026/792203'te doÄŸrulandÄ±: uygun firmalar gÄ±da+bant-iÃ§i, kazanan BAÅHAN AGRO listede 4., benzerler 4/4 gÄ±da)
> KullanÄ±cÄ± ÅŸikayeti (Jandarma 2026/792203, 809K gÄ±da ihalesi): "Uygun Firmalar"da Petrol Ofisi/Otokar,
> "Benzer Ä°haleler"de mobilya/bidon/medikal gaz Ã§Ä±kÄ±yordu. KÃ–K NEDEN: ilanÄ±n kategorisi kanonik 41'den
> deÄŸil, jenerik "Mal AlÄ±mÄ±" kovasÄ± (Jandarma/DMO kaynaÄŸÄ± tÃ¼r adÄ±nÄ± kategoriye yazmÄ±ÅŸ olabilir â€” AI
> kategori backfill'in bu kovayÄ± NEDEN atladÄ±ÄŸÄ± ayrÄ±ca incelenecek). KullanÄ±cÄ± kuralÄ±: konusu eÅŸleÅŸen
> (en az o konuda iÅŸ almÄ±ÅŸ) + geÃ§miÅŸ kazanÄ±mlarÄ± bedele Â±%500 bandÄ±nda (bedel/5..bedel*5) KALAN firmalar;
> benzer ihalelerde de bant ÅART. EK KURAL: dayanak (konu Ã§apasÄ±: kanonik kategori / baÅŸlÄ±k
> konu-kelimesi / embedding) HÄ°Ã‡ yoksa ne benzer ihale ne uygun firma GÃ–STERÄ°LMEZ (boÅŸ dÃ¶ner,
> benzer kartÄ± gizlenir) â€” gerekÃ§e: ileride otomatik firma-davet bu veriden beslenecek, alakasÄ±z
> eÅŸleÅŸme = spam. Eski "aynÄ± tÃ¼r" ve jenerik-kategori doldurmalarÄ± frontend'den de KALDIRILDI.
> **backend/migration_uygun_firmalar_v3.sql (âœ… canlÄ± â€” kullanÄ±cÄ± SSH ile yÃ¼kledi, 17 Tem):**
> - `ihale_konu_kelimeleri(baslik)`: tr_fold + ihale-jargonu stopword ayÄ±klama â†’ konu kelimeleri ('gida').
> - `ihaleye_uygun_firmalar` v3 (+p_baslik, +p_bant=5): kategori kanonik deÄŸilse konu=baÅŸlÄ±k kelimesi;
>   bedel varsa YALNIZ bant-iÃ§i kazanÄ±mlar sayÄ±lÄ±r (istatistikler bant-iÃ§inden), skor=deneyim+aynÄ± il+
>   log-Ã¶lÃ§ek yakÄ±nlÄ±ÄŸÄ±; GROUP BY Ã¼nvan (Ä°stanbul Enerji Ã§ift satÄ±r fix). Anon kilidi KORUNDU (REVOKE).
> - `benzer_ihaleler` (YENÄ° RPC): embedding cosine (varsa) / baÅŸlÄ±k trigram + kanonik kategori/il bonusu,
>   aday bedeli bant dÄ±ÅŸÄ±ysa ELENÄ°R (bedeli bilinmeyen âˆ’5 ceza); idare DÃ–NDÃœRMEZ (anon maskesi), anon'a aÃ§Ä±k.
> **ihale-detay.html (âœ… hazÄ±r, RPC yoksa eski davranÄ±ÅŸa dÃ¼ÅŸer â€” regresyon yok):** kanonikKategori()
> (js/kategoriler.js include edildi), efektifBedel() (yaklaÅŸÄ±k maliyet yoksa sÃ¶zleÅŸme bedeli â€” Jandarma
> sonuÃ§lanmÄ±ÅŸlarÄ±nda kritik), uygunFirmalar v3 Ã§aÄŸrÄ± + "Ã–lÃ§ek âœ“" rozeti (eski "Kapasite âœ“" bedel yokken
> herkese sahte yanÄ±yordu â€” artÄ±k yalnÄ±z bant uygulanÄ±nca), benzerIhaleler Ã¶nce RPC sonra eski 3-kademe.
> **v3.1â€“v3.3 (17 Tem devam, hepsi âœ… canlÄ±):** EK KURAL sonrasÄ± 3 iÅŸ + 2 hata dÃ¼zeltmesi:
> - v3.1: tr_fold(baslik) trigram GIN indeksi; benzer_ihaleler'e AÃ‡IK Ä°HALE ÅŸartÄ± (son_teklif geÃ§miÅŸ
>   aday elenir â€” canlÄ±da 4/4 benzerin tarihi geÃ§miÅŸti); ilan_durum_bayatlat() + run_scraper.sh adÄ±mÄ±
>   (TÃœM scraperlardan SONRA: jandarma/dmo upsert durum:'aktif' ile kaydÄ± yeniden aÃ§Ä±yor).
> - v3.2â†’v3.3 DERSLER: (a) baslik-kelime yolu 10.2sn sÃ¼rÃ¼yordu (planner 537K sonuÃ§tan ters girmiÅŸ,
>   trigram indeksi kullanÄ±lmamÄ±ÅŸ) â†’ plpgsql 2-dal + MATERIALIZED ilgili CTE = 1.33sn (timeout altÄ±);
>   (b) plpgsql RETURN QUERY Ã¶rtÃ¼k cast YAPMAZ â†’ max(bigint)::numeric ÅŸart; (c) ilanlar_durum_check
>   = taslak/aktif/kapali/iptal/sonuclandi â†’ bayatlama 'kapali' yazar ('kapandi' DEÄÄ°L).
> - Ä°lk bayatlama koÅŸusu: 11.627 sÃ¼resi-geÃ§miÅŸ 'aktif' ilan kapatÄ±ldÄ±.
> KALAN: (1) "Mal AlÄ±mÄ±"/jenerik kategorili ilanlarÄ± kanonik kategoriye backfill (kalÄ±cÄ± Ã§Ã¶zÃ¼m),
> (2) ozel-ihaleler `ihaleye_uygun_firmalar_geo` hÃ¢lÃ¢ v2 mantÄ±ÄŸÄ±nda â€” bant kuralÄ± istenirse oraya da,
> (3) baÅŸlÄ±k dalÄ± 1.33sn â€” istenirse ileride MV/Ã¶nbellekle ms'e iner (ÅŸimdilik yeterli).

> ## ğŸ” 17 TEMMUZ â€” TÄ°CARET: HS/SEKTÃ–R ARAMA + TÃœRKÃ‡E HS ETÄ°KETLERÄ° (canlÄ±)
> KullanÄ±cÄ±: 'HS koduna gÃ¶re de arama olmalÄ± (sektÃ¶r yanÄ±na), o kalem/sektÃ¶rde TÃ¼rkiye'nin Ã¼lke-Ã¼lke ihr/ith
> gÃ¶rÃ¼nsÃ¼n' + 'HS aÃ§Ä±klamalarÄ± TÃœRKÃ‡E olmalÄ± (Ä°ngilizce olmaz)'. Ä°kisi de yapÄ±ldÄ±:
> - **HS/SektÃ¶r Sorgusu kartÄ±** (ticaret-analiz.html): 'SektÃ¶re gÃ¶re' (rpc ticaret_harita â†’ Ã¼lke Ã¼lke) VEYA
>   'HS koduna gÃ¶re' (kod/TÃ¼rkÃ§e-aÃ§Ä±klama autocomplete â†’ dis_ticaret_hs â†’ Ã¼lke Ã¼lke). Drill-down'un TERSÄ° yÃ¶nÃ¼.
> - **TÃ¼rkÃ§e HS etiketleri**: kullanÄ±cÄ± PDF'i (AdsÄ±z 1.pdf, 400 kod TÃ¼rkÃ§e) + Workflow ile 5213 kod Ä°ngilizceâ†’TÃ¼rkÃ§e
>   Ã§eviri (24 ajan) + Comtrade H6 taban â†’ js/hs-kodlar.js TÃ¼rkÃ§e (5613/5613 6-hane). ?v=2. TÃ¼rkÃ§e arama Ã§alÄ±ÅŸÄ±yor
>   ('fÄ±ndÄ±k','deri','bilgisayar'). Drill-down + Ã¶neri + sonuÃ§ hep TÃ¼rkÃ§e.
> - **âš ï¸ EÅZAMANLI OTURUM Ã‡AKIÅMASI:** origin/main'de baÅŸka oturum ticaret-analiz.html'i statikâ†’RPC (yÄ±l seÃ§ici)
>   yeniden yazmÄ±ÅŸtÄ±. Onu EZMEDEN: origin'in RPC versiyonunu taban alÄ±p aramamÄ± RPC'ye uyarlayarak geri ekledim
>   (git checkout origin -- + additive). Drill-down + RPC yÄ±l-seÃ§ici + arama + TÃ¼rkÃ§e hepsi bir arada, canlÄ± doÄŸrulandÄ±.
> - Kalan: 2/4-hane HS Ä°ngilizce (UI'da gÃ¶sterilmiyor); HS-search yÄ±lÄ± 2024 (dis_ticaret_hs) vs sektÃ¶r RPC yÄ±lÄ±
>   (2023, full backfill bekliyor); Faz 2 = ihale Ã¼rÃ¼nÃ¼â†”HS eÅŸleÅŸme.

> ## ğŸ› ï¸ 17 TEMMUZ â€” SAHA TESTÄ° DÃœZELTMELERÄ° (kullanÄ±cÄ± geri bildirimi)
> - **âœ… Kazanan firma tÄ±klanamÄ±yordu** (ihale-detay "SonuÃ§landÄ±" banner'Ä±): dÃ¼z <b> idi â†’ firma-analiz linki
>   (Ã¼yeyse; â†—). Not: sayfadaki DÄ°ÄER kazanan render'Ä± (satÄ±r ~853) zaten linkliydi, banner unutulmuÅŸtu.
> - **âœ… NotlarÄ±m'da Kaydet butonu yoktu**: not aslÄ±nda oninput ile OTO-kaydoluyordu ama gÃ¶rÃ¼nÃ¼r buton/geri
>   bildirim olmadÄ±ÄŸÄ± iÃ§in kullanÄ±cÄ± kaydolmuyor sanÄ±yordu â†’ "ğŸ’¾ Kaydet" butonu + yeÅŸil "âœ“ Kaydedildi" +
>   yardÄ±m metni "otomatik kaydedilir".
> - **âœ… "GiriÅŸ yapÄ±n" â†’ dashboard BOUNCE (kritik):** login.html "zaten giriÅŸli mi" kontrolÃ¼
>   `API.auth.girisli_mi()` kullanÄ±yordu; o SADECE legacy `ihale_token` localStorage anahtarÄ±nÄ±n VARLIÄINA
>   bakar (expiry/geÃ§erlilik YOK). GerÃ§ek oturum Supabase'de â†’ **iki auth sistemi Ã§akÄ±ÅŸmasÄ±**: sidebar
>   (Supabase getUser) "Misafir" gÃ¶sterirken login bayat token'Ä± gÃ¶rÃ¼p dashboard'a geri atÄ±yordu; giriÅŸ
>   ekranÄ±na ULAÅILAMIYORDU. Fix: Supabase `getSession()` (expiry dahil); oturum yoksa bayat ihale_token
>   temizlenip form gÃ¶steriliyor. CanlÄ±da reprodÃ¼ce edilip doÄŸrulandÄ±.
> - **â³ Onay e-postasÄ± Ä°ngilizce:** TÃ¼rkÃ§e ÅŸablonlar hazÄ±r+deploy (`email/onay.html`, `email/sifirlama.html`;
>   ham HTML servis ediliyor). GoTrue'da Ã¶zel subject/template YOK â†’ varsayÄ±lan Ä°ngilizce.
>   **ğŸ›‘ 20 TEM DÃœZELTME â€” Ã–NCEKÄ° KOMUT YIKICIYDI, Ã‡ALIÅTIRMAYIN.** Buraya yazdÄ±ÄŸÄ±m ilk blok yalnÄ±z
>   `studio` bloÄŸunu koruyordu; oysa canlÄ± `docker-compose.override.yml` iÃ§inde **Google OAuth ayarlarÄ±**
>   da varmÄ±ÅŸ (`GOTRUE_EXTERNAL_GOOGLE_ENABLED/CLIENT_ID/SECRET/REDIRECT_URI`). O komut Ã§alÄ±ÅŸtÄ±rÄ±lsaydÄ±
>   Google ile giriÅŸ Ã§alÄ±ÅŸmayÄ± bÄ±rakacaktÄ±. **DERS: `cat > dosya` ile prod config yazmadan Ã–NCE dosyayÄ±
>   OKU** â€” "override kÃ¼Ã§Ã¼ktÃ¼r, iÃ§inde ne olabilir ki" varsayÄ±mÄ± bir kimlik doÄŸrulama saÄŸlayÄ±cÄ±sÄ±nÄ± silerdi.
>   Yedek alÄ±ndÄ±: `docker-compose.override.yml.bak.1784543819`. DOÄRU komut (Google bloÄŸu korunur):
>   ```bash
>   cd /opt/supabase/docker && cp docker-compose.override.yml docker-compose.override.yml.bak.$(date +%s) && cat > docker-compose.override.yml <<'EOF'
>   services:
>     studio:
>       ports:
>         - "127.0.0.1:3000:3000"
>     auth:
>       environment:
>         GOTRUE_EXTERNAL_GOOGLE_ENABLED: "true"
>         GOTRUE_EXTERNAL_GOOGLE_CLIENT_ID: ${GOTRUE_EXTERNAL_GOOGLE_CLIENT_ID}
>         GOTRUE_EXTERNAL_GOOGLE_SECRET: ${GOTRUE_EXTERNAL_GOOGLE_SECRET}
>         GOTRUE_EXTERNAL_GOOGLE_REDIRECT_URI: https://ihaleglobal.com/auth/v1/callback
>         GOTRUE_MAILER_SUBJECTS_CONFIRMATION: "E-posta adresinizi doÄŸrulayÄ±n Â· Ä°haleGlobal"
>         GOTRUE_MAILER_SUBJECTS_RECOVERY: "Åifre sÄ±fÄ±rlama Â· Ä°haleGlobal"
>         GOTRUE_MAILER_SUBJECTS_MAGIC_LINK: "GiriÅŸ baÄŸlantÄ±nÄ±z Â· Ä°haleGlobal"
>         GOTRUE_MAILER_SUBJECTS_EMAIL_CHANGE: "E-posta deÄŸiÅŸikliÄŸini onaylayÄ±n Â· Ä°haleGlobal"
>         GOTRUE_MAILER_TEMPLATES_CONFIRMATION: "https://ihaleglobal.com/email/onay.html"
>         GOTRUE_MAILER_TEMPLATES_RECOVERY: "https://ihaleglobal.com/email/sifirlama.html"
>   EOF
>   docker compose up -d auth
>   ```
>   DoÄŸrulama: (1) yeni kayÄ±t denemesi â†’ mail TÃ¼rkÃ§e; (2) **Google ile giriÅŸ de test edilmeli** (bu blok
>   riske girdi). Geri alma: `cp docker-compose.override.yml.bak.1784543819 docker-compose.override.yml
>   && docker compose up -d auth`.
> - **â“ "BoÅŸ Ã§Ä±kan link":** anon reprodÃ¼ksiyon yapÄ±lamadÄ± (Ã¼ye linkleri maskeli); sayfadaki tÃ¼m href'ler
>   geÃ§erli gÃ¶rÃ¼ndÃ¼. KullanÄ±cÄ±dan hangi link/URL olduÄŸu soruldu.

## ğŸŸ¢ ÅU AN NE DURUMDAYIZ (16 Temmuz 2026, en son gÃ¼ncelleme) â€” HERKES Ã–NCE BUNU OKUSUN

> Bu blok her oturumun sonunda gÃ¼ncellenir ve dosyanÄ±n en gÃ¼ncel/otoriter Ã¶zetidir. AltÄ±ndaki
> binlerce satÄ±r tarihsel kayÄ±t/detay â€” Ã§eliÅŸki olursa BU BLOK geÃ§erlidir.
> **KALICI TALÄ°MAT (12 Tem, kullanÄ±cÄ± emri):** Bu blok + ilgili bÃ¶lÃ¼mler her oturumda otomatik
> gÃ¼ncellenir, kullanÄ±cÄ± hatÄ±rlatmak zorunda deÄŸil. Bkz. hafÄ±za `yapilacaklar-auto-update`.

> ## ğŸ—ºï¸ 20 TEMMUZ â€” DASHBOARD Ä°L FÄ°LTRESÄ° Ã–LÃœYDÃœ, DÃœZELTÄ°LDÄ° (âœ… dashboard.html)
> **HATA:** `ilDropdownDoldur()` il listesini `sb.from('ilanlar').select('il')...order('il')` ile
> **limit'siz** Ã§ekiyordu. PostgREST ~1000 satÄ±r tavanÄ±na takÄ±lÄ±yor; il'e gÃ¶re sÄ±ralÄ± ilk 1000 satÄ±rÄ±n
> **tamamÄ± ADANA** olduÄŸu iÃ§in dropdown `["", "ADANA"]` ile kalÄ±yordu â†’ dashboard alt tablosunun il
> filtresi hem ihale hem yeni DT modunda **fiilen iÅŸlevsizdi** (misafirde canlÄ± doÄŸrulandÄ±).
> **Ã‡Ã–ZÃœM:** ihaleler.html'in zaten kullandÄ±ÄŸÄ± statik 81-il listesi (`TR_ILLER`) + `.toLocaleUpperCase('tr')`.
> AÄŸ turu yok, client-load-all deseni yok. **RPC deÄŸil statik seÃ§ildi Ã§Ã¼nkÃ¼** bu dropdown TEK deÄŸerle
> Ä°KÄ° tabloyu birden filtreliyor (`ilanlar.il` + `dogrudan_temin_ilanlari.il`, ikisi de `.eq`) â€”
> `il_sayim()` yalnÄ±z ihale, `dt_il_sayim()` yalnÄ±z DT tarafÄ±nÄ± verirdi.
> **DOÄRULAMA (misafir tarayÄ±cÄ±, canlÄ± anon anahtarÄ±):** 81 seÃ§enek; 81'inin **tamamÄ±** iki tabloda da
> sonuÃ§ dÃ¶ndÃ¼rÃ¼yor (Ã¶lÃ¼ seÃ§enek 0). Ä°hale modu 13.486 â†’ ANKARA 1.186 Â· DT modu 95.606 â†’ ANKARA 6.290
> (doÄŸrudan API sayÄ±mÄ±yla birebir) â†’ ÅANLIURFA 2.871 Â· Ä°STANBUL 12.407. Konsol hatasÄ±z.
> **YAN BULGU (veri kalitesi, ayrÄ± iÅŸ):** `ilanlar.il`'de dropdown'a girmeyen 2 bozuk deÄŸer var â€”
> `''` (84 satÄ±r) ve tekil **`'Ä°ZMIR'`** (1 satÄ±r, yanlÄ±ÅŸ bÃ¼yÃ¼k harf; doÄŸrusu `Ä°ZMÄ°R` = 26.292).
> DT tarafÄ± temiz (81/81 birebir). Bu satÄ±rlar hiÃ§bir il filtresinde gÃ¶rÃ¼nmÃ¼yor.
> **AÃ‡IK:** `TR_ILLER` artÄ±k dashboard.html + ihaleler.html'de Ä°KÄ° KOPYA â€” kategoriler.js gibi tek
> kaynaÄŸa (`js/iller.js`) Ã§ekilmeli; bu iÅŸ kapsam dÄ±ÅŸÄ± bÄ±rakÄ±ldÄ±.

> ## ğŸ›ï¸ 19 TEMMUZ â€” "Ä°DARE TÃœRÃœ" FÄ°LTRESÄ° CANLI (âœ… ihaleler + doÄŸrudan temin)
> KullanÄ±cÄ±nÄ±n baÅŸtan beri istediÄŸi "sadece belediyeler / sadece hastaneler" aramasÄ± Ã§alÄ±ÅŸÄ±yor.
> **TASARIM:** denormalize `idare_tur` kolonu (join/view DEÄÄ°L) â€” mevcut PostgREST desenine
> (.eq('il')/.eq('kategori')) birebir oturdu, frontend'e tek satÄ±r eklendi. `idare_tur_tazele()`
> eÅŸleme tablosundan iki ana tabloyu gÃ¼nceller (IS DISTINCT FROM â†’ yalnÄ±z deÄŸiÅŸenler).
> **CANLI RAKAMLAR** (tarama %10'dayken): ihaleler 44.569 sÄ±nÄ±flÄ± (belediye 7.764 Â· il Ã¶zel idare
> 6.109 Â· saÄŸlÄ±k 5.217 Â· KÄ°T 3.978 Â· milli eÄŸitim 3.528 Â· Ã¼niversite 3.340); **DT 345.453 sÄ±nÄ±flÄ±**
> (belediye 75.470 Â· Ã¼niversite 62.537). Tarama ilerledikÃ§e kapsama orantÄ±lÄ± artacak.
> **Ä°KÄ° CANLI HATA YAKALANDI VE DÃœZELTÄ°LDÄ°:**
> 1. `idare_normalize` gÃ¶vdesinde `tr_fold` ÅŸema-niteliksizdi â†’ ifade indeksi KURULMADI
>    ("function tr_fold(text) does not exist" index build sÄ±rasÄ±nda). â†’ `public.tr_fold` (_fix.sql).
> 2. **Yeni kolon kolon-GRANT'a girmiyor** â†’ filtre seÃ§ilince misafirde 42501, sayfa boÅŸ. PostgREST
>    WHERE iÃ§in de SELECT yetkisi ister. â†’ `GRANT SELECT (idare_tur)` (_grant.sql). **KALICI KURAL:**
>    bu iki tabloya kolon eklendiÄŸinde grant dosyasÄ±na da satÄ±r ekle. Bkz [[anon-maske-iki-kok-neden]].
>    GÃ¼venlik: tÃ¼r bir KATEGORÄ°, kimlik deÄŸil â€” `idare` misafire kapalÄ± kalmaya devam ediyor.
> **DETSÄ°S TAM TARAMA:** Webshare "government sites" eÅŸiÄŸine takÄ±lÄ±p durmuÅŸtu; kullanÄ±cÄ± kimlik
> doÄŸrulamasÄ±nÄ± tamamladÄ±, havuz tekrar aktif (100/100 IP, 0 hata) ve tarama devam ediyor.
> **SIRADAKÄ°:** tarama bitince `--yaz` + `idare_tur_tazele()` Â· gece tazeleme + boÅŸluk raporu
> run_scraper.sh'e Â· kalan "bilinmiyor"lara AI katmanÄ± Â· kurum-analiz/idareler dizinine tÃ¼r rozeti.

> ## ğŸ›ï¸ 18 TEMMUZ (gece) â€” Ä°DARE TÃœRÃœ SINIFLANDIRMASI: altyapÄ± hazÄ±r, TAM TARAMA Ã‡ALIÅIYOR
> Hedef: "kurumlarÄ± EKAP'taki gibi kategorize et" â†’ ihalelerde "sadece belediyeler/hastaneler" filtresi.
> **EKAP'ta hazÄ±r tÃ¼r filtresi YOK** (Ä°dare SeÃ§=tek tek kurum, Kapsam=4734 yasal kapsam) â†’ kendimiz kurduk.
> **Ã‡Ã–ZÃœLEN ZÄ°NCÄ°R** (hafÄ±za: [[ekap-detsis-idare-tur]] â€” pahalÄ±ya mal oldu, tekrar arama):
>   DetsisAgaci (87.528 kayÄ±t: idareId+ad+detsisNo) â†’ GetListByParameters **idareKodList=[idareId]**
>   â†’ o kurumun ihaleleri â†’ `idareAdi` bizim `ilanlar.idare` ile AYNI STRING â†’ eÅŸleÅŸme kesin.
> **3 TUZAK:** (1) "idareKod" DETSÄ°S No DEÄÄ°L idareId (detsisNo/idâ†’0 sonuÃ§); (2) **0 sonuÃ§ "filtre Ã§alÄ±ÅŸtÄ±"
> demek DEÄÄ°L** â€” eÅŸleÅŸmeyen deÄŸer de 0 dÃ¶ner, ilk testim bu yanlÄ±ÅŸ-pozitifle doÄŸru anahtarÄ± atlamÄ±ÅŸtÄ±;
> (3) ad ile join ambigÃ¼ ("BÄ°LGÄ° Ä°ÅLEM DAÄ°RE BAÅKANLIÄI" DETSÄ°S'te 114 kez).
> **GENEL TEKNÄ°K:** bilinmeyen API alanÄ±nÄ± TAHMÄ°N ETME (15 payload+6 ad boÅŸa gitti) â†’ **Angular bundle'Ä±nÄ±
> oku** (/951.*.js iÃ§inde arama modeli aÃ§Ä±kÃ§a yazÄ±lÄ±). TLS: EKAP zayÄ±f cipher â†’ ekap_ssl_baglami() ÅŸart.
> **TÃœR Ã‡IKARIMI DETSÄ°S'Ä°N UZUN ADINDAN** (Ã¼st kurum zinciri iÃ§erir): "Ä°DARÄ° VE MALÄ° Ä°ÅLER DAÄ°RESÄ°
> BAÅKANLIÄI" (jenerik) â†’ "â€¦KAMU Ä°HALE KURUMU" â†’ diger_kamu âœ“ â€” kural motorunun Ã§Ã¶zemediÄŸi durum.
> **YAZILANLAR:** migration_idare_tur.sql (+_fix: idare_normalize'da ÅŸema-nitelikli tr_fold, yoksa ifade
> indeksi kurulmuyor) Â· idare_tur_siniflandir.py (14 tÃ¼r, 741 kelime, 14 ajanlÄ±k envanter; su idaresi
> kÄ±saltma tuzaÄŸÄ± ESKÄ°/BASKI korumalÄ±) Â· ekap_detsis_cek.py (async, 24 iÅŸÃ§i, proxy havuzlu, checkpoint'li).
> **MÄ°MARÄ° (kullanÄ±cÄ± itirazÄ±yla):** tek seferlik dump bayatlar â†’ (a) gece tazeleme (b) idare_tur_bosluk()
> yeni-birim alarmÄ± (c) boÅŸluk kural/AI ile geÃ§ici sÄ±nÄ±flanÄ±r, `kaynak` alanÄ± kesin/geÃ§ici ayrÄ±mÄ±nÄ± tutar.
> **PERF DERSÄ°:** sÄ±ralÄ± 1.6 istek/sn â†’ 15 saat; darboÄŸaz havuz deÄŸil tek-akÄ±ÅŸÃ—600ms â†’ async 24 iÅŸÃ§i ~2,5 saat.
> **DURUM:** tam tarama VDS'te sÃ¼rÃ¼yor (proxy 100/100 IP, 0 hata, VDS IP'si kullanÄ±lmÄ±yor).
> **SIRADAKÄ° (sabah):** `--yaz` â†’ tabloya bas Â· gece tazeleme+boÅŸluk raporu run_scraper.sh'e Â· arayÃ¼zde
> "Ä°dare TÃ¼rÃ¼" filtresi (Ä°haleler/DT/Ä°dareler) Â· kalan "bilinmiyor"lara AI katmanÄ±.

> ## ğŸ§­ 18 TEMMUZ â€” HS HÄ°YERARÅÄ°SÄ° + TÃœM ETÄ°KETLER TÃœRKÃ‡E + ğŸ”´ KIRPILMA HATASI (âœ… CANLI, 792bac0)
> KullanÄ±cÄ±: "alt pozisyonu pozisyona, pozisyonu fasÄ±la baÄŸlayalÄ±m, aramalarÄ± Ã¶yle kategorize edelim."
> **ğŸ”´ Ã–NCE BULUNAN GÄ°ZLÄ° HATA:** `detayAc` `.limit(4000)` diyordu ama **PostgREST 1000-satÄ±r tavanÄ±
> `.limit()`'i eziyor** â†’ HS6 drill-down bÃ¼yÃ¼k ortaklarda SESSÄ°ZCE kÄ±rpÄ±yordu: **DEU 478 kalem
> gÃ¶steriyordu, gerÃ§eÄŸi 4.910** (16.450 ham satÄ±r); USA/ITA/ROU aynÄ±. SÄ±ralama ve DeÄŸiÅŸim de bu kÄ±rpÄ±k
> alt kÃ¼meye gÃ¶reydi. **KURAL: `.limit(>1000)` gÃ¶rdÃ¼ÄŸÃ¼n her sorgu zaten kÄ±rpÄ±ktÄ±r â†’ jsonb RPC'ye taÅŸÄ±.**
> **backend/migration_hs_hiyerarsi.sql (kullanÄ±cÄ± uyguladÄ±, CANLI):** ticaret_hs_kalem / ticaret_hs_ulkeler
> / ticaret_hs_fasil + `hs6 text_pattern_ops` indeksi (LIKE prefix iÃ§in ÅŸart) + timeout.
> **ETÄ°KETLER:** fasÄ±l (97) + pozisyon (1.229) Ä°ngilizceydi â†’ GTÄ°P Ã¼slubunda TÃ¼rkÃ§eleÅŸtirildi
> (3 workflow / 33 ajan: 1.326 Ã§eviri + 465 diakritik dÃ¼zeltme). **6.939 kodun tamamÄ± TÃ¼rkÃ§e.**
> DERS: ajan Ã§Ä±ktÄ±sÄ± diakritiksiz gelebilir; tespitte kelime listesi deÄŸil "15+ karakter, hiÃ§ Ã§ÄŸÄ±Ã¶ÅŸÃ¼ yok"
> kuralÄ± kullan (kelime listesi 265'in 200'Ã¼nÃ¼ kaÃ§Ä±rdÄ±).
> **HÄ°YERARÅÄ°:** arama 3 seviyede (ğŸ“šFasÄ±l/ğŸ“‚Pozisyon/ğŸ“¦Kalem rozetli; eskiden `kod.length!==6 continue`
> ile 2/4-hane atlanÄ±yordu â†’ "makine" 0 sonuÃ§, ÅŸimdi 423 / "Ã§elik" 338); fasÄ±l seÃ§ince o fasÄ±ldaki TÃœM
> kalemlerin toplamÄ± sorgulanÄ±r; fasÄ±l filtresi + satÄ±r breadcrumb'Ä± ("Makineler â€º Aksam ve parÃ§alar").
> **CanlÄ± doÄŸrulama:** DEU 4.910 kalem, 98 fasÄ±l seÃ§eneÄŸi, FasÄ±l 84 â†’ 537 kalemin toplamÄ± / 169 Ã¼lke
> (Almanya $3 Mr), Pozisyon 8407 â†’ 8 kalemin toplamÄ±. Geriye dÃ¶nÃ¼k uyumlu (RPC yoksa eski yol + uyarÄ±).
> **SIRADAKÄ° (kullanÄ±cÄ± istedi):** kurumlarÄ± EKAP'taki gibi kategorize et.

> ## ğŸ” 18 TEMMUZ â€” SECRET ROTASYONU (JWT+anon+service) âœ… CANLI + DB PAROLASI Ä°PTAL (3 ders)
> Studio ifÅŸasÄ± borcu kapandÄ±. **YapÄ±ldÄ±:** keygen (HS256/stdlib, kullanÄ±cÄ± Ã¼retti â€” ben yalnÄ±z public anon'u
> gÃ¶rdÃ¼m) â†’ 24 HTML + 6 JS'te anon key yenilendi + `?v=rot1` cache-bust (commit 211f81a) â†’ VDS `.env` 3 deÄŸer
> + `docker compose up -d` + `ihale-api` restart. **DoÄŸrulandÄ±: eski anon 401 / yeni anon 200**, tÃ¼m sayfa+JS
> yeni imza, REST+RPC+auth 200, konsol temiz.
> **DB parolasÄ± (Faz 2b) DENENDÄ° â†’ Ä°PTAL.** KÄ±sa bir kesinti yaÅŸandÄ±, kÃ¶k nedenler ve KALICI DERSLER:
> 1. **Stack restart sonrasÄ± kong'u da restart et.** `docker compose up -d` rest/auth'u yeniden yaratÄ±r, kong'u
>    yaratmaz â†’ kong bayat upstream'e bakar â†’ container'lar "healthy" iken TÃœM REST/RPC **502**. TeÅŸhis: yanlÄ±ÅŸ
>    anahtar 401 (kong ayakta) + doÄŸru anahtar 502 (upstream Ã¶lÃ¼). Ã‡Ã¶zÃ¼m: `docker compose restart kong`.
> 2. **`postgres` bu sÃ¼rÃ¼mde SUPERUSER DEÄÄ°L** â€” `supabase_admin` superuser. AyrÄ±calÄ±klÄ± rollerde ALTER iÃ§in
>    `-U supabase_admin` ÅŸart (yoksa "Only superusers can alter privileged roles").
> 3. **Yer-tutuculu yÄ±kÄ±cÄ± komut bloklarÄ±na ABORT guard konulmalÄ±** â€” `<...buraya>` doldurulmadan Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±,
>    sed `.env`'e Ã§Ã¶p yazdÄ±. (Åans: ALTER hata verip rollback oldu â†’ DB rolleri deÄŸiÅŸmedi, `.env` geri yazÄ±lÄ±nca
>    tamamen dÃ¼zeldi, veri kaybÄ± yok.)
> **KARAR:** DB parolasÄ± dÃ¶ndÃ¼rÃ¼lmeyecek â€” 5432/6543 dÄ±ÅŸarÄ±ya kapalÄ± olduÄŸu iÃ§in sÄ±zmÄ±ÅŸ parola uzaktan
> kullanÄ±lamaz (fayda ~0), risk kanÄ±tlandÄ±. Kritik olan JWT/service rotasyonu tamam.

> ## ğŸ” 17 TEMMUZ â€” SECRET ROTASYONU YAPILDI (JWT+anon+service) âœ… CANLI, commit `211f81a`
> Studio ifÅŸasÄ±nÄ±n (16 Tem) aÃ§Ä±k kalan tek borcu kapandÄ±. **Risk modeli:** anon key zaten public â€”
> tek baÅŸÄ±na dÃ¶ndÃ¼rmek anlamsÄ±z; asÄ±l sÄ±zan service_role + JWT_SECRET (Studio â†’ Settings/API sayfasÄ±).
> JWT_SECRET sÄ±zdÄ±ysa saldÄ±rgan HER token'Ä± Ã¼retebilir â†’ JWT_SECRET dÃ¶nmeli â†’ anon+service yeniden imzalanÄ±r.
> **SÃ¼reÃ§ (iÅŸleyen reÃ§ete):** (0) kullanÄ±cÄ± stdlib-only keygen script'i Ã§alÄ±ÅŸtÄ±rÄ±r (HS256, dÄ±ÅŸ baÄŸÄ±mlÄ±lÄ±k yok),
> bana YALNIZ anon key'i verir; (1) ben 24 HTML + 6 JS'te anon key swap + 6 JS'i `?v=rot1`'e normalize
> (cache-bust) â†’ push, VDS'e PULL ETMEDEN (site eski anahtarla ayakta); (2) kullanÄ±cÄ± VDS'te
> `/opt/supabase/docker/.env` 3 deÄŸeri sed + `docker compose up -d` â†’ HEMEN `git pull` + backend/.env
> service key + `systemctl restart ihale-api`. Kesinti ~saniyeler.
> **CACHE KEÅFÄ° (planÄ± kolaylaÅŸtÄ±rdÄ±):** HTML edge-cache'siz (`cf-cache-status: DYNAMIC`) â†’ yeni anon
> anÄ±nda; yalnÄ±z 6 JS cache'li (max-age=14400) â†’ `?v` bump yeterli, Cloudflare purge GEREKMEZ.
> **CanlÄ± doÄŸrulama:** eski anonâ†’**401**, yeni anonâ†’**200**; 24/24 sayfa 200; REST(3 tablo)+6 RPC 200;
> ihaleler 375 kayÄ±t; ticaret-analiz 26-yÄ±l dropdown+169 Ã¼lke+HS6 sÄ±ralama; firma-analiz 82.123 firma
> (misafir maskeleme `ğŸ”’ ***` Ã§alÄ±ÅŸÄ±yor); konsol 0 hata; ihale-api active, /api/docs 200.
> **DERSLER:** (a) msys `grep -oE` grup-quantifier'da yanÄ±ltÄ±r â†’ toplu doÄŸrulamayÄ± Python'la yap;
> (b) `perl -i` Windows'ta Ã§oklu-dosyada sessizce no-op â†’ byte-dÃ¼zeyi Python replace kullan (CRLF de korunur);
> (c) eÅŸzamanlÄ± oturum rotasyon commit'inin ÃœSTÃœNE push edebilir â†’ VDS'te eski-imza taramasÄ± ÅART (0 Ã§Ä±ktÄ±).
> **â³ AÃ‡IK â€” FAZ 2b (DB parolasÄ±):** POSTGRES_PASSWORD DÃ–NMEDÄ°. KullanÄ±cÄ± "yapalÄ±m" dedi, keÅŸif adÄ±mÄ±
> bekliyor. **DÄ°KKAT â€” risk/fayda:** fayda DÃœÅÃœK (5432/6543 dÄ±ÅŸarÄ±ya kapalÄ±, [[origin-hardening]] â†’
> sÄ±zmÄ±ÅŸ parola uzaktan kullanÄ±lamaz); risk YÃœKSEK (authenticator/supabase_auth_admin/supabase_storage_admin/
> supabase_admin/pooler rolleri aynÄ± parolayÄ± paylaÅŸÄ±r; `.env` deÄŸiÅŸip roller ALTER edilmezse o servis Ã§Ã¶ker).
> SÄ±ra: Ã¶nce rol keÅŸfi (compose'da `://rol:${POSTGRES_PASSWORD}` grep + pg_roles), sonra ALTER+env+restart.
> **NOT (kullanÄ±cÄ± kararÄ±):** yeni JWT_SECRET+service key kullanÄ±cÄ± terminali yapÄ±ÅŸtÄ±rÄ±nca sohbete dÃ¼ÅŸtÃ¼;
> kullanÄ±cÄ± bunu KABUL ETTÄ° (chat-log maruziyeti, Studio kadar geniÅŸ deÄŸil), yeniden rotasyon YAPILMAYACAK.

> ## ğŸ“ˆ âœ… YAPILDI (17 Tem) â€” TÄ°CARET-ANALÄ°Z Ä°KÄ° Ä°Å (CANLI, 8b4d281)
> 1. **HS6 kalem tablosu sÃ¼tun sÄ±ralama âœ…** â€” drill-down baÅŸlÄ±klarÄ± (Kalem/Ä°hr./DeÄŸiÅŸim/Ä°th./DeÄŸiÅŸim)
>    tÄ±klanÄ±nca sÄ±ralar (detaySirala + yoyNum + ok gÃ¶stergesi; sorgu tablosuyla aynÄ± desen). Yeni Ã¼lke
>    aÃ§Ä±lÄ±nca ihracat-azalan sÄ±fÄ±rlanÄ±r; "ilk 400" notu artÄ±k seÃ§ili sÄ±ralamaya gÃ¶re. CanlÄ± test: DEU
>    Ä°hr.â–¼ / Ä°th.â–¼ / DeÄŸiÅŸimâ–¼(â–²%91â†’82â†’62) / yÃ¶n Ã§evirme Ã§alÄ±ÅŸÄ±yor.
> 2. **YÄ±l kÄ±yaslama "algoritma hatasÄ±" â€” MATEMATÄ°K DOÄRU Ã‡IKTI, sorun ETÄ°KETLEMEYDÄ°.** Veriyle doÄŸrulandÄ±:
>    ticaret_liste(Y,K) kÄ±yas deÄŸerleri backfill sonrasÄ± birebir tutuyor (2023 ihr = sonraki sorgunun
>    kÄ±yas'Ä±; aynÄ± yÄ±l â†’ yuzde guard). Ana Ã¼lke listesi + sektÃ¶r YoY'si DOÄRU. TEK GERÃ‡EK sorun: HS6 drill-
>    down "DeÄŸiÅŸim"i dis_ticaret_hs YALNIZ 2 yÄ±l (2023,2024) iÃ§erdiÄŸinden SABÄ°T 2023â†’2024 hesaplÄ±yor, Ã¼stteki
>    yÄ±l seÃ§icisinden BAÄIMSIZ â†’ "yanlÄ±ÅŸ" izlenimi. FÄ°X: baÅŸlÄ±k tooltip + dipnot "DeÄŸiÅŸim = 2023â†’2024 (Ã¼st
>    seÃ§imden baÄŸÄ±msÄ±z)" ile aÃ§Ä±k etiketlendi. AÃ‡IK SEÃ‡ENEK (kullanÄ±cÄ±ya sorulacak): HS6'yÄ± yÄ±l dropdown'Ä±na
>    baÄŸlamak = tÃ¼m yÄ±llar iÃ§in HS6 backfill (~2 yÄ±lâ‰ˆ761K satÄ±r â†’ 26 yÄ±l ~10M satÄ±r, aÄŸÄ±r) gerektirir; ÅŸimdilik
>    2-yÄ±l sabit + aÃ§Ä±k etiket yeterli gÃ¶rÃ¼ldÃ¼.

> ## ğŸ—ºï¸ğŸ› 17 TEMMUZ â€” HARÄ°TA "Ä°LE TIKLA" Ã–LÃœYDÃœ: svg-zoom pointer-capture BUG'Ä± (âœ… FÄ°X CANLI, 4ae7ace)
> KullanÄ±cÄ±: iki haritada da ile tÄ±klayÄ±nca panel "Bir ile tÄ±klayÄ±n"da kalÄ±yor. KÃ–K NEDEN: js/svg-zoom.js
> `pointerdown`'da `setPointerCapture` alÄ±yordu â†’ capture aktifken tarayÄ±cÄ± click'i path yerine SVG'ye
> hedefler â†’ path'lerdeki click dinleyicileri GERÃ‡EK fare tÄ±klamasÄ±nda hiÃ§ ateÅŸlenmez. svg-zoom eklendiÄŸinden
> beri (16 Tem gece) tÃ¼m choropleth tÄ±klamalarÄ± Ã¶lÃ¼ydÃ¼. **KRÄ°TÄ°K TEST DERSÄ°: `el.dispatchEvent(new MouseEvent
> ('click'))` ile doÄŸrulama SAHTE-POZÄ°TÄ°F** â€” dispatch doÄŸrudan path'e gider, capture retarget'ini atlar;
> harita doÄŸrulamalarÄ± bu yÃ¼zden "Ã§alÄ±ÅŸÄ±yor" gÃ¶rÃ¼nmÃ¼ÅŸtÃ¼. GerÃ§ek-tÄ±klama testi iÃ§in tam pointer dizisi +
> `svg.hasPointerCapture(id)` kontrolÃ¼ kullan. FÄ°X: capture yalnÄ±z GERÃ‡EK pan (1px+ hareket) / pinch
> baÅŸlayÄ±nca alÄ±nÄ±r; temiz tÄ±k path'e gider, sÃ¼rÃ¼kleme-sonrasÄ± tÄ±k yutma (surukledi) korunur.
> svg-zoom.js?v=2 (4 sayfa: harita, firma-analiz, ticaret-analiz, uluslararasi). CanlÄ± doÄŸrulandÄ±:
> pointerdownâ†’capture YOK + Ankara panel 8.428 firma.

> ## ğŸ”§ 17 TEMMUZ â€” VDS ARTIK Ä°ÅLERÄ° KAPANDI (kullanÄ±cÄ± SSH'la koÅŸtu, 3/3 âœ…)
> GeÃ§miÅŸ oturum artÄ±klarÄ± Ã¶nce repoya alÄ±ndÄ± (49cca01: ticaret_backfill.py + 2 ticaret migration +
> harden_origin/persist.sh; VDS'teki elle kopyalanmÄ±ÅŸ ESKÄ° ticaret_backfill.py /tmp'ye yedeklendi).
> SÄ±nÄ±flandÄ±rÄ±cÄ± prod SSH sistem/DB komutlarÄ±nÄ± chat onayÄ±yla bile blokladÄ± â†’ kullanÄ±cÄ±ya hazÄ±r komut
> bloÄŸu verildi, kendisi koÅŸtu (Ä°ÅLEYEN REÃ‡ETE):
> 1. **DOCKER-USER reboot kalÄ±cÄ±lÄ±ÄŸÄ± âœ…** â€” harden_persist.sh: systemd oneshot enabled+active,
>    8000/8443/5432/6543 DROP'larÄ± artÄ±k reboot'ta geri gelir. (Ubuntu "restart required" hÃ¢lÃ¢ bekliyor â€”
>    kernel; firewall aÃ§Ä±sÄ±ndan reboot artÄ±k gÃ¼venli.)
> 2. **migration_ticaret_iso2.sql âœ…** â€” kolon zaten vardÄ±, RPC+GRANT eklendi; canlÄ± doÄŸrulandÄ±:
>    ticaret_liste artÄ±k iso2 dÃ¶ndÃ¼rÃ¼yor (DE/US).
> 3. **Ticaret full backfill âœ… TAMAMLANDI** â€” ticaret_yillar artÄ±k [2000..2025], guncel_yil=2025
>    (REST'ten doÄŸrulandÄ±). YÄ±l dropdown'Ä± kendiliÄŸinden doldu; cron tazelemesi --sadece-guncel ile.

> ## ğŸ­ 17 TEMMUZ (gece) â€” MÄ°SAFÄ°R MASKELEME: KÄ°LÄ°T ALANLAR '***' (âœ… CANLI, ihaleciler modeli)
> KullanÄ±cÄ±: "giriÅŸsiz okunmasÄ±n â€” ilanlarÄ±n kurumlarÄ±, sonuÃ§lar ve yÃ¼klenici verileri **** gÃ¶rÃ¼nsÃ¼n,
> baÅŸlÄ±k kalsÄ±n." Veri-koruma paketi 3/3 â€” SUNUCU TARAFI kolon yetkisiyle (yalnÄ±z frontend maskesi deÄŸil).
> **backend/migration_anon_maske.sql (âœ… canlÄ±, rol testleri geÃ§ti):** anon'a kolon-listeli GRANT:
> - ilanlar: idare/ekap_id/ikn/ilan_metni/ilan_html/yapay_zeka_ozeti/arama_fold/yayinlayan_id KAPALI
>   (arama_fold iÃ§inde Ä°DARE geÃ§iyor; WHERE de yetki istediÄŸinden idare-filtre oracle'Ä± otomatik kapalÄ±)
> - ihale_sonuclari: kazanan_firma(+fold)/yuklenici_*/tum_teklifler/ham_json/ekap_id/ikn/ihale_id KAPALI
>   (tum_teklifler TÃœM katÄ±lÄ±mcÄ± firmalarÄ± iÃ§eriyordu!) â€” bedel/tenzilat/tarih/katÄ±lÄ±mcÄ± sayÄ±sÄ± AÃ‡IK
> - yukleniciler: ad/normalize_ad/arama_fold/vergi_no/ai_yorum KAPALI â€” il/ciro/sÃ¶zleÅŸme/tarih AÃ‡IK
> - DT: idare KAPALI; RPC kilitleri: il_sektor_firmalar/analiz_pivot/kurum_ozet/rekabet_ozet(top-20 idare
>   dÃ¶ndÃ¼rÃ¼yordu!)/ihaleye_uygun_firmalar(_geo); MV: idare_ozet_mv + il_sektor_firma_mv anon'dan REVOKE
> **Frontend (12 sayfa):** misafirde dar select + 'ğŸ”’ ***' + login linki: ihaleler (kart KayÄ±t No/Ä°dare/
> Kazanan ***, aramaâ†’baslik+aciklama ilike, idare filtresi disabled), ihale-detay (eyebrow/idare/kazanan ***,
> ilan metni 'Ã¼yelere Ã¶zel'), sonuclananlar, dogrudan-temin, firma-analiz (dizin adlarÄ± ***, sayÄ±lar aÃ§Ä±k;
> arama+detay+ad-sÄ±ralama kapÄ±lÄ±; fah panel giriÅŸ notu), harita (panel firma listeleri giriÅŸ notu; boyama/
> KPI/RFQ misafirde tam), kurum-analiz (tam kapÄ±), dashboard (gereksiz idare/ekap_id select'ten atÄ±ldÄ±);
> takipte/bildirimler/teklif-olustur misafir-localStorage akÄ±ÅŸlarÄ± Ã§Ã¶kmez (koÅŸullu select, render 'â€”').
> rekabet-analizi + uyumluluk ZATEN Pro-kilitli (dokunulmadÄ±). GiriÅŸli kullanÄ±cÄ±da SIFIR deÄŸiÅŸiklik.
> **backend/migration_anon_maske_index.sql (âœ… canlÄ±):** DEPLOY SONRASI YAKALANAN BUG â€” sonuclananlar misafir
> dalÄ± (WHERE kazanan_teklif NOT NULL) eski partial indexlerle (WHERE kazanan_firma NOT NULL) eÅŸleÅŸmedi â†’
> 537K full-sort â†’ 57014 â†’ 3 anon-predicate'li ikiz index (idx_is_tarih/bedel/tenzilat_anon), EXPLAIN âœ“.
> **CanlÄ± misafir testleri:** API: idare/kazanan_firma/ad/tum_teklifler/select=*/idare-filtre â†’ hepsi 401;
> baslik/bedel/il â†’ 200. TarayÄ±cÄ±: ihaleler 25 kart ***, arama 'yol' Ã§alÄ±ÅŸÄ±yor, detay maskeli+belge akÄ±ÅŸÄ±,
> sonuclananlar ***+bedel aÃ§Ä±k, DT 1.17M kayÄ±t ***, firma dizini 50 satÄ±r *** (ciro aÃ§Ä±k, arama kilitli,
> satÄ±ra tÄ±klaâ†’kapÄ±), harita 81 il boyalÄ±+panel kilitli, kurum-analiz kapÄ±lÄ±. Konsolda perm hatasÄ± yok.
> NOT: <title> kurum adÄ±nÄ± URL param'dan gÃ¶sterir (DB sÄ±zÄ±ntÄ±sÄ± deÄŸil). kik-kararlar/uluslararasi/kamu-
> ihaleleri kapsam dÄ±ÅŸÄ± bÄ±rakÄ±ldÄ± (kamu kararÄ±/AB verisi/KA duyurularÄ± â€” kullanÄ±cÄ± sayarsa eklenir).

> ## ğŸ›ï¸ âœ… YAPILDI (16 Tem) â€” Ä°DARELER + KURUM ANALÄ°ZÄ° BÄ°RLEÅTÄ° + NAV TEKÄ°LLEÅTÄ° (Firmalar dahil)
> Firmalar deseninin aynÄ±sÄ±: **kurum-analiz.html tek hub** â€” `?kurum=` yoksa aÃ§Ä±lÄ±ÅŸ = Ä°DARE DÄ°ZÄ°NÄ°
> (idareler.html'den taÅŸÄ±ndÄ±, `iz-*` prefix: idare_dizin_json + 30dk sessionStorage + arama(trFold)/il/
> aktif/sÄ±ralama/pager + anon ğŸ”’ giriÅŸ kapÄ±sÄ± [bulk_rpc_kilit]); idareye tÄ±kla â†’ **pushState ile AYNI
> SAYFADA analiz** (kurumAc/dizineDon/popstate; grafikler destroy-korumalÄ± â€” 2. aÃ§Ä±lÄ±ÅŸta "Canvas in use"
> yok; satÄ±r tÄ±klama data-ad+delegasyon, inline onclick YOK [tÄ±rnak dersi]). Geri â†’ dizin DOM'u aynen
> (arama/filtre/sayfa korunur). **idareler.html â†’ param koruyan redirect stub.**
> **NAV TEKÄ°LLEÅTÄ° (23 sayfa):** "Ä°dareler Dizini"+"Kurum Analizi" â†’ tek **"ğŸ›ï¸ Ä°dareler"**(kurum-analiz);
> "Firmalar Dizini"+"Firma Analizi" â†’ tek **"ğŸ¢ Firmalar"**(firma-analiz). Tekil linkler de gÃ¼ncellendi
> (sektorler "Ä°dareler â†’", index harita-sekme, firma-analiz geri-btn). kamu-ihaleleri.html BÄ°LÄ°NÃ‡LÄ° atlandÄ±
> (eÅŸzamanlÄ± oturum onu stub'a Ã§eviriyor â€” pop Ã§akÄ±ÅŸmasÄ± Ã¶nlendi; eski linkleri redirect'le Ã§alÄ±ÅŸÄ±r).
> SÃ¼reÃ§: git worktree (claude/idareler-merge) + ana aÄŸaÃ§ta stashâ†’mergeâ†’pushâ†’pop. Lokal test (http.server):
> dizin+kapÄ± âœ“, ?kurum=KARAYOLLARIâ†’4.493 ihale âœ“, dizineDonâ†’kurumAc(ANKARA BÅB)â†’441 âœ“, konsol 0 hata.

> ## ğŸ”’ 16 TEMMUZ (gece) â€” CSV/VERÄ° DIÅA AKTARIMI TÃœM SAYFALARDAN KALDIRILDI (âœ… CANLI, commit `afb7b1b`)
> KullanÄ±cÄ±: "her sayfada csv indirme aÃ§Ä±k, baÅŸlÄ± baÅŸÄ±na veri sorunu â€” teklifler hariÃ§ hiÃ§bir indirme olmasÄ±n".
> **KaldÄ±rÄ±lan (11 sayfa, 286 satÄ±r):** dashboard, dogrudan-temin, firma-analiz, idareler, ihaleler,
> kik-kararlar, kurum-analiz, sektorler, sonuclananlar, takipte, uyumluluk â€” â†“CSV butonu + csvIndir() +
> csv-btn referanslarÄ± (script'le, brace-sayÄ±mlÄ± blok silme; kalan referans taramasÄ± 0).
> **BÄ°LÄ°NÃ‡LÄ° KORUNAN:** (1) teklif-olustur "ğŸ“ Word Ä°ndir" â€” kullanÄ±cÄ±nÄ±n HAZIRLADIÄI teklif (aÃ§Ä±k istisna);
> (2) dokumanlar â€” kullanÄ±cÄ±nÄ±n KENDÄ° yÃ¼klediÄŸi dosyalar; (3) ihale-detay EKAP belge linkleri â€” kaynak
> ÅŸartnameler (platform verisi deÄŸil, teklif hazÄ±rlamak iÃ§in gerekli). Yorum farklÄ±ysa kolayca kaldÄ±rÄ±lÄ±r.
> CanlÄ± doÄŸrulandÄ±: idareler/sonuclananlar'da buton yok + sayfalar Ã§alÄ±ÅŸÄ±yor + konsol temiz; teklif-olustur
> Word Ä°ndir duruyor. Paralel oturum aktifken: 11 dosya stashâ†’temiz-HEAD'de dÃ¼zenleâ†’commit(tam 11 dosya)â†’pop.
> **âœ… PAKET 2/2 DE YAPILDI (aynÄ± gece, kullanÄ±cÄ± onayÄ± "bunu da yap" â€” commit `f78d3e7`+`2b96f5e`):**
> - **RPC kilidi (migration_bulk_rpc_kilit.sql, canlÄ±da):** idare_dizin_json + idare_sayim (23K tam dizin
>   dÃ¶kÃ¼mleri) anon+PUBLIC'ten REVOKE â†’ yalnÄ±z authenticated/service_role. DÄ°KKAT: fonksiyonlar varsayÄ±lan
>   PUBLIC EXECUTE ile doÄŸar â€” yalnÄ±z "FROM anon" REVOKE YETMEZ, PUBLIC'ten de REVOKE ÅŸart. psql rol testi:
>   anonâ†’42501 red, authenticatedâ†’23067 idare âœ“. KÃ¼Ã§Ã¼k aggregate/vitrin RPC'leri bilinÃ§li aÃ§Ä±k (dosyada liste).
> - **Frontend kapÄ±larÄ±:** idareler.html misafire ğŸ”’ "Ã¼yelere Ã¶zel" kartÄ± (login / login?panel=kayit; RPC hiÃ§
>   Ã§aÄŸrÄ±lmaz â€” kapÄ± oturum kontrolÃ¼yle Ã¶nden Ã§izilir); dashboard Top Kurumlar misafirde "ğŸ”’ giriÅŸ yapÄ±n".
>   DERS: supabase-js hata FIRLATMAZ ({data,error}) â€” error kontrolsÃ¼zse kilitli RPC sessizce boÅŸ widget Ã§izer
>   (ilk deneme Ã¶yle oldu, `if (error) throw` hotfix'iyle dÃ¼zeldi).
> - **HÄ±z limiti (nginx origin, CF yerine â€” CF panosuna eriÅŸimim yok, origin'de aynÄ± etki):** `/rest/v1/*`
>   2r/s + burst 60, anahtar CF-Connecting-IP (origin CF-only olduÄŸundan gÃ¼venilir), 429. Dosyalar:
>   backend/nginx_rest_ratelimit.conf â†’ /etc/nginx/conf.d/ihale-ratelimit.conf; backend/nginx_rest_location.conf
>   â†’ /etc/nginx/snippets/ihale-rest-ratelimit.conf (ihale-locations.conf include eder; `^~` prefix regex'i
>   ezer, auth/storage/realtime limitsiz). Scraper'lar localhost:8000 â†’ ETKÄ°LENMEZ (doÄŸrulandÄ±). Test: 150
>   paralel istek â†’ 73Ã—200 + 77Ã—429 âœ“; normal gezinme (harita 81 il, dashboard) 429 gÃ¶rmedi âœ“. NOT: ardÄ±ÅŸÄ±k
>   curl dÃ¶ngÃ¼sÃ¼ limiti TETÄ°KLEMEZ (istek arasÄ± RTT > dolum hÄ±zÄ±) â€” test paralel olmalÄ± (xargs -P).
> **âš ï¸ KALAN RÄ°SK (en bÃ¼yÃ¼ÄŸÃ¼, karar gerek):** ham tablolarÄ±n anon SELECT'i aÃ§Ä±k (ilanlar 356K, ihale_sonuclari
> 537K, yukleniciler 71K, DT 1.14M...) â€” 1000'er satÄ±r sayfalamayla kopyalanabilir; hÄ±z limiti bunu yavaÅŸlatÄ±r/
> loglar ama durdurmaz (2r/s ile 2.1M satÄ±r â‰ˆ 17dk). Kesin Ã§Ã¶zÃ¼m = tablo okumalarÄ±nÄ± da login'e almak â†’ TÃœM
> misafir sayfalarÄ± giriÅŸ duvarÄ±na dÃ¶ner (Ã¼rÃ¼n kararÄ±!). Ä°stenirse reÃ§ete: anon'dan tablo SELECT REVOKE +
> sayfalara idareler-tarzÄ± kapÄ±. **NOT (diÄŸer oturuma):** idareler+kurum-analiz birleÅŸtirme planÄ±ndaki dizin
> gÃ¶rÃ¼nÃ¼mÃ¼ artÄ±k login gerektirir (idare_dizin_json kilitli) â€” hub'a idareler.html'deki girisKapisiGoster
> deseni taÅŸÄ±nmalÄ±.

> ## ğŸ—ºï¸ âœ… YAPILDI (16 Tem gece, commit `fbf8420`) â€” HARÄ°TA FÄ°RMALAR HUB'INDA (RFQ'SUZ), CANLI DOÄRULANDI
> KullanÄ±cÄ± kararÄ± uygulandÄ±: firma-analiz hub'Ä±na "ğŸ“‹ Liste / ğŸ—ºï¸ Harita" gÃ¶rÃ¼nÃ¼m geÃ§iÅŸi eklendi â€” **RFQ
> katmanÄ± YOK** (yalnÄ±z firma yoÄŸunluÄŸu + sektÃ¶r); e-SatÄ±nalma haritasÄ± (harita.html) iki katmanÄ±yla aynen.
> - Uygulama: `fah-*` prefixli gÃ¶mÃ¼lÃ¼ kopya (iframe deÄŸil; portta stil/JS Ã§akÄ±ÅŸmamasÄ± iÃ§in prefix). AynÄ± SVG
>   (js/tr-harita.js) + aynÄ± MV'li RPC'ler (il_firma_dagilimi / il_sektor_ozet / il_sektor_firmalar) â†’ tÃ¼m
>   etkileÅŸimler ~ms. tr-harita(74KB)+kategoriler+svg-zoom yalnÄ±z Harita gÃ¶rÃ¼nÃ¼mÃ¼ Ä°LK aÃ§Ä±lÄ±nca tembel yÃ¼klenir;
>   il_sektor_ozet 6h sessionStorage Ã¶nbelleÄŸi harita.html ile ORTAK anahtar (`harita_sektor_v1`).
> - AkÄ±ÅŸ: il tÄ±kla â†’ o ilde en Ã§ok iÅŸ kazanan 8 firma (genel modda kategori NULL) â†’ firmaya tÄ±kla â†’
>   window.firmaSectiClick kÃ¶prÃ¼sÃ¼yle AYNI SAYFADA analiz aÃ§Ä±lÄ±r (yenileme yok). SektÃ¶r modunda il sÄ±ralamasÄ±
>   + sektÃ¶r-iÃ§i firma listesi. Panel tÄ±klamalarÄ± delegasyonla (firma adÄ±ndaki tÄ±rnak inline onclick'i kÄ±rar).
> - CanlÄ± doÄŸrulama: toggleâ†’kurulum+boyama 3.0sn (ilk aÃ§Ä±lÄ±ÅŸ), 81/81 il boyalÄ±, Ä°stanbul paneli 7.864 firma /
>   â‚º530.6 Mr / 8 firma listesi; file:// Ã¶n-testte sektÃ¶r+il+firma+Liste-dÃ¶nÃ¼ÅŸ zinciri tamam, konsol temiz.
> - SÃ¼reÃ§ notu: eÅŸzamanlÄ± oturum aktifken `git worktree` (claude/harita-firmalar) + ana aÄŸaÃ§ta stashâ†’mergeâ†’pop
>   ile onlarÄ±n commit'siz nav deÄŸiÅŸikliÄŸi korunarak yayÄ±nlandÄ±.

> ## ğŸ¢ 16 TEMMUZ (devam) â€” FÄ°RMALAR DÄ°ZÄ°NÄ° + FÄ°RMA ANALÄ°ZÄ° BÄ°RLEÅTÄ° (CANLI, commit `6218d18`)
> KullanÄ±cÄ±: ikisi aynÄ± ekranda birleÅŸsin. **firma-analiz.html tek hub**: aÃ§Ä±lÄ±ÅŸ = firma DÄ°ZÄ°NÄ°
> (yuklenici_ozet stats + sÄ±ralanabilir yukleniciler tablosu + arama_fold + il filtre + pager, `dz-*` prefix);
> firmaya tÄ±kla â†’ aynÄ± sayfada DETAY (mevcut derin analiz + 2-firma karÅŸÄ±laÅŸtÄ±rma). goster() 'dizin'|'liste'|
> 'detay'; rota varsayÄ±lan â†’ dizin; ?yid=â†’detay, ?ara=/?firma=â†’firma-liste (deep-link korundu).
> **firmalar.html â†’ redirect** (query param korunur, dÄ±ÅŸ `?firma=` linkleri bozulmaz). CanlÄ± doÄŸrulandÄ±:
> dizin 71.384 firma cirosu-sÄ±ralÄ±, arama (kalyonâ†’19), tÄ±klaâ†’detay+karÅŸÄ±laÅŸtÄ±rma, firmalarâ†’firma-analiz redirect.
> **ERTELENDÄ° (bilinÃ§li):** menÃ¼de tek "ğŸ¢ Firmalar" tekilleÅŸtirmesi (24 sayfa nav) â€” EÅZAMANLI baÅŸka oturum
> DMO/Jandarma'yÄ± ana ilanlar'a taÅŸÄ±yÄ±p kamu nav'Ä±nÄ± deÄŸiÅŸtiriyordu (ihaleler.html dirty); bulk nav Ã§akÄ±ÅŸmasÄ±nÄ±
> Ã¶nlemek iÃ§in ayrÄ± yapÄ±lacak. Åu an iki menÃ¼ Ã¶ÄŸesi de (Firmalar Dizini + Firma Analizi) birleÅŸik sayfaya gider.

> ## ğŸ—ºï¸ 16 TEMMUZ (devam) â€” HARÄ°TA SEKTÃ–R VERÄ°SÄ° DÃœZELTÄ°LDÄ° (CANLI)
> KullanÄ±cÄ± ekran gÃ¶rÃ¼ntÃ¼sÃ¼: harita "âš ï¸ SektÃ¶r verisi yÃ¼klenemedi â€” il_sektor_ozet RPC yanÄ±t vermedi". Ä°ki kÃ¶k neden:
> 1. `migration_harita_sektor.sql` (baÅŸka oturumda repoya eklenmiÅŸ) prod DB'ye UYGULANMAMIÅTI â†’ il_sektor_ozet
>    + il_sektor_firmalar RPC'leri yoktu. UygulandÄ± (2 index + 3 fonksiyon; tr_fold/normalize_firma baÄŸÄ±mlÄ±lÄ±klarÄ±
>    mevcuttu, il_rfq_dagilimi p_kategori sÃ¼rÃ¼mÃ¼ geriye uyumlu).
> 2. il_sektor_ozet TABLE dÃ¶nÃ¼yordu â†’ ~3.4K satÄ±r PostgREST db-max-rows=1000'de KESÄ°LÄ°YORDU (yalnÄ±z 26 il).
>    **jsonb'ye Ã§evrildi** (jsonb_agg, DROP+CREATE) â†’ satÄ±r limiti yok. CanlÄ±: 3157 kayÄ±t, **81 il tamamÄ±**,
>    haritada GÄ±da sektÃ¶rÃ¼ seÃ§ilince 81 il boyanÄ±yor, uyarÄ± yok.
> NOT: il_sektor_ozet ~9s hesaplama (529Kâ‹ˆ355K count DISTINCT, statement_timeout=30s). Client sessionStorage'da
>   6 saat cache + lazy (yalnÄ±z sektÃ¶r seÃ§ince, spinner'lÄ±) â†’ kabul edilebilir. Ä°leride matview (idare_ozet_mv
>   deseni gibi, gece REFRESH) ile anlÄ±k yapÄ±labilir â€” istenirse.

> ## âš¡ 16 TEMMUZ (devam) â€” SAYFA-AÃ‡ILIÅI AGGREGATE'LERÄ°: Ã–ZET MV PAKETÄ° + analiz_pivot GERÃ‡EK FIX (âœ… CANLI)
> KullanÄ±cÄ± "yap ne gerekiyorsa yap, aÃ§Ä±k izin sorma" dedi â†’ tÃ¼m sayfalar tarandÄ±, aynÄ± hastalÄ±k toplu kapatÄ±ldÄ±.
> **backend/migration_ozet_mv_paketi.sql (âœ… canlÄ±da):** 6 canlÄ± aggregate minik MV'lere alÄ±ndÄ±, RPC'ler AYNI
> Ä°MZAYLA MV-okur (frontend deÄŸiÅŸikliÄŸi SIFIR): sonuc_ozet 4.0sâ†’343ms (tarayÄ±cÄ± Ã¶lÃ§Ã¼mÃ¼); kategori_sayim
> 2.1sâ†’212ms; il_sayim 1.7sâ†’~0.3s (ANASAYFA); il_firma_dagilimi / yuklenici_ozet 1.6sâ†’DB'de 2-3ms;
> il_sektor_ozet 238K-satÄ±r gruplamaâ†’3.1K'lÄ±k il_sektor_ozet_mv. Timeout gÃ¼nlerinde devreye giren felaket
> fallback'leri (sektorler 256K satÄ±r, index 13 istek) artÄ±k tetiklenmez (kod dursun â€” zararsÄ±z sigorta).
> Gece REFRESH zinciri run_scraper.sh'ta; **DERS: REFRESH CONCURRENTLY'ler AYRI `-c`'lerde olmalÄ±** (tek -c
> iÃ§inde ';' ile birleÅŸince psql Ã¶rtÃ¼k TEK transaction yapar â†’ CONCURRENTLY transaction iÃ§inde Ã‡ALIÅMAZ).
> Tek-satÄ±rlÄ±k MV'lerde sabit id=1 kolonu (CONCURRENTLY kolon-bazlÄ± UNIQUE index ister, expression sayÄ±lmaz).
> **backend/migration_analiz_pivot_firma_index.sql (âœ… canlÄ±da):** analiz_pivot(p_firma) 20s timeout'ta BÄ°LE
> Ã¶lÃ¼yordu (21.5s Ã¶lÃ§Ã¼ldÃ¼) â€” sorun normalize_firma'nÄ±n (plpgsql, ~15 regex) 537K satÄ±rda satÄ±r-baÅŸÄ± Ã§alÄ±ÅŸmasÄ±.
> Fix: normalize_firma IMMUTABLE â†’ `idx_sonuc_kazanan_firma_norm` ifade indeksi + predicate s-tarafÄ±na
> sadeleÅŸtirildi (eski `y.normalize_ad=X OR normalize_firma(s.kazanan_firma)=X` Ã§apraz-tablo OR'u index
> kullanamÄ±yordu; kanonik kimlik zaten normalize_firma). EXPLAIN: Index Scan âœ“. TarayÄ±cÄ±da REC idare-pivot +
> KALYON kategori-pivot birlikte 1.57sn (eski: tek biri 21.5sn'de 57014 â†’ firma-analiz kÄ±rÄ±lÄ±m kartÄ± bÃ¼yÃ¼k
> firmalarda sessizce kayboluyordu). NOT: eÅŸzamanlÄ± baÅŸka oturumun stage'i commit'e karÄ±ÅŸÄ±nca soft-reset ile
> ayÄ±klandÄ± â€” bu repoda commit Ã¶ncesi `git status` kontrolÃ¼ ÅŸart (paralel oturumlar aynÄ± working tree'de).

> ## ğŸ—ºï¸ 16 TEMMUZ (devam) â€” HARÄ°TA "BÄ°R Ä°LE TIKLAYIN" TAKILMASI: sektÃ¶r katmanÄ± MV'ye alÄ±ndÄ± (âœ… CANLI)
> **âœ… DEPLOY + DOÄRULAMA:** migration VDS'te Ã§alÄ±ÅŸtÄ± (MV build 1dk30sn, 238.341 satÄ±r, 3.157 ilÃ—kategori
> grubu). TarayÄ±cÄ±da soÄŸuk oturum: sektÃ¶r seÃ§imi 9.2snâ†’**1.0sn**, il tÄ±klamasÄ±â†’firma listesi **0.99sn**
> (eski: soÄŸukta 57014 timeoutâ†’takÄ±lma). curl Ä±sÄ±nmÄ±ÅŸ: ankara 0.5s, istanbul 0.44s, ozet ~1s. 6sn hata
> izlemede konsol temiz. Gece REFRESH run_scraper.sh'ta (idare MV'nin yanÄ±nda). Ä°steÄŸe baÄŸlÄ± gelecek adÄ±m:
> ozet iÃ§in 3.1K satÄ±rlÄ±k ikinci mini-MV (~1sâ†’~150ms; 6h client cache varken dÃ¼ÅŸÃ¼k Ã¶ncelik).
> KullanÄ±cÄ±: "hala veriler gelmiyor, bir ile tÄ±klayÄ±n da takÄ±lÄ± kalÄ±yor". **KÃ¶k neden (canlÄ±da Ã¶lÃ§Ã¼ldÃ¼):**
> harita sektÃ¶r katmanÄ± iki AÄIR canlÄ± aggregate'e dayanÄ±yordu (529Kâ‹ˆ355K): il_sektor_ozet sektÃ¶r seÃ§ince
> 9.2sn (sÄ±cakken!); il_sektor_firmalar il tÄ±klayÄ±nca sÄ±cak 1.8sn, SOÄUKTA 57014 statement timeout â†’
> panel "YÃ¼klenemedi"/takÄ±lÄ±. (Not: migration_harita_sektor.sql prod'da UYGULANMIÅ Ã§Ä±ktÄ± â€” YAPILACAKLAR'daki
> â³ bayat; fonksiyonlar vardÄ±, sorun yavaÅŸlÄ±k/timeout'tu.)
> **Ã‡Ã¶zÃ¼m (backend/migration_harita_firma_mv.sql â€” YENÄ°, idare_ozet_mv deseninin devamÄ±):**
> - `il_sektor_firma_mv`: ilÃ—kategoriÃ—normalize_firma kÄ±rÄ±lÄ±mÄ± Ã–NCEDEN hesaplÄ±; unique idx (il,kategori,
>   firma_norm) + eriÅŸim idx (il_fold,kategori); gece run_scraper.sh REFRESH CONCURRENTLY (idare MV yanÄ±na).
> - `il_sektor_ozet()` + `il_sektor_firmalar()` AYNI Ä°MZAYLA MV'den okur â†’ frontend deÄŸiÅŸikliÄŸi YOK.
> - Semantik dÃ¼zeltme (bilinÃ§li): ozet.firma_adet artÄ±k normalize_firma bazlÄ± (varyantlar birleÅŸir, firmalar
>   listesiyle tutarlÄ±); 'DiÄŸer' tÄ±klamasÄ± NULL kategorileri de kapsar (eskiden kaÃ§Ä±rÄ±yordu).
> - CREATE OR REPLACE proconfig'i sÄ±fÄ±rladÄ±ÄŸÄ±ndan ALTER SET statement_timeout'lar migration'da YENÄ°DEN konur.

> ## ğŸ›ï¸ 16 TEMMUZ (devam) â€” Ä°DARELER DÄ°ZÄ°NÄ° 60-100sn BEKLEME FIX (âœ… CANLI, DOÄRULANDI)
> KullanÄ±cÄ±: "idare verileri Ã§ekiliyor diye Ã§ok bekletiyor, bunu kaldÄ±rmamÄ±z lazÄ±m".
> **KÃ¶k neden (Ã¶lÃ§Ã¼ldÃ¼):** idareler.html, idare_sayim() RPC'sini db-max-rows=1000 yÃ¼zÃ¼nden ~16 kez ardÄ±ÅŸÄ±k
> Ã§aÄŸÄ±rÄ±yordu ve HER Ã§aÄŸrÄ±da 355K+ ilanlar Ã¼zerinde GROUP BY+MODE() BAÅTAN Ã§alÄ±ÅŸÄ±yordu â€” canlÄ±da sayfa baÅŸÄ±
> Ã¶lÃ§Ã¼m ~4.2sn â†’ toplam 60-70sn spinner. (Not: "client-load-all kapandÄ±" derken bu sayfa RPC'liydi ama
> RPC-sayfalama Ã— canlÄ±-aggregate kombinasyonu gÃ¶zden kaÃ§mÄ±ÅŸ.)
> **Ã‡Ã¶zÃ¼m (backend/migration_idareler_dizin_mv.sql â€” YENÄ°):**
> - `idare_ozet_mv` materialized view = aynÄ± aggregate Ã–NCEDEN hesaplanmÄ±ÅŸ; unique index (CONCURRENTLY ÅŸartÄ±).
> - `idare_dizin_json()` RPC: TÃœM dizin TEK istekte jsonb (json skaler â†’ 1000 satÄ±r sÄ±nÄ±rÄ± iÅŸlemez); satÄ±r
>   formatÄ± dizi `[idare, toplam, aktif, il]` (payload kÃ¼Ã§Ã¼k); statement_timeout 20s (rekabet_ozet dersi).
> - Eski `idare_sayim()` da MV'den okur oldu (cache'li eski HTML de hÄ±zlanÄ±r, canlÄ± GROUP BY tamamen kalktÄ±).
> - `run_scraper.sh` sonuna gece REFRESH MATERIALIZED VIEW CONCURRENTLY eklendi (veri zaten yalnÄ±z scraper
>   turunda deÄŸiÅŸiyor â†’ tazelik kaybÄ± yok).
> - idareler.html: while-dÃ¶ngÃ¼sÃ¼ + progress bar KALDIRILDI â†’ tek `sb.rpc('idare_dizin_json')`; sessionStorage
>   anahtarÄ± `idare_dizin_v1` (30dk TTL). Beklenen: ilk yÃ¼k <1sn, cache'li dÃ¶nÃ¼ÅŸ anÄ±nda.
> **âœ… DEPLOY EDÄ°LDÄ° (kullanÄ±cÄ± onayÄ±yla SSH):** VDS git pull + chmod +x run_scraper.sh (+x dersi) +
> migration Ã§alÄ±ÅŸtÄ±. **CanlÄ± doÄŸrulama:** MV 23.067 idare (16K deÄŸil! eski sayfa ~24 istek Ã— 4.2s â‰ˆ 100sn'ydi);
> json 2MB ham â†’ gzip 323KB; tarayÄ±cÄ±da RPC 1.0sn, sayfa toplam <1.5sn'de tam render (23.067 idare /
> 356.007 ihale kartlarÄ±, 50 satÄ±r tablo). Arama "belediye"â†’6.776, il dropdown 83 seÃ§enek, sessionStorage
> cache yazÄ±yor. Migration anÄ±nda 3 geÃ§ici PGRST 404 gÃ¶rÃ¼ldÃ¼ (ÅŸema cache reload gecikmesi) â€” kendiliÄŸinden
> geÃ§ti, kalÄ±cÄ± deÄŸil. NOT: ekran gÃ¶rÃ¼ntÃ¼sÃ¼ aracÄ± pane-seviyesinde timeout verdi, doÄŸrulama DOM Ã¼zerinden.

> ## ğŸ” 16 TEMMUZ (devam) â€” PLAN KAPILARI: PRO CTA GÄ°ZLE + e-SATINALMA KURUMSAL KAPI (CANLI)
> - **Topbar "Pro'ya GeÃ§" gizleme:** sidebar-user.js Ã¶deme yapmÄ±ÅŸ (Pro/Kurumsal) kullanÄ±cÄ±da topbar CTA'sÄ±nÄ±
>   GÄ°ZLER. Eski selektÃ¶r `.topbar-actions` Ã§oÄŸu sayfada eÅŸleÅŸmiyordu â†’ `.topbar` de eklendi; rozete Ã§evirmek
>   yerine display:none (kullanÄ±cÄ± "gÃ¶zÃ¼kmesin" dedi). **Cloudflare STALE JS servis ediyordu** (Cf-Cache HIT,
>   max-age=14400) â†’ 23 sayfada `sidebar-user.js?v=2` cache-bust ÅART oldu (yoksa fix gÃ¶rÃ¼nmezdi). CanlÄ±: yeni
>   JS servis ediliyor, selektÃ¶r topbar butonunu buluyor (anon'da gÃ¶rÃ¼nÃ¼r, proMu'da gizlenir).
> - **e-SatÄ±nalma Kurumsal kapÄ±sÄ±:** ozel-ihaleler form aÃ§Ä±lÄ±nca Kurumsal DEÄÄ°LSE "ğŸ”’ Ä°hale aÃ§mak Kurumsal plana
>   Ã¶zeldir" gate (form kilitli); ihaleYayinla'da kurumsal kontrolÃ¼ profil kontrolÃ¼nden Ã–NCE. Server-side zorlama
>   ZATEN vardÄ±: RLS `talep_kurumsal_ekler` INSERT = `kullanici_kurumsal_mi()` + VKN/Ã¼nvan/il/ilÃ§e/adres NOT NULL
>   (canlÄ± pg_policy ile doÄŸrulandÄ±) â€” yani "engelle" DB dÃ¼zeyinde gerÃ§ek, frontend anlaÅŸÄ±lÄ±r katman.

> ## ğŸ”— 16 TEMMUZ (devam) â€” KALKINMA AJANSI, RFQ LÄ°STESÄ°NE BÄ°RLEÅTÄ°RÄ°LDÄ° (CANLI)
> KullanÄ±cÄ±: "kalkÄ±nma ajansÄ± ihalelerini niye ayrÄ± sayfaya alÄ±yorsun, hepsini platform satÄ±nalma ihaleleri
> olarak aÃ§sana". YapÄ±ldÄ±: ozel-ihaleler.html'deki ayrÄ± "ğŸ›ï¸ KalkÄ±nma AjansÄ± Ä°haleleri" kartÄ± KALDIRILDI â†’
> platform RFQ'larÄ±yla (satinalma_talepleri) + KA (kamu_ihaleleri kaynak='ka') TEK "Platform SatÄ±nalma
> Ä°haleleri" listesinde CLIENT-SIDE birleÅŸti (taleplerYukle: iki tablo Promise.all â†’ normalize â†’ merge-sort,
> dÃ¼ÅŸÃ¼k hacim ~15 kayÄ±t). Kaynak rozeti (ğŸ¤ Platform RFQ mor / ğŸ›ï¸ KalkÄ±nma AjansÄ±Â·KOD yeÅŸil) + yeni "Kaynak"
> filtresi (rfq/ka). SektÃ¶r filtresi yalnÄ±z RFQ'yu sÃ¼zer (KA'da 41-kanonik taksonomi yok â†’ seÃ§iliyken KA
> hariÃ§). RFQâ†’ozel-ihale-detay, KAâ†’ka.gov.tr yeni sekme. SÃ¼re-doldu rozeti ikisinde de. CanlÄ± doÄŸrulandÄ±:
> tÃ¼mÃ¼ 15 (3 RFQ+12 KA), kaynak='ka'â†’12, kaynak='rfq'â†’3, sektÃ¶r seÃ§iliâ†’KA=0, konsol temiz.

> ## ğŸ¤ 16 TEMMUZ (devam) â€” e-SATINALMA (RFQ) BÃœYÃœK REVÄ°ZYON (CANLI)
> KullanÄ±cÄ±: form â•'ya tÄ±klayÄ±nca aÃ§Ä±lsÄ±n; Ã¼nvan/VKN/adres profilden otomatik+kilitli gelsin (yoksa Ã¶nce
> profil doldurtsun); sÃ¼resi geÃ§en ihale teklif almasÄ±n; aÃ§Ä±k ihalelere il/sektÃ¶r/tarih/durum/arama filtresi.
> - **profil:** vergi_no/acik_adres/firma_il/firma_ilce kolonlarÄ± (migration_profil_firma_kimlik.sql, canlÄ±da).
>   profil.html'de "ğŸ“ Ä°ÅŸ Yeri Adresi" bÃ¶lÃ¼mÃ¼ + VKN artÄ±k DB'de (eskiden yalnÄ±z localStorage). profil RLS
>   `auth.uid()=user_id` doÄŸrulandÄ± â†’ tedarikÃ§i baÅŸkasÄ±nÄ±n VKN/adresini profilden OKUYAMAZ.
> - **ozel-ihaleler.html:** form artÄ±k accordion (â• ile aÃ§Ä±lÄ±r, kapalÄ±yken yer kaplamaz). Firma Ã¼nvan/VKN/il/
>   ilÃ§e/adres profilden OTOMATÄ°K + readonly (kilitli, "Profilden dÃ¼zenle" linki). Profil eksikse form gizli +
>   "âš ï¸ Ã–nce firma profilinizi tamamlayÄ±n" gate (eksik alan listesi + Profili Tamamla). Son teklif tarihi zorunlu.
>   RFQ liste: durum sekmesi (ğŸŸ¢GÃ¼ncel/ğŸ•“GeÃ§miÅŸ/TÃ¼mÃ¼) + il + sektÃ¶r + tarih-aralÄ±ÄŸÄ± + arama (baÅŸlÄ±k/firma/aÃ§Ä±klama);
>   sÃ¼resi geÃ§en kart "â¹ SÃ¼resi doldu â€” teklif kapalÄ±" + soluk. CanlÄ± doÄŸrulandÄ± (accordion, filtreler, sekmeler).
> - **ozel-ihale-detay.html:** sureDoldu()/teklifAcik() â€” durum='acik' olsa bile son_teklif geÃ§miÅŸse teklif
>   formu kapanÄ±r ("â¹ son teklif tarihi geÃ§ti"), teklifVer() guard'lÄ±, header rozeti "SÃ¼resi doldu".
> - NOT: login-arkasÄ± akÄ±ÅŸ (profilâ†’otomatik kilitâ†’yayÄ±nla) anon test edilemedi ama kod+deploy doÄŸrulandÄ±.

> ## ğŸ¤– 16 TEMMUZ (2. oturum devam) â€” AI KATEGORÄ° BACKFILL: Gemini son-katman sÄ±nÄ±flandÄ±rÄ±cÄ± (KOD HAZIR + Ä°NCELENDÄ°, deploy bekliyor)
> KullanÄ±cÄ± onayÄ± ("tamam Ã¶yle yap") + maliyet endiÅŸesi ("dÃ¼zenli maliyet ne olur?"). TasarÄ±m maliyet-gÃ¼venli:
> **her satÄ±r Ã¶mrÃ¼nde YALNIZCA BÄ°R KEZ Gemini'ye gider**, sonucu `ilanlar.ai_kategori_denendi` damgalanÄ±r â†’ tekrar
> Ã§alÄ±ÅŸtÄ±rma aynÄ± satÄ±ra ikinci token HARCAMAZ (idempotent). AI serbest metin deÄŸil **1..41 NUMARA** dÃ¶ndÃ¼rÃ¼r â†’
> KANONIK_KATEGORILER dizinine eÅŸlenir (geÃ§ersiz/kararsÄ±z=0 â†’ 'DiÄŸer' kalÄ±r ama denendi iÅŸaretlenir).
> - `migration_ai_kategori.sql` (YENÄ°): `ai_kategori_denendi timestamptz` + kÄ±smi indeks (kategori='DiÄŸer' AND denendi IS NULL).
> - `ai_kategori_backfill.py` (YENÄ°): google.genai (embed_ortak deseni, eski SDK deprecated), response_mime_type=json+temp0+
>   thinking_budget=0, 50'li paket, retry+backoff, --limit/--batch/--rpm/--dry-run, token+maliyet raporu (thoughts dahil).
>   Batch-by-batch iÅŸleâ†’yazâ†’iÅŸaretle (crash-resumable).
> - `kategori_siniflandir.py`: `KANONIK_KATEGORILER` (41, tek-kaynak, assertion'lÄ±) + `JENERIK_KOVALAR`.
> - `kategori_backfill.py`: **KRÄ°TÄ°K GUARD** â€” spesifik kategoriyi 'DiÄŸer'e ASLA geri ezmez (yoksa her backfill
>   turu AI emeÄŸini geri alÄ±rdÄ±) + dmo/jandarma satÄ±rlarÄ±nÄ± atlar (map-temelli kategorileri otoriter).
> - `run_scraper.sh`: gece MV-refresh'ten Ã–NCE `ai_kategori_backfill.py --limit 400 --rpm 15` (free tier'a sÄ±ÄŸar,
>   harita/sektÃ¶r MV'leri yeni kategorileri aynÄ± gece yansÄ±tÄ±r).
> - **MALÄ°YET (kullanÄ±cÄ±ya):** tek-seferlik ~100K kuyruk â‰ˆ birkaÃ§ $ (BÄ°R KEZ, paid key Ã¶nerilir); gÃ¼nlÃ¼k cron
>   ~birkaÃ§ istek â‰ˆ ~$0 (free kotaya sÄ±ÄŸar). OKAS UYDURULMAZ â€” yalnÄ±z kategori seÃ§ilir, okas kolonu boÅŸ kalÄ±r.
> - **âœ… 18-ajanlÄ± adversarial inceleme TAMAMLANDI (4 boyut + her bulgu baÄŸÄ±msÄ±z doÄŸrulama): 14 bulgu â†’ 8 GERÃ‡EK,
>   HEPSÄ° DÃœZELTÄ°LDÄ°:**
>   1. **[Kritik]** JSON ayrÄ±ÅŸtÄ±rma hatasÄ±nda (gÃ¼venlik filtresi/kesik yanÄ±t) token harcanmÄ±ÅŸ olmasÄ±na raÄŸmen
>      paket iÅŸaretlenmeden `break` ediliyordu â†’ aynÄ± "zehirli" paket her gece yeniden seÃ§ilip yeniden
>      faturalanÄ±yor, kuyruÄŸun geri kalanÄ± hiÃ§ iÅŸlenmiyordu (kalÄ±cÄ± tÄ±kanma). Fix: yanÄ±t ALINDIYSA (parse
>      hatasÄ± olsa bile) `({}, usage)` dÃ¶n â†’ paket 'denendi' damgalanÄ±r, kuyruk ilerler. `(None,None)` artÄ±k
>      SADECE gerÃ§ek hard-fail (kota/anahtar, token harcanmadÄ±) iÃ§in ayrÄ±ldÄ±.
>   2. **[Orta]** `thinking_budget=0` eksikti â†’ gemini-2.5-flash varsayÄ±lan dÃ¼ÅŸÃ¼nmeyle koÅŸuyordu, maliyet raporu
>      `thoughts_token_count`'u saymadÄ±ÄŸÄ± iÃ§in gerÃ§ek harcamanÄ±n altÄ±nda gÃ¶steriyordu. Fix: thinking kapatÄ±ldÄ± +
>      `_usage_tok()` Ã§Ä±ktÄ± tokenine thoughts'u da ekliyor (belt-and-suspenders).
>   3. **[Orta]** AI kuyruk seÃ§imi kaynak filtresi uygulamÄ±yordu â†’ kategori_backfill'in DMO/Jandarma guard'Ä±yla
>      asimetrik (AI, DMO'nun bilerek haritalanmamÄ±ÅŸ karÄ±ÅŸÄ±k kovalarÄ±nÄ± [Ã¶r. "DiÄŸer Ä°hale Ä°lanlarÄ±"] tek
>      kanoniÄŸe zorlayabilirdi). Fix: `secim_cek`+`kuyruk_say` ortak `_KUYRUK_FILTRE`'ye `kaynak=not.in.(dmo,jandarma)` eklendi.
>   4. **[DÃ¼ÅŸÃ¼kÃ—3, aynÄ± kÃ¶k]** `kuyruk_say` ile `secim_cek` farklÄ± predicate kullanÄ±yordu (baÅŸlÄ±ksÄ±z 'DiÄŸer'
>      satÄ±rlar sayÄ±lÄ±yor ama asla seÃ§ilmiyordu) â†’ kuyruk hiÃ§ 0'a inmiyor, dry-run projeksiyonu ÅŸiÅŸiyordu.
>      Fix: ikisi de aynÄ± `_KUYRUK_FILTRE` sÃ¶zlÃ¼ÄŸÃ¼nÃ¼ paylaÅŸÄ±yor.
>   5. **[DÃ¼ÅŸÃ¼k]** Negatif `--batch` yakalanmamÄ±ÅŸ `HTTPStatusError` ile Ã§Ã¶kÃ¼yordu. Fix: `main()` baÅŸÄ±nda
>      `--limit`/`--batch` pozitiflik kontrolÃ¼.
>   6. **[DÃ¼ÅŸÃ¼k]** `KANONIK_KATEGORILER`'in js/kategoriler.js ile tam parite garantisi yoktu (yalnÄ±z DMO/CPV
>      alt-kÃ¼me assertion'Ä± vardÄ±, rename drift'i yakalanmazdÄ±). Fix: `assert len(...)==41` eklendi (ucuz kÄ±smi
>      Ã¶nlem; tam Ã§Ã¶zÃ¼m â€” 41 adÄ± tek paylaÅŸÄ±lan kaynaktan okutmak â€” gelecek iÅŸ).
>   **Kendi doÄŸrulamamda EK bulgu:** yerel test sÄ±rasÄ±nda (`.env` Ã¶lÃ¼ managed DB'ye iÅŸaret ettiÄŸi iÃ§in migration
>   henÃ¼z uygulanmamÄ±ÅŸ ortamda) `kuyruk_say` bir HTTP 400'Ã¼ sessizce "kuyruk=0" diye yorumluyor, ardÄ±ndan
>   `secim_cek` Ã§irkin ham traceback ile Ã§Ã¶kÃ¼yordu. Fix: `kuyruk_say` artÄ±k `status_code>=300`'de -1 dÃ¶ner,
>   `main()` bunu gÃ¶rÃ¼nce migration'Ä± iÅŸaret eden temiz bir mesajla `sys.exit(1)` yapar.
>   TÃ¼m dÃ¼zeltmeler yerelde sahte-yanÄ±t matrisiyle + argparse exit-kod testleriyle + gerÃ§ek 400 senaryosuyla
>   doÄŸrulandÄ± (VDS aÄŸÄ± olmadan, kod-seviyesinde). **HenÃ¼z VDS'e gitmedi â€” commit/push bekliyor.**
> - **DEPLOY (VDS, push sonrasÄ±):** `git pull` â†’ `docker exec ... < backend/migration_ai_kategori.sql` â†’
>   tek-seferlik `python ai_kategori_backfill.py --dry-run` (maliyet gÃ¶r) â†’ `--limit 100000` (paid key ile boÅŸalt).
>   AYRICA: kelime kurallarÄ± + DMO map gÃ¼ncellendiÄŸi iÃ§in `kategori_backfill.py`'yi de tekrar koÅŸ (idempotent, guard'lÄ±).

> ## ğŸ·ï¸ 16 TEMMUZ (2. oturum devam) â€” "DÄ°ÄER" TEÅHÄ°SÄ°: TÃœRKÃ‡E Ã‡EKÄ°M EKLERÄ° + DMO EÅLEME (kelime katmanÄ± yapÄ±ldÄ±, AI katmanÄ± Ã–NERÄ°)
> KullanÄ±cÄ± sorusu "kategorize etmek mi sorun?" Ã¼zerine 4K'lÄ±k DiÄŸer Ã¶rneklemi analiz edildi (scratchpad token frekansÄ±):
> **DiÄŸer'e dÃ¼ÅŸenlerin %100'Ã¼ OKAS'SIZ**; en bÃ¼yÃ¼k kÃ¼me taÅŸÄ±malÄ±-eÄŸitim/araÃ§-kiralama ihaleleri. KÃ–K NEDEN:
> \b tam-kelime regex TÃ¼rkÃ§e Ã‡EKÄ°M EKLERÄ°NÄ° kaÃ§Ä±rÄ±yor â€” "ogrenci tasima" â‰  "Ã¶ÄŸrencilerin taÅŸÄ±nmaSI",
> "arac kirala" â‰  "araÃ§ kiralaMA", "ilac" â‰  "Ä°laÃ§LAR", "parke tas" â‰  "Parke TaÅŸI". Yeni kelime eklerken her Ã§ekim AYRI yazÄ±lmalÄ±.
> - `kategori_siniflandir.py`: veri-tÃ¼revli varyantlar (tasinmasi/tasimali/tasima merkezi/arac gunu/hat arac,
>   arac-tasit kiralama, ogle yemegi, klorlama, buro malzemesi, ag anahtari/omurga ag, biyosidal, bugday,
>   parke tasi, lisans yenileme/alimi) + **DMO_KATEGORI_MAP** (DMO'nun kendi 12 kategori adÄ± â†’ kanonik;
>   dmo_scraper Ã¶nce map'e bakar). Ã–lÃ§Ã¼m: 4K DiÄŸer Ã¶rnekleminde **%16.1 kurtarma** (ekstrapolasyon ~131Kâ†’~21K azalÄ±r);
>   modÃ¼ldeki 9 Ã¶rnek regresyonsuz; DMO/JND dry-run'da Ä°laÃ§larâ†’SaÄŸlÄ±k, Nakil VasÄ±talarâ†’TaÅŸÄ±t, KLORLAMAâ†’Su âœ“.
> - **SONRAKÄ° KATMANLAR (Ã¶neri, onay bekliyor):** (1) kategori_belirle'ye `ilan_metni[:1200]` sinyali
>   (baÅŸlÄ±k jenerik olsa da metinde Ã¼rÃ¼nler yazar; backfill iÃ§in left(ilan_metni,N) dÃ¶nen kÃ¼Ã§Ã¼k RPC gerek);
>   (2) kalan kuyruÄŸa **Gemini toplu sÄ±nÄ±flandÄ±rma** â€” 50 baÅŸlÄ±k/istek JSON batch, gemini-2.5-flash,
>   ~100K satÄ±r â‰ˆ 2K istek (birkaÃ§ $; FREE tier kotaya takÄ±lÄ±r, paid key ÅŸart) â†’ ai_kategori_backfill.py
>   + cron'da gÃ¼nlÃ¼k mini tur (yeni DiÄŸer'ler). GerÃ§ekÃ§i hedef: DiÄŸer %19 â†’ kelime %16 â†’ metin ~%10-12 â†’ AI %3-5.
>   NOT: kategori backfill'i bu kelime gÃ¼ncellemeleri VDS'e GÄ°TTÄ°KTEN sonra (tekrar) koÅŸmak gerekir â€” idempotent.

> ## ğŸ“¦ 16 TEMMUZ (2. oturum devam) â€” KAMU KURUMU Ä°HALELERÄ° EKRANI KALDIRILDI â†’ DMO+JANDARMA ANA LÄ°STEDE
> KullanÄ±cÄ± kararÄ±: "ayrÄ± sayfaya ihtiyaÃ§ yok, Ä°haleler ekranÄ±na al." ilan_gov deseni birebir uygulandÄ±:
> - `dmo_scraper.py` + `jandarma_scraper.py` artÄ±k `kamu_ihaleleri` yerine **doÄŸrudan `ilanlar`'a** yazar:
>   ekap_id='DMO-<no>'/'JND-<psn>' (EKAP IKN'iyle Ã§akÄ±ÅŸamaz), kaynak='dmo'/'jandarma', upsert on_conflict=ekap_id,
>   kategori=kategori_belirle(...), pdf_url=kaynak detay URL'i, DMO ek alanlarÄ± ilan_metni'nde (arama_fold'a girer).
>   **Jandarma'da aÃ§Ä±klamasÄ± "EKAP ÃœZERÄ°NDEN ..DT.." diyen kayÄ±tlar ATLANIR** (mÃ¼kerrer kart Ã¶nlenir).
>   Dry-run yerelde doÄŸrulandÄ±: DMO 34, Jandarma 33 + 8 EKAP-mÃ¼kerrer atlandÄ±, kanonik kategoriler atanÄ±yor âœ“.
> - `ihaleler.html`: kaynakBadge'e ğŸ“¦ DMO + ğŸª– Jandarma; sabit "EKAP" sol etiketi kaynak-farkÄ±ndalÄ±klÄ± oldu
>   (ilan_gov kartlarÄ±nda da yanlÄ±ÅŸ EKAP yazÄ±yordu); **Kaynak filtresi** (f-kaynak: EKAP/Gazete/DMO/Jandarma,
>   ana+fallback sorgu, sÄ±fÄ±rla/kayÄ±tlÄ± arama/?kaynak= URL paramÄ±); jandarma kartÄ±nda PSN token KayÄ±t No gizli.
> - `ihale-detay.html`: ilan_gov'a Ã¶zel ternary'ler `DIS_KAYNAK` haritasÄ±yla genelleÅŸtirildi (eyebrow,
>   "kaynaÄŸÄ±nda aÃ§" butonu Ã—2, Kaynak info-row, belge sekmesi metni) â€” DMO/Jandarma detayÄ± kaynaÄŸÄ±na kÃ¶prÃ¼ler.
> - **25 sayfanÄ±n** sidebar'Ä±ndan "Kamu Kurumu Ä°haleleri" nav satÄ±rÄ± kaldÄ±rÄ±ldÄ±; `kamu-ihaleleri.html` â†’
>   `ihaleler?kaynak=dmo`'ya redirect stub'Ä± (eski yer imleri kÄ±rÄ±lmaz).
> - `kamu_ihaleleri` TABLOSU YAÅIYOR: KA (KalkÄ±nma AjansÄ±, kaynak='ka', 26 kayÄ±t) e-SatÄ±nalma rozetinde onu
>   kullanÄ±yor â€” dokunulmadÄ±. Eski dmo/jandarma satÄ±rlarÄ± tabloda bayat kalacak (zararsÄ±z; istenirse DELETE).
> - Deploy: commit+push â†’ VDS `git pull` â†’ cron (02:00 UTC, run_scraper.sh zaten ikisini Ã§aÄŸÄ±rÄ±yor) ilk turda
>   `ilanlar`'Ä± doldurur; istenirse pull sonrasÄ± elle `python dmo_scraper.py && python jandarma_scraper.py`.
> - Not: dÄ±ÅŸ kaynak satÄ±rlarÄ± bildirim RPC'lerine de girer (sektÃ¶r bildirimi artÄ±k DMO/Jandarma da kapsar).
>   Ä°YÄ°LEÅTÄ°RME ADAYI: jandarma birlik adÄ±ndan il Ã§Ä±karÄ±mÄ± (birÃ§oÄŸu il adÄ±yla baÅŸlÄ±yor) â€” harita/il analizine girer.

> ## ğŸ—ºï¸ 16 TEMMUZ (2. oturum) â€” HARÄ°TAYA SEKTÃ–R KATMANI: ilÃ—sektÃ¶r yoÄŸunluk + il/firma sÄ±ralamasÄ±
> KullanÄ±cÄ± isteÄŸi: "haritada sektÃ¶r sektÃ¶r ayÄ±rÄ±p illerdeki yoÄŸunluklarÄ± ve firmalarÄ± sÄ±ralamak".
> **âœ… KOD HAZIR (yerelde doÄŸrulandÄ±) / â³ MIGRATION VDS'TE Ã‡ALIÅTIRILACAK:**
> ```
> docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_harita_sektor.sql
> ```
> - `backend/migration_harita_sektor.sql` (YENÄ°): (1) `il_sektor_ozet()` â€” ihale_sonuclari(529K)â‹ˆilanlar(355K)
>   ilÃ—kategori firma/sÃ¶zleÅŸme/bedel; tam-tablo aggregate 3s PostgREST timeout KENARINDA olduÄŸundan
>   `ALTER FUNCTION SET statement_timeout='30s'` (rekabet_ozet dersi) + client tek Ã§aÄŸrÄ± & sessionStorage 6h.
>   (2) `il_sektor_firmalar(p_il_folds[],p_kategori,p_limit)` â€” il+sektÃ¶rde SEKTÃ–RE Ã–ZGÃœ sÃ¶zleÅŸme/bedelle firma
>   sÄ±ralamasÄ±; `yuklenici_id` BÄ°LÄ°NÃ‡LÄ° kullanÄ±lmadÄ± (~92K satÄ±rda NULL â†’ firmalarÄ± dÃ¼ÅŸÃ¼rÃ¼rdÃ¼), gruplama
>   `normalize_firma(kazanan_firma)`; il eÅŸleÅŸmesi `tr_fold` + yeni indeks `idx_ilanlar_il_fold_kategori`.
>   (3) `il_rfq_dagilimi(p_kategori DEFAULT NULL)` â€” eski sÄ±fÄ±r-arg sÃ¼rÃ¼m DROP (PostgREST overload belirsizliÄŸi).
> - `harita.html`: 41 kanonik kategori dropdown'Ä± (js/kategoriler.js), sektÃ¶rel choropleth (kova eÅŸikleri
>   sektÃ¶r daÄŸÄ±lÄ±mÄ±ndan quantile), sektÃ¶rel tooltip/lejant/istatistik, panel: sektÃ¶r seÃ§ince TR il sÄ±ralamasÄ±
>   (top 15, bar'lÄ±, tÄ±klaâ†’il), il seÃ§ince o il+sektÃ¶rÃ¼n firma sÄ±ralamasÄ± + kategorili RFQ listesi, `?sektor=`
>   deep-link. Migration uygulanmamÄ±ÅŸsa zarif dÃ¼ÅŸÃ¼ÅŸ: uyarÄ± + TÃ¼m SektÃ¶rler'e dÃ¶nÃ¼ÅŸ (test edildi âœ“).
> - **ğŸ› YOL ÃœSTÃœ BUG FIX (Ã¶nceden vardÄ±):** panel "Ã¶ne Ã§Ä±kan firmalar" `ilike('il','Ä°zmir')` Ä°/Ä± locale
>   tuzaÄŸÄ± â†’ Ä°/Ä±'lÄ± illerde (Ä°stanbul/Ä°zmir/DiyarbakÄ±râ€¦) HEP 0 kayÄ±t dÃ¶nÃ¼yordu (REST'le kanÄ±tlandÄ±: ilike.Ä°zmir=0,
>   eq.Ä°ZMÄ°R=3951). Fix: `.in('il', [ad.toLocaleUpperCase('tr'), ad, alias])`. SektÃ¶r RPC'leri zaten tr_fold'lu.
> - DoÄŸrulama: file:// Ã¶nizleme + canlÄ± VDS API â€” genel mod regresyonsuz (71.384 firma/81 il), sektÃ¶r UI
>   sahte Ã¶nbellek tohumuyla uÃ§tan uca (sÄ±ralama/KPI/pay/geri dÃ¶nÃ¼ÅŸ âœ“), Ä°zmir firma listesi fix sonrasÄ± dolu âœ“.
>   GerÃ§ek sektÃ¶r verisi migration sonrasÄ± akacak; `il_sektor_ozet` sÃ¼resi ilk Ã§aÄŸrÄ±da Ä°ZLENMELÄ° (30s tavan).
> - **ğŸ”´ BULGU (kullanÄ±cÄ± "OKAS'a gÃ¶re mi?" sorusu Ã¼zerine, canlÄ±da Ã¶lÃ§Ã¼ldÃ¼): `ilanlar.kategori`'nin ~%64'Ã¼
>   HÃ‚LÃ‚ ESKÄ° taksonomide** â€” Mal AlÄ±mÄ± %24.3 (86.4K) + DiÄŸer %19.1 (68.2K) + Hizmet AlÄ±mÄ± %14.2 (50.7K) +
>   Ä°nÅŸaat & YapÄ±m %6.1 (21.7K); toplam 46 farklÄ± etiket var (41 kanonik deÄŸil). 'Mal AlÄ±mÄ±'lÄ± en yeni ilan
>   25 Haz 2026 â†’ yeni akÄ±ÅŸ o gÃ¼nden beri kanonik Ã¼retiyor ama `kategori_backfill.py` ana ilanlar tablosunda
>   HÄ°Ã‡/YARIM koÅŸmuÅŸ (DT backfill'i tamamdÄ±, ilanlar deÄŸil!). Etki: sektÃ¶r haritasÄ± + sektorler/rekabet
>   filtreleri eski etiketli kÃ¼tleyi GÃ–REMEZ. **Aksiyon (VDS'te, kullanÄ±cÄ±):**
>   SSH sonrasÄ± `cd /opt/ihale-platform/backend && source venv/bin/activate && python kategori_backfill.py --dry-run`
>   â†’ sayÄ±lar makulse `--dry-run`sÄ±z tekrar (356K satÄ±r â€” uzun sÃ¼rer, nohup+log ile).
>   **Dry-run yapÄ±ldÄ± (16 Tem, kullanÄ±cÄ±):** 356.008 okundu, 163.587 deÄŸiÅŸecek (41 hedef kategori) â€”
>   96.6K gerÃ§ek sektÃ¶re, 67K OKAS'sÄ±z/kelimesiz â†’ DiÄŸer (eski Mal/Hizmet AlÄ±mÄ± jeneriÄŸinden, kayÄ±p yok).
>   DaÄŸÄ±lÄ±m makul bulundu, gerÃ§ek koÅŸum baÅŸlatÄ±lÄ±yor. SonrasÄ±: kategori_sayim ile doÄŸrula; gece
>   yuklenici_yenile firma kategori dizilerini hizalar. GELECEK Ä°Å: 67K'lÄ±k DiÄŸer iÃ§in ek kelime/AI turu.
>   (script REST+service_key ile Ã§alÄ±ÅŸÄ±r, yerel .env Ã–LÃœ managed'Ä± gÃ¶sterir â€” yerelden Ã‡ALIÅTIRMA.)

> ## ğŸ“Š 16 TEMMUZ â€” TRADE MAP (trademap.org) FÄ°ZÄ°BÄ°LÄ°TE: TEKNÄ°K EVET / HUKUKEN HAYIR (danÄ±ÅŸmanlÄ±k, KARAR KULLANICIDA)
> Soru: ITC Trade Map'ten TÃ¼rkiye dÄ±ÅŸ ticaret verisi Ã§ekip Ä°haleGlobal'e eklemek.
> **Teknik bulgu:** yeni trademap.org (beta) login'siz aÃ§Ä±k, temiz JSON API'si var
> (`/api/services/timeSeries/yearly/byCountry?...`, UN Ã¼lke kodlarÄ± â€” TR=792) â†’ Ã§ekmesi trivial.
> **Hukuki bulgu (ITC MAT Terms, canlÄ±da okundu):** tam olarak bu kullanÄ±m AÃ‡IKÃ‡A YASAK â€”
> (1) bot/script/scraping ile toplu veri Ã§ekme yasak, (2) MAT iÃ§eriÄŸini standalone/bulk dataset olarak
> yeniden daÄŸÄ±tma yasak, (3) MAT iÃ§eriÄŸiyle "baÅŸka bir database/platform/dashboard'u besleme (ticari servis)"
> yasak. Bot-detection/rate-limit/ban uyguluyorlar; beta bitince paralÄ± (MAT Pro). ResmÃ® yol: "MAT data
> products"/"embedded versions" â€” ayrÄ± sÃ¶zleÅŸme+Ã¼cret. Kamu-hassas projede ihaleciler-tarzÄ± yasak-kaynak
> baÄŸÄ±mlÄ±lÄ±ÄŸÄ± kurulmaz (bkz. render-still-live dersi).
> **AynÄ± verinin SERBEST kaynaklarÄ±:** TÃœÄ°K dÄ±ÅŸ ticaret (aÃ§Ä±k veri, aylÄ±k, Ã¼lkeÃ—HS), UN Comtrade API
> (Ã¼cretsiz key, atÄ±fla kullanÄ±m), WTO Stats API + UNCTADstat (hizmet ticareti â€” Trade Map servis verisi
> zaten UNCTAD/WTO tahmini). Trade Map bu kaynaklardan DERLÄ°YOR; ham kaynaÄŸa gitmek hem yasal hem bedava.
> **ÃœrÃ¼n Ã¶nerisi (yapÄ±lÄ±rsa):** dar MVP â€” uluslararasÄ± ihaleler dÃ¼nya haritasÄ±na Ã¼lke baÅŸÄ±na tek metrik
> ("TR'nin bu Ã¼lkeye ihracatÄ± $X, trend") katmanÄ±, TÃœÄ°K/Comtrade'den yÄ±llÄ±k gÃ¼ncelleme. Tam istatistik
> modÃ¼lÃ¼ core value-prop deÄŸil (payment atomiklik + launch iÅŸleri Ã¶nde).
>
> **âœ… YAPILDI (aynÄ± gÃ¼n, kullanÄ±cÄ± onayladÄ± â€” canlÄ±da doÄŸrulanacak):** "ğŸ‡¹ğŸ‡· TÃ¼rkiye ile Ticaret" katmanÄ±:
> - `backend/ticaret_verisi_cek.py` â†’ `js/ticaret-tr-veri.js` (134KB statik, DB YOK, cron YOK â€” yÄ±lda 1-2 kez elle):
>   UN Comtrade public preview (anahtarsÄ±z; toplam ihracat/ithalat 2025+2024, motCode=0/partner2=0/C00 temiz satÄ±r)
>   + WITS SDMX (anahtarsÄ±z; 16 HS-aralÄ±ÄŸÄ± sektÃ¶r grubu Ã— Ã¼lke, 2023+2022, ISO-A3). Harita kod allowlist'i
>   dunya-harita.js'ten regex'le â†’ 170 Ã¼lke. DeÄŸerler doÄŸrulandÄ± (TR 2025 ihr $273.4Mr, DEU $22.2Mr âœ“).
> - uluslararasi.html: harita baÅŸlÄ±ÄŸÄ±na mod dÃ¼ÄŸmeleri [Ä°haleler | ğŸ‡¹ğŸ‡· TÃ¼rkiye ile Ticaret] + sektÃ¶r dropdown
>   (ticaret modunda). Ticaret modunda: ihracat hacmine gÃ¶re 5-kova renk (sektÃ¶rde ~10x kÃ¼Ã§Ã¼k eÅŸik),
>   hover tooltip = TÃ¼rkÃ§e Ã¼lke adÄ± (Intl.DisplayNames, fallback Ä°ng.) + ihracat/ithalat + YoY â–²â–¼ + seÃ§ili
>   sektÃ¶r satÄ±rÄ± + "N aÃ§Ä±k ihale â€” tÄ±kla" kÃ¶prÃ¼sÃ¼. Lejantta yÄ±l + kaynak atfÄ± (UN Comtrade & WITS â€” atÄ±f
>   zorunlu). TIC yÃ¼klenmezse dÃ¼ÄŸme gizlenir, ihale modu hiÃ§ etkilenmez. Yerel testte tÃ¼m akÄ±ÅŸ doÄŸrulandÄ±.
>
> **âœ… EK (kullanÄ±cÄ± geri bildirimi, canlÄ±da doÄŸrulandÄ±):**
> - **TÃ¼rkiye artÄ±k beyaz "referans Ã¼lke":** TUR veri dosyasÄ±nda partner olmadÄ±ÄŸÄ± iÃ§in "veri yok" koyusuyla
>   (siyah gibi) boyanÄ±yordu â†’ milli deÄŸerlere aykÄ±rÄ± bulundu. ArtÄ±k her modda beyaz (#eef2f8) + amber
>   kenarlÄ±klÄ± `anavatan`; hover'da "ğŸ‡¹ğŸ‡· TÃ¼rkiye â€” referans Ã¼lke Â· DÃ¼nyaya toplam ihr/ith" (TIC.dunya).
> - **Tooltip yÃ¶n netliÄŸi:** "Ä°hracat/Ä°thalat" belirsizdi (kim kime?) â†’ artÄ±k "TÃ¼rkiye â†’ X (ihracatÄ±mÄ±z)" ve
>   "X â†’ TÃ¼rkiye (ithalatÄ±mÄ±z)"; sektÃ¶r satÄ±rÄ± da TRâ†’X / Xâ†’TR ayrÄ±mlÄ±. Kaynak reporter=TÃ¼rkiye (Comtrade).
> - **â³ SektÃ¶r granÃ¼laritesi (BEKLÄ°YOR):** ÅŸu an 16 WITS grubu (2023). TradeMap-paritesi iÃ§in Comtrade
>   HS 2-digit (AG2, ~97 fasÄ±l â†’ 21 HS bÃ¶lÃ¼mÃ¼ne toplulaÅŸtÄ±r, 2024/2025 taze) planÄ±. ticaret_verisi_cek.py
>   geniÅŸletilecek. Ä°ZÄ°N EKLENDÄ° (`Bash(python *)` settings.local.json'a, kullanÄ±cÄ±) â†’ Ã§alÄ±ÅŸtÄ±rÄ±labilir.
>
> **âœ… EK (kullanÄ±cÄ± geri bildirimi, canlÄ±da doÄŸrulandÄ±) â€” Ä°HALE/TÄ°CARET AYRIMI + YENÄ° SAYFA:**
> - **`ticaret-analiz.html` YENÄ° sayfa** ("Ticaret Analizi", UluslararasÄ± nav'Ä±nda): TÃ¼rkiye ile ticaret
>   HARÄ°TASI (uluslararasi'den taÅŸÄ±ndÄ±) + sÄ±ralanabilir/aranabilir 170-Ã¼lke LÄ°STESÄ° (ihracat/ithalat/YoY,
>   sektÃ¶r-filtreli, baÅŸlÄ±k-tÄ±k sÄ±ralama) + KPI (dÃ¼nya toplamlarÄ±, dÄ±ÅŸ ticaret dengesi) + KAYNAKLAR kartÄ±
>   (UN Comtrade + WITS + yÃ¶ntem + atÄ±f + TÃœÄ°K notu â€” kullanÄ±cÄ±nÄ±n "kaynak nedir?" sorusu dokÃ¼mante edildi).
>   Haritaâ†”liste Ã§ift yÃ¶n (hoverâ†’vurgu, tÄ±kâ†’kaydÄ±r). TÃ¼rkiye beyaz referans, tooltip yÃ¶n-net.
> - **`uluslararasi.html` sadeleÅŸti:** ihale/ticaret ayrÄ±mÄ± â€” mod toggle KALDIRILDI (harita ihale-only),
>   yerine ticaret-analiz linki; ticaret-tr-veri.js kaldÄ±rÄ±ldÄ±; TÃ¼rkiye yine beyaz.
> - **SektÃ¶r dropdown beyaz-kutu fix:** Windows native `<select>` popup'Ä± option arka planÄ±nÄ± koyu yapmaz â†’
>   beyaz-Ã¼stÃ¼ne-beyaz gÃ¶rÃ¼nmezdi; `#dunya-sektor option { background:#fff; color:#1b2942 }`.
> - **âœ… Nav sweep TAMAM (canlÄ±):** backend/scratchpad nav_sweep.py ile 24 sayfaya "ğŸ“ˆ Ticaret Analizi" nav item'Ä±
>   eklendi (toplam 26 sayfa; UluslararasÄ± Ä°haleler'den sonra). Landing/legal 7 sayfa (nav'sÄ±z) atlandÄ±.
> - **âœ… SektÃ¶r upgrade TAMAM (canlÄ±):** backend/ticaret_sektor_yenile.py Ã§alÄ±ÅŸtÄ± â†’ js/ticaret-tr-veri.js artÄ±k
>   **21 standart HS bÃ¶lÃ¼mÃ¼, 2024 taze** (16 WITS grubu/2023 yerine). Ham Deri/YaÄŸ/AÄŸaÃ§/KaÄŸÄ±t/Optik-TÄ±bbi/
>   KÄ±ymetli TaÅŸ/Silah/Sanat ayrÄ±. CanlÄ± doÄŸrulandÄ± (22 seÃ§enek, sektor_yil 2024). Cache: ticaret-tr-veri.js?v=2.
> - **â³ HS6 KALEM-KALEM MODÃœLÃœ (kullanÄ±cÄ±: "6 haneye inelim, deri vs yaÄŸ ayrÄ±mÄ±"):** Comtrade keyless HS6 =
>   Ã¼lke-baÅŸÄ± AG6 top-500 (kÃ¼Ã§Ã¼k partner tam, bÃ¼yÃ¼k partner en bÃ¼yÃ¼k ~500 kalem; deÄŸerin %95+'i). Statik dosyaya
>   sÄ±ÄŸmaz (~200K satÄ±r) â†’ **DB tablosu `dis_ticaret_hs`** (backend/migration_dis_ticaret_hs.sql â€” UYGULANDI,
>   public read + service_role write) + **ingestion `backend/ticaret_hs_cek.py`** (VDS'te nohup Ã‡ALIÅIYOR,
>   ~28dk, 176 Ã¼lke Ã— AG6 X+M â†’ upsert; pipeline 3-Ã¼lke testinde doÄŸrulandÄ±, 8022 satÄ±r). Flush eÅŸiÄŸi 400.
>   **KALAN:** ingestion bitince â†’ ticaret-analiz'e **Ã¼lkeye tÄ±kla â†’ HS6 drill-down** UI (fasÄ±lâ†’baÅŸlÄ±kâ†’6-hane,
>   aranabilir; PostgREST .eq(ulke).order(deger desc)). Faz 2: ihale Ã¼rÃ¼nÃ¼ (CPV/OKASâ†’HS) â†” TR ihracat gÃ¼cÃ¼ eÅŸleÅŸmesi.
>   NOT: tam kuyruk (top-500 Ã¶tesi bÃ¼yÃ¼k partnerlerde) + YoY iÃ§in Ã¼cretsiz Comtrade API KEY (kullanÄ±cÄ± kaydÄ±).
>
> ## ğŸ¢ 16 TEMMUZ â€” EKAP FÄ°RMA VERÄ°SÄ° KAPSAMLI KAZIMA (kullanÄ±cÄ±: "firmalara dair her veriyi Ã§ek, hepsini kazÄ±yalÄ±m")
> **Durum denetimi (bu oturum):** yakalanan firma verisi KAZANAN-merkezli/tek boyutlu. EKSÄ°K ve EKAP'Ä±n
> firma adÄ±na ÃœRETTÄ°ÄÄ° ama bizde OLMAYAN: (1) teklif veren TÃœM istekliler = kaybeden roster (en bÃ¼yÃ¼k boÅŸluk;
> ÅŸu an sadece SAYISI biliniyor, kimlik yok), (2) VKN (%0), (3) ortak giriÅŸim Ã¼ye firmalarÄ± (sadece boolean),
> (4) fesih/tasfiye/sÃ¶zleÅŸme devri (ham tum_teklifler'de var, kolona Ã§Ä±kmÄ±yor; ~%0.6-0.8 â†’ ~7.5K olay),
> (5) yasaklÄ±lar listesi (hiÃ§ Ã§ekilmiyor). Kaynak: workflow tasarÄ±mÄ± (9 ajan) + payload analizi tamamlandÄ±.
> **Roster hipotezi:** GetByIhaleIdIhaleDetay yanÄ±tÄ±ndaki SONUÃ‡ Ä°LANI veriHtml'inde muhtemelen tÃ¼m istekli+teklif
> tablosu var; ÅŸu an sadece SAYI regex'leniyor, isimler atÄ±lÄ±yor. KesinleÅŸtirmek iÃ§in probe (backend/ekap_firma_probe.py) yazÄ±ldÄ±.
> **â›” CANLI PROBE BLOKLU â€” EKAP BAKIMDA (16 Tem):** ekapv2/ekap.kik.gov.tr + ihale.gov.tr planlÄ± bakÄ±mda â†’
> `/b_ihalearama/...` her durum kodunda + tÃ¼m proxy'lerde 404 (VDS'ten de). GEÃ‡Ä°CÄ°; API taÅŸÄ±nmadÄ±, scraper saÄŸlam.
> BakÄ±m bitince: (a) probe Ã§alÄ±ÅŸtÄ±r â†’ roster yerini doÄŸrula, (b) tam firma kazÄ±masÄ±.
> **EKAP'sÄ±z YAPILABÄ°LECEK (bakÄ±mdan baÄŸÄ±msÄ±z):** ÅŸema migration'Ä± (yeni tablolar: ihale_teklifleri/roster,
> firma_yasaklilar, firma_olaylari; yeni kolonlar) + yeniden-kazÄ±ma GEREKTÄ°RMEYEN backfill (fesih/tasfiye/devir/kÄ±sÄ±m
> mevcut 537K tum_teklifler'den saf SQL ile â†’ kolonlar).
> **NOT (scraper saÄŸlÄ±ÄŸÄ±):** EKAP bakÄ±mÄ± bu geceki 02:00 cron'una denk gelirse tur sessizce 0 yazabilir â€” bakÄ±m
> uzarsa tazelik iÃ§in elle tekrar gerekebilir (bkz. scraper-cron-silent-fail).
>
> **âœ… EK (kullanÄ±cÄ± isteÄŸi): haritalara yakÄ±nlaÅŸtÄ±rma/kaydÄ±rma** â€” "Ã¼lkeler Ã§ok kÃ¼Ã§Ã¼k gÃ¶rÃ¼nÃ¼yor":
> - `js/svg-zoom.js` (yeniden kullanÄ±labilir modÃ¼l): tekerlek=imleÃ§-noktalÄ± zoom, sÃ¼rÃ¼kle=pan (yalnÄ±zca
>   zoom'dayken), iki-parmak pinch, +/âˆ’/âŸ² butonlarÄ± (wrapper saÄŸ Ã¼st). SÃ¼rÃ¼kleme sonrasÄ± tÄ±klama
>   capture-phase'de YUTULUR â†’ Ã¼lke/il tÄ±kla-filtrele yanlÄ±ÅŸlÄ±kla tetiklenmez. Ã‡ift-tÄ±k zoom BÄ°LEREK yok
>   (tek-tÄ±k filtreyle Ã§akÄ±ÅŸÄ±yor). viewBox mutasyonu; tooltip'ler clientX/Y'li olduÄŸundan etkilenmez.
> - BaÄŸlanan haritalar: uluslararasi dÃ¼nya (maxZoom 12 â€” BenelÃ¼ks/KÃ¶rfez seÃ§ilebilir oldu), harita.html
>   TR ili (maxZoom 6; boya() fill/g-pins'e dokunduÄŸu iÃ§in butonlar kalÄ±cÄ±). Leaflet TR haritalarÄ±
>   (dashboard js/harita.js + index inline) zaten +/âˆ’ butonluydu â†’ scrollWheelZoom da aÃ§Ä±ldÄ±.
> - Yerel doÄŸrulama: zoom/pan/pinch viewBox matematiÄŸi, tÄ±klama-yutma (filtre deÄŸiÅŸmedi), âŸ² reset,
>   zoom'dayken tooltip â€” hepsi test edildi, konsol temiz.

> ## ğŸ›ï¸ 16 TEMMUZ (devam) â€” KALKINMA AJANSI Ä°HALELERÄ° (ka.gov.tr) â†’ e-SATINALMA'DA (CANLI)
> KullanÄ±cÄ±: "kalkÄ±nma ajansÄ± rozetiyle Ã¶zel e-satÄ±nalmada gÃ¶stersek" â€” doÄŸru karar: KA ihaleleri kamu
> alÄ±cÄ±sÄ± DEÄÄ°L, ajans hibesi kullanan Ã–ZEL firmalarÄ±n denetimli ihaleleri â†’ e-SatÄ±nalma'ya oturuyor.
> - `backend/ka_scraper.py`: **ka.gov.tr/api/tenders** (Nuxt SPA'nÄ±n temiz JSON API'si, sayfalÄ±, CAPTCHA/auth
>   yok â€” Ã¼Ã§ kaynaÄŸÄ±n en kolayÄ±). 97 kayÄ±t (iptal hariÃ§). DÄ°KKAT: API aynÄ± id'yi birden Ã§ok sayfada dÃ¶ndÃ¼rÃ¼yor
>   â†’ dict-dedup ÅŸart (yoksa PostgREST 21000 "cannot affect row a second time").
> - Migration: kamu_ihaleleri'ne `il` + `alt_kaynak` (ajans kodu: baka/istka/fka... ) kolonlarÄ±.
> - `ozel-ihaleler.html`: "ğŸ›ï¸ KalkÄ±nma AjansÄ± Ä°haleleri" kartÄ± â€” yalnÄ±z yayÄ±nda olanlar (son_teklif>=now,
>   canlÄ±da 12), rozet "ğŸ›ï¸ KalkÄ±nma AjansÄ± Â· KOD" (title=ajans tam adÄ±), tÄ±klaâ†’ka.gov.tr redirect.
> - `kamu-ihaleleri.html`: kaynak='ka' HARÄ°Ã‡ tutuldu (sorgular in.(dmo,jandarma)) â€” kamu sayfasÄ± 74'te kaldÄ±,
>   sÄ±zÄ±ntÄ± yok (canlÄ± doÄŸrulandÄ±). Cron'a ka_scraper eklendi.

> ## ğŸ“¦ 16 TEMMUZ (devam) â€” KAMU KURUMU Ä°HALELERÄ°: DMO + JANDARMA KAYNAKLARI EKLENDÄ° (CANLI)
> KullanÄ±cÄ±: EKAP dÄ±ÅŸÄ± iki kamu kaynaÄŸÄ±nÄ± (DMO + Jandarma) "Kamu adÄ± altÄ±nda" ekleyelim. Fizibilite canlÄ±
> doÄŸrulandÄ± â†’ ikisi de dÃ¼z HTTP GET + HTML parse (CAPTCHA/auth/JS YOK, DT kazanan CAPTCHA'sÄ±ndan Ã§ok kolay).
> - **AyrÄ± tablo `kamu_ihaleleri`** (uluslararasi_ihaleler deseni; ana ilanlar kirlenmesin): kaynak(dmo/jandarma),
>   kaynak_id, baslik, idare, kategori, aciklama, talep_no, ekap_referans, tarihler, orijinal_url. UNIQUE(kaynak,kaynak_id).
>   RLS public read. `backend/migration_kamu_ihaleleri.sql` (canlÄ±ya uygulandÄ±).
> - **DMO** (`dmo_scraper.py`): `dmo.gov.tr/Ihale/Liste?type=1` sunucu-render HTML tablo â†’ 34 aktif ihale. UTF-8.
> - **Jandarma** (`jandarma_scraper.py`): `vatandas.jandarma.gov.tr/ihalesorgu/FORM/FrmIhaleListe.aspx` WebForms,
>   birlik-gruplu â†’ 40 ihale. UTF-8 (charset header; Ä°LK tahminim windows-1254 yanlÄ±ÅŸtÄ± â†’ mojibake, r.text ile dÃ¼zeldi).
>   AÃ§Ä±klamalardan EKAP DT no Ã§Ä±karÄ±lÄ±yor (8 kayÄ±t) â€” dedup/izleme iÃ§in.
> - **Sayfa `kamu-ihaleleri.html`** (uluslararasi kalÄ±bÄ±): kaynak rozetli liste (ğŸ“˜ DMO / ğŸ–ï¸ Jandarma) + mor EKAP
>   rozeti + kaynak/arama filtresi + sunucu-sayfalÄ±. Nav "Kamu Ä°haleleri" bÃ¶lÃ¼mÃ¼ne "ğŸ“¦ Kamu Kurumu Ä°haleleri"
>   (24 sayfa). CanlÄ± doÄŸrulandÄ±: 74 kayÄ±t (34+40, 8 EKAP), kaynak filtresi Ã§alÄ±ÅŸÄ±yor.
> - **Cron:** `run_scraper.sh`'e iki scraper eklendi (gece 02:00 turu).
> - **Bilinen kÃ¼Ã§Ã¼k eksik:** arama TÃ¼rkÃ§e Ä°/Ä± katlamÄ±yor (ILIKE `kÄ±rtasiye`â‰ `KIRTASÄ°YE`) â€” doÄŸrudan-temin ile aynÄ±;
>   74 satÄ±rlÄ±k tabloda ileride arama_fold generated kolonuyla giderilebilir.
> **Karar notu:** kullanÄ±cÄ±nÄ±n Ã¶nerdiÄŸi "Ä°stihbarat" baÅŸlÄ±ÄŸÄ± yerine dÃ¼rÃ¼st kaynak rozeti + "Kamu Kurumu" baÅŸlÄ±ÄŸÄ±
> seÃ§ildi (istihbarat yanÄ±ltÄ±cÄ±ydÄ±; bunlar kamu satÄ±nalma kanallarÄ±).

> ## ğŸ› ï¸ 16 TEMMUZ (devam) â€” 8 SÄ°STEM SORUNU: 7 DÃœZELTÄ°LDÄ° + CANLI, #4 SIRADA
> KullanÄ±cÄ± 8 sorun bildirdi; 8 paralel ajanla teÅŸhis edildi (workflow), sonra dÃ¼zeltildi:
> - **#7 teklif hazÄ±rla DONMASI (commit `4fd02af`) â€” EN KRÄ°TÄ°K:** `yazdir()` print ÅŸablonundaki template
>   literal iÃ§inde gÃ¶mÃ¼lÃ¼ `<script src="js/main.js"></script>` vardÄ± â†’ HTML ayrÄ±ÅŸtÄ±rÄ±cÄ± bu `</script>`'i
>   gÃ¶rÃ¼nce ANA script bloÄŸunu satÄ±r 1787'de ERKEN KAPATIYORDU â†’ tÃ¼m sayfa JS'i parse hatasÄ± â†’ hiÃ§bir ÅŸey
>   Ã§alÄ±ÅŸmÄ±yordu (donuk skeleton). SatÄ±r kaldÄ±rÄ±ldÄ± â†’ canlÄ±da ihale Ã¶zeti anÄ±nda yÃ¼kleniyor. **Ders: inline
>   `<script>` iÃ§indeki string/template'lerde `</script>` MUTLAKA `<\/script>` diye escape edilmeli.**
>   (TeÅŸhis ajanÄ± "select(*) aÄŸÄ±r kolon" demiÅŸti â€” o da dar-kolona Ã§evrildi ama asÄ±l neden buydu; ajan
>   sadece okuyup Ã§alÄ±ÅŸtÄ±rmadÄ±ÄŸÄ± iÃ§in gerÃ§ek nedeni kaÃ§Ä±rmÄ±ÅŸtÄ± â€” canlÄ± doÄŸrulama ÅŸart.)
> - **#2 geÃ§miÅŸ kazanan (commit `4e4db15`):** kurum-analiz ihale listesine `ihale_sonuclari` embed'i
>   (ilan_id FK, %100 dolu) â†’ ğŸ† kazanan firma+bedel+tenzilat+tarih; Ã§ok-kÄ±sÄ±mlÄ±da "N kÄ±sÄ±m Â· toplam â‚ºX".
> - **#6 ihale no kopyalama:** ihaleler kartÄ±nda hover â§‰ + tek-tÄ±k kopya (uluslararasi noKopyala deseni).
> - **#8 DT idare tÄ±klama:** link gÃ¶rÃ¼nÃ¼r (hover amber), hedef `dogrudan-temin?idare=` (kurum-analiz uzun DT
>   idare adÄ±nda boÅŸ/timeout dÃ¶nÃ¼yordu â†’ garanti Ã§alÄ±ÅŸan DT-iÃ§i filtreye Ã§evrildi).
> - **#3 idareler Ã¶nbelleÄŸi:** idare_sayim sessionStorage (30dk TTL) â†’ tekrar aÃ§Ä±lÄ±ÅŸta ~15 RPC yok.
> - **#1 kurumlar her tuÅŸta fetch:** ZATEN debounce+client-side, kod deÄŸiÅŸikliÄŸi gerekmedi.
> - **#5 rekabet idare tÄ±klama (commit `4e4db15` + `a8bdbee`):** idare satÄ±rlarÄ± kurum-analiz linkine
>   dÃ¶nÃ¼ÅŸtÃ¼. DoÄŸrularken KEÅÄ°F: `rekabet_ozet` RPC'si ~351K ilanlar'da ~20 alt-agregasyon = ~3s, PostgREST
>   ~3s timeout eÅŸiÄŸinde â†’ sayfa ARALIKLI hiÃ§ yÃ¼klenmiyordu. Fix: `ALTER FUNCTION rekabet_ozet SET
>   statement_timeout='20s'` (kullanÄ±cÄ± onayÄ±yla VDS'e uygulandÄ±, 3/3 baÅŸarÄ±lÄ±). Sayfa Pro-kilitli olduÄŸu
>   iÃ§in anonimde gÃ¶rsel doÄŸrulanamadÄ±; link kodu Ã§alÄ±ÅŸan desenin aynÄ±sÄ±.
> - **#4 firma analizi AIâ†’2-firma karÅŸÄ±laÅŸtÄ±rma (commit `22bd051`) â€” YAPILDI + CANLI:** detay baÅŸlÄ±ÄŸÄ±na
>   "âš–ï¸ Firmayla KarÅŸÄ±laÅŸtÄ±r" â†’ overlay'de 2. firma aranÄ±r; KPI kÄ±yas tablosu (sÃ¶zleÅŸme/ciro/il/sektÃ¶r/
>   tenzilat, yÃ¼ksek=yeÅŸil) + yan yana sektÃ¶r daÄŸÄ±lÄ±mÄ± + "ğŸ¤ Ortak Zemin" (birlikte Ã§alÄ±ÅŸÄ±lan idareler/
>   sektÃ¶rler â€” canlÄ± test: 2 ecza deposu 171 ortak idare). Ã–NEMLÄ°: analiz_pivot BÃœYÃœK firmalarda timeout
>   ediyor (detay sayfasÄ±nÄ±n "En Ã‡ok Ã‡alÄ±ÅŸtÄ±ÄŸÄ± Ä°dareler" kartÄ± da bu yÃ¼zden bÃ¼yÃ¼k firmalarda sessizce
>   kayboluyor â€” ayrÄ± latent bug), o yÃ¼zden karÅŸÄ±laÅŸtÄ±rma kanÄ±tlÄ± ihale_sonuclari(yuklenici_id,â‰¤500)
>   sorgusuna dayandÄ±rÄ±ldÄ±. AI kartÄ± opsiyonel bÄ±rakÄ±ldÄ± (Pro upsell korundu).
>
> **TÃœM 8 SORUN TAMAM.** Kalan latent notlar: (a) analiz_pivot bÃ¼yÃ¼k firmalarda timeout â€” rekabet_ozet gibi
> statement_timeout bump'Ä± gerekebilir (detay sayfasÄ± idare/sektÃ¶r kartÄ± iÃ§in); (b) browser-pane screenshot
> aracÄ± bu oturumda genel Ã§alÄ±ÅŸmadÄ± â€” doÄŸrulamalar javascript_tool DOM sorgularÄ±yla yapÄ±ldÄ±.

> ## ğŸ§¾ 16 TEMMUZ (devam) â€” DASHBOARDâ†’ANASAYFA + DOÄRUDAN TEMÄ°N FÄ°LTRELERÄ° + DT KAZANAN FÄ°ZÄ°BÄ°LÄ°TE
> KullanÄ±cÄ± 3 acil bulgu bildirdi: (a) dashboard adÄ±, (b) DT'de kategori/tÃ¼r filtreleme yok, (c) DT kazanan
> firma takibi. YapÄ±lanlar:
>
> **âœ… 1 â€” Dashboard â†’ "Anasayfa" (commit `70dc7f4`):** 24 sayfada nav/baÅŸlÄ±k/geri-butonlarÄ±; URL `dashboard`
> kaldÄ±; TÃ¼rkÃ§e ek dÃ¼zeltildi. Ä°yzico/proxy panel referanslarÄ± (dÄ±ÅŸ servis) dokunulmadÄ±.
>
> **âœ… 2 â€” DoÄŸrudan temin filtreleri CANLI (commit'ler `c9ab47c`, `efa9313`, `9acf6be`):**
> - **Durum filtresi** (ğŸŸ¢ AÃ§Ä±k / âœ… SonuÃ§landÄ±) â€” EKAP'Ä±n 5 ham durumu 2 gruba (.in()), renkli rozet. Index'siz
>   gÃ¼venli (count latency tur 1.6s / durum 0.4s, mevcut tÃ¼r filtresiyle aynÄ± sÄ±nÄ±f).
> - **Kategori filtresi** â€” `dogrudan_temin_ilanlari.kategori` kolonu + **1.147.412 satÄ±r** sÄ±nÄ±flandÄ±rÄ±ldÄ±
>   (`dt_kategori_backfill.py` keyset+stream+CHUNK=60, idempotent) + `idx_dt_ilanlari_kategori_tarih` kompozit
>   index. Dropdown js/kategoriler.js'ten (41 kanonik). Scraper hook (kayit_donusturâ†’kategori_belirle). CSV'ye
>   kategori + formÃ¼l-enjeksiyon guard. DaÄŸÄ±lÄ±m %45 anlamlÄ± / **%55 "DiÄŸer"** (DT baÅŸlÄ±klarÄ± kÄ±sa+OKAS yok â†’
>   keyword geniÅŸletme ayrÄ± iÅŸ, ortak ilanlar sÄ±nÄ±flandÄ±rmasÄ±nÄ± da etkiler). CanlÄ± doÄŸrulandÄ±: GÄ±daâ†’68.413,
>   Ä°nÅŸaat+SonuÃ§landÄ± kombine Ã§alÄ±ÅŸÄ±yor, konsol temiz. DEPLOY SIRASI korundu (kolon+NOTIFY Ã¶nce, hook sonra).
>
> **ğŸ”’ 3 â€” DT KAZANAN TAKÄ°BÄ°: FÄ°ZÄ°BÄ°L AMA CAPTCHA ARKASINDA (kullanÄ±cÄ± "geniÅŸ geÃ§miÅŸ backfill" seÃ§ti):**
> Ã‡ekiÅŸmeli workflow kanÄ±tladÄ±: E10=dogrudanTeminId / E11=IdareId zaten dtAra listesinde (saklanmÄ±yor) â†’
> `DogrudanTeminDetay.aspx?IdareId=E11&IhaleId=E10` â†’ CAPTCHA (belge-indirmedeki birebir aynÄ±sÄ±) â†’ postback â†’
> "SONUÃ‡ Ä°LANI" bloÄŸunda kazanan+bedel+tarih. **KISIT:** asistan CAPTCHA'yÄ± programatik Ã§Ã¶zemez/Ã§Ã¶zdÃ¼remez;
> ÅŸema+parser+UI+E10/E11 yakalama kurulabilir, asÄ±l Ã§Ã¶zÃ¼m adÄ±mÄ±nÄ± kullanÄ±cÄ±nÄ±n `ekap_captcha_indir` hattÄ±
> Ã§alÄ±ÅŸtÄ±rÄ±r. Maliyet: her sonuÃ§=1 Gemini CAPTCHA; ~1M "15" kaydÄ±nda cookie-reuse (kotayÄ± ~100x dÃ¼ÅŸÃ¼rÃ¼r)
> MUTLAKA test edilmeli. Tam reÃ§ete + entegrasyon tasarÄ±mÄ± hafÄ±za `dt-kazanan-captcha`'da. **DURUM: kullanÄ±cÄ±
> yÃ¶nlendirmesi bekliyor** â†’ **ERTELENDÄ°:** kullanÄ±cÄ± "ÅŸimdilik duralÄ±m, sonra bana TEKRAR SOR ve iÅŸleme
> alalÄ±m" dedi. Ä°skele kurulmadÄ±; sonraki uygun oturumda kullanÄ±cÄ±ya tekrar aÃ§Ä±lacak.

> ## ğŸ”´ 16 TEMMUZ (2. OTURUM) â€” KRÄ°TÄ°K GÃœVENLÄ°K: SUPABASE STUDIO Ä°NTERNETE AÃ‡IKTI â†’ KAPATILDI
> Scraper korumasÄ± araÅŸtÄ±rÄ±lÄ±rken bulundu: `docker-compose.override.yml` Studio'yu `"3000:3000"` ile
> `0.0.0.0`'a yayÄ±nlÄ±yordu â†’ `http://195.85.207.126:3000` dÄ±ÅŸarÄ±dan **HTTP 200, AUTHSIZ** tam DB
> yÃ¶netici paneli. DÃ¼zeltildi: override `"127.0.0.1:3000:3000"` + `docker compose up -d --no-deps studio`;
> dÄ±ÅŸarÄ±dan :3000 artÄ±k 000, site/REST 200 (bozulmadÄ±), `.bak` yedeÄŸi var. EriÅŸim artÄ±k SSH tÃ¼neliyle
> (`ssh -L 3000:localhost:3000`). Detay: hafÄ±za [[studio-3000-exposure]]. **AÃ‡IK Ä°ÅLER (bu ifÅŸa yÃ¼zÃ¼nden):**
> (1) service_role/JWT/DB parola rotasyonu (Ã¶nerildi, YAPILMADI â€” JWT rotasyonu frontend anon anahtarÄ±nÄ±
> da deÄŸiÅŸtirir); (2) âœ… UFW `3000/tcp` kuralÄ± origin sÄ±kÄ±laÅŸtÄ±rmada silindi; (3) âœ… **ORIGIN SIKILAÅTIRILDI**
> â€” `backend/harden_origin.sh` ile Kong :8000/:8443 + Postgres :5432/:6543 (docker-published) iptables
> DOCKER-USER'da ens192'de DROP + nginx :80/:443 UFW'de yalnÄ±z Cloudflare IP aralÄ±klarÄ±. nginxâ†’127.0.0.1:8000
> loopback yolu etkilenmedi; dÄ±ÅŸarÄ±dan doÄŸrulandÄ± (hepsi 000, site+REST CF Ã¼zerinden 200). Detay:
> [[origin-hardening-cf-only]]. **KALAN AÃ‡IK:** (a) DOCKER-USER reboot'ta uÃ§ar (netfilter-persistent yok,
> VDS restart bekliyor) â†’ systemd oneshot/iptables-persistent gerek; (b) service_role/JWT/DB parola rotasyonu
> (Studio+Postgres aÃ§Ä±ktÄ±); (c) baypas kapandÄ± â†’ CF panelinde rate-limit artÄ±k anlamlÄ±.
>
> ## âœ… 16 TEMMUZ (2. OTURUM) â€” VERÄ° AKIÅI DENETÄ°MÄ°: 3 AKIÅ DA AKTÄ°F + KUPON/SUNUCU NOTLARI
> **1) Veri Ã§ekme denetimi (public REST, `olusturulma` yÃ¶ntemi â€” bkz. hafÄ±za `scraper-cron-silent-fail`):**
> - `ilanlar`: son yazÄ±m 16 Tem 09:28 UTC, son 24s **1000+** kayÄ±t, 391'i aynÄ±-gÃ¼n ilan tarihli â†’ SAÄLIKLI.
> - `dogrudan_temin_ilanlari`: son yazÄ±m 09:29 UTC, 24s'te 1000+; yazÄ±mlarÄ±n ~%99'u gÃ¼ncel (tarihâ‰¥10 Tem),
>   en ileri son-teklif 2027 â†’ aÃ§Ä±k DT akÄ±ÅŸÄ± + backfill paralel, SAÄLIKLI. (Not: DT'de tarih kolonu
>   `tarih`, `ilan_tarihi` DEÄÄ°L.)
> - `uluslararasi_ihaleler`: tablo 15 Tem 12:57'de doÄŸdu (Ã¶zellik yeni); 15 Tem 187 + 16 Tem 02:37'de
>   304 (300 TED + 4 Georgia) â†’ iki kaynak da yazÄ±yor, SAÄLIKLI. âš ï¸ TED tam 300 = muhtemel gece limiti;
>   "TED'in tamamÄ± gelsin" istenirse scraper limitine bakÄ±lmalÄ±. Cron LOG'larÄ± denetlenmedi (SSH engelli) â€”
>   kÄ±smi hata gÃ¶rÃ¼nmez ama veri tazeliÄŸi/hacmi normal.
> **2) âœ… Pro kupon ÃœRETÄ°LDÄ°:** kullanÄ±cÄ± kendine Pro istedi (Ã¶nce 1 ay dendi, sonra 6 aya Ã§evrildi).
> VDS'te `kupon_olustur.py --plan standart --ay 6 --adet 1` Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± â†’ **IHP-72DEF88A** (canlÄ± DB'de,
> tek kullanÄ±mlÄ±k). Ders: Pro'nun iÃ§ kodu `standart`; âš ï¸ yerel `backend/.env` hÃ¢lÃ¢ ESKÄ° managed
> Supabase'i gÃ¶steriyor â€” kupon/yazma iÅŸleri asla yerelden deÄŸil VDS'ten yapÄ±lmalÄ±.
> **3) Firma adÄ± mÃ¼kerrer denetimi (KARAR: DOKUNULMADI â€” kullanÄ±cÄ± onayÄ±yla ertelendi):** kullanÄ±cÄ±
> "bazÄ± firma isimlerini multi gÃ¶rdÃ¼m" dedi â†’ 71.384 firmanÄ±n tamamÄ± public REST'ten Ã§ekilip tarandÄ±
> (scratchpad script). Bulgular: normalize_ad mÃ¼kerreri 0 âœ…, birebir aynÄ± ad 0 âœ…, **TÃ¼rkÃ§e harf
> farkÄ±yla (Ã‡/C, Ä°/I) 24 grup** âš ï¸. ÃœÃ§ sÄ±nÄ±f: (a) bariz EKAP typo'su ~10 grup (YÄ°LDÄ°RÄ°M/YILDIRIM,
> BALCÄ°/BALCI, DEMÄ°R GLOBAL-AKSENTAÅ Ä°O "Ä°NSAAT" typo'su â€” aynÄ± gerÃ§ek firma bÃ¶lÃ¼nmÃ¼ÅŸ karne);
> (b) gerÃ§ekten farklÄ± kiÅŸiler olabilir (ACAR/AÃ‡AR, AKCA/AKÃ‡A) â€” OTOMATÄ°K BÄ°RLEÅTÄ°RME YASAK
> (bkz. hafÄ±za vkn-yok-beyan-rozet dersi: iki kiÅŸinin karnesini birleÅŸtirmek dÃ¼rÃ¼stlÃ¼k sorunu);
> (c) Ã§Ã¶p kayÄ±t: "Ä°Å ORTAKLIÄI"/"iÅŸ ortaklÄ±ÄŸÄ±" firma diye girmiÅŸ (9 sÃ¶z., â‚º109M). Arama sayfasÄ±nÄ±n
> ikisini birden gÃ¶stermesi arama_fold katlamasÄ± yÃ¼zÃ¼nden â€” davranÄ±ÅŸ doÄŸru. **Etki ~%0,03 olduÄŸu
> iÃ§in dÃ¼zeltme ertelendi.** Ä°leride yapÄ±lacaksa reÃ§ete: (1) normalize_firma'ya fold EKLEME;
> (2) yuklenici_yenile'ye Ã§Ã¶p-ad filtresi; (3) tr_fold GROUP BY HAVING>1 bekÃ§i raporu;
> (4) sÄ±nÄ±f-(a) typo'larÄ± elle birleÅŸtir.
> **4) ğŸ”´ BOT/SCRAPER KORUMASI DENETÄ°MÄ° â€” KORUMA YOK (kanÄ±tlÄ±, aksiyon bekliyor):** kullanÄ±cÄ± "millet
> bizden veri Ã§ekmesin" diye sordu. Ampirik test: anon key JS'te public (mimari gereÄŸi), curl/httpx ile
> 71K firma ~75 istekte Ã§ekildi, rate limit YOK, python-requests UA'sÄ± bile geÃ§iyor (CF Bot Fight kapalÄ±),
> tek sÄ±nÄ±r PostgREST 1000 satÄ±r/istek (350K ilanlar â‰ˆ 350 istek = dakikalar). robots.txt koruma deÄŸil +
> sitemap-firmalar SEO iÃ§in taramaya davet (bilinÃ§li). RLS'li kullanÄ±cÄ± verisi SAÄLAM. **Plan:**
> (1) CF panel ( mevcut VDS (â‰ˆ8GB/4Ã§ekirdek, disk %14) ÅÄ°MDÄ°LÄ°K YETERLÄ° â€” geÃ§iÅŸ
> tetikleyicileri: 2003+ tam backfill, RAM baskÄ±sÄ±, CPU doygunluÄŸu. GeÃ§ilecekse hedef: WeLAB BL460c
> **Gen8 Pro $43.48/ay** (2x E5-2680, 128GB, 980GB NVMe, "Database Server") â€” NVMe+yÃ¼ksek saat; SAS'lÄ±
> â‚º2.000-15.500 planlara gerek yok.
>
> ## ğŸ¨ 16 TEMMUZ (devam) â€” HARÄ°TA LEJANTLARINA "RENK = YOÄUNLUK" Ä°BARESÄ° + LEJANT KAYMASI DÃœZELTÄ°LDÄ° (commit `b2b4794`)
> KullanÄ±cÄ±: "haritalardaki renkler ihale durumunun yoÄŸunluk pozisyonunu gÃ¶sterir ÅŸekilde ibare olmasÄ± lazÄ±m".
> 4 harita Ã¶rneÄŸinin hepsine aÃ§Ä±k ibare + "veri yok" Ã§ipi + Azâ†’Ã‡ok gradyan ÅŸeridi eklendi:
> - **uluslararasi (dÃ¼nya):** "Renkler Ã¼lkedeki ihale yoÄŸunluÄŸunu gÃ¶sterir" â€” canlÄ±da doÄŸrulandÄ±.
> - **js/harita.js (dashboard) + index.html (satÄ±r-iÃ§i kopya):** "Renkler ildeki ihale yoÄŸunluÄŸunu gÃ¶sterir".
>   **BONUS BUG:** eski lejant renkâ†”aralÄ±k eÅŸlemesi 1 kova KAYMIÅTI (0 rengi #16233d lejantta yoktu, son kova
>   eksikti) â€” canlÄ± il_sayim verisiyle test: eski 85/88 uyuÅŸmazlÄ±k, yeni 0/88. Dashboard'a `?v=2` cache-bust.
> - **harita.html:** firma katmanÄ± "kayÄ±tlÄ± firma yoÄŸunluÄŸu" + RFQ katmanÄ± "aÃ§Ä±k talep durumu" ibareleri â€” canlÄ±da doÄŸrulandÄ±.
> - Not: browser-pane bu oturumda throttle'lÄ±ydÄ± (screenshot/scroll/IO donuk) â†’ index/dashboard lazy-harita
>   render'Ä± pane'de gÃ¶rÃ¼lemedi; doÄŸrulama canlÄ± veriyle birebir mantÄ±k testiyle yapÄ±ldÄ± (init koduna dokunulmadÄ±).

> ## ğŸŒ 16 TEMMUZ â€” ULUSLARARASI: Ä°NTERAKTÄ°F DÃœNYA HARÄ°TASI + DASHBOARD MENÃœ TAÅINDI (CANLI)
> **1) DÃ¼nya haritasÄ± (commit `71c537a`)** â€” kullanÄ±cÄ±: "uluslararasÄ± ihaleler ekranÄ±na bir dÃ¼nya haritasÄ±
> koysak da insanlar tÄ±klasa o Ã¼lkeyi seÃ§seâ€¦ excel formatÄ±nÄ±n dÄ±ÅŸÄ±na Ã§Ä±ksak". YapÄ±ldÄ±:
> - `js/dunya-harita.js` â€” johan/world.geo.json â†’ equirectangular SVG (179 Ã¼lke, key=ISO-A3, Antarktika hariÃ§,
>   viewBox 1000Ã—388.9, ~82KB). `ulke_ihale_dagilimi()` RPC (ulke_kodu, ulke=TÃ¼rkÃ§e ad, adet).
> - `uluslararasi.html`: statsâ†”toolbar arasÄ±na choropleth harita kartÄ±. Ä°hale sayÄ±sÄ±na gÃ¶re 4-bucket renk
>   (1â€“4 / 5â€“19 / 20â€“49 / 50+), hover tooltip (Ã¼lke + adet), **tÄ±klaâ†’f-ulke filtre** (aynÄ± Ã¼lkeye tekrar
>   tÄ±k = filtre kaldÄ±r/toggle). Filtre dropdown â†” harita seÃ§imi Ã§ift-yÃ¶nlÃ¼ senkron; "âœ• Ã¼lke filtresini
>   kaldÄ±r" kÄ±sayolu. Kritik kablo: harita ISO-A3 keyed ama f-ulke **TÃ¼rkÃ§e ad** ile filtreliyor
>   (`query.eq('ulke', ulke)`) â†’ RPC'nin ulke_koduâ†”ulke eÅŸlemesi kÃ¶prÃ¼.
> - CanlÄ±da doÄŸrulandÄ±: 179 path (31 verili renkli), Almanya tÄ±kâ†’"121 ihale" (RPC DEU=121 birebir), tÃ¼m
>   kartlar ğŸŒ Almanya, highlight+temizle butonu; toggleâ†’491'e dÃ¶ndÃ¼. Konsol temiz. (Not: browser-pane
>   screenshot aracÄ± 179-path SVG'yi rasterize ederken timeout veriyor â€” sayfa gerÃ§ek kullanÄ±cÄ±da sorunsuz,
>   iÅŸlevsel JS doÄŸrulamasÄ± eksiksiz.)
>
> **2) Dashboard "Kamu Ä°haleleri"ne taÅŸÄ±ndÄ± (commit `685bd56`)** â€” kullanÄ±cÄ±: "insanlar oradaki TÃ¼rkiye
> haritasÄ±nÄ± ve ihale verilerini GENEL sanar, yanÄ±lgÄ±ya dÃ¼ÅŸeriz". 24 HTML sayfada nav: Dashboard artÄ±k
> "Genel" yerine "Kamu Ä°haleleri" bÃ¶lÃ¼mÃ¼nÃ¼n ilk maddesi; "Genel" etiketi kaldÄ±rÄ±ldÄ±.
>
> **3) GÃ¼rcistan duyuru no gÃ¶rÃ¼nÃ¼r (Ã¶nceki, commit dahil)** â€” Georgia/TED ilanlarÄ±nda `publication_no`
> (Ã¶rn. NAT260014727) baÅŸlÄ±k altÄ±nda kopyalanabilir rozet olarak gÃ¶steriliyor; lang=en link zaten kullanÄ±mda.

> ## ğŸ 15 TEMMUZ (devam) â€” SONUÃ‡LANANLAR SAYFASI DÃœZELTÄ°LDÄ° + CANLI (commit `cb307f7`)
> **Sorun:** `sonuclananlar.html` tÃ¼m `ihale_sonuclari`'yÄ± (355K+ satÄ±r) client'a `for(off+=1000)`
> dÃ¶ngÃ¼sÃ¼yle indiriyor + tÃ¼m ilanlarÄ± ayrÄ±ca Ã§ekiyordu â†’ tablo bÃ¼yÃ¼yÃ¼nce "SonuÃ§lar yÃ¼kleniyorâ€¦"
> sonsuza kadar asÄ±lÄ± kalÄ±yor, istatistikler "â€”". (dogrudan-temin ile aynÄ± sÄ±nÄ±f bug.)
> **Ã‡Ã¶zÃ¼m (server-side'a Ã§evrildi):**
> - Ä°statistik kartlarÄ± â†’ yeni `sonuc_ozet()` RPC (count / sum(kazanan_teklif) / avg(tenzilat, |x|â‰¤100
>   uÃ§-deÄŸer filtresi) / count(distinct firma)). `backend/migration_sonuc_ozet_rpc.sql`.
> - Liste â†’ sunucu sayfalÄ± sorgu + embed `ilanlar(baslik,idare,il,tur)` join; `.order()` sunucuda;
>   `.range()` ile 25'lik sayfalama. `count=exact` 355K'da **timeout** verdi â†’ kaldÄ±rÄ±ldÄ±, toplam RPC'den.
> - SÄ±ralama (tarih/bedel/tenzilat) iÃ§in 3 **partial index** (`WHERE kazanan_firma IS NOT NULL`):
>   `backend/migration_sonuc_index.sql` â†’ ORDER BY+LIMIT full-sort'tan index-scan'e (~1.5s).
> - CSV â†’ capped 5000 satÄ±r sunucu fetch (tÃ¼m tabloyu indirmez).
> - CanlÄ±da doÄŸrulandÄ±: 355.275 kayÄ±t, â‚º4665 Mrd, %51.7 tenzilat, 65.443 firma; sÄ±ralama+sayfalama
>   (1/14211) Ã§alÄ±ÅŸÄ±yor, konsol temiz.
> **Not:** AynÄ± "tÃ¼mÃ¼nÃ¼ client'a indir" kalÄ±bÄ± baÅŸka sayfalarda kaldÄ±ysa (firmalar/idareler/sektÃ¶rler
>   dizinleri zaten server-side sanÄ±yorum) benzer ÅŸekilde taranmalÄ±.

> ## ğŸ§­ 15 TEMMUZ (devam) â€” 3 SÄ°STEM SIRASI (kullanÄ±cÄ±: "hepsini sÄ±rasÄ±yla yap") + TAKSONOMÄ° HÄ°ZALANDI
> KullanÄ±cÄ± 3 iÅŸi sÄ±rayla istedi. SÄ±ra (baÄŸÄ±mlÄ±lÄ±k): **1) SektÃ¶r taksonomi + bildirim â†’ 2) Harita MVP â†’
> 3) Kurumsal doÄŸrulama (GÄ°B/MERSÄ°S)**.
>
> **âœ… 1a â€” SEKTÃ–R TAKSONOMÄ° HÄ°ZALAMA TAMAM + CANLI (commit `59bf492`):**
> - KÃ¶k sorun: profil.html **31 eski kÄ±sa anahtar** (`insaat`...) saklÄ±yordu ama `ilanlar.kategori` /
>   uluslararasÄ± / RFQ hepsi **kanonik ad** ("Ä°nÅŸaat - AltyapÄ± - ÃœstyapÄ± - YapÄ±m") â†’ eÅŸleÅŸme kopuk.
> - `js/kategoriler.js` = TEK KAYNAK (41 kanonik + emoji/aÃ§Ä±klama + eskiâ†’kanonik map). profil.html artÄ±k
>   buradan besleniyor (index-tabanlÄ± DOM id, Set'te kanonik ad; eski satÄ±rlar da doÄŸru gÃ¶sterilir).
> - Migration (`migration_taksonomi_hizala.sql`): ilanlar'da eski **"Ä°nÅŸaat & YapÄ±m" â†’ kanonik: 17.415 satÄ±r**
>   birleÅŸti; mevcut 1 profil kÄ±sa-anahtarâ†’kanonik remap. DoÄŸrulandÄ± (kategoriler.js 41 geÃ§erli; Ä°nÅŸaat&YapÄ±m
>   ~0'a dÃ¼ÅŸtÃ¼, 45 karakter-varyantÄ± straggler ihmal edilebilir).
> - Not: `ilanlar.kategori`'de hÃ¢lÃ¢ genel fallback'ler var ("Mal AlÄ±mÄ±" 173+, "Hizmet AlÄ±mÄ±", "DiÄŸer") â€”
>   bunlar gerÃ§ekten sÄ±nÄ±flandÄ±rÄ±lamamÄ±ÅŸ (keyword yok), hedeflenebilir sektÃ¶r deÄŸil; bÄ±rakÄ±ldÄ±.
> - YAN FAYDA: firmalar artÄ±k 31 deÄŸil TÃœM 41 kanonik kategoriyi seÃ§ebilir (HayvancÄ±lÄ±k, Madencilik, Reklam,
>   Savunma, Turizm, Menkul Mallar, Odun-KÃ¶mÃ¼r, Ä°nÅŸaat Malzemeleri, Kent MobilyalarÄ±, Sanat eklendi).
>
> **âœ… 1b â€” BÄ°LDÄ°RÄ°M EÅLEÅTÄ°RME TAMAM + CANLI (commit `444ce1b`):** notify.py sadece takip edilen ihale
>   hatÄ±rlatÄ±cÄ±sÄ±ydÄ±; sektÃ¶r-bazlÄ± "sana uygun yeni ihale/RFQ" YOKtu. Eklendi (`migration_bildirim_uret.sql`):
>   - `yeni_ilan_bildirim_uret(p_gun)` SECURITY DEFINER â†’ aktif ilanlar Ã— profil.sektorler (kanonik eÅŸleÅŸme)
>     + tercih_iller/tercih_turler filtresi â†’ bildirimler'e ekle (tur='ihale', aksiyon_url=ihale-detay).
>   - `yeni_rfq_bildirim_uret(p_gun)` â†’ yeni RFQ Ã— tedarikÃ§i sektÃ¶rÃ¼ (kendi RFQ'su hariÃ§, tur='eslestirme',
>     ilan_id FK ilanlar'a baktÄ±ÄŸÄ± iÃ§in RFQ'da NULL; dedup aksiyon_url'den).
>   - Dedup NOT EXISTS (ikinci Ã§aÄŸrÄ± 0 dÃ¶ndÃ¼ âœ“). FK doÄŸrulandÄ±: profil.user_id = kullanici_profiller.id =
>     auth.users.id (3/3). Format Ã¶nizlemeyle doÄŸrulandÄ± (kanonik Ä°nÅŸaat eÅŸleÅŸti â†’ taksonomi hizalamasÄ± iÅŸe yaradÄ±).
>   - Gece cron'a baÄŸlandÄ± (`run_scraper.sh` sonu, p_gun=1 â†’ retroaktif spam yok). Bu gece ilk gerÃ§ek Ã¼retim.
>   - AÃ‡IK (iyileÅŸtirme): geniÅŸ-sektÃ¶r firma gÃ¼nde ~50 bildirim alabilir (370/7gÃ¼n 1 firma) â†’ ileride
>     e-posta digest + gÃ¼nlÃ¼k cap. Åimdilik in-app yeterli (bildirimler sayfasÄ± sayfalÄ±). E-posta = 2. faz.

> ## ğŸ 15 TEMMUZ (devam) â€” ULUSLARARASI + FÄ°RMA-ANALÄ°Z HATA DÃœZELTMELERÄ° + CANLI (commit `7d2c63a`)
> KullanÄ±cÄ± 3 hata bildirdi (uluslararasÄ± ihaleler ekran gÃ¶rÃ¼ntÃ¼leri):
> 1. **TED linki 404** â€” `orijinal_url` formatÄ± `/en/notice/{pub}` YANLIÅ (404). DoÄŸru: `/en/notice/-/detail/{pub}`.
>    `ted_scraper.py:158` dÃ¼zeltildi + 183 mevcut kayÄ±t `backend/migration_ted_url_fix.sql` ile backfill edildi
>    (publication_no'dan yeniden kur, idempotent). TarayÄ±cÄ±da notice aÃ§Ä±ldÄ±ÄŸÄ± doÄŸrulandÄ±.
> 2. **GÃ¼rcistan'da "TED'de AÃ§" yazÄ±yor** ama kendi sitesine (tenders.procurement.gov.ge) gidiyordu â€” etiket sabitti,
>    select'te `kaynak` yoktu. `kaynakAc(kaynak)` eklendi: TEDâ†’"TED'de Ä°ncele", georgiaâ†’"GÃ¼rcistan PortalÄ±nda Ä°ncele".
> 3. **Buton belirgin deÄŸil** ("ben bile zor buldum") â€” kÃ¼Ã§Ã¼k mavi metin yerine amber dolu belirgin `.ui-ac-btn`.
> 4. **firma-analiz "Geri" Ã§alÄ±ÅŸmÄ±yor** â€” `href=javascript:history.back()` ama sayfa `pushState` kullanÄ±yor â†’
>    geri kendi state'ine dÃ¶nÃ¼yordu. `geriGit()` (referrer aynÄ±-origin/farklÄ±-sayfaysa oraya, yoksa firmalar) +
>    belirgin bordered buton. **YAN BULGU:** `csvIndir`/`linkPaylas`/`geriGit` IIFE iÃ§inde dÃ¼z `function` idi â†’
>    inline `onclick` global arÄ±yor â†’ CSV+PaylaÅŸ+Geri HEPSÄ° bozuktu; Ã¼Ã§Ã¼ de `window.X=` ile expose edildi.
> Ders: IIFE'li sayfalarda inline `onclick="fn()"` Ã§aÄŸrÄ±lan her fonksiyon `window.X=` ile expose EDÄ°LMELÄ°
>    (closure fonksiyonu onclick'ten eriÅŸilemez).
> **AUDIT YAPILDI (tÃ¼m .html tarandÄ±, line-start IIFE + plain-function imzasÄ±yla):** bozuk yalnÄ±z
>    firma-analiz + **kurum-analiz** (csvIndir/linkPaylasKurum) idi â†’ ikisi de dÃ¼zeltildi+canlÄ±da doÄŸrulandÄ±
>    (commit `e2166df`). DiÄŸer sayfalar (ihaleler/takipte/firmalar/idareler/sektÃ¶rler...) ana script IIFE
>    DEÄÄ°L â†’ fonksiyonlarÄ± zaten global, saÄŸlam (canlÄ± `typeof` ile teyit edildi).

> ## ğŸ” 15 TEMMUZ (devam) â€” e-SATINALMA v4: KURUMSAL GATE + VKN/ÃœNVAN/ADRES ZORUNLU + CANLI (commit `e80d92a`)
> KullanÄ±cÄ± kararÄ±: "her Ã¶nÃ¼ne gelen ihale aÃ§amamalÄ±" + "adres de zorunlu (MaaS harita iÃ§in hazÄ±r veri)".
> **Ã–nemli veri gerÃ§eÄŸi (doÄŸrulandÄ±):** yÃ¼klenicilerin VKN'sini ALAMIYORUZ â€” `yukleniciler.vergi_no` (53.897)
> ve `ihale_sonuclari.yuklenici_vergi_no` (355K) **ikisi de %0 dolu**. Scraper `yukleniciVergiNo` alanÄ±nÄ±
> deniyor ama EKAP kamu sonuÃ§ feed'i VKN dÃ¶ndÃ¼rmÃ¼yor. Ã–nceki "EKAP'tan otomatik VKN doÄŸrularÄ±z" varsayÄ±mÄ± YANLIÅ.
> **YapÄ±ldÄ±:**
> - RFQ YAYINLAMA yalnÄ±z geÃ§erli `kurumsal` abonelikle. AsÄ±l zorlama RLS'te (anon key ile herkes POST atabilir):
>   `SECURITY DEFINER public.kullanici_kurumsal_mi()` + INSERT policy `talep_kurumsal_ekler`
>   (sahiplik + VKN 10-hane + Ã¼nvan + il/ilÃ§e/aÃ§Ä±k adres + kurumsal). `backend/migration_ozel_ihaleler_v4.sql`.
> - Form (ozel-ihaleler.html): VKN (TÃ¼rk checksum, advisory) + Ã¼nvan + **il(zorunlu)/ilÃ§e/aÃ§Ä±k adres** eklendi.
>   `js/plan.js`'e `getPlanKod()`/`isKurumsal()` (getPlan 'standart'+'kurumsal'Ä± ayÄ±ramÄ±yordu).
> - Adres YAPISAL saklanÄ±yor (il/ilce/acik_adres + enlem/boylam kolonlarÄ±) â†’ MaaS harita/geocode iÃ§in hazÄ±r.
> **Ã‡EKÄ°ÅMELÄ° Ä°NCELEME (Workflow, 12 ajan, 5 bulgu onaylandÄ±) â†’ DÃœZELTÄ°LDÄ°:**
>   - 3 aÃ§Ä± baÄŸÄ±msÄ±z aynÄ± kusuru buldu: "Kamuda tanÄ±nan alÄ±cÄ±" gÃ¼ven rozeti SAHTELENEBÄ°LÄ°R (Ã¼nvan beyan,
>     kimliÄŸe baÄŸlanamÄ±yor â†’ Ã¼nlÃ¼ firma karnesi taklidi; fuzzy `%ilike%`+en-bÃ¼yÃ¼k+kaÃ§Ä±rÄ±lmamÄ±ÅŸ `%`/`_` â†’ dÃ¼rÃ¼st
>     kullanÄ±cÄ±da bile yanlÄ±ÅŸ eÅŸleÅŸme). **Rozet KALDIRILDI**; kimlik "AlÄ±cÄ± (beyan) Â· â“˜ doÄŸrulanmamÄ±ÅŸ" gÃ¶steriliyor.
>   - esc() tek-tÄ±rnak hardening. SaÄŸlam Ã§Ä±kanlar: kurumsal-gate/SECURITY DEFINER âœ“, anon-VKN-gÃ¶rÃ¼nÃ¼rlÃ¼ÄŸÃ¼ kasÄ±tlÄ± âœ“.
>   - Ãœnvanâ†’yukleniciler eÅŸleÅŸtirme TEKNOLOJÄ°SÄ° meÅŸru yerinde kalÄ±yor: RFQâ†’**tedarikÃ§i** Ã¶nerisi (o firmanÄ±n
>     kamu-sonucu karnesi, beyan deÄŸil). AlÄ±cÄ±-tarafÄ± rozet olarak KULLANILMAMALI.
> - **Cache tuzaÄŸÄ±:** CF edge eski `js/plan.js`'i sunuyordu â†’ `Plan.isKurumsal` undefined. Fix: `?v=v4` cache-bust
>   + savunmacÄ± `typeof Plan.isKurumsal==='function'` guard. (Ders: js/ dosyasÄ± deÄŸiÅŸince ?v= ÅŸart, CF cache'liyor.)
> **AÃ‡IK (gelecek):** gerÃ§ek kimlik doÄŸrulama = VKNâ†”Ã¼nvan'Ä± yetkili kaynaÄŸa (GÄ°B VKN sorgu / MERSÄ°S / KEP) baÄŸlamak;
>   o zamana kadar gÃ¼ven = Kurumsal-abonelik kapÄ±sÄ± + tedarikÃ§inin beyan VKN'yi baÄŸÄ±msÄ±z doÄŸrulamasÄ±.

> ## ğŸ›¡ï¸ 16 TEMMUZ â€” PROJE GENELÄ° DENETÄ°M (#4): 42 BULGU, ~30 DÃœZELTÄ°LDÄ° + CANLI (gece otonom)
> 6-aÃ§Ä±lÄ± Ã§ok-ajan Ã§ekiÅŸmeli denetim (gÃ¼venlik/RLS/XSS, bug, kopuk-link, performans, backend, UX) â†’ 45 bulgu,
> 42 doÄŸrulandÄ±. Ã–nceliÄŸe gÃ¶re uygulandÄ± (commit'ler ea4d1beâ€¦9026e17):
> **KRÄ°TÄ°K (canlÄ±):** bildirimler.html stored XSS (RFQ baÅŸlÄ±ÄŸÄ±â†’cronâ†’tedarikÃ§i bildirimiâ†’JWT Ã§alma; benim
>   bildirim Ã¶zelliÄŸim tetikliyordu) esc'lendi; teklif-olustur para parse bug (â‚º1.234.567,89â†’DB'ye 1 TL)
>   hesaplanan sayÄ±sal deÄŸere Ã§evrildi.
> **XSS (canlÄ±):** ihaleler + ihale-detay + dashboard scrape-veri sink'leri esc'lendi; ihale-detay ilan_html
>   sanitizer'Ä±na on*/javascript:/data: temizliÄŸi (kara-liste bypass); CSV formÃ¼l-enjeksiyonu korumasÄ± (ihaleler+sonuclananlar).
> **PERF (canlÄ±):** ilanlar 3 index (durum/son_teklif/ilan_tarihi â€” 256K'da seq scan); dashboard 2 widget
>   RPC'ye (idare_sayim/kategori_sayim, ~32 istekâ†’2); sektorler gereksiz count:exact kaldÄ±rÄ±ldÄ±.
> **BACKEND (canlÄ±, api restart):** api.py kredi_dus hatasÄ± artÄ±k yÃ¼kseltiliyor (sessiz bedava AI); bozuk
>   /admin/scraper-cronâ†’503; notify.py deadline dedup (her gece spam); ekap_scraper boÅŸ veride exit(1)+cron uyarÄ±;
>   worker.py cache belge-indirmeden Ã¶nce (#17). RLS: teklif_talep_sahibi_gunceller kaldÄ±rÄ±ldÄ± (alÄ±cÄ± tedarikÃ§i teklifini deÄŸiÅŸtirebiliyordu).
> **POLISH (canlÄ±):** yanlÄ±ÅŸ domain ihaleplatformâ†’ihaleglobal; index footer Ã¶lÃ¼ linkler+Â©2026; fiyatlandÄ±rma
>   404 link; bÃ¼lten il toLocaleUpperCase(tr); ihaleler uydurma Math.random uyum skoruâ†’'profil ekle'; firma-analiz
>   'Ä°halelerini GÃ¶r' kendi sekmesi; kik-kararlar or() sanitize; login Supabase hatalarÄ± TÃ¼rkÃ§e; ekapLink usul argÃ¼manÄ±;
>   dashboard Ctrl+K + kayÄ±tlÄ±-arama tÃ¼m filtreleri taÅŸÄ±yor.
> **MOBÄ°L (canlÄ±, doÄŸrulandÄ±):** 18 app sayfasÄ±na js/main.js (hamburger â€” mobilde nav kayboluyordu) + ihaleler.html
>   eksik responsive @media. Mobilde hamburgerâ†’menÃ¼ aÃ§Ä±lÄ±yor, test edildi.
>
> **âœ… DEVAM TURU EK DÃœZELTMELER (canlÄ±+doÄŸrulandÄ±):**
>  - **firmalar.html #26 client-load-all â†’ server-side** (yuklenici_ozet RPC + arama_fold trgm + sort index + sayfalÄ±). Test edildi.
>  - **#18 RLS anon acik_adres/VKN ifÅŸasÄ±** â†’ column-level grant + ozel-ihale-detay anon dalÄ± gÃ¼venli-kolon. Test: anon select=*â†’401, VKN/adresâ†’42501, detayda gizli, public liste Ã§alÄ±ÅŸÄ±yor.
>  - **kurum-analiz #7 KISMEN**: ilanlar.idare trgm GIN index (full seq scan gitti; client yÃ¼kleme idare-boyutu kadar kaldÄ±).
>  - **#37 profil eriÅŸilebilirlik**: sektÃ¶r/il/tÃ¼r chip'leri klavye-eriÅŸilebilir (role=button/tabindex/keydown/aria/focus).
>  - **CoÄŸrafi eÅŸleÅŸtirme**: il_merkez + ihaleye_uygun_firmalar_geo RPC + Ã¶neri akÄ±ÅŸlarÄ±na baÄŸlandÄ± (mesafe_km gÃ¶sterimi). Test edildi.
>
> **âœ… DEVAM TURU-2 EK (canlÄ±+doÄŸrulandÄ±):** rekabet-analizi #4 â†’ rekabet_ozet RPC (8 breakdown+trend jsonb, render
>   fonksiyonlarÄ± RPC tÃ¼ketiyor, doÄŸrulandÄ±); XSS hardening sweep (sonuclananlar/idareler/kurum-analiz/sektorler/uyumluluk
>   esc'lendi â†’ XSS sÄ±nÄ±fÄ± TÃœM sayfalarda kapalÄ±).
>
> **âœ… DEVAM TURU-3 (16 Tem, canlÄ±+doÄŸrulandÄ±):** kurum-analiz #7 TAM Ã‡Ã–ZÃœM â†’ `kurum_ozet(p_idare)` RPC (backend/migration_kurum_ozet.sql,
>   rekabet_ozet reÃ§etesinin aynÄ±sÄ±): topluCek() 1000'erli client-load-all dÃ¶ngÃ¼sÃ¼ kaldÄ±rÄ±ldÄ± (en bÃ¼yÃ¼k idare 7.072 ilan â†’
>   8 ardÄ±ÅŸÄ±k fetch idi). KPI+8 breakdown (aylÄ±k trend 24 ay/yÄ±llÄ±k/tÃ¼r/il/kategori top12/usul/durum) tek jsonb RPC'den;
>   ihale listesi server-side `.range()` sayfalÄ± (topSayfa=kpi.toplam'dan, count=exact YOK); CSV export lazy â€”
>   sadece tÄ±klanÄ±nca sayfalÄ± Ã§eker. Åekiller eski client hesabÄ±yla birebir (aktif=son_teklif>now, 'DiÄŸer'/'Kategorisiz'/
>   'BelirtilmemiÅŸ' fallback'leri server'da). **DoÄŸrulama:** migration VDS'te uygulandÄ±; en bÃ¼yÃ¼k idare (Ä°l SaÄŸlÄ±k MÃ¼d.
>   SAÄLIK BAKANLIÄI..., ilikeâ†’8.177 kayÄ±t) canlÄ±da test â€” RPC warm ~55ms, konsol temiz, tÃ¼r toplamÄ±=KPI toplamÄ±,
>   pager 409 sayfa/sayfa-2 geÃ§iÅŸi OK; TÃœRASAÅ (371/40 aktif/â‚º21.6M) KPI'larÄ± psql ile birebir. Not: bÃ¼yÃ¼k idarenin
>   bÃ¼tÃ§esi 'â€”' Ã§Ã¼nkÃ¼ backfill verisinde yaklasik_maliyet_min hep 0/NULL (RPC deÄŸil veri durumu).
>   Dokunulan: kurum-analiz.html, backend/migration_kurum_ozet.sql.
>
> **â¸ HÃ‚LÃ‚ ERTELENEN:**
>  - **payment.py atomiklik/idempotency (#12/#19/#27/#28):** iyzico webhook mÃ¼kerrer kredi + kredi_yukle/kupon
>    lost-update/TOCTOU. Para-iÅŸleme kodu; gÃ¶zetimsiz deÄŸiÅŸtirmek RÄ°SKLÄ°. ReÃ§ete: kredi_hareketleri.siparis_id
>    UNIQUE+ON CONFLICT DO NOTHING; kupon `UPDATE...WHERE kullanim<max RETURNING`; kredi_yukle atomik increment. **KULLANICI ONAYIYLA.**
>  - **#14 ihaleler uyum sÄ±ralamasÄ± 200-satÄ±r cap** (server-side uyum/embedding gerekir).

> ## ğŸ” 16 TEMMUZ â€” #3 KURUMSAL DOÄRULAMA: FÄ°ZÄ°BÄ°LÄ°TE (araÅŸtÄ±rÄ±ldÄ±, KARAR KULLANICIDA)
> Soru: beyan VKN'yi yetkili kaynaÄŸa baÄŸlayÄ±p gerÃ§ek "DoÄŸrulanmÄ±ÅŸ Firma" yapabilir miyiz?
> **Bulgu (araÅŸtÄ±rÄ±ldÄ±):** GÄ°B'in ÃœCRETSÄ°Z aÃ§Ä±k VKNâ†’Ã¼nvan API'si YOK. SeÃ§enekler:
>  1. **Ãœcretli entegratÃ¶r API** (Nilvera / Ä°ZÄ°BÄ°Z / Digital Planet): VKNâ†’tam Ã¼nvan+adres+FAAL verir.
>     Hesap + Ã¶deme gerekir â†’ **KULLANICININ Ä°Å KARARI** (ben hesap aÃ§amam/Ã¶deme giremem). EtkinleÅŸtirince
>     `dogrulama_durumu='dogrulanmis'` yazÄ±lÄ±r + yeÅŸil "DoÄŸrulanmÄ±ÅŸ Firma" rozeti (o zaman gerÃ§ek olur).
>  2. **GÄ°B/e-Devlet Ã¼cretsiz web sorgu** (turkiye.gov.tr/gib-intvrg-...): sadece MASKELÄ° ad (ilk harfler) +
>     FAAL durumu; muhtemelen captcha/rate-limit. Prod VDS'ten gov tax endpoint scrape = kÄ±rÄ±lgan + ToS/KVKK
>     riski (kamu-hassas proje) â†’ **otonom kurulmadÄ±** (bilinÃ§li karar). Sadece "VKN gerÃ§ek+FAAL mÄ±" doÄŸrular,
>     tam Ã¼nvan vermez.
>  3. **KEP / kurumsal e-posta / manuel onay**: uygulanabilir ama e-posta altyapÄ±sÄ± (temiz domain, ertelendi)
>     veya insan-ops gerekir.
> **Zaten yapÄ±lan (v4) yeterli baz:** Kurumsal-plan gate (Ã¶deme+audit izi) + zorunlu VKN (checksum) + dÃ¼rÃ¼st
> "beyan Â· doÄŸrulanmamÄ±ÅŸ" etiketi. Sahtelenebilir "kamuda tanÄ±nan" rozeti kaldÄ±rÄ±ldÄ±. Yani anti-fraud'un kod
> kÄ±smÄ± tamam; kalan tek ÅŸey DIÅ doÄŸrulama = para/iÅŸ kararÄ±. **Ã–neri:** hacim artÄ±nca (1) Ã¼cretli API entegre et;
> `satinalma_talepleri`'ne `dogrulama_durumu` kolonu + 3-kademeli rozet (beyan / kurumsal-Ã¼ye / doÄŸrulanmÄ±ÅŸ).

> ## âœ… 16 TEMMUZ â€” HARÄ°TA MVP TAMAM + CANLI (gece otonom, commit `31596a9`)
> KullanÄ±cÄ± "hepsini sÄ±rasÄ±yla yap + gece boyu tam yetki" dedi. #2 Harita MVP yapÄ±ldÄ±:
> - **CoÄŸrafya verisi:** alpers/Turkey-Maps-GeoJSON (MIT) tr-cities.json â†’ Python projeksiyon (equirectangular,
>   boylam cos dÃ¼zeltmesi) â†’ `js/tr-harita.js` (81 il inline SVG path + centroid, 73KB, self-contained,
>   dÄ±ÅŸ tile baÄŸÄ±mlÄ±lÄ±ÄŸÄ± YOK). key=fold(il ad) â†’ Afyonâ†’Afyonkarahisar. Projeksiyon doÄŸrulandÄ± (Ä°stanbul KB,
>   Van/Hakkari doÄŸu, Sinop en kuzey).
> - **harita.html:** TÃ¼rkiye choropleth (firma yoÄŸunluÄŸu, `il_firma_dagilimi()` RPC, **QUANTILE** kova â€”
>   veri 300-1000'de yÄ±ÄŸÄ±lÄ±ydÄ±, sabit kova ayrÄ±m yapmÄ±yordu; tek-hue sÄ±cak sequential dark-surface) +
>   aÃ§Ä±k RFQ pin katmanÄ± (`il_rfq_dagilimi()`) + il tÄ±klama paneli (KPI + top firma ilike il + aÃ§Ä±k RFQ) +
>   hover tooltip + dinamik legend + stat tile'lar. Sidebar'a 23 sayfada eklendi (e-SatÄ±nalma altÄ±na).
> - CanlÄ±da doÄŸrulandÄ±: 81 il, 53.897 firma, Ankara en yoÄŸun (6.241/â‚º1.9Tn), 3 RFQ pin, tÄ±klama paneli Ã§alÄ±ÅŸÄ±yor.
> - **Faz-2 (AÃ‡IK):** coÄŸrafya-aÄŸÄ±rlÄ±klÄ± "En Uygun 3 Ãœretici" (ihaleye_uygun_firmalar'a mesafe boyutu) +
>   MaaS canlÄ±-kapasite yeÅŸil pin + aÃ§Ä±k adres precise geocode (ÅŸu an il-centroid). Screenshot pane'de timeout
>   veriyor (renderer limiti) â†’ gÃ¶rsel deÄŸil DOM/etkileÅŸim testiyle doÄŸrulandÄ±.

> ## ğŸ—ºï¸ 15 TEMMUZ â€” e-SATINALMA HARÄ°TA + MaaS KÃ–PRÃœSÃœ (orijinal planlama notu)
> KullanÄ±cÄ±: e-SatÄ±nalma ekranÄ± TÃ¼rkiye haritasÄ±nda aÃ§Ä±lsÄ±n (kÄ±rmÄ±zÄ± pin=talep/RFQ); ileride MaaS fasoncularÄ±yla
> (yeÅŸil pin=boÅŸ kapasite) aynÄ± ekranda; mesafe-bazlÄ± lokal eÅŸleÅŸtirme + "acil iÅŸ radarÄ±" (spot piyasa push).
> **Benim Ã¶nerim (kullanÄ±cÄ±ya sunuldu):**
> - **Otonom sÄ±ralama + insan-onaylÄ± davet** (manuel pin-avÄ± DEÄÄ°L, tam-otomatik atama da DEÄÄ°L). Mevcut
>   `ihaleye_uygun_firmalar` RPC'sine coÄŸrafi (il/mesafe) boyut eklenerek "Bu Ä°ÅŸ Ä°Ã§in En Uygun 3 Ãœretici" hesaplanÄ±r;
>   alÄ±cÄ± seÃ§er/davet eder (gÃ¼ven+sorumluluk). Bu bizim asÄ±l moat'Ä±mÄ±z (EKAP karnesi + kapasite + coÄŸrafya).
> - **SoÄŸuk-baÅŸlangÄ±Ã§ dÃ¼rÃ¼stlÃ¼ÄŸÃ¼:** ÅŸu an 3 test RFQ var â†’ boÅŸ harita kÃ¶tÃ¼ gÃ¶rÃ¼nÃ¼r. Ã‡Ã¶zÃ¼m: haritayÄ± ELÄ°MÄ°ZDEKÄ°
>   veriyle doldur â€” RFQ pinleri + `yukleniciler.il` yoÄŸunluÄŸu (53.897 firma) â†’ gÃ¼n-1'de deÄŸerli, MaaS beklemeden.
> - **Geocode gerÃ§eÄŸi:** pin koordinat ister, dÃ¼z adres yetmez. Faz-1: il/ilÃ§e MERKEZ (81 il, offline tablo, bedava).
>   Faz-2 (MaaS): aÃ§Ä±k adres â†’ lat/lng geocode + canlÄ± boÅŸ-kapasite yeÅŸil pin + "5 km'de acil lazer kesim" push.
> - **Gizlilik:** aÃ§Ä±k adres pin'i ne aldÄ±ÄŸÄ±nÄ±+nerede olduÄŸunu ifÅŸa eder â†’ herkese ilÃ§e-pin, aÃ§Ä±k adres yalnÄ±z
>   teklif veren/davetli tedarikÃ§iye. (v4'te adres anon-okunur; harita fazÄ±nda bu kÄ±sÄ±t gÃ¶zden geÃ§irilecek.)
> Karar bekleyen: manuel mi otonom mu â†’ Ã¶nerim OTONOM sÄ±ralama + onaylÄ± davet.

> ## ğŸ›ï¸ 15 TEMMUZ (devam) â€” MÄ°MARÄ°/IA KARARI: TEK ENTEGRE APP + MODÃœLLER (subdomain'e BÃ–LME)
> KullanÄ±cÄ±yla netleÅŸen Ã¼rÃ¼n mimarisi (kararlaÅŸtÄ±rÄ±ldÄ±):
> - **3-yÃ¶nlÃ¼ subdomain'e (kamu/Ã¶zel/yurtdÄ±ÅŸÄ±) BÃ–LME.** Tek entegre uygulama, bunlar Ä°Ã‡ERÄ°DE modÃ¼l/sekme.
>   GerekÃ§e: rakip avantajÄ± (moat) ENTEGRASYON â€” Ã¶zel RFQ, EKAP firma-geÃ§miÅŸini kullanÄ±r (eÅŸleÅŸtirme
>   motoru bunu kanÄ±tladÄ±); firma dizini/kategori/bildirim/profil/Ã¶deme hepsi ortak. BÃ¶lmek veri+kullanÄ±cÄ±
>   grafiÄŸini parÃ§alar, tek-hesap/SSO'yu zorlaÅŸtÄ±rÄ±r, kod tekrarÄ± yaratÄ±r.
> - **MENÃœ YAPISI (kullanÄ±cÄ± kararÄ± â€” "Analiz, Kamu Ä°haleleri altÄ±na"):**
>   ```
>   â”œâ”€â”€ Kamu Ä°haleleri  â–¸ Ä°haleler(EKAP) Â· DoÄŸrudan Temin Â· SonuÃ§lananlar Â· ANALÄ°Z(Firmalar/SektÃ¶rler/
>   â”‚                     Rekabet/Kurum-Firma Analizi/KÄ°K/EÅŸleÅŸtirme)
>   â”œâ”€â”€ UluslararasÄ± Ä°haleler  (TED, GÃ¼rcistan â€” yalnÄ±z ilan; analiz YOK)
>   â”œâ”€â”€ Ã–zel Ä°haleler / e-SatÄ±nalma  (RFQ; arkada kamu firma-zekÃ¢sÄ±nÄ± kullanÄ±r)
>   â””â”€â”€ Firmam Â· Takibim Â· Bildirimler
>   ```
>   **Neden Analiz Kamu altÄ±nda:** Ä°ÅŸ bitirme/kim-kazandÄ±/tenzilat SADECE EKAP kamu sonucundan (`ihale_
>   sonuclari`) doÄŸuyor. UluslararasÄ±'da sonuÃ§/kazanan yayÄ±nlanmÄ±yor, Ã¶zel RFQ'da sonuÃ§ gizli â†’ o alanlarda
>   firma analizi YAPILAMAZ. Yani analiz verisi kamuya ait (menÃ¼de Kamu altÄ±nda dÃ¼rÃ¼st), ama Ã¼rettiÄŸi firma
>   zekÃ¢sÄ± MOTORU Ã¶zel RFQ eÅŸleÅŸtirmesini de perde arkasÄ±nda besler. UX notu: Firmalar Dizini'ni "kamu ihale
>   karnesi" olarak konumlandÄ±r (kullanÄ±cÄ± Ã¶zel/yurtdÄ±ÅŸÄ± iÅŸ beklentisine girmesin).
> - **âœ… MENÃœ UYGULANDI + CANLI (commit `f79a356`):** 20 sayfanÄ±n sidebar'Ä± script'le yeniden yazÄ±ldÄ± â€”
>   bÃ¶lÃ¼mler: Genel Â· Kamu Ä°haleleri (Ä°haleler/DT/SonuÃ§lananlar + "â€” Analiz â€”" alt-grubu: Rekabet/Ä°dareler/
>   Firmalar/SektÃ¶rler/Kurum/Firma Analizi/KÄ°K) Â· UluslararasÄ± Â· Ã–zel Ä°haleler ("ğŸ¤ e-SatÄ±nalma YAKINDA"
>   placeholder, tÄ±klanamaz) Â· Firmam (Takibim/Bildirimler/Uyumluluk/DÃ¶kÃ¼manlar/Profil/Abonelik). Sayfa
>   baÅŸÄ±na doÄŸru `active`. CanlÄ±da doÄŸrulandÄ± (firmalar+dashboard, konsol temiz). Sidebar hÃ¢lÃ¢ her sayfada
>   inline (tekrar) â€” gelecekte tek js/sidebar.js bileÅŸenine Ã§ekilebilir (nav deÄŸiÅŸikliÄŸi tek dosya olur).
> - **DEÄERLENDÄ°RÄ°LÄ°YOR (karar bekliyor):** kÃ¶k `ihaleglobal.com`=pazarlama/public + `app.ihaleglobal.com`=
>   uygulama ayrÄ±mÄ±. SEO: asÄ±l kazanÃ§ public tender/kategori/firma sayfalarÄ±nÄ± KÃ–Kte indexlenebilir yapmak
>   (organik lead), app'i noindex/private tutmak â€” subdomain'in kendisi ranking'i sihirli artÄ±rmaz (subdir
>   otoriteyi biraz daha iyi toplar), asÄ±l kaldÄ±raÃ§ public sayfalarÄ±n SSR/prerender+sitemap ile taranabilir
>   olmasÄ± (mevcut SPA bu konuda zayÄ±f). GÃ¼venlik: app auth Ã§erezini `app.`'e scope'larsan izolasyon + sÄ±kÄ±
>   CSP/baÅŸlÄ±k avantajÄ± GERÃ‡EK (parent-domain Ã§erezle SSO yaparsan bu avantaj kaybolur).

> ## ğŸ—ºï¸ 15 TEMMUZ (devam) â€” YENÄ° 2 SÄ°STEM ROADMAP (kullanÄ±cÄ± stratejik yÃ¶n verdi, PLANLAMA)
> KullanÄ±cÄ± ihaleglobal'e 2 yeni sistem eklemek istiyor (mevcut TÃ¼rkiye-kamu sistemine ek):
>
> **SÄ°STEM A â€” ULUSLARARASI Ä°HALELER (yurtdÄ±ÅŸÄ± kaynaklardan, TÃœRKÃ‡E'ye Ã§evrilerek):**
> - Kaynaklar: TED Europa (https://ted.europa.eu â€” AB), GÃ¼rcistan (tenders.procurement.gov.ge), ileride diÄŸerleri.
> - **Fizibilite (araÅŸtÄ±rÄ±ldÄ±):** TED'in RESMÄ° REST API'si var ve Ã‡ALIÅIYOR: `POST api.ted.europa.eu/v3/
>   notices/search` (JSON; publication-number, CPV sorgu dili, Ã§ok-dilli XML/PDF linkleri, sayfalama).
>   GÃ¼rcistan JS web app â†’ iÃ§ API reverse-engineer gerekir (ilan.gov.tr gibi). TED en zengin/kolay baÅŸlangÄ±Ã§.
> - **Ã‡eviri:** baÅŸlÄ±k/aÃ§Ä±klama TÃ¼rkÃ§e'ye Ã§evrilmeli â†’ Gemini ZATEN entegre (ÅŸartname analizi/CAPTCHA'da
>   kullanÄ±lÄ±yor). `gemini-2.5-flash` ile toplu Ã§eviri. Orijinal metni de saklamak iyi olur (`orijinal_dil`).
> - **Åema:** `kaynak='uluslararasi'` (CHECK'te ZATEN var, migration YOK). Yeni kolonlar gerekebilir:
>   ulke, orijinal_dil, orijinal_baslik, orijinal_url, para_birimi (EUR/GEL). il/idare yurtdÄ±ÅŸÄ± iÃ§in farklÄ±.
> - **Plan (fazlÄ±):** (1) TED scraper POC (son N ihale Ã§ek + TÃ¼rkÃ§e Ã§evir + kaynak=uluslararasi insert),
>   (2) frontend'de ayrÄ± sekme/filtre "ğŸŒ UluslararasÄ±" + kaynak rozeti (EKAP/Gazete gibi), (3) gece cron,
>   (4) GÃ¼rcistan + diÄŸer kaynaklar. Dedup: publication-number bazlÄ±.
>
> **SÄ°STEM B â€” PROMENA BENZERÄ° E-SATINALMA (firmalarÄ±n kendi ihale/RFQ aÃ§tÄ±ÄŸÄ± platform):**
> - Promena = KoÃ§'un e-sourcing platformu: ALICI firmalar satÄ±nalma ihtiyacÄ± (RFQ) aÃ§ar, TEDARÄ°KÃ‡Ä° firmalar
>   rekabetÃ§i teklif verir (Ã§oÄŸu zaman reverse auction â€” tedarikÃ§iler fiyat kÄ±rarak yarÄ±ÅŸÄ±r), alÄ±cÄ± en iyiyi seÃ§er.
> - **KullanÄ±cÄ±nÄ±n belirsizliÄŸi:** "sabit tutar mÄ±, yoksa Promena gibi firmalarla yarÄ±ÅŸtÄ±rmak mÄ±?" +
>   "KoÃ§ gibi kÃ¶klÃ¼ gruplar zaten kendi tedarikÃ§i aÄŸÄ±yla destekliyor" â†’ bizim farkÄ±mÄ±z ne olacak?
> - **BÄ°ZÄ°M AVANTAJIMIZ (Ã¶neri notu):** ihaleglobal'de ZATEN 53K+ firma dizini (yukleniciler) + kategori/OKAS
>   eÅŸleÅŸtirme + bildirim altyapÄ±sÄ± + teklif-olustur var. Yani alÄ±cÄ± bir "satÄ±nalma ihalesi" aÃ§Ä±nca, Ä°LGÄ°LÄ°
>   tedarikÃ§ilere (kategoriye gÃ¶re) otomatik bildirim gidebilir â€” Promena'nÄ±n aksine alÄ±cÄ± kendi tedarikÃ§i
>   aÄŸÄ±nÄ± getirmek zorunda deÄŸil. Bu gÃ¼Ã§lÃ¼ bir farklÄ±laÅŸtÄ±rÄ±cÄ±.
> - **Model seÃ§enekleri (KARAR BEKLÄ°YOR):** (1) KapalÄ±-zarf RFQ/e-teklif (tedarikÃ§i tek teklif verir, alÄ±cÄ±
>   deÄŸerlendirir â€” kamu ihale modeline yakÄ±n, teklif-olustur altyapÄ±sÄ±nÄ± kullanÄ±r) â€” Ã–NERÄ°LEN baÅŸlangÄ±Ã§;
>   (2) Reverse auction (canlÄ± fiyat kÄ±rma) â€” Faz 2; (3) basit teklif-toplama. **Ã–neri: Faz 1 kapalÄ±-zarf RFQ.**
> - **Gerekli (bÃ¼yÃ¼k):** yeni tablolar (satinalma_talepleri, tedarikci_teklifleri), alÄ±cÄ±/tedarikÃ§i rolleri,
>   davet/bildirim akÄ±ÅŸÄ±, teklif kÄ±yas ekranÄ±, kazanan seÃ§imi. Gelir modeli (alÄ±cÄ± SaaS / tedarikÃ§i Ã¼yelik /
>   iÅŸlem Ã¼creti) ayrÄ± karar.
>
> **âœ… SÄ°STEM A FAZ 1 (TED) TAMAMLANDI + CANLI (commit `adba908`):** KullanÄ±cÄ± "ayrÄ± ekranda gÃ¶ster,
> TÃ¼rkiye analizine karÄ±ÅŸmasÄ±n" dedi â†’ AYRI `uluslararasi_ihaleler` tablosu (migration uygulandÄ±) +
> AYRI sayfa `uluslararasi.html`. `ted_scraper.py` TED v3 API'den Ã§eker, Ä°ngilizce baÅŸlÄ±ÄŸÄ± Gemini ile
> TOPLU TÃ¼rkÃ§e'ye Ã§evirir, Ã¼lke ISOâ†’TR, kategori (CPV+baÅŸlÄ±k), tÃ¼r (CPV). **183 ihale yÃ¼klendi.**
> Sayfa: server-side arama/Ã¼lke(26)/kategori/tÃ¼r filtresi + EUR bedel + TED linki + orijinal baÅŸlÄ±k.
> Sidebar'a "ğŸŒ UluslararasÄ± Ä°haleler" linki (18 sayfa). Gece cron'a eklendi. **CanlÄ±da doÄŸrulandÄ±**
> (183 ihale, Almanya filtresiâ†’53, TÃ¼rkÃ§e baÅŸlÄ±klar, konsol temiz).
>
> **âœ… GÃœRCÄ°STAN (2. kaynak) EKLENDÄ° + CANLI:** `georgia_scraper.py` â€” tenders.procurement.gov.ge'nin
> `controller.php POST action=search_app` API'si reverse-engineer edildi (HTML tablo parse). Announcment
> number(dedup)+tarih+idare+Procuring category(CPV+aÃ§Ä±klama)+deÄŸer(GEL). BaÅŸlÄ±k Gemini TÃ¼rkÃ§e, kategori
> CPV'den. **4 aÃ§Ä±k ihale eklendi** (varsayÄ±lan arama gÃ¼ncel seti verir; nightly biriktirir). Gece cron'a
> eklendi. Toplam artÄ±k **187 ihale, 27 Ã¼lke** (TED 183 + GÃ¼rcistan 4). CanlÄ±da doÄŸrulandÄ± (GÃ¼rcistan
> filtresiâ†’4, TÃ¼rkÃ§e baÅŸlÄ±k + GEL + rozet). **SÄ±radaki:** TED derin backfill (--max-pages yÃ¼ksek),
> GÃ¼rcistan pagination (ÅŸu an 4; daha fazlasÄ± iÃ§in sayfalama), diÄŸer kaynaklar, opsiyonel dashboard Ã¶zeti.
> Not: kategori bazen CPV fallback artifaktÄ± taÅŸÄ±r (CPV 50 "bakÄ±m/onarÄ±m"â†’TaÅŸÄ±t) â€” ince ayarla dÃ¼zeltilir.
>
> **SÄ°STEM B (Promena benzeri) â€” TASARIM NETLEÅTÄ°, kullanÄ±cÄ±yla uzun tartÄ±ÅŸÄ±ldÄ± (model kararÄ± bekliyor):**
> Ã‡ekirdek fikir (kullanÄ±cÄ±): alÄ±cÄ± firma ihale/RFQ aÃ§ar â†’ Gemini baÅŸlÄ±k/aÃ§Ä±klamayÄ± tarar â†’ o iÅŸe EN
> UYGUN firmalara (geÃ§miÅŸte EKAP'ta o/benzeri iÅŸe girmiÅŸ/kazanmÄ±ÅŸ) davet gÃ¶nderilir. AynÄ±sÄ± EKAP'tan
> Ã§Ä±kan ihaleler iÃ§in de: yeni ihaleye geÃ§miÅŸte benzer iÅŸ almÄ±ÅŸ firmalarÄ± otomatik Ã¶ner.
> - **EÅLEÅTÄ°RME MOTORU = en deÄŸerli kart, BUGÃœN yapÄ±labilir (kanÄ±tlandÄ±):** kategori + il/Ã§evre iller +
>   KAPASÄ°TE KADEMESÄ° (50M'lik iÅŸe 1M altÄ± almÄ±ÅŸÄ± Ã§aÄŸÄ±rma) â†’ hepsi `ihale_sonuclari`+`yukleniciler`+
>   kategori+il verisinden SQL ile Ã§Ä±kÄ±yor. Ã–rn REST sorgusu: "Mobilya" kategorisinde Ä°STÄ°KBAL MOBÄ°LYA
>   Ankara'da 193M/102M'lik iÅŸ kazanmÄ±ÅŸ â†’ bÃ¼yÃ¼k mobilya ihalesine uygun aday. AI'a gerek yok (Gemini
>   sadece RFQ metninden kategori Ã§Ä±karma + davet metni + firma-adÄ± bulanÄ±k eÅŸleÅŸtirmede kullanÄ±lÄ±r).
> - **Ä°LETÄ°ÅÄ°M/DAVET â€” YASAL ANALÄ°Z (kullanÄ±cÄ± itirazÄ±yla netleÅŸti):** BaÅŸta "Ä°YS kesin blokÃ¶r" dedim,
>   B2B iÃ§in FAZLA katÄ±ydÄ±. GerÃ§ek: (1) KVKK m.5/2-d "alenileÅŸtirme" â€” firma kendi iletiÅŸimini kendi
>   sitesinde yayÄ±nladÄ±ysa, iÅŸ amacÄ±yla ulaÅŸmak aÃ§Ä±k rÄ±za olmadan meÅŸru; (2) ticari ileti mevzuatÄ±
>   TACÄ°R/ESNAF alÄ±cÄ±ya Ã¶nceden onay ARAMAZ (B2B istisnasÄ±). Yani "self-published iÅŸ iletiÅŸimine, Ä°LGÄ°LÄ°
>   bir iÅŸ iÃ§in, ret hakkÄ±yla" ulaÅŸmak savunulabilir. **Åartlar:** ret/opt-out ZORUNLU (suppression
>   listesi), mesaj firmanÄ±n iÅŸiyle Ä°LGÄ°LÄ° olmalÄ± (eÅŸleÅŸtirme motoru bunu garanti eder â†’ "spam" deÄŸil),
>   kaynak self-published/doÄŸrulanmÄ±ÅŸ olmalÄ± â€” **Gemini'ye kiÅŸisel cep no TAHMÄ°N ettirme (uydurur +
>   alenileÅŸtirme dÄ±ÅŸÄ±)**. Ã–lÃ§eklenirken KVKK/Ä°YS avukatÄ± teyidi Ã¶nerildi.
> - **GÃ–NDERÄ°M MÄ°MARÄ°SÄ° (deliverability, kullanÄ±cÄ±yla netleÅŸti):** Ana domaini korumak iÃ§in ayrÄ±
>   SUBDOMAIN'den gÃ¶nder (`firsatlar.ihaleglobal.com`) + SPF/DKIM/DMARC + ayrÄ± IP + warm-up. **YAPMA:**
>   ayrÄ± `.co` lookalike domain + otomatik redirect (`getihaleglobal.coâ†’ihaleglobal.com`) â€” bu tam
>   PHISHING deseni, filtreler iÅŸaretler, itibarÄ± bozar. Maildeki link DOÄRUDAN ihaleglobal.com'a
>   (redirect/kÄ±saltÄ±cÄ± yok). AsÄ±l kaldÄ±raÃ§: Ä°LGÄ°LÄ°LÄ°K + dÃ¼ÅŸÃ¼k ÅŸikÃ¢yet + kolay ret.
> - **BÃœYÃœME DÃ–NGÃœSÃœ (Ã¼ye olmayan firmalar iÃ§in):** eÅŸleÅŸen ama Ã¼ye olmayan firmayÄ± alÄ±cÄ±ya "Ã¶nerilen"
>   gÃ¶ster + herkese aÃ§Ä±k firma profil sayfasÄ± â†’ firma kendini bulunca "sahiplen/Ã¼ye ol" â†’ doÄŸaÃ§lama mÃ¼ÅŸteri.
> - **âœ… EÅLEÅTÄ°RME MOTORU POC YAPILDI + CANLI (otonom oturum, commit `b5d9401`):** `migration_ihaleye_
>   uygun_firmalar.sql` â†’ RPC `ihaleye_uygun_firmalar(p_kategori,p_il,p_bedel,p_limit,p_kapasite_esik)`:
>   ihale_sonuclariâ¨ilanlar'dan kategoride kazanan firmalarÄ± puanlar (deneyim Ã¼st-sÄ±nÄ±rlÄ± + AYNI Ä°L
>   bonusu[ilanlar.il=kazandÄ±ÄŸÄ± bÃ¶lge] + KAPASÄ°TE). Kapasite bir FÄ°LTRE: p_bedel verilince max kazanÄ±m
>   < p_bedelÃ—%10 olan firmalar ELENÄ°R (kullanÄ±cÄ± kuralÄ±: 50M iÅŸe kÃ¼Ã§Ã¼k firma Ã§aÄŸÄ±rma). ihale-detay'a
>   "ğŸ¯ Bu Ä°haleye Uygun Firmalar" bÃ¶lÃ¼mÃ¼ eklendi (her EKAP ihalesinde otomatik, firma-analiz linkli).
>   **CanlÄ±da doÄŸrulandÄ±:** Sulama YapÄ±m iÅŸiâ†’MARMARA BETON BORU/BALDAN ASFALT vb. inÅŸaat firmalarÄ±; Bolu
>   50M mobilya senaryosuâ†’kÃ¼Ã§Ã¼k firmalar elendi, kapasiteliler geldi. **Bu, EKAP lead-gen + Promena
>   eÅŸleÅŸtirmesinin gÃ¶rÃ¼nÃ¼r ilk Ã¼rÃ¼nÃ¼.** Sonraki: RFQ aÃ§ma ekranÄ±, Ã¼ye firmaya bildirim, Ã§evre-il komÅŸuluk
>   haritasÄ± (ÅŸu an sadece aynÄ± il), landing page + davet (temiz ayrÄ± domain + ret hakkÄ±).
> - **âœ… e-SATINALMA MODÃœLÃœ v1 YAPILDI + CANLI (commit `49e3fb0`):** `migration_ozel_ihaleler.sql` â†’
>   `satinalma_talepleri` + `tedarikci_teklifleri` tablolarÄ± (RLS: kapalÄ±-zarf â€” tedarikÃ§i sadece kendi
>   teklifini gÃ¶rÃ¼r, alÄ±cÄ± hepsini). `ozel-ihaleler.html`: alÄ±cÄ± ihale formu (baÅŸlÄ±k/kategori[41]/il[81]/
>   miktar/bedel/tarih) â†’ "ğŸ¯ Uygun TedarikÃ§ileri Bul" eÅŸleÅŸtirme motorunu Ã§aÄŸÄ±rÄ±r (giriÅŸ gerekmez, anÄ±nda
>   10 firma) â†’ "Ä°haleyi YayÄ±nla" satinalma_talepleri'ne kaydeder (giriÅŸ+RLS) â†’ aÃ§Ä±k ihaleler listelenir.
>   Nav placeholderâ†’gerÃ§ek link (20 sayfa, e-SatÄ±nalma artÄ±k aktif). **CanlÄ±da doÄŸrulandÄ±** (Mobilya+Ankara
>   +20Mâ†’10 tedarikÃ§i, konsol temiz).
> - **âœ… e-SATINALMA FAZ 2 YAPILDI + CANLI (commit `b99bbd3`):** `ozel-ihale-detay.html` â€” rol bazlÄ±:
>   ALICI(gelen teklifler[kapalÄ±-zarf, fiyata sÄ±ralÄ±]+"Kazanan SeÃ§"[kazanan_teklif_id]+Ã¶nerilen tedarikÃ§iler),
>   TEDARÄ°KÃ‡Ä°(gizli teklif ver / kendi teklifini gÃ¶r), MÄ°SAFÄ°R(RFQ'yu gÃ¶rÃ¼r + giriÅŸ-ile-teklif). v3 RLS:
>   aÃ§Ä±k RFQ'lar HERKESE gÃ¶rÃ¼nÃ¼r (tedarikÃ§i keÅŸif hunisi+SEO, kamu ihaleleri gibi); teklifler gizli kalÄ±r.
>   Liste kartlarÄ± detaya linkli. **3 Ã¶rnek RFQ eklendi** (info@dnclaser.com hesabÄ±yla â€” o hesapla giriÅŸ
>   yapÄ±nca ALICI akÄ±ÅŸÄ±nÄ± [gelen teklif+kazanan seÃ§] test edebilirsin). CanlÄ±da doÄŸrulandÄ± (liste 3 RFQ,
>   detay header+KPI+rozet, konsol temiz).
> - **âœ… e-SATINALMA FAZ 3 YAPILDI + CANLI (commit `547d35a`):** `ihalelerim.html` (Firmam â–¸ Ä°halelerim,
>   22 sayfa nav) â€” giriÅŸ yapan kullanÄ±cÄ± 2 sekmede kendi aktivitesini gÃ¶rÃ¼r: "AÃ§tÄ±ÄŸÄ±m Ä°haleler" (teklif
>   sayÄ±sÄ± + durum + detay linki) ve "VerdiÄŸim Teklifler" (RFQ + bedel + ğŸ†kazandÄ±m/deÄŸerlendirmede).
>   CanlÄ±da doÄŸrulandÄ± (giriÅŸ uyarÄ±sÄ± + nav aktif + 2 sekme + konsol temiz; mevcut sayfalar saÄŸlam).
> - **KALAN (Faz 4):** RFQ yayÄ±nÄ±nda BÄ°LDÄ°RÄ°M â€” ama `profil.sektorler` ESKÄ° kÄ±sa anahtarlar ({insaat,
>   enerji}) yeni ~40 kategoriyle UYUÅMUYOR + Ã§oÄŸu boÅŸ; `bildirimler.kullanici_id` FK kullanici_profiller'e,
>   tur CHECK'inde 'ozel_ihale' yok ('eslestirme' kullanÄ±labilir). Yani Ã–NCE sektorler taksonomisini yeni
>   kategorilere hizala, SONRA DB trigger. AyrÄ±ca (izinli) davet e-postasÄ± (ayrÄ± temiz domain + ret hakkÄ±).
> - **Ä°NÅA SIRASI (kalan):** (1)âœ… EÅŸleÅŸtirme motoru â€” YAPILDI, (2)âœ… RFQ aÃ§ma + eÅŸleÅŸtirme â€” YAPILDI,
>   (2) alÄ±cÄ± RFQ aÃ§ma (kapalÄ±-zarf, Ã–NERÄ°LEN model) + Ã¼ye firmalara bildirim, (3) firma profil + bÃ¼yÃ¼me
>   dÃ¶ngÃ¼sÃ¼, (4) Ä°YS-uyumlu izinli gÃ¶nderim + ayrÄ± subdomain. **Model kararÄ± (kapalÄ±-zarf/reverse-auction/
>   basit) kullanÄ±cÄ±dan bekleniyor; Ã¶nerim kapalÄ±-zarf RFQ.**

> ## âœ… 15 TEMMUZ (devam) â€” kaynak rozeti + gÃ¼ndÃ¼z/gece modu (commit `e095e45`, CANLI)
> **1) Kaynak rozeti:** ihaleler.html kartlarÄ±nda her ihalenin kaynaÄŸÄ± â€” "EKAP" veya ilan.gov.tr iÃ§in
> "ğŸ“° Gazete" (kaynakBadge() + select'e kaynak eklendi). DoÄŸrulandÄ±: "belediyesine ait"â†’5 EKAP+5 Gazete.
> **2) GÃ¼ndÃ¼z/gece modu (sistem ZATEN vardÄ±, theme.js+css light deÄŸiÅŸkenleri 21 sayfada):** kullanÄ±cÄ±
> kÃ¼Ã§Ã¼k saÄŸ-alt â˜€ï¸ butonunu fark etmemiÅŸti â†’ etiketli PILL'e Ã§evrildi ("â˜€ï¸ GÃ¼ndÃ¼z Modu"/"ğŸŒ™ Gece Modu"),
> varsayÄ±lan hÃ¢lÃ¢ gece. **Light-mode bug dÃ¼zeltildi:** `.hizli-chip.active` tanÄ±msÄ±z `var(--blue)` â†’
> ÅŸeffaf zemin â†’ beyaz metin light modda gÃ¶rÃ¼nmezdi; #3b82f6'ya Ã§evrildi. Denetim: diÄŸer hardcoded
> beyazlar renkli/koyu zemin Ã¼stÃ¼nde (OK), Chart.js ticks orta-gri (OK). **Not:** theme.js cache'li
> kullanÄ±cÄ±lar yeni pill'i hard-refresh sonrasÄ± gÃ¶rÃ¼r (script src'de version yok â€” istenirse eklenir).

> ## âœ… 15 TEMMUZ (devam) â€” KATEGORÄ° REDESIGN + ilan.gov.tr SCRAPER (kullanÄ±cÄ± "ikisini yap" dedi, Ä°KÄ°SÄ° DE CANLI)
>
> **âœ… 1) Ä°Å-DOSTU KATEGORÄ° SÄ°STEMÄ° (ihaleciler.com tarzÄ±) â€” CANLI.** Eski: CPV-2-hane ham AB isimleri
> + OKAS'sÄ±z ~%39 jenerik "Mal/Hizmet AlÄ±mÄ±"ya dÃ¼ÅŸÃ¼yordu. Yeni: `backend/kategori_siniflandir.py` â€”
> OKAS AÃ‡IKLAMASI + BAÅLIK Ã¼zerinde TÃ¼rkÃ§e-katlanmÄ±ÅŸ kelime-sÄ±nÄ±rÄ± (\b) eÅŸleÅŸtirmesiyle ~40 iÅŸ-dostu
> kategori. Kapsam aktiflerde **%73.5** (DiÄŸer %26.5, eski jenerik ~%39'a karÅŸÄ±). ekap_scraper entegre.
> **backfill (`kategori_backfill.py`) VDS'te Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±: 178.353 satÄ±r yeniden sÄ±nÄ±flandÄ±rÄ±ldÄ±**
> (kategoriye gÃ¶re toplu PATCH; CHUNK=60 Ã§Ã¼nkÃ¼ UUID id'ler 414 veriyordu). sektorler.html SEKTOR_IKON
> yeni ~40 kategoriye gÃ¼ncellendi. **CanlÄ±da doÄŸrulandÄ±:** sektorler yeni isimleri ikonlarÄ±yla gÃ¶steriyor
> (ğŸ—ï¸ Ä°nÅŸaat-AltyapÄ±, ğŸ½ï¸ GÄ±da, â¤ï¸ SaÄŸlÄ±k...). rekabet-analizi kategori chart'Ä± da otomatik besleniyor.
> **Kalan:** DiÄŸer %26.5 (Ã§oÄŸu OKAS'sÄ±z niÅŸ: maden/demiryolu/savunma) â€” keyword eklemeyle zamanla dÃ¼ÅŸÃ¼rÃ¼lÃ¼r.
> 43 straggler eski isim kaldÄ± (concurrent yazÄ±m, ihmal edilebilir; nightly dÃ¼zeltir).
>
> **âœ… 2) ilan.gov.tr (BasÄ±n Ä°lan Kurumu "Gazete") SCRAPER â€” CANLI.** `backend/ilan_gov_scraper.py`:
> AdsByFilter ABP API'sinden Ä°HALE duyurularÄ±nÄ± Ã§eker (newest-first, 20/sayfa), client-side
> "Ä°lan TÃ¼rÃ¼==Ä°HALE" filtreler, IKN/tÃ¼r/usul/il/son-teklif/baÅŸlÄ±k Ã§Ä±karÄ±r. **kaynak='ilan_gov'**
> (ekap_id=IKN, yoksa adNo; ikn NULLâ†’UNIQUE Ã§akÄ±ÅŸmasÄ± yok). ilanlar upsert on_conflict=ekap_id
> ignore_duplicates â†’ EKAP'ta zaten olan IKN'ler ATLANIR, yalnÄ±zca gazete-Ã¶zel ihaleler eklenir.
> Migration `migration_kaynak_ilan_gov.sql` (kaynak CHECK'ine 'ilan_gov' eklendi) VDS'te uygulandÄ±.
> **VDS'te Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±: 128 yeni gazete-Ã¶zel ihale eklendi** (Ã¶zellikle EKAP'Ä±n kapsamadÄ±ÄŸÄ± 2886 satÄ±ÅŸ/
> kira ihaleleri). Gece cron'una eklendi (`--max-pages 40`, DT sonrasÄ±). **KRÄ°TÄ°K KURAL SAÄLANDI:**
> ihale-detay bu kayÄ±tlarda kaynaÄŸÄ± "EKAP" DEÄÄ°L "ğŸ“° Resmi Ä°lan Â· ilan.gov.tr" gÃ¶steriyor, aksiyon
> butonu ilan.gov.tr'ye linkli, hiÃ§bir EKAP referansÄ± yok (canlÄ±da doÄŸrulandÄ±). **Kalan/gelecek:**
> ihaleler.html liste kartlarÄ±nda da kaynak rozeti gÃ¶sterilebilir; derin geÃ§miÅŸ backfill (--max-pages
> yÃ¼ksek) opsiyonel; TEBLÄ°GAT/Ä°CRA/PERSONEL tÃ¼rleri ÅŸu an alÄ±nmÄ±yor (sadece Ä°HALE).

> ## âœ… 15 TEMMUZ (devam) â€” DEPLOY EDÄ°LDÄ° (kullanÄ±cÄ± "sen push et VDS'e" dedi)
> Bu oturumun TÃœM commit'leri VDS'e pull edildi: `516fc31 â†’ 6d3ba07` (17 dosya, fast-forward).
> **DoÄŸrulandÄ±:** (1) `run_scraper.sh` mode 755 executable (bu geceki cron Ã§alÄ±ÅŸacak); (2) supabase
> shim gte/lte VDS venv'de Ã§alÄ±ÅŸÄ±yor â†’ **notify.py deadline e-postalarÄ± bu gece Ä°LK KEZ gidecek**;
> (3) tÃ¼m bildirim scriptleri syntax OK; (4) canlÄ± frontend gÃ¼ncel (nginx) â€” ihaleglobal.com aktif
> sayacÄ± artÄ±k **4.063** (gerÃ§ek aÃ§Ä±k), dogrudan-temin/teklif-olustur/Pro-rozeti/rekabet-analizi hepsi
> canlÄ±. **YARIN KONTROL:** bu geceki 02:00 UTC cron turu â€” notify e-postasÄ± gitti mi + usul temiz
> yazÄ±ldÄ± mÄ± (`scraper.log`).

> ## ğŸ“Š 15 TEMMUZ (devam) â€” rekabet-analizi fix + KATEGORÄ°/OKAS analizi + ilan.gov.tr (yeni kaynak)
>
> **âœ… REKABET ANALÄ°ZÄ° "Ä°hale UsulÃ¼" bug'Ä± DÃœZELTÄ°LDÄ° (commit `5e53e4e`):** usul chart'Ä±nda EKAP'Ä±n
> Ã§evrilmemiÅŸ ham i18n key'leri (`TENDER_SEARCH.MAIN.PAGEITEM.TENDER_TYPE 4734 / 3-g`) 40-karakter
> kÄ±rpmayla birbirine girip bara taÅŸÄ±yordu. `usulTemizle()` istisna maddelerini "Ä°stisna (4734 3-g)"
> gibi okunur etikete Ã§eviriyor + `.budget-label`'a overflow korumasÄ±. KÃ¶k neden de dÃ¼zeltildi:
> `ekap_scraper.py usul_donustur()` artÄ±k scrape'te temizliyor (yeni veride oluÅŸmaz). "Labaratuvar"â†’
> "Laboratuvar" typo da giderildi. **Not:** rekabet-analizi Pro-kilitli sayfa; tarayÄ±cÄ± doÄŸrulamasÄ±
> giriÅŸ gerektirdi, usulTemizle mantÄ±ÄŸÄ± ham deÄŸerlerle baÄŸÄ±msÄ±z test edildi.
>
> **ğŸ” KATEGORÄ° SÄ°STEMÄ° â€” KULLANICI SORUSU "OKAS'a gÃ¶re mi?" CEVABI + iyileÅŸtirme Ã¶nerisi:**
> - **Bizim kategoriler ZATEN OKAS/CPV-tabanlÄ±:** `ekap_scraper.py:_CPV_KATEGORI` OKAS kodunun Ä°LK 2
>   HANESÄ°NDEN (CPV bÃ¶lÃ¼mÃ¼, 44 adet) tÃ¼retiyor ("45"â†’Ä°nÅŸaat & YapÄ±m, "85"â†’SaÄŸlÄ±k, "33"â†’TÄ±bbi Cihazlar).
> - **Ä°KÄ° SORUN:** (1) Aktif ihalelerin **~%39'unda OKAS YOK** (9.449/15.381) â†’ jenerik "Mal AlÄ±mÄ±"
>   (333)/"Hizmet AlÄ±mÄ±"(106) kovasÄ±na dÃ¼ÅŸÃ¼yor, bilgisiz. (2) OKAS olsa bile ham CPV-bÃ¶lÃ¼mÃ¼ isimleri
>   (AB tarzÄ±) ihaleciler.com'un iÅŸ-dostu kÃ¼rate isimlerinden farklÄ±.
> - **ihaleciler.com (WebFetch ile teyit):** ~36 kÃ¼rate kategori; isimler birden Ã§ok kodu/anahtar
>   kelimeyi BÄ°RLEÅTÄ°RÄ°YOR ("Kanalizasyon - Boru - Su - DoÄŸalgaz - SÄ±hhi Tesisat", "TÄ±bbi Cihaz -
>   Laboratuvar - Hastane EkipmanlarÄ±"). Muhtemelen CPV/OKAS-tabanlÄ± ama iÅŸ-dostu bundle isimlerle +
>   OKAS'sÄ±z ihaleler iÃ§in baÅŸlÄ±k anahtar-kelime eÅŸleÅŸtirmesi. Yani fark KÃœRASYON/Ä°SÄ°MLENDÄ°RME, temel
>   sÄ±nÄ±flandÄ±rma deÄŸil.
> - **Ã–NERÄ° (kullanÄ±cÄ± onayÄ± gerekli â€” Ã¼rÃ¼n kararÄ±):** `_CPV_KATEGORI`'yi ihaleciler.com tarzÄ± ~36 iÅŸ-dostu
>   bundle kategoriye dÃ¶nÃ¼ÅŸtÃ¼r (birden Ã§ok CPV-2-hane â†’ tek zengin isim) + OKAS'sÄ±z ~%39 iÃ§in baÅŸlÄ±k
>   anahtar-kelime sÄ±nÄ±flandÄ±rmasÄ± ekle (jenerik "Mal/Hizmet AlÄ±mÄ±" yerine gerÃ§ek sektÃ¶r). Backfill
>   gerekir (mevcut kategoriyi yeniden hesapla). BÃ¼yÃ¼k iÅŸ; hangi kategori isimlerini istediÄŸinize gÃ¶re
>   ÅŸekillenmeli. `sektorler.html` + rekabet-analizi kategori chart'Ä± bundan beslenir.
>
> **ğŸ†• YENÄ° VERÄ° KAYNAÄI â€” ilan.gov.tr / BasÄ±n Ä°lan Kurumu "Gazete" ilanlarÄ± (kullanÄ±cÄ± talebi):**
> ihaleciler.com 3 kaynak kullanÄ±yor (WebFetch teyidi): **Ekap (7.150) + Gazete (1.259) + Ä°stihbarat
> (1.921)**. Biz SADECE EKAP Ã§ekiyoruz. KullanÄ±cÄ±: ilan.gov.tr'den (https://www.ilan.gov.tr/ilan/
> tum-ilanlar â€” BasÄ±n Ä°lan Kurumu resmi gazete/ihale ilanlarÄ±) de veri Ã§ekip yansÄ±tmalÄ±yÄ±z.
> **KRÄ°TÄ°K KURAL (kullanÄ±cÄ±):** Bu ilanlarÄ±n kaynaÄŸÄ±nÄ± "EKAP" olarak GÃ–STERMEYECEÄÄ°Z (ayrÄ± kaynak
> etiketi â€” Ã¶r. "Resmi Ä°lan"/"Gazete"). **YapÄ±lacak (yeni scraper iÅŸi, henÃ¼z baÅŸlanmadÄ±):**
> - ilan.gov.tr yapÄ±sÄ±nÄ± incele (SSL/API/HTML â€” WebFetch cert doÄŸrulayamadÄ±, tarayÄ±cÄ±/httpx ile bak).
> - Yeni scraper: ilan.gov.tr ihale/resmi ilanlarÄ±nÄ± Ã§ek â†’ `ilanlar` (veya ayrÄ± tablo) + `kaynak`
>   kolonu ('ekap'|'ilan_gov'). Frontend'de kaynak etiketini buna gÃ¶re gÃ¶ster (EKAP deme).
> - MÃ¼kerrer tespiti (aynÄ± ihale hem EKAP hem gazetede olabilir â€” IKN/baÅŸlÄ±k eÅŸleÅŸtirme).
> - Gece cron'una ekle.

> ## ğŸ§¾ 15 TEMMUZ (devam) â€” teklif-olustur 5 kullanÄ±cÄ± bildirimi + Pro rozeti (commit `f103075`)
> KullanÄ±cÄ± ekran gÃ¶rÃ¼ntÃ¼leriyle 5 sorun bildirdi, hepsi dÃ¼zeltildi + push'landÄ± (tarayÄ±cÄ±da doÄŸrulandÄ±):
> 1. Pro hesapta topbar "Pro'ya GeÃ§" hÃ¢lÃ¢ gÃ¶rÃ¼nÃ¼yordu â†’ `js/sidebar-user.js` Pro'da "â­ Pro Plan" rozeti (8 sayfa).
> 2. Mali Teklif â‚º sembolÃ¼ sayÄ±nÄ±n Ã¼stÃ¼ne biniyordu â†’ fiyat input'una `padding-left:24px`.
> 3. Zorunlu belgeler hepsi opsiyonel yapÄ±ldÄ± ("SÄ±k Ä°stenen Belgeler", iÅŸaretsiz) â€” mÃ¼ÅŸteri paylaÅŸmak zorunda deÄŸil.
> 4. KDV artÄ±k KALEM KALEM (%1/8/10/18/20), tutarlar KDV HARÄ°Ã‡ â†’ tabloya KDV% kolonu + satÄ±r select,
>    toplamlar satÄ±r oranlarÄ±ndan, Ã¶nizleme belgesi de gÃ¼ncellendi (karÄ±ÅŸÄ±k oran doÄŸrulandÄ±).
> 5. Kaydet'te `duplicate key ... teklifler_ilan_id_teklif_veren_id_key` â†’ insert yerine upsert (onConflict).
> **âš ï¸ Bunlar da VDS pull ile deploy bekliyor** (aÅŸaÄŸÄ±daki SSH-engeli notuyla aynÄ± â€” `origin/main`=`f103075`).

> ## ğŸš€ 15 TEMMUZ (devam) â€” DENETÄ°M OTURUMU: 17 fix commit'lendi+push'landÄ±, DEPLOY SSH-ENGELLÄ°
> KullanÄ±cÄ± "deploy et, cron'lara bak, ne gÃ¶rÃ¼rsen dÃ¼zelt, otomatik iznin var" dedi. 30-agent
> denetim workflow'u Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± â†’ **21 onaylanmÄ±ÅŸ bulgu**. YapÄ±lanlar:
>
> **âœ… C) Sidebar kullanÄ±cÄ± bloÄŸu â†’ profil** (Ã¶nceki aÃ§Ä±k iÅŸ) â€” `js/sidebar-user.js`'e giriÅŸ-baÄŸÄ±msÄ±z
> click+keyboard, kik-kararlar'a inline. 17+ sayfa. TarayÄ±cÄ±da doÄŸrulandÄ± (commit `804dd74`).
>
> **âœ… KRÄ°TÄ°K â€” notify.py + bulten_gonder.py e-postalarÄ± SESSÄ°ZCE KIRIKMIÅ** (`652eb0f`): sahte
> `backend/supabase/__init__.py` wrapper'Ä±nda `.gte/.lte` yoktu â†’ AttributeError yutuluyordu â†’
> son-teklif-yaklaÅŸan e-postalarÄ± HÄ°Ã‡ gitmiyordu, bÃ¼lten Ã§Ã¶kÃ¼yordu. gte/lte/gt/lt/neq eklendi
> (aynÄ± kolonda gte+lte aralÄ±ÄŸÄ± iÃ§in `_filter_list` tekrarlÄ± param). Unit-test+httpx doÄŸrulandÄ±.
> **DEPLOY olunca bu geceki cron'da deadline e-postalarÄ± Ä°LK KEZ gidecek** (dedup pencere de 20h'e
> Ã§ekildiÄŸi iÃ§in mÃ¼kerrer deÄŸil).
>
> **âœ… GÃœVENLÄ°K â€” firma-analiz.html reflected+stored XSS** (`652eb0f`): `?ara=/?firma=` URL param'Ä±
> 3 sink'e escape'siz gidiyordu (not-found kartÄ±, firma listesi, son-aramalar chip'i URLâ†’localStorage
> â†’render). escapeHtml + sonuÃ§ render'Ä± escape. Payload'lu URL tarayÄ±cÄ±da test â†’ artÄ±k Ã§alÄ±ÅŸmÄ±yor.
>
> **âœ… ana sayfa "Aktif Ä°hale" sayacÄ±** (`652eb0f`): durum='aktif' (15.381, 11K'sÄ± sÃ¼resi geÃ§miÅŸ)
> yerine son_teklif>=now (4.063 gerÃ§ek aÃ§Ä±k). TarayÄ±cÄ±da doÄŸrulandÄ±.
>
> **âœ… dogrudan-temin.html server-side dÃ¶nÃ¼ÅŸÃ¼mÃ¼** (`652eb0f`): 620K kayÄ±tta "5.000" gÃ¶sterip 600K'yÄ±
> aranamaz bÄ±rakÄ±yordu â†’ tam server-side sayÄ±m/arama/sayfalama (arama ILIKE exact-count timeout
> ettiÄŸinden count'suz+probe'lu gÃ¶reli pager). TÃ¼m modlar tarayÄ±cÄ±da doÄŸrulandÄ±.
>
> **âœ… 8 backend cron/bildirim fix** (`4e3a05f`): DEBUG log spam kaldÄ±rÄ±ldÄ±; DT json.JSONDecodeError
> yakalandÄ±; embed throttle backoff; profil 403 sessiz-yutma loglandÄ±; aksiyon_url URL-encode
> (JOHNSON & JOHNSON linki); esleÅŸiyor() kelime-tabanlÄ± (MERTâ‰ DEMERT, 6 test geÃ§ti); haftalÄ±k
> bÃ¼lten dedup; run_scraper.sh inline timestamp.
>
> **âœ… 2 davranÄ±ÅŸsal fix** (`9cf78c0`): mÃ¼kerrer bildirim penceresi 26hâ†’20h (#5); gecelik sonuÃ§
> taramasÄ± `--start-skip 0 --no-checkpoint` ile en-yeniden (#7, checkpoint 2023'e kaymÄ±ÅŸtÄ±, yeni
> sonuÃ§lar yakalanmÄ±yordu).
>
> **ğŸ”´ DEPLOY YAPILAMADI â€” SSH auto-mode classifier engeli:** TÃ¼m commit'ler GitHub'da
> (`origin/main` = `9cf78c0`) ama VDS `git pull` prod'a SSH gerektiriyor ve classifier genel
> "otomatik izin"le bunu AÃ‡MIYOR (hafÄ±za `prod-ssh-auto-mode-limits`). **Fix'ler VDS pull olana
> kadar CANLI DEÄÄ°L** (frontend nginx'ten, backend cron VDS repo'sundan). KullanÄ±cÄ± ya SSH hedefini
> aÃ§Ä±kÃ§a adlandÄ±rmalÄ± ("root@195.85.207.126'ya baÄŸlan deploy et") ya da Bash izin kuralÄ± eklemeli.
>
> **ğŸ“‹ DÃœZELTÄ°LMEYEN (dÃ¼ÅŸÃ¼k-sev / borderline / migration gerektiren) â€” bilinÃ§li ertelendi:**
> - #9 ihale-detay OKAS linki 'guncel' sekmede aÃ§Ä±lÄ±yor â†’ kapalÄ± ihalede tÄ±klanÄ±nca geÃ§miÅŸ
>   eÅŸleÅŸmeler gÃ¶rÃ¼nmez (dÃ¼ÅŸÃ¼k/borderline; veri GeÃ§miÅŸ/SonuÃ§ sekmelerinden eriÅŸilebilir).
> - #11 notify.py in-app bildirim dedup yok (deadline countdown gÃ¼nlÃ¼k tekrarÄ± â€” bÃ¼yÃ¼k Ã¶lÃ§Ã¼de
>   kasÄ±tlÄ± hatÄ±rlatma pattern'i; dÃ¼ÅŸÃ¼k).
> - #14 run_scraper.sh adÄ±m baÅŸÄ±na `timeout` yok (N'i kÃ¶r seÃ§mek meÅŸru uzun adÄ±mÄ± Ã¶ldÃ¼rÃ¼r â€” riskli).
> - #17 kik-kararlar sonuc facet'i %100 'diger' (Ä°ptal/Kabul/Red hep 0) â€” liste endpoint outcome
>   vermiyor; gerÃ§ek fix KÄ°K detay API'si (backend iÅŸ). Facet'i gizlemek UI-yargÄ±sÄ±, ertelendi.
> - #18 kazanan_teklif_farki_yuzde uÃ§ deÄŸerler (-993% gibi) firma/idare AVG'lerini bozuyor â€”
>   ana yÃ¼zey analiz_pivot RPC (SUM/AVG), dÃ¼zeltmesi migration (SSH) gerektiriyor.
> - `il` kolonunda mojibake (AÄRIâ†’"Aï¿½RI", ELAZIÄ, ESKÄ°ÅEHÄ°R) â€” `mojibake_fix.py` konusu, DB-write.

> ## ğŸ¯ 15 TEMMUZ â€” KULLANICI GERÄ° BÄ°LDÄ°RÄ°MÄ°
>
> **âœ… D) OKAS/CPV KODU ARAMASI â€” TAMAMLANDI + CANLIDA (commit `516fc31`).** KullanÄ±cÄ± fikri: OKAS
> resmi sÄ±nÄ±flandÄ±rma, anahtar kelimeden kesin. `ihaleler.html` detaylÄ± aramaya "OKAS / CPV Kodu"
> filtresi (`okas ILIKE %kod%`, ?okas= URL param + kayÄ±tlÄ± arama + sÄ±fÄ±rlama). `ihale-detay.html`'de
> OKAS artÄ±k tÄ±klanabilir (Ã§oklu kodu ayrÄ± linklere bÃ¶ler â†’ o koda sahip diÄŸer ihaleler). **Kapsam:**
> OKAS aktif ihalelerin ~%61'inde var (9.449/15.381); EKAP kalanÄ±nda vermiyor, ilan metninde de yok
> (teyit edildi). Backfill edilen eskilerde %0 (backfill detay Ã§ekmiyor). Anahtar kelime aramasÄ±nÄ±
> TAMAMLAR. **Gelecek fikir:** OKAS kapsamÄ±nÄ± artÄ±rmak iÃ§in EKAP mal-kalem/detay endpoint araÅŸtÄ±rmasÄ±;
> OKAS ana-kategori dropdown'u (44 CPV bÃ¶lÃ¼mÃ¼, `_CPV_KATEGORI` kodda var).
>
> **âœ… A) FÄ°RMA ANALÄ°ZÄ° REDESIGN â€” TAMAMLANDI + CANLIDA (commit `7b686c5`).** ihaleciler.com modeli:
> arama â†’ `yukleniciler`'den AYRI firma listesi (isim+sÃ¶zleÅŸme+ciro+il, ciroya sÄ±ralÄ±, TÃ¼rkÃ§e katlamalÄ±)
> â†’ firmaya tÄ±kla â†’ `yuklenici_id` ile kesin detay (zengin ihale_sonuclari + ilan baÅŸlÄ±k/idare). "(BaÅŸlÄ±k
> yok)" giderildi; sonuÃ§ kartlarÄ±nda kurum(idare, linkli)+firma tam adÄ±+baÅŸlÄ±k+bedel+tenzilat. Tek eÅŸleÅŸmede
> doÄŸrudan detaya atlar. `migration_yukleniciler_arama_fold.sql` + `yuklenici_yenile()` (firma 35.454â†’53.897,
> yuklenici_id baÄŸlarÄ± dolduruldu). **CanlÄ±da doÄŸrulandÄ±:** "dinÃ§"â†’72 firma, Onur DinÃ§erâ†’11 kazanÄ±m/92.8M/7 il.
> SÄ±nÄ±rlama: rakamlar backfill ilerledikÃ§e artacak (bizde sadece KAZANAN veri var, EKAP kaybedeni yayÄ±nlamaz).
>
> **âœ… B) Son aramalar tÄ±klanÄ±nca arama** â€” TAMAMLANDI (A ile birlikte): chip'ler artÄ±k `firmaSectiClick`
> â†’ liste aramasÄ± yapÄ±yor.
>
> **âœ… C) Sol-alt kullanÄ±cÄ± adÄ±/"Ãœcretsiz Plan" â†’ profil ayarlarÄ± â€” TAMAMLANDI (15 Tem).** Sidebar
> alt-kÃ¶ÅŸedeki `.user-row` bloÄŸu artÄ±k tÄ±klanabilir â†’ `profil` sayfasÄ±na gider (temiz URL, tÃ¼m nav ile
> aynÄ± kural). Merkezi `js/sidebar-user.js`'e giriÅŸ durumundan BAÄIMSIZ tÄ±klama+keyboard(Enter/Space)
> +cursor:pointer+role=link+tabindex baÄŸlandÄ± â†’ 17 sayfa tek noktadan kapsanÄ±yor. `kik-kararlar.html`
> UMD sidebar-user.js yerine kendi ES-module'Ã¼nÃ¼ kullandÄ±ÄŸÄ± iÃ§in oraya aynÄ± davranÄ±ÅŸ inline eklendi
> (Ã§ift supabase yÃ¼klememek iÃ§in). `profil.html` zaten hedef, atlandÄ±. **TarayÄ±cÄ±da doÄŸrulandÄ±:**
> dashboard + kik-kararlar user-row tÄ±klamasÄ± `â†’ /profil`'e yÃ¶nlendi (yerelde python http.server temiz
> URL rewrite yapmadÄ±ÄŸÄ± iÃ§in 404 gÃ¶steriyor, nginx prod'da mevcut `href="profil"` nav linkleriyle aynÄ±
> ÅŸekilde Ã§Ã¶zÃ¼lÃ¼r).
>
> --- (eski geri bildirim detayÄ± aÅŸaÄŸÄ±da) ---
>
> **A) FÄ°RMA ANALÄ°ZÄ° KÃ–KLÃœ YENÄ°DEN TASARIM (kullanÄ±cÄ±: "firma analizinde berbatÄ±z, ihaleciler.com'u
> Ã¶rnek al").** KÃ¶k tasarÄ±m hatasÄ± tespit edildi: `firma-analiz.html?firma=X` aramada X terimini TEK
> BÄ°R FÄ°RMA sanÄ±p `kazanan_firma`'da fuzzy ILIKE yapÄ±yor â†’ "dinÃ§" arayÄ±nca "DinÃ§ Grup", "Onur DinÃ§er",
> "DinÃ§erler YapÄ±", "DinÃ§ GÃ¼venlik" gibi FARKLI firmalarÄ± tek sahte "dinÃ§" firmasÄ± altÄ±nda topluyor
> (164 kazanÄ±m, 1 Mrd TL = hepsinin toplamÄ±, anlamsÄ±z). **DoÄŸru model (ihaleciler.com gibi, ki bizde
> ZATEN VAR):** `yukleniciler` tablosu (35K+ firma, normalize edilmiÅŸ, toplam_sozlesme_sayisi/toplam_ciro/
> il/sektor ile) tam olarak bu listeyi veriyor ama firma-analiz onu HÄ°Ã‡ kullanmÄ±yor. **YapÄ±lacak:**
> 1. Arama â†’ `yukleniciler`'den eÅŸleÅŸen AYRI firmalarÄ±n LÄ°STESÄ° gÃ¶sterilsin (isim + sÃ¶zleÅŸme sayÄ±sÄ± +
>    ciro + il), tÄ±pkÄ± ihaleciler.com "YÃ¼kleniciler" sekmesi gibi.
> 2. Bir firmaya tÄ±kla â†’ o firmanÄ±n DETAYI (kazandÄ±ÄŸÄ± ihaleler, katÄ±ldÄ±ÄŸÄ± ihaleler [bizde sadece
>    kazanÄ±lan var â€” EKAP kaybedeni yayÄ±nlamÄ±yor], yÄ±llara/il/sektÃ¶re daÄŸÄ±lÄ±m).
> 3. `yukleniciler`'e `arama_fold` (tr_fold) kolonu + trigram indeks ekle (ÅŸu an "dinÃ§" aramasÄ± Ä°/Ã§
>    yÃ¼zÃ¼nden 0 dÃ¶nÃ¼yor â€” aynÄ± TÃ¼rkÃ§e katlama sorunu; migration_ilanlar_arama_fold.sql ÅŸablonu).
> 4. Detay/SonuÃ§lar sekmesinde "(BaÅŸlÄ±k yok)" bug'Ä±: `ihale_sonuclari.ilan_id`â†’`ilanlar` join'i baslik
>    getirmiyor (backfill'in eklediÄŸi kompakt ilanlar satÄ±rlarÄ±nda baslik null). SonuÃ§larda Ä°HALEYÄ°
>    YAPAN KURUM (idare) + Ä°HALEYÄ° ALAN FÄ°RMANIN TAM ADI (kazanan_firma) + ihale baÅŸlÄ±ÄŸÄ± gÃ¶sterilmeli;
>    ihaleye tÄ±klayÄ±nca detay aÃ§Ä±lmalÄ± (ÅŸu an "veri bulamÄ±yor"). Kompakt satÄ±rlara baslik/idare
>    doldurmak ya da ihale_sonuclari'na bu alanlarÄ± denormalize etmek gerekebilir.
>
> **B) Son aramalar tÄ±klanÄ±nca aramÄ±yor** (kullanÄ±cÄ± bildirdi): firma-analiz landing'de "SON ARAMALAR"
> chip'lerine (Ã¶rn. "dinÃ§ lazer makine") tÄ±klayÄ±nca otomatik o firmayÄ± tekrar aratmalÄ±. Kod
> `firmaSectiClick` onclick'i doÄŸru GÃ–RÃœNÃœYOR ama kullanÄ±cÄ± Ã§alÄ±ÅŸmadÄ±ÄŸÄ±nÄ± sÃ¶ylÃ¼yor â€” redesign sÄ±rasÄ±nda
> tarayÄ±cÄ±da test edilip dÃ¼zeltilecek.
>
> **C) Sol-alt kullanÄ±cÄ± adÄ±/"Ãœcretsiz Plan" tÄ±klanÄ±nca profil ayarlarÄ± aÃ§Ä±lsÄ±n** (kullanÄ±cÄ±: "buna da
> bakacaÄŸÄ±z"): tÃ¼m sayfalarÄ±n sidebar'Ä±nda sol-altta Ã¼ye adÄ± + plan yazan blok var; tÄ±klanÄ±nca
> `profil` sayfasÄ±na gitmeli (ÅŸu an tÄ±klanamÄ±yor). Sidebar tÃ¼m sayfalarda ortak â†’ tek tek ya da paylaÅŸÄ±lan
> parÃ§a olarak eklenmeli.

> ## ğŸ”´ 15 TEMMUZ (devam) â€” GERÃ‡EK BUG: gece cron'u SESSÄ°ZCE Ã‡ALIÅMADI (run_scraper.sh +x kaybÄ±)
> Durum kontrolÃ¼ sÄ±rasÄ±nda bulundu: **15 Tem 02:00 UTC gece turu HÄ°Ã‡ Ã§alÄ±ÅŸmadÄ±** (scraper.log 14 Tem
> 03:01'den beri deÄŸiÅŸmemiÅŸ, bildirimler/scrape_log boÅŸ, aktif sayÄ± 15.381'de sabit). Cron tetiklenmiÅŸ
> (syslog doÄŸruladÄ±) ama **`run_scraper.sh` executable deÄŸildi**: git'e 14 Tem'de mode 100644 (Windows
> +x korumaz) kaydedilmiÅŸ, sonraki bir `git pull` VDS'teki +x'i sÄ±fÄ±rlamÄ±ÅŸ (14 Tem 17:39). Crontab
> `sh -c '.../run_scraper.sh'` non-executable dosyayÄ± Ã§alÄ±ÅŸtÄ±ramaz â†’ "Permission denied" â†’ sistemde MTA
> olmadÄ±ÄŸÄ± iÃ§in hata sessizce kayboldu. 14 Tem Ã§alÄ±ÅŸtÄ± Ã§Ã¼nkÃ¼ +x sÄ±fÄ±rlamasÄ± o turdan SONRAYDI.
> **FIX (commit `1f30011`):** `git update-index --chmod=+x` (git mode 755 â†’ gelecek pull'lar korur) +
> VDS'te `chmod +x`. VDS pull edildi, `mode change 100644 => 100755` doÄŸrulandÄ±, `-rwxr-xr-x`.
> **Bu geceki (16 Tem 02:00) tur artÄ±k Ã§alÄ±ÅŸacak.** KaÃ§an tur elle kurtarÄ±ldÄ±: `ekap_scraper.py -u`
> manuel Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± (12.296 gÃ¼ncel ihale). Bkz. hafÄ±za `scraper-cron-silent-fail` (2. kÃ¶k neden eklendi).
> **KÃ¼Ã§Ã¼k gÃ¶zlem:** ekap_scraper.py log'unda her ihale iÃ§in `[DEBUG-ILAN0-KEYS]` spam'i var â€” zararsÄ±z
> debug Ã§Ä±ktÄ±sÄ±, ileride temizlenebilir. **YARIN KONTROL:** 16 Tem 02:00 turu gerÃ§ekten Ã§alÄ±ÅŸtÄ± mÄ±
> (`stat scraper.log` mtime + yeni `=== Scraper baslatiliyor ===` damgasÄ±).

> ## ğŸ“‹ 15 TEMMUZ (devam) â€” durum kontrolÃ¼: backfill'ler patladÄ± (kullanÄ±cÄ± "kontrol et" dedi)
> Proxy'li derin backfill'ler ~10 saatte muazzam bÃ¼yÃ¼dÃ¼: `ilanlar` 90Kâ†’**157K**, `ihale_sonuclari`
> 153Kâ†’**254K**, `dogrudan_temin_ilanlari` 230Kâ†’**559K**. `--tum-kayitlar` modu (EKAP'Ä±n 1.68M sonuÃ§
> listesinden bizim bilmediÄŸimiz eski ihaleleri de doÄŸrudan ekliyor) Ã§ok verimli Ã§Ä±ktÄ±. Ä°ki sÃ¼reÃ§ de
> checkpoint'li, arka planda saÄŸlÄ±klÄ± Ã§alÄ±ÅŸÄ±yor. Disk hÃ¢lÃ¢ %14 (132GB boÅŸ) â€” kapasite sorunu YOK.
> **Not:** rekabetÃ§i backfill'in ilk turu (skip 81200â†’91200) platoya takÄ±lmÄ±ÅŸtÄ± (0 eÅŸleÅŸme); Ã§Ã¶zÃ¼m
> `--tum-kayitlar --start-skip 200000` ile baÄŸÄ±msÄ±z moda geÃ§mek oldu (PID 2996790).

> ## ğŸ“‹ 15 TEMMUZ OTURUMU (devam) â€” Webshare proxy alÄ±ndÄ± + baÄŸlandÄ± + backfill baÅŸlatÄ±ldÄ±
> KullanÄ±cÄ± Webshare'de **100 TÃ¼rkiye datacenter proxy** satÄ±n aldÄ± (Shared/Datacenter, 100 IP,
> 250GB/ay, ~$3/ay). Kurulum:
> - `backend/proxy_config.py` YENÄ°DEN YAZILDI â€” Ã¶nceden hiÃ§bir scraper tarafÄ±ndan kullanÄ±lmÄ±yordu
>   (kod hazÄ±rdÄ± ama baÄŸlanmamÄ±ÅŸtÄ±). Webshare'in paylaÅŸÄ±mlÄ± rotating gateway'i bu planda KAPALI
>   ("not in your list" hatasÄ±) â€” rotasyon istemci tarafÄ±nda `PROXY_LIST`'ten (100Ã— ip:port, ortak
>   kullanÄ±cÄ±/ÅŸifre) rastgele seÃ§imle yapÄ±lÄ±yor (`rastgele_proxy_url()`).
> - `backend/ekap_sonuc_backfill.py`'nin derin backfill dÃ¶ngÃ¼sÃ¼ndeki EKAP'a giden `httpx.AsyncClient`'Ä±na
>   proxy baÄŸlandÄ± (SADECE bu â€” kendi Supabase REST Ã§aÄŸrÄ±larÄ±mÄ±z proxy'siz kalÄ±yor). Proxy
>   yapÄ±landÄ±rÄ±lmamÄ±ÅŸsa None dÃ¶ner, nightly cron etkilenmez.
> - VDS `backend/.env`'e kimlikler eklendi (yedek alÄ±ndÄ±). Commit `cf2ac0b`.
> - **UÃ§tan uca doÄŸrulandÄ±:** tekil istek (5 gerÃ§ek EKAP kaydÄ±) VE sÃ¼rdÃ¼rÃ¼lebilir test (10 sayfa/1000
>   kayÄ±t, tek proxy IP, 0 hata) ikisi de baÅŸarÄ±lÄ±.
> - **KullanÄ±cÄ± onayÄ±yla derin backfill BAÅLATILDI** (15 Tem ~22:21 UTC): `nohup python3
>   ekap_sonuc_backfill.py --max-pages 50000` (PID deÄŸiÅŸebilir, checkpoint'ten devam eder,
>   `disown` ile SSH kopmalarÄ±na dayanÄ±klÄ±). Log: `logs/sonuc_backfill_proxy.log` (buffering
>   nedeniyle gecikmeli gÃ¶rÃ¼nebilir â€” bilinen zararsÄ±z durum, REST/checkpoint ile doÄŸrula).
>   Checkpoint baÅŸlangÄ±Ã§ `skip=81200`, hÄ±zlÄ± ilerliyor (~3400 kayÄ±t/dk gÃ¶zlemlendi).
> - **SÄ±radaki oturum:** ilerlemeyi kontrol et (`cat backend/.sonuc_backfill_checkpoint.json` +
>   REST'ten `ihale_sonuclari` toplam sayÄ±sÄ±), sÃ¼reÃ§ Ã¶lmÃ¼ÅŸse proxy ile yeniden baÅŸlat (checkpoint
>   kaldÄ±ÄŸÄ± yerden devam eder). Not: Webshare planÄ±nda "10 manual replacement" hakkÄ± var â€” bir IP
>   gerÃ§ekten bloklanÄ±rsa panelden deÄŸiÅŸtirilebilir, ama ÅŸu ana kadar hiÃ§ blok yaÅŸanmadÄ±.

> ## ğŸ“‹ 15 TEMMUZ OTURUMU â€” DASHBOARD: KPI kartlarÄ± tÄ±klanabilir + bildirim dropdown eklendi
> KullanÄ±cÄ± isteÄŸi: KPI sayÄ±larÄ±na (7 GÃ¼n Ä°Ã§inde Bitecek vb.) tÄ±klayÄ±nca filtrelenmiÅŸ ihale listesine
> gitmeli; bildirim ziline tÄ±klayÄ±nca aÃ§Ä±lÄ±r panel gÃ¶sterilmeli. UygulandÄ± ve yerelde gerÃ§ek prod
> verisiyle test edildi (her kart hedefi dashboard sayÄ±sÄ±yla eÅŸleÅŸiyor: 15.381 aktif, 1.195 bÃ¼yÃ¼k
> ihale, 1 bugÃ¼n son teklif). Yol boyu gerÃ§ek bug bulundu+dÃ¼zeltildi: `kpiYukle()`'nin "bugÃ¼n" sÄ±nÄ±rÄ±
> tarayÄ±cÄ± saatini gerÃ§ek UTC'ye Ã§eviriyordu ama DB'deki tarihler ham TÃ¼rkiye-yerel saat (UTC etiketli
> ama dÃ¶nÃ¼ÅŸtÃ¼rÃ¼lmemiÅŸ) â€” TR gece yarÄ±sÄ± sonrasÄ± (21:00-23:59 UTC) "bugÃ¼n" bir gÃ¼n kayÄ±yordu. Commit
> `5dffde9`, VDS'e deploy edildi, canlÄ±da doÄŸrulandÄ±.

> ## ğŸ“‹ 15 TEMMUZ OTURUMU â€” 3 Ä°Å TAMAMLANDI (kullanÄ±cÄ± "Ã¼Ã§Ã¼nÃ¼ de yap" dedi)
> KullanÄ±cÄ± 3 iÅŸi birden istedi; hepsi bitti:
>
> **1. âœ… 10. bug Ã‡Ã–ZÃœLDÃœ â€” `ihaleler.html` ANA arama TÃ¼rkÃ§e eÅŸleÅŸmesi (canlÄ±da doÄŸrulandÄ±):**
> Sunucu-side ILIKE TÃ¼rkÃ§e katlamÄ±yordu â†’ "insaat" yazÄ±nca "Ä°NÅAAT" iÃ§eren ihalelerin hiÃ§biri
> gelmiyordu (ampirik: `baslik ILIKE %insaat%`â†’0, `%Ä°NÅAAT%`â†’1998). **Ã‡Ã¶zÃ¼m:**
> `migration_ilanlar_arama_fold.sql` â€” IMMUTABLE `tr_fold()` (frontend `trFold` ile BÄ°REBÄ°R:
> Ä°/I/Ä±â†’i, Å/ÅŸâ†’s, Ä/ÄŸâ†’g, Ãœ/Ã¼â†’u, Ã–/Ã¶â†’o, Ã‡/Ã§â†’c + lower) + generated STORED `arama_fold` kolonu
> (baslik+idare+okas+isin_yapilacagi_yer+ilan_metni katlanmÄ±ÅŸ) + pg_trgm GIN indeks. `ihaleler.html`
> `arama_fold`'a ILIKE atÄ±yor (terim de trFold'lanÄ±yor), kolon yoksa legacy'ye dÃ¼ÅŸÃ¼yor. Migration
> prod'da 71sn'de uygulandÄ± (90K satÄ±r, kolon+indeks). **CanlÄ±da doÄŸrulandÄ±:** `arama_fold ILIKE
> %insaat%`â†’**6757** (eskiden 0); tarayÄ±cÄ±da "insaat" aramasÄ± 8+ sayfa inÅŸaat ihalesi, konsol temiz.
> Commit `d695714`, VDS'e pull edildi. **Not:** benzer sunucu-side arama `dogrudan-temin.html`'de de
> olabilir (DT artÄ±k 154K kayÄ±t) â€” kontrol edilmedi, olasÄ± takip iÅŸi.
>
> **2. âœ… Gece cron log taramasÄ± â€” TEMÄ°Z (yeni sorun yok):** `scraper.log` son tur 14 Tem 02:00,
> saÄŸlÄ±klÄ± baÅŸlayÄ±p bitmiÅŸ; sunucu UTC saati 14 Tem 21:10, sÄ±radaki tur bu gece 15 Tem 02:00 UTC.
> Logdaki 2 hata (yuklenici_yenile timeout, takip_firmalar 403) = 14 Tem GÃœNDÃœZ dÃ¼zeltilen bug'larÄ±n
> Ã–NCEki turdaki hali (beklenen); fix'ler + `idare_bildirim` cron eklemesi ilk kez BU GECE sÄ±nanacak.
> "E-posta bildirimi aÃ§Ä±k: 1 kullanÄ±cÄ±". Yeni/beklenmedik hata yok. (Kozmetik: notify.py konsol
> banner'Ä± hÃ¢lÃ¢ "Ä°HALE PLATFORM" yazÄ±yor, kullanÄ±cÄ±ya gitmiyor.)
>
> **3. âœ… DT backfill kontrolÃ¼ â€” 154.942 kayÄ±t** (14 Tem sonunda 47.615'ti; ~3Ã—). Tarih aralÄ±ÄŸÄ±
> **2002-05-24 â†’ 2027-07-02** â€” Ã§ok derin geÃ§miÅŸe inmiÅŸ. SÃ¼reÃ§ saÄŸlÄ±klÄ±.
>
> **Bu geceki (15 Tem 02:00 UTC) cron turundan sonra kontrol edilecek:** yuklenici_yenile timeout
> fix'i, takip_firmalar GRANT'i, idare_bildirim cron'u gerÃ§ek turda tuttu mu (log'dan).

> ## ğŸ“‹ 14 TEMMUZ OTURUMU â€” KAPANIÅ Ã–ZETÄ° (kullanÄ±cÄ± "bu kadar yeter" dedi)
> Bu oturumda yapÄ±lan her ÅŸeyin tek-bakÄ±ÅŸ Ã¶zeti (detaylar aÅŸaÄŸÄ±daki bloklarda):
>
> **Deploy/altyapÄ± (kullanÄ±cÄ± onaylarÄ±yla, SSH):**
> - VDS `git pull` (Ã¶nceki ~10 commit canlÄ±ya alÄ±ndÄ±) â†’ ÅŸu an `origin/main`'de son commit `30b79e7`.
> - EÅŸik katsayÄ±sÄ± backfill migration'Ä± (1.767 kayÄ±t, doluluk 866â†’2.633/3.169 aktif YapÄ±m).
> - KÄ°K Kurul KararlarÄ± deploy (97 gerÃ§ek karar, `kik-kararlar` sayfasÄ±nda canlÄ± doÄŸrulandÄ±).
> - `takip_idareler` 404 dÃ¼zeltildi (migration tekrar Ã§alÄ±ÅŸtÄ±, REST 200).
> - DT backfill self-healing yapÄ±ldÄ± + yeniden baÅŸlatÄ±ldÄ±: **2.680 â†’ 47.615 kayÄ±t** (hÃ¢lÃ¢ akÄ±yor).
> - `run_scraper.sh` ilk kez git'e alÄ±ndÄ± (tek kopyasÄ± VDS'teydi, sessiz sapmalar gÃ¶rÃ¼nmÃ¼yordu).
>
> **Bu oturumda bulunup DÃœZELTÄ°LEN 9 gerÃ§ek prod bug'Ä±** (hepsi ya gece log'unu okurken ya da sayfa
> test ederken Ã§Ä±ktÄ±):
> 1. `idare_bildirim.py` cron'da hiÃ§ yoktu â†’ kurum bildirimi 12 Tem'den beri hiÃ§ gitmemiÅŸ (eklendi).
> 2. `kik_backfill.py --max-pages 10` geÃ§ersiz flag â†’ her gece argparse hatasÄ± (`--gun 3` yapÄ±ldÄ±).
> 3. `takip_firmalar` service_role GRANT eksik â†’ rakip bildirimi her gece 403 (GRANT eklendi).
> 4. `yuklenici_yenile()` statement timeout â†’ yukleniciler hiÃ§ tazelenmiyordu (Ã¶zel timeout; artÄ±k
>    35.454 satÄ±r dolu â€” Firmalar Dizini'ni de besliyor).
> 5. DT backfill tekrarlayan ReadTimeout crash-loop â†’ self-healing retry eklendi.
> 6. `kazanan_teklif_farki_yuzde` NUMERIC(5,2) overflow â†’ NUMERIC(9,3)'e geniÅŸletildi.
> 7. `idare_sayim()` RPC'si prod'da hiÃ§ yoktu â†’ deploy + GRANT; idareler.html buna geÃ§irildi.
> 8. `firmalar.html` PostgREST 1000 satÄ±r limiti â†’ 35.454 firmadan 1.000'i gÃ¶rÃ¼nÃ¼yordu (sayfalandÄ±).
> 9. TÃ¼rkÃ§e Ä°/ÅŸ/ÄŸ arama eÅŸleÅŸmesi (firmalar/idareler/sektorler) â†’ `trFold()` eklendi, canlÄ± doÄŸrulandÄ±.
>
> **Tespit edilen ama DÃœZELTÄ°LMEYEN (bÃ¼yÃ¼k iÅŸ, ayrÄ± gÃ¶rev chip'i aÃ§Ä±ldÄ±):**
> - 10. `ihaleler.html` ANA arama: sunucu-side Postgres ILIKE TÃ¼rkÃ§e katlamÄ±yor ("insaat"â†’0, ~2000
>   inÅŸaat ihalesi kaÃ§Ä±yor). `ilanlar` (90K) ÅŸema deÄŸiÅŸikliÄŸi + trigram indeks gerektiriyor.
>
> **HÃ‚LÃ‚ KULLANICI GÄ°RÄ°ÅÄ°/KARARI BEKLEYEN (bunlarÄ± AI yapamadÄ±):**
> - Kurum + rakip takibi e-posta bildiriminin gerÃ§ek kullanÄ±cÄ±yla uÃ§tan uca testi (giriÅŸ gerekiyor,
>   AI parola giremez). GRANT+cron tarafÄ± hazÄ±r; bu geceki 02:00 UTC cron turu ilk canlÄ± testtir.
> - Webshare proxy: hesap var mÄ±? (rekabetÃ§i ihale derin backfill'i buna baÄŸlÄ±; DT buna gerek duymaz).
> - Faz D3 embed hÄ±zÄ± (gece 300 mÃ¼, artÄ±rÄ±lsÄ±n mÄ±?), Ä°yzico (en sona bÄ±rakÄ±ldÄ±), SMS (konuÅŸulmadÄ±).

> ## âœ… 14 Tem â€” 3 KRÄ°TÄ°K PROD Ä°ÅLEMÄ° TAMAMLANDI (kullanÄ±cÄ± onayÄ±yla, SSH)
> 1. **Git pull yapÄ±ldÄ±** â€” VDS artÄ±k `83bd5d2`'de, Ã¶nceki oturumlarÄ±n tÃ¼m bekleyen commit'leri
>    (profil.html fix, takip_idareler, bildirim-sayaci.js, dogrudan-temin Ã§apraz link, vb.) canlÄ±da.
> 2. **EÅŸik katsayÄ±sÄ± backfill Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±** â€” `migration_esik_katsayi_backfill.sql` prod DB'de
>    uygulandÄ±: **1767 kayÄ±t gÃ¼ncellendi**, doluluk 866â†’**2633/3169** aktif YapÄ±m ihalesi.
> 3. **KÄ°K Kurul KararlarÄ± deploy edildi** â€” `deploy_12tem_kik_kararlari.sh` Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±, gerÃ§ek
>    Ã§ekim testi **97 karar** yazdÄ± (canlÄ±da REST API ile doÄŸrulandÄ±: `kik_kararlar` tablosu 97
>    kayÄ±t, Ã¶rn. `2026/UH.I-1835`, idare="MALATYA EÄÄ°TÄ°M VE ARAÅTIRMA HASTANESÄ°"). Gece cron'una
>    zaten ekliydi (`kik_backfill.py --gun 3`), tekrar eklenmedi. **CanlÄ±da tarayÄ±cÄ±yla doÄŸrulandÄ±**
>    (https://ihaleglobal.com/kik-kararlar â†’ "Ara"ya basÄ±nca 97 karar, 5 sayfa, konsol temiz).
>    Not: migration script'inde 1 policy-already-exists ERROR'u vardÄ± ama zararsÄ±z (idempotent
>    migration'Ä±n beklenen NOTICE'larÄ±ndan biri, script durmadÄ±). Not 2: sayfadaki
>    Ä°ptal/Kabul/Red sayaÃ§larÄ± hepsi 0 gÃ¶steriyor Ã§Ã¼nkÃ¼ `sonuc` alanÄ± ÅŸu an tÃ¼m kayÄ±tlarda "diger" â€”
>    bu zaten bilinen sÄ±nÄ±rlama (aÅŸaÄŸÄ±daki "detay API" eksikliÄŸi), bug deÄŸil.
>
> **SÄ±nÄ±rlama (KÄ°K):** liste gÃ¶rÃ¼nÃ¼mÃ¼nde tam karar metni/sonucu (iptal/kabul/red) yok â€” ayrÄ± bir
> "detay" API Ã§aÄŸrÄ±sÄ± gerektiriyor, henÃ¼z Ã§Ã¶zÃ¼lmedi (gelecek iÅŸ).

> ## ğŸ”´ 14 Tem (devam) â€” 2 DAHA GERÃ‡EK CRON BUG'I BULUNDU + DÃœZELTÄ°LDÄ° (gece log'u incelenirken)
> DÃ¼nkÃ¼ (14 Tem 02:00) `scraper.log`'da 2 hata daha bulundu, ikisi de kullanÄ±cÄ± onayÄ±yla dÃ¼zeltildi:
> 1. **`takip_firmalar` 403 permission denied** â€” `migration_takip_firmalar.sql` (Faz E1, eski)
>    service_role'e hiÃ§ GRANT vermemiÅŸ (sonradan yazÄ±lan `migration_takip_idareler.sql`'de bu
>    unutulmamÄ±ÅŸtÄ± â€” karÅŸÄ±laÅŸtÄ±rÄ±nca fark edildi). **SonuÃ§: rakip (firma) takibi bildirimleri
>    12 Tem'den beri muhtemelen HÄ°Ã‡ gÃ¶nderilmemiÅŸ.** `migration_takip_firmalar_service_role_grant.sql`
>    ile dÃ¼zeltildi, GRANT SQL seviyesinde doÄŸrulandÄ±. **Ama `rakip_bildirim.py`'yi manuel test
>    ETMEDÄ°M** â€” script'te dedup yoksa (sadece 26 saatlik zaman penceresi kontrolÃ¼ var) gerÃ§ek
>    eÅŸleÅŸme varsa kullanÄ±cÄ±ya mÃ¼kerrer e-posta gidebilirdi. GerÃ§ek doÄŸrulama bu geceki (02:00 UTC)
>    cron turunda `scraper.log`'dan kontrol edilmeli.
> 2. **`yuklenici_yenile()` 500 statement timeout** â€” `ihale_sonuclari` bÃ¼yÃ¼dÃ¼kÃ§e (138K+, backfill
>    ile artÄ±yor) agregasyon sorgusu varsayÄ±lan timeout'u aÅŸÄ±yordu. `ALTER FUNCTION ... SET
>    statement_timeout='300000'` ile dÃ¼zeltildi VE **uÃ§tan uca doÄŸrulandÄ±**: hem doÄŸrudan psql
>    (49sn, 35.454 satÄ±r) hem de gerÃ§ek cron'un kullandÄ±ÄŸÄ± REST/script yolu (`yuklenici_yenile_calistir.py`,
>    43.7sn, aynÄ± sonuÃ§) ile Ã§alÄ±ÅŸtÄ±. `yukleniciler` tablosu artÄ±k gerÃ§ekten tazeleniyor.
> **Ders:** `takip_idareler` ile `takip_firmalar` migration'larÄ±nÄ± karÅŸÄ±laÅŸtÄ±rÄ±nca ortaya Ã§Ä±ktÄ± â€”
> benzer/kopyalanan migration'lar arasÄ±nda GRANT gibi tekrar eden parÃ§alar tutarlÄ±lÄ±k iÃ§in
> karÅŸÄ±laÅŸtÄ±rmalÄ± kontrol edilmeli (gelecekte yeni "takip_X" tablolarÄ± eklenirse).

> ## âœ… 14 Tem (devam) â€” DT backfill artÄ±k kendi kendini iyileÅŸtiriyor + hÄ±zlÄ± ilerliyor
> SÃ¼reÃ§ bu oturumda 2 kez `httpx.ReadTimeout` ile Ã¶lmÃ¼ÅŸtÃ¼ (EKAP tarafÄ± geÃ§ici kesinti, `sayfa_cek()`
> zaten 3 deneme yapÄ±yordu ama Ã¼Ã§Ã¼ de tÃ¼kenince exception process'i Ã¶ldÃ¼rÃ¼yordu). `ekap_dogrudan_temin_scraper.py`'ye
> ana dÃ¶ngÃ¼ seviyesinde ek bir katman eklendi: son hata da yakalanÄ±yor, checkpoint bozulmadan 60sn
> beklenip AYNI sayfadan devam ediliyor â€” artÄ±k manuel restart gerektirmemeli. Commit `7d96b02`,
> VDS'e pull edilip backfill yeniden baÅŸlatÄ±ldÄ± (PID `2221006`). **Ä°lerleme hÄ±zlÄ±:** 2.680â†’5.247â†’**14.211**
> kayÄ±t (en eski tarih artÄ±k 2021-04-01'e inmiÅŸ, sistem 2022'den beri diye biliniyorduk â€” yani
> EKAP'Ä±n dt sistemi dÃ¼ÅŸÃ¼nÃ¼lenden daha eskiye gidiyor ya da nadir 2021 kayÄ±tlarÄ± da var). Bitince
> (boÅŸ sayfa dÃ¶nÃ¼nce) toplam kayÄ±t/tarih aralÄ±ÄŸÄ± kullanÄ±cÄ±ya bildirilecek.

> ## âœ… 14 Tem (devam) â€” 3. GERÃ‡EK BUG: `kazanan_teklif_farki_yuzde` overflow (dÃ¼zeltildi)
> AynÄ± gece log'unda `numeric field overflow` hatasÄ± bulundu: kolon `NUMERIC(5,2)` (maks Â±999.99)
> ama `ekap_sonuc_backfill.py` tenzilat'Ä± 3 ondalÄ±kla hesaplÄ±yor (`round(...,3)`, zaten scale
> uyumsuzluÄŸu vardÄ±) ve yaklaÅŸÄ±k maliyet kazanan teklife gÃ¶re Ã§ok kÃ¼Ã§Ã¼kse yÃ¼zde Â±999.99'u aÅŸÄ±yor â€”
> bu satÄ±rlar sessizce yazÄ±lamÄ±yordu. KardeÅŸ kolon `tenzilat_yuzde` (Design B) zaten NUMERIC(6,3) idi.
> `migration_kazanan_teklif_farki_genislet.sql` ile NUMERIC(9,3)'e geniÅŸletildi (veri kaybÄ±
> riski yok, sadece geniÅŸletme), VDS'te uygulandÄ± + doÄŸrulandÄ±.
>
> **Bu oturumun genel Ã¶zeti â€” 6 baÄŸÄ±msÄ±z gerÃ§ek prod bug'Ä± bulundu, hepsi gece log'larÄ±nÄ± okurken
> ortaya Ã§Ä±ktÄ±** (idare_bildirim cron'da yok, kik_backfill yanlÄ±ÅŸ flag, takip_firmalar GRANT eksik,
> yuklenici_yenile timeout, DT backfill crash-loop, kazanan_teklif_farki_yuzde overflow). **Tavsiye:**
> `scraper.log`'u dÃ¼zenli (haftalÄ±k?) tarama, sessiz cron hatalarÄ±nÄ± yakalamanÄ±n en etkili yolu
> Ã§Ä±ktÄ± â€” bu oturumda organik olarak yapÄ±ldÄ± ama dÃ¼zenli bir alÄ±ÅŸkanlÄ±k olabilir.

> ## âœ… 14 Tem (devam) â€” `idareler.html` performans optimizasyonu + 7. bug (kullanÄ±cÄ± onayÄ±yla)
> `idare_sayim()` RPC'si `migration_sonuc_schema.sql`'de tanÄ±mlÄ±ydÄ± ama prod'da HÄ°Ã‡ VAR OLMAMIÅTI
> (PGRST202 â€” muhtemelen migration ilk Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±ÄŸÄ±nda script daha Ã¶nceki bir ifadede durmuÅŸ).
> `migration_idare_sayim_grant.sql` ile deploy edildi + GRANT eklendi (commit `2fc2d30`).
> `idareler.html` bu RPC'yi kullanacak ÅŸekilde yeniden yazÄ±ldÄ± (commit `72bdbe7`) â€” Ã¶nceden TÃœM
> `ilanlar` tablosunu (89.975 satÄ±r) 1000'lik sayfalarla tarayÄ±cÄ±ya indirip JS'te GROUP BY yapÄ±yordu.
> **Deploy sÄ±rasÄ±nda 7. bir bug bulundu + hemen dÃ¼zeltildi:** ilk versiyon RPC'yi `.range()` ile
> Ã§aÄŸÄ±rÄ±yordu ama PostgREST sunucusu POST isteklerinde sabit 1000 satÄ±r limiti uyguluyor (`db-max-rows`,
> Range header'Ä± yok sayÄ±yor) â€” canlÄ±da test edilirken "15.130 idareden sadece 1.000'i" gÃ¶rÃ¼ndÃ¼ÄŸÃ¼
> fark edildi. DÃ¼zeltme (commit `4482133`): GET + `limit`/`offset` query param'larÄ±yla sayfalÄ± Ã§ekim
> (PostgREST bunu doÄŸru destekliyor, curl ile doÄŸrulandÄ±). **CanlÄ±da tam doÄŸrulandÄ±:** 15.130 idare,
> 89.974 toplam ihale (gerÃ§ek `ilanlar` sayÄ±sÄ±yla eÅŸleÅŸiyor), arama/filtre Ã§alÄ±ÅŸÄ±yor, konsol temiz.

> ## âœ… 14 Tem (devam) â€” 8. bug: `firmalar.html` da aynÄ± 1000 satÄ±r limitine takÄ±lÄ±yordu
> `idareler.html`'i dÃ¼zeltince aynÄ± deseni `firmalar.html`/`sektorler.html`'de aradÄ±m. `sektorler.html`
> zaten `kategori_sayim()` RPC'sini tercih ediyor + kategori sayÄ±sÄ± az (~40) â†’ 1000 limitine takÄ±lmÄ±yor,
> SORUN YOK. Ama `firmalar.html` `yukleniciler`'i `.limit(5000)` ile Ã§ekiyordu â€” PostgREST `db-max-rows`
> sunucu limiti bunu 1000'e kesiyor (curl ile doÄŸrulandÄ±: Content-Range 0-999/35454). `yukleniciler`
> bugÃ¼n ilk kez tam doldu (35.454, `yuklenici_yenile` timeout fix'i sonrasÄ±) â€” yani Firmalar Dizini
> cirosu en yÃ¼ksek 1000 firmayÄ± gÃ¶sterip kalan ~34.000'i **arama sonuÃ§larÄ±ndan sessizce dÃ¼ÅŸÃ¼rÃ¼yordu**
> (kullanÄ±cÄ± ilk 1000'de olmayan bir firmayÄ± arayÄ±nca "bulunamadÄ±" gÃ¶rÃ¼yordu). `.range()` sayfalÄ±
> Ã§ekime geÃ§irildi (commit `5121ced`). **CanlÄ±da doÄŸrulandÄ±:** 35.454 firma / 710 sayfa yÃ¼kleniyor,
> "kalyon" aramasÄ± 6 firma buluyor, konsol temiz.
>
> ## âœ… 14 Tem (devam) â€” 9. bug DÃœZELTÄ°LDÄ°: TÃ¼rkÃ§e Ä°/ÅŸ/ÄŸ arama eÅŸleÅŸmesi
> Dizin sayfalarÄ±ndaki arama `f.ad.toLowerCase().includes(aramaVal)` kullanÄ±yordu. JS `toLowerCase()`
> TÃ¼rkÃ§e-duyarsÄ±z: `"PREFABRÄ°K".toLowerCase()` â†’ `"prefabriÌ‡k"` (i + combining dot), bu yÃ¼zden dÃ¼z
> `"prefabrik"` yazÄ±nca eÅŸleÅŸmiyordu. `Å/Ä/Ä°/I/Ä±` iÃ§eren firma/idare adlarÄ± normal yazÄ±mla
> bulunamÄ±yordu â€” TÃ¼rk kamu ihale platformu iÃ§in ciddi UX sorunu. **Ã‡Ã¶zÃ¼m uygulandÄ±:** `firmalar.html`,
> `idareler.html`, `sektorler.html`'e `trFold()` (Ä°/I/Ä±â†’i, Å/ÅŸâ†’s, Ä/ÄŸâ†’g, Ãœ/Ã¼â†’u, Ã–/Ã¶â†’o, Ã‡/Ã§â†’c +
> toLowerCase) eklendi, aramanÄ±n her iki tarafÄ±na uygulandÄ±. Commit `cb8291d`. **CanlÄ±da doÄŸrulandÄ±:**
> "prefabrik" â†’ 46 firma (Ã¶nceden 0), "insaat" â†’ 11.898 firma (Ä°NÅAAT eÅŸleÅŸiyor), "saglik" â†’ 1.348
> idare (SAÄLIK BAKANLIÄI eÅŸleÅŸiyor), konsol temiz.
>
> ## ğŸ”´ 14 Tem (devam) â€” 10. bug TESPÄ°T EDÄ°LDÄ° (henÃ¼z DÃœZELTÄ°LMEDÄ°, bÃ¼yÃ¼k iÅŸ): ihaleler.html TÃ¼rkÃ§e arama
> `ihaleler.html` (ANA arama sayfasÄ±) aramayÄ± sunucu-side Postgres `ILIKE` ile yapÄ±yor (client-side JS
> deÄŸil â€” `baslik/idare/okas/isin_yapilacagi_yer/ilan_metni` Ã¼zerinde `.or(...ilike...)`). Bu DB'nin
> locale'inde ILIKE TÃ¼rkÃ§e Ä°/ÅŸ/ÄŸ katlamÄ±yor. **Ampirik olarak REST ile doÄŸrulandÄ±:**
> `baslik ILIKE '%insaat%'` â†’ **0 sonuÃ§**; `'%Ä°NÅAAT%'` â†’ **1998**; `'%inÅŸaat%'` (kÃ¼Ã§Ã¼k ÅŸ) â†’ **74**.
> Yani kullanÄ±cÄ± "insaat" yazÄ±nca ~2000 inÅŸaat ihalesinin HÄ°Ã‡BÄ°RÄ°NÄ° gÃ¶rmÃ¼yor â€” ana sayfada ciddi bug.
> **Ã‡Ã¶zÃ¼m (bÃ¼yÃ¼k iÅŸ, ayrÄ± oturum):** `ilanlar` (90K satÄ±r) Ã¼zerinde ya `unaccent`+trigram, ya da
> TÃ¼rkÃ§e-katlanmÄ±ÅŸ generated kolon(lar) + GIN/trigram indeks + frontend'in arama terimini de aynÄ±
> ÅŸekilde katlayÄ±p o kolonlarÄ± sorgulamasÄ±. En bÃ¼yÃ¼k tabloda ÅŸema deÄŸiÅŸikliÄŸi + performans indeksi +
> sorgu yeniden yazÄ±mÄ± â†’ dikkatli tasarÄ±m ve test ister, oturum sonunda aceleye getirilmemeli.

> ## â„¹ï¸ 14 Tem (devam) â€” YANLIÅ ALARM: DT backfill log'u yanÄ±ltÄ±cÄ± gÃ¶rÃ¼nÃ¼yordu (buffering)
> `dt_backfill.log`'un son satÄ±rlarÄ± eski bir traceback gÃ¶steriyordu (self-healing fix'ten Ã¶nceki
> bir Ã§Ã¶kÃ¼ÅŸten kalma) ve 11 dakika boyunca yeni satÄ±r eklenmemiÅŸ gibi gÃ¶rÃ¼nÃ¼yordu â€” sÃ¼reÃ§ Ã¶lmÃ¼ÅŸ
> sanÄ±ldÄ±. Ama REST API'den kayÄ±t sayÄ±sÄ± kontrol edilince **14.211â†’19.723**'e Ã§Ä±ktÄ±ÄŸÄ± gÃ¶rÃ¼ldÃ¼ â€”
> sÃ¼reÃ§ aslÄ±nda sorunsuz Ã§alÄ±ÅŸÄ±yormuÅŸ. KÃ¶k neden: `nohup python script.py >> log` non-tty stdout'ta
> Python'u block-buffered yapÄ±yor, `print()` Ã§Ä±ktÄ±larÄ± hemen dosyaya yazÄ±lmÄ±yor (traceback'ler
> stderr Ã¼zerinden anlÄ±k yazÄ±lÄ±yor, bu yÃ¼zden "en son" iÃ§erik yanÄ±ltÄ±cÄ± ÅŸekilde eski bir hata
> gibi gÃ¶rÃ¼nÃ¼yor). **GerÃ§ek bug deÄŸil, sadece gÃ¶zlemlenebilirlik sorunu.** Ä°leride sÃ¼reÃ§ yeniden
> baÅŸlatÄ±lÄ±rken `python -u` (unbuffered) eklenirse log gerÃ§ek zamanlÄ±, gÃ¼venilir takip iÃ§in daha
> iyi olur â€” ÅŸu an Ã§alÄ±ÅŸan sÃ¼reci bunun iÃ§in kesintiye uÄŸratmaya deÄŸmez.

> ## âœ… 14 Tem â€” 2 EK DÃœZELTME TAMAMLANDI (kullanÄ±cÄ± ayrÄ± onayÄ±yla)
> 1. **`takip_idareler` dÃ¼zeltildi** â€” migration tekrar Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±, tablo+3 RLS policy oluÅŸtu,
>    `NOTIFY pgrst, 'reload schema'` tetiklendi. **REST API ile doÄŸrulandÄ±: artÄ±k 200 OK** (Ã¶nceden
>    404). Kurum takibi butonu artÄ±k Ã§alÄ±ÅŸmalÄ± â€” henÃ¼z tarayÄ±cÄ±da tÄ±klama testi yapÄ±lmadÄ±.
> 2. **DT backfill process yeniden baÅŸlatÄ±ldÄ±** (`nohup ... --backfill --max-pages 100000 & disown`,
>    checkpoint'ten devam) â€” PID `2122545` doÄŸrulandÄ±, Ã§alÄ±ÅŸÄ±yor. Ã–nceki Ã§Ã¶kÃ¼ÅŸte kayÄ±t 2.680â†’**5.247**'ye
>    Ã§Ä±kmÄ±ÅŸtÄ± (en eski tarih MayÄ±s 2023â†’24 Ara 2021), ÅŸimdi kaldÄ±ÄŸÄ± yerden devam ediyor.

> ## ğŸ”´ 14 Tem â€” 2 GERÃ‡EK CRON BUG'I BULUNDU + DÃœZELTÄ°LDÄ° (VDS `run_scraper.sh`, git'te takip edilmiyor!)
> `run_scraper.sh` repoda YOK (sadece VDS'te elle dÃ¼zenleniyor) â€” bu yÃ¼zden geÃ§miÅŸ deploy script'lerinin
> "eklendi" varsayÄ±mlarÄ± asÄ±l dosyada doÄŸrulanmamÄ±ÅŸtÄ±. Kontrol edilince:
> 1. **`idare_bildirim.py` (kurum takibi bildirimi) hiÃ§ cron'da deÄŸildi** â€” `deploy_12tem_kurum_takibi.sh`
>    muhtemelen bir Ã¶nceki SSH-kopmasÄ± yÃ¼zÃ¼nden 3. adÄ±ma hiÃ§ ulaÅŸmamÄ±ÅŸ (aynÄ± oturumda `takip_idareler`
>    tablosunun da commit olmadan kopmasÄ± gibi). Yani **kurum takibi Ã¶zelliÄŸi deploy edildiÄŸinden beri
>    (12 Tem) hiÃ§bir kullanÄ±cÄ±ya kurum bildirimi gitmemiÅŸ.** SatÄ±r eklendi (sona), doÄŸrulandÄ±.
> 2. **`kik_backfill.py --max-pages 10`** â€” bu flag scraper'Ä±n script'inde HÄ°Ã‡ YOK (argparse sadece
>    `--gun`/`--baslangic`/`--bitis`/`--dry-run` kabul ediyor), muhtemelen eski (13 Tem Ã¶ncesi) bir
>    kik_backfill.py sÃ¼rÃ¼mÃ¼nden kalma satÄ±r, yeniden yazÄ±mda flag'i kaldÄ±rÄ±lmÄ±ÅŸ ama cron satÄ±rÄ±
>    gÃ¼ncellenmemiÅŸ â€” **her gece argparse hatasÄ±yla sessizce baÅŸarÄ±sÄ±z oluyordu.** `--gun 3`'e
>    dÃ¼zeltildi (deploy script'inin Ã¶ngÃ¶rdÃ¼ÄŸÃ¼ doÄŸru deÄŸer).
> **Ders/tavsiye:** `run_scraper.sh` git'e alÄ±nmalÄ± (ÅŸu an tek kopyasÄ± VDS'te, tarihi yok, bu tÃ¼r
> sessiz sapmalar fark edilmiyor) â€” gelecek oturum iÃ§in Ã¶neri.

**CanlÄ± site:** `https://ihaleglobal.com` (VDS `195.85.207.126`, self-hosted Supabase). Managed
Supabase terk edildi, Render tamamen kaldÄ±rÄ±ldÄ±. `ilanlar` ~79.7K (aktif 14.7K), `ihale_sonuclari`
**138K** (geÃ§miÅŸ backfill hÃ¢lÃ¢ arka planda akÄ±yor), `dogrudan_temin_ilanlari` **2.680** (â†“).

**âš ï¸ 12 Tem DÃœZELTME â€” Ã¶nceki oturumun "DT backfill Ã§alÄ±ÅŸÄ±yor, 1.664 kayÄ±t" iddiasÄ± GERÃ‡EKLEÅMEMÄ°Å:**
Bu oturumda kontrol edildiÄŸinde `dogrudan_temin_ilanlari` tablosu **BOÅTU** (0 kayÄ±t) ve iddia edilen
backfill process (PID 3839631) Ã§alÄ±ÅŸmÄ±yordu â€” yani o "deploy" migration'Ä± Ã§alÄ±ÅŸtÄ±rmÄ±ÅŸ ama veri
kalÄ±cÄ± olmamÄ±ÅŸ (process muhtemelen VDS restart'Ä±nda Ã¶ldÃ¼, hiÃ§ commit etmeden). **Bu oturumda GERÃ‡EKTEN
tamamlandÄ±:** migration (idempotent) + `--max-pages 20` gerÃ§ek Ã§ekim â†’ **2.680 gerÃ§ek DT kaydÄ± yazÄ±ldÄ±**
(1.016 farklÄ± idare, 1.821 Mal / 777 Hizmet), gece cron'da (`run_scraper.sh`) `--max-pages 20` ile
gÃ¼ncel tutuluyor. **YENÄ°: `dogrudan-temin.html` gÃ¶rÃ¼ntÃ¼leme sayfasÄ± eklendi** (Ã¶nceden veri DB'de olsa
bile gÃ¶rÃ¼nmÃ¼yordu â€” hiÃ§ frontend yoktu): istatistik + baÅŸlÄ±k/idare arama + tÃ¼r/il filtresi + sÄ±ralama +
sayfalama + CSV; 16 sayfanÄ±n sidebar'Ä±na "âš¡ DoÄŸrudan Temin" linki eklendi. CanlÄ±da doÄŸrulandÄ±
(https://ihaleglobal.com/dogrudan-temin â†’ 2.680 kayÄ±t, 108 sayfa, konsol temiz). **Opsiyonel kalan:**
derin tarihsel DT backfill (`--backfill --max-pages 5000`, checkpoint `.dt_scraper_checkpoint.json`)
elle baÅŸlatÄ±labilir â€” launch'Ä± bloklamÄ±yor, gece cron zaten en yeniyi Ã§ekiyor.

**âœ… KAYIT E-POSTA ONAY AKIÅI DÃœZELTÄ°LDÄ° (12 Tem, kullanÄ±cÄ± bug bildirdi):** Sorun: `signUp`'ta
`emailRedirectTo` yoktu â†’ onay e-postasÄ±ndaki baÄŸlantÄ± SITE_URL'e (anasayfa) dÃ¶nÃ¼yordu, anasayfa hash'teki
token'Ä± iÅŸlemediÄŸi iÃ§in kullanÄ±cÄ± "hiÃ§bir ÅŸey olmadÄ±" sanÄ±yordu (aslÄ±nda onaylanÄ±yordu). Ã‡Ã¶zÃ¼m: (1) `js/api.js`
signUp'a `emailRedirectTo=SITE_URL+"/login"`; (2) `index.html` en Ã¼ste senkron hash-yakalayÄ±cÄ± (allow-list
boÅŸken link anasayfaya dÃ¼ÅŸse bile #access_token'Ä± `/login`'e taÅŸÄ±r); (3) `login.html` hash iÅŸleyici â†’
setSession ile token'Ä± DOÄRULAR (geÃ§ersiz/sÃ¼resi dolmuÅŸsa hata gÃ¶sterir, dashboard'a atmaz), geÃ§erliyse
oturumu kurup dashboard'a alÄ±r; (4) kayÄ±t sonrasÄ± mesaj netleÅŸti. **CanlÄ±da test edildi** (sahte token â†’
`/login`'de kalÄ±p doÄŸru hata veriyor; gerÃ§ek token aynÄ± yolla oturum kurup dashboard'a gider). Commit'ler
`5159815`/`5ddafec`/`91b1d78`. **Opsiyonel (zorunlu deÄŸil):** VDS `ADDITIONAL_REDIRECT_URLS`'e
`https://ihaleglobal.com/**` eklenirse onay linki anasayfa-hop'u olmadan doÄŸrudan `/login`'e dÃ¶ner
(kozmetik; classifier auth-config deÄŸiÅŸikliÄŸini bloke etti, kullanÄ±cÄ± onayÄ±yla yapÄ±labilir).

**ğŸŸï¸ PRO KUPON ÃœRETÄ°LDÄ° (12 Tem, kullanÄ±cÄ± talebi):** `IHP-35533C91` â€” standart (Pro) plan, 12 ay,
1 kullanÄ±m. Kupon sistemi zaten kuruluydu (`backend/kupon_olustur.py`, `kuponlar`/`kupon_kullanimlari`
tablolarÄ±, payment.py `/kupon-kullan` endpoint'i â€” router bu oturumda baÄŸlandÄ±, canlÄ± 401 dÃ¶nÃ¼yor).
KullanÄ±cÄ± `fiyatlandirma_odeme_bolumu` sayfasÄ±ndaki kupon kutusuna girip kendi hesabÄ±nÄ± Pro yapar
(kredi_yukle service_role ile yazar, plan='standart' â†’ js/plan.js artÄ±k tanÄ±yor).

**ğŸ¤– GEMINI/AI KULLANIM HARÄ°TASI (12 Tem, kullanÄ±cÄ± sordu â€” netleÅŸtirildi):** Gemini 4 yerde baÄŸlÄ±:
(1) **Åartname Analizi** `/analiz` (ihale-detay "Analiz Et") â€” bu oturumda uÃ§tan uca test edildi, gerÃ§ek
rapor Ã¼retti âœ…; (2) **AI Firma/Rakip Yorumu** `/ai/firma-yorum` (firma-analiz) ğŸŸ¡; (3) **AI Teklif
TaslaÄŸÄ±** `/teklif-olustur` (teklif-olustur "AI ile OluÅŸtur") ğŸŸ¡; (4) **CAPTCHA Ã§Ã¶zme** (belge indirme,
`gemini-2.5-flash`) â€” aktif kullanÄ±mda âœ…. (5) Semantik embedding (Faz D3) uykuda. **KRÄ°TÄ°K:** bu 3
kullanÄ±cÄ±-Ã¶zelliÄŸinin hepsi bu oturuma kadar KIRIKTI (`gemini-1.5-flash` 404 + File API + kredi bug'larÄ±);
bu oturumda dÃ¼zeltildi. Model her yerde `gemini-2.5-flash`.

**âš ï¸ 12 Tem (otonom devam oturumu) â€” 2 GERÃ‡EK SORUN BULUNDU + 1 DÃœZELTÄ°LDÄ°:**

1. **`takip_idareler` tablosu ÅŸemada YOK (404 PGRST205):** Kurum takibi butonu (`kurum-analiz.html`)
   test edildi â€” tÄ±klanÄ±nca "âœ“ Takip Ediliyor"a dÃ¶nmÃ¼yor, network'te `takip_idareler` sorgusu 404
   dÃ¶nÃ¼yor. Ã–nceki oturumun deploy Ã§Ä±ktÄ±sÄ± migration'Ä±n baÅŸarÄ±lÄ± olduÄŸunu gÃ¶steriyordu (policy'ler
   listelendi) ama ÅŸu an tablo PostgREST ÅŸema Ã¶nbelleÄŸinde yok â€” muhtemelen transaction commit
   olmadan baÄŸlantÄ± koptu (bugÃ¼n SSH birkaÃ§ kez koptu). **Ã‡Ã¶zÃ¼m: migration'Ä± tekrar Ã§alÄ±ÅŸtÄ±r**
   (idempotent, zararsÄ±z): `docker exec -i supabase-db psql -U postgres -d postgres <
   backend/migration_takip_idareler.sql`. Buna karÅŸÄ±n `takip_firmalar` (rakip takibi) SORUNSUZ
   Ã§alÄ±ÅŸÄ±yor â€” canlÄ±da gerÃ§ek kullanÄ±cÄ±yla test edildi, DB'ye yazdÄ±.
2. **DT backfill process (PID 3839631) yine Ã¶lÃ¼:** `dogrudan_temin_ilanlari` iki kontrol arasÄ±nda
   (birkaÃ§ dakika) hiÃ§ bÃ¼yÃ¼medi (2.680'de sabit, en eski tarih hÃ¢lÃ¢ MayÄ±s 2023) â€” process artÄ±k
   Ã§alÄ±ÅŸmÄ±yor. Devam ettirmek istersen tekrar baÅŸlat (checkpoint kaldÄ±ÄŸÄ± yerden devam eder):
   `cd /opt/ihale-platform/backend && source venv/bin/activate && nohup python
   ekap_dogrudan_temin_scraper.py --backfill --max-pages 100000 >> ../logs/dt_backfill.log 2>&1 &`
   â€” bu sefer `disown` da eklemek SSH kopmalarÄ±na karÅŸÄ± ekstra gÃ¼venlik saÄŸlar.
3. **âœ… DÃœZELTÄ°LDÄ° â€” `profil.html` bildirim tercihi bug'Ä±:** `kaydet()` fonksiyonu sektÃ¶r
   seÃ§ilmemiÅŸse en baÅŸta `return` ediyordu â€” bu yÃ¼zden `bildirim_email` gibi sektÃ¶rle alakasÄ±z bir
   ayar bile kaydedilemiyordu (bugÃ¼nkÃ¼ kurum/rakip takibi e-posta Ã¶zelliÄŸinin pratik faydasÄ±nÄ±
   ciddi kÄ±sÄ±tlayan bir bug). Bildirim kaydÄ± artÄ±k sektÃ¶r kontrolÃ¼nden Ã¶nce, `upsert` ile (update
   deÄŸil â€” satÄ±r yoksa update sessizce hiÃ§bir ÅŸey yapmÄ±yordu) ayrÄ± kaydediliyor. Yerel sunucuda
   gerÃ§ek production Supabase'e karÅŸÄ± test edildi, Ã§alÄ±ÅŸÄ±yor. Commit `ad993c9`, pull yeterli.
4. **âœ… DÃœZELTÄ°LDÄ° â€” `bildirimler.html` `aksiyon_url` hiÃ§ kullanÄ±lmÄ±yordu:** DB sorgusu bu kolonu
   SEÃ‡MÄ°YORDU bile â€” `idare_bildirim.py`/`rakip_bildirim.py`'nin yazdÄ±ÄŸÄ± link tamamen kayboluyordu,
   kurum/rakip bildirimleri tÄ±klanamaz kalÄ±yordu. AyrÄ±ca `kurum_takip`/`rakip_hareketi` iÃ§in ikon
   yoktu (ğŸ””'ye dÃ¼ÅŸÃ¼yordu) â€” artÄ±k ğŸ›ï¸/ğŸ†. Commit `94b7b87`.
5. **âœ… EKLENDÄ° â€” `dogrudan-temin.html`'de idare adÄ± artÄ±k Kurum Analizi'ne link veriyor** (Ã¶nceden
   dÃ¼z metindi). Commit `70770d0`.
6. **âœ… EKLENDÄ° â€” Sidebar bildirim rozeti artÄ±k gerÃ§ek okunmamÄ±ÅŸ sayÄ±sÄ±:** tÃ¼m sayfalarda sabit "4"
   hardcode edilmiÅŸti. `js/bildirim-sayaci.js` (18 sayfaya eklendi) canlÄ± sayÄ±yÄ± gÃ¶steriyor, 0 ise
   gizliyor. Commit `52947c9`.
7. **âœ… EKLENDÄ° â€” `takipte.html`'e "Takip EttiÄŸim Kurumlar/Firmalar" bÃ¶lÃ¼mleri:** bugÃ¼ne kadar
   kullanÄ±cÄ±nÄ±n kurum/firma takiplerini gÃ¶rebileceÄŸi/yÃ¶netebileceÄŸi merkezi bir yer yoktu. ArtÄ±k
   liste + "Takibi BÄ±rak" butonu var. `takip_idareler` dÃ¼zelene kadar o bÃ¶lÃ¼m zarifÃ§e boÅŸ gÃ¶rÃ¼nÃ¼r
   (crash yok). Commit `37c3700`.
8. **Genel QA taramasÄ±:** ~12 sayfa (idareler, firmalar, sektorler, rekabet-analizi, uyumluluk,
   dokumanlar, sonuclananlar, takipte, dashboard, ihaleler, ihale-detay, profil, kik-kararlar)
   konsol hatasÄ± iÃ§in tek tek ziyaret edildi â€” hepsi temiz. EKAP linki (bugÃ¼nkÃ¼ erken dÃ¼zeltme)
   ve eÅŸik_katsayÄ± verisi (diÄŸer oturumun regex dÃ¼zeltmesi, 784 kayÄ±t dolu) canlÄ±da doÄŸrulandÄ±.
   Email onay akÄ±ÅŸÄ± dÃ¼zeltmesi (diÄŸer oturum) de canlÄ±da doÄŸrulandÄ± â€” bu ikisi zaten pull edilmiÅŸti.
9. **âœ… EKLENDÄ° (aynÄ± oturumda hemen yapÄ±ldÄ±) â€” Kurum Analizi â†” DoÄŸrudan Temin Ã§apraz linki:**
   `dogrudan-temin.html` artÄ±k `?idare=X` okuyup arama kutusunu dolduruyor; `kurum-analiz.html`'e
   bunu kullanan "âš¡ DoÄŸrudan Temin KayÄ±tlarÄ±" butonu eklendi. Yerel sunucuda test edildi (Erciyes
   Ãœniversitesi â†’ 9 duyuru doÄŸru filtrelendi). Commit `002b592`.

### ğŸ‘¤ SENÄ°N YAPMAN GEREKEN

**1. Backfill'i arada bir kontrol et (otomatik duracak, ama ilerlemeyi gÃ¶rmek istersen):**
```bash
ssh -i ~/.ssh/ihale_oracle root@195.85.207.126
tail -20 /opt/ihale-platform/logs/dt_backfill.log   # buffering yÃ¼zÃ¼nden gecikmeli gÃ¶rÃ¼nebilir
```
Kesintiye uÄŸrarsa (VDS restart vb.) aynÄ± komutla (`nohup python ekap_dogrudan_temin_scraper.py
--backfill --max-pages 100000 >> ../logs/dt_backfill.log 2>&1 &`) kaldÄ±ÄŸÄ± yerden devam eder.

âš ï¸ **DÄ°KKAT (12 Tem'de birkaÃ§ kez yaÅŸandÄ±):** SSH baÄŸlantÄ±sÄ± sÄ±k kopuyor gibi gÃ¶rÃ¼nÃ¼yor. Koptuktan
sonra yanlÄ±ÅŸlÄ±kla yerel Windows `cmd.exe`'de (`C:\Users\dncla>`) komut Ã§alÄ±ÅŸtÄ±rmaya devam edildi â€”
`grep`/`nohup` orada Ã§alÄ±ÅŸmaz. Her komuttan Ã¶nce prompt'un gerÃ§ekten `root@ubuntu:...#` (veya
`(venv) root@ubuntu:...#`) olduÄŸunu doÄŸrula, gerekirse SSH'Ä± yeniden baÅŸlat.

**2. Proxy YOK (12 Tem'de doÄŸrulandÄ± â€” `grep` sonucu `0`):** Webshare proxy `.env`'de tanÄ±mlÄ±
deÄŸil. KullanÄ±cÄ± "sanÄ±rÄ±m satÄ±n almÄ±ÅŸtÄ±k" demiÅŸti ama sistemde iz yok â€” ya hiÃ§ alÄ±nmadÄ± ya da
alÄ±ndÄ±ysa `.env`'e hiÃ§ eklenmedi. **NetleÅŸtirilmesi gereken:** Webshare hesabÄ± gerÃ§ekten var mÄ±
(varsa sadece kullanÄ±cÄ± adÄ±/ÅŸifreyi `.env`'e ekle â€” `PROXY_KULLANICI`/`PROXY_SIFRE`), yoksa yeni
kayÄ±t mÄ± olunacak (~$10/ay, bkz. `backend/proxy_config.py` Ã¼stÃ¼ndeki yorum). Bu netleÅŸmeden
rekabetÃ§i ihalelerin (ilanlar, ayrÄ± sistem) derin backfill'i baÅŸlatÄ±lamaz â€” DoÄŸrudan Temin backfill'i
buna gerek duymuyor, o zaten proxy'siz sorunsuz Ã§alÄ±ÅŸÄ±yor.

**3. Kupon Ã¼retmek iÃ§in (iyzico gelmeden Ã¶nce tanÄ±dÄ±k firmalara Ã¼cretsiz Pro/Kurumsal vermek):**
```bash
cd /opt/ihale-platform/backend && source venv/bin/activate
python kupon_olustur.py --plan standart --ay 3 --adet 5 --aciklama "Beta test firmalarÄ±"
```
`--plan` (`standart`|`kurumsal`), `--ay` (`1`|`3`|`6`|`12`), `--adet` kaÃ§ kod Ã¼retileceÄŸi. **UÃ§tan
uca doÄŸrulandÄ± (11 Tem):** kod Ã¼retildi, kullanÄ±ldÄ±, plan gerÃ§ekten Standart'a geÃ§ti, ikinci
kullanÄ±m doÄŸru reddedildi.

**4. Bekleyen (Ã¶nceki oturumlardan, hÃ¢lÃ¢ aÃ§Ä±k):**
   - Ä°yzico entegrasyonu **kullanÄ±cÄ± kararÄ±yla en sona bÄ±rakÄ±ldÄ±** â€” lisans anlaÅŸmasÄ± netleÅŸince
     yapÄ±lacak. O zamana kadar kupon sistemi Ã¼cretsiz test eriÅŸimi karÅŸÄ±lÄ±yor.
   - **Karar gerektiren:** Faz D3 (semantik eÅŸleÅŸme) ~14 bin mevcut aktif ilanÄ± geriye dÃ¶nÃ¼k embed'lemiyor
     (bilinÃ§li â€” Gemini API maliyeti). Gece baÅŸÄ±na 300 ile mi devam, yoksa `ilan_embed_uret.py --max`
     deÄŸerini bÃ¼yÃ¼tÃ¼p hÄ±zlandÄ±rmak mÄ± istersin?
   - **SMS bildirimi YOK:** Kurum takibi VE rakip (firma) takibi ÅŸu an sadece e-posta + uygulama-iÃ§i
     bildirim gÃ¶nderiyor. SMS istenirse ayrÄ± bir saÄŸlayÄ±cÄ± entegrasyonu gerekir (Netgsm/Twilio gibi)
     â€” henÃ¼z konuÅŸulmadÄ±, tekrar sorulacak olursa bu netleÅŸmeli.

### ğŸ¤– AI'IN (Claude'un) SIRADA YAPACAÄI â€” sen "devam" dediÄŸinde ya da yeni bir yÃ¶n verdiÄŸinde

1. âœ… (14 Tem) DT backfill ilerlemesi kontrol edildi + yeniden baÅŸlatÄ±ldÄ± (2.680â†’5.247, hÃ¢lÃ¢ akÄ±yor).
2. Kurum takibi VE rakip takibi e-postasÄ±nÄ±n gerÃ§ek kullanÄ±cÄ±yla uÃ§tan uca Ã§alÄ±ÅŸtÄ±ÄŸÄ±nÄ± doÄŸrula â€”
   **hÃ¢lÃ¢ yapÄ±lamadÄ±, giriÅŸ gerektiriyor** (AI parola giremez, gÃ¼venlik kuralÄ±). KullanÄ±cÄ± kendi
   hesabÄ±yla "Kurumu Takip Et" butonuna basÄ±p e-posta/bildirim geldiÄŸini teyit etmeli.
3. Proxy netleÅŸince: varsa rekabetÃ§i ihaleler iÃ§in hÄ±zlandÄ±rÄ±lmÄ±ÅŸ backfill'i baÅŸlat
   (`ekap_sonuc_backfill.py --max-pages` bÃ¼yÃ¼k bir deÄŸerle); yoksa proxy alÄ±m sÃ¼recini konuÅŸ.
4. âœ… (14 Tem) `rakip_bildirim.py` VE `idare_bildirim.py` artÄ±k ikisi de cron'da (ikincisi hiÃ§
   yoktu, bu oturumda eklendi) â€” ilk gece turunda gerÃ§ek veriyle doÄŸrulanmalÄ± (log kontrolÃ¼).
5. âœ… (14 Tem) KÄ°K Kurul KararlarÄ± canlÄ±da doÄŸrulandÄ± (97 karar, tarayÄ±cÄ±da test edildi).
6. Sonraki plan maddeleri (dÃ¼ÅŸÃ¼k Ã¶ncelik, net yÃ¶n verirsen): "SÃ¶zleÅŸme Listesi" (madde 7, aÅŸaÄŸÄ±da),
   D3'Ã¼n eski-ilan backfill'i (karar sonrasÄ±).
7. KÃ¼Ã§Ã¼k/dÃ¼ÅŸÃ¼k Ã¶ncelik: `ihale-api` systemd servisi 11 Tem'den beri restart edilmedi, o tarihten
   sonraki tek deÄŸiÅŸiklik (86201d1, marka adÄ± string'leri) canlÄ±da deÄŸil â€” fonksiyonel risk yok,
   istenirse `systemctl restart ihale-api` ile senkronize edilebilir (ayrÄ± onay gerekir).

**12 Tem oturumu (devam):**
- âœ… **YENÄ° Ã–ZELLÄ°K â€” AÃ§Ä±k (GÃ¼ndÃ¼z) Tema:** kullanÄ±cÄ± isteÄŸi ("herkes siyah modu sevmez"). Mevcut CSS
  deÄŸiÅŸken sistemi Ã¼zerine `[data-theme="light"]` override + `js/theme.js` (saÄŸ altta geÃ§iÅŸ dÃ¼ÄŸmesi,
  localStorage kalÄ±cÄ±, varsayÄ±lan koyu). 20 sayfaya eklendi, hardcoded `rgba(255,255,255,X)` kullanÄ±mlarÄ±
  (~93 yer) `var(--overlay-rgb)`'ye Ã§evrildi ki temayla uyumlu olsun. Kapsam dÄ±ÅŸÄ±: hakkimizda/iletisim/
  kvkk/mesafeli-satis (kendi ayrÄ± `:root`'larÄ± var, dokunulmadÄ±) + 1715 firma SEO sayfasÄ±. Yol boyu
  gerÃ§ek bir bug bulundu+dÃ¼zeltildi: `fiyatlandirma_odeme_bolumu.html`'deki kupon kutusu `var(--card, #fff)`
  (hiÃ§ var olmayan bir deÄŸiÅŸken) yÃ¼zÃ¼nden hep beyaz zemine dÃ¼ÅŸÃ¼yordu, Ã¼stÃ¼ndeki beyaz baÅŸlÄ±k gÃ¶rÃ¼nmezdi
  (canlÄ±da doÄŸrulandÄ±, gerÃ§ek bug). Commit `6296971`.
- âœ… **YENÄ° Ã–ZELLÄ°K â€” DoÄŸrudan Temin Scraper (kullanÄ±cÄ±nÄ±n dÃ¼zeltmesiyle):** AI Ã¶nce "17 Temmuz'u
  bekleyelim" demiÅŸti ama kullanÄ±cÄ± haklÄ± Ã§Ä±ktÄ± â€” DoÄŸrudan Temin ilanlarÄ± EKAP'ta ZATEN yayÄ±nlanÄ±yor.
  ekapv2'deki "yeni pilot" (17 Tem, henÃ¼z boÅŸ) ile KARIÅTIRILMAMASI gereken, EKAP'Ä±n eski (legacy)
  domaininde 2022'den beri Ã§alÄ±ÅŸan, herkese aÃ§Ä±k, oturumsuz bir sistem bulundu:
  `ekap.kik.gov.tr/EKAP/Ortak/YeniIhaleAramaData.ashx?metot=dtAra`. Alan eÅŸlemesi EKAP'Ä±n kendi
  `/metot=dtEnum`'undan doÄŸrulandÄ± (4 tÃ¼r, 5 durum, 81 il), canlÄ± veriyle test edildi (3 sayfa/384
  kayÄ±t). Yeni tablo `dogrudan_temin_ilanlari` + `ekap_dogrudan_temin_scraper.py` (gece modu: her
  zaman 1. sayfadan baÅŸlar Ã§Ã¼nkÃ¼ sÄ±ralama en-yeniden-en-eskiye; `--backfill` modu: checkpoint'li
  derin tarama, kullanÄ±cÄ± kararÄ±yla ayrÄ± Ã§alÄ±ÅŸtÄ±rÄ±lÄ±r). SSL iÃ§in `ekap_sonuc_backfill.py`'deki aynÄ±
  zayÄ±flatÄ±lmÄ±ÅŸ TLS context gerekti (kullanÄ±cÄ± onayÄ±yla, EKAP eski cipher kullanÄ±yor). Commit
  `cade8e0`, deploy `backend/deploy_12tem_dogrudan_temin.sh` ile.
- âœ… **YENÄ° Ã–ZELLÄ°K â€” Kurum (Ä°dare) Takibi:** kullanÄ±cÄ± fikri ("kurum da takip edilebilsin, yeni ihale
  yayÄ±nlayÄ±nca mail/SMS gitsin"). `takip_firmalar` (Faz E1) ile birebir aynÄ± desen: `kurum-analiz.html`'e
  "Kurumu Takip Et" butonu, `idare_bildirim.py` (gece cron, `notify.py`'nin e-posta altyapÄ±sÄ±nÄ± reuse
  eder) yeni ilan â†’ anlÄ±k bildirim + e-posta (deadline Ã¶zeti gibi ertesi gÃ¼ne ertelenmiyor, zaman-hassas).
  SMS YOK (â†‘). Commit `b88b3bc`, deploy `backend/deploy_12tem_kurum_takibi.sh` ile (â†‘).
- âœ… **YENÄ° Ã–ZELLÄ°K â€” Rakip (Firma) Takibine E-posta:** kullanÄ±cÄ± isteÄŸi ("aynÄ±sÄ±nÄ± firma takibinde
  de yapalÄ±m"). `rakip_bildirim.py` artÄ±k takip edilen firma yeni ihale kazanÄ±nca sadece bildirimler
  tablosuna yazmÄ±yor, `idare_bildirim.py` ile aynÄ± desende `bildirim_email` aÃ§Ä±k kullanÄ±cÄ±lara anlÄ±k
  e-posta da gÃ¶nderiyor (birden fazla kazanÄ±m tek e-postada gruplanÄ±yor). SMS YOK (â†‘). Commit `a0a717a`.
- âœ… Marka rename script'inin kaÃ§Ä±rdÄ±ÄŸÄ± 2 e-posta ÅŸablonu logosu (notify.py, bulten_gonder.py â€”
  `<span style="...">` iÃ§erdikleri iÃ§in ilk taramadan kaÃ§mÄ±ÅŸlardÄ±) dÃ¼zeltildi, commit `c6c6a1d`.
- âœ… Kupon sistemi VDS'te uÃ§tan uca doÄŸrulandÄ± (gerÃ§ek kupon Ã¼retildi/kullanÄ±ldÄ±, plan deÄŸiÅŸti, tekrar kullanÄ±m reddedildi).
- âœ… **Site genelinde marka adÄ± Ä°halePlatform â†’ Ä°haleGlobal** (1735 dosya: tÃ¼m sayfalar + 1715 Ã¼retilmiÅŸ
  firma SEO sayfasÄ± + `firma_sayfa_uret.py` Ã¼reteÃ§ + API/OpenAPI baÅŸlÄ±ÄŸÄ± + e-posta ÅŸablonlarÄ±). Mekanik
  toplu script ile, commit `86201d1`.
- âœ… **EKAP link bug'Ä± dÃ¼zeltildi:** `ihale-detay.html` (ekapLink) ve `dokumanlar.html`, DoÄŸrudan Temin
  ihalelerini yanlÄ±ÅŸlÄ±kla normal `ekap/search`'e yÃ¶nlendiriyordu â€” artÄ±k `usul`'e gÃ¶re `ekap/search` vs
  `ekap-dt/search` arasÄ±nda doÄŸru ayrÄ±m yapÄ±yor (commit `e5330e9`). Not: ÅŸu an DB'de hiÃ§ DoÄŸrudan Temin
  kaydÄ± olmadÄ±ÄŸÄ± iÃ§in pratik etkisi henÃ¼z yok.
- ğŸ” **AraÅŸtÄ±rma â€” EKAP deep-link (IKN'ye Ã¶zel tek-tÄ±k link):** Teknik olarak imkansÄ±z olduÄŸu doÄŸrulandÄ±
  (Angular SPA, filtre state URL'e hiÃ§ yansÄ±mÄ±yor â€” test edildi, `/ekap/search` URL'i hep sabit kaldÄ±).
  Ama bonus bulgu: EKAP'Ä±n ana arama kutusu IKN'yi zaten direkt tanÄ±yor (yapÄ±ÅŸtÄ±r+Enter â†’ tek sonuÃ§),
  mevcut "EKAP'ta Ara" akÄ±ÅŸÄ± zaten yeterince basit. Konu kapatÄ±ldÄ±.
- ~~ğŸ” AraÅŸtÄ±rma â€” DoÄŸrudan Temin scraper'Ä±: 17 Temmuz'u bekle~~ **DÃœZELTÄ°LDÄ°, bkz. yukarÄ±daki "YENÄ°
  Ã–ZELLÄ°K" maddesi.** Ä°lk bulgu (sadece `/b_ihalearama/api/Ihale/GetListByParameters` Ã§aÄŸrÄ±ldÄ±ÄŸÄ±, DT'nin
  ayrÄ± modÃ¼l olduÄŸu) doÄŸruydu, ama "17 Temmuz'u bekle" tavsiyesi YANLIÅTI â€” kullanÄ±cÄ± dÃ¼zeltti, gerÃ§ek
  ve zaten canlÄ± bir sistem (`ekap.kik.gov.tr`, 2022'den beri) bulundu ve scraper'Ä± yazÄ±ldÄ± (â†‘).
- ğŸ“Š **Backfill matematiÄŸi:** `ekap_sonuc_backfill.py` gece 50 sayfa ile ~AÄŸu 2025'e kadar gelmiÅŸ ama bu
  hÄ±zla 2003'e ulaÅŸmak ~2-3,5 yÄ±l sÃ¼rer â€” gerÃ§ek backfill iÃ§in proxy + hÄ±zlandÄ±rÄ±lmÄ±ÅŸ tek seferlik koÅŸu
  ÅŸart, mevcut pasif gece temposu yeterli deÄŸil.
- ğŸ“Œ **KalÄ±cÄ± talimat eklendi:** kullanÄ±cÄ± YAPILACAKLAR.md'nin her oturumda otomatik gÃ¼ncellenmesini
  istedi, hatÄ±rlatmaya gerek yok (hafÄ±za: `yapilacaklar-auto-update`).

---

> Son gÃ¼ncelleme: 10 Temmuz 2026 (Sonnet oturumu devamÄ± #2 â€” Faz C4 tamamlandÄ±, prod-yazma sÄ±nÄ±rlarÄ±
> netleÅŸti â†’ en alttaki "ğŸ“ SON DURUM (10 Tem 2026, otonom oturum devamÄ± â€” C4 + prod-yazma sÄ±nÄ±rÄ±)"
> bÃ¶lÃ¼mÃ¼ne bak. Ã–nceki oturum notu: "3 gÃ¼n iÃ§inde canlÄ±ya al" dedi ve otonom yetki verdi â€” 3 bekleyen
> madde + KÃ–K NEDEN BULUNAN GERÃ‡EK BUG Ã§Ã¶zÃ¼ldÃ¼, Render baÄŸÄ±mlÄ±lÄ±ÄŸÄ± tamamen kaldÄ±rÄ±ldÄ±, geniÅŸ tarihsel
> backfill baÅŸlatÄ±ldÄ±, bkz. "ğŸ“ SON DURUM (10 Tem, otonom launch oturumu)")
> Bu dosya, Code modunda kodlama yaparken referans alÄ±nacak. Her madde mÃ¼mkÃ¼n olduÄŸunca net ve uygulanabilir yazÄ±ldÄ±.
> 29 Haz 2026: **tendermeister.com** ve **ihaleciler.com** canlÄ± olarak detaylÄ± gezildi; rekabet/Ã¶zellik-aÃ§Ä±ÄŸÄ± analizi en alta "ğŸ†š REKABET ANALÄ°ZÄ°" bÃ¶lÃ¼mÃ¼ne eklendi (Ã–ncelik 9). Ã–nce o bÃ¶lÃ¼mÃ¼ oku.

---

## ğŸ“Œ KALICI Ã‡ALIÅMA TALÄ°MATI (HER YENÄ° AI OTURUMU BUNU UYGULAR)

> Bu bÃ¶lÃ¼m, projede Ã§alÄ±ÅŸan her yapay zekanÄ±n (Claude/Gemini/diÄŸer) uymasÄ± gereken
> daimi kuraldÄ±r. KullanÄ±cÄ± her seferinde tekrar sÃ¶ylemek zorunda kalmasÄ±n diye buraya yazÄ±ldÄ±.

1. **Bu dosyayÄ± sÃ¼rekli gÃ¼ncel tut.** Bir madde Ã¼zerinde Ã§alÄ±ÅŸtÄ±ktan sonra, ne yaptÄ±ÄŸÄ±nÄ±
   ilgili maddenin altÄ±na Ã¶zetle (âœ…/ğŸŸ¡/âš ï¸ durum iÅŸareti + kÄ±sa aÃ§Ä±klama + dokunulan dosyalar).
   TamamlananlarÄ± "TAMAMLANDI", kÄ±smi olanlarÄ± "BÃœYÃœK KISMI TAMAM" gibi iÅŸaretle.
2. **Tavsiye ve Ã¶ngÃ¶rÃ¼lerini ekle.** Ã‡alÄ±ÅŸÄ±rken fark ettiÄŸin iyileÅŸtirme, risk, teknik borÃ§
   veya gelecekte yapÄ±lmasÄ± gerekeni uygun baÅŸlÄ±k altÄ±na (ya da "GELECEK / FÄ°KÄ°RLER" bÃ¶lÃ¼mÃ¼ne) yaz.
3. **KullanÄ±cÄ±nÄ±n ileriye dÃ¶nÃ¼k isteklerini otomatik buraya iÅŸle.** KullanÄ±cÄ± "ÅŸunu da isterim",
   "ileride ÅŸÃ¶yle olsun" derse, onu beklemeden bu dosyaya uygun maddeye/bÃ¶lÃ¼me ekle.
4. **Ã–nce Ã¶ncelik sÄ±rasÄ±na bak** (en altta "Ã–nerilen SÄ±ra"). Aksi belirtilmedikÃ§e o sÄ±rayÄ± izle.
5. **Her Ã¶zellik sonrasÄ± doÄŸrula** (mÃ¼mkÃ¼nse tarayÄ±cÄ±da/Supabase'e karÅŸÄ± test) ve commit mesajÄ±nda ne yaptÄ±ÄŸÄ±nÄ± aÃ§Ä±kla.

---

## ğŸš€ CANLIYA ALMA Ä°LERLEMESÄ° (5 Tem 2026)

**âœ… Ã‡Ã¶zÃ¼lenler:**
- **Anasayfa haritasÄ± prod'da bozuktu** â†’ eksik `data/turkey-provinces.geojson` commit'lendi. AyrÄ±ca il sayÄ±mÄ± 13 istek yerine tek RPC'ye taÅŸÄ±ndÄ± (`backend/migration_il_sayim_rpc.sql` â€” Supabase'de Ã§alÄ±ÅŸtÄ±r; fallback var).
- **Dashboard'a TÃ¼rkiye haritasÄ± eklendi** (giriÅŸ sonrasÄ± yoktu) â†’ `js/harita.js` (yeniden kullanÄ±labilir), ile tÄ±klayÄ±nca `ihaleler?il=X`.
- **3 UX bug'Ä±:** (1) "EKAP'ta GÃ¶rÃ¼ntÃ¼le" 406 hata â†’ Ã§alÄ±ÅŸan public arama sayfasÄ± ("EKAP'ta Ara"); (2) AI analiz kutusundaki `python analiz_runner.py` geliÅŸtirici metni â†’ "Teklif HazÄ±rla" CTA; (3) Dashboardâ†’Kurum Analizi "parametre eksik" â†’ Ä°dareler Dizini'ne yÃ¶nlendirme.
- **ğŸ”´ GECE CRON'U Ã‡Ã–KMÃœÅTÃœ (4 gÃ¼n 0 kayÄ±t)** â†’ kÃ¶k neden: `upsert(ignore_duplicates=True)` sahte supabase wrapper'Ä±nda desteklenmiyordu, her yazma sessizce TypeError. Wrapper dÃ¼zeltildi (commit 5e5a08e). Cron yarÄ±ndan itibaren tekrar Ã§alÄ±ÅŸÄ±r. BugÃ¼nkÃ¼ veri elle tam turla tazelendi.

**â³ Devam eden / planlanan:**
- **TÃ¼m geÃ§miÅŸ (2003+) backfill** (kullanÄ±cÄ± kararÄ±): EKAP'Ä±n sonuÃ§lanmÄ±ÅŸ listesi (~1.68M) taranacak â†’ milyonlarca kayÄ±t. GEREKSÄ°NÄ°M: (a) Webshare proxy (boÅŸ â€” IP ban riski), ~~(b) Supabase plan yÃ¼kseltme (free tier milyonlarÄ± kaldÄ±rmaz)~~ **ARTIK GEÃ‡ERSÄ°Z (11 Tem 2026): VDS'e taÅŸÄ±nalÄ± beri self-hosted Supabase kullanÄ±yoruz, plan/satÄ±r limiti yok, disk bol â€” bu madde sadece proxy'ye baÄŸlÄ±.** (c) ayrÄ± checkpoint'li backfill workflow'u (`ekap_sonuc_backfill.py` temeli var, gece cron'unda 50 sayfa/gece ilerliyor, 11 Tem itibarÄ±yla ~AÄŸu 2025'e kadar gitmiÅŸ). Firma/yÃ¼klenici verisi bunun Ã§Ä±ktÄ±sÄ± olarak gelecek.
- Cron'un GitHub Actions'ta gerÃ§ekten yeÅŸil dÃ¶ndÃ¼ÄŸÃ¼nÃ¼ ilk gece sonrasÄ± doÄŸrula (`olusturulma` bugÃ¼ne yakÄ±n mÄ±).

---

## ğŸ–¥ï¸ BÃœYÃœK PLAN â€” TEK VDS'E TAÅIMA (5 Tem 2026 Â· Faz 2-4 TAMAMLANDI 6 Tem 2026)

> **Bu bÃ¶lÃ¼m bir sonraki oturum/AI iÃ§in devir notudur.** KullanÄ±cÄ± sistemi tek bir sunucuda
> (VDS) birleÅŸtirmeye karar verdi. AÅŸaÄŸÄ±daki karar/gerekÃ§e/plan aynen sÃ¼rdÃ¼rÃ¼lecek.

### âœ… TAMAMLANAN (6 Tem 2026) â€” Sistem VDS'te tam Ã§alÄ±ÅŸÄ±yor: http://195.85.207.126
**VDS:** Datacasa Premium (BaÅŸakÅŸehir/Ä°stanbul, KVM, TÃ¼rkiye âœ“), IP `195.85.207.126`, Ubuntu 24.04, root.
**EriÅŸim:** `ssh -i ~/.ssh/ihale_oracle root@195.85.207.126` (anahtar authorized_keys'te, ÅŸifresiz).

- âœ… **Faz 2 â€” Sunucu:** Docker + UFW (22/80/443/8000/3000) + SSH key. Self-hosted Supabase
  (`/opt/supabase/docker`, 11 container healthy, PG17, JWT/ÅŸifreler generate-keys.sh ile).
- âœ… **Faz 3 â€” Uygulamalar:** nginx tek-domain proxy (frontend + `/rest|/auth|/storage|/realtime|/functions`â†’Kong:8000 + `/api/`â†’FastAPI:8080, uzantÄ±sÄ±z URL `try_files`). FastAPI systemd (`ihale-api`, 127.0.0.1:8080). Scraper cron (02:00 UTC â†’ `/opt/ihale-platform/backend/run_scraper.sh`). Repo: `/opt/ihale-platform`. Python venv **yalÄ±n kurulum** (sÃ¼rÃ¼msÃ¼z â€” eski-pinned requirements backtracking yapÄ±yordu; gerÃ§ek `supabase` paketi gereksiz Ã§Ã¼nkÃ¼ sahte wrapper httpx-tabanlÄ±).
- âœ… **Faz 4 â€” Veri taÅŸÄ±ma:** pg_dump/restore ile **13.535 ilan + 4 auth.users + identities + profiller + RLS/politikalar** taÅŸÄ±ndÄ±. il_sayim RPC eklendi. anon/authenticated GRANT'leri elle verildi (anon SELECT, authenticated yazma; RLS satÄ±r korur). FK'ler (auth.users) geri eklendi. **Scraper testi: EKAP'tan 12.052 canlÄ± ihale yazdÄ± âœ“.** Frontend URL/anon-key VDS kopyasÄ±nda yerele Ã§evrildi (repoya DEÄÄ°L â€” canlÄ± Cloudflare bozulmasÄ±n).
- ğŸ› Yol boyu dÃ¼zeltilen: worker.py stale import (`tum_sonuclari_cek`) api.py'yi Ã§Ã¶kertiyordu â†’ commit 9ea9ca5.

**KRÄ°TÄ°K TEKNÄ°K NOTLAR (sonraki oturum iÃ§in):**
- Supabase direct-conn **IPv6-only**, VDS'in IPv6'sÄ± yok â†’ pg_dump/restore **pooler** Ã¼zerinden: `aws-0-eu-west-3.pooler.supabase.com:5432`, user `postgres.lpgelwfoarhouollhwur`.
- PG sÃ¼rÃ¼mÃ¼ eÅŸleÅŸmeli (managed=self-hosted=17); client PGDG deposundan `postgresql-client-17`.
- Managed Postgres ÅŸifresi sÄ±fÄ±rlandÄ± (Sifre.123123!.) â€” bu SADECE direct DB conn iÃ§indir, app'ler API-key kullanÄ±r, kopmaz.
- Gece scraper `main()` **playwright'siz** (httpx + crypto headers); chromium sadece aÄŸÄ±r belge-indirme turu.

### ğŸ”² KALAN â€” Faz 5-6 (kullanÄ±cÄ± TEST edip "yayÄ±na al" deyince)
- [x] **KullanÄ±cÄ± testi (8 Tem 2026, AI tarayÄ±cÄ±yla uÃ§tan uca):** ana sayfa (14.060 aktif, canlÄ± KPI), harita choropleth + ilâ†’ihaleler yÃ¶nlendirmesi (`?il=ANKARA`), ihaleler listesi/filtre/kart, ihale detay (KPI+uyum+AI sekmesi+benzer ihaleler), giriÅŸ (taÅŸÄ±nan session geÃ§erli â€” "Merhaba, info"), dashboard tÃ¼m widget'lar, canlÄ± arama ("temizlik"â†’77) â€” **hepsi Ã§alÄ±ÅŸÄ±yor, konsol temiz.** 2 kÃ¼Ã§Ã¼k bug bulundu+dÃ¼zeltildi (â†“).
- [x] **GÃ¼venlik doÄŸrulamasÄ± VDS'te (8 Tem 2026, SSH):** devir notundaki "2 kritik aÃ§Ä±k" **ikisi de zaten gÃ¼venli.** (1) Kredi RLS: `kullanici_krediler`+`kredi_hareketleri`'nde YALNIZCA `SELECT` policy var (yazma policy'si yok), RLS aÃ§Ä±k (`relrowsecurity=t`) â†’ bedava-kredi/Ä°yzico-bypass aÃ§Ä±ÄŸÄ± yok, `rls_fix_kredi.sql` GEREKMÄ°YOR. (2) E-posta: `GOTRUE_MAILER_AUTOCONFIRM=false` â†’ onaysÄ±z giriÅŸ engelli.
- [x] **SMTP kuruldu + doÄŸrulandÄ± (8 Tem 2026):** KullanÄ±cÄ± Resend'e kaydoldu, gÃ¶nderim key'i verdi. `/opt/supabase/docker/.env`'de SMTP ayarlandÄ±: `SMTP_HOST=smtp.resend.com`, `SMTP_PORT=465`, `SMTP_USER=resend`, `SMTP_PASS=<resend key>`, `SMTP_SENDER_NAME=IhaleGlobal`, `SMTP_ADMIN_EMAIL=onboarding@resend.dev` (test gÃ¶ndericisi). `.env.bak.<ts>` yedeÄŸi alÄ±ndÄ±. `docker compose up -d auth` ile yenilendi. Test: `farukdinc890@gmail.com` ile signup â†’ HTTP 200, `confirmation_sent_at` set, GoTrue loglarÄ±nda SMTP hatasÄ± YOK, istek 3.4sn (gerÃ§ek gÃ¶nderim) â†’ **boru hattÄ± Ã§alÄ±ÅŸÄ±yor.**
  - âš ï¸ **Resend key "sadece-gÃ¶nderim" yetkili** â€” domain API'si (`POST /domains`) 401 verir; domain doÄŸrulamasÄ± **panelden** yapÄ±lmalÄ±.
  - âš ï¸ **Test gÃ¶ndericisi kÄ±sÄ±tÄ±:** domain doÄŸrulanana kadar `onboarding@resend.dev` YALNIZCA kullanÄ±cÄ±nÄ±n Resend hesabÄ± e-postasÄ±na teslim eder. GerÃ§ek kullanÄ±cÄ±lara mail iÃ§in domain doÄŸrulama ÅART (â†“ handoff).
  - â„¹ï¸ `farukdinc890@gmail.com` hesabÄ± admin ile onaylandÄ± (`email_confirm:true`), giriÅŸ test edildi (token 200). GeÃ§ici parola `GeciciTest123!` â€” kullanÄ±cÄ± deÄŸiÅŸtirmeli.
- [x] **2 dashboard bug'Ä± dÃ¼zeltildi + deploy (commit b347ec3, main'e push):** (1) `durumBadge` teklif tarihi geÃ§miÅŸ kayda "â— AÃ§Ä±k" yerine "â— KapandÄ±" (ihaleler.html ile tutarlÄ±; 2010 tarihli ihaleler "AÃ§Ä±k" gÃ¶rÃ¼nÃ¼yordu). (2) `main-search` Enter â†’ `ihaleler?ara=...` tam listeye yÃ¶nlendirir.
- [ ] **Faz 6 â€” DNS + SSL cut-over** â†’ aÅŸaÄŸÄ±daki "DEVÄ°R" bloÄŸundaki adÄ±m adÄ±m plan.
- [x] **VDS saÄŸlÄ±k doÄŸrulandÄ± (8 Tem 2026):** cron `0 2 * * *` Ã§alÄ±ÅŸÄ±yor â€” bugÃ¼n 02:09'da 253 taze kayÄ±t yazdÄ± (toplam 14.060); disk %13 (19G/158G); FastAPI `ihale-api` active. VDS taÅŸÄ±manÄ±n asÄ±l amacÄ± (gÃ¼venilir cron) doÄŸrulandÄ±.
- [~] ğŸ› **BÄ°LDÄ°RÄ°M SERVÄ°SÄ° â€” notify.py KODU DÃœZELTÄ°LDÄ°, 2 adÄ±m kaldÄ± (8 Tem 2026):** notify.py eski managed ÅŸemasÄ±na gÃ¶re yazÄ±lmÄ±ÅŸtÄ±, 4 uyumsuzluk vardÄ±; **hepsi dÃ¼zeltildi ve VDS'e kopyalandÄ±** (paylaÅŸÄ±lan wrapper'a DOKUNULMADI): (1) `takip`/`user_id` â†’ `takipler`/`kullanici_id`; (2) `bildirim_kaydet` gerÃ§ek `bildirimler` ÅŸemasÄ±na uyduruldu (`kullanici_id`/`tur`/`icerik`/`okundu`/`aksiyon_url`; eski `user_id`/`tip`/`aciklama`/`email_gonderildi` kaldÄ±rÄ±ldÄ±); (3) `sb.auth.admin.list_users()` (sahte wrapper desteklemiyor) â†’ yeni `auth_email_map()` GoTrue admin REST'ini (`/auth/v1/admin/users`, service key) doÄŸrudan `requests` ile Ã§aÄŸÄ±rÄ±yor; (4) FROM_EMAIL/SITE_URL â†’ `ihaleglobal.com` (env-driven). **KALAN 2 ADIM (otonom yapÄ±lamadÄ± â€” prod-mutasyon gÃ¼venlik katmanÄ± aÃ§Ä±k onay ister):**
  - **(a) Migration uygula** (`backend/migration_bildirim_tercihleri.sql` hazÄ±r â€” profil'e `bildirim_email`/`bildirim_son_teklif`/`bildirim_gun_oncesi` ekler, additive/gÃ¼venli): `ssh ... "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_bildirim_tercihleri.sql` VEYA Supabase SQL Editor. Bu gelene kadar notify.py profil-sorgusunda (zararsÄ±z) log hatasÄ± verir.
  - **(b) RESEND key'i notify.py iÃ§in ekle:** VDS `/opt/ihale-platform/backend/.env`'e `RESEND_API_KEY=re_...` ekle (notify.py Resend HTTP API'sini ayrÄ± kullanÄ±r; ÅŸu an backend/.env'de yok). GÃ¶nderim yine domain doÄŸrulanÄ±nca (`noreply@ihaleglobal.com`) canlÄ± olur; o zamana dek `BILDIRIM_FROM_EMAIL=onboarding@resend.dev` test gÃ¶ndericisi.
  - **(c) Son parÃ§a â€” Profil UI:** `profil.html`'e bildirim tercih toggle'larÄ± (kullanÄ±cÄ± `bildirim_email`'i aÃ§sÄ±n). Bu + (a)+(b) + domain doÄŸrulama = bildirimler ilk kez canlÄ±. (UI bilerek otonom yapÄ±lmadÄ± â€” attended/opinionated deÄŸiÅŸiklik.)
- [x] ğŸ” **STATÄ°K BUG AVI â€” "yanlÄ±ÅŸ tablo/kolon adÄ±" sÄ±nÄ±fÄ± (8 Tem 2026):** notify.py'daki bug bir sÄ±nÄ±f Ã§Ä±ktÄ±; repo taranÄ±nca aynÄ± sÄ±nÄ±ftan 6 canlÄ± bug daha bulundu ve **dÃ¼zeltildi + push'landÄ±** (commit â†“). notify.py eski managed ÅŸemasÄ±na gÃ¶re yazÄ±lmÄ±ÅŸ birÃ§ok yer var:
  - ğŸ”´ **js/plan.js â€” GELÄ°R-KRÄ°TÄ°K:** `profil.plan` (var olmayan kolon) okuyordu â†’ **Ã¶deme yapan Pro kullanÄ±cÄ±lar her yerde 'free' gÃ¶rÃ¼nÃ¼yordu** (dashboard 10-ihale limiti, filtre kilitleri vs.). Plan aslÄ±nda `kullanici_krediler.plan`'da (payment.py:215-218 oraya yazar). DÃ¼zeltildi: `kullanici_krediler`'den okur + `plan_bitis` sÃ¼re kontrolÃ¼. *(False-Pro riski yok: sadece Ã¶deyen 'pro' olur.)*
  - ğŸ”´ **js/sidebar-user.js:** aynÄ± `profil.plan` hatasÄ± (select tÃ¼mden patlÄ±yordu â†’ firma adÄ± da kayboluyordu). DÃ¼zeltildi (firma_adi profil'den, plan kullanici_krediler'den).
  - **bildirimler.html:** DB bildirimleri yanlÄ±ÅŸ kolonlarla sorguluyordu (`tip/aciklama/okunmus/created_at/user_id` â†’ gerÃ§ek `tur/icerik/okundu/olusturulma/kullanici_id`) â†’ bildirimler hiÃ§ okunamÄ±yor/iÅŸaretlenemiyordu. DÃ¼zeltildi (okuma + 2 mark-as-read).
  - **teklif-olustur.html:** `kullanici_profiller.select('firma_adi, aktif_plan')` â€” `aktif_plan` yok â†’ select patlÄ±yor. DÃ¼zeltildi (aktif_plan kaldÄ±rÄ±ldÄ±, plan `Plan.getPlan()`'dan). NOT: 2 profil tablosu var â€” `profil` (tercih/filtre, key=user_id) ve `kullanici_profiller` (firma detayÄ±, key=id).
  - **backend/worker.py + backend/api.py:** bildirimler/takipler insert-update'lerinde `ihale_id`â†’`ilan_id`, `ihale_id`â†’`ilan_id` (takipler'de kolon `ilan_id`). DÃ¼zeltildi. âš ï¸ api.py VDS'te `ihale-api` olarak Ã§alÄ±ÅŸÄ±yor â†’ **yeni api.py'Ä±n VDS'e deploy'u gerek** (git pull/scp â€” frontend URL Ã§akÄ±ÅŸmasÄ± yok, backend dosyasÄ±).
  - âœ… **planDusur + teklif kaydetme ARTIK DÃœZELTÄ°LDÄ°** (bu ikisi burada eskiden "DÃœZELTÄ°LMEDÄ°" iÅŸaretliydi, ama commit `4fc8a29` â€” 8 Tem â€” ile Ã§oktan Ã§Ã¶zÃ¼lmÃ¼ÅŸ; 14 Tem'de fark edilip not temizlendi, aÅŸaÄŸÄ±daki satÄ±r 335'e bak).
- [~] **notify.py MÄ°GRATION UYGULANDI + TEMÄ°Z Ã‡ALIÅIYOR (8 Tem, aÃ§Ä±k yetkiyle):** `migration_bildirim_tercihleri.sql` VDS'te uygulandÄ± (profil'e 3 kolon). DÃ¼zeltilmiÅŸ notify.py VDS'te test edildi â†’ "0 kullanÄ±cÄ± â†’ 0/0 gÃ¶nderildi", **Ã§Ã¶kme yok** (gece hatasÄ± giderildi). KALAN: (a) VDS `backend/.env`'e `RESEND_API_KEY=re_...` ekle (gÃ¶nderim iÃ§in; 1 kullanÄ±cÄ± artÄ±k opt-in ama o gÃ¼n eÅŸiÄŸe giren ihalesi yoktu, bkz. 14 Tem notu â€” hÃ¢lÃ¢ eklenmedi), (b) `profil.html`'e bildirim tercih UI'Ä± (kullanÄ±cÄ± `bildirim_email` aÃ§sÄ±n), (c) domain doÄŸrulama â†’ gerÃ§ek gÃ¶nderim. ~~Managed'a da migration gerek~~ **ARTIK GEÃ‡ERSÄ°Z (10 Tem'de managed tamamen terk edildi, bkz. hafÄ±za `vds-managed-split`) â€” tek canlÄ± sistem VDS.**
- [x] **teklif kaydetme + planDusur DÃœZELTÄ°LDÄ° (commit 4fc8a29):** teklif insert ÅŸemaya uyduruldu (teklif_metni JSON); payment.py'a `/plan-iptal` endpoint + planDusur baÄŸlandÄ±. ~~planDusur FastAPI'ye gider (Render ÅŸimdi)~~ **ARTIK GEÃ‡ERSÄ°Z â€” Render 10 Tem'de tamamen kaldÄ±rÄ±ldÄ±, backend tek VDS'te `ihale-api` systemd servisi olarak Ã§alÄ±ÅŸÄ±yor.** Ã–deme akÄ±ÅŸÄ± hÃ¢lÃ¢ Supabase Edge Function `odeme-baslat` kullanÄ±yor â€” ideal: plan-iptal'i de edge function yap (dÃ¼ÅŸÃ¼k Ã¶ncelik).
- [~] ğŸŸ¢ **SONUÃ‡/FÄ°RMA VERÄ°SÄ° â€” PIPELINE Ã‡ALIÅIYOR, GERÃ‡EK VERÄ° AKIYOR (8 Tem, kullanÄ±cÄ± onayÄ±yla):** Firma/yÃ¼klenici tarafÄ± kuruldu ve **gerÃ§ek veri Ã§ekildi.** YapÄ±lanlar:
  - **Åema (TasarÄ±m B, additive):** `backend/migration_sonuc_B_kurulum.sql` VDS'e uygulandÄ± â€” `yukleniciler` + `scrape_log` tablolarÄ± + `ihale_sonuclari`'ya B kolonlarÄ± (drop YOK, eski 15 satÄ±r korundu) + `ilanlar_sonuc` view + anon/authenticated SELECT + RLS public-read + service_role GRANT.
  - **Wrapper:** `backend/supabase/__init__.py`'a `not_()` metodu eklendi (scraper `not.in` filtresi iÃ§in; additive â€” gece scraper'Ä± etkilenmedi).
  - **DOÄRU VERÄ° YOLU BULUNDU:** Ä°hale-bazlÄ± sonuÃ§ DETAY endpoint'leri (GetByIhaleIdSonucIlan vb.) **hepsi 404**. Ã‡alÄ±ÅŸan yol = **`ekap_sonuc_backfill.py`**: EKAP'Ä±n "Result Announcement Published" (durum kodu 15, **1.68M** kayÄ±t) listesini sayfalar, IKN'lerimizle eÅŸleÅŸenler iÃ§in `GetByIhaleIdIhaleDetay`'den kazanan/bedel/tenzilat Ã§eker â†’ `ihale_sonuclari`'ya **Design A** (`kazanan_firma`) yazar. (`ekap_sonuc_scraper.py` = Design B ama 404 endpoint'ler â†’ kullanÄ±lmÄ±yor.)
  - **TEST: `--reset --max-pages 25` â†’ 2500 sonuÃ§lanmÄ±ÅŸ tarandÄ±, 29 eÅŸleÅŸme, 20 gerÃ§ek sonuÃ§ yazÄ±ldÄ±** (toplam 35). Ã–rn: DEMÄ°R YAPI Ä°NÅAAT 2 iÅŸ/181M TL, EMAS DEMÄ°R Ã‡ELÄ°K 2 iÅŸ/39M TL, tenzilatlar %0.37â€“%96. `GROUP BY kazanan_firma` ile firma istatistikleri Ã§Ä±kÄ±yor.
  - **Frontend:** `ihale-detay.html` zaten Design A (`kazanan_firma`) okuyor â†’ **sonuÃ§lanan ihalelerde kazanan/bedel/tenzilat ÅU AN gÃ¶rÃ¼nÃ¼yor**, deÄŸiÅŸiklik gerekmez.
  - **KALAN:** (a) âœ… **cron'a zaten ekli** (14 Tem'de `run_scraper.sh` git'e alÄ±nÄ±rken doÄŸrulandÄ±: `ekap_sonuc_backfill.py --tum-kayitlar --max-pages 50` gece turunda Ã§alÄ±ÅŸÄ±yor, ayrÄ±ca ekleme gerekmiyor). (b) âœ… **`firma-analiz.html` "SonuÃ§lar" sekmesi TAMAMLANDI (commit e045a6c, 9 Tem 2026):** `ihale_sonuclari` WHERE kazanan_firma ILIKE, ilan baÅŸlÄ±klarÄ± `ilanlar` tablosundan zenginleÅŸtirildi, toplam sÃ¶zleÅŸme + ort. tenzilat + liste gÃ¶sterimi. (c) ğŸ”² **Derin tarihsel backfill (Faz 5):** 1.68M'i taramak iÃ§in proxy (IP ban) + Supabase Ã¶lÃ§ek gerek â€” ayrÄ± proje. (d) âœ… **`yukleniciler` artÄ±k dolu** (14 Tem: `yuklenici_yenile()` timeout fix'i sonrasÄ± ilk kez uÃ§tan uca Ã§alÄ±ÅŸtÄ±, **35.454 satÄ±r** yazÄ±ldÄ± â€” bkz. 14 Tem "cron bug" notu yukarÄ±da).
  - ~~Managed'a da migration_sonuc_B_kurulum.sql gerek~~ **ARTIK GEÃ‡ERSÄ°Z (10 Tem'de managed terk edildi).**

<!-- ESKI TESHIS (cozuldu, referans): iki sema catismasi -->
- [x] ~~SONUÃ‡/FÄ°RMA VERÄ°SÄ° â€” Ä°KÄ° ÅEMA Ã‡ATIÅMASI~~ (Ã§Ã¶zÃ¼ldÃ¼ â†‘): `ihale_sonuclari` iÃ§in iki tasarÄ±m vardÄ±:
  - **TasarÄ±m A (MEVCUT, 15 satÄ±r, frontend okuyor):** `ihale_sonuclari{ilan_id, kazanan_firma, kazanan_teklif, kazanan_teklif_farki_yuzde, tum_teklifler...}` â€” ihale-detay.html:716 bunu okur.
  - **TasarÄ±m B (`ekap_sonuc_scraper.py` + `migration_sonuc_schema.sql`):** `ihale_sonuclari{ekap_id, yuklenici_ad, sozlesme_bedeli, tenzilat_yuzde...}` + `yukleniciler` (firma sÃ¶zlÃ¼ÄŸÃ¼) + `scrape_log` (iÅŸlem takibi). Scraper `on_conflict="ekap_id"` ile B'ye yazÄ±yor.
  - Scraper ÅŸu an `scrape_log yok` (PGRST205) hatasÄ±yla duruyor. B'yi kurmak MEVCUT tabloyu (A) bozar + ihale-detay.html'i kÄ±rar.
  - **KARAR GEREK (Ã¶neri: TasarÄ±m B â€” daha zengin: yÃ¼klenici sÃ¶zlÃ¼ÄŸÃ¼, tenzilat, katÄ±lÄ±mcÄ±):** (1) `yukleniciler`+`scrape_log` oluÅŸtur (migration_sonuc_schema.sql'in o kÄ±sÄ±mlarÄ± â€” gÃ¼venli, yeni tablolar), (2) `ihale_sonuclari`'yÄ± B ÅŸemasÄ±na taÅŸÄ± (mevcut 15 satÄ±rÄ± migrate et VEYA drop+recreate+yeniden-scrape), (3) **ihale-detay.html'i B kolonlarÄ±na gÃ¼ncelle** (kazanan_firmaâ†’yuklenici_ad vb.), (4) scraper'Ä± bounded Ã§alÄ±ÅŸtÄ±r (`--limit N`, 0.3s throttle â€” ana scraper zaten bu IP'den ban yemiyor) â†’ doÄŸrula â†’ gece cron'una ekle. Prod DDL + frontend + veri taÅŸÄ±ma iÃ§erdiÄŸi iÃ§in **otonom yapÄ±lmadÄ±; kullanÄ±cÄ± kararÄ±+onayÄ± gerek.**
- [ ] **Faz 5 â€” GeÃ§miÅŸ backfill:** VM'de kompakt 2003+ backfill (ekap_sonuc_backfill.py) â†’ firma verisi dolar. HTML'siz (kompakt strateji â†“). âš ï¸ Otonom BAÅLATILMADI: uzun/riskli iÅŸ (proxy boÅŸ â†’ IP ban riski VDS'in gece cron'unu da vurabilir); kullanÄ±cÄ± "baÅŸlat" deyince checkpoint'li Ã§alÄ±ÅŸtÄ±rÄ±lmalÄ±. NOT: Ã¶nce yukarÄ±daki ÅŸema Ã§atÄ±ÅŸmasÄ± Ã§Ã¶zÃ¼lmeli.
- [ ] Storage `belgeler` bucket taÅŸÄ±nmasÄ± (aÄŸÄ±r belge turu aktifleÅŸince).

---

### ğŸ¤ DEVÄ°R â€” SIRADAKÄ° AI/OTURUM Ä°Ã‡Ä°N (8 Tem 2026, otonom oturumdan)

> **Durum:** VDS tam Ã§alÄ±ÅŸÄ±yor (http://195.85.207.126), gÃ¼venlik temiz, SMTP boru hattÄ± kurulu.
> **Launch'Ä±n Ã¶nÃ¼ndeki tek gerÃ§ek engel = KULLANICININ elindeki 2 panel iÅŸi** (Resend domain + Cloudflare DNS).
> AI eriÅŸimi olmayan yerler net iÅŸaretlendi. SSH: `ssh -i ~/.ssh/ihale_oracle root@195.85.207.126`.

**ADIM 1 â€” Resend domain doÄŸrulama (KULLANICI, Resend paneli):**
- resend.com â†’ Domains â†’ Add â†’ `ihaleglobal.com`. Resend'in verdiÄŸi SPF/DKIM/DMARC (CNAME+TXT) kayÄ±tlarÄ±nÄ± **Cloudflare DNS**'e ekle (proxy KAPALI/gri bulut â€” mail kayÄ±tlarÄ± proxy'lenmez). DoÄŸrulama yeÅŸil olunca AdÄ±m 2.

**ADIM 2 â€” GÃ¶ndericiyi gerÃ§ek adrese Ã§evir (AI, domain doÄŸrulanÄ±nca):**
```bash
ssh -i ~/.ssh/ihale_oracle root@195.85.207.126
cd /opt/supabase/docker
sed -i 's|^SMTP_ADMIN_EMAIL=.*|SMTP_ADMIN_EMAIL=noreply@ihaleglobal.com|' .env
docker compose up -d auth
# test: farkli bir e-postaya signup at, Resend panel â†’ Emails "Delivered" gormeli
```

**ADIM 3 â€” DNS cut-over (KULLANICI, Cloudflare paneli):**
- Cloudflare â†’ DNS â†’ `ihaleglobal.com` A kaydÄ±nÄ± `195.85.207.126`'ya Ã§evir (AAAA/IPv6 varsa sil â€” VDS'in IPv6'sÄ± yok). Proxy (turuncu bulut) AÃ‡IK kalabilir (CDN+SSL).
- `www` de aynÄ± IP'ye.

**ADIM 4 â€” SSL (AI, DNS Ã§evrildikten sonra). Ä°KÄ° seÃ§enek:**
- **(Ã–nerilen, CF-proxy'li) Cloudflare Origin Certificate:** KULLANICI CF â†’ SSL/TLS â†’ Origin Server â†’ Create Certificate (15 yÄ±l) â†’ cert+key'i verir; AI bunlarÄ± `/etc/nginx/ssl/`'e koyup nginx'e `listen 443 ssl` + `ssl_certificate` ekler; CF SSL modu **Full (strict)**. certbot GEREKMEZ.
- **(Alternatif) Let's Encrypt:** `apt install certbot python3-certbot-nginx` (VDS'te certbot YOK); ama CF proxy aÃ§Ä±kken HTTP-01 zorlaÅŸÄ±r â†’ DNS-01 iÃ§in CF API token gerekir. Origin Cert daha basit.

**ADIM 5 â€” URL'leri https'e Ã§evir (AI, SSL sonrasÄ±):**
- VDS `/opt/supabase/docker/.env`: `SITE_URL=https://ihaleglobal.com` (ÅŸu an `http://ihaleglobal.com`) + `docker compose up -d auth`.
- Frontend `SUPABASE_URL`/anon-key â†’ `https://ihaleglobal.com` (VDS kopyasÄ±nda; **repoya da commit** â€” ama DÄ°KKAT: repo ÅŸu an Cloudflare-managed'Ä± besliyor, commit ancak DNS cut-over TAM bitince yapÄ±lmalÄ± yoksa canlÄ± managed bozulur). Managed paralel ayakta = sÄ±fÄ±r kesinti; test bitince commit + eski servis kapat.

**ADIM 6 â€” Eski servisleri kapat (KULLANICI):** Render servisi + GitHub Actions scraper workflow'unu durdur (VDS cron devraldÄ±).

**QA TARAMASI (8 Tem, read-only â€” frontend saÄŸlam):** ana sayfa, harita, ihaleler/detay, dashboard, arama, bildirimler (boÅŸ durum OK), fiyatlandÄ±rma + Ä°yzico Ã¶deme modalÄ± (hatasÄ±z aÃ§Ä±lÄ±yor; kart girilmedi/Ã¶deme yapÄ±lmadÄ±), idareler dizini â€” **hepsi konsol-temiz.**
- ğŸ’³ **Ã–deme PCI notu:** Ã¶deme modalÄ± ham kart numarasÄ±nÄ± doÄŸrudan alÄ±yor (Ä°yzico hosted checkout deÄŸil). payment.py sunucuda tokenize etmiyorsa PCI-DSS yÃ¼kÃ¼ doÄŸar â†’ Ä°yzico hosted/tokenize akÄ±ÅŸÄ± Ã¶nerilir. CanlÄ± Ã§ekim sandbox test kartÄ±yla doÄŸrulanmalÄ± (AI finansal iÅŸlem yapmaz).
- ğŸ“Š **Kozmetik:** "Toplam"="Aktif" her yerde eÅŸit (tÃ¼m kayÄ±tlar `durum='aktif'`; geÃ§miÅŸ/sonuÃ§ verisi Faz 5 backfill gelene dek ayrÄ±ÅŸmaz) â€” bug deÄŸil, veri-durumu.

**AÃ‡IK NOTLAR / temizlik:**
- ğŸ”‘ **Resend key sohbet geÃ§miÅŸinde** â€” kullanÄ±cÄ± isterse rotate edip yeni key'i AdÄ±m 2 mantÄ±ÄŸÄ±yla `.env`'e yazmalÄ± (`SMTP_PASS=`).
- `farukdinc890@gmail.com` geÃ§ici parola `GeciciTest123!` â†’ deÄŸiÅŸtirilmeli.
- E2E test kullanÄ±cÄ±sÄ± (`e2e.test.1783161485@...`) hÃ¢lÃ¢ auth.users'ta â€” zararsÄ±z, silinebilir.
- `GOTRUE_MAILER_EXTERNAL_HOSTS` uyarÄ±sÄ± loglarda var (kozmetik) â€” istenirse `195.85.207.126`+`ihaleglobal.com` allowlist'e eklenir.

---

### ğŸ“œ ORÄ°JÄ°NAL PLAN (referans â€” yukarÄ±da uygulandÄ±)

### KARAR & GEREKÃ‡E
- **Hedef:** Åu an daÄŸÄ±tÄ±k olan sistemi (Cloudflare Pages + Supabase + Render + GitHub Actions)
  **tek bir TÃ¼rk VDS'te** birleÅŸtir.
- **3 neden:** (1) tek pencereden yÃ¶netim (bugÃ¼n cron 4 gÃ¼n sessiz Ã§Ã¶kmÃ¼ÅŸtÃ¼ â€” daÄŸÄ±tÄ±k sistemin bedeli),
  (2) milyonlarca geÃ§miÅŸ ihale satÄ±rÄ±nÄ± **ucuza/sÄ±nÄ±rsÄ±z** saklama (Supabase free 500MB yetmiyor,
  Pro $25/ay pahalÄ± bulundu), (3) **KVKK / kamu:** kamuyla Ã§alÄ±ÅŸÄ±lacaÄŸÄ± iÃ§in veri **TÃ¼rkiye'de**
  tutulmalÄ± (CumhurbaÅŸkanlÄ±ÄŸÄ± Bilgi ve Ä°letiÅŸim GÃ¼venliÄŸi Rehberi + kamu ihale ÅŸartnameleri veri-yeri ister).
- **Kritik:** SaÄŸlayÄ±cÄ± **fiziksel olarak TÃ¼rkiye'de** olmalÄ±. Yurt dÄ±ÅŸÄ± olursa gerekÃ§e Ã§Ã¶ker â†’ o durumda
  Hetzner (~â‚¬4/ay, daha ucuz/gÃ¼venilir) tercih edilir. Yani "TÃ¼rk saÄŸlayÄ±cÄ±"nÄ±n TEK sebebi veri-yeri.

### SAÄLAYICI SEÃ‡Ä°MÄ° (KARAR AÅAMASINDA)
KullanÄ±cÄ± TÃ¼rk VDS bakÄ±yor. DeÄŸerlendirilen adaylar (spec ~4-6 Ã§ekirdek / 8-10GB RAM / 60-130GB, Ubuntu 22.04, tam root):
- **Hosting DÃ¼nyam â€” TR-VDS6:** 4 Ã§ekirdek E5-2699v4 / 8GB ECC / 60GB SATA SSD / 395â‚º/ay. Ä°stanbul, Tier III+, %99.9. SaÄŸlam.
- **Datacasa â€” Premium Sunucu 10:** 6 Ã§ekirdek E5-2698v4 / 10GB / **130GB NVMe** / 349,99â‚º/ay. Spec/fiyat daha iyi
  AMA **datacenter TÃ¼rkiye'de mi doÄŸrulanmalÄ±** (belirsiz) + saÄŸlayÄ±cÄ± itibarÄ± teyit edilmeli. TÃ¼rkiye'deyse tercih edilir.
- âš ï¸ AlÄ±nacak Ã¼rÃ¼n MUTLAKA **VDS / Cloud Sunucu (tam root)** olmalÄ± â€” "Hosting/Web Hosting" DEÄÄ°L.
- Ã–neri seviyesi: 8GB RAM yeterli (analiz iÃ§in); 12GB gerekince sonradan yÃ¼kseltilir. CPU farkÄ± ikincil.

### SSH ANAHTARI (HAZIR)
- KullanÄ±cÄ±nÄ±n makinesinde Ã¼retildi: **`~/.ssh/ihale_oracle`** (private) + **`~/.ssh/ihale_oracle.pub`** (public).
- Public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJgxU49zYE9enXlSCbgAwddf+dTIZai9VrtgDlJJYMdN ihale-oracle-vm`
- Herhangi bir saÄŸlayÄ±cÄ±da geÃ§erli. VM alÄ±nca panele eklenir ya da root ÅŸifresiyle sonra kurulur.

### HEDEF MÄ°MARÄ° (VDS Ã¼stÃ¼nde)
| BileÅŸen | NasÄ±l | Åu an nerede |
|---|---|---|
| DB + Auth + API + RLS + Storage | **Self-hosted Supabase** (Docker) â€” supabase-js/frontend/RLS AYNEN Ã§alÄ±ÅŸÄ±r, sadece URL deÄŸiÅŸir | Supabase (managed) |
| Backend API | FastAPI â†’ `systemd` + `uvicorn`, Ã¶nÃ¼nde nginx | Render |
| Scraper | Linux `cron` â†’ `python ekap_scraper.py` (gece) | GitHub Actions |
| GeÃ§miÅŸ backfill | VM'de uzun sÃ¼ren checkpoint'li iÅŸ (Actions 6h/Render cron yok â€” VM'de sÄ±nÄ±r yok) | (yapÄ±lmadÄ±) |
| Frontend | nginx (statik) â€” AMA **Cloudflare Ã¶nde proxy** kalsÄ±n (bedava CDN+DDoS+SSL, sÄ±fÄ±r yÃ¶netim) | Cloudflare Pages |

### DEPOLAMA STRATEJÄ°SÄ° â€” HÄ°BRÄ°T (Ã–NEMLÄ°)
- Tam ihale satÄ±rÄ± ~**25KB** (ilan HTML dahil), kompakt ~**0.5KB** â†’ **50x fark**.
- **Aktif/gÃ¼ncel ihaleler (~12k): TAM HTML sakla** (detay + iÃ§erik aramasÄ± + AI). ~300MB, ucuz.
- **GeÃ§miÅŸ arÅŸiv (milyonlarca): KOMPAKT sakla** (meta + sonuÃ§: yÃ¼klenici/bedel/tenzilat). ~4GB.
- GeÃ§miÅŸi HTML'li saklasaydÄ±k ~40-100GB gerekirdi (60GB'a sÄ±ÄŸmazdÄ±). Kompakt sayesinde TR-VDS6/130GB rahat.
- **Backfill script'i bu mantÄ±kla yazÄ±lacak (geÃ§miÅŸ = kompakt, HTML yok).**

### FAZLAR (adÄ±m adÄ±m)
1. **Faz 1 â€” Hesap + VM (KULLANICI):** TÃ¼rk VDS al (Ubuntu 22.04, ~8GB, tam root). Datacasa'yÄ± seÃ§erse Ã¶nce
   "TÃ¼rkiye'de mi + itibar" doÄŸrula. IP + root eriÅŸimini AI'a ver.
2. **Faz 2 â€” Sunucu kurulumu (AI, SSH'tan):** Docker + docker-compose, gÃ¼venlik duvarÄ± (ufw: 22/80/443),
   SSH sertleÅŸtirme (key-only), self-hosted Supabase stack.
3. **Faz 3 â€” Uygulamalar:** FastAPI systemd servisi, scraper cron, nginx (frontend + reverse proxy).
4. **Faz 4 â€” Veri taÅŸÄ±ma:** Supabase â†’ yeni Postgres (pg_dump/restore), Storage `belgeler` bucket taÅŸÄ±,
   frontend'in SUPABASE_URL/KEY'lerini yeni VM adresine Ã§evir, RLS policy'lerini uygula (backend/rls_*.sql).
5. **Faz 5 â€” GeÃ§miÅŸ backfill:** VM'de kompakt 2003+ backfill baÅŸlat (ekap_sonuc_backfill.py temeli) â†’ firma verisi dolar.
6. **Faz 6 â€” Cut-over:** Cloudflare DNS'i VM'e Ã§evir (proxy aÃ§Ä±k), uÃ§tan uca test, sonra eski servisleri kapat.
- **Paralel Ã§alÄ±ÅŸÄ±lacak:** mevcut managed sistem taÅŸÄ±ma boyunca AYAKTA kalÄ±r, sadece test bitince DNS Ã§evrilir â†’ sÄ±fÄ±r kesinti.

### AÃ‡IK KARARLAR / SIRADAKI
- [ ] KullanÄ±cÄ± saÄŸlayÄ±cÄ±+paketi kesinleÅŸtirsin (Datacasa TÃ¼rkiye'deyse o; deÄŸilse Hosting DÃ¼nyam TR-VDS6 ya da Hetzner).
- [ ] VM alÄ±nÄ±nca: **Public IP + root eriÅŸimi** â†’ Faz 2 baÅŸlar.
- [ ] KullanÄ±cÄ±nÄ±n kendi tercihi: taÅŸÄ±mayÄ± launch'tan Ã–NCE yapÄ±yor (managed paralel ayakta kalacaÄŸÄ± iÃ§in risksiz).

---

## ğŸ” CANLIYA ALMA â€” GÃœVENLÄ°K DENETÄ°MÄ° & E2E (4 Tem 2026)

> CanlÄ± Supabase'e karÅŸÄ± anon key + gerÃ§ek test kullanÄ±cÄ±sÄ± (signupâ†’login) ile uÃ§tan uca denetim yapÄ±ldÄ±.

**âœ… Okuma (veri sÄ±zÄ±ntÄ±sÄ±) tarafÄ± TAM KORUMALI:**
- TÃ¼m kullanÄ±cÄ± tablolarÄ± (`profil`, `kullanici_krediler`, `kredi_hareketleri`, `bildirimler`, `teklifler`, `takipler`, `kullanici_profiller`) anon SELECT'e `[]` / `count */0` dÃ¶ndÃ¼ â†’ RLS okumayÄ± filtreliyor.
- Kimlik doÄŸrulanmÄ±ÅŸ kullanÄ±cÄ± SADECE kendi satÄ±rlarÄ±nÄ± gÃ¶rÃ¼yor; `kredi_hareketleri` no-filter sorgusu bile `*/0` (baÅŸkasÄ±nÄ±nki gÃ¶rÃ¼nmÃ¼yor).

**âœ… Yazma tarafÄ± â€” doÄŸrulananlar:**
- `profil`: kendi satÄ±rÄ±nÄ± yazabiliyor (201), **baÅŸka user_id ile yazma RLS'le engellendi (403/42501)**.
- `takipler`: kendi satÄ±rÄ± OK, **Ã§apraz-kullanÄ±cÄ± yazma engellendi (403)**.
- `kullanici_krediler.kalan_kredi` **generated (hesaplanan) kolon** â†’ doÄŸrudan kredi yazÄ±lamÄ±yor. Ä°yi tasarÄ±m.

**ğŸ”´ KRÄ°TÄ°K AÃ‡IK â€” ONAYLANDI (policy listesiyle, 4 Tem 2026):**
- `kullanici_krediler` ve `kredi_hareketleri` policy'leri `cmd=ALL` + `auth.uid()=kullanici_id`, WITH CHECK boÅŸ â†’ INSERT/UPDATE'te USING'e dÃ¼ÅŸÃ¼yor. **GiriÅŸ yapmÄ±ÅŸ kullanÄ±cÄ± kendi kredi satÄ±rÄ±nÄ± UPDATE edebiliyor** (`toplam_kredi`'yi ÅŸiÅŸir â†’ `kalan_kredi` hesaplanan kolon otomatik artar â†’ sÄ±nÄ±rsÄ±z bedava kredi, Ä°yzico bypass).
- **DÃœZELTME HAZIR â†’ `backend/rls_fix_kredi.sql`'i Supabase SQL Editor'da Ã§alÄ±ÅŸtÄ±r.** Ä°ki tabloyu salt-okur yapar. Backend payment.py service_role ile yazdÄ±ÄŸÄ± iÃ§in Ã¶deme/kredi yÃ¼kleme ETKÄ°LENMEZ (frontend krediyi zaten sadece okuyor). **CanlÄ±ya/Ä°yzico'ya geÃ§meden Ã–NCE uygulanmalÄ±.**
- `ilanlar`: GÃœVENLÄ° â€” write policy'leri `yayinlayan_id`'ye baÄŸlÄ±; EKAP kayÄ±tlarÄ±nda `null` â†’ kullanÄ±cÄ± EKAP ihalelerini deÄŸiÅŸtiremez.
- Denetim SQL'i: `backend/rls_audit.sql` (salt-okur, RLS on/off + policy listesi).

**ğŸ› BULUNAN & DÃœZELTÄ°LEN BUG â€” takip DB senkronu kÄ±rÄ±ktÄ± (`js/takip.js`):**
- `from('takip')` â†’ var olmayan tablo (gerÃ§ek ad `takipler`); kolon `user_id` â†’ gerÃ§ek ad `kullanici_id`. Hatalar `catch{}` ile sessizce yutuluyordu â†’ **takipler DB'ye hiÃ§ yazÄ±lmÄ±yordu, sadece localStorage'da kalÄ±yordu** (cihaz deÄŸiÅŸince/Ã§Ä±kÄ±ÅŸta kayboluyor).
- DÃ¼zeltme uygulandÄ± ve canlÄ±da doÄŸrulandÄ± (insertâ†’readâ†’delete OK, Ã§apraz-kullanÄ±cÄ± yazma bloklu). ArtÄ±k takip cihazlar arasÄ± senkron olacak.

**âš ï¸ Launch notu â€” e-posta doÄŸrulamasÄ± KAPALI:** signup anÄ±nda `email_verified:true` token verdi, onay adÄ±mÄ± yok â†’ sahte e-postayla hesap aÃ§Ä±labilir. Ãœcretli Ã¼rÃ¼n iÃ§in Supabase Auth'ta e-posta doÄŸrulamayÄ± aÃ§mayÄ± deÄŸerlendir.

### ğŸ”² YAPILACAK â€” E-posta doÄŸrulamasÄ±nÄ± aÃ§ (canlÄ±ya almadan Ã¶nce)
- [ ] Supabase Dashboard â†’ **Authentication â†’ Sign In / Providers â†’ Email** â†’ **"Confirm email"** seÃ§eneÄŸini AÃ‡.
  - Etki: yeni kayÄ±t olan kullanÄ±cÄ±, e-postasÄ±ndaki doÄŸrulama linkine tÄ±klamadan giriÅŸ yapamaz â†’ sahte/Ã§alÄ±ntÄ± e-postayla hesap aÃ§Ä±lmasÄ± engellenir.
  - Not: DoÄŸrulama e-postalarÄ± Supabase'in varsayÄ±lan SMTP'siyle gider (dÃ¼ÅŸÃ¼k limit). CanlÄ±da gÃ¼venilir teslim iÃ§in **Authentication â†’ Emails â†’ SMTP Settings**'ten Resend SMTP'yi baÄŸla (Resend zaten bildirimler iÃ§in kullanÄ±lÄ±yor).
  - Test: aÃ§ â†’ yeni bir e-postayla kayÄ±t ol â†’ giriÅŸ engellenmeli, kutuya doÄŸrulama maili dÃ¼ÅŸmeli.

**ğŸ§¹ Temizlik:** Denetimde 1 test kullanÄ±cÄ±sÄ± oluÅŸturuldu (`e2e.test.1783161485@ihaleglobal-e2etest.com`). Profil satÄ±rÄ± silinemedi (profil'de DELETE policy yok â€” zararsÄ±z). Supabase Dashboard â†’ Auth â†’ Users'tan bu test kullanÄ±cÄ±sÄ±nÄ± silebilirsin (profil satÄ±rÄ± cascade gider).

---

## ğŸ”´ Ã–NCELÄ°K 1 â€” Acil Bug'lar (Ã–nce bunlar Ã§Ã¶zÃ¼lmeli) â€” âœ… TAMAMLANDI (28 Haz 2026)

### 1.1 Redirect Loop â€” âœ… Ã‡Ã–ZÃœLDÃœ
**KÃ¶k neden:** Cloudflare Pages zaten `/sayfa.html`'i uzantÄ±sÄ±z `/sayfa` adresinde servis edip `/sayfa.html â†’ /sayfa` 301'i KENDÄ°SÄ° yapÄ±yor. `_redirects`'teki `/sayfa â†’ /sayfa.html` kuralÄ± bunun tersi â†’ sonsuz dÃ¶ngÃ¼.
**Ã‡Ã¶zÃ¼m:** `_redirects`'teki TÃœM aynÄ±-isimli 301 kurallarÄ± kaldÄ±rÄ±ldÄ± (tÃ¼m iÃ§ linkler zaten uzantÄ±sÄ±z). Dosyaya neden aÃ§Ä±klamasÄ± eklendi.
- Ek olarak: hakkimizda/iletisim/mesafeli-satis sayfalarÄ±ndaki `.html` uzantÄ±lÄ± linkler uzantÄ±sÄ±za Ã§evrildi; kÄ±rÄ±k `/fiyatlandirma.html` â†’ `/fiyatlandirma_odeme_bolumu`, var olmayan `/kullanim-kosullari` â†’ `/kvkk` dÃ¼zeltildi.

### 1.2 ihaleler.html crash â€” âœ… KONTROL EDÄ°LDÄ°
- Referans verilen tÃ¼m JS dosyalarÄ± (`sidebar-user.js`, `plan.js`, `takip.js`) mevcut; eksik dosya crash'i yok.
- **AyrÄ±ca bulunan gerÃ§ek bug:** index.html ve dashboard.html, `ilanlar` tablosunda var olmayan `created_at` kolonunu sorguluyordu â†’ `Promise.all` Ã§Ã¶kÃ¼yor, tÃ¼m sayaÃ§lar "â€”" kalÄ±yordu. DoÄŸru kolon `olusturulma` ile dÃ¼zeltildi.

### 1.3 Login â†’ Dashboard akÄ±ÅŸÄ± â€” âœ… KOD DOÄRULANDI
- Login `signInWithPassword` ile supabase-js session'Ä± kalÄ±cÄ±laÅŸtÄ±rÄ±yor; dashboard `sb.auth.getUser()` ile aynÄ± session'Ä± okuyor â†’ oturum korunuyor. Dashboard'da login'e zorla atan guard yok (loop riski yok). CanlÄ± E2E testi deploy sonrasÄ± yapÄ±lmalÄ±.

### 1.4 ilanlar tablosu â€” âœ… DOLU (premise yanlÄ±ÅŸtÄ±)
- `ilanlar` tablosunda **11.878 gerÃ§ek kayÄ±t var** (curl ile doÄŸrulandÄ±). YAPILACAKLAR'daki "0 kayÄ±t" bilgisi eskiydi; PROJE_DURUM doÄŸru.
- âš ï¸ Not: scraper her upsert'te `olusturulma`'yÄ± bugÃ¼ne Ã§ektiÄŸi iÃ§in "BugÃ¼n Eklenen" ÅŸiÅŸkin (â‰ˆ11.868). GerÃ§ek "yeni eklenen" semantiÄŸi iÃ§in ayrÄ± bir `ilk_gorulme` kolonu gerekir (gelecek iÅŸ).
- âš ï¸ Veri kalitesi: `baslik`/`idare` alanlarÄ±nda TÃ¼rkÃ§e karakter mojibake (Ã§ift-encode) var â€” scraper encoding dÃ¼zeltmesi gerekiyor (gelecek iÅŸ).

---

## ğŸ—ºï¸ Ã–NCELÄ°K 2 â€” TÃ¼rkiye HaritasÄ± (Ä°l BazlÄ± IsÄ± HaritasÄ±) â€” âœ… TAMAMLANDI (28 Haz 2026)

> Referans: ihalegram.com â€” Leaflet.js ile yapÄ±lmÄ±ÅŸ, Ã§ok temiz.

**YapÄ±ldÄ± (index.html):**
- âœ… Leaflet.js choropleth harita (tÃ¼rkiye-provinces.geojson + Supabase il sayÄ±mÄ±)
- âœ… Quantile-bazlÄ± 6 renk skalasÄ± (navyâ†’turuncuâ†’kÄ±rmÄ±zÄ±); proje temasÄ±yla uyumlu
- âœ… Hover tooltip (il adÄ± + sayÄ±), hover'da sÄ±nÄ±r beyazlanÄ±r
- âœ… Legend: dinamik sayÄ± aralÄ±klarÄ± (Ã¶rn. 0 | 1â€“42 | 43â€“76 | ...)
- âœ… Harita Ã¼stÃ¼nde 3 sekme: **Ä°lanlar** (aktif) | Firmalar "YakÄ±nda" | Kurumlar "YakÄ±nda"
- âœ… Bir ile tÄ±klayÄ±nca â†’ `ihaleler?il=Ä°L_ADI` â€” ihaleler.html filtresi otomatik set edilir
- âœ… Ã–zet kartlar: Toplam / GÃ¼ncel / BugÃ¼n Eklenen / Kapsanan Ä°l
- âœ… Lazy-load: harita gÃ¶rÃ¼nÃ¼r olunca baÅŸlar (IntersectionObserver)
- âš ï¸ **Performans notu:** Ä°l sayÄ±mÄ± ÅŸu an 13 paralel istek (Ã—1000 satÄ±r) ile yapÄ±lÄ±yor. Ä°deal: Supabase'de `il_sayim()` RPC fonksiyonu (GROUP BY il) â€” gelecekte hÄ±z iÃ§in eklenebilir.

### 2.1 Teknik altyapÄ±
- **KÃ¼tÃ¼phane:** Leaflet.js 1.9.4 (CDN: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` + CSS)
- **Veri:** TÃ¼rkiye 81 il sÄ±nÄ±rlarÄ± GeoJSON dosyasÄ± (GitHub'da aÃ§Ä±k kaynak mevcut, repoya `data/turkey-provinces.geojson` olarak eklenebilir)
- **Render:** SVG tabanlÄ± (81 path, her path bir il)

### 2.2 GÃ¶rsel Ã¶zellikler (ihalegram'dan birebir)
- Her il, iÃ§indeki ihale sayÄ±sÄ±na gÃ¶re renklendirilir (choropleth / Ä±sÄ± haritasÄ±)
- **Renk skalasÄ± (8 kademe):** koyu lacivert `#312e81` â†’ mor `#4338ca` â†’ ... â†’ kÄ±rmÄ±zÄ± `#ef4444`
- **Legend (lejant):** SaÄŸ altta `0 | 1-2k | 2k-4.7k | 4.7k-9.8k | 9.8k-17.6k | 17.6k-25.5k | 25.5k-33.3k | 33.3k+`
  - NOT: Bizim veri hacmimiz baÅŸta kÃ¼Ã§Ã¼k olacaÄŸÄ± iÃ§in kademe aralÄ±klarÄ±nÄ± dinamik hesaplamak daha doÄŸru (Ã¶rn. quantile bazlÄ±). Sabit 33.3k aralÄ±klarÄ± bizde hep koyu kalÄ±r.
- `fill-opacity: 0.9`, `stroke: #334155` (il sÄ±nÄ±rlarÄ±)
- **Hover tooltip:** Sol Ã¼stte kutu â†’ "Ä°l AdÄ± | ihale sayÄ±sÄ±" (Ã¶rn. "KÄ±rÄ±kkale | 1932")
- Hover'da ilin sÄ±nÄ±rÄ± beyaza dÃ¶ner (vurgu)
- **Zoom kontrolÃ¼:** SaÄŸ Ã¼stte +/- butonlarÄ±

### 2.3 EtkileÅŸim
- Bir ile **tÄ±klayÄ±nca** â†’ o il iÃ§in ihale listesi filtrelenir (ÅŸehir filtresi otomatik o ile set edilir)
- Harita Ã¼stÃ¼nde 3 sekme: **Ä°lanlar | Firmalar | Kurumlar** (ihalegram'daki gibi â€” baÅŸta sadece "Ä°lanlar" yeterli, diÄŸerleri sonra)

### 2.4 Veri sorgusu (Supabase)
- `ilanlar` tablosundan il bazlÄ± sayÄ±m:
  ```sql
  SELECT sehir, COUNT(*) as adet FROM ilanlar GROUP BY sehir;
  ```
- SonuÃ§ bir JS objesine map'lenir: `{ "Ankara": 1234, "Ä°stanbul": 5678, ... }`
- GeoJSON'daki il isimleriyle Supabase'deki `sehir` deÄŸerleri **birebir eÅŸleÅŸmeli** (TÃ¼rkÃ§e karakter / bÃ¼yÃ¼k-kÃ¼Ã§Ã¼k harf normalizasyonu gerekebilir â†’ eÅŸleÅŸtirme tablosu)

### 2.5 Ãœst Ã¶zet kartlarÄ± (haritanÄ±n altÄ±nda â€” ihalegram'daki gibi)
- **BugÃ¼n YayÄ±nlanan** (sayÄ±)
- **BugÃ¼n Bitecekler** (sayÄ±)
- **GÃ¼ncellenen Ä°haleler** (sayÄ±)
- **Toplam Ä°hale** (sayÄ±) â† `ilanlar` tablosu COUNT

---

## ğŸ” Ã–NCELÄ°K 3 â€” GeliÅŸmiÅŸ Arama & Filtreleme â€” ğŸŸ¡ BÃœYÃœK KISMI TAMAM (28 Haz 2026)

**YapÄ±ldÄ± (ihaleler.html):**
- âœ… 3.1 Sekmeler: GÃ¼ncel / GeÃ§miÅŸ / SonuÃ§ / DetaylÄ± Ara (GÃ¼ncel=teklif tarihi gelecekte, GeÃ§miÅŸ=geÃ§miÅŸte, SonuÃ§=veri yokâ†’bilgi mesajÄ±, DetaylÄ± Ara=geliÅŸmiÅŸ panel aÃ§Ä±lÄ±r)
- âœ… 3.2 Filtreler: Åehir (81 il statik), Ä°hale tÃ¼rÃ¼ (+Kiralama), Ä°hale usulÃ¼ (ham EKAP enumâ†’ilike fragment eÅŸleÅŸtirme), YaklaÅŸÄ±k maliyet **min-max**, Ä°hale iÃ§eriÄŸi (full-text, 5 kolon OR ilike), YayÄ±n tarihi aralÄ±ÄŸÄ±
- âœ… 3.3 DetaylÄ± Ara: Ä°dare adÄ± arama, Teklif tarihi aralÄ±ÄŸÄ±, YayÄ±n tarihi aralÄ±ÄŸÄ±
- âœ… 3.4 Full-text (baslik+idare+okas+isin_yapilacagi_yer+ilan_metni)
- âœ… 3.5/3.6 SÄ±ralama + sayaÃ§ + sayfalama (zaten vardÄ±)

**Kalan / engelli (veri eksikliÄŸi):**
- âœ… **Kategori filtresi**: `ihaleler.html`'e KATEGORÄ° dropdown eklendi (29 kategori); scraper artÄ±k OKAS/CPV'den kategori tÃ¼retiyor; `migration_kategori_backfill.sql` ile mevcut kayÄ±tlar backfill edilebilir (Supabase SQL Editor'dan Ã§alÄ±ÅŸtÄ±r).
- âœ… **HÄ±zlÄ± Tarih Filtreleri** (30 Haz 2026): `ihaleler.html`'e tab-bar ile filter-bar arasÄ± chip satÄ±rÄ± eklendi â€” TÃ¼mÃ¼ / BugÃ¼n / Bu Hafta / Son 7 GÃ¼n / Son 30 GÃ¼n. `f-yayin-bas`/`f-yayin-bit` giriÅŸ alanlarÄ±nÄ± siler veya set eder, "DetaylÄ± Ara" panelini aÃ§madan tek tÄ±kla filtre uygular. SÄ±fÄ±rla butonu chip'i de sÄ±fÄ±rlar.
- âš ï¸ DetaylÄ± Ara'nÄ±n bazÄ± alanlarÄ± (teklif tÃ¼rÃ¼, ihale kaynaÄŸÄ±, iÃ§erik tÃ¼rÃ¼, idare tÃ¼rÃ¼, iÅŸin/teslim/Ã¶deme sÃ¼resi, sÄ±nÄ±r deÄŸer) eklenmedi â€” bu kolonlar DB'de yok.
- âœ… **Veri-borcu Ã§Ã¶zÃ¼ldÃ¼ (scraper):** `usul` artÄ±k TÃ¼rkÃ§e'ye Ã§evriliyor; `baslik`/`idare`/`il` mojibake scraper'da dÃ¼zeltiliyor. Mevcut kayÄ±tlar iÃ§in:
  - `migration_veri_temizlik.sql`: il UPPER normalize + ham usul enum dÃ¼zeltme (Supabase SQL Editor'da Ã§alÄ±ÅŸtÄ±r)
  - `mojibake_fix.py`: mevcut kayÄ±tlardaki bozuk TÃ¼rkÃ§e karakterleri Python'da dÃ¼zeltir (`--dry-run` ile Ã¶nce test et)

### (orijinal plan â†“)
## ğŸ” Ã–NCELÄ°K 3 â€” referans

> Hedef: ihaleciler.com kadar gÃ¼Ã§lÃ¼ filtre, ama **daha sade/temiz** bir arayÃ¼z. OnlarÄ±n ekranÄ± kalabalÄ±k; biz aynÄ± gÃ¼cÃ¼ daha az gÃ¶rsel yÃ¼kle vereceÄŸiz.

### 3.1 Sekme yapÄ±sÄ± (Ã¼stte)
ihaleciler.com'da 4 sekme var, bizde de olmalÄ±:
- **GÃ¼ncel** â€” aÃ§Ä±k/aktif ihaleler (teklif tarihi geÃ§memiÅŸ)
- **GeÃ§miÅŸ** â€” teklif tarihi geÃ§miÅŸ ihaleler
- **SonuÃ§** â€” sonuÃ§lanmÄ±ÅŸ / sÃ¶zleÅŸmeye baÄŸlanmÄ±ÅŸ ihaleler
- **DetaylÄ± Ara** â€” tÃ¼m filtrelerin aÃ§Ä±ldÄ±ÄŸÄ± geniÅŸ ekran

### 3.2 Temel filtre alanlarÄ± (GÃ¼ncel/GeÃ§miÅŸ/SonuÃ§ sekmelerinde)
Her sekmede ÅŸu filtreler bulunmalÄ±:
| Filtre | Tip | Not |
|--------|-----|-----|
| **Kategori** | dropdown | 32 kategori (ihaleciler.com taksonomisi) |
| **Åehir** | dropdown | 81 il |
| **Ä°hale tÃ¼rÃ¼** | dropdown | YapÄ±m Ä°ÅŸi, Mal AlÄ±mÄ±, Hizmet AlÄ±mÄ±, DanÄ±ÅŸmanlÄ±k, **Kiralama** â† BÄ°ZDE EKSÄ°K! |
| **Ä°hale usulÃ¼** | dropdown | AÃ§Ä±k, PazarlÄ±k, Belli Ä°stekliler, DoÄŸrudan Temin vb. |
| **YaklaÅŸÄ±k maliyet** | aralÄ±k (min-max) | "â‚ºX TL ye kadar" formatÄ± |
| **Ä°hale iÃ§eriÄŸi** | metin arama | Ä°halenin iÃ§inde geÃ§en HERHANGÄ° bir kelime (full-text search) |
| **YayÄ±n tarihi** | tarih aralÄ±ÄŸÄ± (gg.aa.yyyy) | baÅŸlangÄ±Ã§â€“bitiÅŸ |

### 3.3 DetaylÄ± Ara sekmesi (geniÅŸletilmiÅŸ â€” ihaleciler.com gÃ¶rsel 2'deki gibi)
YukarÄ±dakilere EK olarak:
- **Teklif tÃ¼rÃ¼** (E-ihale, Yerli istekli vb.)
- **Ä°hale kaynaÄŸÄ±** (EKAP, Yerel vb.)
- **Ä°Ã§erik tÃ¼rÃ¼**
- **Ä°dare tÃ¼rÃ¼** (dropdown)
- **Ä°dare adÄ±** (metin arama)
- **Teklif tarihi** (tarih aralÄ±ÄŸÄ±)
- **Ä°ÅŸin sÃ¼resi** (min-max gÃ¼n)
- **Teslim sÃ¼resi** (min-max)
- **Ã–deme sÃ¼resi** (min-max)
- **SÄ±nÄ±r deÄŸer katsayÄ±sÄ±**

### 3.4 Arama davranÄ±ÅŸÄ±
- **"Ä°hale iÃ§eriÄŸi" aramasÄ± full-text olmalÄ±:** ihale baÅŸlÄ±ÄŸÄ± + iÅŸin niteliÄŸi + idare adÄ± + tÃ¼m metin alanlarÄ±nda arama yapmalÄ±.
- Supabase'de `ilanlar` tablosuna full-text search index (Postgres `tsvector`) eklenebilir, ya da basitÃ§e `ILIKE '%kelime%'` ile birden fazla kolonda OR aramasÄ±.

### 3.5 SÄ±ralama seÃ§enekleri (sonuÃ§ listesi Ã¼stÃ¼nde)
- Otomatik (varsayÄ±lan)
- GÃ¶rÃ¼ntÃ¼lenme sayÄ±sÄ±
- YayÄ±n tarihi
- Teklif tarihi
- Åehir
- (SonuÃ§ sekmesinde: SÃ¶zleÅŸme tarihi, Ä°ÅŸ bitiÅŸ)

### 3.6 SonuÃ§ listesi Ã¼st bilgi
- "Toplam: X ihale" sayacÄ±
- Sayfalama: Ä°lk sayfa | Ã–nceki | [1. Sayfa â–¼] | Sonraki | Son sayfa

---

## ğŸ“‹ Ã–NCELÄ°K 4 â€” Ä°hale Listesi KartÄ± â€” ğŸŸ¢ TEMEL TAMAM (28 Haz 2026)

**YapÄ±ldÄ± (ihaleler.html):** Tablo dÃ¼zeni zengin **kart** dÃ¼zenine Ã§evrildi. Her kartta:
- âœ… KayÄ±t no (ekap_id), tÄ±klanabilir baÅŸlÄ±k (â†’ detay), idare adÄ±
- âœ… Etiketler: EKAP (mavi), ihale tÃ¼rÃ¼, ihale usulÃ¼ (ham enumâ†’TÃ¼rkÃ§e), ğŸ“ il
- âœ… YaklaÅŸÄ±k maliyet (aralÄ±k formatÄ±), durum rozeti (AÃ§Ä±k/Son N GÃ¼n/KapandÄ±)
- âœ… Tarihler: YayÄ±n + Son Teklif; uyum % barÄ±; Takibe Al + Detay butonlarÄ±
- Hover efekti, dark/amber tema korundu. TarayÄ±cÄ±da doÄŸrulandÄ± (25 kart, il filtresi dahil).

**Kart'ta gÃ¶sterilemeyen (veri yok â€” sonuÃ§lanmÄ±ÅŸ ihale gerekir):**
- âš ï¸ YÃ¼klenici adÄ±, sÃ¶zleÅŸme bedeli + tenzilat %, sÃ¶zleÅŸme/iÅŸ tarihleri, katÄ±lÄ±mcÄ± sayÄ±sÄ±.
  Bunlar "SonuÃ§" verisi toplanÄ±nca (Ã–ncelik 6 / scraper sonuÃ§ ilanÄ±) eklenebilir.

### ğŸ”‘ BULUNAN VERÄ°-BORÃ‡LARI (filtrelerin tam deÄŸeri iÃ§in Ã–NEMLÄ°)
> Bunlar scraper (`backend/ekap_scraper.py`) ingest aÅŸamasÄ±nda dÃ¼zeltilmeli:
1. **il deÄŸerleri TÃ¼rkÃ§e BÃœYÃœK HARF** (Ã¶rn. `Ä°STANBUL`, `ANKARA`) â€” tutarsÄ±z (birkaÃ§ seed kaydÄ± Title Case). Frontend dropdown buna gÃ¶re bÃ¼yÃ¼k-harf value kullanacak ÅŸekilde ayarlandÄ±, ama **ideal olan ingest'te normalize etmek** (Title Case). il-bazlÄ± her yeni Ã¶zellik (harita!) bu kasing'e dikkat etmeli.
2. **usul ham i18n anahtarÄ±** (`...SEARCH_METHOD.OPEN`) â€” TÃ¼rkÃ§e'ye Ã§evrilmeli.
3. **baslik/idare mojibake** (Ã§ift-encode TÃ¼rkÃ§e karakter) â€” encoding dÃ¼zeltmesi.
4. **kategori kolonu NULL** â€” kategori filtresi iÃ§in doldurulmalÄ± (OKAS/CPV'den tÃ¼retilebilir).
5. **olusturulma her upsert'te bugÃ¼ne Ã§ekiliyor** â†’ "BugÃ¼n Eklenen" sayacÄ± ÅŸiÅŸkin; gerÃ§ek yeni-kayÄ±t takibi iÃ§in `ilk_gorulme` kolonu ekle.

---

## ğŸ“‹ Ã–NCELÄ°K 4 â€” referans (orijinal plan)

> ihaleciler.com'daki ihale kartÄ± Ã§ok detaylÄ±. Bizimki de bu bilgileri gÃ¶stermeli ama **daha sade** kartlarla.

### 4.1 Ä°hale kartÄ±nda gÃ¶sterilecek alanlar
Her ihale kartÄ±nda (SonuÃ§ sekmesi Ã¶rneÄŸi):
- **KayÄ±t no** (Ã¶rn. `2026/796063`)
- **Ä°hale baÅŸlÄ±ÄŸÄ±** (tÄ±klanabilir â†’ detay sayfasÄ±)
- **KatÄ±lÄ±mcÄ± adÄ±** (varsa)
- **YÃ¼klenici adÄ±** (tÄ±klanabilir â†’ o firmanÄ±n tÃ¼m ihaleleri) â† firma bazlÄ± arama linki
- **YaklaÅŸÄ±k maliyet** (â‚º formatÄ±nda)
- **SÃ¶zleÅŸme bedeli** + **tenzilat yÃ¼zdesi** (yeÅŸil rozet, Ã¶rn. `%10,30`)
- **Ä°dare adÄ±** (tÄ±klanabilir â†’ o idarenin tÃ¼m ihaleleri) + **ÅŸehir**
- **Etiketler:** Ekap, ihale usulÃ¼ (Ã¶rn. "PazarlÄ±k usulÃ¼")
- **Tarihler:** YayÄ±n tarihi, Teklif tarihi, Ä°ÅŸ baÅŸlangÄ±Ã§, Ä°ÅŸ bitiÅŸ, SÃ¶zleÅŸme tarihi
- **Durum rozeti:** TamamlandÄ± / Devam ediyor / GÃ¼ncellendi
- **Aksiyon butonlarÄ±:** SÃ¶zleÅŸme listesi | SonuÃ§ Ä°lanÄ± | Benzer ihale geÃ§miÅŸi
- **YÄ±ldÄ±z (takip et)** + **ataÃ§ (dosya ekle)** ikonlarÄ±

### 4.2 Uyum (compatibility) skoru
- Bizim ekstra Ã¶zelliÄŸimiz: kullanÄ±cÄ±nÄ±n seÃ§tiÄŸi kategorilere gÃ¶re uyum % skoru
- Hesap: kategori eÅŸleÅŸmesi (40p) + ÅŸehir (25p) + ihale tÃ¼rÃ¼ (20p) + bÃ¼tÃ§e aralÄ±ÄŸÄ± (15p)
- % olarak gÃ¶sterilir (ihaleciler.com'da yok, bizim artÄ±mÄ±z)

---

## ğŸ“„ Ã–NCELÄ°K 5 â€” Ä°hale Detay SayfasÄ± â€” ğŸŸ¢ BÃœYÃœK KISMI HAZIRDI (28 Haz 2026)

**Zaten vardÄ±:** Header (EKAP#/IKN, baÅŸlÄ±k, idare+il, rozetler, Takibe Al / Teklif HazÄ±rla / EKAP'ta GÃ¶rÃ¼ntÃ¼le), KPI grid (maliyet/son teklif/ilan tarihi/uyum), uyum skoru barÄ±, sekmeler (Ä°hale Bilgileri / Ä°lan Bilgileri / Belgeler), benzer ihaleler.
**Bu oturumda eklendi/dÃ¼zeltildi:**
- âœ… usul ham enum (`...SEARCH_METHOD.BARGAIN`) â†’ "PazarlÄ±k UsulÃ¼" (rozet + bilgi satÄ±rÄ±; `usulLabel`)
- âœ… **AI Analizi sekmesi** eklendi: `yapay_zeka_ozeti` varsa gÃ¶sterir (+analiz tarihi/tÃ¼r), yoksa "Teklif HazÄ±rla & Analiz Et" CTA'lÄ± bilgilendirme. TarayÄ±cÄ±da doÄŸrulandÄ±.

**Bu oturumda eklendi (28 Haz 2026):**
- âœ… **Kategori satÄ±rÄ±**: Ä°hale Bilgileri kartÄ±na `kategori` alanÄ± eklendi; tÄ±klanÄ±nca `ihaleler?kategori=X` filtreli lista aÃ§ar
- âœ… **URL parametresi**: `ihaleler.html` artÄ±k `?kategori=`, `?usul=`, `?tur=` URL parametrelerini de destekler

**Kalan (veri yok):** Ä°dare adres/telefon/toplantÄ± adresi, sÃ¶zleÅŸme bilgileri bloÄŸu (yÃ¼klenici/bedel/sÃ¼re) â€” sonuÃ§lanmÄ±ÅŸ ihale + idare detayÄ± toplanÄ±nca. CPV adÄ± (sadece OKAS kodu var).

---

## ğŸ“„ Ã–NCELÄ°K 5 â€” referans (orijinal plan)

> ihaleciler.com'daki tek ihale detay sayfasÄ± yapÄ±sÄ± (gÃ¶rsel: /tender/...)

### 5.1 Bloklar (yukarÄ±dan aÅŸaÄŸÄ±)
1. **Ãœst butonlar:** Not ekle | Takip et | TÃ¼mÃ¼nÃ¼ yazdÄ±r | Benzer ihale geÃ§miÅŸi
2. **Ä°hale bilgileri bloÄŸu:**
   - KayÄ±t no, Ä°hale baÅŸlÄ±ÄŸÄ±, Ä°ÅŸin adÄ±, YayÄ±n tarihi, Teklif tarihi, Ä°hale tÃ¼rÃ¼, Ä°hale usulÃ¼, Ä°hale kaynaÄŸÄ±, Teklif tÃ¼rÃ¼
3. **Kategori bilgileri bloÄŸu:**
   - Kategori, SektÃ¶r (CPV kodu + isim, Ã¶rn. `45234100 - Demiryolu Ä°nÅŸaatÄ± Ä°ÅŸleri`)
   - Butonlar: GÃ¼ncel ihaleler | GeÃ§miÅŸ ihaleler | Analiz
4. **Ä°dare bilgileri bloÄŸu:**
   - Ä°dare adÄ± (tam hiyerarÅŸi), adres, telefon, ÅŸehir, toplantÄ± adresi
   - Butonlar: GÃ¼ncel ihaleler | GeÃ§miÅŸ ihaleler | Analiz
5. **Ä°hale konusu / iÅŸin niteliÄŸi** (uzun metin)
6. **SÃ¶zleÅŸme bilgileri:**
   - Tarih, bedel, sÃ¼re, yÃ¼klenici, yÃ¼klenici uyruÄŸu, yÃ¼klenici adresi
7. **Footer:** "Bu ilan bilgilendirme amaÃ§lÄ±dÄ±r" + yayÄ±n tarihi

### 5.2 AI Analizi (bizim artÄ±mÄ±z)
- Gemini ile PDF analizi â†’ ihale ÅŸartnamesinden Ã¶zet, riskler, gereksinimler
- Detay sayfasÄ±nda "AI Analizi" sekmesi/bloÄŸu

---

## ğŸ“Š Ã–NCELÄ°K 6 â€” Analiz EkranlarÄ± (Firma & Kurum BazlÄ±) â€” ğŸŸ¡ KISMI (28 Haz 2026)

**YapÄ±ldÄ±:**
- âœ… **`kurum-analiz.html`** oluÅŸturuldu (`?kurum=IDARE_ADI` parametresiyle):
  - 4 KPI kartÄ±: Toplam Ä°hale / Aktif / Toplam BÃ¼tÃ§e / Kapsanan Ä°l
  - Genel BakÄ±ÅŸ sekmesi: YÄ±llÄ±k bar chart (Chart.js, `son_teklif_tarihi` fallback), Ä°hale TÃ¼rÃ¼ breakdown (yatay progress bar), Ä°l BazlÄ± DaÄŸÄ±lÄ±m
  - Ä°hale Listesi sekmesi: sayfalanmÄ±ÅŸ kart listesi (20/sayfa)
  - Dokunulan dosyalar: `kurum-analiz.html`
- âœ… **idare isimlerini tÄ±klanabilir** hale getirdi:
  - `ihaleler.html`: kart-idare â†’ `kurum-analiz?kurum=...`
  - `ihale-detay.html`: detay-idare + info-row Ä°dare â†’ `kurum-analiz?kurum=...`
- âœ… `ihaleler.html` `urlFiltreleriUygula`: `?idare=` parametresi desteklendi (kurum-analiz'den "TÃ¼m Ä°halelerini GÃ¶r" butonu)

- âœ… **`firma-analiz.html`** iskelet oluÅŸturuldu ve Genel BakÄ±ÅŸ gerÃ§ek veriyle dolduruldu (30 Haz 2026):
  - 4 KPI kart: Toplam KayÄ±t / Aktif Ä°hale / Kapsanan Ä°l / Kapsanan SektÃ¶r (gerÃ§ek sayÄ±mlar)
  - **Genel BakÄ±ÅŸ sekmesi**: YÄ±llÄ±k bar chart (Chart.js) + Ä°hale TÃ¼rÃ¼ progress bar + Ä°l DaÄŸÄ±lÄ±mÄ± + Kategori DaÄŸÄ±lÄ±mÄ±
  - SonuÃ§lar sekmesi "YakÄ±nda" placeholder (yÃ¼klenici verisi gelince doldurulacak)
- âœ… **`kurum-analiz.html` AylÄ±k Trend GrafiÄŸi** (30 Haz 2026): 24 aylÄ±k amber line chart Genel BakÄ±ÅŸ sekmesinde
  - Dokunulan dosyalar: `kurum-analiz.html`
- âœ… **`rekabet-analizi.html` Ä°l + Kategori filtresi** (30 Haz 2026): topbar'a 2 yeni dropdown; `yukleData()` server-side filtreler
  - Dokunulan dosyalar: `rekabet-analizi.html`
  - Ä°haleler sekmesi: mevcut DB'den idare/baÅŸlÄ±k eÅŸleÅŸmeli kayÄ±tlarÄ± sayfalÄ± listeler
  - TÃ¼m sidebar nav'lara Firma/Kurum Analizi linkleri eklendi
  - Dokunulan dosyalar: `firma-analiz.html`

**Kalan:**
- âš ï¸ Firma SonuÃ§lar & Genel BakÄ±ÅŸ sekmeleri: EKAP sonuÃ§ ilanÄ± scrape edilince gerÃ§ek veri gelecek (yÃ¼klenici adÄ±, sÃ¶zleÅŸme bedeli, tenzilat, KÄ°K kararlarÄ±)
- âš ï¸ 6.3 Ãœst navigasyon (Kategoriler/Åehirler/SektÃ¶rler/Ä°dareler/YÃ¼kleniciler/KÄ°K) â†’ veri tabanÄ± dolunca eklenir



> ihaleciler.com'un en gÃ¼Ã§lÃ¼ Ã¶zelliÄŸi bu â€” firma/kurum bazlÄ± detaylÄ± istatistik.

### 6.1 Firma (YÃ¼klenici) Analiz EkranÄ±
Bir firma seÃ§ilince gÃ¶sterilecek Ã¶zet (gÃ¶rsel 3'teki gibi):
- GeÃ§miÅŸ ihaleler (sayÄ± + Listele)
- Ä°ptal edilen ihaleler
- KÄ°K kararlarÄ±
- Devam eden (sayÄ± + toplam â‚º)
- Tamamlanan (sayÄ± + â‚º + â‚¬)
- Toplam iÅŸ bitirme (5 yÄ±l) (sÃ¶zleÅŸme sayÄ±sÄ± + â‚º)
- Toplam sÃ¶zleÅŸme (sayÄ± + â‚º + â‚¬)
- YÄ±llÄ±k ortalama
- Ortalama sÃ¶zleÅŸme bedeli
- **Ortalama tenzilat** (yÃ¼zde + tutar)
- Ortalama sÃ¶zleÅŸme sÃ¼resi (gÃ¼n)
- Ä°lk sÃ¶zleÅŸme tarihi / Son sÃ¶zleÅŸme tarihi

**Alt sekmeler:**
- **YÄ±llÄ±k** tablo: YÄ±l | Ort. katÄ±lÄ±mcÄ± | Ort. geÃ§erli teklif | Devam eden | Tamamlanan | Ortalama sÃ¶zleÅŸme bedeli | Toplam sÃ¶zleÅŸme
- **SektÃ¶rler** tablo: SektÃ¶r (CPV) | SektÃ¶r adÄ± | GÃ¼ncel | GeÃ§miÅŸ | Devam eden | Tamamlanan | Toplam sÃ¶zleÅŸme
- **Ä°dareler** tablo: Ä°dare adÄ± | GÃ¼ncel | GeÃ§miÅŸ | Devam eden | Tamamlanan | Toplam sÃ¶zleÅŸme

### 6.2 Kurum (Ä°dare) Analiz EkranÄ±
- Ä°dare bazlÄ± benzer istatistikler (o idarenin aÃ§tÄ±ÄŸÄ± tÃ¼m ihaleler, hangi firmalar kazanmÄ±ÅŸ vb.)

### 6.3 Ãœst navigasyon (ihaleciler.com menÃ¼sÃ¼)
ihaleciler.com'da Ã¼stte 6 ana kategori var, bunlarÄ± deÄŸerlendir:
- **Kategoriler** (kategori bazlÄ± ihale listesi + gÃ¼nlÃ¼k sayÄ±lar)
- **Åehirler** (il bazlÄ± + ilÃ§e kÄ±rÄ±lÄ±mÄ±)
- **SektÃ¶rler** (CPV kodu bazlÄ±)
- **Ä°dareler** (kurum bazlÄ±)
- **YÃ¼kleniciler** (firma bazlÄ±)
- **KÄ°K KararlarÄ±**

---

## ğŸ“Š Dashboard Ä°yileÅŸtirmeleri â€” âœ… TAMAM (30 Haz 2026)

**YapÄ±ldÄ± (dashboard.html):**
- âœ… **En Aktif Kurumlar** widget: aktif ihalelerdeki idare sayÄ±mÄ± (tÃ¼m kayÄ±tlar taranÄ±r, JS'te sÄ±ralanÄ±r), ilk 7 kurum amber progress bar + tÄ±klanabilir kurum-analiz linki ile
- âœ… **Son Eklenen Ä°haleler** widget: `ilan_tarihi` DESC son 6 ihale (30 Haz: `olusturulma` â†’ `ilan_tarihi` dÃ¼zeltildi), baÅŸlÄ±k + il + maliyet + yayÄ±n tarihi + son teklif tarihi; ihale-detay linki
- Ä°ki widget yan yana 2 kolonluk grid dÃ¼zeni, KPI grid altÄ±nda, filtre Ã¼stÃ¼nde
- âœ… **Kategori DaÄŸÄ±lÄ±mÄ± widget** eklendi: 12 renkli progress bar, tÄ±klanÄ±nca `ihaleler?kategori=X` aÃ§ar (28 Haz 2026)
- âœ… **KPI "BugÃ¼n Eklenen"**: `olusturulma` â†’ `ilan_tarihi` ile dÃ¼zeltildi (30 Haz 2026)
- âœ… **index.html "BugÃ¼n Eklenen" (harita + Ã¼st sayaÃ§lar)**: `olusturulma` â†’ `ilan_tarihi` dÃ¼zeltildi (30 Haz 2026)
- âœ… **`ihaleler.html` `sekme` URL parametresi**: `?sekme=guncel/gecmis/sonuc/detayli` ile doÄŸrudan sekme seÃ§imi; `sektorler.html` "GeÃ§miÅŸ" butonu bu parametreyi kullanÄ±yor

---

## ğŸ¤– AI ANALÄ°Z ALTYAPISI â€” âœ… TAMAMLANDI (28 Haz 2026)

**YapÄ±ldÄ±:**
- âœ… `backend/analiz_runner.py` oluÅŸturuldu (Gemini 2.5 Flash + Supabase)
- âœ… `backend/migration_ai_analiz.sql`: `yapay_zeka_ozeti`, `analiz_tarihi`, `analiz_pdf_turu` kolonlarÄ±
- âœ… `ihale-detay.html` AI Analizi sekmesi: 7 bÃ¶lÃ¼mlÃ¼ renkli kart render (Ã–ZET/KÄ°LÄ°T BÄ°LGÄ°LER/GÄ°RÄ°Å ENGELLERÄ°/MALÄ° YÃœKÃœMLÃœLÃœKLER/RÄ°SKLER/FIRSATLAR/TAVSÄ°YE)
- âœ… Ä°lk 3 analiz baÅŸarÄ±yla oluÅŸturuldu ve Supabase'e kaydedildi (3640-3998 karakter/analiz)
- âœ… Supabase wrapper'a `in_()` ve `is_()` metodlarÄ± eklendi (batch update + NULL filtre)

**KullanÄ±m:**
```
python analiz_runner.py --limit 20        # 20 ihale analiz et
python analiz_runner.py --ikn 2026/123456  # tek ihale
python analiz_runner.py --yenile          # daha Ã¶nce analizlenenleri yenile
```

---

## ğŸ§¹ VERÄ° TEMÄ°ZLÄ°K â€” âœ… TAMAMLANDI (28 Haz 2026)

**YapÄ±ldÄ±:**
- âœ… **Usul normalize**: 5538 kayÄ±t `SEARCH_METHOD.OPEN â†’ AÃ§Ä±k Ä°hale`; DiÄŸer (603), DoÄŸrudan Temin (1292), PazarlÄ±k 21/a (21), PazarlÄ±k 21/e (10) dÃ¼zeltildi
- âœ… **Usul normalize (kalan)**: PazarlÄ±k 21/b (234), 21/Ä± (248), 21/c (12), 21/f (29), BARGAIN (4), DiÄŸer (32) â€” tÃ¼m ham enum'lar temizlendi
- âœ… **Kategori backfill**: ~5500 kayÄ±t OKAS/CPV'den 32 kategori tÃ¼retildi; `in_()` batch ile
- âœ… **tur=YapÄ±m fallback**: 246 kayÄ±t `â†’ Ä°nÅŸaat & YapÄ±m` (kategori boÅŸ olanlar)
- âœ… **tur fallback (tam)**: Mal (4199) â†’ "Mal AlÄ±mÄ±", Hizmet (1236) â†’ "Hizmet AlÄ±mÄ±", DanÄ±ÅŸmanlÄ±k (3) â†’ "DanÄ±ÅŸmanlÄ±k"; kalan 9 OKAS kaydÄ± da dÃ¼zeltildi
- âœ… **Kategori dropdown gÃ¼ncellendi** (ihaleler.html): scraper ile tam uyumlu 50+ seÃ§enek; "Genel" (Mal AlÄ±mÄ±/Hizmet AlÄ±mÄ±/DanÄ±ÅŸmanlÄ±k) + "SektÃ¶r" optgroup'larÄ±
- âœ… **ekap_scraper.py** `kategori_tur()`: Mal/Hizmet/DanÄ±ÅŸmanlÄ±k tur fallback eklendi
- âœ… Supabase wrapper'a `in_()` batch + `is_()` NULL filtresi eklendi (timeout sorununu aÅŸtÄ±)
- âš ï¸ `ilk_gorulme` kolonu hÃ¢lÃ¢ yok â€” DDL gerektiriyor (Supabase SQL Editor'dan Ã§alÄ±ÅŸtÄ±r: `migration_ai_analiz.sql`)
- âš ï¸ `idx_ilanlar_analiz` btree index drop gerekiyor â€” `migration_fix_analiz_index.sql` Supabase SQL Editor'dan Ã§alÄ±ÅŸtÄ±r

---

## ğŸ”§ Ã–NCELÄ°K 7 â€” AltyapÄ± / Entegrasyonlar â€” ğŸŸ¡ KISMI (28 Haz 2026)

**YapÄ±ldÄ± (scraper kalite iyileÅŸtirmeleri):**
- âœ… `usul_donustur`: EKAP ham enum (`TENDER_SEARCH.ENUMERATIONS.OPEN` vb.) â†’ TÃ¼rkÃ§e etiket (`AÃ§Ä±k Ä°hale`, `PazarlÄ±k UsulÃ¼` vb.) haritasÄ± eklendi
- âœ… `supabase_yaz`: 2-pass upsert â€” yeni kayÄ±tlarda `olusturulma` korunur, gÃ¼ncellemelerde Ã¼zerine yazÄ±lmaz ("BugÃ¼n Eklenen" ÅŸiÅŸkinliÄŸi Ã¶nlendi)
- âœ… `tur_donustur`: "Kiralama" tipi eklendi

**Bu oturumda yapÄ±ldÄ± (scraper kalite iyileÅŸtirmeleri â€” 28 Haz 2026):**
- âœ… `mojibake_duzelt()`: UTF-8 metin Latin-1 olarak yanlÄ±ÅŸ decode edilmiÅŸse onarÄ±r; `baslik`/`idare`/`il` alanlarÄ±na uygulandÄ±
- âœ… `kategori_tur()`: OKAS/CPV kodunun ilk 2 hanesinden 40+ kategori haritasÄ±; `tur`'dan fallback. `kategori` kolonu artÄ±k scraper'da doldurulacak
- âœ… `ilan_tarihi` Ã§Ä±karma: `detay_cek()` â†’ `ilanList[0].ilanTarihi/tarih/yayimTarihi/baslangicTarihi` ve `bilgi.ilanTarihi` fallback zinciri; `ihaleleri_isle()` â†’ liste response alanlarÄ±ndan da fallback
- âš ï¸ Debug print'ler eklendi â€” scraper Ã§alÄ±ÅŸÄ±nca hangi field adÄ±nÄ±n dolu geldiÄŸi gÃ¶rÃ¼lecek; yanlÄ±ÅŸ field adÄ±ysa dÃ¼zeltilmeli
- âš ï¸ `ilk_gorulme TIMESTAMPTZ DEFAULT NOW()` kolonu Supabase'de manuel eklenecek

**Kalan:**

### 7.1 EKAP Scraper (worker.py)
- Playwright ile EKAP'tan dinamik auth token yakalama
- 15 kategori iÃ§in scraping listesi
- `ilanlar` tablosuna yazma
- Webshare.io rotating proxy entegrasyonu (IP ban Ã¶nleme) â€” **credentials hÃ¢lÃ¢ boÅŸ**

### 7.2 Ä°yzico Ã–deme
- `iyzipay==1.0.46`
- Merchant credentials **hÃ¢lÃ¢ boÅŸ** (.env)
- `odeme_loglari` tablosunda UNIQUE `payment_id` (webhook replay korumasÄ±) â€” kurulu

### 7.3 AI (Gemini)
- PDF analizi: pdfplumber (metin) + Gemini Vision (taranmÄ±ÅŸ belge fallback)
- SonuÃ§lar Supabase'de cache'lenir (tekrar API Ã§aÄŸrÄ±sÄ± Ã¶nleme)

---

## ğŸ¯ Ã–NCELÄ°K 8 â€” UX Felsefesi (Genel Ä°lke)

> **"ihaleciler.com kadar gÃ¼Ã§lÃ¼, ama yarÄ±sÄ± kadar kalabalÄ±k."**

- ihaleciler.com'un filtre gÃ¼cÃ¼nÃ¼ al, ama gÃ¶rsel yoÄŸunluÄŸunu azalt
- DetaylÄ± Ara'yÄ± varsayÄ±lan deÄŸil, "ileri seviye" olarak konumla â€” sade kullanÄ±cÄ± 4-5 filtreyle iÅŸ gÃ¶rsÃ¼n
- Harita ana sayfada Ã¶ne Ã§Ä±ksÄ±n (ihalegram'daki gibi) â€” gÃ¶rsel ve davetkÃ¢r
- Renk paleti: mevcut koyu lacivert/turuncu tema korunsun (ihaleglobal kimliÄŸi)

---

## âœ… Ã–nerilen SÄ±ra (Code modunda hangi sÄ±rayla yapalÄ±m)

1. **Redirect loop'u tÃ¼mden Ã§Ã¶z** (1.1) â€” site aÃ§Ä±lmadan hiÃ§bir ÅŸey test edilemez
2. **worker.py Ã§alÄ±ÅŸtÄ±r, ilanlar tablosunu doldur** (1.4) â€” veri olmadan harita/arama boÅŸ
3. **GeliÅŸmiÅŸ arama + filtreler** (3) â€” Ã§ekirdek iÅŸlev
4. **Ä°hale listesi kartlarÄ±** (4) â€” verinin gÃ¶sterimi
5. **Ä°hale detay sayfasÄ±** (5)
6. **TÃ¼rkiye haritasÄ±** (2) â€” gÃ¶rsel vitrin
7. **Firma/Kurum analiz ekranlarÄ±** (6) â€” ileri Ã¶zellik
8. **Ä°yzico + AI** (7) â€” para kazanma + katma deÄŸer

---
---

# ğŸ†š Ã–NCELÄ°K 9 â€” REKABET ANALÄ°ZÄ° & Ã–ZELLÄ°K AÃ‡IKLARI (29 Haz 2026)

> **Kaynak:** 29 Haziran 2026'da **tendermeister.com** ve **ihaleciler.com** canlÄ± hesaplarla uÃ§tan uca gezildi
> (tendermeister'da tarama Ã§alÄ±ÅŸtÄ±rÄ±ldÄ±: 16 portaldan 136 ihale; ihaleciler'de firma analizi + KÄ°K kararlarÄ± aÃ§Ä±ldÄ±).
> **AmaÃ§:** ihaleglobal.com'da bu iki sitedeki HÄ°Ã‡BÄ°R Ã¶nemli Ã¶zelliÄŸin eksiÄŸi kalmasÄ±n. AÅŸaÄŸÄ±daki maddeler,
> "bizde var / kÄ±smen var / yok" olarak iÅŸaretlendi ve P0â€“P3 Ã¶ncelik verildi.
>
> **Ä°ÅŸaretler:** ğŸŸ¢ bizde var Â· ğŸŸ¡ kÄ±smen/iskelet var Â· ğŸ”´ yok (eklenecek) Â· ğŸ§± veri-baÄŸÄ±mlÄ± (Ã¶nce scraper)

## 9.0 ÃœÃ§ Ã¼rÃ¼nÃ¼n tek bakÄ±ÅŸta karÅŸÄ±laÅŸtÄ±rmasÄ±

| Eksen | ihaleglobal (biz) | tendermeister | ihaleciler.com |
|---|---|---|---|
| **Konum** | TR / EKAP | DE menÅŸeli, AB+DE+TR | TR (kÃ¶klÃ¼) |
| **Kaynaklar** | EKAP | EU TED + 16 DE eyalet portalÄ± + Bund.de + TR eKAP (18) | EKAP + Gazete + Ä°stihbarat (Ã¶zel) |
| **Ã‡ekirdek deÄŸer** | Takip + AI ÅŸartname analizi | AI eÅŸleÅŸme + ihale-baÅŸÄ±na AI teklif workflow | Veri zenginliÄŸi + firma/idare analitiÄŸi |
| **AI eÅŸleÅŸme** | basit aÄŸÄ±rlÄ±klÄ± uyum % | semantik AI skor + %70 bildirim eÅŸiÄŸi | yok (manuel filtre) |
| **Firma/idare analizi** | ğŸŸ¡ iskelet | yok | ğŸŸ¢ derin pivot (amiral gemisi) |
| **SonuÃ§/sÃ¶zleÅŸme verisi** | ğŸ”´ yok | n/a | ğŸŸ¢ var (analitiÄŸin temeli) |
| **KÄ°K kararlarÄ±** | ğŸ”´ yok | yok | ğŸŸ¢ 34.7k karar |
| **AI teklif yazÄ±mÄ±** | ğŸŸ¡ teklif-olustur.html (backend baÄŸÄ± eksik) | ğŸŸ¢ KO tarayÄ±cÄ± + form doldurma + konsept yazÄ±cÄ± | yok |
| **Ã‡oklu dil** | TR | TR/EN/DE/FR/AR | TR |
| **Fiyat** | Free / â‚º1.490 / â‚º3.990 | â‚¬299 / â‚¬499 / â‚¬899 | abonelik |

> **Stratejik okuma:** TÃ¼rkiye pazarÄ±nda asÄ±l rakip **ihaleciler.com** (veri + analitik). tendermeister ise
> **Ã¼rÃ¼n/AI vizyonu** aÃ§Ä±sÄ±ndan nereye gideceÄŸimizi gÃ¶steriyor (AI Brain + ihale-baÅŸÄ±na teklif workflow'u).
> Ä°kisinin kesiÅŸiminde durursak ("ihaleciler'in verisi + tendermeister'in AI'Ä±, daha sade arayÃ¼zle") fark yaratÄ±rÄ±z.

---

## 9.1 ğŸ§± P0 â€” SONUÃ‡ / SÃ–ZLEÅME VERÄ°SÄ° (her ÅŸeyin temeli) â€” ğŸŸ¢ Ã‡ALIÅIYOR, VERÄ° AKIYOR (1 Tem 2026)

> Bu olmadan firma-analiz, idare-analiz, "SonuÃ§" sekmesi, rekabet/fiyat istihbaratÄ± ve uyum skorunun
> "kazanma oranÄ±" iddiasÄ± BOÅ kalÄ±r. ihaleciler'in tÃ¼m gÃ¼cÃ¼ bu veriden geliyor. **En kritik aÃ§Ä±k.**

### âœ… 1 Tem 2026 â€” UÃ§tan uca Ã§alÄ±ÅŸan pipeline kuruldu ve canlÄ± veri akÄ±yor

**Ã–nemli dÃ¼zeltme:** `backend/migration_sonuc_schema.sql` (29 Haz) hiÃ§ Supabase SQL Editor'dan Ã§alÄ±ÅŸtÄ±rÄ±lmamÄ±ÅŸ â€”
onun yerine Supabase'de **farklÄ±, daha eski bir `ihale_sonuclari` ÅŸemasÄ±** zaten kuruluydu (muhtemelen bir
Ã¶nceki oturumdan): `ilan_id` (ilanlar.id UUID FK) + `kazanan_firma` / `kazanan_teklif` / `en_dusuk_teklif` /
`en_yuksek_teklif` / `toplam_teklif_sayisi` / `kazanan_teklif_farki_yuzde` / `sonuc_tarihi` / `tum_teklifler` (jsonb).
`yukleniciler` ve `scrape_log` tablolarÄ± ise hiÃ§ oluÅŸturulmamÄ±ÅŸ (DDL gerektiriyor, SQL Editor'dan manuel).

**DoÄŸru EKAP endpoint'i bulundu:** `ekap_sonuc_scraper.py --probe` Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± â€” ihale bazlÄ± "sonuÃ§" endpoint'leri
(`GetByIhaleIdSonucIlan` vb.) hepsi 404 verdi. Ama zaten **Ã§alÄ±ÅŸan** `GetByIhaleIdIhaleDetay` endpoint'i (ana
scraper'da aktif ihale detayÄ± iÃ§in kullanÄ±lÄ±yor), ihale "Result Announcement Published" (durum kodu **"15"**)
durumundaysa yanÄ±tÄ±na **`sozlesmeBilgiList`** (yÃ¼klenici adÄ±, sÃ¶zleÅŸme bedeli, en yÃ¼ksek/dÃ¼ÅŸÃ¼k teklif, sÃ¶zleÅŸme
tarihi) ve **`ilanList[].veriHtml`** iÃ§inde tam "SONUÃ‡ Ä°LANI" HTML metnini (teklif sayÄ±larÄ± dahil) veriyor.
Yani ayrÄ± bir "sonuÃ§ endpoint'i" yok â€” zaten var olan detay endpoint'i, sonuÃ§lanan ihalelerde otomatik olarak
sonuÃ§ bilgisini de iÃ§eriyor.

**Verimli tarama yÃ¶nÃ¼ bulundu (deneme-yanÄ±lmayla):** Kendi DB'mizdeki "son_teklif_tarihi geÃ§miÅŸ" ilanlarÄ± tek
tek EKAP'ta aratmak (IKN ile) Ã§ok dÃ¼ÅŸÃ¼k isabet verdi (rastgele Ã¶rneklemde 0/15, 0/9, 0/4) â€” Ã§Ã¼nkÃ¼ Ã§oÄŸu idare
"SonuÃ§ Ä°lanÄ±"nÄ± hiÃ§ yayÄ±nlamÄ±yor ya da aylarca gecikmeli yayÄ±nlÄ±yor; bizdeki "tarih geÃ§miÅŸ" olmasÄ± EKAP'ta
sonuÃ§landÄ±ÄŸÄ± anlamÄ±na gelmiyor. **DoÄŸru yÃ¶n tam tersi:** EKAP'Ä±n zaten `ihaleDurumIdList=[5]` filtresiyle
"sonuÃ§lanmÄ±ÅŸ" (1.68M kayÄ±t) listesini baÅŸtan sayfalayÄ±p, her sayfadaki IKN'leri bizim ~12.7k IKN'lik kendi
`ilanlar` tablomuzla kesiÅŸtirmek â€” ilk 1000 kayÄ±tta 7 isabet (%0.7) bulundu, Ã§ok daha verimli.

- âœ… **`backend/ekap_sonuc_backfill.py`** (yeni script â€” `ekap_sonuc_scraper.py`'nin varsayÄ±mlarÄ± gÃ¼ncel ÅŸemayla
  uyuÅŸmadÄ±ÄŸÄ± iÃ§in ayrÄ± yazÄ±ldÄ±, o dosyaya dokunulmadÄ±):
  - Kendi `ilanlar` tablosunu `{ikn: {id, yaklasik_maliyet_min, ...}}` olarak indeksler
  - EKAP'Ä±n durum=5 (sonuÃ§lanmÄ±ÅŸ) listesini sayfalar, IKN eÅŸleÅŸmesi bulunca `GetByIhaleIdIhaleDetay` Ã§aÄŸÄ±rÄ±r
  - **Bulunan veri kalitesi sorunlarÄ± ve dÃ¼zeltmeleri:**
    - `sozlesmeBilgiList.yaklasikMaliyet(Degeri)` alanÄ± EKAP'ta gÃ¶zlemlenen Ã¶rneklerde **10x hatalÄ±** geliyor
      (Ã¶rn. gerÃ§ek 26.737.250 TL yerine 267.372.500 TL) â†’ bunun yerine **SONUÃ‡ Ä°LANI HTML metnindeki**
      "YaklaÅŸÄ±k Maliyeti" rakamÄ± regex ile Ã§Ä±karÄ±lÄ±p kullanÄ±lÄ±yor (`html_yaklasik_maliyet_parse`)
    - `ilanList` bazen hem orijinal ilanÄ± hem sonuÃ§ ilanÄ±nÄ± iÃ§eriyor, sÄ±ra garanti deÄŸil â†’
      "SONUÃ‡ Ä°LANI" baÅŸlÄ±ÄŸÄ±nÄ± taÅŸÄ±yan girdi Ã¶zellikle aranÄ±yor (`sonuc_ilan_html_bul`)
    - BazÄ± (Ã§ok kÄ±sÄ±mlÄ±/ithal) ihalelerde sÃ¶zleÅŸme bedeli **USD/EUR** cinsinden geliyor ama alan sayÄ±sal â€”
      TRY sanÄ±lÄ±rsa tenzilat hesabÄ± tamamen bozuluyor â†’ para birimi tespit edilirse o kayÄ±t atlanÄ±yor
    - Mojibake (TÃ¼rkÃ§e karakter bozulmasÄ±) `mojibake_duzelt()` ile dÃ¼zeltiliyor
  - Checkpoint dosyasÄ± (`.sonuc_backfill_checkpoint.json`) ile kaldÄ±ÄŸÄ± yerden devam eder (kesintiye dayanÄ±klÄ±)
  - `--dry-run` ile DB'ye yazmadan test edilebilir
- âœ… **CanlÄ± veri akÄ±yor â€” ilk gerÃ§ek parti tamamlandÄ± (1 Tem 2026)**: `ihale_sonuclari` tablosuna **15 gerÃ§ek
  sonuÃ§ kaydÄ±** yazÄ±ldÄ± (Ã¶rn. "KESKÄ°NLER GLOBAL DANIÅMANLIK... â€” 13.120.750 TL, tenzilat %50.93",
  "AKSU OTOM.PET... â€” 26.680.000 TL, tenzilat %5.26" vb.).
  **Ã–nemli gÃ¶zlem â€” plato tespit edildi:** EKAP'Ä±n sonuÃ§lanmÄ±ÅŸ (durum=5) listesi tarandÄ±kÃ§a, bizim ~12.7k IKN'lik
  havuzla kesiÅŸim sadece listenin **ilk ~16-20 bin kaydÄ±nda** yoÄŸunlaÅŸÄ±yor; skip=22.100'e kadar (toplam ~22k
  kayÄ±t tarandÄ±) yeni eÅŸleÅŸme Ã§Ä±kmadÄ±, skip=100k/300k/600k/1M nokta kontrollerinde de sÄ±fÄ±r eÅŸleÅŸme bulundu.
  Bu beklenen bir durum: EKAP listesi bÃ¼yÃ¼k ihtimalle yakÄ±n zamanda sonuÃ§lanan ihaleleri Ã¶nce veriyor ve bizim
  `ilanlar` tablomuz da esasen "yakÄ±n zamanda aktifti" ihalelerden oluÅŸuyor â€” iki kÃ¼me sadece dar bir pencerede
  kesiÅŸiyor. **Script artÄ±k bunu otomatik yÃ¶netiyor**: son 100 sayfada (10.000 kayÄ±t) hiÃ§ yeni kayÄ±t yazÄ±lmazsa
  plato tespit edilip tarama kendiliÄŸinden durur (boÅŸuna binlerce istek atÄ±lmÄ±yor).
- âœ… **Frontend baÄŸlandÄ± (`ihaleler.html` + `ihale-detay.html`)**: "SonuÃ§" sekmesi artÄ±k gerÃ§ek veriyle Ã§alÄ±ÅŸÄ±yor â€”
  eskiden hiÃ§ dolmayan `ilanlar.durum='sonuclandi'` filtresi yerine PostgREST'in **otomatik FK embed**
  Ã¶zelliÄŸi kullanÄ±ldÄ±: `ilanlar?select=...,ihale_sonuclari!inner(...)` (view/RPC gerekmeden, FK zaten
  tanÄ±nÄ±yor). Her ihale kartÄ±na, sonucu varsa yeÅŸil "âœ“ SonuÃ§landÄ± â€” Kazanan: X Â· â‚ºY Â· Tenzilat %Z" bloÄŸu
  eklendi (diÄŸer sekmelerde de sonuÃ§ varsa gÃ¶steriliyor). Sekme sayacÄ± da `ihale_sonuclari` COUNT'una baÄŸlandÄ±.
  `ihale-detay.html` sayfa baÅŸlÄ±ÄŸÄ±nÄ±n altÄ±na da aynÄ± bilgiyi gÃ¶steren bir blok eklendi (`sonucBilgiGoster()`).
  Dokunulan dosyalar: `ihaleler.html`, `ihale-detay.html`
- **Kalan (bir sonraki oturum):**
  - **Hacmi bÃ¼yÃ¼tmenin gerÃ§ek yolu bu script'i daha sÄ±k koÅŸmak DEÄÄ°L** (aynÄ± skip aralÄ±ÄŸÄ±nÄ± tekrar tekrar
    taramak aynÄ± platoyu verir) â€” asÄ±l kaldÄ±raÃ§ **ana `ekap_scraper.py`'nin her gece daha fazla/farklÄ± ihale
    keÅŸfetmesi** (yeni aktif ihaleler zamanla sonuÃ§lanÄ±p bu havuza girecek) ve/veya EKAP'Ä±n durum=5 listesinde
    farklÄ± bir sÄ±ralama/filtre parametresi bulup (Ã¶rn. tarih aralÄ±ÄŸÄ± filtresi varsa) hedefli tarama yapmak.
    `--start-skip` ile farklÄ± bir aralÄ±k da denenebilir ama Ã¶nce spot-check yapÄ±lmalÄ± (bu oturumda 100k/300k/
    600k/1M noktalarÄ±nda sÄ±fÄ±r Ã§Ä±ktÄ±, yani rastgele ileri atlamak muhtemelen boÅŸuna).
  - `yukleniciler` + `scrape_log` tablolarÄ± hÃ¢lÃ¢ yok (DDL â€” Supabase SQL Editor'dan elle Ã§alÄ±ÅŸtÄ±rÄ±lmalÄ±);
    olmadan da `ihale_sonuclari` tek baÅŸÄ±na SonuÃ§ sekmesi + gelecekteki firma-analiz iÃ§in yeterli veri saÄŸlÄ±yor
  - Ã‡ok kÄ±sÄ±mlÄ± (kÄ±sÄ±m/lot) ihalelerde ÅŸu an sadece ilk `sozlesmeBilgiList[0]` kaydediliyor â€” Ã§oklu kazanan
    firma senaryosu (aynÄ± ihalede birden fazla lot/kazanan) tek satÄ±ra sÄ±ÄŸmÄ±yor; ileride ayrÄ± bir
    `ihale_sonuclari_kisim` tablosu gerekebilir

- [x] ğŸŸ¢ **DB ÅŸemasÄ± hazÄ±rlandÄ±**: `backend/migration_sonuc_schema.sql` (29 Haz 2026)
  - `ihale_sonuclari` tablosu (yÃ¼klenici, sÃ¶zleÅŸme bedeli, tenzilat, katÄ±lÄ±mcÄ± sayÄ±sÄ± vb.)
  - `yukleniciler` tablosu (firma sÃ¶zlÃ¼ÄŸÃ¼: normalize_ad, ciro, sÃ¶zleÅŸme sayÄ±sÄ±)
  - `scrape_log` tablosu (hangi ihaleler denendi, baÅŸarÄ±lÄ± mÄ±?)
  - `ilanlar_sonuc` VIEW (ilanlar + ihale_sonuclari join)
  - `idare_sayim()` ve `kategori_sayim()` RPC fonksiyonlarÄ± (performans iÃ§in)
  - âš ï¸ **Ã‡alÄ±ÅŸtÄ±r**: Supabase SQL Editor'dan `backend/migration_sonuc_schema.sql`
- [x] ğŸŸ¢ **`backend/ekap_sonuc_scraper.py`** oluÅŸturuldu (29 Haz 2026)
  - `--probe` modu: 1-11 arasÄ± durum kodlarÄ± + tÃ¼m endpoint kombinasyonlarÄ±nÄ± test eder
  - `--limit N`, `--ikn IKN`, `--all`, `--retry-failed` parametreleri
  - 5 farklÄ± EKAP sonuÃ§ endpoint'i sÄ±rayla denenir (kesinlesme/sonuc_ilan/karar/sozlesme/sonuc_detay)
  - `yukleniciler` tablosuna upsert (normalize_ad ile dedup + ciro/sayÄ± gÃ¼ncelleme)
  - âš ï¸ **Ã–nce probe Ã§alÄ±ÅŸtÄ±r**: `python ekap_sonuc_scraper.py --probe`
- [ ] ğŸ”´ **EKAP sonuÃ§ ilanÄ± (kesinleÅŸen ihale kararÄ± / sÃ¶zleÅŸme) scrape'i** â€” `ekap_scraper.py`'a yeni akÄ±ÅŸ:
  - Ã‡ekilecek alanlar: **yÃ¼klenici adÄ± + vergi no/uyruk**, **sÃ¶zleÅŸme bedeli**, **yaklaÅŸÄ±k maliyet**, **tenzilat %**,
    **katÄ±lÄ±mcÄ± sayÄ±sÄ±**, **geÃ§erli teklif sayÄ±sÄ±**, **sÃ¶zleÅŸme tarihi**, **iÅŸe baÅŸlama/bitiÅŸ**, **iÅŸ bitirme belgesi tutarÄ±**.
  - EKAP v2'de sonuÃ§ endpoint'i araÅŸtÄ±r (`GetByIhaleIdSonucIlan` / `KesinlesenIhaleKarari` benzeri); yoksa
    "SonuÃ§ Ä°lanÄ±" HTML'ini ayrÄ±ÅŸtÄ±r.
- [ ] ğŸ”´ **DB ÅŸemasÄ±**: `ilanlar`a sonuÃ§ kolonlarÄ± veya ayrÄ± `ihale_sonuclari` + `firma_istatistikleri` tablosu
  (PLATFORM_CONTEXT'te zaten planlÄ± â€” hayata geÃ§ir). YÃ¼klenici adlarÄ±nÄ± normalize et (tekil firma anahtarÄ±).
- [ ] ğŸ”´ **`yukleniciler` tablosu** (firma sÃ¶zlÃ¼ÄŸÃ¼): ad, vergi no, normalize_ad, toplam sÃ¶zleÅŸme, sektÃ¶r[].
- **Tahmini etki:** Bu tek iÅŸ, 9.2 + 9.3 + 9.7'nin Ã¶nÃ¼nÃ¼ aÃ§ar. **Ä°lk yapÄ±lacak P0 bu.**

> âœ… **Ã–nemli dÃ¼zeltme (29 Haz 2026):** "hangi idare / hangi sektÃ¶r" verisi ASLINDA ZATEN YAZILIYOR.
> `ekap_scraper.py` upsert kaydÄ±nda: `idare` (idareAdi) âœ…, `il` âœ…, `okas` (CPV/OKAS kodu) âœ…,
> `kategori` (OKAS'tan tÃ¼retiliyor) âœ…. Yani her ihalenin idaresi ve sektÃ¶rÃ¼ DB'de var.
> **Eksik olan Ã¼Ã§ ÅŸey:** (1) idare bazlÄ± **arama/dizin sayfasÄ±** (9.9), (2) **CPV-kodu seviyesinde sektÃ¶r**
> gezinmesi â€” ÅŸu an sadece OKAS ilk-2-hane ana kategori var (9.9), (3) **geÃ§miÅŸte ihale alan firma listesi**
> = yÃ¼klenici/sonuÃ§ verisi (bu madde, 9.1). Yani idare/sektÃ¶r iÃ§in "veri yok" deÄŸil, "arama yÃ¼zeyi yok".

### 9.1.1 ğŸ•°ï¸ GeÃ§miÅŸ (bugÃ¼nden Ã¶nceki) veri & kaynak â€” HUKUKÄ° NOT

> KullanÄ±cÄ± sorusu: "GeÃ§miÅŸe yÃ¶nelik veriyi Ã§ekmek iÃ§in ihaleciler.com'dan veri Ã§ekebilir miyiz?"
> **KÄ±sa cevap: Teknik olarak mÃ¼mkÃ¼n ama YAPMA â€” yanlÄ±ÅŸ kaynak. DoÄŸru kaynak EKAP'Ä±n kendisi.**

- â›” **ihaleciler.com'dan veri kazÄ±mak RÄ°SKLÄ° ve YANLIÅ:**
  - ihaleciler'in derlenmiÅŸ veritabanÄ± onlarÄ±n **emeÄŸi/Ã¼rÃ¼nÃ¼**; kullanÄ±m ÅŸartlarÄ± otomatik veri Ã§ekmeyi yasaklar.
  - Bir rakibin DB'sini kopyalayÄ±p **kendi ticari Ã¼rÃ¼nÃ¼mÃ¼zde** kullanmak TÃ¼rkiye'de **haksÄ±z rekabet** (TTK m.54-55)
    ve sÃ¶zleÅŸme ihlali riski doÄŸurur; Ã¼stelik bunu **kendi Ã¼cretli hesabÄ±mÄ±zla** yapmak ihlali ikiye katlar (hesap kapatma + hukuki risk).
  - OnlarÄ±n verisi de zaten Ã§oÄŸunlukla EKAP'tan tÃ¼retilmiÅŸ â€” yani aracÄ±dan kopyalamak yerine **kaynaÄŸa gitmek** hem
    yasal hem daha saÄŸlam (onlarÄ±n scrape hatalarÄ±/gecikmeleri bize miras kalmaz).
- âœ… **DOÄRU yol â€” geÃ§miÅŸ & sonuÃ§ verisini doÄŸrudan EKAP'tan al (kamuya aÃ§Ä±k):**
  - EKAP **Ä°hale SonuÃ§ Ä°lanlarÄ± / KesinleÅŸen Ä°hale KararlarÄ±**'nÄ± KAMUYA aÃ§Ä±k yayÄ±nlar â†’ yÃ¼klenici, sÃ¶zleÅŸme bedeli,
    tenzilat, katÄ±lÄ±mcÄ± sayÄ±sÄ± burada. Bunlar bizim **meÅŸru** geÃ§miÅŸ-veri kaynaÄŸÄ±mÄ±z.
  - [ ] ğŸ”´ **GeÃ§miÅŸ ihale backfill akÄ±ÅŸÄ±**: mevcut scraper sadece AKTÄ°F listeyi Ã§ekiyor (`GetListByParameters` ~11.878).
    KapanmÄ±ÅŸ/geÃ§miÅŸ ihaleleri ve sonuÃ§ ilanlarÄ±nÄ± Ã§ekmek iÃ§in: tarih aralÄ±ÄŸÄ±/sayfalama ile **geÃ§miÅŸe doÄŸru tara**
    (EKAP v2'de kapanmÄ±ÅŸ ihale + sonuÃ§ endpoint'lerini test et; yoksa sonuÃ§ ilanÄ± HTML'ini ayrÄ±ÅŸtÄ±r).
  - [ ] ğŸ”´ Backfill'i **incremental + idempotent** yaz (ikn bazlÄ± upsert, dedup) â€” bir kez geÃ§miÅŸi doldur, sonra gÃ¼nlÃ¼k ekle.
  - âš ï¸ Gece Actions 45dk limiti â†’ backfill'i ayrÄ±, manuel/parÃ§a parÃ§a Ã§alÄ±ÅŸan bir job olarak kur (cron deÄŸil).
- â„¹ï¸ **ihaleciler'in "Ä°stihbarat" kaynaÄŸÄ±** (Ã¶zel/erken intel) EKAP'ta YOK â€” o onlarÄ±n Ã¶zel katma deÄŸeri.
  Onu kopyalayamayÄ±z/kopyalamamalÄ±yÄ±z; karÅŸÄ±lÄ±ÄŸÄ±nÄ± **kendi "Ã¶zel sektÃ¶r alÄ±m ilanlarÄ±"** modÃ¼lÃ¼mÃ¼zle (9.6) kurarÄ±z.


---

## 9.2 ğŸ“Š P1 â€” FÄ°RMA (YÃœKLENÄ°CÄ°) & Ä°DARE ANALÄ°ZÄ° (ihaleciler amiral gemisi) â€” ğŸŸ¡ Ä°SKELET VAR

> ihaleciler'in `/analyze` ekranÄ±: bir yÃ¼klenici/idare/sektÃ¶r iÃ§in Ã§ok-boyutlu pivot. Her satÄ±rda "Listele" ile
> alttaki ihalelere iniliyor. Bizim `firma-analiz.html` + `kurum-analiz.html` iskeleti var ama veri yok.

- [ ] ğŸ§± **firma-analiz.html'i gerÃ§ek veriye baÄŸla** (9.1 sonrasÄ±). Pivot tablolarÄ± (ihaleciler birebir):
  - **YÄ±llÄ±k**: YÄ±l Â· Ort. katÄ±lÄ±mcÄ± Â· Ort. geÃ§erli teklif Â· Devam eden Â· Tamamlanan Â· Ort. sÃ¶zleÅŸme bedeli Â· Toplam sÃ¶zleÅŸme
  - **SektÃ¶rler (CPV)**: CPV kodu Â· ad Â· GÃ¼ncel Â· GeÃ§miÅŸ Â· Devam eden Â· Tamamlanan Â· Toplam sÃ¶zleÅŸme
  - **Ä°dareler**: idare (tam hiyerarÅŸi) Â· aynÄ± kÄ±rÄ±lÄ±m
  - **YÃ¼kleniciler (rakipler)**: aynÄ± sektÃ¶rde yarÄ±ÅŸan firmalar
  - **Åehirler / Ä°hale tÃ¼rÃ¼ / Ä°hale usulÃ¼ / Teklif tÃ¼rÃ¼**: aynÄ± kÄ±rÄ±lÄ±m
  - Ãœst KPI: Ortalama tenzilat %, ort. sÃ¶zleÅŸme sÃ¼resi, ilk/son sÃ¶zleÅŸme tarihi, toplam iÅŸ bitirme (5 yÄ±l)
- [ ] ğŸ§± **kurum-analiz.html'i derinleÅŸtir**: o idarenin aÃ§tÄ±ÄŸÄ± tÃ¼m ihaleler, hangi firmalar kazanmÄ±ÅŸ,
  ortalama tenzilat, tekrar eden yÃ¼kleniciler (idare-firma iliÅŸki aÄŸÄ±).
- [ ] ğŸ”´ **`/analyze` esnek motoru**: herhangi bir filtre kombinasyonuna (firma+sektÃ¶r+il) pivot Ã¼retebilen
  tek bir analiz endpoint'i (ihaleciler bunu yapÄ±yor). Supabase RPC (GROUP BY) ile performanslÄ± yaz.
- ğŸŸ¢ Not: Bizim artÄ±mÄ±z â†’ bu ekranlara **AI yorumu** ekleyebiliriz ("bu firma X idaresinde gÃ¼Ã§lÃ¼, tenzilatÄ± dÃ¼ÅŸÃ¼k").

### 9.2.1 ğŸ” FÄ°RMA ARAÅTIRMA MODÃœLÃœ (yeni â€” kullanÄ±cÄ± isteÄŸi 29 Haz 2026) â€” ğŸ”´ YOK

> KullanÄ±cÄ± net istedi: "geÃ§miÅŸte o iÅŸleri almÄ±ÅŸ firmalarÄ±" araÅŸtÄ±rabileceÄŸimiz bir **firma araÅŸtÄ±rma / firma
> istihbarat** modÃ¼lÃ¼. **Kaynak = EKAP sonuÃ§ ilanlarÄ± (kamuya aÃ§Ä±k olgu), ihaleciler DEÄÄ°L.** Olgular serbest;
> derlemeyi biz yaparÄ±z. Bu modÃ¼l, P0 sonuÃ§ verisi (9.1) gelince hayata geÃ§er; `firma-analiz.html` bunun temeli.

**Veri (9.1'den gelir):** `yukleniciler` tablosu (firma sÃ¶zlÃ¼ÄŸÃ¼: ad, normalize_ad, vergi_no?, il, sektÃ¶r[]) +
`ihale_sonuclari` (ihale â†” kazanan firma â†” sÃ¶zleÅŸme bedeli, tenzilat, katÄ±lÄ±mcÄ±/geÃ§erli teklif sayÄ±sÄ±, tarih).

**(a) Firma Dizini / Arama** (`/firmalar` veya yÃ¼kleniciler dizini, 9.9):
- [ ] ğŸ”´ Firma adÄ±na gÃ¶re arama + sektÃ¶r/ÅŸehir filtresi; toplam ciroya gÃ¶re sÄ±ralama; sayfalama.
- [ ] ğŸ”´ Her firma kartÄ±: ad, ÅŸehir, toplam sÃ¶zleÅŸme sayÄ±sÄ±, toplam ciro (â‚º), son iÅŸ tarihi â†’ profile link.

**(b) Firma Profil SayfasÄ±** (`firma-analiz.html?firma=...` â€” derinleÅŸtir):
- [ ] ğŸ”´ **Kimlik**: ad, (varsa) vergi no, ÅŸehir, ana sektÃ¶rler (CPV).
- [ ] ğŸ”´ **KPI ÅŸeridi**: toplam sÃ¶zleÅŸme sayÄ±sÄ± Â· toplam ciro Â· devam eden Â· tamamlanan Â· **ort. tenzilat %** Â·
  ort. sÃ¶zleÅŸme bedeli Â· ilk/son sÃ¶zleÅŸme tarihi Â· 5-yÄ±llÄ±k iÅŸ bitirme toplamÄ±.
- [ ] ğŸ”´ **KazandÄ±ÄŸÄ± ihaleler listesi** (drill-down, sayfalÄ±): ihale adÄ± Â· idare Â· bedel Â· tenzilat Â· tarih.
- [ ] ğŸ”´ **SektÃ¶r (CPV) kÄ±rÄ±lÄ±mÄ±**: hangi sektÃ¶rlerde ne kadar iÅŸ aldÄ±.
- [ ] ğŸ”´ **Ä°dare kÄ±rÄ±lÄ±mÄ± / iliÅŸki haritasÄ±**: hangi idarelerden iÅŸ alÄ±yor (tekrar eden idare = gÃ¼Ã§lÃ¼ iliÅŸki sinyali).
- [ ] ğŸ”´ **Rakip firmalar**: aynÄ± ihalelerde yarÄ±ÅŸtÄ±ÄŸÄ±/birlikte teklif verdiÄŸi firmalar (co-bidder aÄŸÄ±).
- [ ] ğŸ”´ **Åehir / ihale tÃ¼rÃ¼ / usul kÄ±rÄ±lÄ±mÄ±** (Chart.js + tablo).
- [ ] ğŸ”´ **YÄ±llÄ±k trend** grafiÄŸi (sÃ¶zleÅŸme sayÄ±sÄ± + ciro / yÄ±l).
- [ ] ğŸŸ¡ **OrtaklÄ±k / konsorsiyum geÃ§miÅŸi** (JV ortaklarÄ±) â€” sonuÃ§ verisinde ortak giriÅŸim bilgisi varsa.
- [ ] ğŸŸ¢ **AI firma yorumu (artÄ±mÄ±z)**: Gemini ile Ã¶zet â€” "bu firma X idaresinde baskÄ±n, Y sektÃ¶rÃ¼nde agresif
  tenzilat veriyor, son 1 yÄ±lda Z'ye yÃ¶neldi" â†’ ihaleciler'de OLMAYAN katma deÄŸer.

**(c) Rakip Takibi** (Ã¼retkenlik â€” 9.10 ile baÄŸlÄ±):
- [ ] ğŸ”´ KullanÄ±cÄ± bir/birkaÃ§ **rakip firmayÄ± takibe alÄ±r** â†’ o firma yeni iÅŸ aldÄ±ÄŸÄ±nda/teklif verdiÄŸinde bildirim.
- [ ] ğŸ”´ "Rakiplerim" panosu: takip edilen firmalarÄ±n son hareketleri (kazandÄ±ÄŸÄ±/girdiÄŸi ihaleler).

**SatÄ±ÅŸ deÄŸeri:** "Rakibini araÅŸtÄ±r, hangi idareyle Ã§alÄ±ÅŸÄ±yor, ne kadar tenzilat veriyor, nereye yÃ¶neliyor â€” gÃ¶r."
Bu, fiyat/rekabet istihbaratÄ±nÄ±n (landing'de PREMIUM vaat edilen) somut karÅŸÄ±lÄ±ÄŸÄ±. **9.1 olmadan baÅŸlayamaz.**


---

## 9.3 âš–ï¸ P1 â€” KÄ°K KARARLARI VERÄ°TABANI â€” ğŸ”´ YOK

> ihaleciler'de: **32.255 uyuÅŸmazlÄ±k kararÄ± + 2.454 mahkeme kararÄ±**, kategori/ÅŸehir/tÃ¼r/usul/ÅŸikayetÃ§i/tarih ile aranÄ±r.
> Teklif verenin "itiraz edersem kazanÄ±r mÄ±yÄ±m / bu idare Ã§ok mu ÅŸikayet alÄ±yor" sorusuna cevap = yÃ¼ksek katma deÄŸer.

- [ ] ğŸ”´ **KÄ°K kararlarÄ± scrape** (kik.gov.tr / EKAP karar arÅŸivi): karar no, tarih, idare, ÅŸikayetÃ§i, konu, sonuÃ§, tam metin.
- [ ] ğŸ”´ `kik_kararlari` tablosu + arama sayfasÄ± (`kik-kararlari.html`): full-text + filtreler.
- [ ] ğŸŸ¢ **ArtÄ±mÄ±z**: kararlarÄ± Gemini ile Ã¶zetle ("emsal karar: benzer ÅŸikayet reddedilmiÅŸ") + ihale-detayda
  "bu idarenin/konunun emsal kararlarÄ±" bloÄŸu.

---

## 9.4 ğŸ§  P2 â€” AI ÅÄ°RKET PROFÄ°LÄ° "BRAIN" + RAG BÄ°LGÄ° TABANI â€” ğŸŸ¡ profil.html var + doluluk skoru YAPILDI (30 Haz 2026)

**YapÄ±ldÄ± (30 Haz 2026):**
- âœ… **Profil Doluluk Skoru banner'Ä±** (`profil.html`): sektÃ¶r(30p) + il(20p) + tÃ¼r(20p) + bÃ¼tÃ§e(15p) + eÅŸik(15p) = max 100p.
  Renk: yeÅŸil(%80+), amber(%50+), kÄ±rmÄ±zÄ±(<%50). SeÃ§imler deÄŸiÅŸtikÃ§e anlÄ±k gÃ¼ncellenir.
  Dokunulan dosyalar: `profil.html`

**YapÄ±ldÄ± (30 Haz 2026 â€” devam):**
- âœ… **Firma AdÄ± input** eklendi (`profil.html`): Firma Bilgileri bÃ¶lÃ¼mÃ¼; `firma_adi` DB kolonuna kaydeder, sidebar'da gÃ¶sterilir.
- âœ… **Anahtar Kelimeler alanÄ±** eklendi (`profil.html`): virgÃ¼lle ayrÄ±lmÄ±ÅŸ Ã¶zel kelimeler (Ã¶r: "boya, kaplama").
  `localStorage('ihale_anahtar_kelimeler')` ile anlÄ±k kaydedilir; DB'ye ayrÄ±ca best-effort upsert.
  Textarea oninput â†’ kelimelerKaydet(); baÅŸlangÄ±Ã§ta localStorage'dan Ã¶nceden yÃ¼klenir.
- âœ… **Anahtar kelime bonusu** (`ihaleler.html`): uyumHesapla() sonuna +10p eklendi; ihale baÅŸlÄ±ÄŸÄ±nda
  localStorage keywords bulunursa puan artar (Math.min ile 100'de kÄ±sÄ±tlÄ±).
  Dokunulan dosyalar: `profil.html`, `ihaleler.html`

> profil.html var, RAG yok

> tendermeister'Ä±n kalbi: ÅŸirket profili sadece form deÄŸil, **bilgi tabanÄ±**. Belgeler/referanslar/sertifikalar
> yÃ¼klenir â†’ **indekslenir** â†’ hem eÅŸleÅŸtirmede hem teklif yazÄ±mÄ±nda kullanÄ±lÄ±r. "Yapay Zeka Bilgi DÃ¼zeyi %"
> profil doluluÄŸunu gÃ¶sterir.

- [ ] ğŸ”´ **Firma bilgi tabanÄ±**: kullanÄ±cÄ± kendi belgelerini (iÅŸ bitirme, ISO, kapasite raporu, referans mektuplarÄ±)
  yÃ¼kler â†’ Gemini ile Ã¶zetlenir/embed'lenir â†’ Supabase `pgvector`'da saklanÄ±r (RAG).
- [ ] ğŸ”´ **Profil doluluk skoru** ("AI Bilgi DÃ¼zeyi %") â€” profili tamamlamaya teÅŸvik (onboarding gamification).
- [ ] ğŸ”´ **Profil alanlarÄ± (tendermeister'dan eksiklerimiz)**: temel yetkinlikler, anahtar kelimeler,
  **sertifikalar/yeterlilikler** (uygunluk kontrolÃ¼ iÃ§in), **faaliyet yarÄ±Ã§apÄ± (km)**, **min sÃ¶zleÅŸme deÄŸeri**,
  Ã§ok Ã¼lke kapsamÄ± (yurtdÄ±ÅŸÄ± iÃ§in), iletiÅŸim kiÅŸisi.
- [ ] ğŸ”´ **Otomatik CPV/OKAS kodu Ã¶nerisi**: sektÃ¶r+yetkinlikten AI ile CPV/OKAS belirlet (tendermeister CPV/NUTS yapÄ±yor).
- ğŸŸ¢ Mevcut `profil.html` + `kullanici_profiller` bunun iskeleti; Ã¼zerine RAG ve doluluk skoru eklenecek.

---

## 9.5 ğŸ¤– P2 â€” Ä°HALE-BAÅINA AI TEKLÄ°F WORKFLOW'U â€” ğŸŸ¡ teklif-olustur.html var, entegre deÄŸil

> tendermeister'da her ihalenin "Detaylar"Ä± bir **workflow** sayfasÄ±: 6 sekme. Bizim `teklif-olustur.html` +
> `uyumluluk.html` + `ihale-detay.html` parÃ§alÄ±; bunlarÄ± tek bir akÄ±ÅŸta birleÅŸtir.

- [ ] ğŸ”´ **Belge yÃ¼kle â†’ AI sÄ±nÄ±flandÄ±r**: kullanÄ±cÄ± ÅŸartname/eklerini (PDF/DOCX/XLSX/ZIP) yÃ¼kler â†’ AI tÃ¼r ayÄ±rÄ±r
  (idari ÅŸartname, teknik ÅŸartname, birim fiyat cetveli, sÃ¶zleÅŸme tasarÄ±sÄ±). (tendermeister: ZIP extraction + GAEB tanÄ±ma;
  bizde TR karÅŸÄ±lÄ±ÄŸÄ± = **birim fiyat cetveli / standart formlar** ayrÄ±ÅŸtÄ±rma.)
- [ ] ğŸ”´ **KO (eleme) kriter tarayÄ±cÄ±** = bizim **uyumluluk** modÃ¼lÃ¼mÃ¼zÃ¼n gÃ¼Ã§lendirilmiÅŸ hali: ÅŸartnameden zorunlu
  yeterlilik ÅŸartlarÄ±nÄ± (iÅŸ deneyim oranÄ±, teminat, kapasite, belgeler) Ã§Ä±kar â†’ firmanÄ±n bilgi tabanÄ±yla (9.4)
  **"giriÅŸ engeli var/yok"** kontrolÃ¼. *uyumluluk.html'i buraya entegre et.*
- [ ] ğŸ”´ **AI form doldurma**: standart formlarÄ± (birim fiyat teklif mektubu, iÅŸ deneyim beyanÄ±) firma profilinden doldur.
- [ ] ğŸ”´ **AI konsept/teklif metni yazÄ±cÄ±**: teknik teklif/metodoloji taslaÄŸÄ± Ã¼ret (teklif-olustur.html'in backend baÄŸÄ±).
- [ ] ğŸ”´ **Alt yÃ¼klenici / konsorsiyum modÃ¼lÃ¼**: bu ihale iÃ§in alt yÃ¼klenici/ortak Ã¶ner (PLATFORM_CONTEXT'te konsorsiyum planlÄ±).
- [ ] ğŸŸ¡ **BÃ¶lÃ¼nmÃ¼ÅŸ ekran inceleme**: solda ÅŸartname, saÄŸda teklif (nice-to-have).
- ğŸŸ¢ Mevcut **AI Analizi sekmesi (7 bÃ¶lÃ¼m)** zaten bu workflow'un "analiz" adÄ±mÄ± â€” Ã¼zerine "aksiyon" adÄ±mlarÄ±nÄ± ekle.

---

## 9.6 ğŸ“¡ P3 â€” Ã‡OK KAYNAKLI RADAR + ANLIK TARAMA â€” ğŸŸ¡ EKAP gece cron var

> tendermeister 18 portalÄ±, ihaleciler 3 kaynaÄŸÄ± (EKAP+Gazete+Ä°stihbarat) topluyor. Biz tek kaynak + gece taramasÄ±.

- [ ] ğŸ”´ **Gazete/Ã¶zel sektÃ¶r ilanlarÄ± kaynaÄŸÄ±** (ihaleciler'in "Gazete" + "Ä°stihbarat"Ä±): Ã¶zel sektÃ¶r alÄ±m ilanlarÄ±,
  resmi gazete ihale ilanlarÄ±. (PLATFORM_CONTEXT'te "Ã–zel sektÃ¶r alÄ±m ilanlarÄ±" zaten Faz 2'de planlÄ± â€” baÅŸlat.)
- [ ] ğŸ”´ **"Åimdi tara" / anlÄ±k yenile** butonu (kullanÄ±cÄ± tetikli incremental tarama) â€” gece cron'a ek.
- [ ] ğŸŸ¡ **YurtdÄ±ÅŸÄ±/AB ihale altyapÄ±sÄ±** (tendermeister EU TED yapÄ±yor; PLATFORM_CONTEXT'te "YurtdÄ±ÅŸÄ± ihale altyapÄ±sÄ±" planlÄ±).
  â†’ Ã§ok dilli arayÃ¼z gerektirir (9.8).
- ğŸŸ¢ Bizim gece cron + link-only mimarimiz saÄŸlam temel; Ã¼zerine kaynak Ã§eÅŸitliliÄŸi eklenecek.

---

## 9.7 ğŸ”” P2 â€” AKILLI EÅLEÅME SKORU + BÄ°LDÄ°RÄ°M EÅÄ°ÄÄ° â€” ğŸŸ¡ UI TAMAM, AI BEKLEMEDE (30 Haz 2026)

**YapÄ±ldÄ± (29-30 Haz 2026):**
- âœ… **Minimum uyum eÅŸiÄŸi kullanÄ±cÄ± ayarÄ±**: `profil.html`'e "AkÄ±llÄ± EÅŸleÅŸme EÅŸiÄŸi" bÃ¶lÃ¼mÃ¼ eklendi
  - Range input (0â€“90, 5'er adÄ±m): TÃ¼mÃ¼(0) / %40+(40) / %60+(60) / %75+(75) / %85+(85) preset butonlarÄ±
  - SeÃ§ilen deÄŸer hem `profil.min_uyum_esigi` Supabase kolonuna hem de `localStorage('ihale_min_uyum_esigi')` kaydedilir
  - `ihaleler.html` aÃ§Ä±lÄ±ÅŸÄ±nda localStorage'dan okuyup filtre uygular (Supabase beklemeden anlÄ±k)
  - Dokunulan dosyalar: `profil.html`, `ihaleler.html`
- âœ… **"En Ä°yi EÅŸleÅŸmeler" widget** (`dashboard.html`): profil yÃ¼klendikten sonra 150 aktif ihale Ã§ekip
  `uyumHesapla()` ile skorlar, eÅŸiÄŸi geÃ§enlerin en iyi 6'sÄ±nÄ± 3Ã—2 grid olarak gÃ¶sterir.
  - Skor renkleri: yeÅŸil (%80+), amber (%60+), gri (dÃ¼ÅŸÃ¼k)
  - Kalan gÃ¼n gÃ¶stergesi (kÄ±rmÄ±zÄ± â‰¤3 gÃ¼n), tÄ±klanÄ±nca ihale-detay aÃ§Ä±lÄ±r
  - Profil yoksa "profilinizi doldurun" CTA; eÅŸikten dÃ¼ÅŸÃ¼kse "eÅŸiÄŸi dÃ¼ÅŸÃ¼r" yÃ¶nlendirmesi
  - Dokunulan dosyalar: `dashboard.html`

- [ ] ğŸ”´ **Semantik AI eÅŸleÅŸme**: ÅŸu anki uyum % formÃ¼lÃ¼ basit (kategori+il+tÃ¼r+bÃ¼tÃ§e). tendermeister profil
  anahtar kelimeleri + CPV/NUTS + bilgi tabanÄ±yla **semantik** skor veriyor. Gemini embedding ile firma profili â†”
  ihale ÅŸartnamesi benzerliÄŸi hesapla.

---

## 9.8 ğŸŒ P3 â€” Ã‡OK DÄ°LLÄ° ARAYÃœZ â€” ğŸ”´ sadece TR

- [ ] ğŸ”´ i18n altyapÄ±sÄ± (TR/EN, sonra AR). tendermeister 5 dil (AR dahil) sunuyor â€” yurtdÄ±ÅŸÄ±/uluslararasÄ± firma hedefi iÃ§in.
  YurtdÄ±ÅŸÄ± ihale (9.6) aÃ§Ä±lÄ±rsa zorunlu.

---

## 9.9 ğŸ—‚ï¸ P2 â€” VERÄ° ZENGÄ°NLÄ°ÄÄ° & GEZÄ°NME (ihaleciler dizinleri) â€” ğŸŸ¡ DEVAM EDÄ°YOR (30 Haz 2026)

> ihaleciler Ã¼st menÃ¼sÃ¼: **Kategoriler Â· Åehirler Â· SektÃ¶rler Â· Ä°dareler Â· YÃ¼kleniciler Â· KÄ°K KararlarÄ±** â€”
> her biri sayÄ±lÄ± bir dizin sayfasÄ±. Bizde Kategoriler/Åehirler (harita) var; diÄŸerleri eksik.
>
> âœ… Not: **idareye gÃ¶re ve sektÃ¶re gÃ¶re ARAMA iÃ§in gereken veri DB'de zaten var** (`idare`, `okas`, `kategori`).
> Yani bu maddeler "veri toplama" deÄŸil, **arama/dizin yÃ¼zeyi (UI + GROUP BY sorgusu)** iÅŸidir â†’ gÃ¶rece hÄ±zlÄ±.

- [x] ğŸŸ¢ **Ä°dareye gÃ¶re arama/dizin**: `idareler.html` oluÅŸturuldu (29 Haz 2026).
  - TÃ¼m idareler paginated batch ile Ã§ekilir, client-side GROUP BY + sort
  - Ã–zet kartlar: Toplam Ä°dare / Aktif Ä°dareler / Toplam Ä°hale / Aktif Ä°hale
  - Arama (anlÄ±k filter), Ä°l filtresi, 5 sÄ±ralama seÃ§eneÄŸi (en Ã§ok ihale/aktif/isim/il)
  - Her satÄ±rda: idare adÄ±, baÅŸlÄ±ca il, toplam sayÄ±, aktif sayÄ±, Analiz + Ä°haleler butonlarÄ±
  - 50/sayfa sayfalama; sidebar nav'a tÃ¼m sayfalarda eklendi
  - Dokunulan dosyalar: `idareler.html` (yeni), sidebar gÃ¼ncellemesi (tÃ¼m sayfalar)
- [x] ğŸŸ¢ **SektÃ¶rler dizini** (`sektorler.html`) oluÅŸturuldu (30 Haz 2026).
  - `kategori_sayim()` RPC denemesi (varsa hÄ±zlÄ± yol) â†’ yoksa paginated batch fallback
  - Ã–zet kartlar: Toplam SektÃ¶r / Aktif SektÃ¶rler / Toplam Ä°hale / Aktif Ä°hale
  - Arama, sÄ±ralama (en Ã§ok ihale/aktif/alfabetik/aktiflik oranÄ±), min ihale filtresi
  - Her sektÃ¶r kartÄ±: ikon (45 sektÃ¶re emoji map) + toplam/aktif/kapandÄ± sayÄ±larÄ± + oran barÄ± + "Aktif Ä°haleler / TÃ¼mÃ¼" butonlarÄ±
  - Sidebar nav'a tÃ¼m sayfalarda eklendi
  - Dokunulan dosyalar: `sektorler.html` (yeni)
- âœ… **SektÃ¶rler & Ä°dareler dizini geliÅŸtirmeleri** (`sektorler.html`, `idareler.html`) (30 Haz 2026):
  - `sektorler.html`: "Sadece Aktif" filtresi (min-filter select'e seÃ§enek), ilk 3 sektÃ¶re ğŸ¥‡ğŸ¥ˆğŸ¥‰ rozeti, her karta "ğŸ“Š Analiz" butonu (â†’ `rekabet-analizi?kategori=X`), ğŸ”— PaylaÅŸ butonu (clipboard)
  - `idareler.html`: "Sadece Aktif" filtresi (ayrÄ± select + event), ğŸ”— PaylaÅŸ butonu, Ctrl+K arama odaÄŸÄ± kÄ±sayolu
  - `rekabet-analizi.html`: URL param desteÄŸi â€” `?kategori=X&il=Y&durum=Z` â†’ sayfa aÃ§Ä±lÄ±ÅŸÄ±nda filtreleri Ã¶nceden doldurur (baslat() iÃ§inde URLSearchParams okuma). SektÃ¶r/Ä°dare kartlarÄ±ndaki Analiz linkleri artÄ±k filtreyi otomatik set eder.
  - Dokunulan dosyalar: `sektorler.html`, `idareler.html`, `rekabet-analizi.html`
- âœ… **Sidebar tutarlÄ±lÄ±ÄŸÄ± tamamlandÄ± (30 Haz 2026)**: Kurum Analizi + Firma Analizi + SektÃ¶rler nav linkleri tÃ¼m sayfalara eklendi.
  - `bildirimler.html` + `fiyatlandirma_odeme_bolumu.html`: eksik kurum-analiz/firma-analiz linkleri eklendi
  - `dashboard.html`: kurum-analiz ikonu ğŸ›ï¸ â†’ ğŸ” dÃ¼zeltildi
  - TÃ¼m sayfalarda sidebar tutarlÄ±
- âœ… **Sidebar son dÃ¼zeltmeler (30 Haz 2026)**: `uyumluluk.html` + `dokumanlar.html` + `teklif-olustur.html` eski sidebar
  (href="#" Rekabet Analizi, eksik idareler/sektorler/kurum/firma-analiz linkleri) gÃ¼ncel yapÄ±ya Ã§evrildi.
- âœ… **Ä°hale Detay â€” NotlarÄ±m sekmesi** (`ihale-detay.html`): kiÅŸisel not alma alanÄ± (localStorage `ihale_not_{id}`),
  auto-save oninput, karakter sayacÄ±, temizle butonu, tab badge (not varsa Â· gÃ¶stergesi). Rakiplerde yok â€” Ã¶zgÃ¼n Ã¶zellik.
  Benzer Ä°haleler: kategori+il â†’ kategori â†’ tÃ¼r waterfall; il gÃ¶stergesi eklendi.
  Dokunulan dosyalar: `ihale-detay.html`, `uyumluluk.html`, `dokumanlar.html`, `teklif-olustur.html`
- [ ] ğŸ”´ **YÃ¼kleniciler dizini**: geÃ§miÅŸte ihale alan firmalarÄ±n listesi (9.1 sonuÃ§ verisi gelince) + analiz linki.
- [ ] ğŸ”´ **Resmi KÄ°K iÅŸ-deneyim grup taksonomisi** ((A) KÃ¶prÃ¼/TÃ¼nel/Karayoluâ€¦ (B) Binaâ€¦ (C) Tesisatâ€¦ (D) Enerjiâ€¦ (E) HaberleÅŸme):
  yeterlilik/iÅŸ deneyim eÅŸleÅŸtirmesi iÃ§in kategori aÄŸacÄ±na ekle (ihaleciler'de var).
- ğŸŸ¢ Bizim **TÃ¼rkiye haritasÄ±** ihaleciler'de yok â€” bu bizim gÃ¶rsel artÄ±mÄ±z, koru/Ã¶ne Ã§Ä±kar.

---

## 9.10 ğŸ‘¤ P2 â€” HESAP / ÃœRETKENLÄ°K Ã–ZELLÄ°KLERÄ° â€” ğŸŸ¡ BÃœYÃœK KISMI TAMAM (30 Haz 2026)

> ihaleciler hesap menÃ¼sÃ¼: **BÃ¼ltenlerim Â· OkuduklarÄ±m Â· Takip listem Â· SÃ¶zleÅŸme listem Â· Bildirimler**.

**YapÄ±ldÄ± (29-30 Haz 2026):**
- âœ… **KayÄ±tlÄ± Aramalar (BÃ¼ltenlerim altyapÄ±sÄ±)**: `ihaleler.html`'e "â­ AramayÄ± Kaydet" + "ğŸ“‚ KayÄ±tlÄ±" butonlarÄ±
  eklendi. `KayitliArama` modÃ¼lÃ¼ localStorage (`ihale_kayitli_aramalar_v1`) ile saklar.
  - Filtre panelinin Ã¶zeti okunabilir metne dÃ¶nÃ¼ÅŸtÃ¼rÃ¼lÃ¼r (`filtrelerOzet`)
  - Modal ile isim verilerek kaydedilir; URL parametresiyle tek tÄ±kla uygulanÄ±r
  - Dokunulan dosyalar: `ihaleler.html`
- âœ… **BÃ¼ltenlerim sekmesi** (`bildirimler.html`): KayÄ±tlÄ± aramalarÄ± listeler, "â–¶ Ã‡alÄ±ÅŸtÄ±r" ile filtreli ihale listesi aÃ§Ä±lÄ±r,
  "âœ• Sil" ile localStorage'dan kaldÄ±rÄ±lÄ±r. Sekme badge'i ile kayÄ±t sayÄ±sÄ± gÃ¶sterilir.
  - Dokunulan dosyalar: `bildirimler.html`
- âœ… **Dashboard â€” KayÄ±tlÄ± Aramalar widget**: Dashboard'da son 5 kayÄ±tlÄ± arama tÄ±klanabilir linkler olarak gÃ¶sterilir.
  - Dokunulan dosyalar: `dashboard.html`
- âœ… **Dashboard â€” YaklaÅŸan Son Tarihler widget**: Takip listesindeki aktif ihalelerin kalan gÃ¼nlerine gÃ¶re renkli
  geri sayÄ±m kutularÄ± (kÄ±rmÄ±zÄ± â‰¤3g, amber â‰¤7g, yeÅŸil >7g).
  - Dokunulan dosyalar: `dashboard.html`
- âœ… **OkuduklarÄ±m sekmesi** (`bildirimler.html`): `ihale_okundu_v1` localStorage'dan ID'leri okur, Supabase'den
  baslik/idare/il/tur/son_teklif_tarihi Ã§eker, ihale-detay linki olarak listeler. Sekme badge'i ile sayÄ± gÃ¶sterilir.
  - Dokunulan dosyalar: `bildirimler.html`
- âœ… **SÃ¶zleÅŸme Listesi sekmesi** (`bildirimler.html`) (30 Haz 2026): Takip.liste() ID'lerinden aktif ihaleleri Ã§eker,
  kalan gÃ¼n geri sayÄ±mÄ±yla renkli kartlar gÃ¶sterir (kÄ±rmÄ±zÄ± â‰¤3g, turuncu â‰¤7g, yeÅŸil >7g). SÃ¼resi dolmuÅŸlar da listelenir.
  Sekme badge'i Takip sayÄ±sÄ±ndan beslenir. `sekmeGoster()` refactor edildi: tÃ¼m panel toggle mantÄ±ÄŸÄ± array iteration'a Ã§evrildi.
  - Dokunulan dosyalar: `bildirimler.html`
- âœ… **Rekabet Analizi â€” AylÄ±k Ä°hale Trendi** (30 Haz 2026): `rekabet-analizi.html`'e 24 aylÄ±k line chart eklendi.
  Amber dolgu, tension 0.3. `ilan_tarihi` â†’ `son_teklif_tarihi` fallback. Mevcut chart'lardan Ã¶nce gÃ¶sterilir.
  - Dokunulan dosyalar: `rekabet-analizi.html`
- âœ… **Rekabet Analizi â€” Usul DaÄŸÄ±lÄ±mÄ± + PaylaÅŸ** (`rekabet-analizi.html`) (30 Haz 2026):
  - `usul` alanÄ± data sorgusuna eklendi; `usulBarsRender()` ile yatay bar chart (mavi, top 8 usul) eklendi.
  - ğŸ”— PaylaÅŸ butonu: mevcut filtre state'ini URL parametrelerine (kategori/il/durum) kodlar + clipboard'a kopyalar. URL param desteÄŸiyle (baslat() iÃ§inde URLSearchParams okuma) filtreli gÃ¶rÃ¼nÃ¼m paylaÅŸÄ±labilir.
  - Dokunulan dosyalar: `rekabet-analizi.html`

**Kalan:**
- [ ] ğŸ”´ **BÃ¼ltenlerim e-posta**: kayÄ±tlÄ± arama â†’ Supabase Edge Function ile gÃ¼nlÃ¼k/haftalÄ±k otomatik e-posta Ã¶zeti.
  (Åu an sadece UI; backend tetikleyici yok.)
- âœ… **Takip listem â€” Bittileri KaldÄ±r butonu** (`takipte.html`) (30 Haz 2026): "â†© Bittileri KaldÄ±r" butonu eklendi. Teklif tarihi geÃ§miÅŸ ihaleleri toplu olarak takip listesinden kaldÄ±rÄ±r; DOM gÃ¼ncellemesi + istatistik gÃ¼ncelleme. Dokunulan dosyalar: `takipte.html`
- âœ… **Takip listem â€” CSV Export** (`takipte.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()` fonksiyonu. BOM eklenerek UTF-8 Excel uyumlu CSV (id/ekap_id/baslik/idare/il/tur/durum/son_teklif_tarihi/yaklasik_maliyet_min). Dokunulan dosyalar: `takipte.html`
- âœ… **Uyumluluk â€” Takibe Al butonu** (`uyumluluk.html`) (30 Haz 2026): Her tablo satÄ±rÄ±na â˜†/â˜… Takip toggle butonu eklendi; kategori sÃ¼tun meta'ya eklendi; select sorgusuna `kategori` alanÄ± eklendi. Dokunulan dosyalar: `uyumluluk.html`
- âœ… **Uyumluluk â€” CSV Export** (`uyumluluk.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()` fonksiyonu. `tumScoredIlanlar` global ile tÃ¼m eÅŸleÅŸmeler (aktif sayfa deÄŸil) export edilir; uyum % dahil. Dokunulan dosyalar: `uyumluluk.html`
- âœ… **Kurum Analizi â€” CSV Export** (`kurum-analiz.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()`. `tumIhaleler` global; dosya adÄ±nda kurum adÄ± + tarih. Dokunulan dosyalar: `kurum-analiz.html`
- âœ… **Firma Analizi â€” CSV Export** (`firma-analiz.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()`. `tumIhaleler` global; dosya adÄ±nda firma adÄ± + tarih. Dokunulan dosyalar: `firma-analiz.html`
- âœ… **Ä°dareler Dizini â€” CSV Export** (`idareler.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()`. `filtrelenmis` array (uygulanan filtreler dahil) export edilir. Dokunulan dosyalar: `idareler.html`
- âœ… **SektÃ¶rler Dizini â€” CSV Export** (`sektorler.html`) (30 Haz 2026): "â†“ CSV" butonu + `csvIndir()`. `filtrelenmis` array (aktiflik oranÄ± dahil) export edilir. Dokunulan dosyalar: `sektorler.html`
- âœ… **Rekabet Analizi â€” SÄ±fÄ±rla butonu** (`rekabet-analizi.html`) (30 Haz 2026): Topbar'a â†º SÄ±fÄ±rla butonu + `filtreleriSifirla()` fonksiyonu eklendi. Dokunulan dosyalar: `rekabet-analizi.html`
- âœ… **Profil â€” Belgeler & Yetkilendirmeler** (`profil.html`) (30 Haz 2026): Yeni section-card: textarea + localStorage(`ihale_sertifikalar`); `sertifikalarKaydet()` + init yÃ¼kleme + kaydet() persist. Dokunulan dosyalar: `profil.html`
- âœ… **Profil â€” Ä°letiÅŸim & Vergi bilgileri** (`profil.html`) (30 Haz 2026): Firma Bilgileri kartÄ±na Ä°letiÅŸim KiÅŸisi + Telefon + Vergi No alanlarÄ± eklendi. localStorage(`ihale_iletisim_kisi`, `ihale_iletisim_tel`, `ihale_vergi_no`) ile saklanÄ±r. AI teklif workflow iÃ§in zemin. Ctrl+S ile kaydet kÄ±sayolu eklendi. Dokunulan dosyalar: `profil.html`
- âœ… **Dashboard â€” YaklaÅŸan BitiÅŸ widget budget** (`dashboard.html`) (30 Haz 2026): YaklaÅŸan Son Tarihler widget'Ä±na yaklaÅŸÄ±k maliyet + idare adÄ± eklendi. Select sorgusuna `idare,il,yaklasik_maliyet_min,tahmini_bedel` eklendi. `paraCevir()` helper ile amber renkte maliyet gÃ¶sterimi. Dokunulan dosyalar: `dashboard.html`
- âœ… **Ä°haleler â€” Alt+1/2/3/4 sekme kÄ±sayollarÄ±** (`ihaleler.html`) (30 Haz 2026): Ctrl+K yanÄ±na Alt+1 (GÃ¼ncel), Alt+2 (GeÃ§miÅŸ), Alt+3 (SonuÃ§), Alt+4 (DetaylÄ± Ara) kÄ±sayollarÄ± eklendi. Dokunulan dosyalar: `ihaleler.html`
- âœ… **Uyumluluk â€” BaÅŸlÄ±k/idare arama** (`uyumluluk.html`) (30 Haz 2026): Tablo araÃ§ Ã§ubuÄŸuna metin arama inputu eklendi. `aramaFiltrele()` 250ms debounce ile `yukle(1)` tetikler; `yukle()` iÃ§inde client-side `f-arama` filtresi uygulanÄ±r (baslik/idare). Dokunulan dosyalar: `uyumluluk.html`
- âœ… **Ä°haleler â€” HÄ±zlÄ± Tarih Filtreleri** (30 Haz 2026): â†’ bkz. Ã–ncelik 3 gÃ¼ncelleme. Dokunulan dosyalar: `ihaleler.html`
- âœ… **Takip listem** (`takipte.html`) (30 Haz 2026): renkli kalan gÃ¼n etiketleri (kÄ±rmÄ±zÄ± â‰¤3g, turuncu â‰¤7g, yeÅŸil),
  uyum renklendirmesi, topbar sÄ±ralama select (Son Eklenen / En YakÄ±n Tarih / En YÃ¼ksek Uyum), il gÃ¶sterimi kart alt satÄ±rÄ±na eklendi.
  `uyum.js` paylaÅŸÄ±lan modÃ¼lÃ¼ne anahtar kelime bonusu (+10p) eklendi â€” takipte + dashboard da gÃ¼ncellendi.
  `firma-analiz.html`: Son Aramalar localStorage (`ihale_son_aramalar_firma_v1`) + tÄ±klanabilir chips, `kategori`+`ilan_tarihi` select'e eklendi (grafik/sektÃ¶r dÃ¼zeltmesi).
  `ihale-detay.html`: `benzerIhaleler()` kategori+il â†’ kategori â†’ tÃ¼r fallback zinciriyle gÃ¼Ã§lendirildi; il gÃ¶sterildi.
    Son gÃ¶rÃ¼ntÃ¼lenenler tracking: `ihale_son_gorulenler_v1` localStorage'a id/baslik/idare/il/tarih kaydedilir.
  `dashboard.html`: "Son GÃ¶rÃ¼ntÃ¼lenenler" widget eklendi (localStorage'dan okur, ihale-detay linkleri).
  `bildirimler.html`: TarayÄ±cÄ± push notification banner (izin default ise gÃ¶sterilir, Notification.requestPermission, dismiss â†’ localStorage).
  Dokunulan dosyalar: `takipte.html`, `js/uyum.js`, `firma-analiz.html`, `ihale-detay.html`, `dashboard.html`, `bildirimler.html`
- âœ… **DÃ¶kÃ¼manlar â€” UX iyileÅŸtirmeleri** (`dokumanlar.html`) (1 Tem 2026):
  - Topbar'a "TÃ¼mÃ¼nÃ¼ AÃ§ / TÃ¼mÃ¼nÃ¼ Kapat" toggle butonu eklendi; `tumAcik` state'i tutar.
  - â‰¤3 sonuÃ§ varsa tÃ¼m kartlar sayfa yÃ¼klenince otomatik aÃ§Ä±lÄ±r.
  - Ctrl+K â†’ arama kutusuna odaklan kÄ±sayolu eklendi.
  - Alt+1/2/3 â†’ Takip DÃ¶kÃ¼manlarÄ± / Teknik / Ä°dari sekme kÄ±sayollarÄ± eklendi.
  - Kart `<div>`'ine `data-id` eklendi (toggle-all'Ä±n karta ulaÅŸabilmesi iÃ§in).
  Dokunulan dosyalar: `dokumanlar.html`
- âœ… **Bildirimler â€” UX & veri dÃ¼zeltmesi** (`bildirimler.html`) (1 Tem 2026):
  - `sozlesmeListesiYukle()`: select sorgusuna `yaklasik_maliyet_min` eklendi; maliyet gÃ¶sterimi `yaklasik_maliyet_min || tahmini_bedel` Ã¶nceliÄŸiyle gÃ¼ncellendi (diÄŸer tÃ¼m sayfalarla tutarlÄ±).
  - Alt+1â€“7 â†’ sekme kÄ±sayollarÄ±: TÃ¼mÃ¼ / OkunmamÄ±ÅŸ / Ä°hale / Sistem / BÃ¼ltenlerim / OkuduklarÄ±m / SÃ¶zleÅŸme Listesi.
  Dokunulan dosyalar: `bildirimler.html`
- âœ… **Uyumluluk â€” mojibake bug fix + arama performansÄ±** (`uyumluluk.html`) (1 Tem 2026):
  - **Bulunan gerÃ§ek bug**: Pro kilit ekranÄ± metni bozuk kodlanmÄ±ÅŸtÄ± (`Uyumluluk Analizi ï¿½ Pro ï¿½zelliÄŸi` / `gï¿½re` / `ï¿½zeldir`) â€” dÃ¼zgÃ¼n TÃ¼rkÃ§e karakterlerle dÃ¼zeltildi.
  - **Arama performans iyileÅŸtirmesi**: Ã¶nceki oturumda not edilen optimizasyon uygulandÄ± â€” `yukle()` artÄ±k sadece Supabase fetch+skor+min-uyum filtresini yapÄ±yor; yeni `renderSayfa()` fonksiyonu metin aramasÄ± + sayfalamayÄ± `tumScoredIlanlar` Ã¼zerinde bellekte (anlÄ±k, Supabase'e gitmeden) uyguluyor. `aramaFiltrele()` artÄ±k debounce'lu `yukle(1)` yerine doÄŸrudan `renderSayfa(1)` Ã§aÄŸÄ±rÄ±yor (250ms network gecikmesi kalktÄ±). Sayfalama butonlarÄ± da `renderSayfa()`'a yÃ¶nlendirildi (sayfa deÄŸiÅŸince gereksiz refetch yok).
  Dokunulan dosyalar: `uyumluluk.html`
- [ ] ğŸŸ¡ **Ã‡ok kanallÄ± bildirim**: landing'de SMS/WhatsApp/Telegram vaat ediliyor ama backend yok â†’ en azÄ±ndan
  **e-posta + tarayÄ±cÄ± push** (tendermeister push yapÄ±yor) gerÃ§ekle; SMS/WhatsApp'Ä± sonra.

---

## 9.11 ğŸ’° FiyatlandÄ±rma / konumlandÄ±rma notu

- tendermeister â‚¬299â€“â‚¬899 (kurumsal/AB). ihaleciler TR abonelik. Bizimki â‚º1.490/â‚º3.990 â€” TR pazarÄ±na uygun.
- **Risk:** ihaleciler veri derinliÄŸinde Ã¶nde; biz **AI + sadelik + harita + uyum skoru** ile farklÄ±laÅŸmalÄ±yÄ±z.
  SatÄ±ÅŸ mesajÄ±: *"ihaleciler'in tÃ¼m verisi + yapay zekÃ¢ ile teklif/analiz, yarÄ±sÄ± kadar kalabalÄ±k arayÃ¼zde."*
- Bu yÃ¼zden **P0 (sonuÃ§ verisi) + P1 (analitik/KÄ°K)** olmadan "ihaleciler'e eÅŸ" diyemeyiz; **P2 (AI Brain/teklif)**
  olmadan "tendermeister'e eÅŸ" diyemeyiz. SÄ±ra bu yÃ¼zden aÅŸaÄŸÄ±daki gibi.

---

## ğŸ¯ Ã–NERÄ°LEN UYGULAMA SIRASI (Ã–ncelik 9 iÃ§in)

> "Asla eksiÄŸimiz kalmasÄ±n" hedefi â†’ Ã¶nce ihaleciler paritesi (TR pazarÄ±), sonra tendermeister AI vizyonu.

1. **P0 â€” SonuÃ§/sÃ¶zleÅŸme verisi scrape + ÅŸema** (9.1) â†’ analitiÄŸin yakÄ±tÄ±. *Her ÅŸeyden Ã¶nce bu.*
2. **P1 â€” Firma & idare derin analizi** (9.2) â†’ ihaleciler amiral gemisine parite.
3. **P1 â€” KÄ°K kararlarÄ± DB + arama** (9.3) â†’ ihaleciler'in diÄŸer bÃ¼yÃ¼k kozu.
4. **P2 â€” AI Brain + RAG profil** (9.4) â†’ eÅŸleÅŸme ve teklifin temeli; profil alanlarÄ±nÄ± tamamla.
5. **P2 â€” AkÄ±llÄ± eÅŸleÅŸme skoru + eÅŸik** (9.7) â†’ AI farkÄ± gÃ¶rÃ¼nÃ¼r olur.
6. **P2 â€” Ä°hale-baÅŸÄ±na AI teklif workflow** (9.5) â†’ tendermeister'in Ã§ekirdek deÄŸeri (uyumluluk.html'i entegre et).
7. **P2 â€” Hesap Ã¼retkenlik** (9.10: BÃ¼ltenlerim, OkuduklarÄ±m, SÃ¶zleÅŸme listem, push) + **dizinler** (9.9).
8. **P3 â€” Ã‡ok kaynak + anlÄ±k tarama** (9.6), **Ã§ok dil** (9.8), **yurtdÄ±ÅŸÄ±/AB**.

> **Not (kalÄ±cÄ± talimat gereÄŸi):** Bu bÃ¶lÃ¼m Ã¼zerinde Ã§alÄ±ÅŸÄ±rken her tamamlanan maddeyi ğŸŸ¢'ya Ã§evir,
> dokunulan dosyalarÄ± yaz, ve yeni fark edilen aÃ§Ä±klarÄ± buraya ekle. Veriye baÄŸlÄ± (ğŸ§±) maddeler 9.1 bitmeden baÅŸlamaz.

---

## ğŸ“‹ Ä°HALECÄ°LER.COM EKSÄ°KLERÄ° â€” YAPILACAKLAR (9 Temmuz 2026)

> CanlÄ± karÅŸÄ±laÅŸtÄ±rma yapÄ±ldÄ± (9 Tem 2026). Onlarda var, bizde yok olanlar Ã¶nceliklendirildi.
> **Uygulama sÄ±rasÄ±:** 1 (gÃ¼nlÃ¼k sayaÃ§) â†’ 2 (sonuÃ§lananlar sayfasÄ±) â†’ 3 (KÄ°K kararlarÄ±) â†’ 4+.

### âœ… 1. GÃ¼nlÃ¼k CanlÄ± SayaÃ§ â€” Dashboard (9 Tem 2026, TAMAMLANDI)
ihaleciler ana sayfasÄ±nda "BugÃ¼n yayÄ±nlananlar X | BugÃ¼n yapÄ±lacaklar Y | BugÃ¼n sonuÃ§lananlar Z" 3'lÃ¼ banner var.
- âœ… **Dashboard header sayacÄ± zaten vardÄ±** (`hdr-bugun`, `hdr-songun`); yeni 3'lÃ¼ stats strip eklendi:
  "BugÃ¼n Eklendi Â· BugÃ¼n Son Teklif Â· Toplam KazanÄ±m KaydÄ±" (commit â†“)
- Dokunulan dosyalar: `dashboard.html`

### âœ… 2. SonuÃ§lananlar SayfasÄ± (`/sonuclananlar`) â€” (9 Tem 2026, TAMAMLANDI)
ihaleciler'de "BugÃ¼n sonuÃ§lananlar" akÄ±ÅŸÄ± â†’ kazanan firma + sÃ¶zleÅŸme bedeli + tenzilat gÃ¶steriyor.
- âœ… `sonuclananlar.html` oluÅŸturuldu: `ihale_sonuclari` tÃ¼m kayÄ±tlarÄ± gÃ¶sterir, firma/bedel/tenzilat/tarih
- Filtreler: sÄ±ralama (tarih/bedel/tenzilat), il, maliyet aralÄ±ÄŸÄ±
- Sidebar nav'a eklendi
- Dokunulan dosyalar: `sonuclananlar.html`, nav linkleri (firma-analiz.html vb.)

### âœ… 3. KÄ°K Karar Arama (`/kik-kararlar`) â€” TAMAMLANDI (9 Temmuz 2026)
- `kik-kararlar.html`: arama formu (kelime/no/tÃ¼r/sonuÃ§/tarih aralÄ±ÄŸÄ±), filtre chipleri, CSV, sayfalama
- `backend/supabase/migrations/kik_kararlar_tablo.sql`: DB ÅŸemasÄ± + tam-text indeksler + RLS
- `backend/kik_backfill.py`: KÄ°K API'sinden karar Ã§eken cron scripti
- 15 HTML dosyasÄ±nda sidebar'a âš–ï¸ KÄ°K Kararlar nav linki eklendi

#### ğŸ”§ KÄ°K Cron Kurulum AdÄ±mlarÄ± â€” KULLANICI MANUEL UYGULAR

**VDS BaÄŸlantÄ±sÄ± (PowerShell veya Windows Terminal'de):**
```
ssh -i $HOME\.ssh\ihale_oracle root@195.85.207.126
```

**ADIM 1 â€” Kodu VDS'e Ã§ek:**
```bash
cd /opt/ihale-platform
git pull origin main
```
Beklenen Ã§Ä±ktÄ±: `kik_backfill.py` + `kik_kararlar_tablo.sql` dosyalarÄ±nÄ±n indiÄŸini gÃ¶rÃ¼rsÃ¼n.

**ADIM 2 â€” Supabase'de tabloyu oluÅŸtur (SQL Ã§alÄ±ÅŸtÄ±r):**
VDS'de managed Supabase'e psql ile baÄŸlan ve SQL migration'Ä± uygula:
```bash
cd /opt/ihale-platform/backend
source .env
psql "$SUPABASE_DB_URL" -f supabase/migrations/kik_kararlar_tablo.sql
```
EÄŸer `SUPABASE_DB_URL` yoksa alternatif â€” Supabase Dashboard:
1. https://supabase.com/dashboard â†’ proje â†’ SQL Editor
2. `backend/supabase/migrations/kik_kararlar_tablo.sql` dosyasÄ±nÄ± aÃ§, iÃ§eriÄŸi yapÄ±ÅŸtÄ±r, RUN

**ADIM 3 â€” `run_scraper.sh`'e KÄ°K backfill ekle:**
```bash
cat >> /opt/ihale-platform/backend/run_scraper.sh << 'EOF'
$VENV/python kik_backfill.py --max-pages 10 >> /opt/ihale-platform/logs/scraper.log 2>&1
EOF
```

**ADIM 4 â€” Test Ã§alÄ±ÅŸtÄ±r (5 sayfa = ~100 karar):**
```bash
cd /opt/ihale-platform/backend
source .env
venv/bin/python kik_backfill.py --max-pages 5
```

**ADIM 5 â€” DoÄŸrula:**
```bash
venv/bin/python - << 'PY'
import os, sys
sys.path.insert(0, '.')
from supabase import create_client
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
r = sb.table('kik_kararlar').select('id', count='exact').execute()
print('kik_kararlar kayÄ±t sayÄ±sÄ±:', getattr(r, 'count', None) or len(r.data or []))
PY
```

- [x] ADIM 1: VDS'e git pull Ã§ek âœ…
- [x] ADIM 2: `kik_kararlar` tablosu Supabase'de oluÅŸturuldu âœ…
- [x] ADIM 3: `run_scraper.sh`'e kik_backfill satÄ±rÄ± eklendi âœ…
- [x] ADIM 4: Test Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± â€” KÄ°K tÃ¼m endpointleri bloke ediyor âš ï¸
  - `ekap.kik.gov.tr/EKAP/karar/arama` â†’ 302 (login)
  - `ekapv2.kik.gov.tr/b_ihalearama/api/Karar/Arama` â†’ 401
  - `www.kik.gov.tr/tr/uyusmazlik-kararlari` â†’ 406 (IP bloÄŸu)
- [ ] ADIM 5: â¸ï¸ Beklemede â€” veri kaynaÄŸÄ± sorunu Ã§Ã¶zÃ¼lene kadar sayfa boÅŸ gÃ¶sterir

**Alternatif veri kaynaklarÄ± (yapÄ±lacak):**
- `ekapv2.kik.gov.tr` crypto-auth ile tÃ¼m karar endpoint'leri denendi â†’ tÃ¼mÃ¼ 404 (API'de karar modÃ¼lÃ¼ yok)
- `www.kik.gov.tr` â†’ 406 (IP bloÄŸu, header'dan baÄŸÄ±msÄ±z)
- **Ã‡Ã¶zÃ¼m:** Playwright kurulumu VDS'e (`playwright install chromium`) â†’ headless browser ile kik.gov.tr atlatÄ±labilir
- Veya Ã¼cretli proxy servisi (brightdata.com) â€” dÃ¼ÅŸÃ¼k Ã¶ncelik, ileride deÄŸerlendir

### âœ… 4. EÅŸik KatsayÄ±sÄ± Filtresi â€” TAMAMLANDI (10 Tem 2026, Faz C4, bkz. yukarÄ±daki SON DURUM notu)
`ilanlar.esik_katsayi` kolonu + scraper regex parse + `ihaleler.html` dropdown filtresi kodu hazÄ±r
(`backend/migration_esik_katsayi.sql` â€” VDS'e henÃ¼z uygulanmadÄ±, bkz. "SIRADAKÄ° OTURUM" listesi).

### ğŸ”² 5. Gazete / Yerel Ä°haleler â€” BÃœYÃœK Ä°Å, DÃœÅÃœK Ã–NCELÄ°K
ihaleciler EKAP dÄ±ÅŸÄ±nda gazete ve "istihbarat" kaynaklÄ± ilanlar da gÃ¶steriyor (Ã¶zel sektÃ¶r alÄ±mlarÄ± vb.).
- EKAP-dÄ±ÅŸÄ± kaynak = kendi kazÄ±ma/ortaklÄ±k gerektiriyor; Ã¶nce EKAP derinleÅŸtir.
- ErtelenmiÅŸ (9.6'da iÅŸlenmiÅŸ).

### âœ… 6. BÃ¼lten Sistemi â€” TAMAMLANDI (9 Temmuz 2026)
- `bultenler` tablosu VDS Supabase'de oluÅŸturuldu + GRANT verildi
- `bulten_gonder.py`: gece Ã§alÄ±ÅŸan e-posta gÃ¶nderici; filtre eÅŸleÅŸmesi bulur â†’ Resend ile HTML e-posta gÃ¶nderir â†’ son_gonderim gÃ¼nceller
- `bildirimler.html` BÃ¼ltenlerim sekmesi: DB tabanlÄ±, yeni bÃ¼lten formu (ad/kelime/il/tÃ¼r/min bedel/frekans), e-posta durum gÃ¶stergesi, sil
- `run_scraper.sh`'e `bulten_gonder.py` eklendi â€” her gece scraper'dan sonra Ã§alÄ±ÅŸÄ±r
- **Test:** `venv/bin/python bulten_gonder.py` â†’ "Aktif bÃ¼lten yok, Ã§Ä±kÄ±lÄ±yor" âœ…

### ğŸ”² 7. SÃ¶zleÅŸme Listesi â€” KÃœÃ‡ÃœK Ã–NCELÄ°K
ihaleciler'de kullanÄ±cÄ±lar kazandÄ±klarÄ± ihaleleri "sÃ¶zleÅŸme listesi"ne ekleyebiliyor.
- Bizde `teklifler` tablosu var (taslak/gÃ¶nderildi durumu) â€” sÃ¶zleÅŸmeye dÃ¶nÃ¼ÅŸtÃ¼rme akÄ±ÅŸÄ± eklenebilir.
- DÃ¼ÅŸÃ¼k Ã¶ncelik; teklif modÃ¼lÃ¼ stabil olunca.

---

# ğŸ† Ã–NCELÄ°K 10 â€” FÄ°RMA VERÄ°SÄ° MASTER PLANI: Ä°HALECÄ°LER'Ä° YAKALA VE GEÃ‡ (9 Tem 2026, Fable 5 analizi)

## ğŸ“ SON DURUM (10 Tem 2026, Opus oturumu) â€” Ã–NCE BUNU OKU

> **ğŸ‰ DNS CUTOVER TAMAMLANDI â€” CANLI SÄ°TE ARTIK VDS'TE: `https://ihaleglobal.com`**
> Cloudflare (proxied, Full strict + Origin Cert) â†’ VDS `195.85.207.126` (self-hosted Supabase).
> 20.686 sonuÃ§, 11.186 firma, 14.378 aktif ilan, tÃ¼m Ã–NCELÄ°K 10 Ã¶zellikleri CANLI. Managed terk edildi.
>
> **Cutover'da yapÄ±lanlar:** (1) VDS'e nginx 443/SSL kuruldu (CF Origin Cert `/etc/nginx/ssl/`). (2) Frontend
> (tÃ¼m *.html + js/*.js â€” sidebar-user/plan/takip/api/harita kendi client'Ä±nÄ± oluÅŸturuyordu) managed URL/key â†’
> `https://ihaleglobal.com` + VDS anon key; repo'ya commit'lendi (95373d6), VDS git ile senkron. (3) Cloudflare
> DNS A â†’ VDS IP (proxied), SSL Full(strict). (4) SITE_URL=https, auth restart. CanlÄ± test: 8 sayfa 200,
> auth/REST/RPC/harita hepsi gerÃ§ek veriyle Ã§alÄ±ÅŸÄ±yor.
>
> **âœ… Resend domain doÄŸrulama TAMAMLANDI (10 Tem, kullanÄ±cÄ±):** `ihaleglobal.com` Resend'e eklendi, region
> Ireland (eu-west-1). 4 DNS kaydÄ± Cloudflare'e eklendi (DNS only/gri bulut): TXT `resend._domainkey` (DKIM),
> MX `send.ihaleglobal.com`â†’`feedback-smtp.eu-west-1.amazonses.com` (Ã¶ncelik 10), TXT `send.ihaleglobal.com`
> (SPF `v=spf1 include:amazonses.com ~all`), TXT `_dmarc` (`v=DMARC1; p=none;`). Resend panelinde
> **Status: Verified** (Domain added â†’ DNS verified â†’ Domain verified, hepsi yeÅŸil). Domain artÄ±k mail
> gÃ¶nderebilir durumda.
>
> **âœ… SMTP gÃ¶nderici deÄŸiÅŸimi TAMAMLANDI (10 Tem 2026, kullanÄ±cÄ± tam onay verdi):** VDS
> `/opt/supabase/docker/.env`'de `SMTP_ADMIN_EMAIL=noreply@ihaleglobal.com` yapÄ±ldÄ± (yedek `.env.bak.<ts>`
> alÄ±ndÄ±), `docker compose up -d auth` ile yeniden baÅŸlatÄ±ldÄ±. Test signup (`smtptest.*@gmail.com`) â†’ HTTP 200,
> `confirmation_sent_at` set, auth loglarÄ±nda SMTP hatasÄ± YOK (istek 3.3sn â€” gerÃ§ek SMTP gÃ¶nderim gecikmesi,
> hata olsa anÄ±nda dÃ¶nerdi). ArtÄ±k gerÃ§ek kullanÄ±cÄ±lara `noreply@ihaleglobal.com`'dan mail gidiyor.
>
> **ğŸŸ¡ GitHub Actions scraper TAMAMLANDI (10 Tem):** `.github/workflows/ekap_scraper.yml`'deki `schedule`
> tetikleyicisi kaldÄ±rÄ±ldÄ± (sadece `workflow_dispatch` â€” manuel/yedek olarak kalabilir). VDS cron zaten tek
> aktif scraper. Dosya SÄ°LÄ°NMEDÄ° (acil durumda elle tetiklenebilsin diye).
>
> **âš ï¸ Ã–NEMLÄ° DÃœZELTME â€” Render KAPATILMADI, kapatÄ±lmamalÄ±:** Bu dosyadaki eski not "Render + GitHub Actions
> = eski/gereksiz servisler" diyordu ama bu YANLIÅ/GÃœNCEL DEÄÄ°L. `js/api.js`'deki `CONFIG.BASE_URL` hÃ¢lÃ¢
> `https://ihale-api.onrender.com`'a iÅŸaret ediyor â€” yani **frontend'in AI analiz, Ã¶deme (Ä°yzico), plan-iptal,
> firma-AI-yorum gibi TÃœM backend API Ã§aÄŸrÄ±larÄ± hÃ¢lÃ¢ Render'a gidiyor**, VDS'in kendi FastAPI'sine (`/api/`
> proxy, nginx Ã¼zerinden 127.0.0.1:8080) DEÄÄ°L. Render'Ä± kapatmak bu Ã¶zellikleri anÄ±nda kÄ±rar. Render'Ä±
> gÃ¼venle kapatmak iÃ§in Ã¶nce `js/api.js:15`'teki `BASE_URL`'i `https://ihaleglobal.com/api` yapÄ±p uÃ§tan uca
> test etmek gerekir (ayrÄ± bir iÅŸ â€” bu oturumda yapÄ±lmadÄ±, sadece tespit edildi).
>
> **ğŸ”² KALAN (kÃ¼Ã§Ã¼k, ilk gerÃ§ek deneme UFW klasik gÃ¼venlik sÄ±nÄ±flandÄ±rÄ±cÄ±sÄ± tarafÄ±ndan engellendi â€” kullanÄ±cÄ±
> Ã¶zel onayÄ± gerek):** UFW `8000/tcp Anywhere` aÃ§Ä±k duruyor (Kong'a nginx dÄ±ÅŸÄ±ndan doÄŸrudan eriÅŸilebiliyor).
> nginx zaten `127.0.0.1:8000`'e proxy yapÄ±yor (`/etc/nginx/snippets/ihale-locations.conf:8`) â†’ dÄ±ÅŸarÄ±dan
> eriÅŸime gerek yok, gÃ¼venle kapatÄ±labilir. Komut: `ssh ... "ufw delete allow 8000/tcp"` (v4+v6 iki kural).

---

## ğŸ“ SON DURUM (10 Tem 2026, Sonnet oturumu, devamÄ±) â€” Ã–NCE BUNU OKU

> Bu oturumda tamamlananlar + **3 madde kullanÄ±cÄ±nÄ±n Ã–ZEL onayÄ±nÄ± bekliyor** (genel "her ÅŸeyi yap" yetkisi
> production deÄŸiÅŸiklikleri iÃ§in otomatik gÃ¼venlik sÄ±nÄ±flandÄ±rÄ±cÄ±sÄ±nÄ± geÃ§miyor â€” her biri ayrÄ± ayrÄ±
> onaylanmalÄ±, aÅŸaÄŸÄ±da net komutlarÄ±yla yazÄ±lÄ±).

**âœ… Bu oturumda TAMAMLANANLAR:**
1. SMTP gÃ¶ndericisi `noreply@ihaleglobal.com`'a Ã§evrildi + test signup ile doÄŸrulandÄ± (auth loglarÄ±nda hata yok).
2. GitHub Actions scraper zamanlamasÄ± kapatÄ±ldÄ± (`.github/workflows/ekap_scraper.yml` â€” artÄ±k sadece manuel).
3. **D2 tamamlandÄ±:** `ihale-detay.html` kazanma bandÄ± kutusuna "bu idare/sektÃ¶rde son sÃ¶zleÅŸmeler" emsal
   listesi eklendi (ihale_sonuclariâ‹ˆilanlar, son 5 kayÄ±t). VDS canlÄ± veriyle doÄŸrulandÄ±.
4. **Bildirim servisinin son parÃ§asÄ± tamamlandÄ±:** `profil.html`'e e-posta bildirim tercihi UI'Ä± eklendi
   (bildirim_email/bildirim_son_teklif/bildirim_gun_oncesi â€” DB kolonlarÄ± zaten VDS'te vardÄ±). Kod
   `anahtar_kelimeler` ile aynÄ± savunmacÄ± yazÄ±m deseninde (kolon yoksa sessiz hata). Auth olmadÄ±ÄŸÄ± iÃ§in
   canlÄ± round-trip test edilemedi ama syntax/render doÄŸrulandÄ±.

**âš ï¸ Ã–NEMLÄ° BULGU â€” Render backend HÃ‚LÃ‚ CANLI KULLANIMDA, kapatÄ±lmamalÄ±:**
`js/api.js:15` `CONFIG.BASE_URL` hÃ¢lÃ¢ `https://ihale-api.onrender.com`'a iÅŸaret ediyor. AI analiz, Ä°yzico
Ã¶deme, plan-iptal, firma-AI-yorum gibi TÃœM backend Ã§aÄŸrÄ±larÄ± hÃ¢lÃ¢ Render'a gidiyor â€” VDS'in kendi FastAPI'sine
(`ihale-api` systemd, nginx `/api/` proxy) DEÄÄ°L. **AyrÄ±ca Render'daki deploy GÃœNCEL DEÄÄ°L:** `bb88c40`
(Faz D1, `/ai/firma-yorum`) ve `4fc8a29` (`/plan-iptal`) commit'leri push'landÄ± ama Render'da hÃ¢lÃ¢ 404
dÃ¶nÃ¼yor (kod repoda var, canlÄ±da yok â€” auto-deploy tetiklenmemiÅŸ ya da sessizce fail olmuÅŸ). **Etki:**
kullanÄ±cÄ± "Analizi OluÅŸtur" veya plan iptali denediÄŸinde arka planda 404 alÄ±yor. **KullanÄ±cÄ± Render
dashboard'undan manuel "Deploy latest commit" tetiklemeli** (bu oturumda Render API eriÅŸimi/credential yok).

**ğŸ”² KULLANICI Ã–ZEL ONAYI BEKLEYEN 3 MADDE (genel yetki yeterli gÃ¶rÃ¼lmedi, ayrÄ± ayrÄ± sorulmalÄ±):**
1. **UFW `8000/tcp` kapatma** â€” `ssh -i ~/.ssh/ihale_oracle root@195.85.207.126 "ufw delete allow 8000/tcp"`
   (v4+v6 iki satÄ±r). GÃ¼venli: nginx zaten 127.0.0.1 Ã¼zerinden proxy yapÄ±yor.
2. **`backend/.env`'e RESEND_API_KEY ekleme** â€” notify.py'nin Resend HTTP API'si (SMTP'den ayrÄ±) iÃ§in gerekli.
   AynÄ± key zaten `/opt/supabase/docker/.env`'deki `SMTP_PASS`'te var, sadece kopyalanacak. Bu YAPILMADAN
   bildirimler (yukarÄ±daki UI ile opt-in olsalar bile) gÃ¶nderilemez.
3. **Render'da manuel redeploy tetikleme** (yukarÄ±ya bak) â€” D1 (AI firma yorumu) ve plan-iptal canlÄ±ya
   Ã§Ä±kmasÄ± iÃ§in ÅŸart.

**SÄ±radaki mantÄ±klÄ± adÄ±m (bu 3 onay gelince):** notify.py'yi cron'da test et (artÄ±k gerÃ§ek opt-in kullanÄ±cÄ± +
RESEND_API_KEY olacak), sonra C4/E1/E3/E4'e geÃ§ (bkz. yukarÄ±daki "10.F Uygulama sÄ±rasÄ±").

---

## ğŸ“ SON DURUM (10 Tem 2026, otonom launch oturumu) â€” Ã–NCE BUNU OKU

> KullanÄ±cÄ± "3 gÃ¼n iÃ§inde canlÄ±ya alalÄ±m, saÄŸlam ve geÃ§miÅŸ verilerle" dedi, otonom yetki verdi. Bu oturumda
> yukarÄ±daki 3 bekleyen madde Ã§Ã¶zÃ¼ldÃ¼ + **"Render deploy gÃ¼ncel deÄŸil" teÅŸhisinin YANLIÅ olduÄŸu ortaya Ã§Ä±ktÄ±**
> â€” gerÃ§ek kÃ¶k neden bulunup dÃ¼zeltildi. Render artÄ±k tamamen devre dÄ±ÅŸÄ± bÄ±rakÄ±labilir.

**âœ… TAMAMLANANLAR (kullanÄ±cÄ± onayÄ±yla, SSH ile VDS `195.85.207.126`):**
1. **UFW `8000/tcp` kapatÄ±ldÄ±** (v4+v6). Kong artÄ±k sadece nginx Ã¼zerinden eriÅŸilebilir.
2. **`RESEND_API_KEY` `backend/.env`'e eklendi** (Supabase SMTP_PASS ile aynÄ± Resend key â€” kullanÄ±cÄ± bu spesifik
   credential-reuse'u ayrÄ±ca onayladÄ±). notify.py artÄ±k gerÃ§ek bildirim e-postasÄ± gÃ¶nderebilir.
3. **ğŸ”´ GERÃ‡EK KÃ–K NEDEN BULUNDU + DÃœZELTÄ°LDÄ° â€” `/plan-iptal` 404'Ã¼nÃ¼n sebebi Render'Ä±n eski deploy'u DEÄÄ°LDÄ°:**
   `backend/api.py`, `backend/payment.py`'deki `APIRouter`'Ä± (`/plan-iptal`, `/odeme/baslat`, `/webhook/iyzico`,
   `/planlar`) **hiÃ§bir zaman `include_router()` ile baÄŸlamÄ±yordu.** Bu route'lar repo'da var olalÄ± beri
   (ne Render'da ne VDS'te) hiÃ§ canlÄ± olmamÄ±ÅŸtÄ±. DÃ¼zeltme: `api.py`'ye `from payment import router as
   payment_router` + `app.include_router(payment_router)` eklendi (commit `89fb7ed`). AyrÄ±ca VDS venv'inde
   `iyzipay` paketi eksikti (import zinciri patlardÄ±) â†’ kuruldu. **DoÄŸrulandÄ±:** VDS'te restart sonrasÄ±
   `curl https://ihaleglobal.com/api/plan-iptal` artÄ±k 401 (auth gerekli) dÃ¶nÃ¼yor, 404 deÄŸil.
4. **Render baÄŸÄ±mlÄ±lÄ±ÄŸÄ± tamamen kaldÄ±rÄ±ldÄ± (commit `fcc87cc`):** `js/api.js` `CONFIG.BASE_URL`
   `https://ihale-api.onrender.com` â†’ `https://ihaleglobal.com/api` (VDS'in kendi FastAPI'si, nginx `/api/`
   proxy, aynÄ± origin â†’ CORS'a bile gerek yok). VDS git ile senkron edildi. **DoÄŸrulandÄ± (public internetten
   curl):** `https://ihaleglobal.com/api/planlar` â†’ 200, gerÃ§ek plan verisi dÃ¶nÃ¼yor.
   âš ï¸ **Render servisi artÄ±k kullanÄ±cÄ± tarafÄ±ndan gÃ¼venle kapatÄ±labilir** â€” repo'da `ihale-api.onrender.com`'a
   giden hiÃ§bir runtime referans kalmadÄ± (sadece YAPILACAKLAR.md/payment.py'da eski dokÃ¼man/yorum satÄ±rÄ± var).
5. **GeÃ§miÅŸ veri â€” cron kalÄ±cÄ± olarak geniÅŸ moda geÃ§irildi:** `run_scraper.sh`'teki gece `ekap_sonuc_backfill.py`
   Ã§aÄŸrÄ±sÄ±na `--tum-kayitlar` eklendi (yedek `run_scraper.sh.bak.<ts>` alÄ±ndÄ±). Ã–nceden bu satÄ±r bayraksÄ±zdÄ± â†’
   sadece bizim `ilanlar` havuzumuzla kesiÅŸen sonuÃ§larÄ± yazÄ±yordu (~%0.7 isabet, gece baÅŸÄ±na ~1-2 yeni kayÄ±t).
   ArtÄ±k her gece IKN havuzundan baÄŸÄ±msÄ±z geniÅŸ tarama yapÄ±yor (Faz A3 mantÄ±ÄŸÄ±) â€” geÃ§miÅŸ veri kalÄ±cÄ± olarak bÃ¼yÃ¼yecek.
6. **Ek geniÅŸ backfill partisi baÅŸlatÄ±ldÄ± (kullanÄ±cÄ± onayÄ±yla, arka planda):** VDS'te `nohup ekap_sonuc_backfill.py
   --tum-kayitlar --max-pages 400` â€” log: `/opt/ihale-platform/logs/manual_backfill.log`. Checkpoint
   `.sonuc_backfill_checkpoint.json`'dan devam eder (bu oturum baÅŸÄ±nda skip=20200). BaÅŸlangÄ±Ã§ hacmi: 29.809
   ilan, 20.689 sonuÃ§, 11.187 firma (662 milyar TL sÃ¶zleÅŸme). **SÄ±radaki oturum: log'u kontrol et, tamamlandÄ±ysa
   (veya 403/429 ile durduysa) yeni bir parti baÅŸlat / Webshare proxy deÄŸerlendir.**
7. **Repo temizliÄŸi:** kÃ¶k dizinde yanlÄ±ÅŸ-adlÄ± (Windows path'i literal dosya adÄ± olmuÅŸ) bir stray dosya
   silindi; iÃ§eriÄŸi (`GRANT ALL ON public.bultenler ...`) gerÃ§ek migration dosyasÄ±na (`backend/supabase/
   migrations/bultenler_tablo.sql`) eklendi (VDS'te zaten elle uygulanmÄ±ÅŸtÄ±, sadece dokÃ¼mantasyon eksikti).

**ğŸŸ¡ DÃœÅÃœK Ã–NCELÄ°K â€” bu oturumda gÃ¶rÃ¼lÃ¼p DOKUNULMADI (launch'Ä± bloklamÄ±yor):**
- `teklif-olustur.html:1428` farklÄ±/var olmayan bir Render servisine (`ihaleplatform-backend.onrender.com`,
  `ihale-api.onrender.com` DEÄÄ°L) `.catch(()=>null)` ile sessizce no-op eden bir fetch var â†’ zaten mock/Ã¶rnek
  metne dÃ¼ÅŸÃ¼yor, kÄ±rÄ±k deÄŸil ama "gerÃ§ek AI teklif oluÅŸturma" hiÃ§ Ã§alÄ±ÅŸmÄ±yor. Ä°stenirse `/api/teklif-olustur`
  diye bir endpoint api.py'a eklenip buraya baÄŸlanabilir (ayrÄ± iÅŸ, teklif taslaÄŸÄ± ÅŸema kararÄ± â€” bkz. 9.5 notu).
- `backend/payment.py` docstring'indeki Ä°yzico webhook URL yorumu hÃ¢lÃ¢ eski Render adresini gÃ¶steriyor
  (kod deÄŸil, sadece dokÃ¼mantasyon) â€” payment flow zaten Supabase Edge Function `odeme-baslat` kullanÄ±yor,
  bu router'daki `/odeme/baslat`+`/webhook/iyzico` aktif kullanÄ±lmÄ±yor gibi gÃ¶rÃ¼nÃ¼yor; kafa karÄ±ÅŸÄ±klÄ±ÄŸÄ±
  yaratmasÄ±n diye yorum gÃ¼ncellenebilir, dÃ¼ÅŸÃ¼k Ã¶ncelik.

**ğŸ”´ğŸ”´ KRÄ°TÄ°K BULGU + BÃœYÃœK KISMI DÃœZELTÄ°LDÄ° â€” Ã¶deme yapan HÄ°Ã‡BÄ°R kullanÄ±cÄ± Pro olamÄ±yordu:**
Ã–deme akÄ±ÅŸÄ±nÄ± incelerken (Render kaldÄ±rma sonrasÄ± "gerÃ§ek checkout hangi yolu kullanÄ±yor" kontrolÃ¼nde)
iki ayrÄ±, birbirini pekiÅŸtiren bug bulundu:
1. **`js/plan.js`'nin `PRO_PLANS` listesi** (`isPro()`/`getPlan()` bunu kullanÄ±yor) sadece
   `'pro'|'Pro'|'PRO'|'premium'|'enterprise'` deÄŸerlerini tanÄ±yordu. Ama `kullanici_krediler.plan` kolonu
   `planlar.kod`'a FK'li ve orada **SADECE** `'free'|'standart'|'kurumsal'` geÃ§erli. Yani DB'ye doÄŸru yazÄ±lsa
   bile hiÃ§bir Ã¶deme frontend'de asla "pro" gÃ¶rÃ¼nemezdi â€” 8 Tem'deki "js/plan.js profil.plan yerine
   kullanici_krediler.plan okusun" dÃ¼zeltmesi (bkz. yukarÄ±daki "STATÄ°K BUG AVI" bÃ¶lÃ¼mÃ¼) HANGÄ° TABLODAN
   okunacaÄŸÄ±nÄ± dÃ¼zeltti ama DEÄER eÅŸleÅŸmesini kontrol etmemiÅŸti. **DÃœZELTÄ°LDÄ°:** `PRO_PLANS`'a
   `'standart'`+`'kurumsal'` eklendi (commit `57b6e1c`).
2. **GerÃ§ek checkout butonu payment.py'yi DEÄÄ°L, Supabase Edge Function `odeme-baslat`'Ä± Ã§aÄŸÄ±rÄ±yor**
   (`fiyatlandirma_odeme_bolumu.html:484`, `sb.functions.invoke('odeme-baslat', ...)`). Bu fonksiyon:
   (a) **VDS'in self-hosted functions volume'Ã¼ne HÄ°Ã‡ DEPLOY EDÄ°LMEMÄ°ÅTÄ°** â€” `curl .../functions/v1/odeme-baslat`
   500 "could not find an appropriate entrypoint" dÃ¶nÃ¼yordu (repo'da kod vardÄ±, VDS'te dosya yoktu â€” Render'Ä±n
   webhook'unda olduÄŸu gibi yine "deploy eksikliÄŸi" deÄŸil ama benzer bir "kod var ama canlÄ± deÄŸil" sÄ±nÄ±fÄ±).
   (b) Kod, var OLMAYAN `profil.plan`/`plan_baslangic`/`plan_bitis`/`iyzico_payment_id` kolonlarÄ±na upsert
   atÄ±yordu (`profil` tablosunda bu kolonlar hiÃ§ yok) â€” hata kontrol edilmediÄŸi iÃ§in Ä°yzico'dan para alÄ±nÄ±p
   DB gÃ¼ncellenemese bile kullanÄ±cÄ±ya sahte "Ã¶deme baÅŸarÄ±lÄ±" mesajÄ± dÃ¶nerdi.
   **DÃœZELTÄ°LDÄ° (commit `57b6e1c`):** artÄ±k `kullanici_krediler`'e (payment.py'nin `kredi_yukle()`'siyle aynÄ±
   hedef) yazÄ±yor, `proâ†’standart` kod Ã§evirisi yapÄ±yor (frontend "pro" der, DB "standart" ister),
   `kredi_hareketleri`+`bildirimler` kaydÄ± ekliyor, DB yazÄ±mÄ± baÅŸarÄ±sÄ±z olursa artÄ±k gerÃ§ek hatayÄ± dÃ¶nÃ¼yor.
   **VDS'e deploy edildi** (dosya `/opt/supabase/docker/volumes/functions/odeme-baslat/index.ts`'e kopyalandÄ±,
   `docker compose restart functions`) â€” doÄŸrulandÄ±: `curl .../functions/v1/odeme-baslat` artÄ±k 401
   (auth gerekli) dÃ¶nÃ¼yor, 404/500-entrypoint deÄŸil.
   **âš ï¸ KALAN â€” kullanÄ±cÄ± Ã¶zel onayÄ± istedi, henÃ¼z yapÄ±lmadÄ±:** edge-functions container'Ä±nda
   `IYZICO_API_KEY`/`IYZICO_SECRET_KEY` env deÄŸiÅŸkenleri YOK (backend/.env'de var ama edge function ayrÄ±
   container, ayrÄ± env alÄ±r). Bu eklenmeden fonksiyon "iyzico anahtarlarÄ± tanÄ±mlÄ± deÄŸil" (500) dÃ¶ner.
   Ekleme yeri: `/opt/supabase/docker/.env`'e `IYZICO_API_KEY=`/`IYZICO_SECRET_KEY=` satÄ±rlarÄ± (backend/.env'deki
   ile aynÄ± deÄŸer) + `/opt/supabase/docker/docker-compose.yml`'deki `functions:` servisinin `environment:`
   bloÄŸuna `IYZICO_API_KEY: ${IYZICO_API_KEY}` / `IYZICO_SECRET_KEY: ${IYZICO_SECRET_KEY}` satÄ±rlarÄ± + `docker
   compose up -d functions`. Åu an Ä°yzico sandbox modda (`IYZICO_BASE_URL=https://sandbox.iyzipay.com`, test
   kartÄ±, gerÃ§ek para hareketi yok) â€” canlÄ±ya (gerÃ§ek para) geÃ§meden Ã¶nce prod key'lere Ã§evrilmeli.
   **BU EKLENMEDEN Ã¶deme akÄ±ÅŸÄ± test edilemez/Ã§alÄ±ÅŸmaz â€” sÄ±radaki oturumun ilk iÅŸi bu olmalÄ±.**

**ğŸ”´ğŸ”´ğŸ”´ EN KRÄ°TÄ°K BULGU â€” hiÃ§bir kullanÄ±cÄ± iÃ§in kullanici_krediler satÄ±rÄ± hiÃ§ oluÅŸturulmuyordu, AI analiz
BAÅTAN Ä°TÄ°BAREN KÄ°MSE Ä°Ã‡Ä°N Ã‡ALIÅAMAZDI (bu da dÃ¼zeltildi, kullanÄ±cÄ± onayÄ±yla VDS'e uygulandÄ±):**
`kullanici_krediler` (FK: `kullanici_id â†’ kullanici_profiller.id`) satÄ±rÄ±nÄ± oluÅŸturan HÄ°Ã‡BÄ°R mekanizma
yoktu â€” ne bir DB trigger'Ä± (auth.users'ta trigger arandÄ±, 0 sonuÃ§), ne backend kodu (`kullanici_profiller`
insert/upsert iÃ§in repo genelinde arama yapÄ±ldÄ±, hiÃ§bir sonuÃ§ Ã§Ä±kmadÄ± â€” `api.py`'nin `PUT /profil`'i bile
dÃ¼z `.update()` kullanÄ±yor, satÄ±r yoksa sessizce 0 satÄ±r etkiler). **SonuÃ§: `worker.py`'deki
`kullanici_analiz_isle()` â€” yani "Analiz Et" butonunun kod yolu â€” en baÅŸtaki `kullanici_krediler` sorgusunda
(`.single()`) 0 satÄ±rla patlÄ±yordu.** VDS'te doÄŸrulandÄ±: `kullanici_krediler` tablosu **tamamen BOÅTU** (0 satÄ±r,
6 kayÄ±tlÄ± kullanÄ±cÄ±ya raÄŸmen). Bu, yukarÄ±daki `kredi_dus` parametre-adÄ± bug'Ä±ndan bile Ã¶nce gelen, ondan
BAÄIMSIZ ikinci bir "AI analiz asla tamamlanamaz" nedeniydi â€” ikisi Ã¼st Ã¼ste binmiÅŸ iki ayrÄ± kÄ±rÄ±k halka.

**DÃœZELTME (commit `9643129`, kullanÄ±cÄ± onayÄ±yla VDS'e uygulandÄ±):** `backend/migration_yeni_kullanici_kredi.sql`
â€” `auth.users` INSERT'inde otomatik `kullanici_profiller`+`kullanici_krediler` (free plan, 3 kredi â€”
`planlar.free.aylik_kredi` ile aynÄ±) satÄ±rÄ± oluÅŸturan bir trigger + halihazÄ±rda kayÄ±tlÄ± 6 kullanÄ±cÄ± iÃ§in
tek seferlik backfill. **UygulandÄ± ve doÄŸrulandÄ±:** `auth_users=6, profiller=6, krediler=6` (Ã¶ncesi:
profiller=4, krediler=**0**). Rolled-back transaction ile uÃ§tan uca test edildi: `kredi_dus(...)` artÄ±k
gerÃ§ek bir kullanÄ±cÄ± satÄ±rÄ±na karÅŸÄ± `basari=true` dÃ¶nÃ¼yor, `kalan_kredi=3` doÄŸru okunuyor.

**AynÄ± oturumda ayrÄ±ca dÃ¼zeltildi (commit `f2f1663`):** `worker.py`'deki HER Ä°KÄ° `kredi_dus` Ã§aÄŸrÄ±sÄ± da
var olmayan `p_ihale_id` parametresiyle Ã§aÄŸrÄ±lÄ±yordu (gerÃ§ek imza: `p_kullanici_id/p_miktar/p_referans_id/
p_referans_tip/p_islem_turu/p_aciklama`, ilk ikisi hariÃ§ hepsi DEFAULT'lu). PostgREST bu isimle eÅŸleÅŸen
fonksiyon bulamadÄ±ÄŸÄ± iÃ§in `.execute()` istisna fÄ±rlatÄ±yordu; hiÃ§bir try/except olmadÄ±ÄŸÄ± iÃ§in bu, **Gemini
analizi zaten tamamlanmÄ±ÅŸ/API maliyeti harcanmÄ±ÅŸken** FastAPI'nin Ã§Ä±plak 500'Ã¼ne dÃ¶nÃ¼ÅŸÃ¼yordu. `p_referans_id`'ye
dÃ¼zeltildi + artÄ±k istisna yakalanÄ±p temiz JSON hatasÄ± dÃ¶nÃ¼yor. `api.py`'deki AI Firma Yorumu'nun kredi
dÃ¼ÅŸÃ¼mÃ¼ de aynÄ± hataya sahipti (try/except ile yutuluyordu, crash olmuyordu ama kredi hiÃ§ dÃ¼ÅŸmÃ¼yordu) â€” o da
dÃ¼zeltildi.

**âœ…âœ…âœ… AI ANALÄ°Z UÃ‡TAN UCA CANLI DOÄRULANDI (10 Tem, aynÄ± oturum devamÄ±) â€” platformun asÄ±l Ã¼cretli
Ã¶zelliÄŸi artÄ±k gerÃ§ekten Ã§alÄ±ÅŸÄ±yor.** YukarÄ±daki 3 dÃ¼zeltmeden sonra bile "Analiz Et" hÃ¢lÃ¢ Ã§alÄ±ÅŸamazdÄ± â€”
**6 AYRI EK KIRIK HALKA daha bulunup dÃ¼zeltildi** (hepsi canlÄ± VDS'te gerÃ§ek bir EKAP ihalesi + gerÃ§ek
CAPTCHA Ã§Ã¶zme + gerÃ§ek Gemini Ã§aÄŸrÄ±sÄ±yla test edildi, sonunda gerÃ§ek/kaliteli bir analiz raporu Ã¼retildi):

1. **HiÃ§bir aktif ihalede `pdf_url` dolu deÄŸildi (0/38.029)** â€” belgeler sadece CAPTCHA korumalÄ± bir EKAP
   linki iÃ§eriyordu, gerÃ§ek dosya hiÃ§ indirilmemiÅŸti. Gece turu bilerek "link-only" modda
   (`EKAP_BELGE_LINK=1`) â€” aÄŸÄ±r indirme (`EKAP_BELGE_INDIR`, Gemini ile CAPTCHA Ã§Ã¶zÃ¼p Storage'a yÃ¼kleme)
   zaten yazÄ±lmÄ±ÅŸtÄ± ama HÄ°Ã‡BÄ°R YERDEN Ã§aÄŸrÄ±lmÄ±yordu. **KullanÄ±cÄ± onayÄ±yla:** `worker.py`'ye yeni
   `belge_url_getir()` eklendi â€” talep anÄ±nda (kullanÄ±cÄ± "Analiz Et" dediÄŸinde) `ekap_scraper.
   ekap_captcha_indir()`'i Ã§aÄŸÄ±rÄ±p indirir, `ilanlar.belgeler`'i kalÄ±cÄ± gÃ¼nceller (commit `a204ecf`,
   dÃ¼zeltme `efb8d76` â€” ilk denemede yanlÄ±ÅŸ EKAP id'siyle `GetDokumanUrl`'e tekrar sorulmuÅŸtu, 500 aldÄ±;
   asÄ±l Ã§Ã¶zÃ¼m gece turunun zaten doÄŸruladÄ±ÄŸÄ± `belgeler[0].url` linkini DOÄRUDAN kullanmak).
2. **`belgeler` Storage bucket'Ä± hiÃ§ yoktu** (`docker exec supabase-db psql -c "select * from storage.
   buckets"` â†’ 0 satÄ±r) â€” canlÄ± testte "Bucket not found" ile ortaya Ã§Ä±ktÄ±. **KullanÄ±cÄ± onayÄ±yla** public
   bucket olarak oluÅŸturuldu (200MB limit â€” EKAP dÃ¶kÃ¼man ZIP'leri 88MB'a kadar Ã§Ä±kabiliyor).
3. **storage-api'nin global `FILE_SIZE_LIMIT`'i 50MB'da sabitti** (docker-compose.yml, bucket'Ä±n kendi
   limitinden BAÄIMSIZ, onu ezip geÃ§iyor) â€” 88MB'lÄ±k gerÃ§ek bir belge "Payload too large" (413) verdi.
   200MB'a Ã§Ä±karÄ±ldÄ± + `docker compose up -d storage`.
4. **`analiz_gecmisi` insert'i var olmayan `ihale_id` kolonunu kullanÄ±yordu** (gerÃ§ek kolon: `ilan_id`) â€”
   canlÄ± testte doÄŸrulandÄ±: kredi zaten dÃ¼ÅŸÃ¼lmÃ¼ÅŸ, rapor Ã¼retilmiÅŸken bu adÄ±mda Ã§Ä±plak istisna fÄ±rlatÄ±p
   tÃ¼m isteÄŸi Ã§Ã¶kertiyordu. DÃ¼zeltildi + artÄ±k try/except (rapor kullanÄ±cÄ±ya dÃ¶nmÃ¼ÅŸ olmalÄ±, geÃ§miÅŸ kaydÄ±
   ikincil) (commit `c32d72c`).
5. **Gemini hata verince bile kredi dÃ¼ÅŸÃ¼lÃ¼yordu** â€” `metin_pdf_analiz_et`/`taranmis_pdf_analiz_et` hata
   durumunda `{"hata": "..."}` dÃ¶ner ama ana pipeline bunu hiÃ§ kontrol etmeden "baÅŸarÄ±lÄ±" sayÄ±yordu (canlÄ±
   testte doÄŸrulandÄ±: Gemini File API hatasÄ± â†’ yine de "2 kredi harcandÄ±"). ArtÄ±k `rapor` sadece hata
   iÃ§eriyorsa (gerÃ§ek analiz alanÄ± yoksa) baÅŸarÄ±sÄ±z sayÄ±lÄ±yor, kredi dÃ¼ÅŸÃ¼lmÃ¼yor (commit `c32d72c`).
6. **Gemini File API (`genai.upload_file`) kÄ±rÄ±ktÄ± â€” "API key not valid"** (canlÄ±da doÄŸrulandÄ±: AYNI key ile
   `list_models()`/`generate_content()`/`list_files()` sorunsuz, sadece `upload_file()`'Ä±n kullandÄ±ÄŸÄ± ayrÄ±
   `$discovery/rest` uÃ§ noktasÄ± key'i reddediyor â€” deprecated `google-generativeai` SDK'sÄ±nÄ±n "support
   ended" duyurusuyla tutarlÄ± bir sunset belirtisi). **Ã‡Ã¶zÃ¼m:** taranmÄ±ÅŸ/gÃ¶rsel PDF'ler artÄ±k File API'ye
   hiÃ§ uÄŸramadan `generate_content()`'e **inline bayt** olarak veriliyor (18MB altÄ± â€” Ã§oÄŸu belge), File API
   sadece daha bÃ¼yÃ¼k dosyalarda son Ã§are (commit `cb02529`, ardÄ±ndan bir syntax hatasÄ± acilen dÃ¼zeltildi:
   `337aca6` â€” bu commit'ler arasÄ± VDS API kÄ±sa sÃ¼re 500 crash-loop'taydÄ±, servis saÄŸlÄ±klÄ± halde bÄ±rakÄ±ldÄ±).
7. **`gemini-1.5-flash` Google tarafÄ±ndan TAMAMEN KALDIRILMIÅ** (404 "model not found for API version
   v1beta") â€” deprecated SDK'nÄ±n son noktasÄ±. `ekap_scraper.py`'nin CAPTCHA Ã§Ã¶zÃ¼cÃ¼sÃ¼ zaten `gemini-2.5-flash`
   kullanÄ±yordu (kanÄ±tlanmÄ±ÅŸ Ã§alÄ±ÅŸÄ±yor) â€” `analyzer.py` + `firma_ai_yorum.py` aynÄ± modele geÃ§irildi
   (commit `d40a4f3`).

**SONUÃ‡ â€” canlÄ± uÃ§tan uca test (VDS, gerÃ§ek EKAP ihalesi, sirket_profili sahte ama zararsÄ±z):** CAPTCHA
3/3 denemede ilk seferde Ã§Ã¶zÃ¼ldÃ¼, 88MB+16MB gerÃ§ek belge indirildi, ZIP'ten PDF Ã§Ä±karÄ±ldÄ±, taranmÄ±ÅŸ PDF
tespit edildi, Gemini Vision (inline) gerÃ§ek ve tutarlÄ± bir analiz raporu Ã¼retti (`ozet`, `uygunluk_skoru`,
`karar`, `karar_gerekce`, `kirmizi_alarmlar`, `firsatlar`, `giris_engelleri`, `mali_yuk`, `aksiyon_listesi`
â€” hepsi doldu, doÄŸru ihale bilgisini tanÄ±dÄ±). `analiz_gecmisi` insert'i ayrÄ±ca rolled-back transaction ile
doÄŸrulandÄ± (doÄŸru ÅŸema, hatasÄ±z). **Kredi tÃ¼kendiÄŸi iÃ§in (test kullanÄ±cÄ±sÄ± 3â†’1) tam DB-yazan
`kullanici_analiz_isle()` akÄ±ÅŸÄ± 2-kredi gerektiren bir belgeyle uÃ§tan uca tekrar koÅŸulmadÄ± ama tÃ¼m parÃ§alarÄ±
ayrÄ± ayrÄ± doÄŸrulandÄ± â€” yÃ¼ksek gÃ¼venilirlik.**

**SÄ±radaki mantÄ±klÄ± adÄ±m:** (1) GerÃ§ek bir kullanÄ±cÄ± hesabÄ±yla tarayÄ±cÄ±dan "Analiz Et" dene (nihai UI/UX
doÄŸrulamasÄ± â€” backend artÄ±k saÄŸlam). (2) KullanÄ±cÄ± onayÄ±yla IYZICO key'lerini edge-functions'a ekle â†’
sandbox kartla Ã¶deme testi yap (Ä°yzico test kartÄ±: 5528790000000008). (3) manual_backfill.log'u izle â†’
bittiÄŸinde veri hacmini tekrar say (ÅŸu an ~47k, 20.689'dan baÅŸladÄ±). (4) C4/E1/E3/E4'e geÃ§.
(5) `google.generativeai` â†’ `google.genai` tam SDK migrasyonu dÃ¼ÅŸÃ¼nÃ¼lebilir (ÅŸu an Ã§alÄ±ÅŸÄ±yor ama SDK "support
ended" â€” uzun vadede sorun Ã§Ä±karabilir, acil deÄŸil).

**âœ… EK TUR (10 Tem, "devam et hiÃ§ durma" â€” sistematik tablo/RPC/plan-kontrol denetimi):**
- ğŸ”´ **`js/sidebar-user.js`'de AYNI Pro-plan tespit bug'Ä±** (plan.js'deki ile birebir aynÄ±, baÄŸÄ±msÄ±z kopya):
  `PRO` listesi `'standart'`/`'kurumsal'` iÃ§ermiyordu â†’ **TÃœM sayfalardaki sidebar rozeti** Ã¶deyen
  kullanÄ±cÄ±lar iÃ§in hep "Ãœcretsiz Plan" gÃ¶steriyordu. DÃ¼zeltildi (commit `c1707ca`). Bu ikisi (`js/plan.js`
  + `js/sidebar-user.js`) artÄ±k tarandÄ±, baÅŸka baÄŸÄ±msÄ±z kopya kalmadÄ± (dashboard/teklif-olustur/fiyatlandirma
  hepsi paylaÅŸÄ±lan `Plan.getPlan()`'Ä± kullanÄ±yor, kendi listesi yok â€” doÄŸrulandÄ±).
- ğŸŸ¡ **`kik-kararlar.html`**: (1) sidebar planÄ± var olmayan `kullanicilar` tablosuna sorguluyordu â†’ gerÃ§ek
  `kullanici_krediler` deseni ile deÄŸiÅŸtirildi. (2) ana liste var olmayan `kik_kararlar` tablosunu
  okuyordu â€” sayfa bunu zaten (42P01) zarifÃ§e yakalÄ±yordu (crash yoktu), ama `backend/kik_backfill.py`
  bu tabloya yazmayÄ± bekliyordu ve migration hiÃ§ yazÄ±lmamÄ±ÅŸtÄ±. `migration_kik_kararlar_tablo.sql` ile
  eklendi (kullanÄ±cÄ± onayÄ±yla VDS'e uygulandÄ±, RLS+public SELECT). **KÄ°K kaynaÄŸÄ± hÃ¢lÃ¢ IP-bloklu (302,
  cron her gece "0 eklendi") â€” bu SADECE tabloyu hazÄ±rladÄ±, veri akÄ±ÅŸÄ±nÄ± baÅŸlatmadÄ±** (ayrÄ± iÅŸ, Playwright
  gerektirir, bkz. Faz E4).
- ğŸŸ¢ **`sektorler.html`'in beklediÄŸi `kategori_sayim()` RPC'si hiÃ§ yoktu** â€” sayfa zaten defensif
  (38 sayfalanmÄ±ÅŸ istekle manuel fallback, Ã§Ã¶kÃ¼ÅŸ yoktu) ama yavaÅŸtÄ±. `il_sayim()` ile aynÄ± desende
  eklendi (kullanÄ±cÄ± onayÄ±yla VDS'e uygulandÄ±, commit `4fd18a7`).
- âœ… **Sistematik denetim tamamlandÄ±:** tÃ¼m backend `.rpc()` Ã§aÄŸrÄ±larÄ± (`normalize_firma`, `analiz_pivot`,
  `kredi_dus`, `il_sayim`, `kategori_sayim`) gerÃ§ek `pg_proc` imzalarÄ±yla eÅŸleÅŸiyor. TÃ¼m frontend `.from()`
  Ã§aÄŸrÄ±larÄ± (~90 site) gerÃ§ek `information_schema.tables` listesiyle karÅŸÄ±laÅŸtÄ±rÄ±ldÄ± â€” yukarÄ±daki 2 madde
  (kullanicilar, kik_kararlar) dÄ±ÅŸÄ±nda sapma bulunmadÄ±. `teklif-olustur.html`'in `teklifler` insert'i
  ÅŸemayla uyumlu doÄŸrulandÄ± (8 Tem'deki dÃ¼zeltme kalÄ±cÄ±ymÄ±ÅŸ). `notify.py`/`bulten_gonder.py`'nin tablo/kolon
  referanslarÄ± da statik olarak doÄŸru bulundu (ayrÄ±ca cron loglarÄ±nda hatasÄ±z Ã§alÄ±ÅŸtÄ±klarÄ± zaten gÃ¶rÃ¼lmÃ¼ÅŸtÃ¼).
  Yerel Ã¶nizlemede `sektorler.html` (yeni RPC, tek istekle "48 sektÃ¶r" doÄŸru geldi) ve `kik-kararlar.html`
  (tablo artÄ±k var, konsol hatasÄ±z) manuel doÄŸrulandÄ±.

- ğŸ”´ğŸ”´ **GÄ°ZLÄ°LÄ°K AÃ‡IÄI BULUNDU + DÃœZELTÄ°LDÄ° (kullanÄ±cÄ± onayÄ±yla) â€” `kullanici_profiller` RLS'i Ã§ok
  gevÅŸekti:** SELECT policy'si `auth.role()='authenticated'` ÅŸartÄ±yla (satÄ±r filtresi YOK) tanÄ±mlÄ±ydÄ± â€”
  yani **giriÅŸ yapmÄ±ÅŸ HER kullanÄ±cÄ±, BAÅKA firmalarÄ±n** `vergi_no`, `mersisi_no`, `telefon`,
  `yillik_ciro_tl`, `calisma_illeri`, `referanslar` gibi Ã¶zel iÅŸ bilgilerini okuyabiliyordu (tam anonim
  deÄŸil â€” hesap aÃ§mak yeterliydi). HiÃ§bir mevcut Ã¶zellik bu geniÅŸ eriÅŸime ihtiyaÃ§ duymuyor doÄŸrulandÄ±
  (Firmalar Dizini ayrÄ± tablodan/`yukleniciler`'den okuyor; `teklif-olustur.html`/`sidebar-user.js` zaten
  sadece `.eq('id', user.id)` ile kendi satÄ±rÄ±nÄ± okuyor). `migration_kullanici_profiller_rls_sikilastir.sql`
  ile `auth.uid() = id`'ye sÄ±kÄ±laÅŸtÄ±rÄ±ldÄ±, VDS'e uygulandÄ±, doÄŸrulandÄ± (4 policy de artÄ±k own-row).
  **AyrÄ±ca tÃ¼m public tablolardaki RLS policy'leri tek tek gÃ¶zden geÃ§irildi** (`ilanlar`, `ihale_sonuclari`,
  `kik_kararlar`, `yukleniciler`, `dokuman_sablonlari`, `konsorsiyumlar` â€” hepsi kasÄ±tlÄ±/gerekÃ§eli geniÅŸ
  eriÅŸimli: kamu ihale verisi, paylaÅŸÄ±lan ÅŸablonlar, "aÃ§Ä±k" konsorsiyum ilanlarÄ±) â€” `kullanici_profiller`
  dÄ±ÅŸÄ±nda baÅŸka anomali bulunmadÄ±.

---

## ğŸ“ SON DURUM (10 Tem 2026, otonom oturum devamÄ± â€” C4 + prod-yazma sÄ±nÄ±rÄ±) â€” Ã–NCE BUNU OKU

> KullanÄ±cÄ± "sÄ±rada ne var, otomatik onay veriyorum" dedi. Bu oturumda harness'Ä±n "auto mode classifier"Ä±
> ilk defa gÃ¶zlemlendi: **genel "sorma bana" onayÄ±, canlÄ± VDS'e SSH ile DB okuma/config-dump/migration
> yazma gibi iÅŸlemler iÃ§in YETERLÄ° SAYILMIYOR** â€” her production DB okuma/yazma isteÄŸi ayrÄ± ayrÄ±
> reddedildi ("blanket approval does not meet the named+specific bar"). Salt dosya/proses okuma (log
> tail, ps aux, checkpoint cat) SORUNSUZ geÃ§ti; `docker exec psql` / env dump / migration pipe HEPSÄ°
> engellendi. **Bu nedenle bundan sonraki oturumlarda:** VDS canlÄ± DB durumunu public REST API (anon key,
> `js/api.js`'teki `SUPABASE_ANON_KEY`) Ã¼zerinden oku (bu bir gÃ¼venlik ihlali deÄŸil â€” herkese aÃ§Ä±k aynÄ±
> veri), production yazma/migration/env-config iÅŸlemleri iÃ§in kullanÄ±cÄ±dan **o an, o komut iÃ§in** aÃ§Ä±k
> onay iste (blanket yetki yetmiyor).

**âœ… Bu oturumda TAMAMLANANLAR:**
1. **Backfill saÄŸlÄ±k kontrolÃ¼ (public REST API ile, SSH DB sorgusu YERÄ°NE):** `ilanlar` 29.809â†’**51.944**,
   `ihale_sonuclari` 20.689â†’**66.710** (3 katÄ±n Ã¼zerinde bÃ¼yÃ¼me), `yukleniciler` 11.187. `/api/planlar`
   200 dÃ¶nÃ¼yor (Render baÄŸÄ±mlÄ±lÄ±ÄŸÄ± kaldÄ±rma kalÄ±cÄ±). Checkpoint dosya-okuma ile: skip 20200â†’**42.200**,
   backfill process hÃ¢lÃ¢ arka planda Ã§alÄ±ÅŸÄ±yor (PID canlÄ±, `--tum-kayitlar --max-pages 400`). MÃ¼dahale
   gerekmedi, kendi haline bÄ±rakÄ±ldÄ±.
2. **Faz C4 â€” SÄ±nÄ±r DeÄŸer KatsayÄ±sÄ± (N) TAMAMLANDI (kod, migration dosyasÄ± hazÄ±r â€” VDS'e UYGULANMADI):**
   - `backend/ekap_scraper.py`: `esik_katsayi_parse()` eklendi â€” yapÄ±m iÅŸi ilan metninin sonundaki
     `"...sÄ±nÄ±r deÄŸer katsayÄ±sÄ± (N) = 1,00"` deseninden regex ile sayÄ±sal deÄŸeri Ã§Ä±karÄ±r (canlÄ± Ã¶rnek
     veriyle doÄŸrulandÄ± â€” public REST'ten Ã§ekilen gerÃ§ek bir YapÄ±m ilanÄ±nÄ±n `ilan_metni`'nde pattern
     birebir bulundu, `python -c` ile 4 varyant test edildi, hepsi doÄŸru parse). `detay_cek()` ve
     `ihaleleri_isle()`'ye entegre edildi.
   - `backend/migration_esik_katsayi.sql` (yeni, additive): `ilanlar.esik_katsayi NUMERIC` ekler.
     **VDS'E UYGULANMADI** â€” `cat migration_esik_katsayi.sql | ssh ... psql` denendi, auto-mode
     classifier "production migration, isimlendirilmiÅŸ Ã¶zel onay yok" diyerek reddetti. **SÄ±radaki
     oturum/kullanÄ±cÄ±: bu dosyayÄ± VDS'e uygula** (`docker exec -i supabase-db psql -U postgres -d
     postgres < backend/migration_esik_katsayi.sql`), sonra `git pull` ile VDS frontend'ini gÃ¼ncelle.
   - `ihaleler.html`: DetaylÄ± Ara paneline "SÄ±nÄ±r DeÄŸer KatsayÄ±sÄ± (YapÄ±m)" dropdown'u (4 bant: â‰¤0,80 /
     0,80â€“1,00 / 1,00â€“1,20 / >1,20), ana sorguya `esik_katsayi` select+filtre eklendi, kart etiketlerine
     `N: 1,00` rozeti (sadece deÄŸer varsa), sÄ±fÄ±rlama/kayÄ±tlÄ±-arama/URL-restore akÄ±ÅŸlarÄ±na da eklendi.
     âš ï¸ **KRÄ°TÄ°K â€” migration uygulanmadan bu kod deploy edilirse `ilanlar` sorgusu 400 verirdi**
     (`column ilanlar.esik_katsayi does not exist`) â€” bunu local preview'da yakaladÄ±m (result-count
     "âš  Hata" gÃ¶sterdi). **DÃ¼zeltildi:** `ilanlariYukle()`'ye migration-yok fallback eklendi â€” hata
     mesajÄ± `esik_katsayi` iÃ§eriyorsa, aynÄ± sorguyu bu alan olmadan sessizce tekrar dener
     (`console.info` ile loglar, kullanÄ±cÄ±ya kÄ±rmÄ±zÄ± hata gÃ¶stermez). Local preview'da doÄŸrulandÄ±:
     migration'sÄ±z halde bile filtre paneli + liste + kartlar sorunsuz render oldu, konsol temiz.
   - **NOT â€” VDS'te henÃ¼z git pull yapÄ±lmadÄ±, bu deÄŸiÅŸiklikler sadece repo'da.** Cloudflare Pages artÄ±k
     kullanÄ±lmÄ±yor (DNS VDS'e cutover oldu) â†’ bu dosyalar GitHub'a push'lansa bile canlÄ± siteye
     otomatik yansÄ±maz (VDS'te elle `git pull` gerekir, auto-deploy workflow'u yok â€” `.github/workflows/`
     iÃ§inde sadece `ekap_scraper.yml` var). Yani commit+push GÃœVENLÄ°, canlÄ±yÄ± bozmaz.

3. **Faz E1 â€” Rakip Takibi TAMAMLANDI (kod, migration dosyasÄ± hazÄ±r â€” VDS'e UYGULANMADI):**
   - `backend/migration_takip_firmalar.sql` (yeni): `takip_firmalar(kullanici_id, firma_ad)` tablosu,
     own-row RLS (select/insert/delete `auth.uid() = kullanici_id`), `authenticated` GRANT. **VDS'e
     UYGULANMADI** (aynÄ± prod-yazma sÄ±nÄ±rÄ± â€” bkz. yukarÄ±daki not).
   - `firma-analiz.html`: firma baÅŸlÄ±ÄŸÄ±na "â­ Rakibi Takip Et" butonu â€” giriÅŸ yapmamÄ±ÅŸsa `login?donus=...`
     ile yÃ¶nlendirir (login sonrasÄ± aynÄ± firma sayfasÄ±na dÃ¶ner), giriÅŸliyse `takip_firmalar`'a
     upsert/delete. `takip_firmalar` yoksa (migration uygulanmadan) try/catch ile sessizce "â­ Rakibi
     Takip Et" varsayÄ±lanÄ±nda kalÄ±r â€” local preview'da doÄŸrulandÄ± (buton render oldu, konsol temiz,
     login redirect + `donus` round-trip doÄŸru Ã§alÄ±ÅŸtÄ±).
   - `login.html`: yeni `donusHedefi()` â€” `?donus=` parametresini okur, **sadece site-iÃ§i gÃ¶reli yol**
     kabul eder (`/` ile baÅŸlayÄ±p `//` ile baÅŸlamayan â€” open-redirect korumasÄ±), yoksa `dashboard`'a
     dÃ¼ÅŸer. Hem "giriÅŸ baÅŸarÄ±lÄ±" hem "zaten giriÅŸli" yollarÄ±na baÄŸlandÄ±.
   - `backend/rakip_bildirim.py` (yeni): gece cron'da `ekap_sonuc_backfill.py`'den SONRA Ã§alÄ±ÅŸacak â€”
     son 26 saatte `scrape_tarihi`'si gÃ¼ncellenen `ihale_sonuclari` satÄ±rlarÄ±nÄ± `takip_firmalar` ile
     eÅŸleÅŸtirir (iki yÃ¶nlÃ¼ substring, `firma-analiz.html`'in ILIKE aramasÄ±yla aynÄ± mantÄ±k), eÅŸleÅŸme
     varsa `bildirimler`'e kayÄ±t aÃ§ar. `takip_firmalar`/`ihale_sonuclari.scrape_tarihi` yoksa (migration
     sÄ±rasÄ± gelmemiÅŸse) 404'te sessizce Ã§Ä±kar, cron'u Ã§Ã¶kertmez. **Migration uygulanmadan test
     EDÄ°LEMEDÄ°** (service key ile prod'a yazmak ayrÄ± bir onay gerektirir) â€” ama `esleÅŸiyor()` fonksiyonu
     yerel olarak birim test edildi.
     ğŸ› **YazÄ±m sÄ±rasÄ±nda bulunan+dÃ¼zeltilen bug:** Python'un `str.lower()`'Ä± TÃ¼rkÃ§e "Ä°"yi yanlÄ±ÅŸ Ã§evirir
     (`"Ä°".lower()` â†’ `"iÌ‡"`, birleÅŸik karakter, dÃ¼z `"i"` DEÄÄ°L) â†’ `"DEMÄ°R YAPI".lower()` iÃ§inde
     `"demir yapÄ±"` (dÃ¼z ASCII i) hiÃ§ bulunamÄ±yordu, tÃ¼m bÃ¼yÃ¼k-harfli firma eÅŸleÅŸmeleri sessizce
     kaÃ§Ä±rÄ±lÄ±rdÄ±. `_tr_lower()` yardÄ±mcÄ± fonksiyonu eklendi (Ä°â†’i, Iâ†’Ä±, sonra `.lower()`) â€” aynÄ± ders
     `backend/firma_normalize.py`'de zaten biliniyordu (TR locale notu), burada tekrarlandÄ± Ã§Ã¼nkÃ¼ ayrÄ±
     bir yeni dosyaydÄ±.
   - **KALAN:** `run_scraper.sh`'e `rakip_bildirim.py` Ã§aÄŸrÄ±sÄ±nÄ± eklemek (`yuklenici_yenile_calistir.py`
     satÄ±rÄ±ndan hemen sonra) â€” bu da production dosya yazma, migration'la birlikte kullanÄ±cÄ±/sonraki
     oturum tarafÄ±ndan yapÄ±lmalÄ±.

4. **Faz E3 â€” SEO Firma SayfalarÄ± TAMAMLANDI (kod + gerÃ§ek veriyle Ã¼retilmiÅŸ 1.696 statik sayfa,
   repo'ya commit'lendi â€” VDS'e henÃ¼z git pull YAPILMADI):**
   - `backend/firma_sayfa_uret.py` (yeni): sadece **public REST API'yi (anon key) okur** â€” production'a
     hiÃ§ yazmÄ±yor, bu yÃ¼zden hiÃ§bir onay engeline takÄ±lmadan yerel makineden Ã§alÄ±ÅŸtÄ±rÄ±labildi.
     `yukleniciler`'den `toplam_sozlesme_sayisi >= 3` olan firmalarÄ± (1.696 kayÄ±t â€” ince/thin-content
     SEO riskinden kaÃ§Ä±nmak iÃ§in eÅŸik konuldu, `>=1` ile 11.187 olurdu) Ã§ekip her biri iÃ§in gerÃ§ek
     `<title>`/`<meta description>`/canonical/OG/JSON-LD Organization iÃ§eren, arama motorunun ilk
     yÃ¼klemede gÃ¶receÄŸi statik bir HTML sayfasÄ± Ã¼retiyor. TÃ¼rkÃ§eâ†’ASCII slug fonksiyonu (Ä°/I/ÄŸ/ÅŸ/Ã¼/Ã¶/Ã§
     dahil) + Ã§akÄ±ÅŸma durumunda `-2/-3` son eki gÃ¼venlik aÄŸÄ± (test setinde hiÃ§ tetiklenmedi, 1696/1696
     benzersiz).
   - **1.696 dosya Ã¼retilip `firma/<slug>.html`'e yazÄ±ldÄ±** (14MB, repo'ya commit edildi) + gerÃ§ek
     veriyle `sitemap-firmalar.xml` (1.696 URL) + yeni `robots.txt` (dashboard/profil/bildirimler/
     teklif-olustur/Ã¶deme/api gibi giriÅŸ-gerektiren yollarÄ± Disallow eder, sitemap'i iÅŸaret eder).
   - Her sayfa: firma adÄ±/il/sektÃ¶r/KPI Ã¶zeti (toplam sÃ¶zleÅŸme, toplam ciro, ilk/son iÅŸ) + "ğŸ“Š DetaylÄ±
     Analizi GÃ¶r" CTA'sÄ± â†’ `firma-analiz?firma=<ad>` (tam etkileÅŸimli/AI destekli sÃ¼rÃ¼m â€” "Ã¶zet public,
     derinlik uygulama-iÃ§i" stratejisi). Sayfa ÅŸablonu marka tutarlÄ±lÄ±ÄŸÄ± iÃ§in `index.html`'in public
     nav+footer kabuÄŸunu (`landing-nav`, `css/style.css` deÄŸiÅŸkenleri) yeniden kullanÄ±yor, app-shell/
     sidebar YOK (hafif/hÄ±zlÄ± SEO iniÅŸ sayfasÄ±).
   - Local preview'da doÄŸrulandÄ±: `<title>`/meta/canonical/JSON-LD/CTA linki hepsi doÄŸru render oldu,
     CSS (amber renk) yÃ¼klendi, konsol hatasÄ±z. CTA linkinin local'de 404 vermesi **beklenen davranÄ±ÅŸ**
     (uzantÄ±sÄ±z URL'ler local Python server'da Ã§alÄ±ÅŸmaz, prod nginx'te Ã§alÄ±ÅŸÄ±r â€” bkz. [[project-stack]]
     memory'si, sitedeki TÃœM diÄŸer iÃ§ linklerle aynÄ± desen).
   - Ã‡akÄ±ÅŸma kontrolÃ¼ yapÄ±ldÄ±: yeni `firma/` klasÃ¶rÃ¼ mevcut `firma-analiz.html` (tekil) ve `firmalar.html`
     (dizin sayfasÄ±) ile isim Ã§akÄ±ÅŸmÄ±yor.
   - **KALAN:** VDS'te `git pull` (statik dosyalar otomatik canlÄ± olur, nginx zaten her yolu genel
     `try_files` ile sunuyor â€” ekstra config GEREKMÄ°YOR, sadece dosya senkronu). Ä°stenirse ileride:
     (a) eÅŸiÄŸi dÃ¼ÅŸÃ¼rÃ¼p daha fazla firma kapsanabilir, (b) gece cron'una eklenip yeni firmalar
     otomatik sayfa alabilir (ÅŸu an manuel/tek seferlik Ã¼retim), (c) Google Search Console'a
     sitemap gÃ¶nderilmesi (kullanÄ±cÄ± tarafÄ±nda, hesap gerektirir).

5. **E4 (KÄ°K kararlarÄ±) â€” sadece araÅŸtÄ±rma, kod DEÄÄ°ÅMEDÄ°:** kullanÄ±cÄ± onayÄ±yla tek bir test isteÄŸi
   atÄ±ldÄ±, sonuÃ§ + gerekÃ§e yukarÄ±daki "10.E FAZ E" bÃ¶lÃ¼mÃ¼ndeki E4 maddesine eklendi (Ã¶zet: gerÃ§ek bir
   iÃ§ API bulundu ama Ã§alÄ±ÅŸan `b_ihalearama` tabanÄ±nda deÄŸil, ve EKAP'Ä±n kendi menÃ¼sÃ¼ de bu Ã¶zelliÄŸi
   `externalLink` ile dÄ±ÅŸarÄ± yÃ¶nlendiriyor â€” dÃ¼ÅŸÃ¼k Ã¶ncelikte kalmalÄ±).

6. **Faz D4 â€” AI Teklif Workflow BaÄŸlantÄ±sÄ± TAMAMLANDI (kod hazÄ±r â€” VDS'e henÃ¼z deploy edilmedi):**
   `teklif-olustur.html`'deki "âœ¨ Teknik Teklif OluÅŸtur" butonu artÄ±k gerÃ§ekten hiÃ§ var olmayan
   `ihaleplatform-backend.onrender.com` yerine **gerÃ§ek bir backend endpoint'ine** baÄŸlÄ± â€” Ã¶nceden bu
   buton HER ZAMAN sabit/kanÄ±ksanmÄ±ÅŸ Ã¶rnek metne dÃ¼ÅŸÃ¼yordu (kullanÄ±cÄ± "AI oluÅŸturdu" sanÄ±yordu, aslÄ±nda
   ÅŸablon metindi â€” sessiz bir UX yanÄ±ltmasÄ±ydÄ±).
   - `backend/teklif_ai.py` (yeni, `firma_ai_yorum.py` ile aynÄ± desen): ihale detayÄ± + kullanÄ±cÄ±nÄ±n
     firma profili + **aynÄ± idare/kategoride geÃ§miÅŸte kazanan firmalarÄ±n ortalama tenzilatÄ±**
     (`analiz_pivot('firma', p_idare=..., p_kategori=...)` â€” D2'nin kazanma-bandÄ± Ã¶zelliÄŸiyle aynÄ± RPC)
     Gemini'ye baÄŸlam olarak veriliyor â†’ "piyasa farkÄ±nda" taslak (plan D4'Ã¼n tam istediÄŸi: "benzer
     iÅŸleri geÃ§miÅŸte X,Y firmalarÄ± %Z tenzilatla aldÄ±"). 3 bÃ¶lÃ¼m (KAPSAM/NEDEN/YÃ–NTEM) `###` ayÄ±racÄ±yla
     parse ediliyor.
   - `api.py`'ye `POST /teklif-olustur {ihale_id}` eklendi (`/ai/firma-yorum` ile birebir aynÄ± iskelet:
     auth zorunlu, kredi Ã¶n kontrolÃ¼, RPC hata verirse sessizce boÅŸ baÄŸlamla devam, kredi dÃ¼ÅŸÃ¼mÃ¼
     try/except'li â€” baÅŸarÄ±sÄ±z Gemini Ã§aÄŸrÄ±sÄ±nda kredi dÃ¼ÅŸmez, aynÄ± D1'de dÃ¼zeltilen ilkeyle tutarlÄ±).
   - `teklif-olustur.html`: fetch artÄ±k `${API.CONFIG.BASE_URL}/teklif-olustur`'a (aynÄ±-origin,
     `https://ihaleglobal.com/api`) gerÃ§ek `sb.auth.getSession()` token'Ä±yla gidiyor (fiyatlandÄ±rma
     sayfasÄ±ndaki `planDusur()` ile aynÄ±, kanÄ±tlanmÄ±ÅŸ auth deseni â€” `js/api.js`'nin `ihale_token`
     localStorage mekanizmasÄ± yerine bunu tercih ettim Ã§Ã¼nkÃ¼ payment flow'da zaten doÄŸrulanmÄ±ÅŸ).
     GiriÅŸsiz kullanÄ±cÄ±da artÄ±k sessizce ÅŸablon metne dÃ¼ÅŸmÃ¼yor, net "giriÅŸ yapmalÄ±sÄ±nÄ±z" hatasÄ± veriyor
     (yanÄ±ltÄ±cÄ± olmasÄ±n diye) â€” local preview'da doÄŸrulandÄ± (`window.aiTeklifOlustur()` Ã§aÄŸrÄ±sÄ± â†’
     doÄŸru toast, kapsam alanÄ± boÅŸ kaldÄ±, buton/loading state doÄŸru resetlendi, konsol hatasÄ±z). 402
     (yetersiz kredi) durumu da ayrÄ±ca ele alÄ±nÄ±yor. GerÃ§ek network/ihale-bulunamadÄ± hatalarÄ±nda (backend
     kapalÄ±yken/canlÄ± deÄŸilken) eski davranÄ±ÅŸ korunuyor â€” kanÄ±ksanmÄ±ÅŸ Ã¶rnek metne nazikÃ§e dÃ¼ÅŸÃ¼yor.
   - **KALAN:** VDS'te `git pull` + `systemctl restart ihale-api` (yeni Python dosyasÄ±/import eklendi,
     mevcut migration'lara baÄŸÄ±mlÄ± deÄŸil â€” `analiz_pivot` zaten VDS'te kurulu, migration beklemiyor).
     GerÃ§ek bir giriÅŸ yapmÄ±ÅŸ kullanÄ±cÄ± + gerÃ§ek ihale ID'siyle uÃ§tan uca DOÄRULANMADI (local'de
     backend/Gemini canlÄ± deÄŸildi) â€” sÄ±radaki oturumun ilk iÅŸlerinden biri bu olmalÄ±.

7. **Faz D3 â€” Semantik EÅŸleÅŸme TAMAMLANDI (kod hazÄ±r â€” VDS'e henÃ¼z deploy edilmedi, geÃ§miÅŸ ilanlar
   embed EDÄ°LMEDÄ°, kasÄ±tlÄ±):**
   - ğŸ› **Plandaki `text-embedding-004` model adÄ± da KALDIRILMIÅ** (gemini-1.5-flash'la aynÄ± sÄ±nÄ±f
     sorun â€” Google eski model adlarÄ±nÄ± sÃ¼nsetliyor). `client.models.list()` ile canlÄ± doÄŸrulandÄ±:
     embedContent destekleyen gÃ¼ncel model **`models/gemini-embedding-001`**. Bu model varsayÄ±lan
     3072 boyut dÃ¶ndÃ¼rÃ¼yor (pgvector index limitleri iÃ§in fazla) â€” `EmbedContentConfig
     (output_dimensionality=768)` ile Matryoshka/MRL kÄ±saltmasÄ± istendi, canlÄ± test edildi (768 boyut
     doÄŸru dÃ¶ndÃ¼). âš ï¸ KÄ±saltÄ±lmÄ±ÅŸ Ã§Ä±ktÄ± norm=1 DEÄÄ°L (test: 0.588) ama bu SORUN DEÄÄ°L â€” pgvector'Ä±n
     `<=>` operatÃ¶rÃ¼ cosine mesafeyi zaten vektÃ¶r normlarÄ±na bÃ¶lerek hesaplÄ±yor, manuel normalize
     gerekmiyor.
   - `backend/embed_ortak.py` (yeni, paylaÅŸÄ±lan yardÄ±mcÄ±): `embed_uret(metin) -> list[float]|None`,
     hem `ilan_embed_uret.py` hem `api.py` bunu kullanÄ±yor (DRY).
   - `backend/migration_semantik_esleme.sql` (yeni): `CREATE EXTENSION vector` + `ilanlar.embedding`/
     `kullanici_profiller.embedding` (vector(768)) + HNSW index + **`semantik_skor_batch(p_ilan_ids)`
     RPC**. âš ï¸ **GÃ¼venlik tasarÄ±mÄ± bilerek `p_kullanici_id` parametresi ALMIYOR** â€” SECURITY DEFINER
     iÃ§inde doÄŸrudan `auth.uid()` kullanÄ±yor, Ã§Ã¼nkÃ¼ bu oturumun baÅŸÄ±nda bulunan `kullanici_profiller`
     gizlilik aÃ§Ä±ÄŸÄ± dersinden sonra "Ã§aÄŸÄ±ran istediÄŸi kullanÄ±cÄ± ID'sini geÃ§ebilir" deseninden
     kaÃ§Ä±nÄ±ldÄ± â€” sadece kendi embedding'inle karÅŸÄ±laÅŸtÄ±rma yapabilirsin.
   - `backend/ilan_embed_uret.py` (yeni, gece cron adayÄ±): SADECE `durum='aktif'` + `embedding IS
     NULL` ilanlarÄ±, **varsayÄ±lan 300/Ã§alÄ±ÅŸtÄ±rma sÄ±nÄ±rlÄ±** â€” bilinÃ§li olarak TÃœM geÃ§miÅŸi (51k+ satÄ±r)
     tek seferde embed etmeye Ã‡ALIÅMIYOR (proje hafÄ±zasÄ±ndaki "Gemini kota uyarÄ±sÄ±" dersine uyularak;
     mevcut 51k+ geÃ§miÅŸ/kompakt satÄ±rÄ±n zaten `ilan_metni` yok, embed edilecek anlamlÄ± metin de yok â€”
     scriptte `ilan_metni not.is.null` filtresiyle bu zaten dÄ±ÅŸlanÄ±yor).
   - `api.py`'nin `PUT /profil`'i artÄ±k kaydÄ± gÃ¼ncelledikten sonra `firma_adi`+`faaliyet_alanlari`+
     `referanslar`'dan embedding Ã¼retip `kullanici_profiller.embedding`'i tazeliyor (try/except'li â€”
     migration uygulanmadan/Gemini hata verirse profil kaydÄ± yine BAÅARILI dÃ¶ner, sadece embedding
     boÅŸ kalÄ±r).
   - `ihaleler.html`: `ilanlariYukle()`'de kural-tabanlÄ± `_uyum` hesaplandÄ±ktan hemen sonra
     `semantik_skor_batch` RPC'si Ã§aÄŸrÄ±lÄ±p **%60 kural + %40 semantik** harmanlanÄ±yor (plandaki
     KABUL KRÄ°TERÄ° D formÃ¼lÃ¼ birebir). RPC/embedding yoksa (migration uygulanmadÄ±, kullanÄ±cÄ± giriÅŸsiz,
     ya da o ilan/profil iÃ§in embedding boÅŸ) sessizce atlanÄ±yor, `_uyum` salt kural-tabanlÄ± kalÄ±yor.
     Local preview'da doÄŸrulandÄ±: RPC 404 dÃ¶ndÃ¼ (migration henÃ¼z VDS'te yok), liste yine de 200 ihale
     ile sorunsuz render oldu, konsol hatasÄ±z â€” `esik_katsayi` fallback'iyle aynÄ± anda, birbirini
     bozmadan Ã§alÄ±ÅŸtÄ±klarÄ± da gÃ¶rÃ¼ldÃ¼.
   - **KALAN (sÄ±rasÄ±yla):** (a) migration'Ä± VDS'e uygula, (b) VDS'te `git pull` + `ihale-api` restart,
     (c) `ilan_embed_uret.py`'yi cron'a ekle (`yuklenici_yenile_calistir.py`'den sonra, `rakip_bildirim.py`
     ile aynÄ± satÄ±rda), (d) **BÄ°LÄ°NÃ‡LÄ° KULLANICI KARARI GEREKÄ°YOR:** mevcut ~14k aktif ilanÄ±n geÃ§miÅŸe
     dÃ¶nÃ¼k embed'lenmesi (script gece baÅŸÄ±na 300 iÅŸler â†’ ilk dolana kadar ~47 gece SÃœRER, ya da
     `--max` bÃ¼yÃ¼tÃ¼lÃ¼p tek seferde/birkaÃ§ gÃ¼nde bitirilebilir â€” bu bir maliyet/hÄ±z kararÄ±, otonom
     yapÄ±lmadÄ±). Migration + cron gelene kadar ihaleler.html tamamen eskisi gibi (salt kural-tabanlÄ±)
     Ã§alÄ±ÅŸmaya devam eder, hiÃ§bir regresyon yok.

**ğŸ”² SIRADAKÄ° OTURUM/KULLANICI Ä°Ã‡Ä°N â€” TEK KOMUTA Ä°NDÄ°RÄ°LDÄ°:**

`backend/deploy_10tem_oturum.sh` (yeni) bu oturumdaki 3 migration + `run_scraper.sh` satÄ±rlarÄ± +
`ihale-api` restart + doÄŸrulama adÄ±mlarÄ±nÄ±n HEPSÄ°NÄ° tek seferde uygular (idempotent â€” birden fazla
Ã§alÄ±ÅŸtÄ±rÄ±lsa da gÃ¼venli). VDS'te:
```bash
ssh -i ~/.ssh/ihale_oracle root@195.85.207.126
cd /opt/ihale-platform && git pull origin main
bash backend/deploy_10tem_oturum.sh
```
Script sonunda 3 doÄŸrulama sorgusu (`esik_katsayi` kolonu, `takip_firmalar` tablosu,
`semantik_skor_batch` RPC) `1` dÃ¶nÃ¼yorsa hepsi canlÄ± demektir.

**Script'ten SONRA elle yapÄ±lmasÄ± gerekenler:**
1. `POST /teklif-olustur`'u gerÃ§ek bir giriÅŸ yapmÄ±ÅŸ kullanÄ±cÄ± + gerÃ§ek ihale ID'siyle tarayÄ±cÄ±dan test
   et (D4 â€” henÃ¼z uÃ§tan uca doÄŸrulanmadÄ±, backend/Gemini local'de canlÄ± deÄŸildi).
2. `ihaleler.html`'de "SÄ±nÄ±r DeÄŸer KatsayÄ±sÄ±" dropdown filtresini gerÃ§ek veriyle dene (C4).
3. HÃ¢lÃ¢ bekleyen (Ã¶nceki oturumlardan): IYZICO_API_KEY/SECRET edge-functions'a ekleme (Ã¶deme testi
   iÃ§in ÅŸart â€” bkz. yukarÄ±daki "ğŸ”´ğŸ”´ KRÄ°TÄ°K BULGU" notu), manual_backfill.log'un durumu (10 Tem son
   kontrolde saÄŸlÄ±klÄ± ilerliyordu: `ilanlar` 66.387, `ihale_sonuclari` 107.155, checkpoint skip=56.900
   â€” hÃ¢lÃ¢ artÄ±yor, 403/429 ile durduysa Webshare proxy deÄŸerlendir).
4. Mevcut ~14k aktif ilanÄ±n geÃ§miÅŸe dÃ¶nÃ¼k semantik embed'lenmesi (D3) bilinÃ§li olarak otomatik
   BAÅLATILMADI â€” Gemini API maliyeti/kota kararÄ± sana ait (script gece baÅŸÄ±na sadece 300 yeni ilan
   iÅŸler varsayÄ±lan olarak, `ilan_embed_uret.py --max` deÄŸeriyle hÄ±zlandÄ±rÄ±labilir).

<details><summary>(tarihsel â€” cutover Ã¶ncesi durum notlarÄ±)</summary>

> **VDS (`195.85.207.126`) = gerÃ§ek/gÃ¼ncel production ve Ã–NCELÄ°K 10 Ã¶zellikleri BURADA CANLI.**
> **Managed (`lpgelwfoarhouollhwur.supabase.co`) = donmuÅŸ; canlÄ± site hÃ¢lÃ¢ buna baÄŸlÄ± â†’ CUTOVER GEREK.**

**âœ… Kod (repo, tÃ¼mÃ¼ push'landÄ± â€” 8 commit):** A2, A3, B1, B2, B3, C1, C2, C3, D1, D2, E2 fazlarÄ±.
Yeni dosyalar: `firmalar.html`, `backend/firma_normalize.py`, `backend/firma_ai_yorum.py`,
`backend/yuklenici_yenile_calistir.py`, `backend/migration_{sonuc_kisim,yuklenici_agg,analiz_rpc}.sql`.

**âœ… VDS'e uygulandÄ± + canlÄ± doÄŸrulandÄ± (SSH, aÃ§Ä±k kullanÄ±cÄ± yetkisiyle):**
- 3 migration Ã§alÄ±ÅŸtÄ±rÄ±ldÄ± â†’ `analiz_pivot` RPC + `yuklenici_yenile()` + kÄ±sÄ±m desteÄŸi aktif.
- **Faz A3 (`--tum-kayitlar` geniÅŸ backfill) canlÄ± EKAP'a karÅŸÄ± Ã‡ALIÅTI + BÄ°TTÄ°** â€” IKN-havuzuna baÄŸlÄ±
  olmadan sonuÃ§lanmÄ±ÅŸ her ihaleyi kompakt yazdÄ± (15.000 kayÄ±t tarandÄ±, 14.767 sonuÃ§ yazÄ±ldÄ±, **0 hata**, %95+ verim).
- **âœ… VERÄ° HACMÄ° PATLADI: `ihale_sonuclari` 35 â†’ 20.686 sonuÃ§** (toplam 662 milyar TL sÃ¶zleÅŸme),
  `ilanlar` kompakt geÃ§miÅŸ 15.126 satÄ±r (`durum='sonuclandi'`, aktif sayaÃ§larÄ± kirletmez).
  **`yukleniciler` firma sÃ¶zlÃ¼ÄŸÃ¼ tazelendi â†’ 11.186 BENZERSÄ°Z FÄ°RMA** (0 yetim). Zirvede Ä°PEK HIRDAVAT
  (109 iÅŸ/441M TL), MERÄ°DYEN TESÄ°SAT (77 iÅŸ/330M TL). `analiz_pivot` uÃ§tan uca doÄŸrulandÄ± (firmaâ†’idare
  kÄ±rÄ±lÄ±mÄ± gerÃ§ek veriyle Ã§alÄ±ÅŸÄ±yor). Checkpoint skip=15200 â†’ cron buradan devam eder, veri her gece artar.
- **Cron gÃ¼ncellendi** (`run_scraper.sh`): her gece sonuÃ§ taramasÄ± + firma tazeleme â†’ kendini besliyor.

**ğŸ› UÃ§tan uca testte bulunan+dÃ¼zeltilen 2 bug (repoda):** (1) `normalize_firma` tam kelime ÅŸirket
eklerini ("ANONÄ°M ÅÄ°RKETÄ°" vb.) temizlemiyordu â†’ kÄ±smi ad aramasÄ± eÅŸleÅŸmiyordu. (2) `--tum-kayitlar`
kompakt insert'i `ilanlar.kaynak` (NOT NULL) vermiyordu â†’ 23502 hatasÄ±. Ä°kisi de dÃ¼zeltildi.

**ğŸ”´ KALAN â€” kullanÄ±cÄ±/sonraki oturum:**
1. âœ… ~~DNS cutover~~ **YAPILDI (10 Tem)** â€” yukarÄ±ya bak.
2. C4 (eÅŸik katsayÄ±sÄ±), D3 (semantik embedding), D4 (teklif workflow), E1/E3/E4 henÃ¼z YAPILMADI.
3. Resend e-posta domain doÄŸrulama + eski servisleri kapat (yukarÄ±daki cutover-sonrasÄ± notu).

</details>

---

> **BU BÃ–LÃœM SONNET Ä°Ã‡Ä°N YAZILDI.** UygulayÄ±cÄ± AI: aÅŸaÄŸÄ±daki fazlarÄ± SIRAYLA yap, her fazÄ±n sonundaki
> "KABUL KRÄ°TERÄ°"ni doÄŸrulamadan sonrakine geÃ§me. Her adÄ±mda dosya yollarÄ±, tablo/kolon adlarÄ± ve
> komutlar aÃ§Ä±kÃ§a verildi. KararsÄ±z kaldÄ±ÄŸÄ±n yerde bu bÃ¶lÃ¼mdeki varsayÄ±lanÄ± uygula, kullanÄ±cÄ±ya sorma.
>
> **9 Tem 2026 canlÄ± kontrol (anonim):** ihaleciler.com ÅŸu an ~13.0k aktif ihale (EKAP 9.158 + Gazete 1.229 +
> Ä°stihbarat 2.174), 81 il, 40+ sektÃ¶r, 16 idare tÃ¼rÃ¼, yÃ¼klenici dizini (`/contractors`), KÄ°K kararlarÄ±,
> `/analyze` pivot motoru (Ã¼yelik-korumalÄ±; metrikler: sÃ¶zleÅŸme bedeli aralÄ±ÄŸÄ±, tenzilat %, katÄ±lÄ±mcÄ±/geÃ§erli
> teklif sayÄ±sÄ±, yayÄ±n/teklif/sÃ¶zleÅŸme tarihleri, iÅŸ/Ã¶deme/teslim sÃ¼releri, eÅŸik katsayÄ±sÄ± 0.70â€“1.20).
>
> **Stratejik Ã¶zet:** ihaleciler'in TEK gerÃ§ek hendeÄŸi = YILLARA YAYILMIÅ SONUÃ‡ VERÄ°SÄ° (firma Ã— ihale Ã— bedel Ã—
> tenzilat). UI'larÄ± eski, AI'larÄ± YOK. Bizim boru hattÄ±mÄ±z Ã§alÄ±ÅŸÄ±yor (ekap_sonuc_backfill.py â†’ ihale_sonuclari,
> 35 kayÄ±t) ama hacim yok. Plan = (A) hacmi bÃ¼yÃ¼t, (B) firma katmanÄ±nÄ± kur, (C) analiz motorunu yaz,
> (D) AI'Ä± verinin ÃœSTÃœNE koy (onlarda hiÃ§ yok â†’ geÃ§iÅŸ noktamÄ±z), (E) tahmin/istihbarat (kimsede yok).
>
> â›” **HUKUKÄ° SINIR (deÄŸiÅŸmedi, bkz. 9.1.1):** ihaleciler.com'dan TEK SATIR veri Ã§ekilmeyecek. TÃ¼m veri
> EKAP/KÄ°K kamu kaynaklarÄ±ndan. ihaleciler sadece "Ã¶zellik referansÄ±".

### ğŸŸ¡ Ä°LERLEME (9 Tem 2026, Sonnet oturumu â€” kod hazÄ±r, DB migration'larÄ± BEKLÄ°YOR)

> **GÃœNCELLEME (9 Tem, Opus oturumu):** KullanÄ±cÄ± aÃ§Ä±k SSH yetkisi verdi â†’ VDS'e 3 migration UYGULANDI +
> DOÄRULANDI, `--tum-kayitlar` geniÅŸ backfill canlÄ± EKAP'a karÅŸÄ± test edildi ve Ã‡ALIÅIYOR (2 sayfada 189
> sonuÃ§/0 hata), arka planda bÃ¼yÃ¼k parti Ã§alÄ±ÅŸÄ±yor (35 â†’ 700+ sonuÃ§ ve artÄ±yor). Detay: aÅŸaÄŸÄ±daki
> "VDS'E UYGULANDI" + "A3 CANLI DOÄRULANDI" bloklarÄ±nda. Managed bilinÃ§li atlandÄ± (donmuÅŸ, cutover gerek).
>
> Bu oturumda A2/A3/B1/B2/B3/C1 iÃ§in KOD yazÄ±ldÄ± ve `firmalar.html` local Ã¶nizlemede doÄŸrulandÄ±.

- âœ… **A2+A3 kod hazÄ±r** (`backend/ekap_sonuc_backfill.py`): Ã§ok kÄ±sÄ±mlÄ± (kÄ±sÄ±m/lot) desteÄŸi eklendi
  (`sonuc_kayitlari_olustur()` artÄ±k liste dÃ¶ner, her kÄ±sÄ±m `(ilan_id, kisim_no)` ile upsert edilir);
  katÄ±lÄ±mcÄ± sayÄ±sÄ± HTML'den parse ediliyor (`html_teklif_sayisi_parse` â†’ `katilimci` alanÄ±); B kolonlarÄ±
  (tenzilat_yuzde, yaklasik_maliyet, katilimci_sayisi, gecerli_teklif_sayisi, sozlesme_tarihi, ikn,
  yuklenici_ad, sozlesme_bedeli) artÄ±k her yazÄ±mda dolduruluyor. `--tum-kayitlar` flag'i eklendi
  (`ilan_kompakt_ekle()`): IKN bizim havuzda yoksa bile kompakt satÄ±r oluÅŸturup devam eder; 403/429
  alÄ±nca "PROXY GEREK" logu ile duruyor (kullanÄ±cÄ± Webshare doldurunca devam edilir).
- âœ… **`backend/migration_sonuc_kisim.sql`** (yeni): `ihale_sonuclari`'ya `kisim_no` ekler, eski
  tekil `ilan_id` kÄ±sÄ±tÄ±nÄ± `(ilan_id, kisim_no)`'ya geniÅŸletir. **UYGULANMADI.**
- âœ… **B1 kod hazÄ±r**: `backend/firma_normalize.py` (Python normalize_ad/ortak_girisim tespiti) +
  `backend/migration_yuklenici_agg.sql`'deki `normalize_firma()` (SQL ikizi, davranÄ±ÅŸÃ§a senkron).
- âœ… **B2 kod hazÄ±r**: `backend/migration_yuklenici_agg.sql` â†’ `yuklenici_yenile()` RPC'si (agregasyon
  + `ihale_sonuclari.yuklenici_id` doldurma). Cron tetikleyici: `backend/yuklenici_yenile_calistir.py`
  (REST Ã¼zerinden RPC Ã§aÄŸÄ±rÄ±r). **RPC UYGULANMADI, cron'a EKLENMEDÄ°.**
- âœ… **B3 TAMAMLANDI (frontend)**: `firmalar.html` (yeni) â€” idareler.html ÅŸablonundan, arama+il filtresi+
  4 sÄ±ralama+CSV+paylaÅŸ+boÅŸ-durum. `yukleniciler` boÅŸken/tablo yokken kullanÄ±cÄ±ya kÄ±rmÄ±zÄ± hata yerine
  bilgilendirici mesaj gÃ¶steriyor (test edildi: managed'da tablo 404 verdi, mesaj dÃ¼zgÃ¼n gÃ¶rÃ¼ndÃ¼).
  Sidebar linki (`ğŸ¢ Firmalar Dizini`) **17 sayfaya** eklendi (idareler linkinden hemen sonra, tutarlÄ±
  konumda): bildirimler, dokumanlar, firma-analiz, fiyatlandirma_odeme_bolumu, ihale-detay, ihaleler,
  kik-kararlar, kurum-analiz, profil, rekabet-analizi, sektorler, sonuclananlar, teklif-olustur,
  uyumluluk, dashboard, takipte, idareler (kendi sayfasÄ±, `active` sÄ±nÄ±fÄ±yla). Ana sayfa haritasÄ±ndaki
  "ğŸ¢ Firmalar (YakÄ±nda)" sekmesi artÄ±k gerÃ§ek link (`index.html`) â€” choropleth deÄŸil, doÄŸrudan dizine yÃ¶nlendirir.
  âš ï¸ Not: `firma-analiz.html`'in `?firma=` parametresi ham ada ILIKE arama yapÄ±yor (normalize_ad deÄŸil) â€”
  `firmalar.html` linkleri bu yÃ¼zden `f.ad` (gÃ¶rÃ¼nen ad) kullanÄ±yor, `f.normalizeAd` deÄŸil.
- âœ… **C1 kod hazÄ±r**: `backend/migration_analiz_rpc.sql` â†’ `analiz_pivot(p_grup, p_firma, p_idare,
  p_kategori, p_il, p_yil)` RPC'si (whitelist'li dinamik GROUP BY, 7 kÄ±rÄ±lÄ±m). **UYGULANMADI.**
  ğŸ› YazÄ±m sÄ±rasÄ±nda bulunan+dÃ¼zeltilen bug: `p_firma` filtresi ham firma adÄ±nÄ± normalize etmeden
  `normalize_ad`'a karÅŸÄ± karÅŸÄ±laÅŸtÄ±rÄ±yordu (asla eÅŸleÅŸmezdi) â€” artÄ±k `normalize_firma($1)` ile sarmalanÄ±yor.
- âœ… **C2 TAMAMLANDI (frontend, RPC'siz de gÃ¼venli)**: `firma-analiz.html` SonuÃ§lar sekmesine
  `pivotKirilimGoster()` eklendi â€” `analiz_pivot('idare', p_firma=FIRMA)` ve `('kategori', ...)` Ã§aÄŸÄ±rÄ±p
  "En Ã‡ok Ã‡alÄ±ÅŸtÄ±ÄŸÄ± Ä°dareler" + "SektÃ¶r KÄ±rÄ±lÄ±mÄ±" kartlarÄ±nÄ± gÃ¶sterir. RPC yoksa (`Could not find function`)
  `console.info` ile sessizce loglanÄ±r, sayfa hiÃ§ etkilenmez â€” local Ã¶nizlemede doÄŸrulandÄ± (hata yok,
  boÅŸ-durum kartÄ± normal render oldu). Firma deÄŸiÅŸince pivot cache'i sÄ±fÄ±rlanÄ±yor (`_pivotYuklendi`).
- âœ… **C3 TAMAMLANDI (frontend, RPC'siz de gÃ¼venli)**: `kurum-analiz.html` DaÄŸÄ±lÄ±m Analizi sekmesine
  "ğŸ† Kazanan Firmalar" kartÄ± eklendi (`analiz_pivot('firma', p_idare=KURUM)`) â€” RPC yoksa kart
  `display:none` kalÄ±r (local Ã¶nizlemede doÄŸrulandÄ±, konsol hatasÄ±z). Bu, ihaleciler'in "idare hangi
  firmalarla Ã§alÄ±ÅŸÄ±yor" gÃ¶rÃ¼nÃ¼mÃ¼ne parite.
- [ ] ğŸ”´ **C4 YAPILMADI**: eÅŸik katsayÄ±sÄ± kolonu/filtresi henÃ¼z eklenmedi (scraper + DB + UI gerekiyor,
  ayrÄ± bir iÅŸ â€” bkz. madde 4 "Ä°HALECÄ°LER.COM EKSÄ°KLERÄ°").

#### âœ… VDS'E UYGULANDI + DOÄRULANDI (9 Tem 2026, Opus oturumu â€” kullanÄ±cÄ± aÃ§Ä±k SSH yetkisi verdi)

> **VDS (`195.85.207.126`, self-hosted Supabase) tam iÅŸlevsel.** 3 migration sÄ±rayla uygulandÄ±,
> `yuklenici_yenile()` Ã§alÄ±ÅŸtÄ± â†’ **33 firma** sÃ¶zlÃ¼ÄŸe girdi, `analiz_pivot` RPC'si doÄŸru veri dÃ¶ndÃ¼rÃ¼yor.

- âœ… **3 migration VDS `supabase-db`'ye uygulandÄ±**: `migration_sonuc_kisim.sql` â†’ `migration_yuklenici_agg.sql`
  â†’ `migration_analiz_rpc.sql`. Hepsi temiz (BEGINâ€¦COMMIT).
- âœ… **`yuklenici_yenile()` Ã§alÄ±ÅŸtÄ± â†’ 33 firma** (Ã¶rn. DEMÄ°R YAPI 2 iÅŸ/181M TL, KOÃ‡ SÄ°STEM 1 iÅŸ/76M TL).
  REST tetikleyici `yuklenici_yenile_calistir.py` de test edildi (âœ“ 33 satÄ±r).
- âœ… **`analiz_pivot` doÄŸrulandÄ±**: `analiz_pivot('yil')` â†’ 2026: 35 ihale/677M TL. `analiz_pivot('idare',
  p_firma:='DEMÄ°R YAPI Ä°NÅAAT')` â†’ TCDD 2 iÅŸ/181M TL (kÄ±smi ad eÅŸleÅŸmesi Ã§alÄ±ÅŸÄ±yor).
- ğŸ› **UÃ‡TAN UCA TESTTE BULUNAN + DÃœZELTÄ°LEN BUG (normalize_firma)**: normalizasyon "ANONÄ°M ÅÄ°RKETÄ°",
  "LÄ°MÄ°TED ÅÄ°RKETÄ°" gibi TAM kelime eklerini temizlemiyordu (sadece "A.Å." kÄ±saltmasÄ±nÄ±) â†’ kÄ±smi ad
  aramalarÄ± ("DEMÄ°R YAPI Ä°NÅAAT") tam adla ("...ANONÄ°M ÅÄ°RKETÄ°") eÅŸleÅŸmiyordu. Hem SQL `normalize_firma()`
  hem Python `firma_normalize.py` dÃ¼zeltildi (ANONÄ°M/LÄ°MÄ°TED/ÅÄ°RKET(Ä°)/KOLLEKTÄ°F/KOMANDÄ°T tam kelimeleri
  + noktalama-Ã¶nce-temizlik sÄ±rasÄ±). VDS'te fonksiyon gÃ¼ncellendi, `yukleniciler` yeniden anahtarlandÄ±
  (11 yetim eski-anahtar satÄ±r hedefli DELETE ile temizlendi â†’ tam 33 firma). Repo'ya da iÅŸlendi.
- âœ… **Cron gÃ¼ncellendi** (`run_scraper.sh`, yedek alÄ±ndÄ±): ana scraper'dan sonra `ekap_sonuc_backfill.py
  --max-pages 50` + `yuklenici_yenile_calistir.py` eklendi â†’ sistem her gece kendini besliyor (Faz A1+B2).
- âœ… **C2/C3 frontend bu veriye karÅŸÄ± DB katmanÄ±nda doÄŸrulandÄ±** (psql/REST). Client JS zaten local
  Ã¶nizlemede "RPC yokken bozulmuyor" diye test edilmiÅŸti; artÄ±k RPC canlÄ± â†’ VDS frontend'inde gerÃ§ek veriyle
  Ã§alÄ±ÅŸacak (cutover sonrasÄ± kullanÄ±cÄ±ya gÃ¶rÃ¼nÃ¼r).

#### ğŸ”´ KRÄ°TÄ°K â€” MANAGED SUPABASE ARTIK DONMUÅ, CUTOVER GEREKLÄ°

> **VDS scraper'Ä± `SUPABASE_URL=http://localhost:8000`'e (VDS-local Supabase) yazÄ±yor â€” managed'a DEÄÄ°L.**
> Yani gece taramasÄ± artÄ±k **sadece VDS-local'Ä±** besliyor. Managed (`lpgelwfoarhouollhwur.supabase.co`,
> canlÄ± Cloudflare sitesinin baÄŸlÄ± olduÄŸu DB) **donmuÅŸ**: 15 sonuÃ§, yeni tablo/RPC yok, veri tazelenmÄ±yor.
>
> **SONUÃ‡:** Bu Ã¶zellikleri (firmalar dizini, pivot analizler, AI yorum, kazanma bandÄ±) gerÃ§ek kullanÄ±cÄ±lara
> canlÄ± yapmanÄ±n yolu **managed'a migration DEÄÄ°L** (Ã§Ã¶pe giden iÅŸ â€” managed terk ediliyor), **DNS cutover**:
> - Managed'a migration YAPILMADI (bilinÃ§li â€” donmuÅŸ DB'ye yatÄ±rÄ±m anlamsÄ±z).
> - Cutover adÄ±mlarÄ± hazÄ±r: bkz. "ğŸ¤ DEVÄ°R" bloÄŸu AdÄ±m 3-6 (Cloudflare DNS â†’ `195.85.207.126`, SSL, URL'ler).
> - Cutover olunca VDS canlÄ±ya geÃ§er â†’ tÃ¼m bu Ã¶zellikler + taze veri + firma analitiÄŸi kullanÄ±cÄ±ya aÃ§Ä±lÄ±r.
> - âš ï¸ EÄŸer cutover YAKIN DEÄÄ°LSE ve managed'Ä±n da gÃ¼ncel kalmasÄ± isteniyorsa: (a) 3 migration'Ä± Supabase
>   Dashboard SQL Editor'dan managed'a uygula, (b) scraper'Ä± managed'a da yazacak ÅŸekilde Ã§ift-yaz yap â€”
>   ama bu geÃ§ici; asÄ±l Ã§Ã¶zÃ¼m cutover.

#### ğŸ”‘ (REFERANS) DB migration'larÄ±nÄ± elle uygulama komutlarÄ±

AÅŸaÄŸÄ±daki 3 dosya VDS'e VE managed Supabase'e (cutover'a dek ikisi de canlÄ±) sÄ±rayla uygulanmalÄ±:
`backend/migration_sonuc_kisim.sql` â†’ `backend/migration_yuklenici_agg.sql` â†’ `backend/migration_analiz_rpc.sql`
(bu sÄ±ra Ã¶nemli: kisim.sql Ã¶nce, Ã§Ã¼nkÃ¼ diÄŸer ikisi `ihale_sonuclari` ÅŸemasÄ±nÄ±n nihai halini varsayÄ±yor).

**VDS (SSH):**
```bash
ssh -i ~/.ssh/ihale_oracle root@195.85.207.126
cd /opt/ihale-platform && git pull origin main
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_sonuc_kisim.sql
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_yuklenici_agg.sql
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_analiz_rpc.sql
# doÄŸrula:
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT yuklenici_yenile();"
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT * FROM analiz_pivot('yil') LIMIT 5;"
```
**Managed Supabase (Dashboard â†’ SQL Editor):** aynÄ± 3 dosyanÄ±n iÃ§eriÄŸini sÄ±rayla yapÄ±ÅŸtÄ±r+RUN.

**Sonra cron'a ekle (VDS, `run_scraper.sh`'e, ana scraper'dan SONRA):**
```bash
cat >> /opt/ihale-platform/backend/run_scraper.sh << 'EOF'
$VENV/python ekap_sonuc_backfill.py --max-pages 50 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python yuklenici_yenile_calistir.py >> /opt/ihale-platform/logs/scraper.log 2>&1
EOF
```
Bu 2 satÄ±r A1'i de tamamlar (9.1'in bekleyen (a) maddesiyle aynÄ± iÅŸ).

**GeniÅŸ backfill'i baÅŸlatmak isterseniz (Faz A3, proxy'siz ilk deneme):**
```bash
venv/bin/python ekap_sonuc_backfill.py --tum-kayitlar --max-pages 200 --reset
```

---

## 10.0 Mevcut durum envanteri (Sonnet: Ã¶nce bunu doÄŸrula)

| VarlÄ±k | Durum | Yer |
|---|---|---|
| `ilanlar` | ~14.0k aktif ihale, gece cron VDS'te | VDS Supabase (`ssh -i ~/.ssh/ihale_oracle root@195.85.207.126`) |
| `ihale_sonuclari` | ~35 kayÄ±t, Design A (`kazanan_firma`,`kazanan_teklif`,`kazanan_teklif_farki_yuzde`) + B kolonlarÄ± migration'la eklendi (`tenzilat_yuzde`,`yaklasik_maliyet`,`katilimci_sayisi`,`gecerli_teklif_sayisi`) ama B kolonlarÄ± BOÅ | `backend/migration_sonuc_B_kurulum.sql` uygulandÄ± |
| `yukleniciler` | tablo VAR, BOÅ | aynÄ± migration |
| SonuÃ§ scraper | Ã‡ALIÅIYOR: `backend/ekap_sonuc_backfill.py` (EKAP durum=15 listesi Ã— bizim IKN kesiÅŸimi, checkpoint'li, plato-tespitli) | cron'a eklenmesi bekliyor (bkz. 9.1 kalan (a)) |
| Firma UI | `firma-analiz.html` (SonuÃ§lar sekmesi Ã§alÄ±ÅŸÄ±yor), `kurum-analiz.html`, `rekabet-analizi.html`, `sonuclananlar.html` | frontend |
| AI | Gemini analiz (`analyzer.py`, 7 bÃ¶lÃ¼mlÃ¼ ÅŸartname analizi) â€” sonuÃ§/firma verisine HÄ°Ã‡ baÄŸlÄ± deÄŸil | backend |
| KÄ°K kararlarÄ± | UI+tablo+script hazÄ±r, kaynak IP-bloklu (Playwright Ã§Ã¶zÃ¼mÃ¼ bekliyor) | `backend/kik_backfill.py` |

## 10.A FAZ A â€” VERÄ° HACMÄ°: sonuÃ§ verisini 35'ten on binlere Ã§Ä±kar (her ÅŸeyin Ã¶nkoÅŸulu)

**A1. Cron'a gÃ¼nlÃ¼k sonuÃ§ taramasÄ± ekle (5 dk):** `run_scraper.sh`'e ana scraper'dan SONRA gelecek satÄ±r:
`$VENV/python ekap_sonuc_backfill.py --max-pages 50 >> /opt/ihale-platform/logs/scraper.log 2>&1`
MantÄ±k: her gece EKAP'Ä±n "yeni sonuÃ§lananlar" penceresini tarar; bizim havuz bÃ¼yÃ¼dÃ¼kÃ§e kesiÅŸim bÃ¼yÃ¼r.

**A2. KayÄ±t baÅŸÄ±na eksik alanlarÄ± doldur:** `ekap_sonuc_backfill.py`'de SONUÃ‡ Ä°LANI HTML'i zaten parse ediliyor
(`html_yaklasik_maliyet_parse`). AynÄ± HTML'den regex ile ÅŸunlarÄ± da Ã§Ä±kar ve `ihale_sonuclari`'nÄ±n ZATEN VAR OLAN
B kolonlarÄ±na yaz: **katÄ±lÄ±mcÄ± sayÄ±sÄ±** ("... dokÃ¼man satÄ±n alÄ±nmÄ±ÅŸ/indirilmiÅŸ", "X istekli katÄ±lmÄ±ÅŸ"),
**geÃ§erli teklif sayÄ±sÄ±**, **sÃ¶zleÅŸme tarihi**, mÃ¼mkÃ¼nse **iÅŸe baÅŸlama/bitiÅŸ**. Ek olarak `tenzilat_yuzde`'yi
(zaten `kazanan_teklif_farki_yuzde` hesaplanÄ±yor) B kolonuna da kopyala â€” analiz motoru B kolonlarÄ±ndan okuyacak.
- Ã‡ok kÄ±sÄ±mlÄ± ihale: `sozlesmeBilgiList` birden fazla elemanlÄ±ysa HER kÄ±smÄ± ayrÄ± satÄ±r yaz. Bunun iÃ§in migration:
  `ihale_sonuclari`'ya `kisim_no INTEGER DEFAULT 1` ekle + unique constraint'i `(ilan_id, kisim_no)` yap
  (yeni dosya: `backend/migration_sonuc_kisim.sql`; hem VDS'e hem managed'a uygulanacak â€” VDS: `docker exec -i supabase-db psql -U postgres -d postgres < dosya`).

**A3. GEÃ‡MÄ°ÅE DÃ–NÃœK GENÄ°Å BACKFILL â€” "havuzdan baÄŸÄ±msÄ±z" mod (BÃœYÃœK KALDIRAÃ‡):**
Åu anki script SADECE bizim `ilanlar` IKN'leriyle kesiÅŸeni yazÄ±yor (%0.7 isabet) â†’ hacim tavanÄ± bizim havuz.
Ä°haleciler'i yakalamak iÃ§in bu baÄŸÄ± kopar:
- `ekap_sonuc_backfill.py`'ye `--tum-kayitlar` flag'i ekle: IKN bizde OLMASA BÄ°LE sonuÃ§lanmÄ±ÅŸ ihaleyi Ã§ek,
  Ã¶nce `ilanlar`'a KOMPAKT bir satÄ±r upsert et (ikn, baslik, idare, il, tur, usul, okas/kategori, ilan_tarihi,
  `durum='sonuclandi'`, `ilan_metni=NULL` â€” depolama stratejisi "geÃ§miÅŸ=kompakt ~0.5KB", bkz. VDS bÃ¶lÃ¼mÃ¼),
  sonra `ihale_sonuclari` satÄ±rÄ±nÄ± yaz.
- HÄ±z/koruma: sayfa baÅŸÄ±na 0.3s throttle korunacak; `--max-pages` sÄ±nÄ±rÄ± ile parÃ§a parÃ§a (gecelik 200 sayfa =
  20k kayÄ±t taramasÄ± â‰ˆ makul). Checkpoint zaten var. **Proxy'siz baÅŸla** (ana scraper aynÄ± IP'den ban yemiyor);
  ilk 403/429'da dur ve log'a "PROXY GEREK" yaz â€” o noktada kullanÄ±cÄ± Webshare'i doldurur.
- Hedef: **Ã¶nce son 2 yÄ±l** (analitik deÄŸerin %80'i gÃ¼ncel veride), sonra 2003'e doÄŸru. 1.68M kayÄ±t Ã— son 2 yÄ±l
  â‰ˆ tahmini 300-400k sonuÃ§ â†’ Supabase self-hosted VDS'te disk sorunu yok (%13 dolu, 158G).
**KABUL KRÄ°TERÄ° A:** `ihale_sonuclari` â‰¥ 10.000 satÄ±r, `katilimci_sayisi` doluluk â‰¥ %60, cron her gece artÄ±rÄ±yor.

## 10.B FAZ B â€” FÄ°RMA KATMANI: `yukleniciler` sÃ¶zlÃ¼ÄŸÃ¼nÃ¼ kur ve doldur

**B1. Normalizasyon fonksiyonu (kritik â€” firma birleÅŸtirme):** `backend/firma_normalize.py`:
`normalize_ad()`: bÃ¼yÃ¼k harf (TR locale: Ä°/I dikkat), "A.Å./LTD.ÅTÄ°./TÄ°C./SAN./Ä°NÅ." varyantlarÄ±nÄ± tekilleÅŸtir,
noktalama/fazla boÅŸluk temizle, mojibake dÃ¼zelt. AynÄ± fonksiyonun SQL karÅŸÄ±lÄ±ÄŸÄ±nÄ± da yaz (migration'da
`immutable` PL/pgSQL fonksiyon `normalize_firma(text)`), Ã§Ã¼nkÃ¼ hem Python-yazma hem SQL-sorgulama tarafÄ± aynÄ±
anahtarÄ± kullanmalÄ±. Ortak giriÅŸim ("Ä°Å ORTAKLIÄI", "ORTAK GÄ°RÄ°ÅÄ°M", "-" ile ayrÄ±lmÄ±ÅŸ iki firma) tespit edilirse
`ortak_girisim=true` iÅŸaretle ve mÃ¼mkÃ¼nse ortaklarÄ± ayÄ±r (`ortaklar text[]`).

**B2. `yukleniciler`'i agregasyonla doldur (scrape DEÄÄ°L, mevcut veriden tÃ¼ret):**
`backend/migration_yuklenici_agg.sql` iÃ§inde RPC `yuklenici_yenile()`:
`INSERT ... SELECT normalize_firma(kazanan_firma), min(kazanan_firma) as gorunen_ad, count(*), sum(kazanan_teklif), avg(tenzilat), max(sonuc_tarihi), array_agg(distinct kategori), array_agg(distinct il) FROM ihale_sonuclari JOIN ilanlar ... GROUP BY 1 ON CONFLICT (normalize_ad) DO UPDATE ...`
Cron sonunda Ã§aÄŸÄ±r (`run_scraper.sh`'e psql/REST Ã§aÄŸrÄ±sÄ±). BÃ¶ylece `yukleniciler` HER GECE kendini tazeler.

**B3. Firma dizini sayfasÄ± `firmalar.html`** (idareler.html'i ÅŸablon al â€” aynÄ± kart/filtre/CSV dÃ¼zeni):
arama + il + sektÃ¶r filtresi, sÄ±ralama (toplam ciro / iÅŸ sayÄ±sÄ± / son iÅŸ tarihi), her kart â†’ `firma-analiz?firma=<normalize_ad>`.
Sidebar'a "ğŸ¢ Firmalar" linkini TÃœM sayfalara ekle. Ana sayfadaki harita "Firmalar" sekmesini ("YakÄ±nda") buna baÄŸla.
**KABUL KRÄ°TERÄ° B:** `firmalar.html` canlÄ±da arama+filtreyle Ã§alÄ±ÅŸÄ±yor; `yukleniciler` satÄ±r sayÄ±sÄ± = distinct normalize_ad sayÄ±sÄ±; ortak giriÅŸimler Ã§ift firma yaratmÄ±yor.

## 10.C FAZ C â€” ANALÄ°Z MOTORU: ihaleciler `/analyze` paritesi (RPC tabanlÄ±)

**C1. Tek esnek pivot RPC:** `backend/migration_analiz_rpc.sql` â†’ `analiz_pivot(p_firma text, p_idare text, p_kategori text, p_il text, p_yil int, p_grup text)`:
`ihale_sonuclari â‹ˆ ilanlar` Ã¼zerinde verilen filtrelerle `p_grup`'a gÃ¶re (`'yil'|'kategori'|'idare'|'il'|'usul'|'tur'|'firma'`)
GROUP BY dÃ¶ner: `grup_deger, ihale_sayisi, toplam_bedel, ort_bedel, ort_tenzilat, ort_katilimci, ort_gecerli_teklif`.
SECURITY DEFINER + anon EXECUTE (veri zaten public-read). Client-side 1000'er batch Ã§ekme ALIÅKANLIÄINI BIRAK â€” bu RPC her analiz sayfasÄ±nÄ±n tek veri kaynaÄŸÄ± olsun.

**C2. `firma-analiz.html`'i tam profile dÃ¶nÃ¼ÅŸtÃ¼r** (9.2.1(b) listesi geÃ§erli, veri artÄ±k var):
KPI ÅŸeridi (toplam sÃ¶zleÅŸme+ciro+ort.tenzilat+ort.katÄ±lÄ±mcÄ±+ilk/son iÅŸ) Â· YÄ±llÄ±k trend (Chart.js line) Â·
SektÃ¶r kÄ±rÄ±lÄ±mÄ± Â· Ä°dare kÄ±rÄ±lÄ±mÄ± ("en Ã§ok Ã§alÄ±ÅŸtÄ±ÄŸÄ± 10 idare" â€” tekrar eden idare vurgusu) Â·
**Rakip firmalar**: aynÄ± (kategoriÃ—il) hÃ¼cresinde kazanan diÄŸer firmalar (`analiz_pivot` p_grup='firma') Â·
KazandÄ±ÄŸÄ± iÅŸler listesi (mevcut SonuÃ§lar sekmesi, sayfalÄ±). Hepsi C1 RPC'sinden.

**C3. `kurum-analiz.html`'i derinleÅŸtir:** o idarenin sonuÃ§lanan iÅŸleri, kazanan firma daÄŸÄ±lÄ±mÄ± (pasta),
ort. tenzilat, "bu idarede kazanmak iÃ§in ort. %X tenzilat gerekir" kutusu.

**C4. EÅŸik katsayÄ±sÄ± (ihaleciler'de var, bizde yok â€” madde 4):** `ilanlar`'a `esik_katsayi NUMERIC` kolonu
(migration) + scraper'da EKAP detayÄ±ndan Ã§ek (yapÄ±m iÅŸi sÄ±nÄ±r deÄŸer katsayÄ±sÄ± 0.70â€“1.20 aralÄ±ÄŸÄ± ilan/idari
ÅŸartname verisinde) + `ihaleler.html` DetaylÄ± Ara'ya dropdown. BulunamÄ±yorsa NULL bÄ±rak, filtre "belirtilmemiÅŸ"i dÄ±ÅŸlar.
**KABUL KRÄ°TERÄ° C:** firma-analiz bir gerÃ§ek firma iÃ§in <2sn'de KPI+4 kÄ±rÄ±lÄ±m gÃ¶steriyor; sorgular RPC'den (Network sekmesinde tek istek/kÄ±rÄ±lÄ±m).

## 10.D FAZ D â€” AI KATMANI: veriyi yoruma Ã§evir (ihaleciler'de YOK â†’ geÃ§iÅŸ noktasÄ±)

> Ä°lke: AI'Ä± ham LLM Ã§aÄŸrÄ±sÄ± olarak deÄŸil, **C fazÄ±nÄ±n RPC Ã§Ä±ktÄ±sÄ±nÄ± prompt'a gÃ¶men** yapÄ± olarak kur.
> HalÃ¼sinasyon riski = dÃ¼ÅŸÃ¼k (sayÄ±lar bizden, yorum AI'dan). Cache'le (kredi sistemine uygun).

**D1. AI Firma Yorumu:** `api.py`'ye `POST /ai/firma-yorum {firma}` â†’ `analiz_pivot`'un 4 kÄ±rÄ±lÄ±mÄ±nÄ± JSON olarak
Gemini'ye ver, iste: gÃ¼Ã§lÃ¼ olduÄŸu idareler/sektÃ¶rler, tenzilat agresifliÄŸi, yÃ¶nelim (son 12 ay), rekabet Ã¶nerisi
("bu firmayla X ihalesinde karÅŸÄ±laÅŸÄ±rsanÄ±z ..."). Sonucu `yukleniciler.ai_yorum` + `ai_yorum_tarih`'e cache'le
(7 gÃ¼n geÃ§erli). `firma-analiz.html`'e "ğŸ¤– AI Rakip Analizi" kartÄ± (1 kredi dÃ¼ÅŸ; free'de blur+CTA).
**D2. Tenzilat/kazanma tahmini (KÄ°MSEDE YOK â€” amiral gemisi adayÄ±):** `ihale-detay.html`'e "Bu ihaleyi kazanmak
iÃ§in tahmini teklif bandÄ±" kutusu: aynÄ± (idareÃ—kategoriÃ—il) geÃ§miÅŸ sonuÃ§larÄ±ndan ortÂ±std tenzilat â†’ yaklaÅŸÄ±k
maliyetten banda Ã§evir + geÃ§miÅŸ Ã¶rnekleri listele. Ä°lk sÃ¼rÃ¼m SALT Ä°STATÄ°STÄ°K (RPC), yeterli veri yoksa ("<5 emsal")
kutuyu gizle. AI sadece aÃ§Ä±klama metnini yazar. Bu Ã¶zellik pazarlamada "Fiyat Ä°stihbaratÄ±" olarak PRO'ya baÄŸlanÄ±r.
**D3. Semantik eÅŸleÅŸme (9.7'deki bekleyen iÅŸ):** Gemini `text-embedding-004` ile (a) firma profili (sektÃ¶r+
anahtar kelime+sertifika metni) ve (b) yeni ihale baÅŸlÄ±k+Ã¶zet embed'i â†’ pgvector `ilanlar.embedding` kolonu +
cron'da yeni ilanlara embed. Uyum skoru = mevcut kural puanÄ± %60 + cosine %40. pgvector self-hosted'da kurulu
deÄŸilse: `CREATE EXTENSION vector;` (VDS'te mÃ¼mkÃ¼n, managed'da da var).
**D4. AI teklif workflow baÄŸlantÄ±sÄ± (9.5):** teklif-olustur.html'e firma verisini enjekte et: "benzer iÅŸleri
geÃ§miÅŸte X,Y firmalarÄ± %Z tenzilatla aldÄ±" baÄŸlamÄ±nÄ± teklif metni promptuna ekle â†’ teklif taslaÄŸÄ± piyasa-farkÄ±nda olur.
**KABUL KRÄ°TERÄ° D:** D1+D2 canlÄ±da bir gerÃ§ek firma/ihale Ã¼zerinde Ã§alÄ±ÅŸÄ±yor, sonuÃ§lar cache'leniyor, kredi dÃ¼ÅŸÃ¼mÃ¼ iÅŸliyor.

### ğŸŸ¡ Ä°LERLEME D1 (9 Tem 2026, Sonnet â€” kod hazÄ±r, DB migration + frontend kartÄ± BEKLÄ°YOR)

- âœ… **`backend/firma_ai_yorum.py`** (yeni): `firma_yorum_uret(firma_adi, kirilimlar)` â€” analyzer.py ile
  aynÄ± Gemini 1.5 Flash konfigÃ¼rasyonu, kÄ±rÄ±lÄ±mlarÄ± (idare/kategori/il/yÄ±l) JSON olarak prompt'a gÃ¶mÃ¼yor,
  4-6 cÃ¼mlelik dÃ¼z metin TÃ¼rkÃ§e yorum istiyor (halÃ¼sinasyon riskini azaltmak iÃ§in "bu sayÄ±lara sadÄ±k kal" talimatÄ±).
- âœ… **`api.py`'ye `POST /ai/firma-yorum {firma}` endpoint'i eklendi**: auth zorunlu â†’ cache kontrolÃ¼
  (`yukleniciler.ai_yorum`, 7 gÃ¼n) â†’ kredi Ã¶n kontrolÃ¼ â†’ `analiz_pivot` RPC'sinden 4 kÄ±rÄ±lÄ±m â†’ Gemini â†’
  cache'e yaz â†’ `kredi_dus` RPC'sini Ã§aÄŸÄ±r (1 kredi).
  ğŸ› YazÄ±m sÄ±rasÄ±nda bulunan+dÃ¼zeltilen bug: fake `supabase` wrapper'da (`backend/supabase/__init__.py`)
  `.maybe_single()` YOK, sadece `.single()` (0 satÄ±rda Ä°STÄ°SNA fÄ±rlatÄ±r) â€” ilk sÃ¼rÃ¼m `.maybe_single()`
  kullanÄ±yordu, bu yeni firma aranÄ±nca hep 500 dÃ¶nerdi. DÃ¼z `.select().limit(1)` + liste kontrolÃ¼ne Ã§evrildi.
  âš ï¸ **DoÄŸrulanmamÄ±ÅŸ varsayÄ±m:** `kredi_dus` RPC'sinin tanÄ±mÄ± repoda yok (muhtemelen Supabase panelinden
  elle oluÅŸturulmuÅŸ); `p_ihale_id=None` ile Ã§aÄŸrÄ±lÄ±yor â€” RPC bunu kabul etmiyorsa (NOT NULL kÄ±sÄ±tÄ± vb.)
  kredi dÃ¼ÅŸÃ¼mÃ¼ hata verir ama try/except ile yutulur (yorum yine Ã¼retilir/cache'lenir, sadece kredi dÃ¼ÅŸmez).
  **Migration'lar uygulanÄ±nca RPC'nin gerÃ§ek imzasÄ±nÄ± kontrol et** (Supabase Dashboard â†’ Database â†’ Functions).
- âœ… **`migration_yuklenici_agg.sql` gÃ¼ncellendi**: `yukleniciler`'e `ai_yorum TEXT` + `ai_yorum_tarih
  TIMESTAMPTZ` eklendi (henÃ¼z uygulanmadÄ±, diÄŸer Faz B/C migration'larÄ±yla birlikte uygulanacak).
- âœ… **Frontend kartÄ± TAMAMLANDI**: `firma-analiz.html` SonuÃ§lar sekmesine "ğŸ¤– AI Rakip Analizi" kartÄ± eklendi
  (`aiYorumKartiGoster()`). `js/plan.js`'in `Plan.getPlan()`'Ä± ile free/pro ayrÄ±mÄ± yapÄ±lÄ±yor: free'de blurlanmÄ±ÅŸ
  Ã¶rnek metin + "Pro'ya GeÃ§ ve AÃ§" CTA, pro'da "Analizi OluÅŸtur (1 kredi)" butonu â†’ `API.firma.yorum_al(FIRMA)`.
  `js/api.js`'e `firma.yorum_al()` metodu eklendi (`POST /ai/firma-yorum`, Render API'sine gider â€” `CONFIG.BASE_URL`).
  Backend/endpoint henÃ¼z canlÄ± olmadÄ±ÄŸÄ±ndan buton tÄ±klanÄ±nca hata yakalanÄ±p "yakÄ±nda aktif olacak" gÃ¶steriyor
  (kÄ±rmÄ±zÄ± hata/konsol patlamasÄ± yok â€” local Ã¶nizlemede doÄŸrulandÄ±: free state'te kart doÄŸru render oldu,
  konsol temiz). Migration'lar + Render deploy sonrasÄ± pro kullanÄ±cÄ±yla uÃ§tan uca test edilmeli.

### ğŸŸ¡ Ä°LERLEME D2 (9 Tem 2026, Sonnet â€” kod hazÄ±r, migration bekliyor)

- âœ… **`ihale-detay.html`'e "ğŸ“Š Tahmini Kazanma BandÄ±" kutusu eklendi** (`kazanmaBandiGoster()`):
  sadece aktif+idare+kategori+yaklasik_maliyet_min dolu ihalelerde Ã§alÄ±ÅŸÄ±r. `analiz_pivot('yil',
  p_idare, p_kategori, p_il)` Ã§aÄŸÄ±rÄ±p dÃ¶nen yÄ±l satÄ±rlarÄ±nÄ± ihale_sayisi ile aÄŸÄ±rlÄ±klandÄ±rÄ±p
  ortalama tenzilat Ã§Ä±karÄ±r; toplam emsal <5 ise kutuyu hiÃ§ gÃ¶stermez (plandaki kural). Bant,
  ort. tenzilat Â±8 puan sabit geniÅŸlikle hesaplanÄ±yor (v1 â€” RPC std sapma dÃ¶ndÃ¼rmÃ¼yor, ileride
  `analiz_pivot`'a `stddev_tenzilat` eklenip bant daralt/geniÅŸlet dinamikleÅŸtirilebilir).
  RPC yoksa `console.info` ile sessizce geÃ§er â€” local Ã¶nizlemede aktif bir ihale ile test edildi,
  konsolda sadece bilgi logu var, sayfa (KPI/tab/baÅŸlÄ±k) tamamen saÄŸlam kaldÄ±.
  âš ï¸ **AI aÃ§Ä±klama metni YAPILMADI** (plan: "AI sadece aÃ§Ä±klama metnini yazar") â€” v1 salt istatistik.
  Ä°stenirse D1'deki `firma_ai_yorum.py` deseni tekrarlanarak eklenebilir, dÃ¼ÅŸÃ¼k Ã¶ncelik.
- [ ] ğŸ”´ GeÃ§miÅŸ Ã¶rnek listesi (plan: "+ geÃ§miÅŸ Ã¶rnekleri listele") eklenmedi â€” sadece Ã¶zet bant var,
  alt satÄ±ra "bu idare/kategoride son N sÃ¶zleÅŸme" mini-liste eklenmesi ayrÄ± bir kÃ¼Ã§Ã¼k iÅŸ.

## 10.E FAZ E â€” Ä°STÄ°HBARAT & FARK AÃ‡ICILAR (ihaleciler'i geÃ§tiÄŸimiz yer)

- **E1. Rakip Takibi (9.2.1(c)):** `takip_firmalar` tablosu (kullanici_id, normalize_ad) + firma-analiz'e
  "â­ Rakibi Takip Et" + cron'da yeni sonuÃ§ yazÄ±lÄ±rken takipÃ§ilere `bildirimler` kaydÄ± + bÃ¼lten e-postasÄ±na
  "Rakip hareketleri" bloÄŸu (`bulten_gonder.py` geniÅŸlet). ihaleciler'de bu YOK.
- âœ… **E2 TAMAMLANDI (9 Tem 2026):** `kurum-analiz.html`'in "Kazanan Firmalar" kartÄ±na (Faz C3) yoÄŸunlaÅŸma
  endeksi eklendi â€” ilk 3 firmanÄ±n toplam iÅŸ payÄ± hesaplanÄ±p (â‰¥3 firma + â‰¥5 toplam iÅŸ varsa) renkli bir
  etiketle gÃ¶steriliyor (%60+ kÄ±rmÄ±zÄ± "yÃ¼ksek yoÄŸunlaÅŸma", %35+ amber "orta", altÄ± yeÅŸil "daÄŸÄ±nÄ±k"). RPC
  henÃ¼z uygulanmadÄ±ÄŸÄ±ndan bu kod da C3 ile aynÄ± try/catch iÃ§inde â€” canlÄ± doÄŸrulama migration sonrasÄ±.
- **E3. SEO firma sayfalarÄ±:** `firmalar/<slug>` statik-vari URL'ler (Cloudflare `_redirects` veya SSR-siz
  meta enjeksiyonu) â†’ Google'dan "X firmasÄ± ihale" aramalarÄ± bize gelsin. ihaleciler login duvarÄ±nÄ±n arkasÄ±nda â€”
  biz Ã¶zet kÄ±smÄ± PUBLIC bÄ±rakÄ±p derinliÄŸi PRO yaparsak organik trafiÄŸi alÄ±rÄ±z.
- **E4. KÄ°K kararlarÄ± kaynaÄŸÄ± (madde 3 devamÄ±) â€” 10 Tem'de feasibility test edildi, "sadece Playwright kur"
  yeterli DEÄÄ°L:** VDS'te playwright zaten kurulu + chromium Ã§alÄ±ÅŸÄ±yor (doÄŸrulandÄ±) ama iki ayrÄ± sorun var:
  (1) `kik_backfill.py`'nin hedeflediÄŸi `ekap.kik.gov.tr/EKAP/karar/arama` artÄ±k `ekapv2.kik.gov.tr` ana
  sayfasÄ±na redirect ediyor (200 ama yanlÄ±ÅŸ sayfa) â€” muhtemelen eski portal taÅŸÄ±nÄ±rken bu endpoint kaldÄ±rÄ±ldÄ±/
  taÅŸÄ±ndÄ±, URL gÃ¼ncellenmesi gerekiyor. (2) Alternatif kaynak `www.kik.gov.tr/tr/uyusmazlik-kararlari`
  gerÃ§ek Playwright+chromium ile (gerÃ§ekÃ§i User-Agent/viewport/locale ile bile) hÃ¢lÃ¢ **406** veriyor â€” bu
  basit bir IP engeli deÄŸil, WAF/bot-korumasÄ± (muhtemelen TLS parmak izi/JA3 gibi header-Ã¶tesi sinyaller);
  dÃ¼z `playwright install` bunu aÅŸmÄ±yor. GerÃ§ek Ã§Ã¶zÃ¼m ya (a) doÄŸru gÃ¼ncel endpoint'i bulmak (ekapv2 API'sinde
  bir "karar arama" uÃ§ noktasÄ± olabilir, `ekap_scraper.py`'nin ENDPOINTS deseniyle taranabilir) ya da
  (b) ciddi stealth/proxy altyapÄ±sÄ± (playwright-stealth, residential proxy) â€” ikisi de ayrÄ±, kapsamlÄ± bir iÅŸ.
  DÃ¼ÅŸÃ¼k Ã¶ncelik, launch'Ä± bloklamÄ±yor (sayfa zaten "henÃ¼z senkronize edilmedi" ile zarifÃ§e dÃ¶nÃ¼yor).
  **10 Tem 2026 EK BULGU â€” (a) yolu da denendi, Ã¶lÃ¼ Ã§Ä±ktÄ±:** `ekapv2.kik.gov.tr`'nin kendi minify'lÄ± JS
  bundle'larÄ± statik olarak indirilip (`main.*.js` + 66 lazy-chunk, `curl` ile) "karar" iÃ§in tarandÄ±.
  GerÃ§ek bir `KurulKararlariClient.getKurulKararlari()` (`/api/KurulKararlari/GetKurulKararlari`) bulundu
  â€” ama **kullanÄ±cÄ± onayÄ±yla tek bir test isteÄŸi** atÄ±ldÄ±ÄŸÄ±nda, Ã§alÄ±ÅŸan `b_ihalearama` tabanÄ±nda **404**
  dÃ¶ndÃ¼ (`"Url: /api/KurulKararlari/GetKurulKararlari, Not Found"`) â†’ bu controller farklÄ±/muhtemelen
  iÃ§ bir backend'de duruyor, tahmin edip taramak (`/b_admin` vb.) gÃ¼venlik sÄ±nÄ±flandÄ±rÄ±cÄ±sÄ± tarafÄ±ndan
  haklÄ± olarak engellendi (tek istek onayÄ±nÄ±n kapsamÄ± aÅŸÄ±lÄ±yordu). AyrÄ±ca genel kullanÄ±cÄ± menÃ¼sÃ¼ndeki
  "Kurul KararlarÄ±" linki bizzat uygulamanÄ±n kendi kodunda `externalLink:true` iÅŸaretli â€” yani EKAP'Ä±n
  KENDÄ°SÄ° de normal kullanÄ±cÄ±larÄ± muhtemelen aynÄ± WAF-engelli `www.kik.gov.tr` sayfasÄ±na gÃ¶nderiyor,
  kendi API'sini kullanmÄ±yor. **SonuÃ§: bu gerÃ§ekten "doÄŸru endpoint'i bulamadÄ±k" deÄŸil, "public bir
  API bilerek yok" durumu â€” E4 dÃ¼ÅŸÃ¼k Ã¶ncelikte kalmalÄ±, ciddi stealth/proxy olmadan ilerlemez.**
- **E5. Gazete/Ä°stihbarat kaynaÄŸÄ± (madde 5)** dÃ¼ÅŸÃ¼k Ã¶ncelik: E1-E4 bitmeden BAÅLAMA.

## 10.F Uygulama sÄ±rasÄ± & disiplin (Sonnet iÃ§in)

1. **A1â†’A2â†’A3** (veri olmadan gerisi boÅŸ â€” A3 uzun sÃ¼rer, arka planda cron'la akmaya devam eder; B'ye A'nÄ±n
   KABUL kriterini beklemeden, ilk ~1-2k satÄ±r oluÅŸunca geÃ§ebilirsin)
2. **B1â†’B2â†’B3** â†’ 3. **C1â†’C2â†’C3â†’C4** â†’ 4. **D1â†’D2** (D3/D4 sonra) â†’ 5. **E1â†’E3â†’E4**
- Her migration Ä°KÄ° yere: VDS (`docker exec -i supabase-db psql...`) + managed (Supabase SQL Editor, cutover'a dek).
- Her faz sonunda: commit (TR mesaj, ne yapÄ±ldÄ±ÄŸÄ± net) + bu dosyada ilgili maddeyi âœ…/ğŸŸ¡ iÅŸaretle + dokunulan dosyalarÄ± yaz.
- Frontend deÄŸiÅŸikliklerini tarayÄ±cÄ±da doÄŸrula; RPC'leri Ã¶nce curl/psql ile test et.
- â›” ihaleciler.com'a istek atan HÄ°Ã‡BÄ°R kod yazma. â›” Managed Supabase'e milyonlarca satÄ±r YÃœKLEME (free tier) â€”
  bÃ¼yÃ¼k hacim SADECE VDS'e; managed cutover'a kadar yalnÄ±zca mevcut akÄ±ÅŸla yaÅŸar.

**KonumlandÄ±rma cÃ¼mlesi (pazarlama, D2 sonrasÄ±):** *"ihaleciler sana geÃ§miÅŸi gÃ¶sterir; Ä°haleGlobal kazanmak iÃ§in
kaÃ§ vermen gerektiÄŸini sÃ¶yler."*

---

# 🔵 İHALEPRO ANALİZİ SONUCU İŞ KUYRUĞU (23 Tem 2026)

> Tam envanter: `rakip_analiz_ihalepro.md`. Kullanıcı Chrome'da app.ihalepro.com gezildi (Temel paket).
> ÇARPICI: sonuçta 1.688.002 / sözleşmede 2.945.049 kayıtları var (biz 539K) — fark TARİHSEL derinlik.

## Onaylılar (kullanıcı bu oturumda istedi)
- [ ] 🔴 **2024 ihale SONUÇ backfill** — bizde 2024=6.029, 2023=126.855 (tuhaf çukur). ekap_sonuc_backfill ile 2024'ü doldur; başlangıç/bitiş tarihi + iş süresi alanlarını da TOPLA (aşağıdaki sözleşme maddesinin ön koşulu).
- [ ] 🔴 **Tema: sol flyout alt menüler** (İhalePro tarzı) — üst sekmeler yerine sol menüde ikinci panel: İhaleler→(Aktif/DT), Sonuçlar→(Tümü/Bekleyen/İptal/Sonuçlanan), Sözleşmeler→(Tümü/Biten/Devam Eden), Analiz→(...). Mobil davranışı main.js hamburger ile uyumlu olmalı.
- [ ] 🔴 **Sonuçlar bilgi mimarisi**: "Sonuç Bekleyenler" (süresi geçmiş + sonuç kaydı yok) / "İptal Edilenler" / "Sonuçlananlar" ayrımı — kullanıcının "sonuç > geçmiş olmalı" talebinin çözümü.
- [ ] 🔴 **Sözleşmeler bölümü**: biten / devam eden işler (is_baslama/is_bitis dolunca).

## Bizim veriyle hemen türetilebilir (kazıma yok)
- [ ] 🔴 Firma segmentleri: Parlayan Yıldızlar / Sönen Yıldızlar / İlk Kez Kazananlar / 150Mn+ — ihale_sonuclari'ndan gece MV; analiz sayfasına segment kartları.
- [ ] 🔴 Bugünkü-değer tutarlar (TÜFE çarpanı): sözleşme bedelinin yanında "bugünkü değeri ₺X" (İhalePro'nun 3-değerli gösterimi). TÜİK TÜFE serisi statik tablo.
- [ ] 🟠 Kurumlar sayfasına toplam harcama kolonları (idare_ozet_mv'ye sözleşme toplamı).
- [ ] 🟠 Firma detayına sekmeler: İş Yapılan Kurumlar / Rakipler (co-bidder) / Ortak Girişim / Kullanıcı Notları.
- [ ] 🟠 Takvime ekle (ICS indir) — ihale satırı + detay sayfası.
- [ ] 🟡 Mail ile paylaş (mailto:).

## Yeni veri kaynağı gerektirenler
- [ ] 🟠 **Yasaklı firmalar** (onlarda 17.055): EKAP yasaklılar sorgusu / Resmî Gazete — firma karnesine "yasaklı" rozeti (fesih şeridinin yanına). Kaynak araştırması gerekli.
- [ ] 🟠 **KİK kararları** 120.884: uyuşmazlık + mahkeme + tutanak; kik-kararlari.html iskeleti bizde var, scraper yok (eski madde, önceliği yükseldi).
- [ ] 🟡 İptal edilen ihaleler ayrı listesi (EKAP durum akışından geliyorsa etiketle).

## Yapmayacaklarımız (bilinçli)
- Excel/CSV export (kalıcı yasak) · doküman indirme sinyali ("ilgilendiği ihaleler" — EKAP bu veriyi bize vermiyor)

## 🎨 SAYFA DESENİ DÖNÜŞÜMÜ (23 Tem — kullanıcı onayladı: "sayfaları da değiştireceğiz")
> Hedef desen İhalePro'dan uyarlanır; ihaleler.html + dogrudan-temin.html + sonuç/sözleşme sayfaları ORTAK şablona geçer.
- [ ] 🔴 **Sol filtre sütunu**: akordeon gruplu filtreler (bizde üst grid); altta yapışkan "Filtreyi Uygula" + "Aramayı Kaydet". Mobilde filtre çekmecesi (drawer).
- [ ] 🔴 **Satır accordion önizleme**: satıra tıklayınca detaya gitmeden "Özet Bilgi" + butonlar (Detay · EKAP İlanı · Doküman · Takibe Al · Takvime Ekle ICS · Paylaş). İdare HİYERARŞİSİ özette gösterilir (detsis zincirimiz var).
- [ ] 🔴 **Kolon başlığından sıralama** (tarih ⇅ / bedel ⇅ / il ⇅) — dropdown sort yerine.
- [ ] 🟠 **"Listede Ara"**: mevcut sonuç kümesi içinde anlık ikinci arama kutusu.
- [ ] 🟠 **Global arama çubuğu** (topbar): kapsam dropdown (İhale/DT/Firma/İdare/Sonuç) + tek kutu; Ctrl+K zaten var — kapsamlandır.
- [ ] 🟠 **Kalan gün rozeti** satırda ("Son 47 gün", ≤3 gün kırmızı) — kısmen var, desene standartlaştır.
- [ ] 🟠 Yeni filtreler: **Benzer İş (iş deneyim grubu)** · **Sözleşme Tipi** · **Düzeltme İlanı** · "AI önerilen" toggle (uyum% motorumuza bağlanır).
- [ ] 🟡 Satır "Mail ile paylaş" (mailto:).

## ✅ 23 Tem KULLANICI KARARLARI (AskUserQuestion)
- [x] Karar: sonuç arşivi TÜM geçmiş çekilecek (kullanıcı 2003 istedi; API'nin en eskisi ~2010 — 2010'a kadar çekilecek, 2003-2009 için kaynak yok)
- [ ] 🔴 Tam arşiv backfill zinciri (2024 penceresi bu gece; kalan ~1,5M kayıt sonraki gecelere bölünecek, skip-pencere yöntemiyle)
- [ ] 🔴 Firma segmentleri MV + analiz kartları (Parlayan/Sönen/İlk Kez/150Mn+ — SQL türetme)
- [ ] 🔴 Bugünkü-değer TL (TÜFE çarpan tablosu; sözleşme bedeli yanında "bugünkü ₺X")
- [ ] 🔴 Yasaklı firmalar: kaynak araştır (EKAP yasaklı sorgusu / Resmî Gazete) → firma karnesine rozet

## ✅ 23 Tem GECE — otonom geliştirme turu
- [x] Takvime Ekle (ICS): ihaleler + doğrudan-temin kartlarında 📅 buton (son teklif → .ics + 1 gün önce hatırlatma)
- [x] Listede Ara: ihaleler'de yüklü kartlar içinde anlık istemci filtresi
- [x] 🔴 CANLI HATA: DT `tarih DESC NULLS LAST` indeks yok → misafirde "0 kayıt" (backfill 2M'e çıkarınca patladı) → idx_dt_ilanlari_tarih_nl (4485ms→1,3ms)
- [x] 🔴 CANLI HATA: ilanlar maliyet sıralaması Geçmiş sekmede timeout → idx_ilanlar_maliyet_nl (3s→0,1sn)
- [x] Menü: "Sonuç Bekleyenler"→sekme=gecmis&durum=kapali (gerçek filtre); "İptal Edilenler" kaldırıldı (EKAP'ta iptal statüsü yok)
- [x] Sonuç zinciri kusuru düzeltildi (DT geç biterse 23 saat kaçak → 90dk sabit tavan + 01:45 kesim)
- [x] KARAR: DT 2020-2023 backfill'i durduruldu (2022-2023 dolu, 2023-11/12 checkpoint'te kaldı) → 2024 SONUÇ backfill'ine öncelik (daha değerli, 81K kazanan)

## Firma segmentleri — GECEYE ERTELENDİ (2024 sonuç açığı)
Parlayan/Sönen Yıldızlar YIL-BAZLI karşılaştırma ister; 2024 sonuç verisi eksik (6K)
olduğu için ŞU AN yanıltıcı olur. 2024 sonuç backfill bitince yapılacak. Ölçülen segment
büyüklükleri (mevcut veri): 150Mn+ 4.954 · ilk-kez-1y 12.803 · aktif-1y 35.037 · toplam 82.263.
