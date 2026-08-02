# ANT–PVG Research Observatory

منصة بحث محلية، محكومة بالمصادر، لإدارة موسوعة نظرية الأعداد التحليلية وخرائط المعرفة والادعاءات والمراجع وبوابات مراجعة الأدبيات لمشروعات ANT وPVG/PVFC.

## المبادئ

- **Local-first:** ملفات الكتب والموسوعات وقواعد البيانات التشغيلية تبقى محليًا.
- **ثلاث طبقات منفصلة:** `ENCYCLOPEDIA` و`MODEL_SYNTHESIS` و`LITERATURE`.
- **لا جدة بلا بوابة أدبيات:** `NOT-FOUND-YET` لا تعني `NOVEL`.
- **الادعاء ككائن مستقل:** بيان، حالة، أدلة، اعتماد، ومراجعة جدة.
- **GitHub للشفرة والحوكمة فقط:** لا PDF ولا SQLite تشغيلية في المستودع.

راجع `ARCHITECTURE.md` للبنية المرجعية وحدود التخزين والحوكمة وخارطة المراحل.

## بدء التشغيل محليًا

```powershell
cd D:\ant-pvg-research-observatory
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn ant_pvg_observatory.main:app --reload --app-dir backend/src
```

شغّل `alembic upgrade head` بعد أي سحب يتضمن ترحيلات جديدة، وقبل تشغيل الخادم.

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

ضع أي PDF داخل أحد هذه المجلدات، ثم استخدم:

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

## فهرسة الصفحات

بعد استيراد الوثيقة، خذ قيمة `id` الخاصة بها ثم نفّذ:

```text
POST /api/documents/{document_id}/index-pages
```

مثال للموسوعة إذا كان رقمها `2`:

```text
POST /api/documents/2/index-pages
```

يعيد الطلب ملخصًا بعدد الصفحات المستخرجة والفارغة والفاشلة. ولعرض النص صفحةً صفحة:

```text
GET /api/documents/{document_id}/pages
```

إعادة الفهرسة آمنة: تُستبدل صفحات الوثيقة نفسها ولا تتكرر السجلات. حالة `EMPTY` تعني أن محرك PDF لم يستخرج نصًا، ولا تثبت أن الصفحة المرئية فارغة.

## الحالة

```text
VERSION = 0.3.0-dev
PHASE   = PDF PAGE INDEXING
BRANCH  = agent/pdf-page-indexing-v0.3
```
