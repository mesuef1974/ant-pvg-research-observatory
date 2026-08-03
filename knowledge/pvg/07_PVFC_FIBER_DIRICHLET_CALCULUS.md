# حساب الألياف الأولية PVFC وسلاسل ديريشليه

```text
NAME   = Prime-Valuation Fiber Calculus over a Partition Skeleton
STATUS = ALGEBRAIC IDENTITIES PROVED; NOVELTY NOT ESTABLISHED
```

## 1. الرفع من الأشكال إلى الأعداد

لكل تقسيم \(\lambda\):

\[
\mathcal F_\lambda=\{n:\lambda(n)=\lambda\}.
\]

دالة العد:

\[
\pi_\lambda(x)=\#\{n\le x:n\in\mathcal F_\lambda\}.
\]

سلسلة ديريشليه:

\[
D_\lambda(s)=\sum_{n\in\mathcal F_\lambda}n^{-s}.
\]

## 2. المولد التحليلي الشامل

\[
\mathcal Z(s;\mathbf y)
=
\prod_p\left(1+\sum_{a\ge1}y_ap^{-as}\right).
\]

وبتوسيعه:

\[
\mathcal Z(s;\mathbf y)
=
1+\sum_{\lambda}D_\lambda(s)
\prod_{a\ge1}y_a^{m_a(\lambda)}.
\]

هذا يجمع كل الألياف في مولد واحد.

## 3. الصيغة الدقيقة بدلالة دالة زيتا الأوليات

ضع:

\[
P(s)=\sum_pp^{-s}.
\]

إذا \(\lambda=(\lambda_1,\ldots,\lambda_\ell)\)، فإن:

\[
D_\lambda(s)=
\frac1{\prod_rm_r(\lambda)!}
\sum_{\Pi\in\mathcal P([\ell])}
\prod_{B\in\Pi}
(-1)^{|B|-1}(|B|-1)!
P\left(s\sum_{i\in B}\lambda_i\right).
\]

هذه صيغة احتواء–استبعاد على تقسيمات مجموعة مواضع الأجزاء.

أمثلة:

\[
D_{(1)}=P(s),
\qquad
D_{(2)}=P(2s),
\]

\[
D_{(1,1)}=\frac{P(s)^2-P(2s)}2,
\]

\[
D_{(2,1)}=P(s)P(2s)-P(3s).
\]

## 4. قانون الانتقال العام

لـ\(r\ge1\):

\[
\boxed{
P(rs)D_\lambda(s)
=
(m_r(\lambda)+1)
D_{\operatorname{sort}(\lambda,r)}(s)
+
\sum_{j:m_j(\lambda)>0}
(m_{j+r}(\lambda)+1)
D_{R_{j\to j+r}\lambda}(s).
}
\]

المعنى:

- الحد الأول: ولادة جزء جديد حجمه \(r\).
- الحدود الأخرى: دمج/رفع جزء \(j\) إلى \(j+r\).

## 5. أمثلة أساسية

\[
P(s)^2=D_{(2)}+2D_{(1,1)}.
\]

\[
P(s)D_{(1,1)}=D_{(2,1)}+3D_{(1,1,1)}.
\]

\[
P(s)D_{(2,1)}
=
D_{(3,1)}+2D_{(2,2)}+2D_{(2,1,1)}.
\]

المعاملات ناتجة من مضاعفات الأجزاء المتساوية، وليست معاملات تجريبية.

## 6. النسخة العددية

\[
\sum_p\pi_\lambda(x/p^r)
=
(m_r+1)\pi_{\lambda\cup\{r\}}(x)
+
\sum_j(m_{j+r}+1)\pi_{R_{j\to j+r}\lambda}(x).
\]

هذه هوية عدّ دقيقة عند تفسير الطرف الأيسر بعدد الأزواج \((p,n)\) مع الوزن المناسب؛ لكنها ليست بعدُ صيغة تقاربية.

## 7. مصفوفات المستويات

\[
\mathbf D_N(s)=(D_\lambda(s))_{\lambda\vdash N}.
\]

توجد مصفوفة انتقال غير سالبة:

\[
P(s)\mathbf D_N(s)=L_{N+1}\mathbf D_{N+1}(s).
\]

لأن \(p(N+1)>p(N)\)، لا تكفي المعادلة المفردة لاسترجاع المستوى الأعلى كاملًا.

## 8. مؤثرات الأنماط الصورية

على كثيرات الحدود في \(y_j\):

\[
\mathcal B=y_1,
\qquad
\mathcal D=\partial_{y_1},
\]

\[
\mathcal R=\sum_{j\ge1}y_{j+1}\partial_{y_j},
\qquad
\mathcal L=\sum_{j\ge2}y_{j-1}\partial_{y_j}.
\]

وتحقق:

\[
[\mathcal D,\mathcal B]=I,
\qquad
[\mathcal L,\mathcal R]=y_1\partial_{y_1}.
\]

هذه مؤثرات تقسيمات كلاسيكية في جوهرها؛ محتوى PVFC هو تخصصها إلى الألياف وسلاسل ديريشليه.

## 9. الجداء الداخلي الموزون

\[
w(\lambda)=\prod_rm_r(\lambda)!.
\]

وعلى المستوى \(N\):

\[
\langle f,g\rangle_N
=
\sum_{\lambda\vdash N}w(\lambda)f(\lambda)\overline{g(\lambda)}.
\]

وجدنا:

\[
L_{N+1}=U_N^*,
\]

ومن ثم:

\[
K_N=U_N^*U_N\ge0.
\]

## 10. ما هو كلاسيكي وما هو خاص بالمشروع

`CLASSICAL`:

- الدوال المتناظرة والتقسيمات.
- تحويل القواعد بين الدوال الأحادية ومجاميع القوى.
- مؤثرات الصعود والهبوط.

`PVFC-SPECIFIC ORGANIZATION`:

- ربط كل رأس بليف من الأعداد.
- \(D_\lambda,\pi_\lambda\).
- تخصص مجاميع القوى إلى \(P(rs)\).
- نظام انتقال متزامن للألياف والعد.

`OPEN`:

- هل يعطي هذا النظام حدودًا جديدة لـ\(\pi_\lambda(x)\)؟
- هل يوجد ثابت/طيف يميز الأوزان الأولية عالميًا؟
