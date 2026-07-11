/**
 * SEO Meta Tag Yönetimi
 * index.html'e ekle — diğer sayfalara da kopyalanabilir
 */

// index.html <head> içine eklenecek meta taglar:
const SEO_META = `
<!-- SEO -->
<meta name="description" content="Türkiye'nin en akıllı ihale takip platformu. EKAP ihalelerini yapay zeka ile analiz et, riski ve fırsatı anında gör. Ücretsiz dene.">
<meta name="keywords" content="ihale takip, kamu ihalesi, EKAP, ihale analiz, yapay zeka ihale, ihale platformu">
<meta name="author" content="İhaleGlobal">
<meta name="robots" content="index, follow">

<!-- Open Graph (LinkedIn, WhatsApp paylaşım önizlemesi) -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://ihaleplatform.com">
<meta property="og:title" content="İhaleGlobal — Yapay Zeka ile İhale Analizi">
<meta property="og:description" content="Kamu ihalelerini saniyeler içinde analiz et. Risk, fırsat ve uyumluluk skoru — hepsi tek ekranda.">
<meta property="og:image" content="https://ihaleplatform.com/img/og-image.png">
<meta property="og:locale" content="tr_TR">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="İhaleGlobal — Yapay Zeka ile İhale Analizi">
<meta name="twitter:description" content="Kamu ihalelerini saniyeler içinde analiz et.">
<meta name="twitter:image" content="https://ihaleplatform.com/img/og-image.png">

<!-- Canonical -->
<link rel="canonical" href="https://ihaleplatform.com">

<!-- Favicon -->
<link rel="icon" type="image/png" href="/img/favicon.png">
`;

// Structured Data (Google'da zengin sonuç)
const STRUCTURED_DATA = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "İhaleGlobal",
    "applicationCategory": "BusinessApplication",
    "description": "Türkiye kamu ihalelerini yapay zeka ile analiz eden SaaS platformu",
    "url": "https://ihaleplatform.com",
    "offers": [
        {
            "@type": "Offer",
            "name": "Ücretsiz Plan",
            "price": "0",
            "priceCurrency": "TRY"
        },
        {
            "@type": "Offer",
            "name": "Standart Plan",
            "price": "1490",
            "priceCurrency": "TRY"
        }
    ]
};

// Structured data'yı sayfaya ekle
document.addEventListener("DOMContentLoaded", () => {
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(STRUCTURED_DATA);
    document.head.appendChild(script);
});
