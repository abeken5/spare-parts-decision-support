# Proje Tüzüğü (Project Charter)

## 1. Proje Kimliği
- **Proje Adı:** Savunma ve Havacılık MRO Yedek Parça Envanter Karar Destek Sistemi
- **Proje Yöneticisi:** Ahmet Elvan Beken
- **Süre ve Dil:** 6 Hafta (Sprint 0 – Sprint 5) | Doküman/UI Türkçe, kod İngilizce (`snake_case`).

## 2. İş Problemi ve Amaç
Bakım-onarım (MRO) operasyonlarında yedek parça talebi seyrek (*intermittent*) ve ani sıçramalıdır (*lumpy*). Sabit Excel Min/Max kuralları ve normal dağılım varsayan klasik *Safety Stock* formülleri sıfır talep dönemlerini ve değişken tedarik sürelerini yönetemez.

**Temel İş Sorusu:** *"Parça bazında ne zaman, ne kadar sipariş verilmeli ve mevcut Min/Max politikası yerine önerilen politika, hedef hizmet seviyesini koruyarak toplam maliyeti ne kadar düşürür?"*

## 3. Başarı Kriterleri ve Koruyucu Kısıt (Guardrail)
1. **Birincil Hedef:** %95 hizmet seviyesinde önerilen politikanın, mevcut Min/Max politikasına göre toplam envanter maliyetini **en az %15** düşürmesi *(kesin eşik Sprint 1 veri kalibrasyonu sonrası kilitlenecektir)*.
2. **Koruyucu Kısıt (Guardrail):** Maliyet tek başına kazananı belirlemez. Her backtest çıktısında **Fill Rate**, **Cycle Service Level** ve **Stoksuzluk Günü** yan yana raporlanır; hedef hizmet seviyesinin altına düşen politika elenir.

## 4. Maliyet Modeli ve Operasyonel Varsayımlar
1. **Elde Tutma Maliyeti:** $\text{Ortalama Eldeki Stok} \times \text{Birim Maliyet} \times \%22\text{ (Yıllık)}$ *(Sermaye %13, depolama/sigorta %5, eskime riski %4)*.
2. **Sipariş Maliyeti:** $\text{Verilen Sipariş Sayısı} \times 1.500\text{ TL}$ *(Satın alma, CoC sertifika kontrolü ve giriş kalite muayenesi)*.
3. **Stoksuzluk Cezası (Backorder Varsayımı):** MRO'da eksik parça kayıp satışa (*Lost Sales*) dönüşmez, bakım emri açık bekler (*Backorder*). $\text{Ceza} = \text{Karşılanamayan Birim} \times \text{Birim Ceza}$.
4. **Kapsam Dışı Maliyet:** Birim satın alma maliyeti ($\text{Birim Fiyat} \times \text{Toplam Talep}$), backorder altında uzun vadede sabit kaldığı için karşılaştırma denklemine dahil edilmemiştir.

### Kritiklik (VED) Bazlı Ceza ve 3 Senaryolu Duyarlılık Matrisi
| Kritiklik | Operasyonel Etki | Düşük (0.5x) | Baz (1.0x) | Yüksek (2.0x) |
| :--- | :--- | :--- | :--- | :--- |
| **V — Vital** | Ekipmanı yerde tutar (AOG) | Fiyat × 0.75 | **Fiyat × 1.50** | Fiyat × 3.00 |
| **E — Essential** | Bakım takvimini geciktirir | Fiyat × 0.375 | **Fiyat × 0.75** | Fiyat × 1.50 |
| **D — Desirable** | Rutin sarf / ikame edilebilir | Fiyat × 0.125 | **Fiyat × 0.25** | Fiyat × 0.50 |

## 5. Kapsam ve Kapsam Dışı
- **Kapsam İçi (MVP):** Parametrik sentetik MRO veri üreteci, SQLite şeması ve ABC/KPI SQL görünümleri, ABC-XYZ ve ADI/CV² segmentasyonu, Naive/MA/Croston/SBA/TSB tahmin modelleri, klasik SS/ROP/EOQ vs. Bootstrap/Monte Carlo karşılaştırması, Min/Max backtest motoru, Streamlit dashboard, birim testler.
- **Kapsam Dışı:** METRIC çok kademeli model, (S-1, S) politikası, bütçe kısıtlı çoklu parça optimizasyonu, derin öğrenme, canlı ERP entegrasyonu.
