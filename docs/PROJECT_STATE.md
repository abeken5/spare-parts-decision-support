# PROJECT_STATE.md — Proje Canlı Durum Özeti

- **Son Güncelleme:** 2026-11-15
- **Aktif Faz:** Sprint 2 Tamamlandı -> Sprint 3 (Ampirik Simülasyon & Min/Max Backtest) Başlangıcı

## 1. Tamamlanan İşler
- **Sprint 0:** Yönetişim dokümanları (Tüzük, RACI, Risk, Karar Günlüğü, WBS) ve CI (`pytest`) kuruldu.
- **Sprint 1:** Sentetik veri üreteci (`200` parça, `1.095` gün), SQLite analitik veritabanı (`mro_inventory.db`) ve ABC-XYZ / Syntetos-Boylan segmentasyonu tamamlandı.
- **Sprint 2:**
  - `src/forecasting/models.py` ile 5 model yarıştırıldı, RMSSE + %2 basitlik toleransıyla parça ve segment kazananları seçilip 24 ayla yeniden eğitildi.
  - `src/inventory/classical.py` ile gün biriminde klasik SS/ROP/EOQ politikaları üretildi; toplam **12 birim test** doğrulandı.

## 2. Sıradaki İşler (Sprint 3)
- Ampirik Bootstrap / Monte Carlo lead-time talep simülasyonu (`src/simulation/`).
- Klasik normal dağılım vs. ampirik simülasyon karşılaştırması.
- Kapalı test penceresinde (son 365 gün) mevcut Min/Max vs. Önerilen Politika backtest'i ve 3 kademeli VED ceza duyarlılık analizi (`src/evaluation/`).

## 3. Gerçekleşen Metrikler (Sprint 1 – Sprint 2)
- **ABC Dağılımı:** A: 45 (%79,9), B: 49 (%15,0), C: 106 (%5,1).
- **Kova Hassasiyeti (`DEC-05`):** Günlük -> Aylık geçişte sınıf değiştiren parça oranı: **107 / 200 (%53,5)**.
- **Segment Bazlı Kazanan Modeller (RMSSE):** Smooth: `Croston (0.738)`, Intermittent: `Croston (0.775)`, Lumpy: `Croston (0.971)`, Erratic: `SBA (0.348)`.
- **Klasik Politika Ortalamaları (CSL=%95):** Smooth SS: `14.24`, Intermittent SS: `5.34`, Lumpy SS: `11.95`, Erratic SS: `15.93`.
