# GATE-PVFC-SD-001 — مؤثرات انتقال الألياف وأبراج Selberg–Delange

```text
STATUS          = REVIEW-IN-PROGRESS
VERDICT         = PARTIAL
SEARCH-CUTOFF   = 2026-08-02
PASS            = 1 (مسح أول، غير شامل)
```

## السؤال البحثي

هل يوجد في الأدبيات تمثيل موحد لانتقالات الألياف على **جميع** معاملات
Selberg–Delange، بحيث يُعطى برج المعاملات التقاربية بمؤثرات رفع/خفض على بنية
دوال متناظرة مخصَّصة عند \(x_p = p^{-s}\)؟

## نطاق المسح

| البعد | ما شمله |
|---|---|
| المحرك | Consensus (Semantic Scholar + PubMed + Scopus + arXiv)، وبحث ويب، وتحقق مباشر من arXiv |
| العبارات | Selberg–Delange asymptotic coefficients؛ symmetric function specialization Dirichlet series prime powers؛ vertex operators Hall–Littlewood raising operators |
| تاريخ القطع | 2026-08-02 |
| ما لم يُمسح | multislice / Schreier orbits (العبارة انحرفت إلى نتائج غير ذات صلة، تحتاج صياغة أدق) |

## الحصيلة

### 1. طرف Selberg–Delange: ناضج ونشط، لكن بلا بنية مؤثرات

الأدبيات هنا غزيرة ومستمرة إلى 2025، وكلها تدور على **التقديرات التقاربية
لمتوسطات الدوال الضربية**، لا على بنية جبرية لبرج المعاملات:

- Bretèche–Tenenbaum، فروض بديلة للطريقة الكلاسيكية (Acta Arithmetica 2020، محكَّم).
- Granville–Koukoulopoulos، ما وراء طريقة LSD حين يكون المتوسط على الأوليات
  معروفًا بحد خطأ ضعيف (The Ramanujan Journal 2017، محكَّم).
- Koukoulopoulos–Soundararajan، بنية الدوال الضربية ذات المجاميع الجزئية الصغيرة
  (Discrete Analysis 2019، محكَّم).
- Cui–Wu، الطريقة في الفترات القصيرة (Acta Arithmetica 2014؛ Science China 2018).
- Janisch، تفسير احتمالي عبر تقارب mod-Poisson (2025، **حالة النشر غير محققة**).

**الاستنتاج:** لا شيء في هذا الطرف يقدّم مؤثرات انتقال على برج المعاملات. غياب
المطابقة هنا واقعة عن هذا المسح لا عن الأدبيات كلها.

### 2. طرف الدوال المتناظرة: يوجد إطار قريب جدًا — وهو الأهم

**Weising، *Artin Symmetric Functions*، arXiv:2409.09643v3**
(قُدِّم 2024-09-15، آخر مراجعة 2024-10-31؛ math.NT + math.CO + math.RT).
**نسخة أولية — لا مرجع دورية ولا DOI ناشر.** تحقُّق مباشر من صفحة arXiv بتاريخ
تاريخ القطع أعلاه.

يبني هذا العمل **حلقة دوال متناظرة حسابية** من عائلة حلقات مفهرسة بالمثاليات
الأولية، ويفكّ عناصرها في أساس Hall–Littlewood مخصَّص، ثم يحسب تحويلات Mellin
ويربطها بجداءات لا نهائية من دوال \(L\) لأرتين المزاحة، ويعطي مفكوكًا صريحًا
لسلاسل ديريشليه الناتجة عبر مُوالِد Hall–Littlewood.

**الأثر على `CLAIM-0001`** (أن \(D_\lambda(s)\) تخصيص للدالة المتناظرة الأحادية
\(m_\lambda\) عند \(x_p=p^{-s}\)): الإطار العام — دوال متناظرة مفهرسة بالأوليات
تُنتج سلاسل ديريشليه عبر تخصيص — **موجود ومنشور**. فحالة الادعاء
`KNOWN-IN-EQUIVALENT-FORM` تبقى، ولا يجوز وصفه بالجِدّة. والجذر أقدم من ذلك:
تماثل Satake بصيغة Macdonald هو ما يربط الأساس المتناظر بالعوامل المحلية أصلًا،
وهو مذكور في العمل نفسه.

### 3. طرف المؤثرات: المفهوم قياسي منذ 1991

- Jing، *Vertex operators and Hall–Littlewood symmetric functions*
  (Advances in Mathematics 1991، محكَّم، 175 استشهادًا). مؤثر يُلحق جزءًا
  بالتقسيم، ومعاملات Kostka–Foulkes معاملاتُ مصفوفة على الفضاء.
- Shimozono–Zabrocki، تعميم مؤثرات Jing (Advances in Mathematics 2000، محكَّم).
- Garsia، الربط بين مؤثرات الرفع ومتعددات Macdonald (Discrete Math 1992، محكَّم).
- Rozhkovskaya، التحويلات الخطية على مؤثرات Hall–Littlewood
  (Journal of Mathematical Sciences 2023، محكَّم).

**الأثر على `CLAIM-0003`**: «مؤثر ينتقل بين ألياف/تقسيمات» ليس مفهومًا جديدًا؛
هو مؤثر Bernstein/Jing القياسي. الجِدّة المحتملة — إن وُجدت — ليست في وجود
المؤثر بل في **تخصيصه العددي عند \(x_p=p^{-s}\) وربطه ببرج معاملات
Selberg–Delange تحديدًا**. ويجب أن تُصاغ بهذا الحصر لا بإطلاق.

## الحكم

`PARTIAL`.

الطرفان موجودان في الأدبيات وناضجان: بنية الدوال المتناظرة المفهرسة بالأوليات
وتخصيصها إلى سلاسل ديريشليه من جهة، ومؤثرات الرفع على أساس Hall–Littlewood من
جهة أخرى. ولم أعثر في هذا المسح على عمل **يجمعهما على معاملات Selberg–Delange
بالتحديد**.

## ما لا يعنيه هذا الحكم

عدم العثور واقعة عن هذا المسح لا عن العالم. `PARTIAL` هنا **ليست جِدّة**، ولا
تُرقّى إلى جِدّة إلا بعد:

1. مسح `multislice` و`Schreier orbits` بصياغة أدق (لم يُنجَز).
2. فحص Macdonald، *Symmetric Functions and Hall Polynomials*، الفصل الخامس
   (تماثل Satake) قراءةً مباشرة لا اعتمادًا على ذكره في أعمال لاحقة.
3. فحص أدبيات plethysm وdouble Dirichlet series بحثًا عن الجسر المفقود.
4. مراسلة مختص، فالنتيجة السالبة من مسح آلي أضعف الأدلة.

## المراجع المرشَّحة للقراءة

| المفتاح | الحالة الببليوغرافية | حالة القراءة | العلاقة |
|---|---|---|---|
| `Weising2024ArtinSymmetricFunctions` | **نسخة أولية** arXiv:2409.09643v3، محققة | DISCOVERED | PARTIAL |
| `Jing1991VertexOperators` | محكَّم، Advances in Mathematics | DISCOVERED | PARTIAL |
| `BretecheTenenbaum2020Remarks` | محكَّم، Acta Arithmetica | DISCOVERED | ADJACENT |
| `GranvilleKoukoulopoulos2017BeyondLSD` | محكَّم، The Ramanujan Journal | DISCOVERED | ADJACENT |
| `Macdonald1995SymmetricFunctions` | كتاب معياري | DISCOVERED | PARTIAL |

لا يجوز إغلاق هذه البوابة بحكم `KNOWN` قبل أن يصير أحد هذه المراجع
`FULLY-READ` بعلاقة `COVERS` — وهو قيد يفرضه المرصد آليًا لا يُترك للتقدير.

## تصريح منهجي

لا تقدّم في فرضية ريمان، ولا في فرضية ريمان المعمَّمة، ولا مسار مؤمَّن.
