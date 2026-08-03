"""يتحقّق من أن ``PVFC-01`` و``PVFC-02`` تخصيصان لواقعتين في الدوال المتناظرة.

الادّعاء المفحوص هنا:

1. ``PVFC-01``: صيغةُ الاحتواء–الاستبعاد على تقسيمات مواضع الأجزاء تساوي
   **الدالة الأحادية المتناظرة** \\(m_\\lambda\\) مقيَّمةً عند
   \\(x_p=p^{-s}\\). أي أن \\(D_\\lambda(s)=m_\\lambda(p^{-s})\\).

2. ``PVFC-02``: قانون الانتقال \\(P(rs)D_\\lambda\\) هو مفكوك الجداء
   \\(p_r\\cdot m_\\lambda\\) في الأساس الأحادي.

والفحص يؤكّد **التطابق** ولا يبرهنه ولا يغني عن الاستشهاد.
"""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from math import factorial


def set_partitions(items: list[int]):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for smaller in set_partitions(rest):
        for i in range(len(smaller)):
            yield smaller[:i] + [[first] + smaller[i]] + smaller[i + 1 :]
        yield [[first]] + smaller


def m_lambda(lam: tuple[int, ...], xs: list[float]) -> float:
    """‏\\(m_\\lambda\\): مجموع على المواضع المتمايزة، بلا تكرار."""
    total, seen = 0.0, set()
    for idx in itertools.permutations(range(len(xs)), len(lam)):
        key = tuple(sorted(zip(idx, lam, strict=True)))
        if key in seen:
            continue
        seen.add(key)
        term = 1.0
        for i, e in zip(idx, lam, strict=True):
            term *= xs[i] ** e
        total += term
    return total


def d_lambda_pvfc(lam: tuple[int, ...], xs: list[float]) -> float:
    """صيغة ``PVFC-01`` كما هي في الأرشيف."""
    pre = 1
    for m in Counter(lam).values():
        pre *= factorial(m)

    def power_sum(r: int) -> float:
        return sum(x**r for x in xs)

    total = 0.0
    for blocks in set_partitions(list(range(len(lam)))):
        term = 1.0
        for block in blocks:
            term *= (
                (-1) ** (len(block) - 1)
                * factorial(len(block) - 1)
                * power_sum(sum(lam[i] for i in block))
            )
        total += term
    return total / pre


def transition_rhs(lam: tuple[int, ...], r: int, xs: list[float]) -> float:
    """الطرف الأيمن من قانون ``PVFC-02``."""
    mult = Counter(lam)
    out = (mult[r] + 1) * m_lambda(tuple(sorted(lam + (r,), reverse=True)), xs)
    for j in sorted(set(lam)):
        rest = list(lam)
        rest.remove(j)
        rest.append(j + r)
        out += (mult[j + r] + 1) * m_lambda(tuple(sorted(rest, reverse=True)), xs)
    return out


SHAPES = ((1,), (2,), (1, 1), (2, 1), (1, 1, 1), (3, 1), (2, 2), (2, 1, 1), (3, 2, 1))
PRIMES = [2, 3, 5, 7, 11, 13, 17]


def main() -> int:
    # الطرفية على ويندوز قد تكون cp1256، ولا تسع الحروف اليونانية
    sys.stdout.reconfigure(encoding="utf-8")

    ok_d = tot_d = ok_t = tot_t = 0
    for s in (1.4, 2.0, 3.1):
        xs = [p ** (-s) for p in PRIMES]
        for lam in SHAPES:
            a, b = d_lambda_pvfc(lam, xs), m_lambda(lam, xs)
            ok_d += abs(a - b) <= 1e-11 * max(1.0, abs(b))
            tot_d += 1
            for r in (1, 2, 3):
                lhs = sum(x**r for x in xs) * m_lambda(lam, xs)
                rhs = transition_rhs(lam, r, xs)
                ok_t += abs(lhs - rhs) <= 1e-10 * max(1.0, abs(lhs))
                tot_t += 1

    print(f"  D_λ = m_λ عند x_p=p^-s        {ok_d}/{tot_d}")
    print(f"  P(rs)·D_λ = مفكوك p_r · m_λ    {ok_t}/{tot_t}")
    return 0 if ok_d == tot_d and ok_t == tot_t else 1


if __name__ == "__main__":
    raise SystemExit(main())
