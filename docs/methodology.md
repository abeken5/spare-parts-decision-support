# Metodoloji Dokümanı

1. **Veri Ayrımı (`DEC-05`):** 1.095 günlük seri `730 gün` kalibrasyon (`is_backtest=0`) ve `365 gün` kapalı test (`is_backtest=1`) olarak ayrılır.
2. **Segmentasyon:** ABC-XYZ ve VED sınıflandırması ile Syntetos-Boylan (`ADI = 1.32`, `CV² = 0.49`) matrisi uygulanır (`Smooth: 84`, `Intermittent: 87`, `Lumpy: 27`, `Erratic: 2` — *Erratic n=2 olduğu için sınıf ortalamaları ihtiyatla yorumlanır*).
3. **Tahmin Yarışması (`DEC-07`):** 18 ay eğitim / 6 ay *rolling-origin* doğrulamada Naive, MA_3, Croston, SBA ve TSB modelleri `RMSSE` ve **%2 basitlik toleransı** ile yarışır. 16 *obsolescence* parçasının hiçbirinde TSB kazanmamıştır (`R-09`).
4. **Ampirik Blok Bootstrap (`DEC-09`):** 730 günlük seriden gerçekleşen tedarik süresi $L^*$ kadar ardışık bloklar 10.000 kez örneklenir (`CSL %85–%99.5`).
5. **CRN Backtest & Duyarlılık (`DEC-02`, `DEC-11`):** Ortak Rastgele Sayılar (CRN) ve eşit başlangıç stoğu altında gerçek **Backorder** (`/30` günlük ve `/7` haftalık) ile **Tek Seferlik / Kayıp Satış** modları, yoğunlaşma (ilk 5 ve 10 parça hariç) ve 20-tohum aralıklarıyla değerlendirilir.
