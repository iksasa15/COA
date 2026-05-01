# وثائق الوكلاء — C.O.A (Council of Agents)

مجلد يشرح **كل وكيل (أو طبقة معالجة)** في المشروع: ماذا يفعل، أين الكود، وكيف يظهر في الواجهة إن وُجد.

| # | الملف | الاسم |
|---|--------|--------|
| — | [00_threat_engine.md](00_threat_engine.md) | محرك التحليل الحتمي (ليس CrewAI) |
| 1 | [01_agent_eye.md](01_agent_eye.md) | الوكيل 1 — The Eye (جمع بيانات LLM) |
| 2 | [02_agent_brain.md](02_agent_brain.md) | الوكيل 2 — The Brain (صيد تهديدات LLM) |
| 3 | [03_agent_strategist.md](03_agent_strategist.md) | الوكيل 3 — The Strategist (حلول LLM) |
| 4 | [04_agent_incident_reporter.md](04_agent_incident_reporter.md) | الوكيل 4 — تقرير الحوادث |
| 5 | [05_agent_defense_context.md](05_agent_defense_context.md) | الوكيل 5 — السياق الدفاعي |
| 6 | [06_agent_ics_specialist.md](06_agent_ics_specialist.md) | الوكيل 6 — أخصائي OT/ICS |

**ملاحظة:** الوكلاء 1–3 يعملون عبر **CrewAI + Ollama** عند تفعيل مسار المجلس في `main.py`؛ مسار **الويب/الفحص السريع** يعتمد غالباً على `ThreatAnalyzer` + الوكلاء 4–6 بدون LLM للوكلاء 1–3.
