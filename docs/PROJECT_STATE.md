# PROJECT_STATE.md — Proje Canlı Durum Özeti

- **Son Güncelleme:** 2026-11-14
- **Aktif Faz:** Sprint 0 — Yönetişim, Kapsam Kilitleme ve Altyapı Kurulumu

## 1. Tamamlanan İşler
- GitHub deposu (`spare-parts-decision-support`), klasör iskeleti ve `.venv` sanal ortamı kuruldu.
- Tüzük, Veri Hazırlık, WBS, RACI, Risk Kaydı, Karar Günlüğü ve Değişiklik Kaydı (`/docs/pm`) tamamlandı.
- Smoke test ve GitHub Actions CI iş akışı yapılandırıldı.

## 2. Sıradaki İşler (Sprint 1)
- `data/generator.py` ile 200 kalemlik MRO parça ve 36 aylık talep/lead-time sentetik veri üretimi.
- `sql/schema.sql` ve ABC/KPI SQL görünümleri.
- ABC-XYZ ve Syntetos-Boylan (ADI/CV²) sınıflandırma modülü + birim testler.

## 3. Açık Riskler ve Kararlar
- **Açık Riskler:** R-01 (Ceza maliyeti duyarlılığı), R-03 (Baseline kıyaslaması), R-04 (Kullanıcı benimsemesi).
- **Kararlar:** DEC-01 (TR doküman/EN kod), DEC-02 (3 kalemli maliyet + VED duyarlılık), DEC-03 (SQLite), DEC-04 (`seed=42`).
