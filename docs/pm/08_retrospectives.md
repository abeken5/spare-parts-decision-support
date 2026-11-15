# Sprint Retrospektifleri

## Sprint 0–2 Retrospektifi
- **Ne İyi Gitti.** Sabit `seed=42` ile 1.095 günlük MRO veri üreteci, SQLite şeması ve `RMSSE` + %2 basitlik toleranslı tahmin yarışması kuruldu (`DEC-05`, `DEC-07`).

## Sprint 3–4 Retrospektifi
- **Ne İyi Gitti.** 10.000 senaryolu Ampirik Blok Bootstrap (`CSL %85–%99.5`) ve 365 günlük CRN backtest motoru kuruldu.
- **Düzeltme Notu (`CHG-05`, `DEC-11`):** İlk prototip kayıp satış varsayımıyla (`82.72 -> 48.46 M TL`) hesaplanmıştı; sonradan gerçek **Backorder** takibine ve `CSL %98` optimumuna güncellenerek `56.69 -> 33.01 M TL` (%41,8 tasarruf) olarak kesinleştirildi.

## Sprint 5 Retrospektifi (Bağımsız Denetim ve Kapanış)
- **Tarih:** 2026-11-15
- **Ne İyi Gitti.** Ceza tanımı duyarlılığı (`/30`, `/7`, tek seferlik), yoğunlaşma analizi (ilk 5 ve 10 parça hariç), 20-tohum dayanıklılığı ve sızıntısız ERP aksiyon planı tamamlandı (`20/20 birim test yeşil`).
