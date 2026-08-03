"""يتحقّق حاسوبيًا من مضمون ``PVG-TAU-01``: تعظيم \\(\\tau\\) عند التوازن.

ثلاثة أشياء تُفحص استقصاءً تامًّا على مجالات صغيرة:

1. التغليب يُحفظ عند إضافة ثابت لكل مركّبة: \\(a\\succ b\\Rightarrow a+1\\succ b+1\\).
   (مُلخِّصٌ آلي زعم عكس ذلك أثناء المسح؛ الفحص يحسم.)
2. تقعّر Schur لـ\\(\\tau\\): \\(a\\succ b\\Rightarrow\\prod(a_i+1)\\le\\prod(b_i+1)\\).
3. الشكل الأمثل عند ثبات \\(\\omega=k\\) و\\(\\Omega=A\\) هو \\((q+1)^r q^{k-r}\\)
   حيث \\(A=kq+r\\).

والفحص يؤكّد الصياغة ولا يبرهن تقعّر Schur ولا يغني عن الاستشهاد:
لا يحل الفحص محل البرهان، ولا محل المصدر.
"""

from __future__ import annotations

import itertools
import sys
from math import prod


def majorizes(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    """‏\\(a\\succ b\\): المجموع نفسه، والمجاميع الجزئية للمرتَّب تنازليًا أكبر."""
    A, B = sorted(a, reverse=True), sorted(b, reverse=True)
    if sum(A) != sum(B):
        return False
    running = 0
    for x, y in zip(A, B, strict=True):
        running += x - y
        if running < 0:
            return False
    return True


def main() -> int:
    # الطرفية على ويندوز قد تكون cp1256، ولا تسع الحروف اليونانية
    sys.stdout.reconfigure(encoding="utf-8")

    shift_ok = schur_ok = pairs = 0
    for k in range(2, 6):
        for total in range(k, 16):
            parts = [
                p
                for p in itertools.product(range(total + 1), repeat=k)
                if sum(p) == total
            ]
            for a, b in itertools.combinations(parts, 2):
                if not majorizes(a, b):
                    continue
                pairs += 1
                shift_ok += majorizes(
                    tuple(x + 1 for x in a), tuple(x + 1 for x in b)
                )
                schur_ok += prod(x + 1 for x in a) <= prod(x + 1 for x in b)

    print(f"  أزواج مغلِّبة   {pairs}")
    print(f"  إزاحة التغليب  {shift_ok}/{pairs}")
    print(f"  تقعّر Schur    {schur_ok}/{pairs}")

    shape_ok = shapes = 0
    for k in range(2, 6):
        for A in range(k, 20):
            best = max(
                (
                    p
                    for p in itertools.product(range(1, A + 1), repeat=k)
                    if sum(p) == A
                ),
                key=lambda p: prod(x + 1 for x in p),
            )
            q, r = divmod(A, k)
            predicted = sorted([q + 1] * r + [q] * (k - r), reverse=True)
            shape_ok += sorted(best, reverse=True) == predicted
            shapes += 1
    print(f"  الشكل الأمثل   {shape_ok}/{shapes}")

    return 0 if shift_ok == schur_ok == pairs and shape_ok == shapes else 1


if __name__ == "__main__":
    raise SystemExit(main())
