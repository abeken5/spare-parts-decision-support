<img width="1854" height="910" alt="image" src="https://github.com/user-attachments/assets/0fafff90-adc7-4b11-97b1-c9c7d5415986" />
﻿[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mro-spare-parts-dss.streamlit.app)

# ✈️ Savunma & Havacılık MRO Yedek Parça Envanter Optimizasyonu ve Karar Destek Sistemi

Kesikli (*intermittent*) ve ani sıçramalı (*lumpy*) talep desenlerine sahip **200 kritik MRO yedek parçası** için talep segmentasyonu, uzman zaman serisi tahmin yarışması, **10.000 senaryolu Ampirik Blok Bootstrap** simülasyonu ve **365 günlük Ortak Rastgele Sayılar (CRN) backtest** değerlendirmesi sunan uçtan uca karar destek sistemi.

---

## 1. Yönetici Özeti ve Temel Bulgular (365 Günlük Kapalı Test Penceresi)

Geleneksel Min/Max kuralları ve normal dağılım varsayan ders kitabı emniyet stoğu formülleri, haftalarca sıfır talep görüp aniden patlayan kritik yedek parçalarda ağır kuyruk (*heavy-tail*) riskini kaçırmaktadır. İlk **730 gün (24 tam takvim ayı)** üzerinde kalibre edilip hiç görülmemiş **son 365 gün** üzerinde test edilen politikaların özeti:

| Politika | Elde Tutma (M TL) | Sipariş (M TL) | Baz Stoksuzluk (M TL) | Baz Toplam Maliyet (M TL) | Gerçekleşen Fill Rate | Vital (V) Ort. Stoksuzluk |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mevcut Stilize Min/Max (`1.5 / 3.0 ay`)** | 17.23 | 1.95 | 63.54 | **82.72 M TL** | %92.17 | 2.32 gün |
| **Eşit Fill Rate Min/Max Grid (`2.0 / 4.0 ay`)** | 25.60 | 1.58 | 35.82 | **63.00 M TL** | %95.62 | 1.18 gün |
| **Klasik Normal `(s, Q)` (`CSL = %95`)** | 16.77 | 2.73 | 36.09 | **55.58 M TL** | %94.31 | 1.36 gün |
| **Önerilen Blok Bootstrap `(s, Q)` (`CSL = %95`)** | **18.29** | **3.14** | **27.02** | **48.46 M TL** | **%95.52** | **1.16 gün** |
| **Yüksek Koruma Blok Bootstrap (`CSL = %98`)** | 22.37 | 3.23 | 14.25 | **39.86 M TL** | **%97.58** | **0.56 gün** |

### Öne Çıkan 4 Metodolojik ve Finansal Çıkarım
1. **%41,4 Toplam Maliyet Tasarrufu:** `Bootstrap_CSL95`, mevcut Min/Max kuralına kıyasla toplam maliyeti `82.72 M TL`'den `48.46 M TL`'ye indirirken (**34.26 M TL net tasarruf**), hayati (`V`) parçalardaki ortalama stoksuzluk süresini **2.32 günden 1.16 güne** düşürdü.
2. **Eşit Hizmet Seviyesinde %28,5 Sermaye Verimliliği:** Mevcut Min/Max kuralını %95,6 Fill Rate seviyesine zorlamak `25.60 M TL` elde tutma maliyeti yaratırken, Blok Bootstrap aynı hizmeti `18.29 M TL` ile **%28,5 daha az işletme sermayesiyle** sağladı.
3. **Zaman Kovası Hassasiyeti (`107 / 200` Parça):** Günlük veriden aylık toplulaştırmaya geçildiğinde parçaların **%53,5'inin** Syntetos-Boylan sınıfı değişti. Bu nedenle sınıflandırma ve tahmin aylık kovada yapılırken envanter simülasyonu günlük çözünürlükte tutuldu.
4. **Seyrek Talepte MAPE Yanılgısı:** Sıfır talep aylarında klasik MAPE metriğinin `0/0` nedeniyle tanımsız/sonsuz olduğu gösterildi; model seçiminde ortalamayı koruyan **RMSSE** ve **%2 basitlik toleransı** kullanıldı.

## 2. Kurulum ve Calistirma

``bash
pip install -r requirements.txt
pytest
streamlit run app/streamlit_app.py
``


---

## 2. Bu Proje Nasil Yonetildi? (PM Artefaktlari)

Bu calisma yalnizca teknik bir modelleme degil, uctan uca proje yonetimi disipliniyle teslim edilmistir:
- [Proje Tuzugu (Charter)](docs/pm/01_project_charter.md) — Is sorusu, kapsam ve basari kriterleri
- [Veri Hazirlik Degerlendirmesi](docs/pm/02_data_readiness.md) — Sentetik veri gerekcesi (seed=42)
- [WBS ve Zaman Cizelgesi](docs/pm/03_wbs_schedule.md) — Sprint 0-4 is kirilimi
- [Paydas Haritasi ve RACI](docs/pm/04_stakeholder_raci.md) — Bakim, satin alma, finans ve yonetim rolleri
- [Risk Kaydi (R-01..10)](docs/pm/05_risk_register.md) & [Degisiklik Kaydi](docs/pm/07_change_log.md)
- [Mimari Karar Gunlugu (DEC-01..10)](docs/pm/06_decision_log.md) — Yontem secim gerekceleri
- [Yonetici Karar Brifingi](docs/executive_decision_brief.md) & [Retrospektifler](docs/pm/08_retrospectives.md)

> **Veri Seffaflik Notu:** Gizlilik ve erisim kisitlari nedeniyle projede savunma/havacilik MRO dinamiklerini (kesikli talep, rejim kaymasi ve kullanimdan kalkma) yansitan sabit tohumlu (seed=42) sentetik veri kullanilmistir.
