# Yönetici Karar Özeti — MRO Yedek Parça Envanter Optimizasyonu

## 1. Yönetici Özeti ve Guardrail Doğrulaması (365 Günlük Kapalı Test)
- **Önerilen Politika:** Ampirik Blok Bootstrap `(s, Q)` — **CSL = %98** (CSL %95: `33.7 M TL`, CSL %98: `33.01 M TL`, CSL %99: `33.47 M TL`).
- **Tüzük Başarı Kriteri (%15 Maliyet Düşüşü):** **Karşılandı** — Mevcut Min/Max `56.69 M TL` -> Bootstrap CSL %98 `33.01 M TL` (**23.68 M TL / %41.8 tasarruf**).
- **Guardrail (%95 Fill Rate):** **Karşılandı** — Fill Rate `%91.36` -> `%96.0`; Vital açık sipariş günü `22.22` -> `5.9 gün` (**%73.4 azalma**).
- **Adil Kıyas:** Klasik `(s, Q)` formülüne (`35.49 M TL`) göre **%7.0**, ayarlı `3.0/6.0 ay` Min/Max kuralına (`47.47 M TL`) göre **%30.5** avantaj.

## 2. Ceza Tanımı Duyarlılığı (`DEC-11`)
- **Günlük `/30` Backorder Cezası:** CSL98 `33.01 M TL` vs. Min/Max 3/6 `47.47 M TL` (Mevcut: `56.69 M TL`).
- **Haftalık `/7` Backorder Cezası:** CSL98 `59.22 M TL` vs. Min/Max 3/6 `73.26 M TL` (Mevcut: `179.9 M TL`).
- **Kayıp Satış (Lost Sales):** CSL98 `46.51 M TL` vs. Min/Max 3/6 `59.88 M TL` (Mevcut: `81.93 M TL`).

## 3. Yoğunlaşma ve Çoklu Tohum Dayanıklılığı
- **Tum Portfoy Tasarruf (200 SKU, Backorder):** `%41.8` (23.68 M TL net tasarruf)
- **Ilk 5 Parca Haric Tasarruf (195 SKU):** `%11.2` (En yuksek 5 tasarruf parcasi cikarildiginda)
- **Ilk 10 Parca Haric Tasarruf (190 SKU):** `%3.2` (En yuksek 10 tasarruf parcasi cikarildiginda)
- **20-Seed MinMax'e Karsi Tasarruf Araligi:** `%38.4` (Min %33.3 - Max %43.3)
- **20-Seed Klasik Formule Karsi Tasarruf Araligi:** `%7.9` (Min %4.2 - Max %11.7)

## 4. Parça Bazlı Aksiyon Dağılımı (200 SKU — Sıfır Test Sızıntısı)
- **Hizmet Koruması (ROP Yükselt):** 106 parça
- **Vital Koruma (ROP Yükselt):** 48 parça
- **Aşırı Stoğu Erit (Sermaye Çöz):** 31 parça
- **Dengeli (s, Q Geçişi):** 8 parça
- **Düşük Hız / Eskime İzleme (Manuel Onay):** 7 parça