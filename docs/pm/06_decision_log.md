# Karar Günlüğü (Decision Log)

| Karar ID | Tarih | Konu | Seçilen Karar | Gerekçe |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-01** | 2026-11-14 | Dil Standardı | **Türkçe doküman/UI + İngilizce kod** | İşe alım uzmanları için net okunabilirlik, kod tabanında evrensel Python standardı. |
| **DEC-02** | 2026-11-14 | Maliyet ve Ceza Yapısı | **3 kalemli maliyet, Backorder, VED bazlı ceza + 3 senaryolu duyarlılık** | Satın alma maliyeti backorder altında sabittir; duyarlılık analizi varsayım yanlılığını önler. |
| **DEC-03** | 2026-11-14 | Veritabanı | **SQLite** | Kurulumsuz, taşınabilir ve analitik SQL görünümleri yazmaya uygun yapı. |
| **DEC-04** | 2026-11-14 | Tekrar Üretilebilirlik | **`RANDOM_SEED = 42`** | Veri üretimi ve simülasyon sonuçlarının her çalıştırmada birebir doğrulanabilmesi. |

| **DEC-05** | 2026-11-15 | Veri Çözünürlüğü ve Sızıntı Kuralı | **1.095 gün üretim (730 gün kalibrasyon, 365 gün backtest); günlük simülasyon + aylık tahmin hibriti** | Stoksuzluk günü ve gün cinsinden lead-time dağılımı için günlük veri şarttır. Aylık toplulaştırma yalnızca ADI/CV² ve tahmin modelleri için takvim günleriyle yapılır. Tüm parametreler yalnızca ilk 730 günden hesaplanır. |
| **DEC-06** | 2026-11-15 | Mevcut Politika (Baseline) Tanımı | **Stilize kaba kural: Min = 1.5 ay, Max = 3.0 ay eğitim ortalaması (günlük kontrol, backorder)** | Gerçek şirket verisi değil, stilize kuraldır. Saman adam (strawman) etkisini önlemek için lead time dağılımları 7-42 gün aralığında kalibre edildi; ayrıca 1/2, 1.5/3, 2/4 ay duyarlılık gridi ve ortak rastgele sayılar (CRN) uygulanacak. |
