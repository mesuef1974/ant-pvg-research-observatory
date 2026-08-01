# ANT–PVG Research Observatory

منصة بحث محلية، محكومة بالمصادر، لإدارة موسوعة نظرية الأعداد التحليلية وخرائط المعرفة والادعاءات والمراجع وبوابات مراجعة الأدبيات لمشروعات ANT وPVG/PVFC.

## المبادئ

- **Local-first:** ملفات الكتب والموسوعات وقواعد البيانات التشغيلية تبقى محليًا.
- **ثلاث طبقات منفصلة:** `ENCYCLOPEDIA` و`MODEL_SYNTHESIS` و`LITERATURE`.
- **لا جدة بلا بوابة أدبيات:** `NOT-FOUND-YET` لا تعني `NOVEL`.
- **الادعاء ككائن مستقل:** بيان، حالة، أدلة، اعتماد، ومراجعة جدة.
- **GitHub للشفرة والحوكمة فقط:** لا PDF ولا SQLite تشغيلية في المستودع.

## بدء التشغيل محليًا

```powershell
cd D:\ant_pvg_research_observatory
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn ant_pvg_observatory.main:app --reload --app-dir backend/src
```

ثم افتح:

```text
http://127.0.0.1:8000/docs
```

## الاختبارات

```powershell
ruff check .
pytest -q
```

## المكتبة المحلية

أنشئ المجلدات محليًا ولا تدفعها إلى Git:

```text
library/
├── encyclopedia/
├── books/
├── papers/
├── pvg/
└── notes/
```

## الحالة

```text
VERSION = 0.1.0-dev
PHASE   = PLATFORM FOUNDATION
BRANCH  = agent/platform-v1-foundation
```
