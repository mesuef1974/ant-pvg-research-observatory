"""يتحقّق حاسوبيًا من اختزال مصفوفة الوجوه إلى تطابق واحد.

الادّعاء أن ``PVG-FM-01`` و``PVG-FM-02`` تتبعان من

    F = v vᵀ − diag(a_i²) = D_a (J − I) D_a,   D_a = diag(a_i)

فـ``J − I`` مصفوفةُ جوار الغراف التام، وقانون Sylvester يحفظ التوقيع.

والفحص هنا يؤكّد **الاختزال** لا يبرهن المبرهنتين ولا يغني عن الاستشهاد:
لا يحل الفحص محل البرهان، ولا محل المصدر.
"""

from __future__ import annotations

import random

import numpy as np


def face_matrix(a: list[int]) -> np.ndarray:
    v = np.array(a, dtype=float)
    return np.outer(v, v) - np.diag(v**2)


def main() -> int:
    random.seed(7)
    checks = {"التطابق": 0, "التوقيع": 0, "المحدد": 0}
    trials = 0
    for k in range(2, 8):
        for _ in range(60):
            a = [random.randint(1, 9) for _ in range(k)]
            F, Da, J = face_matrix(a), np.diag(a).astype(float), np.ones((k, k))

            checks["التطابق"] += np.allclose(F, Da @ (J - np.eye(k)) @ Da)

            ev = np.linalg.eigvalsh(F)
            inertia = (
                int((ev > 1e-8).sum()),
                int((ev < -1e-8).sum()),
                int((abs(ev) <= 1e-8).sum()),
            )
            checks["التوقيع"] += inertia == (1, k - 1, 0)

            claim = (-1) ** (k + 1) * (k - 1) * np.prod(np.array(a, float)) ** 2
            checks["المحدد"] += abs(np.linalg.det(F) - claim) <= 1e-6 * max(
                1.0, abs(claim)
            )
            trials += 1

    for label, passed in checks.items():
        print(f"  {label:10} {passed}/{trials}")
    return 0 if all(v == trials for v in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
