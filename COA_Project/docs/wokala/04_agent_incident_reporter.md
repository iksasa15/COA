# الوكيل 4 — Incident Reporter (تقرير الحوادث)

## ما هو؟

وكيل **منطقي/تقريري** يبني **تصنيف الحادث**، **ملخصاً تنفيذياً**، و**تقرير حادث نصي** مع ربط **MITRE ATT&CK** حيث ينطبق — بدون الاعتماد على سحابة.

## ماذا يفعل؟

- يصنّف الشدة والفئة والأولوية من نتائج التحليل.
- يولّد ملخصاً للإدارة وللمحلل.
- يُلحق لاحقاً أقسام **Defense Context** و **MITRE Deep** عند توليد التقرير الكامل (انظر [`agents/incident_reporter.py`](../../agents/incident_reporter.py)).

## أين الكود؟

- [`agents/incident_reporter.py`](../../agents/incident_reporter.py)

## الواجهة

- أزرار **Incident report** / تصدير TXT و HTML من [`web/src/ScanPage.tsx`](../../web/src/ScanPage.tsx) بعد فحص ناجح.
- الخادم: [`web_api.py`](../../web_api.py) مسارات `/api/reports/*`.

## القيود

- التقرير يعكس **آخر فحص** مخزّن في خادم الويب؛ ليس أرشيفاً زمنياً افتراضياً.
