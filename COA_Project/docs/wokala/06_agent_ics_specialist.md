# الوكيل 6 — ICS Specialist (أخصائي OT/ICS)

## ما هو؟

وكيل **حتمي** (بدون LLM) يقيّم مخرجات **التحليل السلبي لـ OT/ICS** (`ics_analyzer`) ويُنتج:

- تقرير ASCII بعنوان **ICS THREAT ASSESSMENT**
- تصنيفات أثرية تجريبية: Cyber / Operational / Safety
- قوائم **DO / DON'T** تراعي استمرارية الإنتاج (نبرة OT)

## ما الذي يُغذّيه؟

- [`ics_analyzer/analyzer.py`](../../ics_analyzer/analyzer.py) — يربط جدول الاتصالات بمنافذ ICS معروفة (502، 102، 4840، …) **دون** إرسال حزم فحص نشطة.
- سيناريوهات YAML: [`defense_playbooks_ot/`](../../defense_playbooks_ot/)

## أين الكود؟

- [`agents/ics_specialist.py`](../../agents/ics_specialist.py)

## الواجهة

- تبويب **OT/ICS** في لوحة الفحص
- صفحة [`#/ot-dashboard`](../../web/src/OtDashboardPage.tsx)
- خيار **عرض توضيحي (محاكاة OT)**: [`fixtures/demo_ot_ics.json`](../../fixtures/demo_ot_ics.json) + `GET /api/demo/ot-ics-fixture`

## القيود

- لا يحلّل إطارات بروتوكول (Modbus/S7) — ذلك يتطلب PCAP + Scapy لاحقاً.
- على حاسوب تطوير عادي غالباً **صفر hits** — طبيعي؛ استخدم العرض التوضيحي للهاكاثون أو بيئة OT حقيقية/محاكاة (Conpot، إلخ).

## المرجع النظري

- [`docs/OT_ICS_DEFENSE_AR.md`](../OT_ICS_DEFENSE_AR.md)
