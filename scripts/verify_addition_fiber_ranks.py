"""يتحقّق من صيغتَي الرتبة في ألياف الجمع: ``ADD-03`` و``ADD-04``.

مؤثر قناة الفرق على فضاء الأوزان \\(V_N=\\mathbb C^{N-1}\\):

    (D_{N,r} w)_d = Σ_{2a−N ≡ d (mod r)} w_a

والمزعوم ``rank D_{N,r} = min(N−1, r/gcd(2,r))``، وللمعايير المتعدّدة
``rank J_{N;r} = min(N−1, L/gcd(2,L))`` حيث ``L = lcm(r_i)``.

هذان المؤثران من بناء الأرشيف نفسه، فلا سابقة لهما في الأدبيات تُطلب: السؤال
ليس «هل هذا معروف» بل «هل هذا صحيح». والفحص يجيب عن الثاني وحده.
"""

from __future__ import annotations

import sys
from math import gcd, lcm

import numpy as np


def channel_matrix(n: int, r: int) -> np.ndarray:
    matrix = np.zeros((r, n - 1))
    for a in range(1, n):
        matrix[(2 * a - n) % r, a - 1] = 1.0
    return matrix


def joint_matrix(n: int, moduli: tuple[int, ...]) -> np.ndarray:
    """‏J يحفظ التوقيع **المتزامن**، لا الهوامش المنفصلة.

    الأرشيف يشدّد على الفرق: المؤثر المكدَّس M=(D_{r_1},…) يحفظ الهوامش وقد
    يفقد اقتران المعلومات بين المعايير، فلا يُساوى بـJ.
    """
    signatures: dict[tuple[int, ...], int] = {}
    for a in range(1, n):
        key = tuple((2 * a - n) % r for r in moduli)
        signatures.setdefault(key, len(signatures))
    matrix = np.zeros((len(signatures), n - 1))
    for a in range(1, n):
        matrix[signatures[tuple((2 * a - n) % r for r in moduli)], a - 1] = 1.0
    return matrix


MODULI_SETS = ((3, 5), (2, 3), (4, 6), (3, 7), (2, 5), (6, 10), (3, 4, 5))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    single_ok = single_total = 0
    for n in range(3, 26):
        for r in range(1, 20):
            rank = np.linalg.matrix_rank(channel_matrix(n, r))
            single_ok += rank == min(n - 1, r // gcd(2, r))
            single_total += 1

    joint_ok = joint_total = 0
    for n in range(3, 20):
        for moduli in MODULI_SETS:
            rank = np.linalg.matrix_rank(joint_matrix(n, moduli))
            modulus = lcm(*moduli)
            joint_ok += rank == min(n - 1, modulus // gcd(2, modulus))
            joint_total += 1

    print(f"  ADD-03  rank D = min(N−1, r/gcd(2,r))   {single_ok}/{single_total}")
    print(f"  ADD-04  rank J = min(N−1, L/gcd(2,L))   {joint_ok}/{joint_total}")
    return 0 if single_ok == single_total and joint_ok == joint_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
