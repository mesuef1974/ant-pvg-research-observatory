# GATE-PVG-FND-001 — متجه الأُسُس والتفاف ديريشليه بوصفه التفافًا جمعيًا

```text
STATUS          = CLOSED
VERDICT         = KNOWN
SEARCH-CUTOFF   = 2026-08-03
PASSES          = 1 (مسح موجَّه، ثم قراءة المصدر الأصلي)
```

## السؤال البحثي

هل تمثيل \(\mathbb N_{\ge1}\cong\bigoplus_p\mathbb N_0\) بمتجه الأُسُس
(`PVG-FND-01`)، وتحوُّلُ التفاف ديريشليه تحته إلى التفاف جمعي على المخروط
(`PVG-FND-06`)، موجودان في الأدبيات؟

## الحصيلة: نعم، منذ 1959، ومحكَّم

**Cashwell & Everett، *The ring of number-theoretic functions*، Pacific Journal
of Mathematics 9(4) 1959، ص975–985. محكَّم.** قُرئ المقال نفسه لا ملخّصًا عنه.

المقدمة، ص975:

> The domain Ω is isomorphic to the domain P of formal power series over F in a
> countable set of indeterminates.

والبند **14**، ص982، يبني التماثل صراحةً:

> Let the primes p of N be listed in any definite order \(p_1,p_2,p_3,\ldots\).
> Then every integer n may be written uniquely in the form
> \(n=p_1^{a_1}p_2^{a_2}\cdots\) and uniquely described by a vector
> \((a_1,a_2,\ldots)\) with non-negative integral components, finitely many of
> which are non-zero.

هذه **`PVG-FND-01` حرفًا بحرف**. ثم:

\[
\alpha\ \longrightarrow\ P(\alpha)=\sum\alpha(n)\,x_1^{a_1}x_2^{a_2}\cdots
\]

> addition is preserved, and \(P(\alpha\cdot\beta)=P(\alpha)P(\beta)\), the
> latter operation being the usual formal operation on power series involving
> multiplication and collection of (finite numbers of) "like terms."

وضربُ متسلسلتَي قوى هو التفافُ معاملاتهما الجمعي على شبكة الأُسُس. فهذه
**`PVG-FND-06` حرفًا بحرف**.

أي أن النتيجتين مذكورتان **معًا في فقرة واحدة** قبل 67 سنة، في دورية محكَّمة،
ولغرضٍ آخر تمامًا: البرهنة على أن حلقة الدوال الحسابية وحيدةُ التحليل.

## أدلة مساندة

| المرجع | العلاقة | الملاحظة |
|---|---|---|
| Elliott، *Ring structures on groups of arithmetic functions*، J. Number Theory 2008، محكَّم | مجاور | يمضي أبعد: بنية حلقية عبر متجهات Witt، الجمع فيها التفافُ ديريشليه. |
| MacHenry–Wong، arXiv:1009.1892؛ وRocky Mountain J. Math. 42(4) 2012 | مجاور | تمثيل الدوال الضربية بمتعدّدات Schur الخطّافية. **لم يُقرأ بعد.** |

## الحكم

`KNOWN`. لا فجوة ولا مساحة جِدّة، ولم تُدَّع.

### الأثر

`CLAIM-PVG-FND-01` و`CLAIM-PVG-FND-06` كلتاهما `KNOWN` بإسناد محكَّم مقروء.

وهذا لا يقدح في PVG. الأساس المشترك مع أدبيات راسخة **دليل صحة لا عيب**؛ والذي
كان عيبًا هو بقاؤه غير مفحوص. عدمُ العثور سابقًا كان واقعةً عن مسحنا لا عن
العالم — وهذه الواقعة انتهت اليوم.

### درس منهجي

بحثُ الأدبيات بدأ من الطبقات العليا (`PVFC`، Selberg–Delange) وتَرك الأسس بلا
فحص لأنها «بديهية». والبديهي هو أوّل ما يجب فحصه: هو الأكثر احتمالًا أن يكون
معروفًا، والأقلّ إثارةً للشك.

---

لا تقدّم في فرضية ريمان، ولا في المعمَّمة، ولا مسار مؤمَّن.
