# الوكيل 1 — The Eye (System Data Collector)

## الدور في المجلس

**جامع البيانات:** يراجع بيانات خام من النظام (JSON/ملخص) ويعيد تنظيمها ووصفها **دون** أن يصنّفها كتهديد بنفسه — التركيز على الدقة والهيكلة.

## التقنية

- جزء من **CrewAI** في [`agents/council.py`](../../agents/council.py) (`_create_data_collector`).
- النموذج: **Ollama** محلي (مثلاً `llama3.1`) حسب [`config/settings.py`](../../config/settings.py).

## ماذا يفعل عملياً؟

1. يستلم وصفاً لبيانات النظام (من مهمة `create_collection_task`).
2. يُخرج ملخصاً منظماً يساعد الوكيل 2 على الشرح والتحليل بلغة طبيعية.

## متى يُستخدم؟

- عند تشغيل **CouncilOfAgents** من `main.py` (أو المسارات التي تستدعي المجلس) **و** Ollama متوفر.
- **ليس** هو الذي يجمع `psutil` من الجهاز — الجمع الفعلي في [`core/data_collector.py`](../../core/data_collector.py).

## القيود

- بدون Ollama / CrewAI لن يعمل هذا المسار؛ الفحص القياسي يبقى يعمل عبر `data_collector` + `ThreatAnalyzer`.
