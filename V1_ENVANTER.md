# V1 — İhalePro Düzeni Envanteri (28 Tem 2026)

> **AMAÇ:** v1 = ihalepro'nun sayfa/akış/özellik düzeninin birebir karşılığı (mavi kurumsal),
> v2 = mevcut İhaleGlobal sayfalarımız (amber). Profil menüsünden geçiş.
>
> **SINIR (kullanıcı onaylı):** ihalepro'nun LOGOSU, "İhalePro" MARKASI ve birebir pazarlama
> metinleri/görselleri KOPYALANMAZ. Düzen, akış, özellik, sütun yapısı, renk şeması kopyalanır.
> Kendi iG logomuz + kendi metinlerimiz + kendi verimiz kullanılır.

## 🎨 Renk Paleti (canlı ölçüm — computed styles)

| Rol | Değer | Not |
|---|---|---|
| Ana lacivert (sidebar/başlık) | `#0C3E70` rgb(12,62,112) | en baskın kurumsal renk |
| Koyu lacivert 2 (banner) | `#0B3F77` rgb(11,63,119) | |
| Mavi (link/vurgu/sayı) | `#135EAA` rgb(19,94,170) | KPI sayıları, linkler |
| Teal aksan | `#00A19A` rgb(0,161,154) | ikincil vurgu, "yeni" rozetleri |
| Gövde metni | `#2F3D4D` rgb(47,61,77) | koyu arduvaz |
| İkincil metin | `#495057` / `#6C757D` | |
| Zemin | `#FFFFFF` beyaz + açık gri kart | |
| **Font** | **"Open Sans", sans-serif** | |

## 🧭 Navigasyon (sol dar ray — ikon + etiket)
`Bana Özel · Analiz · İhaleler · Sonuçlar · Sözleşmeler · Kararlar · Firmalar · Kurumlar · Sektörler · Global`
Aktif öğe: beyaz "çıkıntı sekme" + koyu ikon.

## 🔝 Topbar
`[Kapsam dropdown ▾] [Arama: "İhale, firma, kurum, sonuç ara.." 🔍]` … sağda:
`Mevcut Paket: Temel + [Paket Yükselt]` · `7 Gün Ücretsiz / Demo Talep Et` · 4 ikon (rapor+, profil, takvim/ajanda, zil)
Breadcrumb: `🏠 > Kamu > İhaleler > İhaleler`

## 📄 Sayfa Envanteri (35 rota / ~11 şablon)

### A) KULLANICI
| Rota | Sayfa |
|---|---|
| `/user/dashboard` | **Bana Özel** (ana panel) |
| `/user/profile` | Profilim |
| `/user/calendar` | Ajandam |
| `/user/reports` | Rapor Ekle |
| (base64) | Raporlarım · Analizler |

**Bana Özel bölüm sırası:** arama → Merhaba+isim → **TR harita + 6 KPI (2 sütun)** → Takip Listem (4 kart, her kartta "Yeni Ekle") → Takip Ettiğim Firmaların Tüm Sözleşmeleri → **"Sizin İçin Katılabileceğiniz İhaleleri Bulduk!"** (tablo) → **AI Asistan promo** → İhale Raporlarım → İhale Sonuç Raporlarım → Takip Ettiğim İhaleler → Takip Edilenlerde Son Güncellemeler → Son İncelediğim İhaleler → Tarihi Yaklaşan İhalelerim → Favori Aramalarım
**KPI'lar:** Aktif İhale · İşveren İdare · Doğrudan Temin · Sektörde Fırsat · Sözleşme · Yüklenici Firma
**Slogan:** "Güncel, doğru ve kapsamlı veri havuzu ile kararlarınızı güvenle alın!"

### B) KAMU (liste şablonu — hepsi aynı iskelet)
| Rota | Sayfa |
|---|---|
| `/kamu/ihaleler/aktif` | **Aktif İhaleler** |
| `/kamu/ihaleler?methods=D` | Doğrudan Teminler |
| (sekme) | Sonuçlar |
| `/kamu/sozlesmeler` | Sözleşmeler — Tümü |
| `/kamu/sozlesmeler/biten-isler` | Biten İşler |
| `/kamu/sozlesmeler/devam-eden-isler` | Devam Eden İşler |
| `/kamu/kik-kararlari/tumu` | KİK Kararları — Tümü |
| `/kamu/kik-kararlari/uyusmazlik-kararlari` | Uyuşmazlık Kararları |
| `/kamu/kik-kararlari/mahkeme-kararlari` | Mahkeme Kararları |
| `/kamu/kik-kararlari/mahkeme-tutanaklari` | Mahkeme Tutanakları |
| `/kamu/yasakli-sorgulama` | Yasaklı Sorgulama |

**LİSTE ŞABLONU (kritik — en çok tekrar eden):**
- Başlık + sekmeler (Aktif İhaleler | Sonuçlar)
- **SOL FİLTRE PANELİ (accordion, sticky "Filtreyi Uygula" butonu):**
  `Sadece E-İhale İlanlı` (toggle) · `Yapay Zeka ile Önerilen İhaleler` (toggle, vurgulu) ·
  Kelime Arama · Yayın Tarihi · İhale Tarihi · Yaklaşık Maliyet · İhale Tipi · İhale Usulü ·
  İhale Yapan İdare · Sektörler · İhalenin Yapılacağı İl · İşin Yapılacağı İl · Benzer İş ·
  Sözleşme Tipi · Düzeltme İlanı · Diğer Filtreler
  + `Aramayı Kaydet` + `Nasıl Arama Yaparım?` + `Filtreyi Uygula` / `Vazgeç`
- **SAĞ İÇERİK:** "Arama kriterinize uygun **5.345** ihale ilanı listeleniyor" + `Listede Ara` + **Excel export** (yeşil buton)
- **TABLO:** `İhale Tarihi (↕)` | `İKN/İhale Adı (↕)` | `İhale Tipi Usulü` | `İhale İli (↕)`
  Satır: tarih+saat+**"Son X gün"** · İKN + ihale adı (mavi link) · tip/usul · il
  Satır sağı: **takvime ekle** butonu + **genişlet (chevron)**
- Sayfalama: 1 2 3 4 5 …

### C) ANALİZ (İhalePro modülü)
| Rota | Sayfa |
|---|---|
| `/ihalepro/dashboard/main` | **Genel Bakış** (firma analiz paneli) |
| `/ihalepro/firmalar` | Tüm Firmalar |
| `/ihalepro/firmalar/takip-ettiklerim` | Takip Ettiklerim |
| `/ihalepro/firmalar/parlayan-yildizlar` | **Parlayan Yıldızlar** |
| `/ihalepro/kurumlar` | Tüm Kurumlar |
| `/ihalepro/kurumlar/takip-ettiklerim` | Takip Ettiklerim |
| (base64) | Tüm İdareler |
| `/ihalepro/sektorler` | Tüm Sektörler |
| `/ihalepro/sektorler/takip-ettiklerim` | Takip Ettiklerim |
| `/ihalepro/dashboard/bitecek-sozlesmeler` | Bitecek Sözleşmeler |

**ANALİZ GENEL BAKIŞ şablonu:** firma başlık bandı (koyu mavi kutu + ad) → "Firmanın Tüm Zamanlarda
Gerçekleşen Sözleşme Verileri" + Tarih Aralığı seçici → 2 büyük kart (`N ihale / N sözleşme`,
`N kurum ile iş bitirme`) → 3 kart (Toplam Sözleşme Bedeli · Ortalama Sözleşme Bedeli ·
En Çok İş Yaptığı Sektör — ₺/$/bugünkü değer üçlüsü) → **Türkiye Geneli haritası** + sağ panel
(Toplam ihale bedeli · En çok ihale kazanılan il · N sözleşme) + `Tablo Görünümü` toggle →
**"Sizin İçin Katılabileceğiniz İhaleleri Bulduk!"** tablosu + `Tümü >`

### D) BANK (ayrı modül — bankalar için)
`/bank/dashboard` · `/bank/firmalar` · `/bank/ihaleler` · `/bank/sektorler` · `/bank/kurumlar`

## 🔒 Paywall Modeli (ihalepro'da)
Ücretsiz ("Temel") pakette değerler `*****` + 🔒 kilit ikonu ile maskeli; "Paketini Yükselt" CTA'sı.
Bizde karşılığı: mevcut plan sistemi (`plan_kodu` standart/kurumsal) + `js/plan.js`.

## 🏗️ v1 İnşa Sırası (öneri)
1. `css/v1.css` — mavi kurumsal tema (yukarıdaki palet + Open Sans)
2. v1 kabuk: sidebar (10 öğe) + topbar (kapsam arama + paket rozeti + 4 ikon) + breadcrumb
3. **v1 Bana Özel** (`v1-benim-sayfam.html`)
4. **v1 Liste şablonu** (`v1-ihaleler.html`) → Sonuçlar/Sözleşmeler/KİK/DT hepsi bu şablondan türer
5. v1 Analiz Genel Bakış + Firmalar/Kurumlar/Sektörler
6. v1 Ajanda · Raporlar · Profil · Yasaklı Sorgulama
7. **v1/v2 geçişi** — profil menüsünde "Sürüm" satırı (localStorage `ihale_surum`)


## ✅ İNŞA DURUMU (28 Tem)

| Sayfa | Dosya | Durum |
|---|---|---|
| Bana Özel | `v1-benim-sayfam.html` | ✅ mavi harita + 6 KPI hero + 9 bölüm |
| İhaleler (liste şablonu) | `v1-ihaleler.html` | ✅ 14 filtre + tablo + Excel + sayfalama |
| Sektörler | `v1-sektorler.html` | ✅ 45 sektör, çubuk, takip |
| Firmalar | `v1-firmalar.html` | ✅ Tümü/Takip/Parlayan Yıldızlar |
| Kurumlar | `v1-kurumlar.html` | ✅ Tümü/Takip |
| KİK Kararları | `v1-kararlar.html` | ✅ 775 karar, 4 sekme, TR-katlamalı arama |
| Sözleşmeler | `v1-sozlesmeler.html` | ✅ 2,25M sözleşme, Biten/Devam Eden, Excel |
| Analiz | `v1-analiz.html` | ⏳ sırada |
| Global | `v1-global.html` | ⏳ |
| Ajanda / Raporlar / Profil / Yasaklı | — | ⏳ |

### Öğrenilen kritik teknik notlar
- ⛔ **`window.KATEGORILER` nesne dizisi** (`{kod,emoji,...}`) — string sanıp `esc()` çağırmak sayfayı öldürür.
- ⛔ **Sıralama yönü indeksle EŞLEŞMELİ:** `idx_ilanlar_durum_son_teklif` = `(durum, son_teklif_tarihi DESC NULLS LAST)`.
  `ASC NULLS LAST` istersen planner indeksi kullanamaz → 1,6M satır tarar (7064ms). `ASC NULLS FIRST` → **0,79ms**.
- ⛔ **Büyük tabloda `select+count:'exact'+order+range` BİRLİKTE timeout** — sayımı ayrı `head:true` sorgusuna böl.
- ⛔ **`ihale_sonuclari` kolon adları:** `tenzilat_yuzde` (tenzilat değil), `sozlesme_bedeli`, `is_bitis_tarihi` (Biten/Devam Eden bundan türer), `lot_sayisi` YOK.
- ⛔ **KİK aramada TR katlama şart** (`arama_fold`) — düz `ilike` İ/ı yüzünden sessiz veri kaybı yapar.


## 🏁 v1 KAPSAM TAMAMLANDI (28 Tem) — 15 sayfa

| Sayfa | Dosya |
|---|---|
| Bana Özel | `v1-benim-sayfam.html` |
| İhaleler (Aktif / Sonuçlar / **Doğrudan Teminler**) | `v1-ihaleler.html` |
| **İhale Detayı** | `v1-ihale-detay.html` |
| Sözleşmeler (Tümü / Biten / Devam Eden) | `v1-sozlesmeler.html` |
| KİK Kararları (4 sekme) | `v1-kararlar.html` |
| Yasaklı Sorgulama | `v1-yasakli.html` |
| Analiz (firma paneli) | `v1-analiz.html` |
| Firmalar (3 sekme) | `v1-firmalar.html` |
| Kurumlar | `v1-kurumlar.html` |
| Sektörler | `v1-sektorler.html` |
| Global (TED) | `v1-global.html` |
| **Bank Modülü** (5 sekme) | `v1-bank.html` |
| Ajanda | `v1-ajanda.html` |
| Raporlar | `v1-raporlar.html` |
| Profil | `v1-profil.html` |

Menü: 11 öğe (Bana Özel · Analiz · İhaleler · Sonuçlar · Sözleşmeler · Kararlar · Firmalar · Kurumlar · Sektörler · Global · Bank).
Sürüm geçişi **iki yönlü** (v1 `js/v1-kabuk.js` · v2 `js/sidebar-user.js`).

### Ek teknik notlar
- Aktif menü sekmesinde ihalepro'nun "ters köşe" numarası tarayıcıda çirkin beyaz bloklar üretti → **kullanma**; temiz yuvarlak sekme + ince teal çubuk yeterli.
- `dogrudan_temin_ilanlari` kolonları: `dt_no`, `tarih` (son_teklif_tarihi DEĞİL), `kategori`, `yayin_tarihi`.
- Benzer ihalede **kategori tek başına yetmez** — sınıflandırıcı gürültüsü var, `tur` ile birlikte filtrele.
