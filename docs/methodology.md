# Metodoloji Dok?man?

1. **Veri Ayr?m? (`DEC-05`):** 730 g?n kalibrasyon (`is_backtest=0`), 365 g?n kapal? test (`is_backtest=1`).
2. **Segmentasyon:** ABC-XYZ, VED ve Syntetos-Boylan (`Smooth: 84`, `Intermittent: 87`, `Lumpy: 27`, `Erratic: 2` ? *Erratic n=2 ihtiyatla yorumlan?r*).
3. **Tahmin (`DEC-07`):** 18 ay e?itim / 6 ay rolling-origin do?rulama, `RMSSE` + %2 basitlik tolerans? (16 eskime par?as?n?n hi?birinde TSB kazanmad?).
4. **Blok Bootstrap (`DEC-09`):** 730 g?nl?k seriden $L^*$ ard???k g?nl?k bloklarla 10.000 senaryo.
5. **CRN Backtest (`DEC-02`, `DEC-10`):** Ger?ek Backorder (birincil) ve Lost Sales (duyarl?l?k), VED ceza ?arpanlar?, yo?unla?ma ve 20-tohum analizi.
