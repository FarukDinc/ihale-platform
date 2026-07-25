/**
 * TÜFE Bugünkü-Değer Çevirici — İhaleGlobal
 * ------------------------------------------------------------
 * Nominal TL tutarı, sözleşme tarihindeki alım gücüne göre BUGÜNKÜ TL'ye çevirir.
 * Kaynak: TÜİK Tüketici Fiyat Endeksi (2003=100), YILLIK ORTALAMA değerler.
 *   https://www.hakedis.org/endeksler/tuketici-fiyat-genel-endeksi-ve-degisim-oranlari-2003
 *
 * Kullanım:
 *   <script src="/js/tufe.js"></script>
 *   TUFE.buguneCevir(1000000, '2015-06-01')  → 2015'in 1 Mn TL'si bugün ~kaç TL
 *   TUFE.carpani('2015-06-01')               → o yılın çarpanı (ör. 15.13)
 *   TUFE.formatBugunku(nominal, tarih)        → "15,1 Mn ₺ (bugünkü değer)" metni
 *
 * GÜNCELLEME: yeni yıl verisi çıkınca ENDEKS'e ekle ve GUNCEL_ENDEKS'i güncelle.
 * NOT: DT tutarlarında da çalışır ama DT ölçeği küçük; asıl değer ihale/sözleşme bedellerinde.
 */
const TUFE = (() => {
  // Yıllık ortalama TÜFE endeksi (2003=100). TÜİK/hakedis.org.
  const ENDEKS = {
    2003: 100.00,
    2004: 107.51, 2005: 117.51, 2006: 129.18, 2007: 140.44,
    2008: 153.27, 2009: 164.50, 2010: 178.48, 2011: 189.58,
    2012: 207.20, 2013: 222.49, 2014: 241.35, 2015: 261.30,
    2016: 282.21, 2017: 313.08, 2018: 360.70, 2019: 418.58,
    2020: 473.51, 2021: 569.03, 2022: 957.12, 2023: 1439.61,
    2024: 2359.35, 2025: 3132.76, 2026: 3953.93,  // 2026: Ocak-Mayıs ort.
  };
  // Bugünkü alım gücü referansı = en güncel yıl endeksi.
  const GUNCEL_YIL = 2026;
  const GUNCEL_ENDEKS = ENDEKS[GUNCEL_YIL];

  function yilCoz(tarih) {
    if (!tarih) return null;
    const y = (tarih instanceof Date) ? tarih.getFullYear()
            : parseInt(String(tarih).slice(0, 4), 10);
    if (!y || isNaN(y)) return null;
    if (y < 2003) return 2003;          // 2003 öncesi taban
    if (y > GUNCEL_YIL) return GUNCEL_YIL; // gelecek çöp tarih
    return y;
  }

  /** O tarihin bugünkü-değer çarpanı (yoksa null). */
  function carpani(tarih) {
    const y = yilCoz(tarih);
    if (y == null || !ENDEKS[y]) return null;
    return GUNCEL_ENDEKS / ENDEKS[y];
  }

  /** Nominal tutarı bugünkü TL'ye çevir (çeviremezse nominal'i döndür). */
  function buguneCevir(tutar, tarih) {
    const c = carpani(tarih);
    if (c == null || tutar == null) return tutar;
    return Math.round(Number(tutar) * c);
  }

  const _tl = (v) => v == null ? '—' : (Number(v) / 1e6 >= 1
      ? (Number(v) / 1e6).toLocaleString('tr-TR', { maximumFractionDigits: 1 }) + ' Mn ₺'
      : Number(v).toLocaleString('tr-TR') + ' ₺');

  /** "12,3 Mn ₺" — bugünkü değer metni (nominal+tarih verilir). */
  function formatBugunku(nominal, tarih) {
    return _tl(buguneCevir(nominal, tarih));
  }

  return { ENDEKS, GUNCEL_YIL, GUNCEL_ENDEKS, carpani, buguneCevir, formatBugunku };
})();
if (typeof module !== 'undefined') module.exports = TUFE;
