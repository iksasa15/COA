# 🛡️ C.O.A — Council of Agents v3.0

> نظام فحص أمني احترافي متكامل يعمل محلياً — مع VirusTotal، YARA، GUI، وHelpdesk Bot API

## ✨ ما الجديد في v3.0

| الميزة | الوصف |
|--------|-------|
| 🔍 **VirusTotal Integration** | فحص الملفات والـ IPs ضد قاعدة بيانات عالمية (70+ antivirus) |
| 🎯 **YARA Rules Engine** | 7 قواعد جاهزة للكشف عن malware, ransomware, cryptominers, RATs |
| 📊 **Incident Reporter (Agent 4)** | تقارير احترافية مع MITRE ATT&CK mapping |
| 🖥️ **Desktop GUI** | واجهة رسومية dark-themed بـ Tkinter |
| 🤖 **Helpdesk Bot API** | REST API + Python SDK للدمج مع bots |

## 🏛️ المعمارية الكاملة

```
┌──────────────────────────────────────────────────┐
│  Council of Agents (4 Specialized AI)            │
├──────────────────────────────────────────────────┤
│  1. Data Collector  (The Eye)                    │
│  2. Threat Hunter   (The Brain)                  │
│  3. Solution Advisor(The Strategist)             │
│  4. Incident Reporter(The Storyteller) 🆕       │
└──────────────────────────────────────────────────┘
           ↓             ↓             ↓
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │   CLI    │  │   GUI    │  │ REST API │
    │  main.py │  │  gui.py  │  │helpdesk_ │
    │          │  │          │  │   api.py │
    └──────────┘  └──────────┘  └──────────┘
```

## 📂 الهيكل الكامل

```
COA_Project/
├── main.py                      # CLI entry point
├── gui.py                       # 🆕 Desktop GUI (Tkinter)
├── helpdesk_api.py              # 🆕 Helpdesk Bot integration
├── requirements.txt
├── README.md
│
├── config/
│   └── settings.py
│
├── agents/
│   ├── council.py               # Original 3 agents (CrewAI)
│   └── incident_reporter.py     # 🆕 Agent #4
│
├── core/
│   ├── data_collector.py        # Async + parallel
│   ├── threat_analyzer.py       # ML-style scoring
│   ├── solution_engine.py       # Dry-run + validator
│   ├── virustotal.py            # 🆕 VT integration
│   ├── yara_engine.py           # 🆕 YARA scanning
│   └── rules/
│       └── baseline.yar         # 🆕 7 detection rules
│
├── utils/
│   ├── admin_check.py
│   ├── ui_manager.py            # Rich CLI
│   ├── cache.py                 # SmartCache
│   ├── logger.py                # Structured logs
│   ├── report_generator.py      # TXT reports
│   └── html_report.py           # Interactive HTML
│
├── tests/
│   ├── test_core.py             # 34 tests
│   └── test_v3_features.py      # 🆕 19 tests (53 total)
│
├── logs/                        # Auto-generated
└── reports/                     # Scan outputs
```

## 🚀 التثبيت السريع

```bash
# 1. فك الضغط
unzip COA_Project_v3.zip && cd COA_Project

# 2. بيئة افتراضية
python -m venv venv
venv\Scripts\activate   # Windows

# 3. المتطلبات
pip install -r requirements.txt

# 4. Ollama (للـ LLM المحلي)
ollama pull llama3.1 && ollama serve

# 5. (اختياري) VirusTotal API key
# Get free key from: https://www.virustotal.com/gui/join-us
set VT_API_KEY=your_api_key_here
```

## 🎮 طرق الاستخدام الثلاث

### 1. 💻 Command Line (CLI)
```bash
python main.py                    # فحص عادي
python main.py --dry-run          # محاكاة آمنة
python main.py --html --json      # تقارير متعددة
python main.py --quick            # فحص سريع
```

### 2. 🖥️ Desktop GUI
```bash
python gui.py
```
واجهة رسومية كاملة بـ dark theme:
- Start Scan button
- إحصائيات مباشرة
- جدول تهديدات ملوّن
- تبويبات (Threats, Processes, Network, Logs)
- أزرار Export (TXT, HTML, Incident Report)

### 3. 🤖 Helpdesk Bot API
```bash
# تشغيل API server
python helpdesk_api.py

# أو استيراد كـ SDK
from helpdesk_api import COAHelpdesk

bot = COAHelpdesk()
result = bot.scan_system(user_id="employee_123")
print(result["bot_response"])
# "✅ Good news! Your system is clean..."
```

#### REST API Endpoints:
```
GET  /health                   # Health check
POST /scan                     # Start scan
GET  /remediation/<scan_id>    # Get fix plan
POST /execute                  # Execute step
```

## 🔍 VirusTotal Integration

```python
from core.virustotal import vt_client

# فحص ملف
result = vt_client.check_file("C:\\suspicious.exe")
if result['is_malicious']:
    print(f"⚠️ Detected by {result['detection_ratio']} engines")
    print(f"Threats: {result['threat_names']}")

# فحص IP
result = vt_client.check_ip("1.2.3.4")
if result['is_malicious']:
    print(f"⚠️ Malicious IP - {result['country']}")
```

## 🎯 YARA Rules

قواعد جاهزة للكشف عن:
- ✅ **Cryptominers** — xmrig, stratum protocols
- ✅ **Obfuscated PowerShell** — base64, encoded commands
- ✅ **Ransomware** — encryption patterns, ransom notes
- ✅ **Remote Access Trojans** — meterpreter, cobalt strike
- ✅ **Persistence Mechanisms** — registry Run keys, tasks
- ✅ **Anti-Analysis** — VM detection, debugger checks
- ✅ **Known Malware** — WannaCry, Emotet, TrickBot, etc.

```python
from core.yara_engine import yara_engine

result = yara_engine.scan_file("C:\\suspicious.exe")
if result['is_malicious']:
    print(f"⚠️ {result['matched_count']} rule(s) matched!")
    for match in result['matches']:
        print(f"- {match['rule']}: {match['description']}")
```

## 📊 Incident Reporter Agent (الجديد!)

الوكيل الرابع يقوم بـ:
- ✅ **تصنيف الحادث** (CRITICAL/HIGH/MEDIUM + Priority P1-P5)
- ✅ **Executive Summary** - ملخص لأصحاب القرار
- ✅ **Technical Findings** - تفاصيل للفنيين
- ✅ **MITRE ATT&CK mapping** - ربط بإطار معياري
- ✅ **Recommendations** - توصيات مخصصة
- ✅ **Timeline** - سلسلة الأحداث

## 🤖 Helpdesk Bot Integration Flow

```
User: "My PC is acting weird"
   ↓
Helpdesk Bot → COAHelpdesk.scan_system()
   ↓
COA performs full scan (~1s)
   ↓
Returns JSON with:
  - severity, category, priority
  - threat_count
  - bot_response (user-friendly text)
  - needs_action (boolean)
   ↓
Bot displays to user:
"🚨 I found 2 critical issues. Please disconnect 
 from the internet and contact IT immediately..."
```

## 🧪 الاختبارات

```bash
# جميع الاختبارات (53 test)
pytest tests/ -v

# with coverage
pytest --cov=. --cov-report=html tests/
```

## 📈 الأداء

| العملية | الزمن |
|---------|-------|
| Data collection (parallel) | ~0.5s |
| Cached second call | ~0.01s |
| Threat analysis | ~0.1s |
| Bot API response | ~0.6s total |
| Full scan with all features | ~1-2s |

## 🔐 الأمان

- ✅ جميع البيانات تبقى محلياً
- ✅ LLM محلي (Ollama) - لا يرسل بيانات للـ cloud
- ✅ VirusTotal يرسل hashes فقط (ليس الملفات)
- ✅ Command Validator يحجب الأوامر الخطيرة
- ✅ Human-in-the-Loop إجباري لكل الأوامر
- ✅ Dry-run mode للتجربة الآمنة

## 📊 مثال لتدفق الـ Bot

```python
# 1. المستخدم يطلب فحص
bot = COAHelpdesk(dry_run_default=True)
scan = bot.scan_system(user_id="john")

# 2. الحصول على خطة
plan = bot.get_remediation_plan(scan["scan_id"])

# 3. تنفيذ مع موافقة
for step in plan["steps"]:
    # عرض الخطوة للمستخدم
    print(f"Step: {step['action']}")
    user_approved = input("Approve? (y/n): ") == 'y'
    
    # تنفيذ
    result = bot.execute_step(
        scan_id=scan["scan_id"],
        step_number=step["step"],
        user_approved=user_approved,
    )
```

## 🔮 خارطة الطريق v4.0

- [ ] Real-time monitoring daemon
- [ ] Windows Event Log integration
- [ ] Registry tampering detection
- [ ] Network traffic capture
- [ ] Multi-agent collaboration via LLM
- [ ] Mobile app for remote scanning
- [ ] Docker containerization

## 📜 الترخيص

MIT License

---

**C.O.A v3.0 — من نظام فحص بسيط إلى منصة أمنية متكاملة 🚀**

كل البيانات محلية • 4 وكلاء AI • 3 واجهات • 53 اختبار • MITRE ATT&CK 🔒
# COA
