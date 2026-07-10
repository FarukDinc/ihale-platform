"""
Faz D3 — Semantik Eşleşme: paylaşılan embedding yardımcı fonksiyonu.

Gemini'nin embedContent destekleyen GÜNCEL modeli `text-embedding-004` DEĞİL
(o kaldırıldı — analyzer.py/firma_ai_yorum.py'de gemini-1.5-flash'ın kaldırılmasıyla
aynı sınıf sorun, bkz. YAPILACAKLAR.md). Yerine `models/gemini-embedding-001`
kullanılıyor, `output_dimensionality=768` ile (Matryoshka/MRL — kısaltılmış çıktı
pgvector index limitleri için uygun, cosine mesafesi normalize etmeden de doğru çalışır
çünkü `<=>` operatörü zaten vektör normlarına böler).

Kullanım:
    from embed_ortak import embed_uret
    vec = embed_uret("Ankara ili yol yapım işi ihalesi")   # list[float] (768) ya da None
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_BOYUT = 768

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def embed_uret(metin: str) -> list[float] | None:
    """Verilen metni 768-boyutlu embedding'e çevirir. Hata/boş metinde None döner."""
    if not _client or not (metin or "").strip():
        return None
    try:
        r = _client.models.embed_content(
            model=EMBED_MODEL,
            contents=metin[:8000],  # modelin token limiti için kaba bir üst sınır
            config=types.EmbedContentConfig(output_dimensionality=EMBED_BOYUT),
        )
        return list(r.embeddings[0].values)
    except Exception as e:
        print(f"    ✗ embed_uret hatası: {str(e)[:150]}")
        return None
