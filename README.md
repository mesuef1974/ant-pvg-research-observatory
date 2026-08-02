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
cd D:\ant-pvg-research-observatory
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

ضع أي PDF داخل أحد هذه المجلدات، ثم استخدم من صفحة Swagger:

```text
POST /api/documents/import-local
```

مثال الطلب:

```json
{
  "relative_path": "encyclopedia/volume-01.pdf",
  "source_layer": "ENCYCLOPEDIA",
  "title": "الموسوعة الشاملة في نظرية الأعداد التحليلية — المجلد الأول"
}
```

المستورد:

- يمنع المسارات خارج `library/`؛
- يقبل PDF فقط في هذه المرحلة؛
- يسجل SHA-256 والحجم وعدد الصفحات؛
- يعيد السجل الموجود إذا أُعيد استيراد الملف نفسه؛
- يحفظ المسار النسبي فقط، ولا يرفع الملف إلى Git.

لعرض الوثائق المسجلة:

```text
GET /api/documents
```

## الحالة

```text
VERSION = 0.2.0-dev
PHASE   = MULTI-DOCUMENT LOCAL LIBRARY
BRANCH  = agent/library-multidoc-import-v0.2
```
