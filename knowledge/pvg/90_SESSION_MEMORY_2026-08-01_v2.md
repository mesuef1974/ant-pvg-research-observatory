# ذاكرة جلسة مشروع PVG — سجل مرجعي تشغيلي

```text
PROJECT        = Prime-Valuation Geometry (PVG)
SESSION-DATE   = 2026-08-01
LANGUAGE       = Arabic
STATUS         = CONSOLIDATED-SESSION-MEMORY
PURPOSE        = منع تكرار المسارات المنجزة، تثبيت النتائج والتصحيحات، وتحديد السؤال التالي
SCOPE          = كل ما أمكن استعادته من سياق هذه الجلسة والمحتوى الظاهر فيها
LIMITATION     = هذا سجل علمي شامل ومنظم، وليس نسخًا حرفيًا لكل رسالة؛ بعض المقاطع
                 كانت مختصرة/محذوفة في واجهة السياق، لذلك لا يمكن إعادة بناء النص الحرفي
                 الكامل لها دون ملف تصدير للمحادثة.
```

---

## 0. قاعدة التشغيل من الآن

قبل أي متابعة في PVG يجب فحص هذا الملف أولًا.

لا يُعاد فتح موضوع مسجل تحت `CLOSED / ESTABLISHED` إلا في واحدة من الحالات:

1. طلب المستخدم إعادة الشرح.
2. ظهور تعارض أو خطأ يحتاج تصحيحًا.
3. الانتقال من النتيجة القديمة إلى تعميم جديد محدد.
4. تقديم مثال جديد يختبر النتيجة، لا يعيدها فقط.

الرد التالي لا يبدأ من تعريفات:
- متجه التقييم،
- الدعم،
- \(\omega,\Omega\)،
- جمع المتجهات،
- \(\gcd/\operatorname{lcm}\)،
- صندوق القواسم،
- تفكيك الطبقات،
إلا إذا كان ذلك ضروريًا مباشرة للسؤال الجديد.

---

# 1. الهدف الأعلى للجلسة

التركيز كان على **PVG نفسها**، لا على ANT ولا غولدباخ ولا زيتا، مع السعي للانتقال من:

\[
n=\prod_p p^{\nu_p(n)}
\longleftrightarrow
\nu(n)=(\nu_2(n),\nu_3(n),\nu_5(n),\ldots)
\]

بوصفه تمثيلًا ساكنًا، إلى بنية تشمل:

- المحاور والوجوه والخلايا.
- العلاقة بين الوجوه.
- الشكل والحجم والدعم.
- مصفوفات الوجوه والطيف.
- المتجهات والحقول المتجهة.
- التفاضل المنفصل.
- الهسيان والانحناء المختلط.
- التدفقات والديناميكا.
- تطبيق أولي على \(\tau(n)\).

---

# 2. الوجه \(2\!-\!3\) — الحالة المعتمدة

## 2.1 تعريف الوجه

\[
\mathcal F_{2,3}
=
\{2^a3^b:a,b\in\mathbb N_0\}
\longleftrightarrow
\mathbb N_0^2.
\]

النقطة:

\[
2^a3^b\longleftrightarrow(a,b).
\]

## 2.2 المحاور والداخل

- محور \(2\): \((a,0)\).
- محور \(3\): \((0,b)\).
- داخل الوجه: \((a,b)\) مع \(a,b\ge1\).

## 2.3 العمق الوجهي

\[
d_{23}(a,b)=\min(a,b).
\]

والتفكيك:

\[
2^a3^b
=
6^{d_{23}}2^{a-d_{23}}3^{b-d_{23}}.
\]

بعد استخراج \(6^{d_{23}}\)، تقع البقية على أحد المحورين.

## 2.4 خط التوازن

\[
a=b.
\]

وهو شعاع:

\[
6^d.
\]

---

# 3. المخروط \(2\!-\!3\!-\!5\) والعلاقة بين الوجوه

## 3.1 المخروط

\[
\mathcal C_{2,3,5}
=
\{2^a3^b5^c:a,b,c\in\mathbb N_0\}.
\]

## 3.2 الوجوه

\[
\mathcal F_{23}:c=0,\qquad
\mathcal F_{25}:b=0,\qquad
\mathcal F_{35}:a=0.
\]

## 3.3 الداخل الحقيقي

\[
a,b,c\ge1.
\]

أول نقطة داخلية:

\[
(1,1,1)\longleftrightarrow30.
\]

إسقاطاتها الوجهية:

\[
6,\quad10,\quad15.
\]

## 3.4 هوية إعادة البناء من الوجوه

لـ:

\[
n=2^a3^b5^c,
\]

نعرف:

\[
\pi_{23}(n)=2^a3^b,\quad
\pi_{25}(n)=2^a5^c,\quad
\pi_{35}(n)=3^b5^c.
\]

ثم:

\[
\boxed{
n^2=\pi_{23}(n)\pi_{25}(n)\pi_{35}(n).
}
\]

وكذلك:

\[
\boxed{
n=
\gcd(\pi_{23},\pi_{25})
\gcd(\pi_{23},\pi_{35})
\gcd(\pi_{25},\pi_{35}).
}
\]

## 3.5 مبرهنة اللصق

ثلاث نقاط على الوجوه تلصق إلى نقطة داخلية واحدة إذا وفقط إذا اتفقت تقييماتها على المحاور المشتركة:

\[
\nu_2(x_{23})=\nu_2(x_{25}),
\]

\[
\nu_3(x_{23})=\nu_3(x_{35}),
\]

\[
\nu_5(x_{25})=\nu_5(x_{35}).
\]

هذه النتيجة معتمدة كأساس لنظرية لصق البيانات الوجهية.

---

# 4. العمق الثلاثي وتوجيه الخروج

## 4.1 العمق الثلاثي

\[
d_{235}(a,b,c)=\min(a,b,c).
\]

والتفكيك:

\[
2^a3^b5^c
=
30^d\,2^{a-d}3^{b-d}5^{c-d}.
\]

بعد نزع \(30^d\)، تنعدم مركبة واحدة على الأقل، فتقع البقية على أحد الوجوه.

## 4.2 وجه الخروج

- إذا كان \(c\) هو الأصغر: الخروج إلى \(F_{23}\).
- إذا كان \(b\) هو الأصغر: الخروج إلى \(F_{25}\).
- إذا كان \(a\) هو الأصغر: الخروج إلى \(F_{35}\).

## 4.3 جدران التعادل

\[
a=b,\qquad a=c,\qquad b=c.
\]

والشعاع المركزي:

\[
a=b=c
\longleftrightarrow30^d.
\]

---

# 5. صندوق القواسم والمعقّد الوجهي

## 5.1 الصندوق الطبيعي

لـ:

\[
n=2^a3^b5^c,
\]

مجموعة القواسم تقابل:

\[
B(n)=[0,a]\times[0,b]\times[0,c].
\]

## 5.2 مساحات الوجوه

\[
A_{23}=ab,\qquad
A_{25}=ac,\qquad
A_{35}=bc.
\]

هذه **مساحات** وليست أطوال أضلاع مثلث.

تم تصحيح هذا صراحة في الجلسة.

## 5.3 استعادة الأسس من المساحات

\[
a=\sqrt{\frac{A_{23}A_{25}}{A_{35}}},
\]

\[
b=\sqrt{\frac{A_{23}A_{35}}{A_{25}}},
\]

\[
c=\sqrt{\frac{A_{25}A_{35}}{A_{23}}}.
\]

## 5.4 شرط توافق ثلاثية المساحات

ثلاثية \((X,Y,Z)\) تأتي من \((ab,ac,bc)\) إذا كانت:

\[
\frac{XY}{Z},\qquad
\frac{XZ}{Y},\qquad
\frac{YZ}{X}
\]

مربعات صحيحة كاملة.

## 5.5 الثوابت المتناظرة

\[
E_1=a+b+c,
\]

\[
E_2=ab+ac+bc,
\]

\[
E_3=abc.
\]

و:

\[
\tau(n)
=
(a+1)(b+1)(c+1)
=
1+E_1+E_2+E_3.
\]

## 5.6 كثيرة حدود المعقّد

\[
P_n(t)=\prod_{p\mid n}(1+\nu_p(n)t).
\]

في الدعم الثلاثي:

\[
P_n(t)
=
1+E_1t+E_2t^2+E_3t^3.
\]

و:

\[
P_n(1)=\tau(n).
\]

---

# 6. قانون الضرب والتداخل المحوري

إذا:

\[
a_p=\nu_p(m),\qquad b_p=\nu_p(n),
\]

فإن:

\[
P_{mn}(t)
=
\prod_p(1+(a_p+b_p)t).
\]

إذا كان:

\[
\gcd(m,n)=1,
\]

فإن:

\[
P_{mn}(t)=P_m(t)P_n(t).
\]

أما عند وجود محور مشترك، تظهر تصحيحات محلية.

## 6.1 طاقة التداخل

\[
\boxed{
\mathcal O(m,n)
=
\sum_p\nu_p(m)\nu_p(n).
}
\]

## 6.2 تغير المساحة الوجهية

\[
\boxed{
E_2(mn)
=
E_2(m)+E_2(n)+E_1(m)E_1(n)-\mathcal O(m,n).
}
\]

## 6.3 كثيرة الحدود المعلّمة

\[
\mathscr P_n(\mathbf z)
=
\prod_p(1+\nu_p(n)z_p).
\]

هذه تحتفظ بأسماء المحاور، بخلاف \(P_n(t)\).

---

# 7. مصفوفة الوجوه وطيفها

## 7.1 التعريف

لـ:

\[
n=\prod_{i=1}^kp_i^{a_i},
\]

نعرف:

\[
F_{ij}
=
\begin{cases}
a_ia_j,&i\ne j,\\
0,&i=j.
\end{cases}
\]

وبصيغة مصفوفية:

\[
F=vv^T-D,
\]

حيث:

\[
v=(a_1,\ldots,a_k)^T,\qquad
D=\operatorname{diag}(a_1^2,\ldots,a_k^2).
\]

## 7.2 التوقيع العام

\[
\boxed{
\operatorname{Inertia}(F)=(1,k-1,0).
}
\]

أي:

- قيمة ذاتية موجبة واحدة.
- \(k-1\) قيم سالبة.
- لا أصفار.

## 7.3 المحدد

\[
\boxed{
\det(F)
=
(-1)^{k+1}(k-1)
\left(\prod_i a_i\right)^2.
}
\]

## 7.4 الحالة المتوازنة

إذا:

\[
a_1=\cdots=a_k=d,
\]

فإن:

\[
\operatorname{Spec}(F)
=
\{(k-1)d^2,-d^2,\ldots,-d^2\}.
\]

## 7.5 مثال \(30\)

\[
F=
\begin{pmatrix}
0&1&1\\
1&0&1\\
1&1&0
\end{pmatrix},
\]

وطيفها:

\[
\{2,-1,-1\}.
\]

تم شرح القيم والمتجهات الذاتية في الجلسة.

## 7.6 المعادلة الطيفية

القيم الذاتية تحقق:

\[
\boxed{
1=\sum_i\frac{a_i^2}{\lambda+a_i^2}.
}
\]

والمتجه الذاتي الموافق لقيمة \(\lambda\) يحقق:

\[
x_i\propto\frac{a_i}{\lambda+a_i^2}.
\]

---

# 8. فضاء الشكل

## 8.1 التطبيع اللوغاريتمي

للدعم الثلاثي:

\[
g=(abc)^{1/3},
\]

\[
A=\frac ag,\quad B=\frac bg,\quad C=\frac cg,
\]

ثم:

\[
u=\log A,\quad v=\log B,\quad w=\log C,
\]

بحيث:

\[
u+v+w=0.
\]

إذن فضاء الأشكال الثلاثية مستوى ثنائي الأبعاد، بعد حذف التكبير الشعاعي.

## 8.2 متري الشكل

\[
\boxed{
r^2
=
\frac13
\left[
\log^2\frac ab+
\log^2\frac ac+
\log^2\frac bc
\right].
}
\]

## 8.3 الفرق بين عمليتين

رفع العدد إلى قوة:

\[
n\mapsto n^m
\]

يعطي:

\[
(a,b,c)\mapsto(ma,mb,mc),
\]

ويحفظ الشكل.

أما الضرب في:

\[
30^t
\]

فيعطي:

\[
(a,b,c)\mapsto(a+t,b+t,c+t),
\]

ويدفع الشكل نحو التوازن.

## 8.4 معدل الانكماش

\[
r(a+t,b+t,c+t)\sim\frac{D(a,b,c)}{t}.
\]

هذا تدفق له دالة ليابونوف \(r^2\).

---

# 9. التطبيق على دالة القواسم

## 9.1 عند ثبات \(\omega,\Omega\)

إذا ثبتنا:

\[
\omega(n)=k,\qquad
\Omega(n)=A,
\]

فإن:

\[
\tau(n)=\prod_i(a_i+1)
\]

تبلغ أقصاها عندما تختلف الأسس بمقدار لا يتجاوز \(1\).

إذا:

\[
A=kq+r,\qquad0\le r<k,
\]

فالشكل الأمثل:

\[
(q+1,\ldots,q+1,q,\ldots,q).
\]

## 9.2 الترتيب بالتغليب

\[
a\succ b
\Longrightarrow
\tau(a)\le\tau(b).
\]

أي \(\log\tau\) Schur-concave في متجه الأسس عند ثبات المجموع.

## 9.3 قيد الحجم الحقيقي

عند:

\[
\sum_i a_i\log p_i\le L,
\]

الحل المستمر يحقق:

\[
\frac1{a_i+1}
=
\lambda\log p_i.
\]

أي:

\[
(a_i+1)\log p_i\approx C.
\]

## 9.4 نتائج الاختبار العددي المسجلة في الجلسة

الاختبار حتى حدود من رتبة \(10^5\)–\(3\times10^5\) أظهر:

- عدم وجود فجوات في الدعم لدى أصحاب سجلات \(\tau\).
- الأسس غير متزايدة مع الأوليات.
- الاتزان الداخلي مفيد بعد تطبيق بوابات الدعم والترتيب.
- الاستقرار تحت حركة محلية أحادية لا يكفي لتحديد صاحب السجل.
- المقياس \(R_{\mathrm{sup}}\) بصيغته المستمرة فشل، وتم رفضه.
- PVG تعمل كمرشح قوي لفضاء المرشحين، لا كحاسم للأمثلية حتى الآن.

---

# 10. الحقول المتجهة على PVG

## 10.1 الدالة كحقل قياسي

لدالة حسابية \(f\):

\[
F(a,b,\ldots)
=
f\left(\prod_pp^{a_p}\right).
\]

## 10.2 الفرق الأمامي

\[
\boxed{
D_p^+f(n)=f(np)-f(n).
}
\]

## 10.3 الفرق الخلفي

\[
\boxed{
D_p^-f(n)=f(n)-f(n/p),
\qquad p\mid n.
}
\]

## 10.4 الفرق المركزي

\[
\boxed{
D_p^0f(n)
=
\frac{f(np)-f(n/p)}2.
}
\]

## 10.5 الفرق بين \(df\) و\(\nabla f\)

- \(df\): فروق على الحواف، طبيعي من بنية الشبكة.
- \(\nabla f\): يحتاج متريًا لتحويل القيم الحافية إلى متجه.
- التباعد واللابلاسيان يحتاجان أيضًا قياسًا وأوزانًا وشروط حدود.

هذه نقطة معتمدة، ولا يجوز الخلط بينها لاحقًا.

---

# 11. تصحيح مهم في مشتقات \(\tau\)

على الوجه \(2\!-\!3\):

\[
\tau(a,b)=(a+1)(b+1).
\]

إذن:

\[
D_2^+\tau=b+1,
\qquad
D_3^+\tau=a+1.
\]

و:

\[
\boxed{
D_2^{+\,2}\tau=0,
\qquad
D_3^{+\,2}\tau=0.
}
\]

لكن:

\[
\boxed{
D_2D_3\tau=1.
}
\]

الادعاء السابق بأن المشتقة الثانية المحورية لـ\(\tau\) سالبة كان خطأ وتم تصحيحه.

لدالة \(\log\tau\)، الانحناء المحوري سالب:

\[
D_p^{+\,2}\log\tau<0.
\]

---

# 12. التفاضل الخارجي والدوران

لدالة على النقاط:

\[
dF
\]

حقل على الحواف.

ثم:

\[
\boxed{
d^2F=0.
}
\]

هذا يعني أن دوران **حقل التدرج** حول أي مربع يساوي صفرًا.

لكن لا يعني أن كل الحقول على PVG عديمة الدوران.

مثال حقل عام على وجه:

\[
V_2(a,b)=-b,\qquad V_3(a,b)=a
\]

له دوران غير صفري.

إذن:

\[
\boxed{
\operatorname{curl}\nabla F=0
}
\]

ولا يصح تعميم ذلك إلى كل الحقول.

---

# 13. الانحناء المختلط اللوغاريتمي

لدالة موجبة \(f\):

\[
\boxed{
\mathcal K_{p,q}^f(n)
=
D_pD_q\log f(n)
=
\log\frac{f(npq)f(n)}{f(np)f(nq)}.
}
\]

## 13.1 التفسير

- موجب: تعاون بين المحورين.
- سالب: تنافس.
- صفر: استقلال نسبي بينهما.

## 13.2 توصيف الضربية

مع التطبيع المناسب:

\[
\boxed{
f\text{ موجبة وضربية}
\iff
\mathcal K_{p,q}^f=0
\quad\forall p\ne q.
}
\]

هذه أقوى نتيجة مفهومية في مسار الحقول حتى الآن:

\[
\boxed{
\text{الضربية = انعدام الانحناء المختلط اللوغاريتمي}.
}
\]

## 13.3 أمثلة

- \(\tau,\sigma,\varphi\): انحناء مختلط لوغاريتمي صفري.
- \(f(n)=n+1\): انحناء مختلط موجب.

---

# 14. الانحناء المحوري

\[
\boxed{
\kappa_p^f(n)
=
D_p^{+\,2}\log f(n)
=
\log\frac{f(np^2)f(n)}{f(np)^2}.
}
\]

- \(\tau\): سالب.
- \(\sigma\): سالب.
- \(\varphi\): صدمة عند دخول المحور، ثم صفر داخل الشعاع.
- \(\operatorname{rad}\): معلوماتها تتركز عند دخول المحور.

---

# 15. الصفحة التفاعلية المنشأة

تم إنشاء صفحة ويب محلية لحقول المتجهات على الوجه \(2\!-\!3\):

```text
FILE = pvg_vector_fields_face_2_3.html
```

تتضمن:

- \(\Omega,\log n,\tau,\sigma,\varphi,\operatorname{rad}\).
- الفرق الخام.
- المكسب اللوغاريتمي.
- الكفاءة لكل \(\log p\).
- الأسهم وخطوط الاتزان.
- المشتقة المختلطة.
- مسارًا جشعًا محليًا.

---

# 16. المتجهات: ما نوقش بالفعل ولا يعاد

تم بالفعل مناقشة وتثبيت:

- متجهات الأساس \(e_p\).
- التمثيل:
  \[
  \nu(n)=\sum_p\nu_p(n)e_p.
  \]
- الدعم وحجم الدعم.
- \(\Omega\) ككتلة \(L^1\).
- \(\log n\) كارتفاع موزون.
- الجمع:
  \[
  \nu(mn)=\nu(m)+\nu(n).
  \]
- الترتيب الجزئي والقسمة.
- \(\gcd\) كـ\(\min\).
- \(\operatorname{lcm}\) كـ\(\max\).
- المسافة الشبكية.
- التطبيع الشكلي.
- الشعاع البدائي والقوى الكاملة.
- الزوايا والجداء الداخلي.
- الانتقال داخل الوجه وإدخال محور جديد.
- تفكيك المتجه إلى طبقات:
  \[
  v=\sum_j\mathbf1_{\{p:v_p\ge j\}}.
  \]
- ملف الأبعاد وكثيرة حدود الطبقات.

هذه الموضوعات `CLOSED-AS-FOUNDATION`، ولا يعاد شرحها تلقائيًا.

---

# 17. أمثلة المستخدم الأخيرة — التفسير الصحيح

الأمثلة كانت من نوع:

\[
(1,0,\ldots,0,1),
\]

\[
(1,0,\ldots,0,2),
\]

\[
(0,\ldots,0,1,1).
\]

المستخدم صحح أن المقصود `0,1` كمركبتين، وليس العدد العشري `0.1`.

هذه الأمثلة ليست المطلوب النهائي؛ هي إشارات إلى الرغبة في دراسة أعمق للمتجهات.

لا يجوز العودة فقط إلى تفسير أنها:
- \(e_p+e_q\)،
- \(e_p+2e_q\)،
- \(e_q+e_r\)،
لأن هذا شرح تم بالفعل.

---

# 18. ما لم يُدرس بعمق بعد في متجهات PVG

هذا هو الباب الحقيقي التالي.

## 18.1 جبر العائلات المتجهية

ليس المتجه المفرد، بل مجموعات مثل:

\[
\{e_p+e_q:q\ne p\},
\]

\[
\{e_p+2e_q:q\ne p\},
\]

\[
\{e_q+e_r:q<r\}.
\]

الأسئلة:

- كيف تتوزع هذه العائلات؟
- ما رسوم التقاطع بينها؟
- ما مؤثرات الانتقال التي ترسل عائلة إلى أخرى؟
- ما المدارات تحت تبديل الأوليات؟

## 18.2 مدارات زمرة تبديلات المحاور

يجب فصل:

- الشكل غير المعلّم.
- هوية المحاور.

متجهان مثل:

\[
e_p+e_q,\qquad e_r+e_s
\]

في المدار الشكلي نفسه تحت تبديل المحاور، مع اختلاف كلفتهما الحسابية.

## 18.3 مؤثرات النقل بين المحاور

تعريف مؤثرات مثل:

\[
T_{p\to q}v=v-e_p+e_q
\]

عندما \(v_p>0\).

ودراسة:

- شروط التعريف.
- أثرها على \(\Omega,\log n,\tau\).
- عدم تبادلية مؤثرات النقل المقيدة.
- رسوم المدارات الناتجة.

## 18.4 متجهات الفروق بين الأعداد

\[
\delta(m,n)=\nu(n)-\nu(m)\in\mathbb Z^{(\mathcal P)}.
\]

هذه تعيش في فضاء النسب الموجبة، وتمثل:

\[
\frac nm.
\]

ينبغي دراسة:

- الجزء الموجب والسالب.
- المسارات الدنيا.
- النقل المتوازن.
- تحلل الفرق إلى عمليات حذف وإضافة.

## 18.5 المستوى الثابت لـ\(\Omega\)

المجموعة:

\[
\{v\ge0:\|v\|_1=N\}
\]

هي طبقة تركيبية مهمة.

على دعم منتهٍ حجم \(k\)، نقاطها تراكيب \(N\) إلى \(k\) أجزاء، وعددها:

\[
\binom{N+k-1}{k-1}.
\]

هذا هو المكان الطبيعي لدراسة أنماط باسكال التي لاحظها المستخدم سابقًا.

## 18.6 الرسوم البيانية لمتجهات المستوى

رؤوسها المتجهات ذات كتلة ثابتة، والحافة تمثل نقل وحدة:

\[
v\mapsto v-e_p+e_q.
\]

هذا رسم جديد مهم:

- يحفظ \(\Omega\).
- يغير الشكل.
- يربط بمسائل التحسين.
- قد يكون له لابلاسيان وطيف خاصان.

## 18.7 متجهات الوجوه ككائنات مستقلة

بدل تمثيل العدد نفسه، يمكن اعتبار:

\[
e_p+e_q
\]

متجه وجه أساسي.

ثم دراسة فضاء مولد بهذه المتجهات:

\[
\mathcal W_2=\operatorname{span}\{e_p+e_q:p<q\}.
\]

والعلاقات الخطية والتوافقية بينها.

## 18.8 مؤثر الحافة–المحور

تعريف مصفوفة وقوع تربط:

- المحاور \(p\).
- الوجوه \(\{p,q\}\).

هذا يقود إلى:
- فضاء السلاسل.
- مؤثرات الحدود.
- لابلاسيان هودج.
- فصل حركات المحاور عن حركات الوجوه.

هذا لم يُنجز بعد، وهو مرشح قوي جدًا للمتابعة.

---

# 19. السؤال البحثي التالي المعتمد

بدل إعادة أساسيات المتجهات، نبدأ من:

\[
\boxed{
\mathcal E_2
=
\{e_p+e_q:p<q\}
}
\]

بوصفها **مجموعة متجهات الوجوه الأساسية**.

ثم نبني:

1. مصفوفة الوقوع بين المحاور والوجوه.
2. فضاء السلاسل \(C_0,C_1,C_2\).
3. مؤثر الحدود.
4. لابلاسيان المحاور والوجوه.
5. طيف العلاقة بين الوجوه التي تشترك في محور.
6. تفسير أمثلة المستخدم كمسارات بين متجهات وجهية، لا كنقاط منفردة فقط.

هذا المسار جديد نسبيًا مقارنة بما نوقش، وهو أقرب إلى تعميق «متجهات PVG» فعلًا.

---

# 20. تصنيف الحالة

```text
ESTABLISHED
- PVG point/axis/face/cone representation
- gluing of 2-3, 2-5, 3-5 faces
- divisor box and face spectrum
- face matrix and inertia theorem
- shape space and balancing flow
- discrete derivative foundations
- logarithmic mixed curvature criterion for multiplicativity
- first divisor-function application and numerical diagnostics

CORRECTED
- face areas are not triangle side lengths
- D_p^2 tau = 0 in raw forward-difference form
- only gradient fields have zero curl; not all vector fields
- 0,1 in the user's vector was two coordinates, not decimal 0.1

REJECTED / INSUFFICIENT
- treating one scalar balance measure as complete
- R_sup continuous support criterion
- claiming current PVG solves ANT problems
- treating the Laplacian alone as sufficient
- re-explaining basic vector support/layers as if new

NEXT
- vector families, transport operators, fixed-mass layers
- incidence geometry of axes and face-vectors
- chain complexes / Hodge-type operators on PVG
```

---

# 21. بروتوكول متابعة مختصر

عند قول المستخدم «تابع» بعد هذا الملف:

1. لا نعود إلى تعريف المتجه.
2. لا نكرر الدعم والكتلة والطبقات.
3. نبدأ مباشرة بمصفوفة الوقوع:
   \[
   B_{p,\{q,r\}}
   \]
   بين المحاور ومتجهات الوجوه.
4. ندرس مثالًا منتهيًا على المحاور:
   \[
   2,3,5,7
   \]
   ثم نعمم.
5. كل نتيجة تصنف:
   - `IDENTITY`
   - `PROVED`
   - `INTERPRETATION`
   - `HYPOTHESIS`
   - `OPEN`

---

# 22. الخلاصة التشغيلية

الجلسة لم تعد في مرحلة:

\[
\text{ما هو متجه PVG؟}
\]

بل وصلت إلى:

\[
\boxed{
\text{كيف نبني جبرًا ومؤثرات على عائلات متجهات PVG؟}
}
\]

وأفضل كائن تالٍ هو:

\[
\boxed{
\text{رسم المحور–الوجه ومصفوفة وقوعه،}
}
\]

لأن ذلك يربط مباشرة:

- أمثلة المتجهات المتباعدة في الإحداثيات.
- الوجوه التي تشترك في محور.
- الانتقال بين الوجوه.
- لابلاسيان جديد غير لابلاسيان شبكة النقاط.
- وطيف قد يحمل معلومات عن بنية الدعم والعلاقات بين المحاور.
---

# 23. تحديث الأدبيات والتموضع البحثي — 2026-08-01

```text
UPDATE-STATUS        = LITERATURE-POSITIONING-RECORDED
CLASSIFICATION       = MIXED: CLASSICAL-SKELETON + POTENTIAL-PVG-LIFT
NOVELTY-CLAIM        = NOT-YET-ESTABLISHED
BIBLIOGRAPHY-GATE    = FORMAL SOURCE-BY-SOURCE REVIEW STILL REQUIRED
```

## 23.1 ما تبين أنه موجود في الأدبيات

العناصر التالية لها سوابق واضحة في نظرية التقسيمات والتوافقيات الجبرية:

1. شبكة يونغ على التقسيمات الصحيحة.
2. مؤثرات الصعود والهبوط بإضافة صندوق أو حذفه.
3. الـ Differential Posets وعلاقات من نوع:
   \[
   DU-UD=I.
   \]
4. المؤثرات الطيفية على فضاءات التقسيمات.
5. الدوال المتناظرة، ومجاميع القوى، وقواعد التقسيمات.
6. تفسير حاصل ضرب الدوال المتناظرة بمعاملات تركيبية.
7. استعمال أوزان المدارات وزمر التناظر الداخلية للتقسيمات.

بالتالي لا يجوز تقديم ما يلي بوصفه اكتشافًا جديدًا مستقلًا:

- كون أنماط متجهات التقييم تقسيمات صحيحة.
- رسم الانتقالات بين الأنماط.
- مؤثرات الإضافة والحذف المجردة.
- جبر الصعود والهبوط المجرد على شبكة يونغ.
- مجرد وجود طيف لمؤثرات على التقسيمات.

## 23.2 ما يختلف في مسار PVG

المسار الحالي لا يدرس التقسيم \(\lambda\) كرأس توافقـي مجرد فقط، بل يرفع كل رأس إلى ليف عددي:

\[
\mathcal F_\lambda
=
\{n\ge2:\lambda(n)=\lambda\}.
\]

ويزود كل ليف بكائنين تحليليين:

\[
\pi_\lambda(x)
=
\#\{n\le x:\lambda(n)=\lambda\},
\]

و:

\[
D_\lambda(s)
=
\sum_{n\in\mathcal F_\lambda}n^{-s}.
\]

ثم يربط الألياف بمؤثرات ناتجة من الضرب بالأوليات وقواها:

\[
P(rs)=\sum_p p^{-rs}.
\]

هذا الرفع هو موضع الإضافة المحتملة، لا شبكة يونغ نفسها.

## 23.3 الصياغة الصحيحة للبرنامج

لا يقدم المشروع نفسه على أنه:

```text
NEW THEORY OF YOUNG LATTICE
```

بل على أنه:

```text
YOUNG/PARTITION SKELETON
        +
PRIME-VALUATION NUMERICAL FIBERS
        +
DIRICHLET SERIES AND COUNTING FUNCTIONS
        +
PRIME-WEIGHTED TRANSITION OPERATORS
```

الصياغة المقترحة:

\[
\boxed{
\text{Prime-Valuation Fiber Calculus over a Partition Skeleton}
}
\]

أو:

\[
\boxed{
\text{Dirichlet Fiber Operators in Prime-Valuation Geometry}
}
\]

وهذه أسماء عمل مؤقتة، وليست عناوين نشر معتمدة.

## 23.4 الهيكل الرفعي

لدينا الإسقاط:

\[
\Lambda:
\mathrm{PVG}_{\mathbb N}
\to
\mathfrak P,
\qquad

u(n)\mapsto\lambda(n).
\]

وفوق كل رأس \(\lambda\) يوجد ليف لا نهائي:

\[
\mathcal F_\lambda.
\]

إذن البنية المقترحة:

\[
\boxed{
\mathrm{PVG}_{\mathbb N}
\overset{\Lambda}{\longrightarrow}
\mathfrak P
}
\]

هي تغطية عددية غير متجانسة؛ لأن عناصر الليف تحمل أوزانًا أولية:

\[
\log p.
\]

## 23.5 المولد التحليلي الشامل

\[
\boxed{
\mathcal Z(s;\mathbf y)
=
\prod_p
\left(
1+\sum_{a\ge1}y_a p^{-as}

ight).
}
\]

وتوسيعه:

\[
\boxed{
\mathcal Z(s;\mathbf y)
=
1+
\sum_{\lambda\in\mathfrak P}
D_\lambda(s)
\prod_{a\ge1}y_a^{m_a(\lambda)}.
}
\]

## 23.6 معادلات الانتقال بين الألياف

\[
\boxed{
P(rs)D_\lambda(s)
=
\bigl(m_r(\lambda)+1\bigr)
D_{\operatorname{sort}(\lambda,r)}(s)
+
\sum_{\substack{j\ge1 \ m_j(\lambda)>0}}
\bigl(m_{j+r}(\lambda)+1\bigr)
D_{R_{j\to j+r}\lambda}(s).
}
\]

والنسخة العددية:

\[
\boxed{
\sum_p
\pi_\lambda\left(\frac{x}{p^r}
ight)
=
\bigl(m_r(\lambda)+1\bigr)
\pi_{\operatorname{sort}(\lambda,r)}(x)
+
\sum_{\substack{j\ge1 \ m_j(\lambda)>0}}
\bigl(m_{j+r}(\lambda)+1\bigr)
\pi_{R_{j\to j+r}\lambda}(x).
}
\]

## 23.7 أمثلة انتقال أساسية

\[
P(s)^2
=
D_{(2)}(s)+2D_{(1,1)}(s).
\]

\[
P(s)D_{(1,1)}(s)
=
D_{(2,1)}(s)+3D_{(1,1,1)}(s).
\]

\[
P(s)D_{(2,1)}(s)
=
D_{(3,1)}(s)
+
2D_{(2,2)}(s)
+
2D_{(2,1,1)}(s).
\]

## 23.8 مصفوفات المستويات

\[
\mathbf D_N(s)
=
(D_\lambda(s))_{\lambda\vdash N}.
\]

وتوجد مصفوفة:

\[
L_{N+1}
\in
M_{p(N)\times p(N+1)}(\mathbb Z_{\ge0})
\]

تحقق:

\[
\boxed{
P(s)\mathbf D_N(s)
=
L_{N+1}\mathbf D_{N+1}(s).
}
\]

لكن لأن:

\[
p(N+1)>p(N),
\]

فلا تكفي هذه المعادلة وحدها لاستعادة المستوى الأعلى كاملًا.

## 23.9 مؤثرات الأنماط

\[
\mathcal B=y_1,
\qquad
\mathcal D=\partial_{y_1},
\]

\[
\mathcal R
=
\sum_{j\ge1}
y_{j+1}\partial_{y_j},
\]

\[
\mathcal L
=
\sum_{j\ge2}
y_{j-1}\partial_{y_j}.
\]

وتحقق:

\[
[\mathcal D,\mathcal B]=I,
\]

و:

\[
[\mathcal L,\mathcal R]
=
y_1\partial_{y_1}.
\]

هذه البنية تسجل كرفع PVG موزون، لا كمؤثرات تقسيمات جديدة في ذاتها.

## 23.10 الوزن الطبيعي والترافق

\[
\boxed{
w(\lambda)
=
\prod_{r\ge1}m_r(\lambda)!
}
\]

ومع:

\[
\langle f,g
angle_N
=
\sum_{\lambda\vdash N}
w(\lambda)
f(\lambda)\overline{g(\lambda)},
\]

نحصل على:

\[
\boxed{
L_{N+1}=U_N^*.
}
\]

ومن ثم:

\[
\boxed{
K_N=U_N^*U_N\ge0.
}
\]

## 23.11 حدود الادعاء بالجدة

```text
CLASSICAL
- partitions and Young diagrams
- Young lattice
- abstract up/down operators
- differential-poset framework
- symmetric-function algebra
- orbit/stabilizer multiplicities

PVG-SPECIFIC FORMULATION
- fiber F_lambda of integers with exact exponent pattern
- counting function pi_lambda(x)
- Dirichlet series D_lambda(s)
- prime-zeta weighted transitions between fibers
- arithmetic energy log p on lifted edges
- simultaneous fiber-counting and Dirichlet operator system

OPEN NOVELTY
- whether this full package exists already under another terminology
- whether the transition system yields new asymptotics or bounds
- whether the fiber spectrum captures prime distribution not visible in the skeleton
```

## 23.12 السؤال البحثي الأعلى

\[
\boxed{
\text{هل يضيف الرفع إلى الألياف الأولية وسلاسل ديريشليه معلومات تحليلية جديدة؟}
}
\]

وبصياغة أدق:

> هل يمكن بناء نظرية طيفية أو عودية للألياف \(\mathcal F_\lambda\)، تستخدم الأوزان الأولية \(p^{-s}\) أو \(\log p\)، وتنتج نتائج عن \(\pi_\lambda(x)\) أو \(D_\lambda(s)\) لا تختزل إلى جبر الدوال المتناظرة وحده؟

## 23.13 برنامج العمل القادم

```text
PHASE A — BIBLIOGRAPHY HARDENING
- formal bibliography for Young lattice, differential posets, up/down operators
- literature on integers with prescribed exponent pattern
- literature on prime-zeta and symmetric-function expansions
- literature on almost-prime counting by exact exponent type

PHASE B — FIBER CALCULUS
- formal definitions and domains
- prove all transition identities
- construct level matrices automatically
- verify weighted adjointness

PHASE C — ANALYTIC TEST
- compute normalized vectors D_N(s) for real s>1
- compare with spectral vectors of K_N
- study limits as s→1+ and s→∞
- identify what depends on prime weights and what is purely combinatorial

PHASE D — NOVELTY GATE
- no novelty claim unless an analytic theorem survives removal of the partition skeleton
```

# 24. نقطة المتابعة المعتمدة

\[
\boxed{
\text{تحليل المتجهات } \mathbf D_N(s)
\text{ على فضاء هيلبرت الموزون ومقارنتها بطيف }K_N.
}
\]

الاختبار الأول:

1. حساب \(D_\lambda(s)\) لجميع \(\lambda\vdash N\) حتى \(N=6\) أو \(8\).
2. تطبيع \(\mathbf D_N(s)\) بالمعيار الموزون.
3. إسقاطه على المتجهات الذاتية لـ\(K_N\).
4. دراسة \(s\to1^+\)، والقيم الوسطية، و\(s\to\infty\).
5. فصل ما يعتمد على الأوليات عما هو تركيبي محض.

# 25. الحالة المرجعية بعد التحديث

```text
CURRENT-STATE
= PARTITION SKELETON IDENTIFIED AS CLASSICAL
+ PVG FIBER LIFT FORMULATED
+ DIRICHLET/COUNTING TRANSITIONS DERIVED
+ WEIGHTED HILBERT STRUCTURE FOUND
+ NOVELTY NOT YET CLAIMED
+ ANALYTIC SPECTRAL TEST NEXT
```
