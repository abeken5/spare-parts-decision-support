# Savunma ve Havacılık MRO Yedek Parça Karar Destek Sistemi

[![CI](https://github.com/abeken5/spare-parts-decision-support/actions/workflows/ci.yml/badge.svg)](https://github.com/abeken5/spare-parts-decision-support/actions)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mro-spare-parts-dss.streamlit.app)

Seyrek (*intermittent*) ve ani sıçramalı (*lumpy*) talebe sahip 200 MRO yedek parçası için **ABC-XYZ + VED + Syntetos-Boylan (`ADI/CV²`)** segmentasyonu, tahmin yarışması (`RMSSE`), **10.000 senaryolu Ampirik Blok Bootstrap** ve **365 günlük kapalı CRN backtest** motorunu birleştiren karar destek sistemi.

## 1. Yönetici Özeti ve Temel Bulgular (365 Günlük Kapalı Test)

> **Başlık Sonucu:** Mevcut Min/Max kuralına göre **%41,8 toplam maliyet tasarrufu** (`56.69` -> `33.01 M TL`; ilk 5 parça hariç **%14,2**), klasik normal `(s, Q)` formülüne göre **%7,0** maliyet avantajı sağlanmıştır. Ayarlı Min/Max (`3/6 ay`) karşısındaki üstünlük ceza tanımına duyarlı olup **`Bootstrap_CSL98` politikasında her üç ceza tanımında da (`/30`, `/7`, tek seferlik) korunmaktadır** (`DEC-11`).

| Politika | Elde Tutma (M TL) | Sipariş (M TL) | Ceza (M TL) | Toplam Baz (M TL) | Fill Rate | Vital Açık Sipariş |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mevcut Min/Max (1.5 / 3.0 ay)** | 19.34 | 1.98 | 35.37 | **56.69** | %91.36 | 22.22 gün |
| **Ayarlı Min/Max (3.0 / 6.0 ay)** | 38.21 | 1.12 | 8.14 | **47.47** | %97.76 | 4.82 gün |
| **Klasik Normal (s, Q) CSL %95** | 21.84 | 2.65 | 11.00 | **35.49** | %93.54 | 10.45 gün |
| **Bootstrap (s, Q) CSL %95** | 21.15 | 2.68 | 9.87 | **33.70** | %93.96 | 9.00 gün |
| **Önerilen: Bootstrap (s, Q) CSL %98** | 24.18 | 2.61 | 6.22 | **33.01** | **%96.00** | **5.90 gün** |

- **Ceza Tanımı Duyarlılığı (`DEC-11`):** Günlük `/30` (`33.01 vs 47.47 M TL`), haftalık `/7` (`59.22 vs 73.26 M TL`) ve tek seferlik (`51.74 vs 60.11 M TL`) tanımlarının tamamında `Bootstrap_CSL98` ayarlı Min/Max (`3/6 ay`) kuralını yenmektedir (`data/processed/backtest_mode_comparison.csv`).
- **Eskime Dürüstlük Notu (`R-09`):** 16 eskime parçasının hiçbirinde TSB kazanmamıştır.

## 2. Kurulum (`Makefile`)
```bash
make setup && make pipeline && make test && make demo
```

## 3. PM Yönetişim Artefaktları
- [Proje Tüzüğü](docs/pm/01_charter.md) | [Veri Hazırlık](docs/pm/02_data_readiness.md) | [WBS & Takvim](docs/pm/03_wbs_schedule.md) | [RACI](docs/pm/04_stakeholder_raci.md) | [Risk Kaydı](docs/pm/05_risk_register.md) | [Karar Günlüğü](docs/pm/06_decision_log.md) | [Değişiklik Kaydı](docs/pm/07_change_log.md) | [Retrospektifler](docs/pm/08_retrospectives.md) | [Yönetici Özeti](docs/pm/09_executive_summary.md) | [Metodoloji](docs/methodology.md)
