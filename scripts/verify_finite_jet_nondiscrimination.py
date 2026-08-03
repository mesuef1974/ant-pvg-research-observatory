"""بناءٌ صريح للأبجدية التي تزعم ``PVFC-09`` وجودَها.

المبرهنة: ثبّت \\(s_0>1\\)، ومستوى \\(N\\)، ورتبة اشتقاق \\(m\\)، كلَّها منتهية.
لكل \\(\\varepsilon>0\\) توجد **أبجدية منتهية غير أولية** تقرّب جميع

    d^k/ds^k Σ_a a^{-rs}  عند s₀،   2 ≤ r ≤ N،  0 ≤ k ≤ m

الخاصةَ بالأوليات ضمن \\(\\varepsilon\\). فلا بصمة أولية محلية مستقرة ذات رتبة
محدودة داخل \\(s>1\\).

وبرهانُ الأرشيف من خطوتين، وهما خطوتا هذا البناء:

1. **قطع الذيل** — السلاسل متقاربة تقاربًا مطلقًا داخل \\(s>1\\)، فيكفي رأسٌ
   منتهٍ.
2. **إزاحة العناصر** — تُزاح الأوليات الباقية إزاحةً ضئيلة فتصير أعدادًا غير
   صحيحة، والمقادير مستمرة فتبقى ضمن \\(\\varepsilon\\).

**حدٌّ صادق**: عند \\(\\varepsilon\\) صغيرة جدًّا يتجاوز حدُّ القطع أكبرَ أوليّ
في القائمة المستعملة، فتصير المقارنة مع القائمة نفسها ويفقد الصفُّ معناه.
يُعلَن ذلك بدل إخفائه.

والفحص يُظهر البناء ولا يبرهن المبرهنة.
"""

from __future__ import annotations

import sys

import numpy as np
from sympy import primerange

S0, LEVEL, ORDER = 1.3, 6, 3
PRIME_LIMIT = 2_000_000


def moments(alphabet, s0: float, level: int, order: int) -> np.ndarray:
    values = np.asarray(alphabet, dtype=float)
    logs = np.log(values)
    return np.array(
        [
            [
                np.sum((-r * logs) ** k * values ** (-r * s0))
                for k in range(order + 1)
            ]
            for r in range(2, level + 1)
        ]
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    primes = list(primerange(2, PRIME_LIMIT))
    target = moments(primes, S0, LEVEL, ORDER)
    print(
        f"  الأوليات < {PRIME_LIMIT} ({len(primes)} عنصرًا)، "
        f"s₀={S0}، N={LEVEL}، m={ORDER}"
    )

    all_ok = True
    for epsilon in (1e-3, 1e-6, 1e-9):
        cutoff = 3
        while True:
            head = [p for p in primes if p <= cutoff]
            if head and np.max(np.abs(moments(head, S0, LEVEL, ORDER) - target)) < epsilon / 2:
                break
            cutoff *= 2

        degenerate = cutoff > primes[-1]

        rng = np.random.default_rng(0)
        shift = 1e-3
        while True:
            alphabet = [p * (1 + shift * (1 + rng.random())) for p in head]
            error = np.max(np.abs(moments(alphabet, S0, LEVEL, ORDER) - target))
            if error < epsilon:
                break
            shift /= 4

        non_integer = all(abs(x - round(x)) > 1e-12 for x in alphabet)
        all_ok &= non_integer and error < epsilon
        note = "  ← منحطّ: القطع تجاوز القائمة" if degenerate else ""
        print(
            f"  ε={epsilon:<7.0e} |A|={len(alphabet):<7} T={cutoff:<9} "
            f"إزاحة≈{shift:.1e}  خطأ={error:.2e}  غير صحيحة={non_integer}{note}"
        )

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
