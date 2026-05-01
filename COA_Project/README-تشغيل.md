# تشغيل C.O.A — دليل سريع

## المتطلبات

- **Python 3.11** (يفضّل عبر Homebrew مع `python-tk@3.11` إن أردت واجهة Tk القديمة)
- **Node.js 18+** و `npm` — لواجهة **React** فقط
- (اختياري) **Ollama** للنماذج المحلية مع CrewAI

---

## 1) إعداد البيئة

```bash
cd COA_Project
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

على **macOS** إذا ظهر خطأ `_tkinter` عند تشغيل `gui.py`:

```bash
brew install python-tk@3.11
# ثم أعد إنشاء الـ venv باستخدام:
# /opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv
```

---

## 2) واجهة React (موصى بها)

تحتاج **طرفيتين**.

### الطرفية أ — خادم الـ API

```bash
cd COA_Project
source venv/bin/activate
python web_api.py
```

أو:

```bash
python react_gui.py
```

أو:

```bash
python main.py --gui
```

الخادم يعمل على: **http://127.0.0.1:5050**

### الطرفية ب — واجهة الويب

```bash
cd COA_Project/web
npm install          # مرة واحدة فقط
npm run dev
```

افتح المتصفح: **http://localhost:5173** (تظهر **صفحة الرئيسية**).

- من الرئيسية اضغط **«الانتقال إلى صفحة الأداء»** أو افتح مباشرة: **http://localhost:5173/#/dashboard**
- بعد فحص ناجح: **http://localhost:5173/#/mitre-heatmap** لعرض خريطة MITRE الحرارية (أو من رابط «خريطة MITRE» في لوحة الأداء).
- في لوحة الأداء اضغط **Start scan** لبدء الفحص.
- التصدير (TXT / HTML / تقرير الحادث) يعمل بعد فحص ناجح.

---

## 3) سطر الأوامر (CLI)

```bash
cd COA_Project
source venv/bin/activate
python main.py
```

خيارات مفيدة:

```bash
python main.py --dry-run
python main.py --no-admin-check
python main.py --vt --yara
```

---

## 4) واجهة Tkinter القديمة (اختياري)

```bash
cd COA_Project
source venv/bin/activate
python gui.py
```

---

## 5) API الـ Helpdesk (منفذ 5000)

```bash
python helpdesk_api.py
```

---

## 6) Ollama (اختياري)

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

---

## 7) بناء واجهة React للإنتاج (بدون `npm run dev`)

```bash
cd COA_Project/web
npm run build
```

الملفات تُنشأ في `web/dist/` — يمكن لاحقاً جعل Flask يخدم `dist/` من مسار ثابت إذا رغبت.

---

## استكشاف الأخطاء

| المشكلة | الحل |
|--------|------|
| `command not found: ollama` | ثبّت Ollama (مثلاً `brew install ollama`) |
| `could not connect to running Ollama` | `brew services start ollama` |
| `ModuleNotFoundError: _tkinter` | استخدم واجهة React أو `brew install python-tk@3.11` وأعد بناء الـ venv |
| الواجهة لا تتصل بالـ API | تأكد أن `web_api.py` يعمل على **5050** قبل `npm run dev` |
| فشل الـ scan من المتصفح | تحقق من الطرفية التي تشغّل Python لرسالة الخطأ |

---

لمزيد من التفاصيل والمعمارية راجع `README.md` في نفس المجلد.
