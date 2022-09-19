from unittest import TestCase

from shapely.extension.util.iter_util import win_slice, first


class IterUtilTest(TestCase):
    def test_win_slice(self):
        l = [1, 2, 3, 4]
        win = win_slice(l, win_size=2)
        self.assertEqual((1, 2), next(win))
        self.assertEqual((2, 3), next(win))
        self.assertEqual((3, 4), next(win))
        with self.assertRaises(StopIteration):
            next(win)

        win = win_slice(l, win_size=2, tail_cycling=True)
        self.assertEqual((1, 2), next(win))
        self.assertEqual((2, 3), next(win))
        self.assertEqual((3, 4), next(win))
        self.assertEqual((4, 1), next(win))

        win = win_slice(l, win_size=2, tail_cycling=False)
        self.assertEqual((1, 2), next(win))
        self.assertEqual((2, 3), next(win))
        self.assertEqual((3, 4), next(win))

        win = win_slice(l, win_size=3, head_cycling=True, tail_cycling=False)
        self.assertEqual((3, 4, 1), next(win))
        self.assertEqual((4, 1, 2), next(win))
        self.assertEqual((1, 2, 3), next(win))
        self.assertEqual((2, 3, 4), next(win))

        win = win_slice(l, win_size=3, head_cycling=True, tail_cycling=True)
        self.assertEqual((3, 4, 1), next(win))
        self.assertEqual((4, 1, 2), next(win))
        self.assertEqual((1, 2, 3), next(win))
        self.assertEqual((2, 3, 4), next(win))
        self.assertEqual((3, 4, 1), next(win))
        self.assertEqual((4, 1, 2), next(win))
        with self.assertRaises(StopIteration):
            next(win)

        win = win_slice(l, win_size=2, step=2)
        self.assertEqual((1, 2), next(win))
        self.assertEqual((3, 4), next(win))
        with self.assertRaises(StopIteration):
            next(win)

        win = win_slice(l, win_size=2, enumerated=True)
        self.assertEqual((0, (1, 2)), next(win))
        try:
            for i, (t0, t1) in win:
                pass
        except Exception as e:
            self.fail(str(e))

    def test_first(self):
        l = [1, 2, 3, 1]
        val = first(lambda n: n == 3, l)
        self.assertEqual(3, val)

        idx = first(lambda n: n == 3, l, return_idx=True)
        self.assertEqual(2, idx)

        idx = first(lambda n: n == 1, l, return_idx=True, reverse=True)
        self.assertEqual(3, idx)

        idx = first(lambda n: n == 1, l, return_idx=True)
        self.assertEqual(0, idx)

        self.assertIsNone(first(lambda n: n == 5, l, return_idx=True))
