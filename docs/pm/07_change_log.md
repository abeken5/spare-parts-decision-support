# Değişiklik Kaydı (Change Log)

| ID | Tarih | Bileşen | Önceki Durum | Yeni Durum | Gerekçe |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CHG-01** | 2026-11-14 | Veri Kapsamı | 500 SKU / 5 yıl | **200 SKU / 1.095 gün (2 yıl eğitim + 1 yıl test)** | İnteraktif simülasyon hızı ve sızıntısız test ayrımı (`DEC-05`). |
| **CHG-02** | 2026-11-15 | Sentetik Üreteç | Sabit talep | **`regime_shift` ve `obsolescence` desenleri** | Totoloji riskini (`R-06`) ve TSB modelini test etmek için. |
| **CHG-03** | 2026-11-15 | Tahmin Kriteri | MASE / MAPE | **RMSSE + %2 basitlik toleransı** | Seyrek talepte sıfır medyan yanılgısını önlemek için (`DEC-07`). |
| **CHG-04** | 2026-11-15 | Teslimat Takvimi | 6 haftalık yayılı | **14–15 Kasım yoğunlaştırılmış teslimat** | Tek kişilik portföy geliştirmede kilometre taşları 2 günde tamamlandı. |
| **CHG-05** | 2026-11-15 | Backtest & Ceza | Tek modlu simülasyon | **Gerçek Backorder (`/30`, `/7`) + Tek Seferlik duyarlılık ve `CSL %98`** | Tüzük uyumu, guardrail (`%96.0` Fill Rate) ve ceza tanımı sağlamlığı (`DEC-11`). |
