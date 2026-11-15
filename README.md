# Savunma ve Havacılık MRO Yedek Parça Karar Destek Sistemi

[![CI](https://github.com/abeken5/spare-parts-decision-support/actions/workflows/ci.yml/badge.svg)](https://github.com/abeken5/spare-parts-decision-support/actions)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mro-spare-parts-dss.streamlit.app)

## 1. Yönetici Özeti (365 Günlük Kapalı Test)

> **Başlık Sonucu (`Bootstrap_CSL98`):** Mevcut Min/Max kuralına göre **%41.8 toplam tasarruf** (`56.69` -> `33.01 M TL`), klasik `(s, Q)` formülüne göre **%7.0** avantaj sağlanmıştır (`DEC-11`). Sonucun yüksek birim maliyetli birkaç Vital parçada yoğunlaştığı açıkça raporlanmıştır: en yüksek tasarruflu ilk 5 parça hariç net tasarruf **%11.2** (tüzüğün %15 eşiğinin altında), ilk 10 parça hariç **%3.2** seviyesindedir.

| Politika | Elde Tutma (M TL) | Sipariş (M TL) | Ceza (M TL) | Toplam Baz (M TL) | Fill Rate | Vital Açık Sipariş |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `MinMax_Current_1.5_3.0m` | 16.9 | 2.29 | 37.5 | **56.69** | %91.36 | 22.22 gün |
| `MinMax_Grid_3.0_6.0m` | 38.27 | 1.35 | 7.85 | **47.47** | %97.18 | 6.7 gün |
| `Classical_Hist_CSL95` | 15.75 | 3.21 | 16.53 | **35.49** | %92.87 | 11.06 gün |
| `Bootstrap_CSL95` | 17.11 | 3.86 | 12.73 | **33.7** | %93.96 | 9.0 gün |
| `Bootstrap_CSL98` | 21.02 | 4.01 | 7.98 | **33.01** | %96.0 | 5.9 gün |

- **Guardrail:** Fill Rate `%91.36` -> **`%96.0`**; Vital açık sipariş `22.22` -> **`5.9 gün`** (**%73.4 azalma**).
- **Ceza & Mod Duyarlılığı (`DEC-11`):** Backorder `/30` (`33.01` vs `47.47 M TL`), Backorder `/7` (`59.22` vs `73.26 M TL`) ve Kayıp Satış (`46.51` vs `59.88 M TL`) altında `Bootstrap_CSL98` ayarlı Min/Max (`3/6 ay`) kuralını yenmektedir.

## 2. Kurulum & PM Dokümanları
```bash
make setup && make pipeline && make test && make demo
```
- [Tüzük](docs/pm/01_charter.md) | [Veri](docs/pm/02_data_readiness.md) | [WBS](docs/pm/03_wbs_schedule.md) | [RACI](docs/pm/04_stakeholder_raci.md) | [Risk](docs/pm/05_risk_register.md) | [Kararlar](docs/pm/06_decision_log.md) | [Değişiklik](docs/pm/07_change_log.md) | [Retro](docs/pm/08_retrospectives.md) | [Özet](docs/pm/09_executive_summary.md) | [Metodoloji](docs/methodology.md)
