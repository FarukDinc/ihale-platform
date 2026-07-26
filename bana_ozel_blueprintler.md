# Bana Ozel — 5 Ozellik Blueprint (26 Tem paralel tasarim turu)


---

## Blueprint 1

Kod tabanını inceledim. Blueprint aşağıda — bizim gerçek tablo/RPC/dosya adlarımızla, mevcut `Takip`/`TakipDT`/`takvimeEkle`/`takipler` altyapısını yeniden kullanacak şekilde.

---

# Ajanda / Takvim Görünümü — Uygulanabilir Blueprint

## Mimari karar (en önemli nokta)
Takip verisi zaten iki yerde: **localStorage birincil** (`Takip.liste()`, `TakipDT.liste()`) + login'liyse **`takipler`/`dt_takipler`** tablolarıyla senkron (`js/takip.js`). İlan tarihleri zaten `ilanlar` tablosunda (`son_teklif_tarihi`, `ihale_tarihi`). Yani takvim **saf frontend özelliği** — `takipte.html`'in bugün yaptığı `ilanlar.in('id', ids)` sorgusunu birebir yeniden kullanır. **MVP için yeni tablo da yeni RPC de GEREKMEZ.** Bu, hem "mevcut altyapıyı yeniden kullan" hem "gerçekçi ol" kısıtına uyar ve proxy havuzu meşgulken (kazıma gerektirmez) hemen çıkar.

---

## 1. VERİTABANI

**MVP: değişiklik yok.** Sorgu PK (`ilanlar.id`) üzerinden `.in()` — mevcut PK indeksi yeterli, statement_timeout riski yok (takip seti kullanıcı başına küçük, ≤ birkaç yüz satır). `son_teklif_tarihi` + `ihale_tarihi` `ilanlar`'da mevcut (ikincisini `backend/migration_etkin_tarih.sql` `i.ihale_tarihi` olarak kullanıyor → gerçek kolon).

**KRİTİK anon doğrulaması** (memory dersi: *sonradan eklenen kolon kolon-GRANT'a girmez → misafirde sayfayı ÖLDÜRÜR*). Takvim misafirde de çalışacaksa (localStorage takibi girişsiz de var), select'te kullanılacak `ihale_tarihi` kolonunun anon GRANT'ında olduğunu deploy öncesi curl'le doğrula:
```
curl -s "https://ihaleglobal.com/rest/v1/ilanlar?select=son_teklif_tarihi,ihale_tarihi&limit=1" -H "apikey: <anon>"
# 200 + gövde  → OK.  401/42501 → ihale_tarihi maskede, misafir dalından ÇIKAR.
```
`idare`/`ekap_id` anon'a KAPALI — misafir select'ine ASLA konmaz (aksi halde 42501 tüm sorguyu düşürür).

**Opsiyonel (kolay, isteğe bağlı):** kullanıcı varsayılan görünüm tercihi:
```sql
ALTER TABLE public.kullanici_profiller ADD COLUMN IF NOT EXISTS ajanda_varsayilan text DEFAULT 'liste';
-- 'liste' | 'takvim'. RLS zaten profil kendi-satır; ek GRANT gerekmez.
```

**Stretch (Büyük efor, ayrı onay) — "yaklaşan ihaleler" ajandası** (takip edilen kurum/firmadan gelecek ilanlar). Bu, kullanıcının takip setinde OLMAYAN ilanları da tarar → `idare IN (...) AND son_teklif_tarihi BETWEEN ...`. Anon 3s / auth 8s sınırında ağırlaşabilir → ifade/kompozit indeks:
```sql
CREATE INDEX IF NOT EXISTS idx_ilanlar_stt_gelecek
  ON public.ilanlar (son_teklif_tarihi)
  WHERE son_teklif_tarihi >= now() - interval '1 day';   -- partial, yalnız açık pencere
-- idare eşleşmesi için mevcut idare normalize indeksinden yararlan (migration_idare_norm_indeks.sql).
```

---

## 2. RPC / BACKEND

**MVP: yeni RPC yok.** `takipte.html`'deki mevcut desen aynen:
```js
sb.from('ilanlar')
  .select(uye
    ? 'id,ekap_id,baslik,idare,il,durum,son_teklif_tarihi,ihale_tarihi,yaklasik_maliyet_min,yaklasik_maliyet_max'
    : 'id,baslik,il,durum,son_teklif_tarihi,ihale_tarihi,yaklasik_maliyet_min,yaklasik_maliyet_max')
  .in('id', Takip.liste());
```
DT için `dogrudan_temin_ilanlari.in('dt_no', TakipDT.liste())` (yine mevcut dar/uye select ayrımıyla).

**Stretch RPC (kurum/firma takibinden yaklaşan)** — mevcut login-gating desenine uygun (SECURITY INVOKER, yalnız authenticated GRANT, anon EXECUTE yok):
```sql
CREATE OR REPLACE FUNCTION public.ajanda_yaklasan(p_bas date, p_bit date)
RETURNS jsonb LANGUAGE sql SECURITY INVOKER STABLE AS $$
  SELECT coalesce(jsonb_agg(x), '[]'::jsonb) FROM (
    SELECT i.id, i.baslik, i.idare, i.il, i.son_teklif_tarihi, i.ihale_tarihi, 'kurum'::text AS kaynak
    FROM ilanlar i
    JOIN takip_idareler t ON t.kullanici_id = auth.uid() AND t.idare_ad = i.idare
    WHERE i.son_teklif_tarihi >= p_bas AND i.son_teklif_tarihi < p_bit
    LIMIT 500                       -- örnekleme/tavan; bulk çekimi engeller
  ) x;
$$;
REVOKE EXECUTE ON FUNCTION public.ajanda_yaklasan(date,date) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.ajanda_yaklasan(date,date) TO authenticated;
```
Güvenlik: SECURITY INVOKER + RLS + `auth.uid()` filtresi → kullanıcı yalnız KENDİ takip ettiği kurumu görür; LIMIT 500 kötüye kullanımı sınırlar; maskeli kolon dönmez (authenticated'ın tablo SELECT'i var).

---

## 3. FRONTEND

**Yerleşim kararı:** yeni tam sayfa AÇMA. İki dokunuş:
- **Birincil:** `C:\ihale_platform\takipte.html` içine **"📋 Liste | 📅 Takvim" görünüm anahtarı** (topbar'a segment toggle). Aynı `tumIlanlar` verisini paylaşır — ikinci fetch yok. `takipte` zaten kenar-menüde (`nav-item active`), yeni menü girişi gerekmez; istersen `#takvim` hash derin-linki.
- **İkincil (Orta efor):** `C:\ihale_platform\dashboard.html`'e "Bu Ay" mini şeridi (yalnız içinde bulunulan ay, tıkla → `takipte#takvim`).
- **Yeni dosya:** `C:\ihale_platform\js\ajanda.js` — CSP nedeniyle **self-contained saf CSS-grid takvim** (7 sütun `display:grid`), dış CDN/lib YOK. `takvimeEkle`'yi (ICS) ve `Takip`/`TakipDT`'yi import eder, yeniden yazmaz.

**UI akışı:**
1. Ay ızgarası: Pzt→Paz başlık, ay içi günler; `‹ Temmuz 2026 ›` gezinme.
2. Her ilan iki işaret bırakabilir: `son_teklif_tarihi` (öncelikli, "Son teklif") + `ihale_tarihi` ("İhale günü") — farklı ikon/nokta.
3. Renk kuralı: yaklaşan (bugün≤tarih) = **`var(--amber)`**, geçmiş = **`var(--muted)` (gri)**; bugün hücresine amber halka.
4. Güne tıkla → altta **gün paneli** açılır: o günün ihale kartları (başlık→`ihale-detay?id=`, durum badge, yaklaşık maliyet, `📅 Takvim` = mevcut `takvimeEkle(id, son_teklif_tarihi)`).

**Tema:** Tüm renkler CSS değişkeni (`--amber`, `--muted`, `--navy-mid`, `--border`) — `theme.js` `data-theme` ile açık/koyu otomatik; sabit hex yok (memory: Chart.js dersi — sabit renk açık temada kaybolur).

**Mobil (<900px):** `.sidebar` zaten gizli. Takvim ızgarası dar ekranda okunmaz → **≤600px'de otomatik "Ajanda listesi" moduna** düş (günlere göre gruplu dikey liste), ızgara `overflow-x:auto` değil, tam yeniden akış. Hücre min-yükseklik + dokunma hedefi ≥40px.

**Türkçe metinler:** "Takvim", "Bu ay son teklif veren ihale yok", "Son teklif: {başlık}", "İhale günü", "Yaklaşan", "Geçti", "‹ Önceki ay / Sonraki ay ›", "Bugün".

---

## 4. GÜVENLİK / GATING

- **Login zorunlu DEĞİL** (mevcut `Takip` ile tutarlı): misafir localStorage takibiyle takvimi görür; `ilanlar` **dar anon select** ile okunur, `idare`/`ekap_id` istenmez → kartta `—`. Kurum/firma takibinden yaklaşanlar (stretch RPC) **yalnız authenticated**.
- **Veri-koruma rasyonu korunur:** CSV/Excel export YASAĞI aynen geçerli. ICS yalnız **tekil etkinlik** (mevcut `takvimeEkle`, politika istisnası "hazırlanan çıktı" ruhunda, tek satır). **"Ayın tamamını .ics indir" gibi toplu export EKLENMEZ** — bu bir toplu-dışa-aktarım vektörü olur; en fazla tek güne kadar sınırlı kal, tercihen tekil.
- **Kötüye kullanım (bulk kazıma):** Takvim yalnız kullanıcının KENDİ takip setini okur (satır sayısı `takipler` kadar sınırlı) — yeni veri yüzeyi açmaz. Stretch RPC'de `auth.uid()` + `LIMIT 500` zorunlu. Anon'a hiçbir yeni RPC/kolon GRANT'ı yok.

---

## 5. UÇ DURUMLAR

- **Boş veri:** Takip yoksa → mevcut `.empty-state` yeniden kullanılır ("İhalelere Git"). Görünen ayda takip varsa ama o ayda tarih yoksa → "Bu ay işaretli ihale yok, ‹ › ile gezin".
- **Çok büyük sonuç:** Kullanıcı 300+ takip → PostgREST `.in()` URL uzunluğu riski; **ids'i ~150'lik parçalara böl**, birleştir (takvim yalnız görünen ayı client-side süzer, hepsini bir kez çeker). Timeout riski yok (PK erişimi).
- **Maskeli anon:** `idare`/`ekap_id` select'e girerse 42501 tüm sorguyu düşürür → misafir dalında ASLA istenmez; deploy öncesi anon curl doğrulaması (bkz. §1).
- **Mükerrer:** Aynı ilan hem `son_teklif` hem `ihale_tarihi` taşırsa → iki AYRI işaret (farklı tip), aynı güne düşerse iki nokta; `(id, tip)` ile dedup. localStorage+DB birleşimi zaten `Set` ile tekilleştiriyor. Tarih `null` → takvime konmaz.
- **Zaman dilimi:** `son_teklif_tarihi` `timestamptz`. Gün hücresine yerleştirirken `new Date(x).getDate()` (yerel) kullan; UTC'ye çevirip gün atlatma. Not: mevcut `takvimeEkle` ICS'te UTC `Z` formatı üretiyor — takvim ızgarasında yerel gün kullan, tutarsızlık yaratma.

---

## 6. EFOR + SIRA

- **Küçük (MVP, ~yarım gün) — sıfır DB/RPC:** `takipte.html` görünüm anahtarı + `js/ajanda.js` self-contained ızgara + gün paneli, mevcut `tumIlanlar` fetch'ini ve `takvimeEkle`'yi yeniden kullan. Renk amber/gri, açık+koyu tema.
- **Orta (+1 gün):** dashboard "Bu Ay" mini şeridi + mobil ajanda-liste modu + DT takiplerini (`TakipDT`) de ızgaraya kat (`dogrudan_temin_ilanlari.tarih`).
- **Büyük (ayrı onay):** `ajanda_yaklasan` RPC (kurum/firma takibinden yaklaşan) + `idx_ilanlar_stt_gelecek` + **bildirim entegrasyonu** (mevcut `yeni_ilan_bildirim_uret`/`bildirim-sayaci.js` deseniyle "yarın son teklif" hatırlatması).

**Bağımlılıklar:** MVP kazıma gerektirmez → proxy havuzu meşguliyeti ENGEL DEĞİL. DB kolonu/indeks/RPC (Orta profil kolonu + Büyük) VDS'te `psql` yazma = **ayrı SSH onayı** (memory: prod-ssh-auto-mode-limits). Frontend deploy = VDS'te `git pull`. CSS/JS 4s cache → `ajanda.js?v=1` ve `takipte.html` script sürüm bump'ı şart.

**Önerilen sıra:** 1) MVP frontend-only çıkar, canlıda misafir+üye anon curl doğrula → 2) gün paneli + DT + mobil → 3) dashboard şeridi → 4) onay alınca stretch RPC+indeks+bildirim.

**İlgili dosyalar:** `C:\ihale_platform\takipte.html`, `C:\ihale_platform\js\takip.js`, `C:\ihale_platform\ihaleler.html` (satır 1185 `takvimeEkle` kaynağı), `C:\ihale_platform\dashboard.html`, `C:\ihale_platform\js\bildirim-sayaci.js`; yeni: `C:\ihale_platform\js\ajanda.js` (+ opsiyonel `C:\ihale_platform\backend\migration_ajanda.sql`).


---

## Blueprint 2

Codebase incelemesi tamam. Gerçek tablo/RPC/dosya adları ve mevcut desenlerle doğrulanmış blueprint aşağıda.

---

# Blueprint — "Takip Listem" Paneli

## 0. Mimari karar (özet)

- **Yeni tablo YALNIZCA `takip_sektorler`** — `takip_firmalar` ve `takip_idareler` zaten CANLI (aynı RLS deseni, `firma-analiz.html:1367` / `kurum-analiz.html:1120` içinden yazılıyor). Sektör için üçüncü ikizi kur.
- **Firma→sözleşme eşleşmesi isim-fold üzerinden.** `ihale_sonuclari.kazanan_firma_fold` zaten `GENERATED ALWAYS AS (tr_fold(kazanan_firma)) STORED` (bkz. `backend/migration_ihale_sonuclari_arama_fold.sql`). Join anahtarı `kazanan_firma_fold = tr_fold(firma_ad)` → `tr_fold` IMMUTABLE olduğu için **bayt-bayt aynı**, doğuştan tutarlı. `yuklenici_id` ile join YAPMA (ihale_sonuclari'nda seyrek dolu; `rakip_bildirim.py` de isimle eşleştiriyor).
- **Bildirim: SIFIRDAN CRON YOK.** `rakip_bildirim.py` (gece cron, `ekap_sonuc_backfill.py`'den sonra) takip edilen firma yeni iş alınca zaten `bildirimler`'e `tur='rakip_hareketi'` + e-posta yazıyor. Bu akış hazır; panel onu görselleştirir.
- **Panel = dashboard bloğu**, tam akış = `takipte.html`'e yeni sekme. Yeni sayfa açma.
- **MV GEREKMEZ.** Kullanıcının takip listesi küçük (onlarca firma); her firma btree index seek. `authenticated` 8s timeout içinde rahat. Tek eksik: `kazanan_firma_fold` üzerinde **eşitlik için btree** (şu an sadece GIN-trgm var → substring için, eşitlik-join için verimsiz).
- **Kısıt notu:** Bu iş DB + RPC + frontend; **kazıma gerektirmiyor** → proxy havuzu meşguliyetinden etkilenmez. Sadece SSH prod-yazma (migration) + cron dokunuşu ayrı onay ister.

---

## 1. VERİTABANI

### 1a. `takip_sektorler` (yeni) — `backend/migration_takip_sektorler.sql`

`takip_idareler` ile birebir desen (service_role GRANT'i baştan koy — `takip_firmalar`'da unutulup 12→21 Tem arası bildirimler sessizce düşmüştü, bkz. `migration_takip_firmalar_service_role_grant.sql`):

```sql
BEGIN;
CREATE TABLE IF NOT EXISTS public.takip_sektorler (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sektor       TEXT NOT NULL,          -- KANONİK kategori (js/kategoriler.js tek kaynağı)
  olusturulma  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kullanici_id, sektor)
);
ALTER TABLE public.takip_sektorler ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "takip_sektorler_kendi_okur" ON public.takip_sektorler;
DROP POLICY IF EXISTS "takip_sektorler_kendi_ekler" ON public.takip_sektorler;
DROP POLICY IF EXISTS "takip_sektorler_kendi_siler" ON public.takip_sektorler;
CREATE POLICY "takip_sektorler_kendi_okur" ON public.takip_sektorler FOR SELECT USING (auth.uid() = kullanici_id);
CREATE POLICY "takip_sektorler_kendi_ekler" ON public.takip_sektorler FOR INSERT WITH CHECK (auth.uid() = kullanici_id);
CREATE POLICY "takip_sektorler_kendi_siler" ON public.takip_sektorler FOR DELETE USING (auth.uid() = kullanici_id);

GRANT SELECT, INSERT, DELETE ON public.takip_sektorler TO authenticated;
GRANT SELECT              ON public.takip_sektorler TO service_role;  -- gece bildirim okur

NOTIFY pgrst, 'reload schema';
COMMIT;
```

**Anon maskeleme:** `anon`'a HİÇ GRANT verme (varsayılan REVOKE). Memory dersi (anon-maske kök-neden A): yeni tablo default-ayrıcalıkla anon-açık DOĞMAZsa iş biter; burada zaten kimse `anon`'a grant etmiyor → güvenli. Yine de deploy sonrası `anon` key ile `curl .../rest/v1/takip_sektorler` → **401 beklenir**, gövdeye bak (HTTP 200 ≠ ifşa dersi).

### 1b. Eşitlik-join için btree indeks — aynı migration dosyasına ekle

```sql
-- kazanan_firma_fold'da yalnız GIN-trgm var (substring için); eşitlik-join yavaş.
CREATE INDEX IF NOT EXISTS idx_sonuc_kazanan_fold_tarih
  ON public.ihale_sonuclari (kazanan_firma_fold, sonuc_tarihi DESC NULLS LAST);
ANALYZE public.ihale_sonuclari;
```

Bu bileşik indeks hem eşitlik-join'i hem akıştaki `ORDER BY sonuc_tarihi DESC`'i tek seek'le karşılar → **keyset sayfalama** mümkün.

### 1c. Kötüye kullanım tavanı (DB trigger — asıl anti-scrape savunması)

Client-side plan tavanı (bkz. §4) bypass edilebilir (INSERT doğrudan PostgREST'e gider). Cömert bir DB tavanı koy:

```sql
CREATE OR REPLACE FUNCTION public.takip_tavan_kontrol() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE n int;
BEGIN
  EXECUTE format('SELECT count(*) FROM public.%I WHERE kullanici_id = $1', TG_TABLE_NAME)
    INTO n USING NEW.kullanici_id;
  IF n >= 500 THEN
    RAISE EXCEPTION 'Takip limiti aşıldı (%).', TG_TABLE_NAME USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER trg_takip_tavan_firma  BEFORE INSERT ON public.takip_firmalar
  FOR EACH ROW EXECUTE FUNCTION public.takip_tavan_kontrol();
-- aynısını takip_idareler + takip_sektorler için de.
```

500 = normal kullanıcıyı hiç etkilemez, toplu-takip-ederek-hepsini-çek saldırısını durdurur.

---

## 2. RPC / BACKEND

İki yeni RPC. İkisi de **SECURITY INVOKER** — `authenticated`'ın `ihale_sonuclari`/`ilanlar`/`takip_*`'te SELECT'i zaten var; RLS `takip_*`'i otomatik kendi satırlarına daraltır (SECURITY DEFINER'a gerek YOK, tam da bu yüzden daha güvenli). `anon`'a EXECUTE verme (login-gating deseni).

### 2a. Panel özeti — `takip_ozet() → jsonb`

```sql
CREATE OR REPLACE FUNCTION public.takip_ozet()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'firma',  (SELECT count(*) FROM public.takip_firmalar  WHERE kullanici_id = auth.uid()),
    'idare',  (SELECT count(*) FROM public.takip_idareler  WHERE kullanici_id = auth.uid()),
    'sektor', (SELECT count(*) FROM public.takip_sektorler WHERE kullanici_id = auth.uid()),
    'yeni_sozlesme_30g', (
      SELECT count(*)
      FROM public.takip_firmalar tf
      JOIN public.ihale_sonuclari s ON s.kazanan_firma_fold = tr_fold(tf.firma_ad)
      WHERE tf.kullanici_id = auth.uid()
        AND s.sonuc_tarihi >= now() - interval '30 days'
    )
  );
$$;
REVOKE ALL ON FUNCTION public.takip_ozet() FROM public, anon;
GRANT EXECUTE ON FUNCTION public.takip_ozet() TO authenticated;
```

### 2b. Firma sözleşme akışı — `takip_firma_sozlesmeleri(p_limit, p_once) → jsonb`

Keyset sayfalama (`sonuc_tarihi < p_once`); OFFSET değil (539K'da OFFSET pahalı — sonuç-backfill'de OFFSET→keyset dersi commit `acc9f27`).

```sql
CREATE OR REPLACE FUNCTION public.takip_firma_sozlesmeleri(
  p_limit int         DEFAULT 30,
  p_once  timestamptz DEFAULT NULL   -- bu tarihten ÖNCEKİ sayfa (keyset imleci)
) RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  WITH takip AS (
    SELECT DISTINCT tr_fold(firma_ad) AS fold, min(firma_ad) AS firma_ad
    FROM public.takip_firmalar
    WHERE kullanici_id = auth.uid()
    GROUP BY tr_fold(firma_ad)          -- İ/ı fold çakışmasını tek satıra indir (mükerrer koruması)
  )
  SELECT COALESCE(jsonb_agg(row_to_json(x)::jsonb ORDER BY x.sonuc_tarihi DESC NULLS LAST), '[]'::jsonb)
  FROM (
    SELECT s.id, s.ilan_id, t.firma_ad AS takip_firma, s.kazanan_firma,
           s.kazanan_teklif, s.sozlesme_bedeli, s.sozlesme_tarihi, s.sonuc_tarihi,
           s.il, s.kategori, s.fesih_var, s.tasfiye_var, s.lot_sayisi,
           i.baslik, i.ikn
    FROM takip t
    JOIN public.ihale_sonuclari s ON s.kazanan_firma_fold = t.fold
    LEFT JOIN public.ilanlar i    ON i.id = s.ilan_id
    WHERE (p_once IS NULL OR s.sonuc_tarihi < p_once)
    ORDER BY s.sonuc_tarihi DESC NULLS LAST
    LIMIT LEAST(p_limit, 50)             -- sert tavan: sayfa başına en çok 50
  ) x;
$$;
REVOKE ALL ON FUNCTION public.takip_firma_sozlesmeleri(int, timestamptz) FROM public, anon;
GRANT EXECUTE ON FUNCTION public.takip_firma_sozlesmeleri(int, timestamptz) TO authenticated;
```

- **Örnekleme/limit:** sayfa başına ≤50, imleç = son satırın `sonuc_tarihi`'si (`p_once`). Frontend "Daha Fazla" ile ilerler.
- **`ilanlar` join LEFT:** eski sonuçların ilan kaydı olmayabilir → satır düşmesin.

### 2c. Sektör bildirimi — mevcut `yeni_ilan_bildirim_uret`'i GENİŞLET (yeni cron yazma)

`backend/migration_bildirim_uret.sql` içindeki `adaylar` CTE'sinde aday kümesini `takip_sektorler` ile birleştir. Mevcut dedup (`NOT EXISTS ... tur='ihale'`) çift bildirimi zaten engeller — bir kullanıcı sektörü hem `profil.sektorler`'de hem `takip_sektorler`'de tutsa bile aynı `ilan_id` iki kez yazılmaz:

```sql
-- adaylar CTE'sine UNION ekle:
UNION
SELECT ts.kullanici_id AS user_id, i.id, i.baslik, i.kategori, i.il, i.idare
FROM public.ilanlar i
JOIN public.takip_sektorler ts ON i.kategori = ts.sektor
WHERE i.durum = 'aktif' AND i.kategori IS NOT NULL
  AND i.olusturulma >= now() - (p_gun * interval '1 day')
  AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi > now())
```

Firma-kazanç bildirimi için **hiçbir şey yazma** — `rakip_bildirim.py` hazır (`tur='rakip_hareketi'`, e-posta şablonu dahil, `aksiyon_url=/firma-analiz?firma=...`). `bildirim-sayaci.js` bunu zaten sayıyor.

**Karar noktası (kullanıcıya):** `takip_sektorler` ile `profil.sektorler` semantik olarak örtüşüyor. Öneri: panel sektör-takibini `takip_sektorler`'e yaz (açık takip semantiği + panel sayacı), bildirimi yukarıdaki UNION'la sağla. `profil.sektorler`'i (profil sayfası filtresi) olduğu gibi bırak.

---

## 3. FRONTEND

### Dosyalar
| Dosya | Değişiklik |
|---|---|
| `C:\ihale_platform\dashboard.html` | KPI kartlarından sonra **"Takip Listem" panel bloğu** (özet + Yeni Ekle + son 5 sözleşme) |
| `C:\ihale_platform\js\takip.js` | `TakipDT` ikizi gibi **`TakipFirma` / `TakipIdare` / `TakipSektor`** nesneleri (firma-analiz/kurum-analiz'deki satır-içi yazımları buraya topla) |
| `C:\ihale_platform\js\api.js` | `takipOzet()`, `takipFirmaSozlesmeleri(limit, once)` RPC sarmalayıcıları |
| `C:\ihale_platform\takipte.html` | Yeni sekmeler: **Firmalar / Kurumlar / Sektörler** + tam sonsuz-akış |
| `C:\ihale_platform\js\kenar-menu.js` | "Takibim" (satır 69) zaten var; flyout alt-öğe "Takip Listem" eklenebilir (opsiyonel) |

### UI akışı (dashboard bloğu)
```
┌─ 🔖 Takip Listem ───────────────────────────── [Tümünü Gör →] ─┐
│  [ 12 Firma ]  [ 4 Kurum ]  [ 3 Sektör ]     ⊕ Yeni Ekle       │
│                                                                 │
│  Takip ettiğim firmaların yeni sözleşmeleri                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🏆 ABC İnşaat A.Ş. — "Okul onarım işi" · 4,2M ₺ · 12 Tem   │ │
│  │ 🏆 XYZ Ltd. — "Temizlik hizmeti" · 1,1M ₺ · 10 Tem         │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```
- **Yeni Ekle** → küçük modal, 3 sekme: Firma ara (mevcut firma arama), Kurum ara, Sektör seç (`js/kategoriler.js` 41 kanonik). Seçim `TakipFirma/İdare/Sektor.toggle()` çağırır → sayaç anında tazelenir.
- **Satır tıklama** → `ihale-detay?id=` (varsa) veya `firma-analiz?firma=`.
- **Reuse `benzer_ihaleler`:** satır altında "Bu işe benzer AÇIK ihaleler →" — takip edilen firmanın kazandığı `ilan_id` ile `benzer_ihaleler` RPC'sini çağırıp cross-sell (mevcut motoru yeniden kullan).
- **Reuse ICS:** takip edilen **kurumların** yaklaşan yeni ilan son-teklif tarihleri için `takvimeEkle` (past sözleşmelerde takvim anlamsız — ICS'i yalnız kurum-takip akışında göster).

### Tema / mobil
- Sadece CSS değişkenleri: `var(--amber)`, `var(--card-bg)`, `var(--muted)`, `var(--navy-mid)`, `var(--border)` → koyu+açık otomatik. Sabit hex kullanma (theme.js `data-theme` dersi).
- Panel grid `repeat(auto-fit, minmax(90px,1fr))`; mobilde sayaçlar alt alta. `dashboard.html` zaten `js/main.js` hamburger + global mobil bloğu kullanıyor.
- CSS/JS 4s cache → `?v` bump şart (`takip.js?v=2` → `?v=3`).

### Türkçe metinler
"Takip Listem" · "Yeni Ekle" · "Tümünü Gör →" · "Takip ettiğim firmaların yeni sözleşmeleri" · "Henüz firma/kurum/sektör takip etmiyorsunuz — eklemek için ⊕ Yeni Ekle" · "Daha Fazla" · "Firma Ara / Kurum Ara / Sektör Seç" · "Bu işe benzer açık ihaleler" · boş-durum: "Takip ettiğiniz firmaların son 30 günde yeni sözleşmesi yok."

---

## 4. GÜVENLİK / GATING

- **Login-gated (ücretli DEĞİL) — temel panel.** Firma/kurum takibi zaten giriş yapan herkese açık (`firma-analiz.html` "Takibe Al"). Panel yeni bir veri yüzeyi açmıyor; `authenticated`'ın `firma-analiz`'de gördüğü aynı sözleşme verisi. Misafir → panel yerine "Giriş yap / Ücretsiz üye ol" CTA'sı (RPC'yi hiç çağırma).
- **Veri-koruma rasyonelinin korunması:**
  - RPC'ler `anon`'a EXECUTE YOK → misafir çağıramaz (401). Anon maskeleme (`***`) devrede olsa da bu yüzeye hiç ulaşmaz.
  - **CSV/Excel export YOK** (tarihsel yasak korunur). Akış yalnız ekranda + keyset sayfalı; "Dışa Aktar" butonu ekleme. İstisna (hazırlanan teklif) burada geçerli değil.
  - Döndürülen alanlar (`kazanan_firma`, `kazanan_teklif`) `authenticated` için zaten görünür → **yeni ifşa yok**.
- **Bulk-kazıma önlemi (katmanlı):**
  1. DB trigger tavanı 500/tablo (§1c) — asıl savunma, bypass edilemez.
  2. RPC sayfa başına ≤50 satır + keyset (tüm tabloyu tek çağrıda çekmek imkânsız).
  3. Origin'de `/rest/v1` **2 r/s** limiti zaten kalıcı (bkz. origin-hardening).
  4. Yalnız **takip ettiğin** firmaların verisi gelir — rastgele firma çekilemez; `firma-analiz` zaten aynı veriyi daha kolay verdiği için bu RPC ek bir kazıma kaldıracı değil.
- **Plan katmanı (UX, sert değil):** `js/plan.js` `isPro()` (plan_kodu `standart`/`kurumsal` = Pro). Free: 10 firma / 5 kurum / 3 sektör; Pro: yüksek limit + "tüm arşiv" derin akış. Tavan aşımında `plan.js` `lockElement` overlay'i ("Pro'ya Geç"). Bu yalnız UX; gerçek sınır DB trigger'ında.

---

## 5. UÇ DURUMLAR

- **Boş veri:** takip yok → sayaç `0` + boş-durum metni + Yeni Ekle CTA. `jsonb_agg` `COALESCE(...,'[]')` ile hep dizi döner (null değil).
- **Çok büyük sonuç:** mega-müteahhit (binlerce sözleşme) takip edilirse → akış keyset LIMIT ≤50, "Daha Fazla". `takip_ozet.yeni_sozlesme_30g` 30-gün penceresiyle + bileşik indeksle sınırlı → 8s timeout riski yok.
- **Maskeli anon:** misafir RPC'yi çağırmaz (CTA gösterilir); çağırsa 401. `takip_sektorler`/`takip_firmalar` anon-GRANT yok → tablo da 401. Deploy sonrası anon-curl ile doğrula (200+`[]` bile değil, tam 401 beklenir).
- **Mükerrer:**
  - Çok-kısımlı ihale → `ihale_sonuclari`'nda aynı `ilan_id` çok satır. `lot_sayisi>1` ise satırda "çok kısımlı" rozeti göster, `kazanan_teklif`'i tekil kısım değeriymiş gibi sunma (tenzilat-çok-lot dersi). Gerekirse akışı `ilan_id`+`kazanan_firma_fold`'da distinct'le.
  - İ/ı fold çakışması / kullanıcının aynı firmayı iki yazımla takibi → RPC'de `GROUP BY tr_fold(firma_ad)` tek satıra indirir.
  - Bildirim tekrarı → mevcut `NOT EXISTS` dedup + `rakip_bildirim.py` `PENCERE_SAAT=20` (24h cron'la örtüşme mükerrerini önler) zaten çözüyor.

---

## 6. EFOR + BAĞIMLILIK + ADIM SIRASI

**Bağımlılıklar:** SSH prod-yazma (migration) ayrı onay · gece cron zincirine dokunuş (`rakip_bildirim.py` zaten kayıtlı; sektör için `yeni_ilan_bildirim_uret` düzenlemesi) · her migration sonunda `NOTIFY pgrst, 'reload schema'`. **Kazıma/proxy bağımlılığı YOK.**

**Efor:**
- **Küçük (~yarım gün):** `takip_sektorler` migration (`takip_idareler`'i kopyala) + btree indeks + dashboard panel özeti (`takip_ozet` RPC + 3 sayaç + Yeni Ekle modalı, `js/kategoriler.js` dropdown).
- **Orta (~1–2 gün):** `takip_firma_sozlesmeleri` RPC + keyset akış + `takipte.html` sekmeleri + `js/takip.js` `TakipFirma/İdare/Sektor` nesneleri + `js/api.js` sarmalayıcılar + `benzer_ihaleler` cross-sell.
- **Büyük (~1 gün + onay):** sektör bildirim UNION'ı (`migration_bildirim_uret.sql` düzenle) + DB tavan trigger + plan-katman limitleri + anon-curl güvenlik doğrulaması.

**Önerilen sıra:**
1. `YAPILACAKLAR.md`'ye işi yaz, tek kuyruktan ilerle (memory kuralı; paralel oturum aynı dosyalara yazıp canlı hata çıkarmıştı).
2. `backend/migration_takip_sektorler.sql` (tablo + btree indeks + tavan trigger) → uygula → **anon-curl 401 doğrula**.
3. `backend/migration_takip_ozet_rpc.sql` (iki RPC) → uygula → authenticated token ile yalnız kendi verisi geldiğini doğrula.
4. Frontend: `js/takip.js` + `js/api.js` + `dashboard.html` paneli + `takipte.html` sekmeleri (`?v` bump).
5. `migration_bildirim_uret.sql` sektör UNION'ı + cron doğrulaması (bir gece bekle, `bildirimler`'de kayıt oluştu mu DB'den kontrol — cron'un `stdout` yutması dersi: DB'den doğrula, script çıktısına güvenme).

**Yeniden kullanılan mevcut altyapı:** `takip_firmalar`/`takip_idareler` tabloları + RLS deseni · `rakip_bildirim.py` (firma-kazanç bildirimi + e-posta, hazır) · `yeni_ilan_bildirim_uret` (sektör bildirimi, genişletilerek) · `bildirim-sayaci.js` · `benzer_ihaleler` RPC · `takvimeEkle` ICS · `js/plan.js` gating · `js/kategoriler.js` kanonik sektörler · `tr_fold`/`kazanan_firma_fold` üretilmiş kolon.


---

## Blueprint 3

Grounding complete. I have confirmed every table/column/RPC/index I'll reference actually exists. Here is the blueprint.

---

# Blueprint — Global Arama Derinleştirme (kapsam sonrası) · İhaleGlobal

> Kapsam yönlendirmesi (İhale/Firma/İdare/Sonuç/Sözleşme dropdown + sonuç sayfasına gitme) #2'de yapılıyor. Bu blueprint yalnız **DERİN** katmanı tasarlar: her kapsam için canlı öneri/autocomplete, Ctrl+K komut paleti, son aramalar, tüm app sayfalarına taşıma, performans.

## 0. Mimari karar ve yeniden kullanım envanteri

Tek cümle: **sıfır yeni kazıma, neredeyse sıfır yeni DB nesnesi.** Öneri altyapısının %90'ı zaten prod'da; tek gerçek yeni backend nesnesi bir dağıtıcı RPC, tek yeni frontend dosyası `js/global-arama.js`.

| İhtiyaç | Zaten VAR (yeniden kullan) | Kanıt |
|---|---|---|
| İhale başlık öneri | `ilanlar.baslik_fold` (generated STORED) + `idx_ilanlar_baslik_fold_trgm2` GIN — **anon'a da GRANT'lı** | `migration_ilanlar_baslik_fold.sql` |
| Firma öneri | `yukleniciler.arama_fold`=tr_fold(ad) + `idx_yukleniciler_arama_fold_trgm` GIN (anon maskeli) | `migration_yukleniciler_arama_fold.sql` |
| İdare öneri | `idare_agac_ara(p_q, p_limit)` RPC — hazır, authenticated-only, tr_fold'lu | `migration_idare_agac_rpc.sql` |
| Sonuç/Sözleşme öneri | `ihale_sonuclari.kazanan_firma_fold` + `idx_ihale_sonuclari_kazanan_firma_fold_trgm` (anon maskeli) | `migration_ihale_sonuclari_arama_fold.sql` |
| TR harf katlama | `tr_fold(text)` IMMUTABLE — frontend `trFold()` ile bayt-bayt aynı | prod |
| Login-gating deseni | REVOKE PUBLIC→anon, GRANT authenticated+service_role + `SET ROLE anon` öz-test | `migration_bulk_rpc_kilit.sql` |
| Kaydedilen arama → bülten | `kayitli_aramalar` (user_id, params jsonb, RLS kendi) + `yeni_ilan_bildirim_uret` + `bildirim-sayaci.js` | `migration_kullanici_kayitlari.sql` |
| Navigasyon komutları (Ctrl+K'da) | `js/kenar-menu.js` içindeki `MENU` ağacı | prod |
| Tema | CSS değişkenleri (`--navy-mid`, `--card-bg`, `--amber`, `--border`, `--muted`, `--off-white`) + `theme.js data-theme` | prod |

---

## 1. VERİTABANI

### 1.1 Yeni kolon/indeks — GEREKMİYOR
İhale, Firma, İdare, Sonuç, Sözleşme kapsamlarının hepsinin katlanmış (`*_fold`) kolonu ve `gin_trgm_ops` indeksi zaten prod'da. Leading-wildcard `LIKE '%terim%'` sorguları bu GIN indekslerinden yürür. **Yeni ADD COLUMN / CREATE INDEX yok.**

Tek istisna (opsiyonel, orta iş): "Sonuç"/"Sözleşme" kapsamında öneriyi `sonuc_tarihi DESC` / `sozlesme_tarihi DESC` ile sıralarken trgm filtresi + sıralama birlikte ~539K satırda 8s'e yaklaşırsa, kısmi yardımcı indeks:
```sql
CREATE INDEX IF NOT EXISTS idx_sonuc_sozlesme_tarih
  ON public.ihale_sonuclari (sozlesme_tarihi DESC NULLS LAST)
  WHERE sozlesme_bedeli IS NOT NULL;
```
Ama önce EXPLAIN ile ölç; trgm+LIMIT 10 büyük olasılıkla indekssiz de ms mertebesinde döner (öneri hiçbir zaman sayfalanmaz).

### 1.2 statement_timeout riski
Öneri sorguları `LIKE '%q%'` (trgm GIN) + `LIMIT ≤10`, sayfalama yok → tekil sorgu birkaç ms. anon 3s / authenticated 8s limitinin çok altında. **MV veya gece REFRESH gerekmez.** İdare kapsamı zaten hazır `idare_hiyerarsi_sayim_mv`'yi kullanan RPC üzerinden gelir.

### 1.3 "Son aramalar" — tablo YOK, localStorage
`kayitli_aramalar` = kalıcı **kayıtlı arama** (bülten üreten filtre seti), farklı bir kavram. "Son aramalar" efemer geçmiş → mevcut `ihale_kayitli_aramalar_v1` localStorage desenini izleyip `ig_son_aramalar_v1` anahtarında, cihaz-yerel, ~10 kayıt cap. Yeni tablo/RLS/yazma-yolu (dolayısıyla yeni suistimal yüzeyi) açmaz.

> Opsiyonel (büyük, cihazlar-arası isteniyorsa): `arama_gecmisi(user_id, kapsam, terim, olusturulma)` — RLS "kendi", anon REVOKE, authenticated CRUD; `migration_kullanici_kayitlari.sql`'i şablon al. Varsayılan öneri: yapma, localStorage yeter.

---

## 2. RPC / BACKEND

Tek dağıtıcı RPC. Frontend'in her kapsam için ayrı endpoint bilmesine gerek kalmaz; Ctrl+K'nın "hepsi" modu tek round-trip olur (2r/s origin limiti için kritik, bkz. §4).

```sql
-- migration_ara_oneri.sql  (idempotent)
CREATE OR REPLACE FUNCTION public.ara_oneri(
  p_kapsam text,                 -- 'ihale'|'firma'|'idare'|'sonuc'|'sozlesme'|'hepsi'
  p_q      text,
  p_limit  integer DEFAULT 8
) RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY INVOKER               -- authenticated'ın tablo SELECT'i devrede; maske authenticated'ta yok
AS $$
DECLARE
  q     text := btrim(coalesce(p_q, ''));
  f     text;
  n     integer := LEAST(GREATEST(coalesce(p_limit, 8), 1), 10);  -- cap 10, enumerasyon freni
  out   jsonb := '[]'::jsonb;
BEGIN
  IF length(q) < 2 THEN RETURN '[]'::jsonb; END IF;   -- min uzunluk: oracle + gürültü freni
  f := '%' || public.tr_fold(q) || '%';

  IF p_kapsam IN ('ihale','hepsi') THEN
    out := out || (
      SELECT coalesce(jsonb_agg(x), '[]'::jsonb) FROM (
        SELECT jsonb_build_object(
                 'tip','ihale', 'id', i.id, 'ana', i.baslik,
                 'alt', concat_ws(' · ', i.il, to_char(i.son_teklif_tarihi,'DD.MM.YYYY')),
                 'url', '/ihale-detay?id=' || i.id) AS x
          FROM public.ilanlar i
         WHERE i.baslik_fold LIKE f
         ORDER BY i.son_teklif_tarihi DESC NULLS LAST
         LIMIT CASE WHEN p_kapsam='hepsi' THEN 3 ELSE n END
      ) s);
  END IF;

  IF p_kapsam IN ('firma','hepsi') THEN
    out := out || (
      SELECT coalesce(jsonb_agg(x), '[]'::jsonb) FROM (
        SELECT DISTINCT ON (y.normalize_ad) jsonb_build_object(
                 'tip','firma', 'id', y.id, 'ana', y.ad,
                 'alt', concat_ws(' · ', y.il,
                          y.toplam_sozlesme_sayisi || ' sözleşme'),
                 'url', '/firma-analiz?firma=' || y.id) AS x,
               y.normalize_ad, y.toplam_ciro
          FROM public.yukleniciler y
         WHERE y.arama_fold LIKE f
         ORDER BY y.normalize_ad, y.toplam_ciro DESC NULLS LAST
      ) d
      ORDER BY d.toplam_ciro DESC NULLS LAST
      LIMIT CASE WHEN p_kapsam='hepsi' THEN 3 ELSE n END );
  END IF;

  IF p_kapsam IN ('idare','hepsi') THEN
    out := out || (          -- hazır idare_agac_ara'yı sarıyoruz, tekrar yazmıyoruz
      SELECT coalesce(jsonb_agg(jsonb_build_object(
               'tip','idare', 'id', a.detsis_no, 'ana', a.ad,
               'alt', concat_ws(' · ', a.ust_ad, a.toplam_ihale || ' ihale'),
               'url', '/kurum-analiz?detsis=' || a.detsis_no)), '[]'::jsonb)
        FROM public.idare_agac_ara(q, CASE WHEN p_kapsam='hepsi' THEN 3 ELSE n END) a );
  END IF;

  IF p_kapsam IN ('sonuc','sozlesme') THEN
    out := out || (
      SELECT coalesce(jsonb_agg(x), '[]'::jsonb) FROM (
        SELECT DISTINCT ON (r.ilan_id) jsonb_build_object(
                 'tip', p_kapsam, 'id', r.id, 'ana', r.kazanan_firma,
                 'alt', concat_ws(' · ', r.il,
                          to_char(coalesce(r.sozlesme_tarihi, r.sonuc_tarihi),'DD.MM.YYYY')),
                 'url', '/ihale-detay?id=' || r.ilan_id) AS x, r.ilan_id
          FROM public.ihale_sonuclari r
         WHERE r.kazanan_firma_fold LIKE f
           AND (p_kapsam <> 'sozlesme' OR r.sozlesme_bedeli IS NOT NULL)
           AND (r.lot_sayisi = 1 OR r.lot_sayisi IS NULL)   -- çok-lot mükerrerini at
         ORDER BY r.ilan_id, coalesce(r.sozlesme_tarihi, r.sonuc_tarihi) DESC NULLS LAST
      ) s
      LIMIT n );
  END IF;

  RETURN out;
END;
$$;

-- Login-gating (bulk_rpc_kilit deseni): PUBLIC'ten de REVOKE ŞART
REVOKE EXECUTE ON FUNCTION public.ara_oneri(text,text,integer) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.ara_oneri(text,text,integer) FROM anon;
GRANT  EXECUTE ON FUNCTION public.ara_oneri(text,text,integer) TO authenticated, service_role;
NOTIFY pgrst, 'reload schema';

-- Öz-test (bulk_rpc_kilit'teki gibi): anon reddedilmeli
SET ROLE anon;
DO $$ BEGIN
  BEGIN PERFORM public.ara_oneri('firma','test',5);
    RAISE EXCEPTION 'HATA: anon ara_oneri calistirabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: anon reddedildi'; END;
END $$;
RESET ROLE;
```

**Güvenlik modeli:** `SECURITY INVOKER` → authenticated rolünün tablo SELECT'i geçerli (maske authenticated'ta uygulanmaz, doğru davranış). anon EXECUTE yok → misafir bu RPC'ye hiç ulaşamaz, isim ifşası imkânsız. `firma`/`sonuc`/`sozlesme` içinde maskeli kolonlar okunuyor ama yalnız authenticated çağırdığı için sorun yok — anon maske dersindeki "view sahip-yetkisiyle çalışır" tuzağına düşmez çünkü bu bir view değil, INVOKER fonksiyon.

**Örnekleme/limit:** `n = LEAST(GREATEST(p_limit,1),10)`, min uzunluk 2, sayfalama/cursor YOK → tek çağrıda en çok 10 satır, sistematik enumerasyon yolu kapalı.

---

## 3. FRONTEND

### 3.1 Dosyalar
- **YENİ `js/global-arama.js`** — özelliğin tamamı: gövdeye eklenen fixed overlay (Ctrl+K paleti) + kenar rayına arama ikonu + debounce'lu öneri + localStorage son aramalar. Kendi kendini mount eder (kenar-menu.js deseni).
- **DÜZENLE `js/kenar-menu.js`** — iki satır: (a) rayın en üstüne (logo altına) bir `ara` ikonu ekle; tıklama `window.igAramaAc()` çağırır. (b) `mont()` sonunda `<script src="/js/global-arama.js?v=1">` enjekte et → kenar-menu.js zaten 24 app sayfasında yüklü olduğundan özellik **tek dosyaya dokunarak** tüm sayfalara yayılır. Yeni HTML sayfası veya 24 sayfaya script eklemek YOK.
- **DÜZENLE `js/main.js`** — mobil hamburger başlığına arama ikonu; aynı `window.igAramaAc()`'i çağırır (kenar-menu <900px gizli).
- **Yeni sayfa YOK.** Enter → sonuç sayfası = feature #2'nin yönlendirmesi (`/ihaleler?ara=`, `/firma-analiz?ara=` vb.).

### 3.2 UI akışı
1. Tetikleyici: raydaki ara ikonu, mobil başlıktaki ikon, veya global **Ctrl/Cmd+K**.
2. Ekran ortasında overlay: üstte kapsam dropdown (İhale/Firma/İdare/Sonuç/Sözleşme) + tek input (feature #2 ile aynı sözleşme). Kapsam seçili değilse **hepsi** modu.
3. Yazınca **300ms debounce + AbortController** (uçuştaki isteği iptal) → `sb.rpc('ara_oneri', {p_kapsam, p_q, p_limit:8})`. Sonuçlar `tip` rozetiyle listelenir (İhale/Firma/İdare/Sonuç/Sözleşme etiketi + `ana` + gri `alt`).
4. Input boşken: **"Son aramalar"** (localStorage `ig_son_aramalar_v1`) + `kenar-menu.js`'nin `MENU` ağacından türetilmiş **navigasyon komutları** ("İdareler'e git", "Rekabet Analizi'ne git" — sıfır maliyet, ağaç zaten var).
5. Klavye: ↑/↓ gez, Enter seçili önerinin `url`'ine git (yoksa feature #2 sonuç sayfasına yönlendir + terimi `ig_son_aramalar_v1`'e yaz), Esc kapat.
6. Her öneri satırında sağda küçük "Kaydet" → `kayitli_aramalar`'a insert (`params` jsonb) → mevcut bülten (`yeni_ilan_bildirim_uret`) bu kayıtlı aramayı zaten işliyor. Sıfırdan bildirim yazmıyoruz.

### 3.3 Tema / mobil / metinler
- Overlay tamamen CSS değişkeni: `background:var(--navy-mid)`, kart `var(--card-bg)`, kenar `var(--border)`, aktif satır `rgba(240,165,0,.14)`+`var(--amber)`, ikincil metin `var(--muted)`. `theme.js` `data-theme`'i kökte çevirdiği için açık+koyu otomatik; ekstra tema kodu yok. CSS/JS 4s cache → `?v=1` bump ŞART.
- Mobil: overlay `position:fixed; inset:0` tam ekran → mobilde de çalışır. Ctrl+K masaüstü; mobilde başlık ikonu. Rayın kendisi <900px zaten gizli.
- Türkçe metinler: placeholder **"İhale, firma, idare, sonuç ara…  ⌘K"**; boş durum başlığı **"Son aramalar"**; sonuç yok **"Sonuç bulunamadı — Enter ile tümünde ara"**; misafir teaser **"Canlı firma/idare önerileri üyelere özel · Giriş yap"**.

---

## 4. GÜVENLİK / GATING

- **Login-gated (ücretli DEĞİL).** Arama bir navigasyon aracı, toplu veri değil; tüm authenticated kullanıcılara açık. `ara_oneri` anon'a kapalı (RPC deseni). Ücretli kapı (plan_kodu='standart') gereksiz ve dönüşümü kırar. (Export'un bilerek açılması ayrı konu; burada export yok.)
- **Misafir yolu, veri-koruma rasyonelini korur:** anon `ara_oneri`'yi çağıramaz. Ama `ilanlar.baslik_fold` zaten anon'a GRANT'lı (başlık kimlik verisi değil) → misafire yalnız **İhale-başlık** önerisi, doğrudan PostgREST ile verilebilir: `sb.from('ilanlar').select('id,baslik').ilike('baslik_fold', tr_fold(q)...)`. Firma/İdare/Sonuç kapsamlarında misafire teaser + giriş kapısı. İsim ifşası (idare/kazanan/firma) hiçbir yolla anon'a sızmaz — arama_fold/kazanan_firma_fold anon maskeli, RPC anon'a kapalı.
- **Bulk-kazıma önlemi:** (a) RPC'de `LIMIT ≤10`, cursor/sayfalama yok → çıktı tavanlı; (b) min uzunluk 2; (c) client 300ms debounce + AbortController → yalnız son istek gider; (d) origin'de `/rest/v1` **2 r/s** limiti (hafıza: origin-hardening) `/rest/v1/rpc/ara_oneri`'yi de kapsar. **Etkileşim uyarısı:** debounce'suz autocomplete bu 2r/s'ye takılır → 300ms debounce + iptal ZORUNLU. Gerekirse nginx'te `rpc/ara_oneri` için ayrı, biraz daha yüksek bir lane; ama önce debounce ile ölç.
- Enumerasyon oracle'ı: top-N + sayfalama yok + isim RPC'si login'li olduğundan, sistematik "tüm firmaları dök" yolu yok (bu tam olarak `bulk_rpc_kilit`'in kapattığı senaryonun küçük hali).

---

## 5. UÇ DURUMLAR

- **Boş sorgu / <2 karakter:** RPC `[]` döner; UI "Son aramalar" + navigasyon komutları gösterir.
- **Sonuç yok:** "Sonuç bulunamadı — Enter ile tümünde ara" + feature #2 sonuç sayfasına yönlendirme.
- **Çok büyük eşleşme:** öneri hiçbir zaman >10 döndürmez; altta "Tümünü gör (Enter)" satırı tam sonuç sayfasına götürür.
- **Maskeli anon:** `ara_oneri` 42501/erişim yok; UI yakalar → İhale-başlık önerisi (anon-granted `baslik_fold`) + diğer kapsamlarda giriş teaser'ı. `-o /dev/null` yanılgısına düşmeden gövdeye bakılır (HTTP 200 ≠ ifşa dersi): burada 200+`[]` = RLS/GRANT koruyor.
- **Mükerrer:** İhale — `ekap_ihale_id`/`id` ile tekil (öneride başlık zaten tekil kayıt). Firma — `DISTINCT ON (normalize_ad)`, en yüksek ciroyu tut. Sonuç/Sözleşme — `DISTINCT ON (ilan_id)` + `lot_sayisi=1 veya NULL` filtresi (çok-lotta aynı ihalenin tekrarını eler; tenzilat-çok-lot dersiyle tutarlı).
- **TR harf:** her yerde `tr_fold` (İ/ı ilike sessiz-0 tuzağı); frontend `trFold()` ile bayt-bayt aynı olduğundan eşleşme paritesi korunur.
- **Bayat token/oturum:** öneri çağrısı supabase-js `sb.rpc` ile gider (canlı oturum); `api.js` deseninde 401 → login. Overlay her sayfada olduğundan `window.supabase` yüklü değilse ikon pasif (graceful).

---

## 6. EFOR ve ADIM SIRASI

**Boyut:** Küçük-Orta. Ağır iş (fold kolonları + trgm indeksler + idare arama RPC) zaten bitmiş.

- **Küçük:** İdare kapsamı (`idare_agac_ara` sarma), İhale/Firma/Sonuç önerileri (mevcut indeksler), son aramalar (localStorage).
- **Orta:** `ara_oneri` RPC + grant + öz-test; `global-arama.js` overlay + Ctrl+K + debounce/abort; kenar-menu enjeksiyonu.
- **Büyük (opsiyonel, önerilmez):** cihazlar-arası `arama_gecmisi` tablosu; "hepsi" sıralama ince ayarı.

**Bağımlılıklar:** `baslik_fold`/`arama_fold`/`kazanan_firma_fold` + trgm indeksler (HEPSİ VAR), `idare_agac_ara` (VAR), `tr_fold` (VAR), `kayitli_aramalar`+`yeni_ilan_bildirim_uret` ("Kaydet" için, VAR), feature #2 sonuç-sayfası yönlendirmesi (Enter hedefi). **Kısıt:** RPC deploy'u SSH prod yazma = ayrı onay; proxy havuzları meşgul ama bu özellik hiç kazıma başlatmaz.

**Önerilen sıra:**
1. `backend/migration_ara_oneri.sql` yaz → psql ile uygula (SSH yazma onayı iste) → anon öz-testi yeşil, `NOTIFY pgrst`.
2. `js/global-arama.js` — overlay + öneri + debounce/abort + localStorage; **önce yalnız `ihaleler.html`'de pilot** (kenar-menu.js'in yaptığı gibi), 2r/s ile birlikte ölç.
3. Onay sonrası `js/kenar-menu.js`'e ray ikonu + script enjeksiyonu → 24 sayfaya yayılır; `?v` bump.
4. `js/main.js` mobil arama ikonu (parite).
5. Misafir yolu: anon İhale-başlık önerisi (doğrudan PostgREST) + teaser.
6. Opsiyonel: öneri satırında "Kaydet" → `kayitli_aramalar` + mevcut bülten entegrasyonu.

**Dokunulan dosyalar:** `backend/migration_ara_oneri.sql` (yeni), `C:\ihale_platform\js\global-arama.js` (yeni), `C:\ihale_platform\js\kenar-menu.js` (2 satır), `C:\ihale_platform\js\main.js` (1 ikon). Yeni HTML sayfası, yeni tablo, yeni indeks, yeni kazıma: **yok.**


---

## Blueprint 4

Blueprint hazır. Kod tabanını gerçek tablo/RPC/dosya adlarıyla doğruladım; aşağısı doğrudan uygulanabilir plandır.

---

# Blueprint — "Benim Firmam → Kişisel Eşleşme"

Doğrulama notu: Aşağıdaki her nesne canlı şemayla teyit edildi. **Yeniden kullanılan hazır altyapı:** `benzer_ihaleler` / `ihaleye_uygun_firmalar` / `ihale_konu_kelimeleri` RPC'leri (`backend/migration_uygun_firmalar_v3.sql` + `_v3_1.sql`), `yukleniciler` firma-autocomplete deseni (`firma-analiz.html:1186`), `takip_firmalar` RLS deseni, `bildirimler` + `yeni_ilan_bildirim_uret` üretici deseni, `js/plan.js` (isPro/lockElement/getPlanKod), `tr_fold` + `idx_ilanlar_baslik_fold_trgm` GIN trigram indeksi, ICS `takvimeEkle`.

**Kök tasarım kararı:** `benzer_ihaleler` TEK bir kaynak `ilan_id`'den beslenir — firmanın onlarca geçmiş kazanımı yok. Bu yüzden firmanın kazanım *profilini* (kategori + il + ölçek bandı + konu kelimeleri) toplayıp aktif ilanlarla eşleştiren **yeni bir aggregate RPC** gerekiyor; ama içini sıfırdan yazmadan mevcut `ihale_konu_kelimeleri`, trigram indeksi, ±%500 bant mantığı ve `durum='aktif' AND son_teklif>=now()` filtresini yeniden kullanıyoruz.

---

## 1) VERİTABANI

### 1a. Kalıcı firma seçimi — `kullanici_profiller.firma_id`
`kullanici_profiller.id = auth.uid()` (RLS teyitli). **Kritik boşluk:** tabloda yalnız SELECT policy'si var (`profil_sadece_kendi_okur`, `migration_kullanici_profiller_rls_sikilastir.sql`) — UPDATE policy'si YOK, yani kullanıcı PostgREST'ten firma_id yazamaz. İki çözüm; **RPC yolunu (1c) öneriyorum** (geniş UPDATE grant'ından kaçınır).

```sql
-- backend/migration_firmam_eslesme.sql
ALTER TABLE public.kullanici_profiller
  ADD COLUMN IF NOT EXISTS firma_id     uuid REFERENCES public.yukleniciler(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS firma_secildi timestamptz;

-- ihale_sonuclari.yuklenici_id üzerinde İNDEKS YOK (yalnız yuklenici_ad text indeksi var,
-- migration_sonuc_schema.sql:51) → firma profili çıkarımı 539K satırda seq scan = timeout riski.
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_yuklenici_id
  ON public.ihale_sonuclari (yuklenici_id);
```

### 1b. RLS + GRANT + anon maskeleme
- `firma_id` `kullanici_profiller`'de → mevcut "yalnız kendi satırını okur" RLS'i firma_id'yi de kapsar; **anon zaten tüm tablodan REVOKE'lu**, ek maskeleme gerekmez.
- Firmanın adı (`yukleniciler.ad`/`arama_fold`) anon'a **zaten '***'** (`migration_anon_maske.sql:65`); kullanıcı giriş yaptığı için görür. Kolon maskesine dokunma.

### 1c. Yazma yolu — SECURITY DEFINER RPC (geniş UPDATE grant'ı yerine)
```sql
CREATE OR REPLACE FUNCTION public.firmami_belirle(p_yuklenici_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'giris gerekli'; END IF;
  -- Yalnız gerçek bir yüklenici id'si kabul et (çöp id ile FK/enumerasyon engeli)
  IF NOT EXISTS (SELECT 1 FROM public.yukleniciler WHERE id = p_yuklenici_id) THEN
    RAISE EXCEPTION 'firma bulunamadi';
  END IF;
  UPDATE public.kullanici_profiller
     SET firma_id = p_yuklenici_id, firma_secildi = now()
   WHERE id = auth.uid();               -- yalnız KENDİ satırı
END; $$;
REVOKE EXECUTE ON FUNCTION public.firmami_belirle(uuid) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmami_belirle(uuid) TO authenticated, service_role;
```
(Alternatif: kolon-seviyeli `GRANT UPDATE(firma_id) ON kullanici_profiller TO authenticated` + `FOR UPDATE USING(auth.uid()=id)` policy — ama RPC daha temiz ve doğrulama yapar.)

### 1d. statement_timeout riski + MV çözümü
Çoğu firmada `idx_ihale_sonuclari_yuklenici_id` ile profil çıkarımı ms sürer. Ama **150mn segment** firmaları binlerce satır → authenticated 8s kenarına yaklaşabilir. Bilinen reçete (bkz. memory: MV + gece REFRESH): profili önden hesaplayan hafif MV, gece cron'da tazelenir. İlk sürümde opsiyonel; EXPLAIN >2s gösterirse aç:

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS public.firma_profil_mv AS
SELECT s.yuklenici_id,
       (array_agg(DISTINCT i.kategori) FILTER (WHERE i.kategori IS NOT NULL))          AS kategoriler,
       (array_agg(DISTINCT i.il)       FILTER (WHERE i.il IS NOT NULL))                AS iller,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli)) AS medyan_bedel,
       max(COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))                               AS max_bedel,
       count(*)                                                                        AS kazanim
FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id = s.ilan_id
WHERE s.yuklenici_id IS NOT NULL
GROUP BY s.yuklenici_id;
CREATE UNIQUE INDEX ON public.firma_profil_mv (yuklenici_id);
REVOKE SELECT ON public.firma_profil_mv FROM anon;   -- yeni MV varsayılan anon-açık doğar (memory: A maddesi)
GRANT  SELECT ON public.firma_profil_mv TO authenticated, service_role;
```
Gece `run_scraper.sh` sonuna `REFRESH MATERIALIZED VIEW CONCURRENTLY public.firma_profil_mv;` — `yuklenici_ozet`/`yuklenici_segment_yenile` zaten orada koşuyor, aynı zincire eklenir.

---

## 2) RPC / BACKEND

### 2a. Ana eşleşme RPC'si — `firma_icin_acik_ihaleler`
Firmanın kazanım profilini toplar, aktif ilanlarla eşleştirir. `ihaleye_uygun_firmalar` v3'ün **tersi yönü**: firma→ihale. Aynı bant + konu-kelimesi + trigram indeksi mantığını kullanır.

```sql
CREATE OR REPLACE FUNCTION public.firma_icin_acik_ihaleler(
  p_yuklenici_id uuid,
  p_limit        int     DEFAULT 12,
  p_bant         numeric DEFAULT 5      -- ölçek bandı ±%500
)
RETURNS TABLE (
  id                   uuid,
  baslik               text,
  idare                text,            -- authenticated-only RPC → idare döndürmek güvenli
  il                   text,
  kategori             text,
  yaklasik_maliyet_min numeric,
  yaklasik_maliyet_max numeric,
  tahmini_bedel        numeric,
  son_teklif_tarihi    timestamptz,
  skor                 numeric,
  eslesme_nedeni       text             -- "Aynı kategoride 14 kazanım · aynı il" gibi rozet metni
)
LANGUAGE sql STABLE AS $$
  WITH firma AS (   -- profil: firma_profil_mv varsa oradan, yoksa canlı topla
    SELECT
      (SELECT array_agg(k) FROM (
         SELECT i.kategori k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL
         GROUP BY i.kategori ORDER BY count(*) DESC LIMIT 5) t)          AS kategoriler,
      (SELECT array_agg(DISTINCT i.il) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.il IS NOT NULL)       AS iller,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))
         FROM public.ihale_sonuclari s WHERE s.yuklenici_id=p_yuklenici_id) AS bedel
  )
  SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
         i.yaklasik_maliyet_min::numeric, i.yaklasik_maliyet_max::numeric, i.tahmini_bedel::numeric,
         i.son_teklif_tarihi::timestamptz,
         round(
           (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 40 ELSE 0 END)
         + (CASE WHEN i.il = ANY(f.iller) THEN 15 ELSE 0 END)
         + (CASE WHEN f.bedel IS NULL OR f.bedel<=0 THEN 0
                 ELSE 20*(1 - LEAST(abs(ln(GREATEST(
                        COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0),1),1)/f.bedel))/ln(p_bant),1)) END)
         , 1)                                                              AS skor,
         (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 'Uzmanlık alanınız'
               ELSE 'Benzer konu' END
          || CASE WHEN i.il = ANY(f.iller) THEN ' · daha önce iş aldığınız il' ELSE '' END) AS eslesme_nedeni
  FROM public.ilanlar i, firma f
  WHERE i.durum='aktif'
    AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
    -- KONU ŞART: firmanın kategorisi VEYA firmanın kazanım başlıklarından çıkan konu kelimesi
    AND ( i.kategori = ANY(f.kategoriler)
       OR EXISTS (
            SELECT 1 FROM public.ihale_konu_kelimeleri(
              (SELECT string_agg(i2.baslik,' ') FROM public.ihale_sonuclari s2
                 JOIN public.ilanlar i2 ON i2.id=s2.ilan_id
               WHERE s2.yuklenici_id=p_yuklenici_id LIMIT 50)) t
            WHERE tr_fold(i.baslik) LIKE '%'||t.kelime||'%') )   -- idx_ilanlar_baslik_fold_trgm
    -- ÖLÇEK BANDI ŞART (±%500) — dayanaksız/alakasız eşleşme spam'ini keser
    AND (f.bedel IS NULL OR f.bedel<=0
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0)) IS NULL
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0))
         BETWEEN f.bedel/p_bant AND f.bedel*p_bant)
  ORDER BY skor DESC, i.son_teklif_tarihi ASC NULLS LAST
  LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) TO authenticated, service_role;
NOTIFY pgrst, 'reload schema';
```
- **Güvenlik modeli:** SECURITY INVOKER (authenticated'ın her iki tabloda SELECT'i var, `migration_anon_maske.sql`). anon REVOKE. `ihaleye_uygun_firmalar` v3 ile aynı desen.
- **Örnekleme/limit:** `p_limit` (blok için 12, bildirim için sınırsız). Konu-kelime alt sorgusu firmanın 50 kazanımından string_agg ile beslenir (büyük firmada bounded).
- **Firma-detay için mevcut `yuklenici_ozet`/`firma_segment_listesi`** rozet kartında yeniden kullanılır (firma başlığı + toplam ciro/sözleşme).

### 2b. Sertleştirilmiş dashboard varyantı (opsiyonel, anti-enumerasyon)
Dashboard'un kalıcı çağrısı için firma id'yi client'tan almayan sürüm:
```sql
CREATE OR REPLACE FUNCTION public.firmam_acik_ihaleler(p_limit int DEFAULT 12)
RETURNS SETOF public.firma_icin_acik_ihaleler  -- aynı satır tipi
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public AS $$
  SELECT * FROM public.firma_icin_acik_ihaleler(
    (SELECT firma_id FROM public.kullanici_profiller WHERE id=auth.uid()), p_limit, 5);
$$;
```
Kayıtlı firma yoksa boş döner → onboarding teaser tetikler.

### 2c. Firma autocomplete — YENİ RPC GEREKMEZ
`firma-analiz.html:1186` deseni birebir kullanılır: `sb.from('yukleniciler').select('id,ad,il,toplam_sozlesme_sayisi,toplam_ciro').ilike('arama_fold','%'+trFold(term)+'%').limit(10)`, fallback `.ilike('ad',...)`. `arama_fold` anon-maskeli ama özellik login-gated → üye görür. **Tek gereksinim:** `yukleniciler.arama_fold` üzerinde `gin_trgm_ops` indeksi olduğunu doğrula (1M+ firmada substring ilike için); yoksa `CREATE INDEX ... USING gin (arama_fold gin_trgm_ops)` ekle.

### 2d. Bildirim üretici — `firma_uygun_bildirim_uret`
`yeni_ilan_bildirim_uret` (`migration_bildirim_uret.sql`) birebir şablon. Canlı `bildirimler` şeması: `kullanici_id, baslik, icerik, tur, ilan_id, aksiyon_url, okundu, olusturulma` (üretici gövdesindeki kolonlar — CREATE TABLE'daki eski şema değil).
```sql
CREATE OR REPLACE FUNCTION public.firma_uygun_bildirim_uret(p_gun int DEFAULT 1)
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path=public AS $$
DECLARE eklenen int;
BEGIN
  WITH adaylar AS (
    SELECT kp.id AS user_id, m.id AS ilan_id, m.baslik, m.kategori, m.il
    FROM public.kullanici_profiller kp
    CROSS JOIN LATERAL public.firma_icin_acik_ihaleler(kp.firma_id, 20, 5) m
    WHERE kp.firma_id IS NOT NULL
  ), yeni AS (
    INSERT INTO public.bildirimler (kullanici_id,baslik,icerik,tur,ilan_id,aksiyon_url,okundu,olusturulma)
    SELECT a.user_id, 'Firmanıza uygun yeni ihale: '||left(a.baslik,60),
           a.kategori||COALESCE(' · '||a.il,''), 'ihale', a.ilan_id,
           'ihale-detay?id='||a.ilan_id, false, now()
    FROM adaylar a
    WHERE NOT EXISTS (SELECT 1 FROM public.bildirimler b
      WHERE b.kullanici_id=a.user_id AND b.ilan_id=a.ilan_id AND b.tur='ihale')
    RETURNING 1)
  SELECT count(*) INTO eklenen FROM yeni; RETURN eklenen;
END; $$;
REVOKE ALL ON FUNCTION public.firma_uygun_bildirim_uret(int) FROM public, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.firma_uygun_bildirim_uret(int) TO service_role;
```
Gece cron'da scraper'lardan + `ilan_durum_bayatlat`'tan SONRA. **Frontend bildirim tarafı sıfır değişiklik** — `bildirim-sayaci.js` rozeti + `dashboard.html` notif-dropdown zaten `bildirimler` okuyor.

---

## 3) FRONTEND

**Değişen dosyalar:** `dashboard.html` (blok + JS), yeni `js/firmam.js` (autocomplete + seçim + eşleşme render — tek modül), opsiyonel `js/kenar-menu.js` (mevcut `id:'firmam'` flyout'una satır).

**Neden ayrı sayfa değil, dashboard bloğu:** özellik "dashboard'da firmasını seçsin" diyor; `benzer_ihaleler` kutusu zaten `ihale-detay`'da var — burada firma-merkezli hero blok. Kenar-menüde `Firmam` grubu (`kenar-menu.js:67`) zaten mevcut; oraya `{ ad:'Firma Eşleşmelerim', href:'dashboard#firmam' }` eklenir.

**UI akışı:**
1. Dashboard header'ın (`Merhaba …`) hemen altına, `dash-mod-wrap`'ten önce büyük blok.
2. **firma_id yoksa (onboarding teaser):** amber kenarlı kart —
   Başlık: **"Firmanızı belirleyin, size özel ihaleleri getirelim"**
   Alt: *"Firmanızı seçin; geçmiş kamu kazanımlarınıza benzeyen açık ihaleleri otomatik bulalım."*
   İçinde autocomplete input (`placeholder="Firma adı ara…"`) + seçince `firmami_belirle` RPC → `localStorage`'a firma_id cache + bloğu yeniden render.
3. **firma_id varsa:** başlık **"Sizin İçin Katılabileceğiniz İhaleleri Bulduk"** + firma adı rozeti (`yuklenici_ozet`) + "Firmayı değiştir" linki. Altında `firmam_acik_ihaleler(12)` kartları: her kart = başlık, idare, il, kategori çipi, yaklaşık maliyet (**`tufe.js` bugünkü-değer** ile), son teklif geri sayımı, `eslesme_nedeni` rozeti, **"Takvime Ekle"** (mevcut `takvimeEkle` ICS), **"Takip Et"** (mevcut `js/takip.js`), "Detay →" (`ihale-detay?id=`).
4. Boş sonuç → *"Firmanızın profiline uyan açık ihale şu an yok. Yeni ihale gelince bildireceğiz."* (bildirim zaten kurulu).

**Tema/mobil:** Mevcut CSS değişkenleri (`var(--navy-mid)`, `var(--amber)`, `var(--border)`, `var(--white)`, `var(--muted)`) → `data-theme` ile açık/koyu otomatik. Kart grid'i mevcut `stat-card` deseniyle `grid-template-columns:repeat(auto-fit,minmax(...))` → mobilde tek sütun. Hepsi Türkçe.

---

## 4) GÜVENLİK / GATING

- **Login-gated (zorunlu):** `firmami_belirle`, `firma_icin_acik_ihaleler`, `firmam_acik_ihaleler` → anon REVOKE, authenticated GRANT. Misafir yalnız teaser başlığını görür, autocomplete/eşleşme çalışmaz (arama_fold anon-maskeli, RPC anon'a kapalı).
- **Ücretli katman (öneri, zorunlu değil):** Blok tüm üyelere açık; **ilk 3 kart bedava, tam liste + gece bildirimi Pro'ya kilitli** → `js/plan.js` `isPro()` + `lockElement()` (mevcut `.pro-lock-overlay` deseni). Bu, ücretli değeri korur ama export yasağını hiç ihlal etmez.
- **Veri-koruma rasyonu korunur:** RPC **CSV/Excel üretmez, ekran-içi kartlar** döndürür (istisna listesine bile girmez). Döndürdüğü `idare` yalnız authenticated'a gider; `kazanan_firma`/`yuklenici_ad` HİÇ dönmez → anon maske delinmez.
- **Kötüye kullanım (bulk kazıma):** (a) authenticated-only; (b) çıktı yalnız *açık ilan* teaser'ı (kazanan/firma-özel veri yok — firma profili zaten `firma-analiz`'de görünür, marjinal sızıntı yok); (c) origin `/rest/v1` **2r/s limiti** (memory: origin-hardening) toplu çağrıyı boğar; (d) dashboard kalıcı çağrısı `firmam_acik_ihaleler` firma id'yi `auth.uid()`'den okur → keyfi firma enumerasyonu imkânsız. `migration_bulk_rpc_kilit.sql` kilidi de aynı desende uygulanabilir.

---

## 5) UÇ DURUMLAR

- **Boş veri / firma_id yok:** `firmam_acik_ihaleler` boş döner → teaser. Firmanın hiç kazanımı yoksa (yeni/az veri) profil boş → RPC boş → "profile uyan açık ihale yok" + bildirim vaadi.
- **Çok büyük sonuç (150mn segment firma):** profil aggregation seq scan riski → `idx_ihale_sonuclari_yuklenici_id` şart; hâlâ yavaşsa `firma_profil_mv`. RPC `p_limit=12` + `LIMIT 50` konu-kelime alt sorgusu ile bounded.
- **Maskeli anon:** özellik login-gated; anon teaser başlığından öteye geçemez, RPC 42501/EXECUTE-yok alır. `arama_fold` anon-maskeli olduğu için autocomplete de misafirde çalışmaz (kasıtlı).
- **Mükerrer firma (aynı ünvan farklı yuklenici_id):** seçim `yukleniciler.id` (tekil) üzerinden; `normalize_ad` UNIQUE olduğundan `yukleniciler` zaten tekilleştirilmiş. Bildirimde `NOT EXISTS (…ilan_id…tur='ihale')` dedup — `yeni_ilan_bildirim_uret` ile aynı satır iki üreticiden çift bildirim üretmez.
- **Bayat durum:** `benzer_ihaleler` v3_1 dersi — `son_teklif_tarihi < now()` adayları RPC içinde elenir; gece `ilan_durum_bayatlat()` zaten 'kapandi' yapar.
- **İki auth bounce (memory):** firma seçimi Supabase oturumuna bağlı; `js/api.js` token aynası deseni kullanılır, bayat `ihale_token`'a güvenilmez.

---

## 6) EFOR + BAĞIMLILIK + SIRA

| Adım | İş | Efor |
|---|---|---|
| 1 | `migration_firmam_eslesme.sql`: firma_id kolonu + `idx_ihale_sonuclari_yuklenici_id` + `firmami_belirle` RPC + kullanici_profiller UPDATE yolu | **Küçük** |
| 2 | `firma_icin_acik_ihaleler` + `firmam_acik_ihaleler` RPC'leri; canlıda EXPLAIN ANALYZE ile timeout doğrula (3 firma: küçük/orta/150mn) | **Orta** |
| 3 | Frontend: `js/firmam.js` (autocomplete `yukleniciler`/arama_fold reuse + seçim + kart render + tufe/ICS/takip reuse) + `dashboard.html` blok + onboarding teaser | **Orta** |
| 4 | Gating: `js/plan.js` isPro ile ilk-3/tam-liste kilidi + teaser | **Küçük** |
| 5 | `firma_uygun_bildirim_uret` + gece cron'a ekle (scraper + `ilan_durum_bayatlat` SONRASI); frontend bildirim tarafı reuse (0 iş) | **Küçük** |
| 6 | (Koşullu) `firma_profil_mv` + gece REFRESH — sadece 2. adım EXPLAIN >2s gösterirse | **Orta** |

**Bağımlılıklar:** 2 ← 1 (kolon+indeks). 3 ← 1,2. 5 ← 2. Adım 1'in indeksi HER ŞEYİN önkoşulu (yoksa RPC timeout). **Proxy havuzu bağımlılığı YOK** — yeni kazıma başlatmıyoruz, sadece mevcut veriyi eşleştiriyoruz (kısıt karşılanıyor). **SSH prod yazma:** migration'lar `docker exec -i supabase-db psql < …` ile uygulanır → ayrı onay ister (memory: prod-ssh-auto-mode-limits); frontend deploy = VDS'te `git pull`.

**Önerilen ilk PR:** Adım 1+2+3 (çekirdek özellik, login-gated, bildirimsiz) → doğrula → sonra 4 (gating) + 5 (bildirim). Adım 6 yalnız ölçüm gerektirirse.

İlgili dosyalar: `C:\ihale_platform\backend\migration_uygun_firmalar_v3.sql`, `C:\ihale_platform\backend\migration_uygun_firmalar_v3_1.sql`, `C:\ihale_platform\backend\migration_anon_maske.sql`, `C:\ihale_platform\backend\migration_takip_firmalar.sql`, `C:\ihale_platform\backend\migration_bildirim_uret.sql`, `C:\ihale_platform\backend\migration_kullanici_profiller_rls_sikilastir.sql`, `C:\ihale_platform\backend\migration_sonuc_schema.sql`, `C:\ihale_platform\dashboard.html`, `C:\ihale_platform\firma-analiz.html`, `C:\ihale_platform\js\api.js`, `C:\ihale_platform\js\plan.js`, `C:\ihale_platform\js\kenar-menu.js`.
