# Risk Kaydı (Risk Register)

| ID | Risk Tanımı | Kategori | Olasılık | Etki | Azaltma Planı (Mitigation) | Durum |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **R-01** | **Ceza maliyeti varsayımsal:** Yüksek ceza politikayı yapay avantajlı gösterebilir. | Metodoloji | Yüksek | Yüksek | VED bazlı ceza ve 3 senaryolu (0.5x/1.0x/2.0x) duyarlılık analizi raporlandı. | Azaltıldı |
| **R-02** | **Gerçek MRO verisi erişim kısıtı:** Gizlilik nedeniyle açık veri bulunamaması. | Veri | Yüksek | Orta | Sabit seed'li (`42`) sentetik veri üreteci geliştirildi (`DEC-02`, `CHG-02`). | Gerçekleşti |
| **R-03** | **Model karmaşıklığı riski:** Croston/TSB'nin aşırı seyrek parçalarda MA'yı yenememesi. | Teknik | Orta | Orta | %2 basitlik toleransı ile segment bazlı kazanan seçildi. | Azaltıldı |
| **R-04** | **Benimseme riski:** Planlamacıların simülasyona güvenmeyip Excel Min/Max'a dönmesi. | UX / Süreç | Orta | Yüksek | Mevcut Min/Max ile önerilen `(s, Q)` TL ve açık sipariş günü farkı yan yana sunuldu. | İzleniyor |
| **R-05** | **Dar eğitim penceresi:** Aşırı seyrek parçalarda gözlem sayısının az olması. | Teknik | Orta | Orta | 730 günlük kalibrasyon sabitlendi; sıfır tahminde `Q>=1` taban kuralı eklendi. | Azaltıldı |
| **R-06** | **Sentetik veri totolojisi:** Sabit dağılıma uyan modelin yapay kazanması. | Metodoloji | Orta | Yüksek | `regime_shift` ve `obsolescence` desenleri eklendi (`CHG-02`). | Azaltıldı |
| **R-07** | **Saman adam baseline riski:** Mevcut Min/Max'ın zayıf kurgulanması. | Metodoloji | Orta | Yüksek | Min/Max duyarlılık gridi (`1/2`, `1.5/3`, `2/4`, `3/6 ay`) ve klasik `(s, Q)` eklendi (`DEC-06`, `DEC-10`). | Azaltıldı |
| **R-08** | **Doğrulama gürültüsü:** 0-2 talep olayı gören parçalarda seçim oynaklığı. | Teknik | Orta | Orta | Rolling-origin doğrulama ve segment bazlı kazanan üretildi. | Gerçekleşti |
| **R-09** | **TSB eskime avantajı:** Eskime parçasında TSB'nin yapay öne çıkması. | Metodoloji | Yüksek | Düşük | 16 eskime parçasının hiçbirinde TSB kazanmadı; şeffaf raporlandı. | Kapatıldı |
| **R-10** | **CSL vs. Fill Rate karışıklığı:** Hizmet seviyesi tanımlarının karışması. | Metodoloji | Orta | Orta | Guardrail gereği `%96.0` Fill Rate veren `CSL %98` seçildi. | Azaltıldı |
| **R-11** | **Tasarruf yoğunlaşması:** Portföy tasarrufunun birkaç Vital-Lumpy parçaya yaslanması. | Metodoloji | Yüksek | Orta | İlk 5 (%11.2) ve ilk 10 (%3.2) parça hariç sonuçlar raporlandı. | Gerçekleşti |
| **R-12** | **Ceza tanımı duyarlılığı:** Günlük `/30` yerine `/7` veya kayıp satış ceza seçimi. | Metodoloji | Orta | Yüksek | Üç ceza tanımı karşılaştırıldı (`DEC-11`); `CSL %98` hepsinde kazandı. | Azaltıldı |
