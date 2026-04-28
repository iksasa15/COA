# 🚀 دليل تشغيل C.O.A — ربط الوكلاء الثلاثة

> **الإجابة المختصرة:** لا تحتاج Google Colab! المشروع مصمم ليعمل محلياً بالكامل عبر Ollama.

## 🎯 الفكرة الأساسية

```
CrewAI (الموجود في كودنا) ──→ Ollama (محلي) ──→ llama3.1 (نموذج محلي)
            ↓
   3 وكلاء يعملون معاً
```

كل وكيل يستخدم **نفس الـ LLM المحلي**. لا cloud، لا API keys، لا تكاليف.

---

## 📋 المتطلبات

| المكون | الحد الأدنى | الموصى به |
|--------|-------------|-----------|
| RAM | 8 GB | 16 GB |
| Storage | 10 GB | 20 GB |
| OS | Windows 10+ | Windows 11 |
| Python | 3.10+ | 3.11+ |

---

## 🔧 الخطوات بالترتيب

### الخطوة 1: تثبيت Python

تأكد أن Python 3.10+ مثبت:
```cmd
python --version
```

إذا لم يكن مثبتاً، حمّل من: https://www.python.org/downloads/

⚠️ **مهم**: عند التثبيت، فعّل خيار "Add Python to PATH"

---

### الخطوة 2: تثبيت Ollama

#### Windows:
1. اذهب إلى: https://ollama.com/download/windows
2. حمّل `OllamaSetup.exe`
3. ثبّته (بمعالج التثبيت العادي)
4. سيعمل تلقائياً في الخلفية

#### للتأكد من التثبيت:
```cmd
ollama --version
```

---

### الخطوة 3: تحميل النموذج

افتح CMD وشغّل:
```cmd
ollama pull llama3.1
```

⏱️ سيستغرق 5-15 دقيقة (حجم النموذج ~4.7 GB)

#### بدائل أصغر (للأجهزة الضعيفة):
```cmd
# نموذج صغير (1.3 GB)
ollama pull llama3.2:1b

# نموذج متوسط (2 GB)
ollama pull llama3.2:3b

# Mistral (4 GB - أسرع)
ollama pull mistral
```

---

### الخطوة 4: التحقق من Ollama يعمل

في CMD جديد:
```cmd
ollama list
```

يجب أن ترى:
```
NAME                ID              SIZE      MODIFIED
llama3.1:latest     xxx             4.7 GB    2 minutes ago
```

اختبار سريع:
```cmd
ollama run llama3.1 "Hello, are you working?"
```

---

### الخطوة 5: إعداد مشروع C.O.A

```cmd
# 1. فك ضغط المشروع
cd C:\Path\To\COA_Project

# 2. إنشاء بيئة افتراضية
python -m venv venv

# 3. تفعيل البيئة
venv\Scripts\activate

# 4. تثبيت المتطلبات
pip install -r requirements.txt
```

---

### الخطوة 6: تعديل الإعدادات (إذا لزم)

افتح `config/settings.py` وعدّل:

```python
# إذا استخدمت نموذج مختلف
LLM_MODEL = "llama3.1"        # أو "mistral", "llama3.2:3b"

# هذا الـ URL لا تغيّره (Ollama يعمل عليه افتراضياً)
LLM_BASE_URL = "http://localhost:11434"

# درجة الإبداع - 0.3 جيدة للأمن
LLM_TEMPERATURE = 0.3
```

---

### الخطوة 7: تشغيل النظام 🎉

```cmd
# تأكد أن Ollama يعمل (يجب أن يكون شغال في الخلفية)
ollama list

# شغّل CMD كـ Administrator
# ثم شغّل المشروع
python main.py
```

---

## 🐛 حل المشاكل الشائعة

### ❌ "Connection refused" أو "Cannot connect to Ollama"

**السبب:** Ollama لا يعمل

**الحل:**
```cmd
# Windows: ابحث عن Ollama في Task Manager
# أو شغّله يدوياً:
ollama serve
```

### ❌ "Model not found"

**السبب:** لم يتم تحميل النموذج

**الحل:**
```cmd
ollama pull llama3.1
```

### ❌ بطء شديد في الاستجابة

**السبب:** النموذج كبير على جهازك

**الحل:** استخدم نموذج أصغر:
```cmd
ollama pull llama3.2:3b
# ثم في settings.py:
LLM_MODEL = "llama3.2:3b"
```

### ❌ "Out of Memory"

**السبب:** RAM غير كافي

**الحل:**
- أغلق التطبيقات الأخرى
- استخدم نموذج 1B بدلاً من 8B
- زد الـ swap file

---

## 🎮 طرق التشغيل

بعد التثبيت، يمكنك التشغيل بـ 3 طرق:

### 1. CLI (Command Line)
```cmd
python main.py
python main.py --dry-run        # محاكاة آمنة
python main.py --quick          # بدون AI (أسرع)
```

### 2. GUI (واجهة رسومية)
```cmd
python gui.py
```

### 3. REST API (للدمج مع bots)
```cmd
python helpdesk_api.py
# يعمل على http://localhost:5000
```

---

## 💡 نصائح للأداء الأفضل

### 1. للجهاز الضعيف (8GB RAM):
```python
# في settings.py
LLM_MODEL = "llama3.2:1b"   # نموذج صغير وسريع
```

### 2. للجهاز المتوسط (16GB RAM):
```python
LLM_MODEL = "llama3.1"      # افتراضي جيد
```

### 3. للجهاز القوي (32GB+ RAM):
```python
LLM_MODEL = "llama3.1:70b"  # أكثر دقة
# يحتاج 40GB+ RAM
```

### 4. استخدام GPU (إذا متوفر):
Ollama يستخدم GPU تلقائياً إذا كان متوفراً (NVIDIA).
للتحقق:
```cmd
ollama ps
# يجب أن ترى "GPU" بدلاً من "CPU"
```

---

## 🆚 مقارنة الخيارات

| الخيار | السرعة | الخصوصية | التكلفة | التعقيد |
|--------|--------|----------|---------|---------|
| **Ollama المحلي** ⭐ | ⚡⚡ | 🔒🔒🔒 | مجاني | بسيط |
| Google Colab | ⚡ | ❌ | مجاني محدود | معقد |
| OpenAI API | ⚡⚡⚡ | ❌ | $$$ | بسيط |
| Claude API | ⚡⚡⚡ | ❌ | $$$ | بسيط |

**التوصية النهائية:** Ollama المحلي هو الخيار الأمثل لمشروع أمني يهتم بالخصوصية.

---

## 🔍 إذا أصرّيت على Google Colab

⚠️ **لا أنصح بهذا لمشروعك** لأنه:
1. يفقد فلسفة "Local & Private"
2. Colab ينقطع كل ساعتين
3. يحتاج ngrok معقّد
4. بطء بسبب الإنترنت

لكن إذا كنت تريد التجربة فقط، إليك الخطوات في الملف التالي.

---

## 📞 للدعم

إذا واجهت أي مشكلة، ابعث لي:
1. لقطة شاشة للخطأ
2. مخرجات `ollama list`
3. مخرجات `python --version`
4. حجم RAM لديك

سأساعدك في الحل! 🚀
