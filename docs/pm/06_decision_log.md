# Karar Günlüğü (Decision Log)

| Karar ID | Tarih | Konu | Seçilen Karar | Gerekçe |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-01** | 2026-11-14 | Dil Standardı | **Türkçe doküman/UI + İngilizce kod** | İşe alım uzmanları için net okunabilirlik, kod tabanında evrensel Python standardı. |
| **DEC-02** | 2026-11-14 | Maliyet ve Ceza Yapısı | **3 kalemli maliyet, Backorder, VED bazlı ceza + 3 senaryolu duyarlılık** | Satın alma maliyeti backorder altında sabittir; duyarlılık analizi varsayım yanlılığını önler. |
| **DEC-03** | 2026-11-14 | Veritabanı | **SQLite** | Kurulumsuz, taşınabilir ve analitik SQL görünümleri yazmaya uygun yapı. |
| **DEC-04** | 2026-11-14 | Tekrar Üretilebilirlik | **`RANDOM_SEED = 42`** | Veri üretimi ve simülasyon sonuçlarının her çalıştırmada birebir doğrulanabilmesi. |
| **DEC-05** | 2026-11-15 | Veri Çözünürlüğü ve Sızıntı Kuralı | **1.095 gün üretim (730 gün kalibrasyon, 365 gün backtest)** | Tüm parametreler yalnızca ilk 730 günden hesaplanır (`assert` ile korunur). |
| **DEC-06** | 2026-11-15 | Mevcut Politika (Baseline) Tanımı | **Stilize kaba kural: Min = 1.5 ay, Max = 3.0 ay + 4 kademeli duyarlılık gridi** | Saman adam etkisini önlemek için `1/2..3/6 ay` gridi ve ortak rastgele sayılar (CRN) uygulanır. |
| **DEC-07** | 2026-11-15 | Tahmin Yarışması ve Seçim Kuralı | **18 ay eğitim / 6 ay rolling-origin doğrulama; RMSSE (%2 basitlik toleransı)** | MASE seyrek talepte sıfır medyanı ödüllendirdiği için RMSSE seçildi; MAPE tanımsızdır. |
| **DEC-08** | 2026-11-15 | Takvim Dönüşümü ve Klasik Formüller | **Tüm girdiler gün biriminde (`730 gün = 24 tam takvim ayı`); gerçekleşen L ve σL** | Oracle sızıntısı önlenir; klasik politika `(s, Q)`, mevcut Min/Max `(s, S)` yapısındadır. |
| **DEC-09** | 2026-11-15 | Simülasyon Yöntemi (Blok Bootstrap) | **730 günlük seriden ardışık L* günlük blok bootstrap (10.000 senaryo, seed=42)** | Otokorelasyonu ve `regime_shift` kuyruk riskini koruyarak ampirik dağılım üretir. |
| **DEC-10** | 2026-11-15 | Adil Kıyas & Başlangıç Stoğu | **CSL %85–%99.5 + Genişletilmiş Min/Max gridi + CRN + Eşit Başlangıç Stoğu** | Tüm politikalarda başlangıç stoğu `min_stock` olarak eşitlenerek yanlılık sıfırlandı. |
| **DEC-11** | 2026-11-15 | Ceza Tanımı Duyarlılığı & CSL %98 | **Birincil `/30` günlük ceza + `/7` ve Kayıp Satış duyarlılığı; önerilen `Bootstrap_CSL98`** | `CSL %98`, birincil `/30` altında maliyet minimumudur (`33.01 M TL`), `%95` Fill Rate guardrail'ini sağlayan en düşük CSL'dir (`%96.00`) ve `/30`, `/7` ile Kayıp Satış modlarında ayarlı `3/6 ay` Min/Max'ı yener (`33.01 vs 47.47`, `59.22 vs 73.26`, `46.51 vs 59.88 M TL`). |
