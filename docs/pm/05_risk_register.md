# Risk Kayd? (Risk Register)

| ID | Risk Tan?m? | Kategori | Olas?l?k | Etki | Azaltma Plan? | Durum |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **R-01** | Ceza maliyeti varsay?msal | Metodoloji | Y?ksek | Y?ksek | VED bazl? ceza ve 3 senaryolu duyarl?l?k raporland?. | Azalt?ld? |
| **R-02** | Ger?ek MRO verisi k?s?t? | Veri | Y?ksek | Orta | Sabit seed (`42`) sentetik veri ?reteci kuruldu (`DEC-02`). | Ger?ekle?ti |
| **R-03** | Model karma??kl??? riski | Teknik | Orta | Orta | %2 basitlik tolerans? ile segment bazl? kazanan se?ildi. | Azalt?ld? |
| **R-04** | Kullan?c? benimseme riski | UX | Orta | Y?ksek | Mevcut Min/Max ile `(s, Q)` fark? yan yana sunuldu. | ?zleniyor |
| **R-05** | Dar e?itim penceresi | Teknik | Orta | Orta | 730 g?n sabitlendi; s?f?r tahminde `Q>=1` taban? eklendi. | Azalt?ld? |
| **R-06** | Sentetik veri totolojisi | Metodoloji | Orta | Y?ksek | `regime_shift` ve `obsolescence` desenleri eklendi (`CHG-02`). | Azalt?ld? |
| **R-07** | Saman adam baseline riski | Metodoloji | Orta | Y?ksek | Min/Max gridi (`1/2..3/6 ay`) ve klasik `(s, Q)` eklendi. | Azalt?ld? |
| **R-08** | Do?rulama g?r?lt?s? | Teknik | Orta | Orta | Rolling-origin do?rulama ve segment kazanan? eklendi. | Ger?ekle?ti |
| **R-09** | TSB eskime avantaj? | Metodoloji | Y?ksek | D???k | 16 eskime par?as?n?n hi?birinde TSB kazanmad?. | Kapat?ld? |
| **R-10** | CSL vs Fill Rate kar???kl??? | Metodoloji | Orta | Orta | Guardrail gere?i `%96.0` Fill Rate veren `CSL %98` se?ildi. | Azalt?ld? |
| **R-11** | Tasarruf yo?unla?mas? | Metodoloji | Y?ksek | Orta | ?lk 5 (%14.2) ve ilk 10 (%5.7) hari? sonu?lar raporland?. | Ger?ekle?ti |
| **R-12** | Ceza tan?m? duyarl?l??? | Metodoloji | Orta | Y?ksek | `/30`, `/7` ve tek seferlik cezalar kar??la?t?r?ld? (`DEC-11`). | Azalt?ld? |
