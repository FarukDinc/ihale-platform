# İhalePlatform — Geliştirici Context Dosyası
# Yeni konuşmada Claude'a bu dosyayı yapıştır

## MİMARİ
```
Frontend  → Netlify (HTML + Vanilla JS)
Backend   → Render.com (FastAPI + Python)
Veritabanı → Supabase (PostgreSQL)
Ödeme     → İyzico
Proxy     → Webshare (rotating residential)
AI        → Gemini 1.5 Flash
```

## MODÜLLER

### Faz 1 — Mevcut (yazıldı)
- EKAP ihale takip (ekap_scraper.py)
- Gemini PDF analizi — metin + taranmış (analyzer.py)
- Worker + Supabase entegrasyonu (worker.py)
- FastAPI backend (api.py)
- İyzico ödeme (payment.py)
- Rotating proxy (proxy_config.py)
- Frontend 13 sayfa + 8 JS modül
- Supabase şema v2 (supabase_schema_v2.sql)

### Faz 2 — Yazılacak
- AI teklif & döküman yazımı
- Kazanan & rekabet analizi
- Akıllı eşleştirme motoru
- Özel sektör alım ilanları
- Firma-Tedarikçi ağı
- Konsorsiyum sistemi
- İhale bazlı hafif CRM
- Yurtdışı ihale altyapısı

## TEMEL VERİTABANI TABLOLARI (v2)
- kullanici_profiller (tipler[], hizmet_alanlari[])
- kullanici_krediler + kredi_hareketleri
- planlar (free/standart/kurumsal)
- ilanlar (kaynak: ekap/ozel/uluslararasi) ← ana tablo
- teklifler
- ihale_sonuclari + firma_istatistikleri
- takipler (CRM durumları dahil)
- eslestirmeler
- konsorsiyumlar + konsorsiyum_uyeleri
- dokuman_sablonlari + uretilen_dokumanlar
- bildirimler
- analiz_gecmisi

## KREDİ SİSTEMİ
- Free: 3 kredi/ay
- Standart: 50 kredi — 1490 TL/ay
- Kurumsal: 250 kredi — 3990 TL/ay
- Metin PDF: 1 kredi | Taranmış PDF: 2 kredi
- Teklif yazımı: 1 kredi
- Cache: Gemini'ye gitmiyor ama yine 1 kredi düşüyor

## KULLANICI TİPLERİ
- alici: ihale açan veya özel ilan yayınlayan
- tedarikci: ihaleye veya ilana teklif veren
- taseron: alt yüklenici
- idare: kamu kurumu
- Bir kullanıcı birden fazla tip olabilir (tipler[] array)

## KİLİT DOSYALAR
```
backend/
  ekap_scraper.py    → EKAP Playwright scraper + proxy
  analyzer.py        → Gemini analiz (metin+vision)
  worker.py          → Scraper+Analyzer+Supabase pipeline
  api.py             → FastAPI endpoints
  payment.py         → İyzico entegrasyonu
  proxy_config.py    → Webshare rotating proxy
  render.yaml        → Render.com deploy config
  requirements.txt   → pip bağımlılıkları

js/
  api.js             → Tüm API çağrıları
  ui.js              → Toast, spinner, rapor render
  dashboard.js       → Dashboard
  auth.js            → Giriş/kayıt
  ihaleler.js        → Liste + filtre
  ihale-detay.js     → Detay + analiz
  profil.js          → Firma profili
  fiyatlandirma.js   → Ödeme modal
  seo.js             → Meta tags
```

## ÖNEMLİ NOTLAR
- Gemini API key: .env'de GEMINI_API_KEY
- EKAP tokenları her çalıştırmada Playwright ile yakalanır
- Taranmış PDF → Gemini File API ile doğrudan upload
- Cache: yapay_zeka_ozeti JSONB alanında tutulur
- RLS aktif: kullanıcılar sadece kendi verilerini görür
- ilanlar tablosu hem EKAP hem özel hem uluslararası ilanları tutar
