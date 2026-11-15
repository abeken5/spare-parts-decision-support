# PROJECT_STATE.md — Proje Canlı Durum Özeti

- **Son Güncelleme:** 2026-11-15
- **Aktif Faz:** Sprint 3 Tamamlandı -> Sprint 4 (Streamlit Karar Destek Arayüzü & Yönetici Raporu) Başlangıcı

## 1. Tamamlanan İşler
- **Sprint 0:** Yönetişim dokümanları (Tüzük, RACI, Risk, Karar Günlüğü, WBS, Değişiklik Kaydı) ve CI (`pytest`) kuruldu.
- **Sprint 1:** Sentetik veri üreteci (`200` parça, `1.095` gün), SQLite analitik veritabanı (`mro_inventory.db`) ve ABC-XYZ / Syntetos-Boylan segmentasyonu tamamlandı.
- **Sprint 2:** 5 modelli tahmin yarışması (`RMSSE` + %2 basitlik toleransı) ve gün biriminde klasik `(s, Q)` modülü tamamlandı.
- **Sprint 3:**
  - `src/simulation/bootstrap.py` ile 10.000 iterasyonlu Blok Bootstrap motoru (`CSL %85–%99`) kuruldu.
  - `src/evaluation/backtest.py` ile kapalı 365 günlük CRN backtest ve 3 kademeli VED ceza duyarlılık analizi tamamlandı; toplam **18 birim test** doğrulandı.

## 2. Sıradaki İşler (Sprint 4)
- Yönetici karar özeti ve parça bazlı aksiyon önerileri üreticisi (`src/reporting/`).
- Etkileşimli Streamlit Karar Destek Dashboard'u (`app/streamlit_app.py`).
- Final README vitrini ve portföy sunum paketi.

## 3. Gerçekleşen Backtest Metrikleri (365 Günlük Kapalı Test Penceresi)
- **Mevcut Stilize Min/Max (1.5/3.0 ay):** Baz Toplam Maliyet `82.72 M TL` | Elde Tutma `17.23 M TL` | Fill Rate `%92.17` | Vital Stoksuzluk `2.32 gün`
- **Eşit Fill Rate Min/Max Grid (2.0/4.0 ay):** Baz Toplam Maliyet `63.00 M TL` | Elde Tutma `25.60 M TL` | Fill Rate `%95.62` | Vital Stoksuzluk `1.18 gün`
- **Klasik Normal (s, Q) CSL %95:** Baz Toplam Maliyet `55.58 M TL` | Elde Tutma `16.77 M TL` | Fill Rate `%94.31` | Vital Stoksuzluk `1.36 gün`
- **Ampirik Blok Bootstrap (s, Q) CSL %95:** Baz Toplam Maliyet `48.46 M TL` | Elde Tutma `18.29 M TL` | Fill Rate `%95.52` | Vital Stoksuzluk `1.16 gün`
- **Ampirik Blok Bootstrap (s, Q) CSL %98:** Baz Toplam Maliyet `39.86 M TL` | Elde Tutma `22.37 M TL` | Fill Rate `%97.58` | Vital Stoksuzluk `0.56 gün`
