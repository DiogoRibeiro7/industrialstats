import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from doe_python.designs.screening import PlackettBurmanDesign
from doe_python.designs.base import Factor


class TestPlackettBurmanDesign(unittest.TestCase):
    def test_generate_design(self):
        factors = [Factor('A', [1, -1]), Factor('B', [1, -1]), Factor('C', [1, -1])]
        design = PlackettBurmanDesign(factors, randomize=False)
        dm = design.generate_design()
        self.assertEqual(dm.shape, (8, 4))
        self.assertTrue({'A', 'B', 'C'}.issubset(dm.columns))
        # Check orthogonality
        mat = dm[['A','B','C']].to_numpy()
        prod = mat.T @ mat
        for i in range(prod.shape[0]):
            for j in range(prod.shape[1]):
                if i == j:
                    self.assertEqual(prod[i, j], 8)
                else:
                    self.assertEqual(prod[i, j], 0)


if __name__ == '__main__':
    unittest.main()
