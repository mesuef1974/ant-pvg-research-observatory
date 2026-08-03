"""مصفوفة الوجوه مصفوفةُ DPR1، ومعادلتُها السرّية هي القياسية — بشرط.

الأرشيف يعطي لمصفوفة الوجوه المعادلة الطيفية

    1 = Σ_i a_i² / (λ + a_i²)،        x_i ∝ a_i / (λ + a_i²)

وهذه بالضبط المعادلة السرّية القياسية لمصفوفة **قطرية زائد رتبة واحدة**
(diagonal-plus-rank-one، DPR1): بوضع ``A = D + ρ z zᵀ`` عند ``D = −diag(a²)``
و``ρ = 1`` و``z = a``، تصير ``f(λ) = 1 + ρ Σ ζ_i²/(d_i − λ) = 0`` عينَ معادلة
الأرشيف.

**والشرط المفقود في الأرشيف**: أدبيات DPR1 تشترط عدمَ قابلية الاختزال، أي
``d_i ≠ d_j`` — وهنا **تمايزُ الأُسُس**. فإذا تكرّر أُسّ بتضاعف ``m`` صار
``−a²`` قيمةً ذاتية مباشرةً بتضاعف ``m−1``، وهي قطبٌ للمعادلة السرّية لا جذر،
فلا تحكمها المعادلة.

وهذا لا يمسّ ``PVG-FM-01`` (التوقيع) ولا ``PVG-FM-02`` (المحدد): كلتاهما تصحّ
مع التكرار، وقد فُحصتا في ``verify_face_matrix.py``.
"""

from __future__ import annotations

import random
import sys

import numpy as np


def face_matrix(a: np.ndarray) -> np.ndarray:
    return np.outer(a, a) - np.diag(a**2)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    # ١) أُسُس متمايزة: المعادلة السرّية تحكم كل قيمة ذاتية.
    random.seed(11)
    ok = total = 0
    for k in range(2, 8):
        for _ in range(60):
            a = np.array(random.sample(range(1, 12), k), dtype=float)
            for eigenvalue in np.linalg.eigvalsh(face_matrix(a)):
                total += 1
                ok += abs(np.sum(a**2 / (eigenvalue + a**2)) - 1.0) < 1e-7
    print(f"  أُسُس متمايزة: 1 = Σ a²/(λ+a²)        {ok}/{total}")

    # ٢) أُسُس مكرَّرة: −a² قيمة ذاتية بتضاعف ≥ m−1، خارج المعادلة السرّية.
    random.seed(5)
    ok_repeat = total_repeat = 0
    for _ in range(200):
        k = random.randint(3, 7)
        a = np.array([random.randint(1, 3) for _ in range(k)], dtype=float)
        eigenvalues = np.linalg.eigvalsh(face_matrix(a))
        for value in set(a.tolist()):
            multiplicity = int(np.sum(a == value))
            if multiplicity > 1:
                total_repeat += 1
                found = int(np.sum(np.abs(eigenvalues + value**2) < 1e-8))
                ok_repeat += found >= multiplicity - 1
    print(f"  أُسُس مكرَّرة: −a² ذاتية بتضاعف ≥ m−1   {ok_repeat}/{total_repeat}")

    return 0 if ok == total and ok_repeat == total_repeat else 1


if __name__ == "__main__":
    raise SystemExit(main())
