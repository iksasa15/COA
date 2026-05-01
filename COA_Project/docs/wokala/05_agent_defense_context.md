# الوكيل 5 — Defense Context Analyzer (السياق الدفاعي)

## ما هو؟

طبقة **استراتيجية حتمية** (بدون LLM) تربط نتائج الفحص بملفات **APT إقليمية** (YAML) و **playbooks دفاعية**، وتُنتج:

- إسناداً **فرضياً** مع نسبة ثقة.
- ترتيباً لملفات التعريف الأقرب للمؤشرات.
- **خريطة حرارية** لتقنيات MITRE للواجهة.
- نوايا استراتيجية مبسّطة و«موقفاً دفاعياً» مقترحاً.

## أين المحرك؟

- واجهة الوكيل: [`agents/defense_context_analyzer.py`](../../agents/defense_context_analyzer.py)
- المنطق: [`core/defense_context_engine.py`](../../core/defense_context_engine.py)
- ملفات YAML: [`apt_profiles/`](../../apt_profiles/)، [`defense_playbooks/`](../../defense_playbooks/)
- قواعد YARA إضافية: [`core/rules/defense_context/`](../../core/rules/defense_context/)

## الواجهة (React)

- صفحة [`#/defense-context`](../../web/src/DefenseContextPage.tsx)
- جزء في لوحة الفحص بعد الفحص
- خريطة MITRE تستهلك `mitre_heatmap` من نفس الحزمة

## إخلاء مسؤولية

- النصوص تصرّح أن الارتباط **تجريبي/استدلالي** وليس استخباراتاً مصنّفاً — مناسب للهاكاثون والتدريب.

## القيود

- جودة الإسناد تعتمد على تغطية ملفات YAML وعلى إشارات `ThreatAnalyzer`؛ ليست بديلاً عن Threat Intelligence الاحترافي.
