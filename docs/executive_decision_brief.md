# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu

## 1. Temel Karar Önerisi
- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — Hedef Döngü Hizmet Seviyesi **CSL = %95**
- **Yıllık Toplam Maliyet Etkisi (Baz Senaryo):** `82.72 M TL` -> `48.46 M TL` (**34.26 M TL / %41.4 tasarruf**)
- **Hizmet Seviyesi (Fill Rate) Etkisi:** `%92.17` -> `%95.52` (+3.35 puan)
- **Vital (V) Parça Stoksuzluk Riski:** `2.32 gün` -> `1.16 gün` (%50 azalma)
- **Eşit Fill Rate Sermaye Verimliliği:** Mevcut kuralı %95,6 Fill Rate'e zorlamak (`2.0/4.0 ay`) `25.6 M TL` elde tutma maliyeti yaratırken, Bootstrap `18.29 M TL` ile aynı hizmeti **%28,5 daha az işletme sermayesiyle** sağlar.

## 2. Parça Bazlı Aksiyon Dağılımı (200 SKU)
- **Kritik Stok Artışı (ROP Yükselt):** 91 parça
- **Dengeli (s, Q Geçişi):** 56 parça
- **Aşırı Stoğu Erit (Sermaye Çöz):** 46 parça
- **Düşük Hız / Eskime İzleme (Manuel Onay):** 7 parça

## 3. Uygulama ve Yönetişim Notu
- Düşük hızlı / eskime riski taşıyan parçalar otomatik yenilemeye kapatılarak bakım mühendisliği onayına bağlanmalıdır (`R-04`).
- Yıllık bütçe kısıtına göre CSL seviyesi `%95` (`48.46 M TL` toplam maliyet) ile `%98` (`39.86 M TL` toplam maliyet, `0.56 gün` Vital stoksuzluk) arasında seçilebilir.