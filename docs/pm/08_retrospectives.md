# Sprint Retrospektifleri

## Sprint 1 Retrospektifi (Veri Üretimi, SQLite ve Segmentasyon)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - Sabit tohumlu (`seed=42`) sentetik veri üreteci, Pareto 80/15/5 ABC dağılımını (45 A, 49 B, 106 C) ve VED kritiklik yapısını (50 V, 90 E, 60 D) tek seferde üretti.
  - Sızıntı kuralı (`DEC-05`) gereği tüm SQL görünümleri ve segmentasyon kuralları yalnızca ilk 730 günlük kalibrasyon verisine izole edildi.
  - Günlük -> aylık kova geçişinde 107/200 parçanın sınıf değiştirdiği ampirik olarak doğrulandı.
- **Ne Zorladı / Ne İyileştirilecek?**
  - PowerShell terminalinde büyük tek parça yapıştırmalar tampon sınırına takıldı; tüm kurulum komutları küçük modüler parçalara bölünerek çözüldü.
- **Sprint 2 Aksiyonu:**
  - Tahmin modellerinde özellikle talebi sıfırlanan 16 *obsolescence* parçası üzerinde TSB modelinin Croston/SBA karşısındaki davranışını izlemek.
