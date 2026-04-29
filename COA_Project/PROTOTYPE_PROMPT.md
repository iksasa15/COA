# 🎯 C.O.A — Council of Agents
## Master Prototype Prompt — البرومبت الشامل للبروتوتايب

> هذا الملف يحتوي على البرومبت الشامل الذي يصف المشروع كاملاً.
> استخدمه عند:
> - عرض المشروع لمستثمرين/مدراء
> - شرح الفكرة لفريق العمل
> - إعطائه لـ AI آخر لتطوير ميزات جديدة
> - توثيق المشروع للمستقبل

---

## 📋 البرومبت الكامل (نسخة كاملة)

```
# C.O.A (Council of Agents) — AI-Powered Local Security Scanner

## 🎯 PROJECT VISION
Build a 100% local, privacy-first security scanning system that uses 
multiple specialized AI agents working as a council to detect, analyze, 
and remediate security threats on user's machines — without sending 
any data to external servers.

## 🏛️ ARCHITECTURE OVERVIEW

The system consists of FOUR specialized AI agents orchestrated by CrewAI 
framework, all powered by a local LLM (Ollama running llama3.1):

### Agent 1: Data Collector ("The Eye")
- **Role**: Senior System Forensics Specialist
- **Mission**: Collect raw system telemetry (network connections, 
  running processes, system metrics)
- **Output**: Clean, structured JSON
- **Personality**: Meticulous, never interprets, only observes

### Agent 2: Threat Hunter ("The Brain")
- **Role**: Elite Cyber Threat Hunter
- **Mission**: Analyze patterns, identify suspicious behavior, 
  classify threats by severity
- **Output**: Threat list with confidence scores and MITRE ATT&CK mapping
- **Personality**: Skeptical, precise, hates false positives

### Agent 3: Solution Advisor ("The Strategist")
- **Role**: Senior Incident Response Architect
- **Mission**: Design surgical remediation plans for confirmed threats
- **Output**: Reversible commands with risk assessment
- **Personality**: Cautious, prefers reversible actions, "First, do no harm"

### Agent 4: Incident Reporter ("The Storyteller")
- **Role**: Cybersecurity Documentation Specialist
- **Mission**: Transform findings into professional reports
- **Output**: Multi-audience reports (executive + technical)
- **Personality**: Clear communicator, maps to MITRE/NIST frameworks

## 🔄 WORKFLOW

```
1. User runs: python main.py (or launches GUI)
   ↓
2. Admin privileges check + welcome banner
   ↓
3. Agent 1 collects: 
   - Network connections (psutil.net_connections)
   - Running processes (psutil.process_iter)
   - System metrics
   ↓
4. Agent 2 analyzes using:
   - Rule-based scoring (suspicious ports, temp folders)
   - ML-style signal correlation
   - VirusTotal API (optional)
   - YARA rules engine (optional)
   ↓
5. Agent 3 generates remediation:
   - taskkill commands for malicious processes
   - netsh firewall rules (reversible)
   - Investigation commands for uncertain cases
   ↓
6. 🔒 HUMAN-IN-THE-LOOP GATE
   System asks: "Approve this command? (Y/N)"
   No execution without explicit user approval
   ↓
7. Agent 4 generates final report:
   - TXT (human-readable)
   - HTML (interactive dashboard)
   - JSON (for API integration)
   - Incident Report (with MITRE ATT&CK mapping)
```

## 🛡️ CORE PRINCIPLES

1. **Privacy First**: All data stays on the user's machine
2. **Human Authority**: AI suggests, humans decide
3. **Reversibility**: Prefer firewall rules over file deletion
4. **Transparency**: Every action is logged and explained
5. **No False Promises**: Agents say "I don't know" when uncertain

## 💻 TECH STACK

- **Language**: Python 3.10+
- **AI Framework**: CrewAI (agent orchestration)
- **Local LLM**: Ollama with llama3.1 (or llama3.2 for weaker machines)
- **System Monitoring**: psutil
- **CLI UI**: Rich library (colors, tables, progress bars)
- **GUI**: Tkinter (built-in, no extra install)
- **API**: Flask (REST endpoints for Helpdesk Bot integration)
- **Detection**: YARA rules + VirusTotal API
- **Logging**: Structured JSON logs with rotation

## 🎮 INTERFACES (THREE WAYS TO USE)

### 1. CLI (Command Line)
```bash
python main.py                    # Normal scan
python main.py --dry-run          # Safe simulation
python main.py --html --json      # Multiple report formats
python main.py --quick            # Skip AI, rules only
```

### 2. GUI (Desktop App)
```bash
python gui.py
```
Dark-themed Tkinter interface with:
- Real-time stats cards
- Color-coded threat table
- Process/network tabs
- Export buttons

### 3. REST API (For Bot Integration)
```bash
python helpdesk_api.py
# Server runs on http://localhost:5000
```
Endpoints:
- POST /scan — Start security scan
- GET /remediation/<scan_id> — Get fix plan  
- POST /execute — Execute approved step
- GET /health — Health check

## 🔍 DETECTION CAPABILITIES

The system detects:

### Network Threats
- Connections to known malicious ports (4444, 1337, 31337, etc.)
- C2 (Command & Control) communication patterns
- Data exfiltration to external IPs
- Reverse shell connections

### Process Threats
- Processes from %TEMP% folders
- Cryptominer signatures (high CPU, low RAM)
- Process masquerading (svch0st.exe vs svchost.exe)
- Unsigned executables
- Living-off-the-land techniques

### File-based Threats (with YARA)
- Ransomware (encryption patterns)
- Remote Access Trojans (RATs)
- Obfuscated PowerShell
- Anti-analysis/sandbox evasion
- Known malware families (WannaCry, Emotet, etc.)

### IP/Domain Reputation (with VirusTotal)
- Cross-reference against 70+ antivirus engines
- Geographic and ASN context
- Confidence scoring

## 📊 SCORING SYSTEM

Each threat gets a score (0-100) based on weighted signals:

| Signal | Weight |
|--------|--------|
| Connection to suspicious port | 40 |
| Process running from temp | 30 |
| Masquerading process name | 30 |
| External connection from temp | 35 |
| High CPU + Low RAM | 15 |
| No digital signature | 20 |

Severity Mapping:
- 80+ → CRITICAL (immediate kill)
- 60-79 → HIGH (investigate + kill)
- 40-59 → MEDIUM (investigate)
- 20-39 → LOW (monitor)

Confidence Levels:
- HIGH: 3+ signals correlated
- MEDIUM: 2 signals
- LOW: 1 signal

## 🔒 SAFETY MECHANISMS

### 1. Command Validator (Blacklist)
Always blocked, even with user approval:
- format c:
- del /f /s /q C:\\
- shutdown /s /t 0
- diskpart clean
- Fork bombs

### 2. Dry-Run Mode
```bash
python main.py --dry-run
```
- Simulates all commands
- No actual execution
- Shows what WOULD happen
- Perfect for testing

### 3. Rollback Support
Firewall rules track their own undo commands:
- Block: `netsh advfirewall firewall add rule ...`
- Rollback: `netsh advfirewall firewall delete rule ...`

### 4. Audit Trail
Every action logged in:
- coa.log (human-readable)
- coa.json.log (structured JSON for SIEM)
- COA_Audit_Report.txt (per-scan record)

## 🎨 UI/UX DESIGN

### CLI (Rich library)
- Cyan banners with pyfiglet ASCII art
- Color-coded severity (Red/Orange/Yellow/Green)
- Progress spinners during long operations
- Tables with rounded corners
- Confirmation prompts in highlighted boxes

### GUI (Tkinter dark theme)
- Background: #0f172a (Slate 900)
- Accents: #38bdf8 (Cyan 400)
- Cards with subtle borders
- Treeview tables with severity colors
- Threading to prevent UI freezing

### HTML Reports
- Dark mode with glassmorphism
- Stats grid layout
- Severity pills (rounded badges)
- Collapsible threat details
- Mobile-responsive

## 🤖 HELPDESK BOT INTEGRATION

Designed to plug into existing IT Helpdesk Bots:

```python
from helpdesk_api import COAHelpdesk

bot = COAHelpdesk(dry_run_default=True)

# When user reports issue
result = bot.scan_system(user_id="employee_123")

# Bot responds in friendly language
print(result["bot_response"])
# "✅ Good news! Your system is clean..."
# OR
# "🚨 I found 2 critical issues..."
```

The bot:
- Translates technical findings to plain language
- Provides step-by-step remediation
- Always asks for user approval
- Escalates to IT for critical issues

## 📂 PROJECT STRUCTURE

```
COA_Project/
├── main.py                    # CLI entry point
├── gui.py                     # Desktop GUI
├── helpdesk_api.py            # REST API server
├── run.bat                    # Windows quick launcher
├── requirements.txt           # Dependencies
├── README.md                  # User documentation
├── SETUP_GUIDE.md             # Installation guide
│
├── config/
│   └── settings.py            # Configuration
│
├── agents/
│   ├── council.py             # 3 main agents (CrewAI)
│   ├── incident_reporter.py   # Agent #4
│   └── prompts.py             # All agent prompts
│
├── core/
│   ├── data_collector.py      # Async parallel collection
│   ├── threat_analyzer.py     # ML-style scoring
│   ├── solution_engine.py     # Command generator
│   ├── virustotal.py          # VT API integration
│   ├── yara_engine.py         # YARA rules engine
│   └── rules/
│       └── baseline.yar       # 7 detection rules
│
├── utils/
│   ├── admin_check.py         # Privilege verification
│   ├── ui_manager.py          # Rich CLI components
│   ├── cache.py               # Smart cache (TTL)
│   ├── logger.py              # Structured logging
│   ├── report_generator.py    # TXT reports
│   └── html_report.py         # Interactive HTML
│
└── tests/
    ├── test_core.py           # 34 core tests
    └── test_v3_features.py    # 19 v3 tests
                               # = 53 tests total ✅
```

## 🎯 USE CASES

### 1. Personal Use
End users run periodic scans to ensure their machine is clean.

### 2. IT Helpdesk Automation
Helpdesk bots scan user machines remotely when issues are reported.

### 3. SOC Integration
Security teams export JSON reports to SIEM systems.

### 4. Incident Response
Rapid triage during security incidents with MITRE ATT&CK mapping.

### 5. Compliance Auditing
Regular automated scans with auditable trail.

## 🔮 FUTURE ROADMAP

### v4.0 (Planned)
- Real-time monitoring daemon
- Windows Event Log parsing
- Registry tampering detection  
- Network traffic capture
- Mobile app (remote scanning)
- Docker containerization

### v5.0 (Vision)
- Multi-machine fleet management
- Cloud dashboard (optional opt-in)
- ML-based anomaly detection
- Threat intelligence feeds
- Automated learning from incidents

## ✅ CURRENT STATUS

- ✅ 4 AI agents fully implemented
- ✅ 3 user interfaces (CLI/GUI/API)
- ✅ 53 unit tests passing
- ✅ VirusTotal integration
- ✅ YARA rules engine (7 rules)
- ✅ MITRE ATT&CK mapping
- ✅ Multi-format reports (TXT/HTML/JSON)
- ✅ Helpdesk Bot integration ready
- ✅ Dry-run safety mode
- ✅ Command validator (blacklist)
- ✅ Rollback support for firewall rules
- ✅ Structured logging with rotation
- ✅ Smart caching (80x speedup)

## 🚀 GETTING STARTED

For end users:
```cmd
1. Download and install Ollama:
   https://ollama.com/download/windows

2. Pull the AI model:
   ollama pull llama3.1

3. Run the project:
   Right-click run.bat → "Run as administrator"
   Choose [1] for CLI or [2] for GUI
```

For developers:
```bash
git clone <repo>
cd COA_Project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v   # All 53 tests should pass
python main.py               # Run the system
```

---

This is C.O.A — A complete, production-ready, privacy-first AI 
security scanner. Built with care, tested rigorously, and designed 
to put humans in control of AI decisions.

🔒 Local. 🤝 Trustworthy. 🚀 Effective.
```

---

## 📖 كيف تستخدم هذا البرومبت؟

### 🎯 السيناريو 1: عرض المشروع لمستثمر
انسخ القسم الأول (PROJECT VISION) + ARCHITECTURE OVERVIEW + USE CASES

### 🎯 السيناريو 2: شرح للفريق التقني
انسخ قسم WORKFLOW + TECH STACK + DETECTION CAPABILITIES

### 🎯 السيناريو 3: إعطائه لـ AI آخر لتطوير ميزة
أعطه البرومبت كامل + اطلب الميزة المحددة:
> "Based on this C.O.A project, add a new feature that..."

### 🎯 السيناريو 4: توثيق المشروع
ضعه في README.md أو ملف توثيق رسمي

---

## 🎁 برومبت بصيغة قصيرة (Pitch in 60 seconds)

```
C.O.A is a local-first AI security scanner that uses 4 specialized 
AI agents (Data Collector, Threat Hunter, Solution Advisor, Incident 
Reporter) to detect and respond to security threats on user machines 
— without sending any data externally. 

Powered by Ollama (local LLM), it offers 3 interfaces: CLI for power 
users, GUI for everyone, and REST API for IT Helpdesk Bot integration. 

Key innovation: Human-in-the-Loop architecture — AI suggests, humans 
decide. Every command requires explicit approval. Detection includes 
network analysis, process monitoring, YARA rules, and VirusTotal 
integration. Reports map findings to MITRE ATT&CK framework.

Built in Python with CrewAI orchestration. 53 unit tests passing. 
Production-ready. Open source.

The future of security is local, transparent, and human-controlled. 
That's C.O.A.
```

---

**كل ما تحتاجه في مكان واحد. جاهز للاستخدام في أي سياق! 🚀**
