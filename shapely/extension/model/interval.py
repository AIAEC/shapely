from collections.abc import Sequence
from functools import reduce
from math import isclose
from typing import List, Union, Tuple, Iterable

from shapely.extension.typing import Num
from shapely.extension.util.func_util import min_max


class Interval:
    """
    代表数学上区间的类,但需要注意的是Interval类的运算还不涉及到区间的开闭性
    """

    def __init__(self, left: float = 0.0, right: float = 0.0):
        self.left = left
        self.right = right

    def __bool__(self):
        return self.length > 0

    def __getitem__(self, index: int):
        if index == 0:
            return self.left
        return self.right

    def __iter__(self):
        return iter([self.left, self.right])

    def __lt__(self, other: 'Interval') -> bool:
        return tuple(self) < tuple(other)

    def __le__(self, other: 'Interval') -> bool:
        return tuple(self) <= tuple(other)

    def __gt__(self, other: 'Interval') -> bool:
        return tuple(self) > tuple(other)

    def __ge__(self, other: 'Interval') -> bool:
        return tuple(self) >= tuple(other)

    def __eq__(self, other: Union['Interval', Tuple[float, float]]) -> bool:
        if not isinstance(other, Interval):
            other = Interval.from_tuple(other)
        return self.left == other.left and self.right == other.right

    def __hash__(self):
        return hash(('interval', self.left, self.right))

    def __repr__(self):
        return f'interval({self.left},{self.right})'

    def almost_equal(self, other: Union['Interval', Tuple[float, float]], abs_tol: float) -> bool:
        """

        Parameters
        ----------
        other
        abs_tol

        Returns
        -------

        """
        if not isinstance(other, Interval):
            other = Interval.from_tuple(other)
        return (isclose(self.left, other.left, abs_tol=abs_tol)
                and isclose(self.right, other.right, abs_tol=abs_tol))

    @property
    def mid(self) -> float:
        """

        Returns
        -------

        """
        return (self.left + self.right) / 2

    @property
    def length(self) -> float:
        """
        Returns
        -------
        number type(int, Num)
        """
        return self.right - self.left

    def overlaps(self, interval_or_intervals: Union['Interval', List['Interval']]) -> bool:
        """

        Parameters
        ----------
        interval_or_intervals

        Returns
        -------

        """
        if not interval_or_intervals:
            return False

        intervals: List['Interval'] = (
            interval_or_intervals if isinstance(interval_or_intervals, (list, tuple)) else [interval_or_intervals])

        for interval in intervals:
            if not (self.right <= interval.left or interval.right <= self.left):
                return True

        return False

    @classmethod
    def empty(cls) -> 'Interval':
        """

        Returns
        -------

        """
        return Interval(0, 0)

    @classmethod
    def intersection_of(cls, intervals: Iterable['Interval']) -> 'Interval':
        """

        Parameters
        ----------
        intervals

        Returns
        -------

        """
        if not intervals:
            return cls.empty()

        intervals = list(intervals)

        if len(intervals) == 1:
            return intervals[0]

        return reduce(lambda interval, next_interval: interval.intersection(next_interval), intervals)

    def intersection(self, other: 'Interval') -> 'Interval':
        """

        Parameters
        ----------
        other

        Returns
        -------

        """
        if self.right < other.left or other.right < self.left:
            return self.empty()

        left = max(self.left, other.left)
        right = min(self.right, other.right)

        if left > right:
            return self.empty()

        return Interval(left, right)

    def __and__(self, other: 'Interval') -> 'Interval':
        return self.intersection(other)

    def buffer(self, dist: float) -> 'Interval':
        if not self:
            return self.empty()

        left = self.left - dist
        right = self.right + dist

        if left > right:
            return self.empty()
        return Interval(left, right)

    @classmethod
    def union_of(cls, intervals: Union['Interval', Sequence['Interval']]) -> List['Interval']:
        """

        Parameters
        ----------
        intervals

        Returns
        -------

        """
        if isinstance(intervals, Interval):
            intervals = [intervals]

        if not isinstance(intervals, Sequence):
            raise TypeError(f'expect list or tuple of interval, given {intervals}')

        sorted_intervals: List['Interval'] = sorted(intervals)
        prev_interval_idx: int = 0

        for interval in sorted_intervals:
            if interval.left <= sorted_intervals[prev_interval_idx].right:
                # if current interval get overlap with previous intervals, merge them
                sorted_intervals[prev_interval_idx].right = max(interval.right,
                                                                sorted_intervals[prev_interval_idx].right)

            else:
                prev_interval_idx += 1
                sorted_intervals[prev_interval_idx] = interval

        return sorted_intervals[:prev_interval_idx + 1]

    def __add__(self, other: Union['Interval', Sequence['Interval']]) -> List['Interval']:
        if isinstance(other, Interval):
            other = [other]

        return self.union_of([self, *other])

    def minus(self, interval_or_intervals: Union['Interval', Sequence['Interval']]) -> List['Interval']:
        """

        Parameters
        ----------
        interval_or_intervals

        Returns
        -------

        """
        if not interval_or_intervals:
            return [self]

        intervals = interval_or_intervals if isinstance(interval_or_intervals, Sequence) else [interval_or_intervals]
        intervals = self.union_of(intervals)

        if not self.overlaps(intervals):
            return [self]

        result_intervals: List['Interval'] = []
        last_interval = None
        for interval in intervals:
            if interval.left >= self.right:
                break

            if interval.right >= self.left:
                if last_interval is None and interval.left > self.left:
                    result_intervals.append(Interval(self.left, interval.left))

                if last_interval is not None:
                    result_intervals.append(Interval(last_interval.right, interval.left))

                last_interval = interval

        if last_interval is not None and last_interval.right < self.right:
            result_intervals.append(Interval(last_interval.right, self.right))

        return result_intervals

    def __sub__(self, other) -> List['Interval']:
        return self.minus(other)

    def __contains__(self, num_or_interval: Union[float, 'Interval']) -> bool:
        if isinstance(num_or_interval, Num):
            return self.left <= num_or_interval <= self.right
        if isinstance(num_or_interval, Interval):
            return self.left <= num_or_interval.left and num_or_interval.right <= self.right
        raise TypeError(
            f"num_or_interval should be of type (int, Num, 'Interval'), given {type(num_or_interval)}")

    @classmethod
    def from_tuple(cls, tuple_: Tuple[float, float]) -> 'Interval':
        """

        Parameters
        ----------
        tuple_

        Returns
        -------

        """
        return cls(*tuple_)

    @classmethod
    def from_nums(cls, nums: List[float]) -> 'Interval':
        """

        Parameters
        ----------
        nums

        Returns
        -------

        """
        return cls(*min_max(nums))
