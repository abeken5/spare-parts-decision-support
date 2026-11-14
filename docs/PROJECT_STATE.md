# PROJECT_STATE.md — Proje Canlı Durum Özeti

- **Son Güncelleme:** 2026-11-15
- **Aktif Faz:** Sprint 1 Tamamlandı -> Sprint 2 (Tahmin Modelleri & Klasik SS/ROP/EOQ) Başlangıcı

## 1. Tamamlanan İşler
- **Sprint 0:** Proje Tüzüğü, Veri Hazırlık, WBS, RACI, Risk Kaydı, Karar Günlüğü, Değişiklik Kaydı ve CI (`pytest`) kuruldu.
- **Sprint 1:**
  - `data/generator.py` ile 200 parça, 219.000 günlük talep satırı, 5.000 tedarik süresi kaydı ve stilize Min/Max politikası üretildi.
  - `sql/schema.sql`, `sql/abc_analysis.sql`, `sql/kpi_views.sql` ve `src/ingestion/load_sqlite.py` ile SQLite analitik veritabanı (`mro_inventory.db`) kuruldu.
  - `src/segmentation/classify.py` ile ABC-XYZ ve Syntetos-Boylan (`ADI/CV²`) sınıflandırması tamamlandı ve 4 birim test doğrulandı.
  - Sprint 1 Retrospektifi (`08_retrospectives.md`) eklendi.

## 2. Sıradaki İşler (Sprint 2)
- Naive, 3-Aylık Hareketli Ortalama, Croston, SBA ve TSB tahmin modellerinin kodlanması (`src/forecasting/`).
- MAE, RMSE, MASE kıyaslaması ve seyrek talepte MAPE yanılgısı analizi.
- Klasik Safety Stock, ROP ve EOQ modülü (`src/inventory/`) + birim testler.

## 3. Açık Riskler ve Kararlar
- **Açık Riskler:** R-01 (Ceza duyarlılığı), R-03 (Baseline kıyaslaması), R-04 (Kullanıcı benimsemesi), R-05 (24 aylık eğitim penceresi).
- **Kararlar:** DEC-01 – DEC-06 aktif.

## 4. Gerçekleşen Metrikler (Sprint 1)
- **ABC Dağılımı (Yıllık Kullanım Hacmi ~557,6 Milyon TL):** A: 45 parça (%79,9), B: 49 parça (%15,0), C: 106 parça (%5,1).
- **Syntetos-Boylan (Aylık Kova):** Intermittent: 87, Smooth: 84, Lumpy: 27, Erratic: 2.
- **Kova Hassasiyeti (`DEC-05`):** Günlük -> Aylık toplulaştırmada sınıfı değişen parça oranı: **107 / 200 (%53,5)**.
