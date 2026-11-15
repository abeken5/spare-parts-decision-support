# Risk Kayd? (Risk Register)

| ID | Risk Tan?m? | Kategori | Olas?l?k | Etki | Azaltma Plan? (Mitigation) | Durum |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **R-01** | **Ceza maliyeti varsay?msal:** Y?ksek ceza politikay? yapay avantajl? g?sterebilir. | Metodoloji | Y?ksek | Y?ksek | VED bazl? ceza tablosu ve 3 senaryolu duyarl?l?k analizi raporland?. | Azalt?ld? |
| **R-02** | **Ger?ek MRO verisi eri?im k?s?t?:** Gizlilik nedeniyle a??k veri bulunamamas?. | Veri | Y?ksek | Orta | Sabit seed'li (`42`) sentetik veri ?reteci geli?tirildi (`DEC-02`, `CHG-02`). | Ger?ekle?ti |
| **R-03** | **Model karma??kl??? riski:** Croston/TSB'nin a??r? seyrek par?alarda MA'y? yenememesi. | Teknik | Orta | Orta | %2 basitlik tolerans? ile segment bazl? kazanan se?ildi. | Azalt?ld? |
| **R-04** | **Benimseme riski:** Planlamac?lar?n Excel Min/Max'a d?nmesi. | UX / S?re? | Orta | Y?ksek | Mevcut Min/Max ile ?nerilen `(s, Q)` TL ve stoksuzluk fark? yan yana sunuldu. | ?zleniyor |
| **R-05** | **Dar e?itim penceresi:** A??r? seyrek par?alarda g?zlem say?s?n?n az olmas?. | Teknik | Orta | Orta | 730 g?nl?k kalibrasyon sabitlendi; s?f?r tahminde `Q>=1` taban? eklendi. | Azalt?ld? |
| **R-06** | **Sentetik veri totolojisi:** Sabit da??l?ma uyan modelin yapay kazanmas?. | Metodoloji | Orta | Y?ksek | `regime_shift` ve `obsolescence` desenleri eklendi (`CHG-02`). | Azalt?ld? |
| **R-07** | **Saman adam baseline riski:** Mevcut Min/Max'?n zay?f kurgulanmas?. | Metodoloji | Orta | Y?ksek | Min/Max duyarl?l?k gridi (`1/2`, `1.5/3`, `2/4`, `3/6 ay`) ve klasik `(s, Q)` eklendi. | Azalt?ld? |
| **R-08** | **Do?rulama g?r?lt?s?:** 0-2 talep olay? g?ren par?alarda se?im oynakl???. | Teknik | Orta | Orta | Rolling-origin do?rulama ve segment bazl? kazanan ?retildi. | Ger?ekle?ti |
| **R-09** | **TSB eskime avantaj?:** Eskime par?as?nda TSB'nin yapay ?ne ??kmas?. | Metodoloji | Y?ksek | D???k | 16 eskime par?as?n?n hi?birinde TSB kazanmad?; ?effaf raporland?. | Kapat?ld? |
| **R-10** | **CSL vs. Fill Rate kar???kl???:** Hizmet seviyesi tan?mlar?n?n kar??mas?. | Metodoloji | Orta | Orta | Aray?zde CSL hedefi ve ger?ekle?en Fill Rate ayr? g?sterildi. | Azalt?ld? |
