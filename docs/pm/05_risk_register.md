# İş Kırılım Yapısı (WBS) ve 6 Haftalık Takvim

- **Sprint 0 (Hafta 1):** Yönetişim dokümanları (Tüzük, RACI, Risk, Karar Günlüğü), repo iskeleti, CI ve GitHub Projects.
- **Sprint 1 (Hafta 2):** Sentetik veri üreteci (`generator.py`), SQLite şeması, ABC/KPI SQL görünümleri, ABC-XYZ ve ADI/CV² sınıflandırma + testler.
- **Sprint 2 (Hafta 3):** Naive, MA, Croston, SBA, TSB tahmin modelleri; MAE/RMSE/MASE kıyaslaması ve MAPE yanılgısı analizi; klasik SS/ROP/EOQ + testler.
- **Sprint 3 (Hafta 4):** Bootstrap / Monte Carlo simülasyonu, klasik formülle karşılaştırma, Min/Max backtest ve 3 senaryolu ceza duyarlılık analizi.
- **Sprint 4 (Hafta 5):** Streamlit karar destek arayüzü ve Yönetici Özeti (`09_executive_summary.md`).
- **Sprint 5 (Hafta 6):** Uçtan uca doğrulama, Streamlit Community Cloud yayını, README finalizasyonu ve retrospektif.

```mermaid
gantt
    title MRO Yedek Parça Karar Destek Sistemi (6 Hafta)
    dateFormat  YYYY-MM-DD
    section Sprintler
    Sprint 0 - PM ve Altyapı          :active, s0, 2026-11-14, 7d
    Sprint 1 - Veri ve Segmentasyon   :s1, 2026-11-21, 7d
    Sprint 2 - Tahmin ve Klasik SS    :s2, 2026-11-28, 7d
    Sprint 3 - Simülasyon ve Backtest :s3, 2026-12-05, 7d
    Sprint 4 - Streamlit ve Özet      :s4, 2026-12-12, 7d
    Sprint 5 - Yayın ve Kapanış       :s5, 2026-12-19, 7d
@'
# Risk Kaydı (Risk Register)

| ID | Risk Tanımı | Olasılık | Etki | Azaltma Planı (Mitigation) | Durum |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **R-01** | **Ceza maliyeti varsayımsal, sonuç duyarlı:** Yüksek ceza seçilirse önerilen politika yapay olarak avantajlı görünebilir. | Yüksek | Yüksek | VED kritiklik bazlı ceza tablosu ve 3 senaryolu (Düşük/Baz/Yüksek) duyarlılık analizi ile başabaş noktası raporlanacak. | Aktif |
| **R-02** | **Gerçek MRO verisine erişim kısıtı:** Gizlilik nedeniyle açık savunma/havacılık verisi bulunamaması. | Yüksek | Orta | Literatür parametrelerine sadık, sabit seed'li sentetik veri üreteci geliştirildi ve DEC-02'ye işlendi. | Gerçekleşti |
| **R-03** | **Model karmaşıklığının baseline'ı geçememesi:** Croston/TSB'nin aşırı seyrek parçalarda hareketli ortalamayı yenememesi. | Orta | Orta | Segment bazlı en iyi model seçilecek; yenemediği durumlar dürüstçe raporlanacak. | İzleniyor |
| **R-04** | **Son kullanıcı benimseme riski:** Planlamacıların simülasyona güvenmeyip Excel Min/Max'a dönmesi. | Orta | Yüksek | Arayüzde mevcut Min/Max ile önerilen politika TL ve stoksuzluk günü farkıyla yan yana şeffaf sunulacak. | İzleniyor |
