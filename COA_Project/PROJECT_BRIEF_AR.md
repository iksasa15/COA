# وثيقة تعريف مشروع C.O.A لصديقك

وثيقة عربية جاهزة للنسخ أو المشاركة: فكرة المشروع، ما تعرضه الواجهات من «صفحات» أو تبويبات، ودور أهم الملفات.

---

## فكرة المشروع

**C.O.A (Council of Agents) — منصة الدفاع السيبراني السيادية للبيئات الحساسة:** ذكاء دفاعي محلي يجمع بيانات النظام (عمليات، شبكة، إلخ)، يحللها بحثاً عن مؤشرات تهديد، ويولّد تقارير (نص، HTML، تقرير حادث) دون إلزام ببنية سحابية مركزية. يدعم **YARA** ووكلاء **CrewAI** بما فيها وكيل **تقرير الحوادث** مع **MITRE ATT&CK**؛ **VirusTotal** تكامل **اختياري** للبيئات المتصلة ويُعطّل في التشغيل السيادي/المعزول.

**الشعار:** ذكاء دفاعي محلي. بلا سحابة. بلا تسريب. — *Sovereign Defense Intelligence. On-Premise. Air-Gapped Ready.*

نص العرض للهاكاثون: [PITCH_HACKATHON_AR.md](PITCH_HACKATHON_AR.md) · التفاصيل المعمارية: [README.md](README.md) · التشغيل: [README-تشغيل.md](README-تشغيل.md).

---

## «الصفحات» — ماذا يرى المستخدم؟

المشروع **ليس موقعاً متعدد المسارات (routes)** بالمعنى التقليدي؛ الواجهات الرئيسية كالتالي:

| الواجهة | العنوان / المسار | ماذا يحتوي؟ |
|--------|-------------------|-------------|
| **واجهة React (موصى بها)** | `http://localhost:5173` (Vite) + API على `http://127.0.0.1:5050` | **SPA** في [web/src/App.tsx](web/src/App.tsx): صفحة رئيسية، **لوحة الأداء** `#/dashboard` (فحص، تبويبات، سياق دفاعي، تبويب **OT/ICS**)، **خريطة MITRE** `#/mitre-heatmap`، **لوحة OT/ICS** `#/ot-dashboard` (بعد فحص يُحمّل `sessionStorage` مفتاح `coa_last_scan_extras`). |
| **واجهة Tkinter** | تشغيل سطح المكتب عبر `python gui.py` | واجهة رسومية قديمة بنفس الفكرة تقريباً: فحص، جداول، تبويبات، تصدير. |
| **سطر الأوامر CLI** | `python main.py` | لا «صفحة»؛ مخرجات في الطرفية وتقارير في مجلد `reports/`. |
| **تقرير HTML ثابت (مثال)** | ملف مثل [reports/COA_Report.html](reports/COA_Report.html) | تقرير تفاعلي يُنشأ بعد الفحص (وليس صفحة تنقل داخل التطبيق). |
| **Helpdesk API** | منفذ **5000** عند `python helpdesk_api.py` | REST للبوتات/التكامل، وليس واجهة مستخدم بصرية. |

**ملفات الويب الداعمة لـ React:** [web/index.html](web/index.html) (نقطة الدخول)، [web/src/main.tsx](web/src/main.tsx) (ربط React بالـ DOM)، [web/vite.config.ts](web/vite.config.ts) (إعداد Vite والـ proxy للـ API إن وُجد).

---

## أهم الملفات ووظيفة كل واحد

### جذر المشروع

- **[main.py](main.py)** — نقطة الدخول الرئيسية: فحص CLI، خيارات (`--dry-run`, `--vt`, `--yara`, `--gui`, `--helpdesk`، إلخ)، تنسيق التحليل والتقارير.
- **[web_api.py](web_api.py)** — خادم **Flask** للواجهة الحديثة: مسارات مثل `/api/health` و`/api/scan` وتنزيل التقارير؛ يستدعي جمع البيانات والتحليل ووكيل التقرير.
- **[react_gui.py](react_gui.py)** — يشغّل نفس تطبيق Flask من `web_api` على المنفذ **5050** مع رسائل توضيحية للمطور.
- **[gui.py](gui.py)** — واجهة **Tkinter** القديمة.
- **[helpdesk_api.py](helpdesk_api.py)** — API مخصص لتكامل **Helpdesk / بوت** (مثلاً `/health`, `/scan`, إلخ حسب README).
- **[requirements.txt](requirements.txt)** — تبعيات Python.
- **[README.md](README.md)** — وثائق المشروع والهيكل.
- **[README-تشغيل.md](README-تشغيل.md)** — خطوات التشغيل السريعة (طرفيتان لـ React + استكشاف أخطاء).

### `config/`

- **[settings.py](config/settings.py)** — إعدادات عامة (مثل مسارات التقارير والمجلدات).

### `agents/`

- **[council.py](agents/council.py)** — منطق «مجلس الوكلاء» الأصلي (CrewAI) للمهام المتخصصة.
- **[incident_reporter.py](agents/incident_reporter.py)** — الوكيل الرابع: تقرير حادث، تصنيف شدة، ملخص تنفيذي، MITRE، إلخ.
- **[defense_context_analyzer.py](agents/defense_context_analyzer.py)** — الوكيل الخامس: سياق دفاعي (APT profiles + playbooks + heatmap بيانات للواجهة).
- **[ics_specialist.py](agents/ics_specialist.py)** — الوكيل السادس: تقييم OT/ICS سلبي (نص تقرير + DO/DON'T تشغيلية).
- **[prompts.py](agents/prompts.py)** — نصوص الـ prompts للوكلاء.

### `core/`

- **[data_collector.py](core/data_collector.py)** — جمع بيانات النظام (عمليات، شبكة، …).
- **[threat_analyzer.py](core/threat_analyzer.py)** — تحليل التهديدات والنتائج المجمّعة.
- **[defense_context_engine.py](core/defense_context_engine.py)** — مطابقة مؤشرات الفحص مع ملفات APT/SOC playbooks (محرك حتمي).
- **[mitre_deep_analysis.py](core/mitre_deep_analysis.py)** — تحليل MITRE «عميق»: ترتيب تكتيكات، D3FEND، فجوات كشف، طبقة Navigator، سياق ICS.
- **[docs/MITRE_ATTACK_DEFENSE_AR.md](docs/MITRE_ATTACK_DEFENSE_AR.md)** — شرح ATT&CK والربط العميق للعرض والمحكّمين.
- **[scripts/download_mitre_stix.py](scripts/download_mitre_stix.py)** — تنزيل `enterprise-attack.json` / `ics-attack.json` إلى `mitre_data/` (اختياري).
- **[solution_engine.py](core/solution_engine.py)** — اقتراح/تحقق من خطوات المعالجة (مع دعم محاكاة).
- **[virustotal.py](core/virustotal.py)** — تكامل VirusTotal.
- **[yara_engine.py](core/yara_engine.py)** — محرك قواعد YARA.
- **[rules/baseline.yar](core/rules/baseline.yar)** — قواعد YARA العامة.
- **[rules/defense_context/](core/rules/defense_context/)** — قواعد YARA إضافية للسياق الدفاعي (مع `baseline` تُحمّل معاً).
- **[apt_profiles/](apt_profiles/)** — ملفات YAML لملفات تعريف APT علنية (للمطابقة التجريبية).
- **[defense_playbooks/](defense_playbooks/)** — سيناريوهات دفاعية مبسطة (YAML).
- **[ics_analyzer/](ics_analyzer/)** — تحليل OT/ICS سلبي (منافذ معروفة + جدول اتصالات؛ مجلد `protocols/` مخصص لاحقاً لـ PCAP/Scapy).
- **[defense_playbooks_ot/](defense_playbooks_ot/)** — سيناريوهات OT تجريبية (Stuxnet-like / TRITON-like drill / إلخ — إرشادية فقط).
- **[docs/OT_ICS_DEFENSE_AR.md](docs/OT_ICS_DEFENSE_AR.md)** — مبدأ Passive-by-default وربط MITRE ICS للعرض.
- **[ics_vulnerabilities/README.md](ics_vulnerabilities/README.md)** — كيفية إثراء CVE من CISA/البائعين دون بيانات وهمية في المستودع.

### `utils/`

- **[admin_check.py](utils/admin_check.py)** — التحقق من صلاحيات المسؤول عند الحاجة.
- **[ui_manager.py](utils/ui_manager.py)** — واجهة طرفية غنية (Rich) لـ CLI.
- **[report_generator.py](utils/report_generator.py)** — تقارير نصية وسجل أحداث الفحص.
- **[html_report.py](utils/html_report.py)** — توليد تقرير HTML.
- **[logger.py](utils/logger.py)** — تسجيل منظم.
- **[cache.py](utils/cache.py)** — تخزين مؤقت للبيانات/النتائج.

### `tests/`

- **[test_core.py](tests/test_core.py)** و **[test_v3_features.py](tests/test_v3_features.py)** و **[test_defense_context.py](tests/test_defense_context.py)** و **[test_ics_analyzer.py](tests/test_ics_analyzer.py)** — اختبارات الوحدات.

### `web/src/` (واجهة React)

- **[App.tsx](web/src/App.tsx)** — التوجيه: رئيسية، `#/dashboard`، `#/mitre-heatmap`، `#/ot-dashboard`.
- **[OtDashboardPage.tsx](web/src/OtDashboardPage.tsx)** — لوحة OT/ICS من جلسة الفحص الأخيرة.
- **[main.tsx](web/src/main.tsx)** — تشغيل التطبيق على عنصر `#root`.
- **[vite-env.d.ts](web/src/vite-env.d.ts)** — أنواع TypeScript لبيئة Vite.

### مجلدات مخرجات

- **`logs/`** — سجلات تُنشأ تلقائياً.
- **`reports/`** — مخرجات الفحص (TXT، HTML، إلخ).

---

## مخطط تدفق مختصر

```mermaid
flowchart LR
  subgraph ui [واجهات]
    React[React SPA]
    Tk[gui Tkinter]
    CLI[main CLI]
  end
  subgraph api [خوادم]
    WebAPI[web_api Flask 5050]
    Helpdesk[helpdesk_api 5000]
  end
  subgraph core [منطق الفحص]
    DC[data_collector]
    TA[threat_analyzer]
    IR[incident_reporter]
  end
  React --> WebAPI
  WebAPI --> DC --> TA --> IR
  CLI --> DC
  Tk --> DC
  Helpdesk --> DC
```
