# Sprint Retrospektifleri

## Sprint 0–1 Retrospektifi (Yönetişim & Veri Segmentasyonu)
- **Ne İyi Gitti?** Sabit `seed=42` ile 1.095 günlük MRO veri üreteci ve SQLite analitik şeması kuruldu (`DEC-03`, `DEC-05`).
- **Ne İyileştirilecek?** Sentetik veri totolojisini önlemek için talep rejimi kayması ve eskime desenleri eklendi.
- **Aksiyon:** `regime_shift` ve `obsolescence` senaryoları `CHG-02` ile üretece dahil edildi.

## Sprint 2–3 Retrospektifi (Tahmin & CRN Backtest)
- **Ne İyi Gitti?** `RMSSE` + %2 basitlik toleranslı rolling-origin yarışma ve 10.000 senaryolu Ampirik Blok Bootstrap tamamlandı.
- **Ne İyileştirilecek?** İlk prototipte kayıp satış varsayımıyla (`82.72 -> 48.46 M TL`) hesaplanan maliyetler tüzükteki Backorder yapısına geçirildi.
- **Aksiyon:** Gerçek Backorder motoru ve `CSL %98` optimumu (`56.69 -> 33.01 M TL`) `CHG-05` ve `DEC-11` ile kesinleştirildi.

## Sprint 4–5 Retrospektifi (Ürünleştirme & Harici Teknik Geri Bildirim)
- **Ne İyi Gitti?** Ceza ve mod duyarlılığı (`/30`, `/7`, Kayıp Satış), yoğunlaşma analizi (ilk 5 parça hariç `%11,2`, ilk 10 hariç `%3,2`) ve sızıntısız ERP aksiyon planı tamamlandı (`20/20 birim test yeşil`).
- **Ne İyileştirilecek?** Tüm README tablolarının elle yazım yerine doğrudan CSV çıktılarından üretilmesi standartlaştırıldı.
- **Aksiyon:** `Makefile` sekme formatı onarıldı ve tüm belgeler senkronize edildi (`CHG-06`).
