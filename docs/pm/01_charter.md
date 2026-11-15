# Proje Tüzüğü (Project Charter)

## 1. Proje Kimliği
- **Proje Adı:** Savunma ve Havacılık MRO Yedek Parça Envanter Karar Destek Sistemi
- **Proje Yöneticisi:** Ahmet Elvan Beken
- **Süre ve Dil:** 6 Hafta (Sprint 0 – Sprint 5) | Doküman/UI Türkçe, kod İngilizce (`snake_case`).

## 2. İş Problemi ve Amaç
Bakım-onarım (MRO) operasyonlarında yedek parça talebi seyrek (*intermittent*) ve ani sıçramalıdır (*lumpy*). Sabit Excel Min/Max kuralları ve normal dağılım varsayan klasik *Safety Stock* formülleri sıfır talep dönemlerini ve değişken tedarik sürelerini yönetemez.

**Temel İş Sorusu:** *"Parça bazında ne zaman, ne kadar sipariş verilmeli ve mevcut Min/Max politikası yerine önerilen politika, hedef hizmet seviyesini koruyarak toplam maliyeti ne kadar düşürür?"*

## 3. Başarı Kriterleri ve Koruyucu Kısıt (Guardrail)
1. **Birincil Hedef:** Önerilen politikanın mevcut Min/Max politikasına göre toplam envanter maliyetini **en az %15** düşürmesi *(kesin eşik Sprint 1 veri kalibrasyonu sonrası %15 olarak kilitlenmiştir)*.
2. **Koruyucu Kısıt (Guardrail):** Her backtest çıktısında **Fill Rate**, **Cycle Service Level** ve **Açık Sipariş Günü** yan yana raporlanır; `%95` Fill Rate eşiğinin altına düşen politika elenir.

## 4. Maliyet Modeli (`DEC-02`, `DEC-11`)
1. **Elde Tutma Maliyeti:** Ortalama Eldeki Stok x Birim Maliyet x %22 (Yıllık).
2. **Sipariş Maliyeti:** Verilen Sipariş Sayısı x 1.500 TL.
3. **Stoksuzluk Cezası (Backorder):** Birincil modelde açık backorder miktarı aylık bekleme oranıyla (`/30`) günlük cezalandırılır; `/7` haftalık ve tek seferlik ceza tanımları duyarlılık olarak raporlanır (`DEC-11`).
4. **Kapsam Dışı Maliyet:** Birim satın alma maliyeti backorder altında sabit kaldığı için hariç tutulmuştur.

### Kritiklik (VED) Bazlı Ceza ve 3 Senaryolu Duyarlılık Matrisi
| Kritiklik | Operasyonel Etki | Düşük (0.5x) | Baz (1.0x) | Yüksek (2.0x) |
| :--- | :--- | :--- | :--- | :--- |
| **V — Vital** | Ekipmanı yerde tutar (AOG) | Fiyat x 0.75 | **Fiyat x 1.50** | Fiyat x 3.00 |
| **E — Essential** | Bakım takvimini geciktirir | Fiyat x 0.375 | **Fiyat x 0.75** | Fiyat x 1.50 |
| **D — Desirable** | Rutin sarf / ikame edilebilir | Fiyat x 0.125 | **Fiyat x 0.25** | Fiyat x 0.50 |

## 5. Gerçekleşen Backtest Sonucu (`CHG-06`, `DEC-11`)
- 365 günlük kapalı testte `Bootstrap_CSL98` toplam maliyeti `%41,8` düşürmüş ve `%96,00` Fill Rate ile `%95` guardrail eşiğini sağlamıştır.
