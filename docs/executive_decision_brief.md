# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu

## 1. Yönetici Özeti ve Duyarlılık Bulguları (365 Günlük Kapalı Test)
- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — Politika Hedefi **CSL = %95** (Tüzük Başarı Kriteri: min. %15 maliyet düşüşü -> **Karşılandı**)
- **Backorder (Birincil Model) Toplam Maliyet Etkisi:** Mevcut Min/Max `56.69 M TL` -> Bootstrap CSL %95 `33.7 M TL` (**22.99 M TL / %40.6 tasarruf**). Kayıp Satış (*Lost Sales*) duyarlılığında tasarruf **%36.8** (`81.93 M TL` -> `51.77 M TL`).
- **Adil Kıyas (Klasik Formül & Ayarlı Min/Max):** Klasik normal `(s, Q)` formülüne (`35.49 M TL`) göre **%5.0**, eşit hizmet seviyesindeki `2.0/4.0 ay` Min/Max kuralına (`47.93 M TL`) göre **%29.7** toplam maliyet avantajı sağlanmıştır (`3.0/6.0 ay` ayarlı Min/Max: `47.47 M TL`).
- **Hizmet ve Vital (V) Risk Etkisi:** Portföy Fill Rate `%91.36` -> `%93.96`; hayati (`V`) parçalarda ortalama açık sipariş günü `22.22 gün` -> `9.0 gün` (**%59.5 azalma**).

## 2. Yoğunlaşma ve Çoklu Tohum Dayanıklılığı
- **Tum Portfoy Tasarruf (200 SKU, Backorder):** `%40.5` (22.99 M TL net tasarruf)
- **Ilk 5 Parca Haric Tasarruf (195 SKU):** `%14.2` (En yuksek 5 tasarruf parcasi cikarildiginda)
- **Ilk 10 Parca Haric Tasarruf (190 SKU):** `%5.7` (En yuksek 10 tasarruf parcasi cikarildiginda)
- **20-Seed MinMax'e Karsi Tasarruf Araligi:** `%37.1` (Min %30.2 - Max %42.0)
- **20-Seed Klasik Formule Karsi Tasarruf Araligi:** `%6.4` (Min %3.7 - Max %9.4)

## 3. Parça Bazlı Aksiyon Dağılımı (200 SKU — Sıfır Test Sızıntısı)
- **Hizmet Koruması (ROP Yükselt):** 81 parça
- **Vital Koruma (ROP Yükselt):** 46 parça
- **Aşırı Stoğu Erit (Sermaye Çöz):** 46 parça
- **Dengeli (s, Q Geçişi):** 20 parça
- **Düşük Hız / Eskime İzleme (Manuel Onay):** 7 parça

## 4. Uygulama ve Bütçe Seçeneği
- **Politika Hedefi Notu:** Ceza katsayıları altında toplam maliyet CSL arttıkça düşmeye devam ettiği için `%95` (`33.7 M TL`) işletme sermayesi disiplini adına politika hedefi seçilmiştir; bütçe elverdiğinde `%98` (`33.01 M TL`, `5.9 gün` Vital açık sipariş) önerilir.
- Düşük hızlı / eskime riski taşıyan parçalar otomatik yenilemeye kapatılarak bakım mühendisliği onayına bağlanmalıdır (`R-04`).