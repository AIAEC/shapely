from unittest import TestCase

from shapely.extension.model.interval import Interval


class IntervalTest(TestCase):
    def test_union_empty_list(self):
        result = Interval.union_of([])
        self.assertListEqual([], result)

    def test_union_intervals(self):
        result = Interval.union_of([Interval(0, 1), Interval(2, 3), Interval(4, 5)])
        self.assertListEqual([Interval(0, 1), Interval(2, 3), Interval(4, 5)], result)

        result = Interval.union_of([Interval(0, 1), Interval(1, 2), Interval(2, 3)])
        self.assertListEqual([Interval(0, 3)], result)

        result = Interval.union_of([Interval(2, 3), Interval(0, 1), Interval(0.5, 1), Interval(2, 3)])
        self.assertListEqual([Interval(0, 1), Interval(2, 3)], result)

    def test_interval_minus(self):
        result = Interval(0, 10).minus([Interval(1, 2), Interval(3, 4)])
        self.assertListEqual([Interval(0, 1), Interval(2, 3), Interval(4, 10)], result)

        result = Interval(0, 10).minus([Interval(1, 5), Interval(2, 10)])
        self.assertListEqual([Interval(0, 1)], result)

        result = Interval(0, 10).minus([Interval(1, 9), Interval(0, 2), Interval(8, 10)])
        self.assertListEqual([], result)

        result = Interval(0, 5).minus([Interval(1, 9), Interval(0, 2), Interval(8, 10)])
        self.assertListEqual([], result)

        result = Interval(10, 20).minus([Interval(1, 9), Interval(0, 2), Interval(8, 10)])
        self.assertListEqual([Interval(10, 20)], result)

        result = Interval(-10, 0).minus([Interval(1, 9), Interval(0, 2), Interval(8, 10)])
        self.assertListEqual([Interval(-10, 0)], result)

        result = Interval(-10, 0).minus([Interval(1, 9), Interval(0, 2), Interval(8, 10), Interval(-2, 10)])
        self.assertListEqual([Interval(-10, -2)], result)

        result = Interval(left=0, right=13.222460699900509).minus(
            [Interval(left=5.062221778270723e-16, right=1.4717076893029434e-14),
             Interval(left=2.682451368214445e-16, right=13.222460699900509)])
        self.assertListEqual([Interval(0, 2.682451368214445e-16)], result)

    def test_intervals_intersection(self):
        # simple non-overlapping
        self.assertFalse(Interval(0, 1).overlaps(Interval(1.1, 2)))

        # simple overlapping
        self.assertTrue(Interval(0, 1).overlaps(Interval(0.999, 2)))

        # intervals in random order
        self.assertFalse(Interval(0, 1).overlaps(Interval(-1, 0)))

        # intervals contain one another
        self.assertTrue(Interval(0, 1).overlaps(Interval(-1, 3)))

        # intervals more than 3 and overlap
        self.assertTrue(Interval(0, 1).overlaps([Interval(0.5, 1.5), Interval(1.4, 2)]))

    def test_create_from_nums(self):
        nums = [0, 0, 0]
        interval = Interval.from_nums(nums)
        self.assertEqual(0, interval.left)
        self.assertEqual(0, interval.right)

        nums = list(range(10))
        interval = Interval.from_nums(nums)
        self.assertEqual(0, interval.left)
        self.assertEqual(9, interval.right)

    def test_contains(self):
        interval0 = Interval(0, 1)
        interval1 = Interval(0, 1.1)

        self.assertTrue(0 in interval1)
        self.assertTrue(int(2) not in interval1)
        self.assertTrue(1.2 not in interval1)
        self.assertTrue(0.1 in interval1)
        self.assertTrue(int(1) in interval1)
        self.assertTrue(interval0 in interval1)

    def test_get_with_index(self):
        interval = Interval(0, 1)
        self.assertEqual(0, interval[0])
        self.assertEqual(1, interval[1])

    def test_intersection_of(self):
        interval0 = Interval(0, 10)
        interval1 = Interval(2, 8)
        interval2 = Interval(3, 5)

        result = Interval.intersection_of([interval0, interval1, interval2])
        self.assertEqual(Interval(3, 5), result)

        interval3 = Interval(11, 20)
        result = Interval.intersection_of({interval0, interval1, interval3})
        self.assertEqual(Interval.empty(), result)


def test_buffer():
    interval = Interval(0, 10)

    assert interval.buffer(5).length == 5 * 2 + interval.length
    assert interval.buffer(-2).length == -2 * 2 + interval.length

    assert Interval(-5, 15) == interval.buffer(5)
    assert Interval(2, 8) == interval.buffer(-2)

    assert not (interval.buffer(-5))

    assert not Interval.empty().buffer(5)
    assert not Interval.empty().buffer(-2)


def test_move():
    interval = Interval(0, 10)
    assert Interval(5, 15) == interval.move(5)
    assert Interval(-5, 5) == interval.move(-5)
    assert Interval(5, 5) == Interval.empty().move(5)
