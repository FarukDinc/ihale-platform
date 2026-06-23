/**
 * İhalePlatform — UI Yardımcıları
 * Bildirim, yükleme, modal vb.
 */

const UI = (() => {

    // ── Bildirim toast ──────────────────────────────────
    function bildirim_goster(mesaj, tur = "bilgi", link = null) {
        // Varsa eski toast'u kaldır
        document.querySelectorAll(".toast").forEach(t => t.remove());

        const renkler = {
            bilgi:  { bg: "#0A1628", icon: "ℹ️" },
            basari: { bg: "#10b981", icon: "✅" },
            uyari:  { bg: "#F0A500", icon: "⚠️" },
            hata:   { bg: "#ef4444", icon: "❌" }
        };
        const { bg, icon } = renkler[tur] || renkler.bilgi;

        const toast = document.createElement("div");
        toast.className = "toast";
        toast.innerHTML = `
            <span>${icon}</span>
            <span>${mesaj}</span>
            ${link ? `<a href="${link}" style="color:#fff;text-decoration:underline;margin-left:8px">→</a>` : ""}
        `;
        toast.style.cssText = `
            position: fixed; bottom: 24px; right: 24px; z-index: 9999;
            background: ${bg}; color: white; padding: 14px 20px;
            border-radius: 10px; display: flex; align-items: center;
            gap: 10px; font-size: 14px; font-weight: 500;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
            max-width: 380px;
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    // ── Yükleme spinner ─────────────────────────────────
    function yukleniyor_goster(konteyner, mesaj = "Yükleniyor...") {
        if (typeof konteyner === "string") {
            konteyner = document.querySelector(konteyner);
        }
        if (!konteyner) return;

        konteyner.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;
                        justify-content:center;padding:60px;color:#64748b;">
                <div class="spinner" style="
                    width:40px;height:40px;border:3px solid #e2e8f0;
                    border-top-color:#F0A500;border-radius:50%;
                    animation:spin 0.8s linear infinite;margin-bottom:16px">
                </div>
                <span style="font-size:14px">${mesaj}</span>
            </div>
        `;
    }

    // ── Boş durum ───────────────────────────────────────
    function bos_durum_goster(konteyner, mesaj, ikon = "📭") {
        if (typeof konteyner === "string") {
            konteyner = document.querySelector(konteyner);
        }
        if (!konteyner) return;

        konteyner.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;
                        justify-content:center;padding:80px;color:#94a3b8;">
                <div style="font-size:48px;margin-bottom:16px">${ikon}</div>
                <p style="font-size:15px;text-align:center">${mesaj}</p>
            </div>
        `;
    }

    // ── Para formatı ────────────────────────────────────
    function para_formatla(tutar) {
        if (!tutar) return "Belirtilmemiş";
        return new Intl.NumberFormat("tr-TR", {
            style: "currency",
            currency: "TRY",
            maximumFractionDigits: 0
        }).format(tutar);
    }

    // ── Tarih formatı ────────────────────────────────────
    function tarih_formatla(tarih_str) {
        if (!tarih_str) return "—";
        const t = new Date(tarih_str);
        return t.toLocaleDateString("tr-TR", {
            day: "2-digit", month: "2-digit", year: "numeric"
        });
    }

    // ── Kalan gün ───────────────────────────────────────
    function kalan_gun(tarih_str) {
        if (!tarih_str) return null;
        const fark = new Date(tarih_str) - new Date();
        const gun = Math.ceil(fark / (1000 * 60 * 60 * 24));
        if (gun < 0)  return '<span style="color:#ef4444">Sona erdi</span>';
        if (gun === 0) return '<span style="color:#F0A500">Bugün</span>';
        if (gun <= 3)  return `<span style="color:#ef4444">${gun} gün</span>`;
        if (gun <= 7)  return `<span style="color:#F0A500">${gun} gün</span>`;
        return `<span style="color:#10b981">${gun} gün</span>`;
    }

    // ── Skor rozeti ─────────────────────────────────────
    function skor_rozet(skor) {
        if (!skor && skor !== 0) return "";
        let renk, etiket;
        if (skor >= 70) { renk = "#10b981"; etiket = "Uyumlu"; }
        else if (skor >= 40) { renk = "#F0A500"; etiket = "Orta"; }
        else { renk = "#ef4444"; etiket = "Düşük"; }

        return `
            <span style="background:${renk}22;color:${renk};
                padding:3px 10px;border-radius:20px;font-size:12px;
                font-weight:600">
                ${skor}/100 — ${etiket}
            </span>
        `;
    }

    // ── Karar rozeti ────────────────────────────────────
    function karar_rozet(karar) {
        if (!karar) return "";
        const renkler = {
            "GİR":    { bg: "#10b981", text: "✅ GİR" },
            "DÜŞÜN":  { bg: "#F0A500", text: "🤔 DÜŞÜN" },
            "GIRME":  { bg: "#ef4444", text: "❌ GIRME" }
        };
        const ayar = renkler[karar.toUpperCase()] || { bg: "#64748b", text: karar };
        return `
            <span style="background:${ayar.bg};color:white;
                padding:4px 14px;border-radius:20px;font-size:13px;
                font-weight:700">
                ${ayar.text}
            </span>
        `;
    }

    // ── Analiz raporu render ─────────────────────────────
    function rapor_render(rapor, konteyner) {
        if (typeof konteyner === "string") {
            konteyner = document.querySelector(konteyner);
        }
        if (!konteyner || !rapor) return;

        const r = rapor.rapor || rapor;
        const ozet = r.ozet || {};
        const alarmlar = r.kirmizi_alarmlar || [];
        const firsatlar = r.firsatlar || [];
        const mali = r.mali_yuk || {};
        const engeller = r.giris_engelleri || {};
        const aksiyonlar = r.aksiyon_listesi || [];

        konteyner.innerHTML = `
            <!-- Karar Başlığı -->
            <div style="text-align:center;padding:24px;background:#f8fafc;
                        border-radius:12px;margin-bottom:24px">
                <div style="margin-bottom:12px">
                    ${karar_rozet(r.karar)}
                </div>
                ${skor_rozet(r.uygunluk_skoru)}
                <p style="color:#64748b;margin-top:12px;font-size:14px">
                    ${r.karar_gerekce || ""}
                </p>
            </div>

            <!-- Özet -->
            <div class="rapor-bolum">
                <h3>📋 İhale Özeti</h3>
                <table style="width:100%;border-collapse:collapse">
                    ${[
                        ["Kurum", ozet.idare],
                        ["Konu", ozet.konu],
                        ["Tahmini Bedel", ozet.tahmini_bedel],
                        ["İş Süresi", ozet.sure],
                        ["Lokasyon", ozet.yer]
                    ].map(([k, v]) => v ? `
                        <tr style="border-bottom:1px solid #f1f5f9">
                            <td style="padding:8px 0;color:#64748b;width:140px;font-size:13px">${k}</td>
                            <td style="padding:8px 0;font-size:13px;font-weight:500">${v}</td>
                        </tr>
                    ` : "").join("")}
                </table>
            </div>

            <!-- Kırmızı Alarmlar -->
            ${alarmlar.length ? `
            <div class="rapor-bolum">
                <h3>🚨 Kırmızı Alarmlar</h3>
                ${alarmlar.map(a => `
                    <div style="background:#fef2f2;border-left:3px solid #ef4444;
                                padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;
                                font-size:13px;color:#7f1d1d">
                        ${a}
                    </div>
                `).join("")}
            </div>
            ` : ""}

            <!-- Fırsatlar -->
            ${firsatlar.length ? `
            <div class="rapor-bolum">
                <h3>✅ Fırsatlar & Avantajlar</h3>
                ${firsatlar.map(f => `
                    <div style="background:#f0fdf4;border-left:3px solid #10b981;
                                padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;
                                font-size:13px;color:#14532d">
                        ${f}
                    </div>
                `).join("")}
            </div>
            ` : ""}

            <!-- Mali Yük -->
            <div class="rapor-bolum">
                <h3>💰 Mali Yük</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                    ${[
                        ["Geçici Teminat", mali.gecici_teminat],
                        ["Kesin Teminat", mali.kesin_teminat],
                        ["Ödeme Süresi", mali.odeme_suresi],
                        ["Fiyat Farkı", mali.fiyat_farki],
                        ["Avans", mali.avans]
                    ].filter(([,v]) => v).map(([k, v]) => `
                        <div style="background:#f8fafc;padding:12px;border-radius:8px">
                            <div style="font-size:11px;color:#94a3b8;margin-bottom:4px">${k}</div>
                            <div style="font-size:14px;font-weight:600">${v}</div>
                        </div>
                    `).join("")}
                </div>
            </div>

            <!-- Giriş Engelleri -->
            ${Object.keys(engeller).length ? `
            <div class="rapor-bolum">
                <h3>🔒 Giriş Engelleri</h3>
                ${Object.entries(engeller).map(([kategori, maddeler]) =>
                    Array.isArray(maddeler) && maddeler.length ? `
                    <div style="margin-bottom:12px">
                        <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;
                                    letter-spacing:0.5px;margin-bottom:6px">${kategori}</div>
                        ${maddeler.map(m => `
                            <div style="font-size:13px;padding:4px 0;color:#374151">• ${m}</div>
                        `).join("")}
                    </div>
                ` : "").join("")}
            </div>
            ` : ""}

            <!-- Aksiyon Listesi -->
            ${aksiyonlar.length ? `
            <div class="rapor-bolum">
                <h3>📌 Yapılacaklar</h3>
                ${aksiyonlar.map((a, i) => `
                    <div style="display:flex;gap:12px;padding:8px 0;
                                border-bottom:1px solid #f1f5f9;font-size:13px">
                        <span style="background:#0A1628;color:white;width:22px;height:22px;
                                     border-radius:50%;display:flex;align-items:center;
                                     justify-content:center;font-size:11px;flex-shrink:0">
                            ${i + 1}
                        </span>
                        <span>${a}</span>
                    </div>
                `).join("")}
            </div>
            ` : ""}

            <!-- Meta -->
            <div style="margin-top:24px;padding:12px;background:#f8fafc;
                        border-radius:8px;font-size:12px;color:#94a3b8">
                PDF türü: ${r._meta?.pdf_turu || "—"} &nbsp;|&nbsp;
                Harcanan kredi: ${r._meta?.harcanan_kredi || 1} &nbsp;|&nbsp;
                Sayfa sayısı: ${r._meta?.sayfa_sayisi || "—"}
            </div>
        `;
    }

    // CSS animasyonları ekle
    const style = document.createElement("style");
    style.textContent = `
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes slideIn { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .rapor-bolum { margin-bottom: 24px; }
        .rapor-bolum h3 { font-size: 15px; font-weight: 700; color: #0A1628;
                          margin-bottom: 12px; padding-bottom: 8px;
                          border-bottom: 2px solid #f1f5f9; }
    `;
    document.head.appendChild(style);

    return {
        bildirim_goster,
        yukleniyor_goster,
        bos_durum_goster,
        para_formatla,
        tarih_formatla,
        kalan_gun,
        skor_rozet,
        karar_rozet,
        rapor_render
    };

})();
