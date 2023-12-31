import unittest
import random
import torch
import numpy as np


class TestCase(unittest.TestCase):
    """Superclass for unit test cases in auto_LiRPA."""
    def __init__(self, methodName='runTest', seed=1, ref_path=None, generate=False):
        super().__init__(methodName)

        self.addTypeEqualityFunc(np.ndarray, 'assertArrayEqual')
        self.addTypeEqualityFunc(torch.Tensor, 'assertTensorEqual')

        self.set_seed(seed)
        self.ref_path = ref_path
        self.generate = generate

    def set_seed(self, seed):
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        random.seed(seed)
        np.random.seed(seed)

    def setUp(self):
        """Load the reference result if it exists."""
        if self.generate:
            self.reference = None
        else:
            self.reference = torch.load(self.ref_path) if self.ref_path else None

    def save(self):
        """Save result for future comparison."""
        print('Saving result to', self.ref_path)
        torch.save(self.result, self.ref_path)

    def check(self):
        """Save or check the results.

        This function can be called at the end of each test.
        If `self.generate == True`, save results for future comparison;
        otherwise, compare the current results `self.result` with the loaded
        reference `self.reference`. Results are expected to be a list or tuple
        of `torch.Tensor` instances.
        """
        if self.generate:
            self.save()
        else:
            for i in range(len(self.result)):
                self.assertEqual(self.result[i], self.reference[i])

    def assertArrayEqual(self, a, b, msg=None):
        self.assertIsInstance(a, np.ndarray, 'First argument is not an np.ndarray')
        self.assertIsInstance(b, np.ndarray, 'Second argument is not an np.ndarray')
        return np.allclose(a, b)

    def assertTensorEqual(self, a, b, msg=None):
        self.assertIsInstance(a, torch.Tensor, 'First argument is not an torch.Tensor')
        self.assertIsInstance(b, torch.Tensor, 'Second argument is not an torch.Tensor')
        return torch.allclose(a, b)
