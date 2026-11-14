# Veri Hazırlık Değerlendirmesi (Data Readiness Assessment)

## 1. İhtiyaç Duyulan Tablolar
1. `parts`: `part_id`, parça adı, birim maliyet (TL), VED kritiklik sınıfı, tedarikçi.
2. `current_policy`: Mevcut sabit `min_stock`, `max_stock` ve başlangıç stoğu.
3. `demand_history`: 36 aylık (1095 günlük) tüketim kayıtları (sıfır talep dönemleri dahil).
4. `lead_time_history`: Sipariş ve teslim tarihleri ile tedarik süresi (`lead_time_days`) dağılımı.

## 2. Boşluk Analizi ve Sentetik Veri Kararı
Savunma/havacılık MRO verileri gizlilik nedeniyle kamuya açık değildir (**R-02**). Bu nedenle Syntetos & Boylan (2005) literatüründeki 4 talep sınıfını (Smooth, Erratic, Intermittent, Lumpy) dengeli temsil eden, 200 parçalık ve sabit tohumlu (`RANDOM_SEED = 42`) parametrik veri üreteci (`data/generator.py`) geliştirilecektir. İlk 24 ay kalibrasyon, son 12 ay politika backtest penceresi olarak ayrılacaktır.
