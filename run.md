# تشغيل C.O.A من البداية للنهاية

دليل عملي واحد: المتطلبات، الإعداد، ثم كل طرق التشغيل (واجهة React، CLI، Tkinter، Helpdesk API) مع المنافذ واستكشاف الأخطاء.

**المجلد الأساسي للمشروع:** `COA_Project/` (كل أوامر Python و`web/` من داخله ما لم يُذكر غير ذلك).

**وثائق إضافية:**

- [COA_Project/README-تشغيل.md](COA_Project/README-تشغيل.md) — مختصر بالعربية
- [SETUP_GUIDE.md](SETUP_GUIDE.md) — Ollama وWindows وتفاصيل النماذج
- [COA_Project/README.md](COA_Project/README.md) — المعمارية والميزات

---

## 1. ماذا تحتاج قبل البدء

| المكوّن | مطلوب؟ | ملاحظات |
|---------|---------|---------|
| **Python** | نعم | يُفضّل **3.11** (موثّق في المشروع). 3.10+ قد يعمل؛ راجع `requirements.txt`. |
| **pip + venv** | نعم | لعزل التبعيات داخل `COA_Project/venv`. |
| **Node.js 18+ و npm** | نعم **لواجهة React فقط** | لتشغيل `npm run dev` و`npm run build` داخل `COA_Project/web`. |
| **Ollama** | اختياري | للمجلس (CrewAI) والتحقق من وكلاء الذكاء في الواجهة؛ الفحص بدون مجلس يعمل بدونه. |
| **مفتاح VirusTotal** | اختياري | فقط عند تشغيل `--vt`؛ عرّف `VT_API_KEY` في `.env`. |

**ذاكرة وتخزين تقريبية:** RAM 8 GB كحد أدنى للتجربة؛ 16 GB أوصى إن استخدمت نماذج Ollama أكبر. مساحة كافية لـ `venv` ولنماذج Ollama إن وُجدت.

---

## 2. الخطوة 1 — الدخول للمشروع وإنشاء البيئة الافتراضية

```bash
cd COA_Project
python3.11 -m venv venv
```

**تفعيل البيئة:**

- macOS / Linux:
  ```bash
  source venv/bin/activate
  ```
- Windows (CMD):
  ```cmd
  venv\Scripts\activate
  ```

**تثبيت التبعيات:**

```bash
pip install -r requirements.txt
```

---

## 3. الخطوة 2 — ملف البيئة `.env`

من جذر `COA_Project`:

```bash
cp .env.example .env
```

عدّل `.env` حسب الحاجة (على الأقل نموذج Ollama إن استخدمت المجلس):

- `COA_LLM_MODEL` — مثل `llama3.1` أو `llama3.2:3b`
- `COA_LLM_BASE_URL` — عادة `http://localhost:11434`
- `VT_API_KEY` — إن أردت `--vt`

لا ترفع `.env` إلى Git إذا احتوى على أسرار.

---

## 4. الطريقة الموصى بها — واجهة React + API (طرفيتان)

### الطرفية 1: خادم Flask (API)

```bash
cd COA_Project
source venv/bin/activate   # أو venv\Scripts\activate على Windows
python web_api.py
```

- يعمل على: **http://127.0.0.1:5050**
- بدائل مكافئة لتشغيل نفس الـ API (اختر واحداً): `python react_gui.py` أو `python main.py --gui` (حسب ما وثّقه المشروع).

### الطرفية 2: واجهة Vite (React)

```bash
cd COA_Project/web
npm install    # مرة واحدة بعد الاستنساخ أو تغيير package.json
npm run dev
```

- المتصفح: **http://localhost:5173**
- الرئيسية: `http://localhost:5173/#/`
- لوحة الفحص: `http://localhost:5173/#/dashboard`

**بعد تشغيل الاثنين:**

- من لوحة الفحص: **بدء فحص** يجمع من الجهاز عبر الـ API.
- **تحميل بيانات وهمية** يستدعي `POST /api/demo/seed-session` دون جمع من الجهاز (لتجربة الواجهات).
- التصدير (TXT / HTML / تقرير حادث / Navigator JSON) يُفعّل عادة بعد فحص ناجح أو جلسة وهمية محمّلة.

**ملاحظة:** إعداد Vite قد يوجّه طلبات `/api` إلى المنفذ 5050 — إن فشل الاتصال، تأكد أن `web_api.py` يعمل أولاً.

---

## 5. سطر الأوامر (CLI)

```bash
cd COA_Project
source venv/bin/activate
python main.py
```

أمثلة خيارات:

```bash
python main.py --dry-run
python main.py --no-admin-check
python main.py --vt --yara
```

التقارير تُكتب عادة تحت مجلد التقارير حسب إعدادات المشروع (راجع `README.md`).

---

## 6. واجهة Tkinter (قديمة)

```bash
cd COA_Project
source venv/bin/activate
python gui.py
```

على **macOS** إن ظهر خطأ `_tkinter`: راجع قسم Tk في [README-تشغيل.md](COA_Project/README-تشغيل.md) (`python-tk` وإعادة إنشاء الـ venv).

---

## 7. Helpdesk API (منفذ مختلف)

```bash
cd COA_Project
source venv/bin/activate
python helpdesk_api.py
```

- يعمل على: **http://127.0.0.1:5000** (وليس 5050)
- للدمج مع بوتات أو أتمتة خارج واجهة المتصفح.

---

## 8. Ollama (اختياري — للمجلس والوكلاء)

1. ثبّت Ollama من الموقع الرسمي أو عبر الحزم (مثل `brew install ollama` على macOS).
2. شغّل الخدمة ثم حمّل نموذجاً:
   ```bash
   ollama pull llama3.1
   ```
3. تأكد أن القيم في `.env` تطابق النموذج وعنوان Ollama.

تفاصيل إضافية ونماذج أخف: [SETUP_GUIDE.md](SETUP_GUIDE.md).

**تشغيل مجلس CrewAI من CLI (بعد جاهزية Ollama):**

```bash
cd COA_Project && source venv/bin/activate && python main.py --council
```

أو: `bash COA_Project/scripts/council-local.sh` من جذر المستودع.

---

## 9. بناء واجهة React للإنتاج (بدون `npm run dev`)

```bash
cd COA_Project/web
npm run build
```

المخرجات في `COA_Project/web/dist/`. يمكن لاحقاً ربط Flask بخدمة `dist/` إن رغبت بعرض ثابت من الخادم نفسه.

---

## 10. استكشاف الأخطاء السريع

| العرض أو الرسالة | ماذا تفعل |
|-------------------|-----------|
| الواجهة لا تتصل بالـ API | تأكد أن `python web_api.py` يعمل على **5050** قبل فتح Vite. |
| `could not connect` / Ollama | شغّل Ollama؛ `ollama list`؛ تأكد من `COA_LLM_BASE_URL` في `.env`. |
| فشل الفحص من المتصفح | راجع طرفية Python لرسالة الخطأ (صلاحيات، جدار ناري، إلخ). |
| `ModuleNotFoundError: _tkinter` | استخدم React أو ثبّت `python-tk` وأعد إنشاء الـ venv (انظر README-تشغيل). |
| نموذج غير موجود | `ollama pull <اسم_النموذج>` ومزامنة الاسم مع `.env`. |

---

## 11. ملخص المنافذ

| الخدمة | المنفذ الافتراضي |
|--------|------------------|
| API الويب (`web_api.py`) | **5050** |
| واجهة React (`npm run dev`) | **5173** |
| Helpdesk API | **5000** |
| Ollama | **11434** |

---

## 12. ختام

1. `cd COA_Project` → `venv` → `pip install -r requirements.txt`
2. `cp .env.example .env` وتعديل اختياري
3. لتجربة كاملة بالواجهة: **طرفية API** + **طرفية `npm run dev`**
4. Ollama اختياري للمسار الذي يستخدم المجلس / CrewAI

للتفاصيل المعمارية والوكلاء: [COA_Project/README.md](COA_Project/README.md).
