# GATE-PVG-FND-002 — أسس PVG الحسابية والشبكية

```text
STATUS          = CLOSED
VERDICT         = KNOWN
SEARCH-CUTOFF   = 2026-08-03
PASSES          = 1 (مسح موجَّه + قراءة المصدرين)
```

## السؤال البحثي

بعد أن تبيّن أن `PVG-FND-01` و`PVG-FND-06` هما Cashwell–Everett 1959، بقيت
أربع نتائج في الطبقة نفسها بلا فحص:

| المعرّف | النتيجة |
|---|---|
| `PVG-FND-02` | \(\mathbb Q_{>0}\cong\bigoplus_p\mathbb Z\) |
| `PVG-FND-03` | \(\nu(mn)=\nu(m)+\nu(n)\) |
| `PVG-FND-04` | القسمة ترتيب، وgcd/lcm هما min/max |
| `PVG-FND-05` | القواسم نقاط صندوق |

## الحصيلة: أربعتها معروفة، بمصدرين مقروءين

### `FND-02` و`FND-03` — Cashwell–Everett 1959، البند 14 ص982

التوصيف الوحيد لكل صحيح بمتجه أُسُس منتهي الحامل يجعل ضربَ الأعداد جمعًا
للمتجهات — وهذه `FND-03` بعينها، أي أن التطابق **تماثلُ أحاديات**. و`FND-02`
تتمّتُه الزمرية: عند تمرير التماثل إلى \(\mathbb Q_{>0}\) تصير المركّبات
صحيحة، فتُعطى الزمرةُ الحرة الأبيلية على الأوليات.

### `FND-04` و`FND-05` — Haukkanen 2016، المقدمة ص68. محكَّم

قُرئت المقدمة في ملف PDF الأصلي. نصُّها:

> It is well known that the set \(\mathbb Z_+\) of positive integers is a poset
> under the usual divisibility relation. It is likewise well known that the gcd
> and the lcm operations serve as the meet and the join on this poset. Thus
> \(\mathbb Z_+\) is a lattice under the usual divisibility relation, known as
> **the divisor lattice**. This lattice is distributive.

هذه **`FND-04` بلفظها**. وللبنية **اسمٌ مستقرّ** في الأدبيات: *the divisor
lattice*. وتكرار «well known» مرّتين في سطرين شهادةٌ إضافية على كلاسيكيّتها.

و`FND-05` تتبعها في سطر: \(d\mid n\iff 0\le\nu_p(d)\le\nu_p(n)\) لكل \(p\)،
فالقواسم **فترةٌ** في الشبكة — صندوقٌ — وعددُ نقاطها \(\prod(a_p+1)=\tau(n)\)،
وهي صيغة في كل مقرَّر.

## الحكم

`KNOWN` للأربع. لا فجوة ولا مساحة جِدّة، ولم تُدَّع.

## الخط الفاصل

مع البوابة السابقة، صارت **ستُّ نتائج** من طبقة أسس PVG مسنَدةً إلى أدبيات
محكَّمة: `FND-01` … `FND-06`. أي أن **طبقة الأسس كلها كلاسيكية** — وهذا ليس
قدحًا بل تحديدُ موضع: PVG لا يبدأ عند الأسس، بل يبدأ بعدها.

وهذا الخط هو المكسب الحقيقي: كل ادعاء جِدّة لاحق يُقاس إليه، ولا يُطالَب بأن
يُثبت جِدّة ما هو دونه.

---

لا تقدّم في فرضية ريمان، ولا في المعمَّمة، ولا مسار مؤمَّن.
