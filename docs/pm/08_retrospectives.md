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

## Sprint 3 Retrospektifi (Blok Bootstrap Simülasyonu ve 365 Günlük Backtest)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti?**
  - 10.000 senaryolu Blok Bootstrap motoru, Smooth sınıfta klasik formülle örtüşürken Erratic (+6.50 ROP) ve Lumpy (+3.97 ROP) sınıflarda ağır kuyruk riskini yakaladı.
  - Kapalı 365 günlük test penceresinde `Bootstrap_CSL95`, mevcut Min/Max politikasına kıyasla baz toplam maliyeti `82.72 M TL`'den `48.46 M TL`'ye (%41,4 tasarruf) indirdi ve Fill Rate'i `%92,17`'den `%95,52`'ye yükseltti.
  - Eşit Fill Rate noktasında (`MinMax_Grid_2.0_4.0m` %95,62 vs. `Bootstrap_CSL95` %95,52) elde tutma maliyetinin `25.60 M TL`'den `18.29 M TL`'ye (%28,5 azalma) düştüğü kanıtlandı.
- **Ne İyileştirilecek?**
  - Tablo birleştirmelerinde ortak sütun adlarının (`sb_class`) açıkça seçilmesi için şema doğrulaması eklendi.
- **Sprint 4 Aksiyonu:**
  - Yönetici karar özetini, parça bazlı aksiyon listesini ve etkileşimli Streamlit karar destek uygulamasını (`app/streamlit_app.py`) oluşturmak.

## Sprint 4 Retrospektifi
- **Tarih:** 2026-11-15
- **Sonuc:** 200 SKU aksiyon plani, yonetici brifingi, Streamlit arayuzu ve final README tamamlandi (19/19 test).
