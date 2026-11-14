# Sprint Retrospektifleri

## Sprint 1 Retrospektifi (Veri Üretimi, SQLite ve Segmentasyon)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - Sabit tohumlu (`seed=42`) veri üreteci Pareto 80/15/5 ABC dağılımını (45 A, 49 B, 106 C) ve VED yapısını (50 V, 90 E, 60 D) tek seferde üretti.
  - Sızıntı kuralı (`DEC-05`) gereği SQL görünümleri ve segmentasyon yalnızca ilk 730 günlük kalibrasyon verisine izole edildi.
  - Günlük -> aylık kova geçişinde 107/200 parçanın (%53,5) sınıf değiştirdiği ampirik olarak doğrulandı.
- **Ne İyileştirilecek?**
  - PowerShell yapıştırma tamponu sınırını aşmamak için komut blokları modüler parçalara bölündü.
- **Sprint 2 Aksiyonu:**
  - Seyrek talepte sıfır-medyan tuzağını önlemek için seçim kriteri olarak RMSSE kullanmak ve TSB'nin *obsolescence* parçalarındaki davranışını raporlamak.

## Sprint 2 Retrospektifi (Tahmin Yarışması ve Klasik SS/ROP/EOQ)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - 5 aday model (Naive, MA_3, Croston, SBA, TSB) rolling-origin 6 aylık doğrulamadan geçirildi; Croston ve SBA tüm sınıflarda en düşük RMSSE değerlerini aldı.
  - Seyrek talepte MAPE'nin sıfıra bölme nedeniyle tanımsız kaldığı sayısal olarak doğrulandı.
  - Klasik SS/ROP/EOQ modülü gün biriminde kuruldu; 12 birim testin tamamı yeşil geçti.
- **Ne İyileştirilecek?**
  - Lumpy sınıfta nokta tahmin hatasının (`RMSSE = 0.971`) ve negatif bias'ın (`-1.95`) yüksek kalması, nokta tahmin yerine ampirik lead-time talep dağılımı simülasyonunun gerekliliğini doğruladı.
- **Sprint 3 Aksiyonu:**
  - Günlük talep ve gerçekleşen lead time kayıtlarından ampirik Bootstrap simülasyonu kurarak klasik normal dağılım formülü ile farkını ölçmek ve Ortak Rastgele Sayılar (CRN) ile adil backtest yapmak.
