# جبر مؤثرات PVFC ووحدة الولادة–النفاثة

```text
DOMAIN = OPERATOR ALGEBRA
STATUS = ALGEBRAICALLY PROVED + CORRECTIONS RECORDED
```

## 1. أساس الأشكال

ليكن \(e_\mu\) متجه الأساس الموافق للتقسيم \(\mu\).

## 2. مؤثر الولادة

\[
B_a e_\mu
=
(m_a(\mu)+1)e_{\mu\cup\{a\}}.
\]

يضيف جزءًا جديدًا حجمه \(a\).

## 3. مؤثر الرفع/الدمج

\[
T_r e_\mu
=
\sum_{j:m_j(\mu)>0}
(m_{j+r}(\mu)+1)e_{R_{j\to j+r}\mu}.
\]

يختار جزءًا موجودًا \(j\) ويزيده بـ\(r\).

مؤثر الضرب بمجموع القوى:

\[
M_a=B_a+T_a.
\]

وبعد تخصص ديريشليه:

\[
M_a\mathbf D=P(as)\mathbf D.
\]

## 4. علاقات المبدلات

### مبرهنة الجبر — `PROVED`

\[
[B_a,B_r]=0,
\]

\[
[T_a,T_r]=0,
\]

\[
\boxed{[T_r,B_a]=B_{a+r}},
\]

ومن ثم:

\[
\boxed{[T_r,M_a]=B_{a+r}}.
\]

التفسير: كل المسارات تتطابق وتُلغى عدا المسار الذي يرفع الجزء المولود حديثًا \(a\) إلى \(a+r\).

الجبر بنية شبه مباشرة:

\[
\mathfrak b\rtimes\mathfrak t,
\]

حيث فضاء الولادات وفضاء الرفعات أبليان، و\(\operatorname{ad}(T_r)B_a=B_{a+r}\).

`FINITE-VERIFIED`: كل التقسيمات حتى \(\Omega=12\)، وكل \(1\le a,r\le4\).

## 5. الجبر التبادلي للولادات

\[
\mathscr B=\mathbb C[B_1,B_2,\ldots].
\]

نعرّف الاشتقاق:

\[
\delta_r(B_a)=B_{a+r}
\]

ويمتد بقاعدة لايبنتز. عندها:

\[
[T_r,F]=\delta_r(F)
\qquad\forall F\in\mathscr B.
\]

كما أن:

\[
[\delta_a,\delta_r]=0.
\]

## 6. لماذا فضاء النفاثات وحده غير مغلق

إذا:

\[
J^\infty\mathbf D
=
\operatorname{span}\{\mathbf D,\mathbf D',\ldots\},
\]

فإن:

\[
T_r\mathbf D=P(rs)\mathbf D-B_r\mathbf D.
\]

الحد \(B_r\mathbf D\) لا ينتمي عمومًا إلى فضاء النفاثات بمعاملات عددية. إذن النفاثات وحدها لا تكفي.

## 7. وحدة الولادة–النفاثة

\[
\boxed{
\mathscr M=\mathscr B\otimes J^\infty\mathbf D.
}
\]

العنصر النموذجي:

\[
F(B)\mathbf D^{(k)}.
\]

هذه الوحدة مغلقة تحت \(B_a,T_r,M_a,\partial_s\).

## 8. الصيغة على أساس المشتقات المقسومة

ضع:

\[
\mathbf E_k=\mathbf D^{(k)}/k!,
\qquad
N\mathbf E_k=\mathbf E_{k-1}.
\]

عندها:

\[
T_r=P(r(s+N))-B_r+\delta_r,
\]

\[
M_r=P(r(s+N))+\delta_r.
\]

على القطاع الخالي من الولادات \(F=1\):

\[
M_r=P(r(s+N)).
\]

## 9. تمثيل النفاثات

على نفاثة الرتبة \(m\):

\[
\mathcal J_m(M_a)
=
\sum_{q=0}^m\frac{a^qP^{(q)}(as)}{q!}N^q
=
P(a(s+N)).
\]

هذه مصفوفة Toeplitz مثلثية، وتبقى مؤثرات \(M_a\) متبادلة لأنها دوال في نفس المؤثر العديم القوى \(N\).

`CORRECTED`: الحد \(aP'(as)\) ليس مبدلًا محيطيًا \([\partial_s,M_a]\) إذا عُدّ \(M_a\) مؤثرًا مجردًا مستقلًا عن \(s\). إنه يظهر عند تفاضل معادلة المتجه الذاتي/في تمثيل النفاثة. يجب فصل المبدل التركيبي عن بيانات المشتقة التحليلية.

## 10. قانون الطبقتين

للطبقتين الأوليين من برج العد، يظهر مؤثر كتلي سفلي مثلثي. على قطاع الولادات الصحيح:

\[
\widehat K_a
=
\delta_aI_2+
\begin{pmatrix}
p_a&0\\
-q_a&p_a
\end{pmatrix},
\quad
p_a=P(a),\ q_a=aP'(a).
\]

ومصدر الانتقال:

\[
S_a=B_{a+1}I_2+q_aE,
\qquad
E=\begin{pmatrix}0&0\\1&0\end{pmatrix}.
\]

المؤثر الكامل:

\[
\widehat{\mathbb K}_a
=
\begin{pmatrix}
\widehat K_a&0\\
S_a&\widehat K_a
\end{pmatrix}.
\]

### شرط الكوسيكل — `PROVED`

\[
[\widehat K_a,S_b]=[\widehat K_b,S_a],
\]

وبالتالي:

\[
[\widehat{\mathbb K}_a,\widehat{\mathbb K}_b]=0.
\]

`CORRECTED`: المصفوفة القديمة من دون \(\delta_a\) لم تكن مغلقة بعد تكرار الانتقالات.

## 11. الطبقة الثالثة

الطبقة الثالثة تحتاج:

\[
P(a),\quad aP'(a),\quad\frac{a^2P''(a)}2,
\]

و:

\[
B_{a+1},\quad B_{a+2},\quad\delta_a,\quad\delta_1.
\]

لكنها لا تحتاج نوع مولد جديد؛ يكفي:

\[
\mathscr B\otimes\mathbb C[N]/(N^3).
\]

`OPEN`: استخراج كتل المصدر الدقيقة للطبقة الثالثة وإثبات كوسيكلها الكامل.
