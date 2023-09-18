from decimal import Decimal
from math import radians, sin, cos, tan, floor, ceil, isclose, asin, degrees, acos, atan, atan2, isnan
from operator import attrgetter
from typing import Union, Sequence, Tuple, Literal, List

from shapely.extension.constant import MATH_EPS
from shapely.extension.typing import Num
from shapely.extension.util.func_util import sign


class Angle:
    """
    The model that represent the concept of angle. This model is mainly used for angle calculation, modulo calculation,
    rotating_angle calculation and including_angle calculation
    """

    def __init__(self, angle_degree: Union[float, 'Angle'], range_: Tuple[float, float] = (0, 360)):
        """
        init angle instance

        Parameters
        ----------
        angle_degree: angle in degree format or Angle instance

        range_: Tuple[num, num], which means the output of angle.degree will be mod into this range. And the result
        includes both end. if we denote range_ as (lower, upper), then the output might include any angle between lower
        and upper inclusively.

        Notice: given range (lower, upper), when given angle can be divided exactly by upper, we return upper directly
        for calculation conveniency, otherwise we return value that mod into space [lower, upper]

        """
        self._assert_valid_angle(angle_degree)
        self._assert_valid_range(range_)

        if isinstance(angle_degree, Angle):
            self._angle_degree = angle_degree.degree
            self._range = angle_degree.mod
        else:
            self._angle_degree = angle_degree
            self._range = range_

    def __repr__(self):
        return f'{self.degree}%{self._range}'

    @classmethod
    def from_radian(cls, radian: float, range_: Tuple[float, float] = (0, 360)):
        return cls(angle_degree=degrees(radian), range_=range_)

    @staticmethod
    def _assert_valid_angle(angle_degree) -> None:
        if not isinstance(angle_degree, (Num, Angle)):
            raise TypeError(f'angle_degree should be a number or angle, given {angle_degree}')

    @staticmethod
    def _assert_valid_range(range_) -> None:
        if not (isinstance(range_, Sequence)
                and len(range_) == 2
                and all(isinstance(num, Num) for num in range_)
                and range_[0] < range_[1]):
            raise ValueError(f'expect [num0, num1] as range, and num0 < num1, given {range_}')

    def set_mod(self, range_: Tuple[float, float]) -> 'Angle':
        """
        set the angle degree mod range.

        Notice: range should be specified by angle in Degree format

        Parameters
        ----------
        range_: tuple[num, num], each number represent angle in degree format, first num must less than second num

        Returns
        -------
        self
        """
        self._assert_valid_range(range_)
        self._range = range_
        return self

    @property
    def degree(self) -> float:
        """
        angle in degree format modulo given range.

        Notice: given range (lower, upper), when angle can be divided exactly by upper, we return upper
        directly for calculation conveniency, otherwise we return value that mod into space [lower, upper]

        Returns
        -------
        float
        """
        degree_range = Decimal(self._range[1] - self._range[0])

        # denote angle_degree as angle, range as (lower, upper)
        # special case: for conveniency in angle or side predication case, sometimes we want to return upper directly.
        # we return upper directly, if angle == upper or angle != lower and angle mod range === upper.
        # here in order to handle the float precision limit(e.g. -1e-14 - 360 returns an integer), we use Decimal to
        # expand the precision digits
        if self._angle_degree == self._range[1]:
            # angle == upper case
            return self._range[1]

        if self._angle_degree != self._range[0]:
            mod = (Decimal(self._angle_degree) - Decimal(self._range[1])) / degree_range

            if float(mod).is_integer():
                # angle != lower and angle mode range == upper
                return self._range[1]

        # normal case: in most case, we calculate the value modulo
        # then modulo = (angle - lower) % (upper - lower) + lower, in which (upper - lower) is the mod range,
        # (angle - lower) move the origin angle to fit mod space (0, (upper - lower)), and + lower recover result
        # to [lower, upper].
        # no need to handle precision here. since above code has done that
        return (self._angle_degree - self._range[0]) % float(degree_range) + self._range[0]

    @property
    def radian(self) -> float:
        """
        the radian of angle degree
        Returns
        -------
        float
        """
        return radians(self.degree)

    @property
    def mod(self):
        """
        get the modulo space

        Returns
        -------
        tuple[num, num]. the modulo space
        """
        return tuple(self._range)

    @mod.setter
    def mod(self, range_: Tuple[float, float]):
        self.set_mod(range_)

    def sin(self) -> float:
        """
        same as math.sin(angle.radian)

        Returns
        -------
        float
        """
        return sin(self.radian)

    def cos(self) -> float:
        """
        same as math.cos(angle.radian)

        Returns
        -------
        float
        """
        return cos(self.radian)

    def tan(self) -> float:
        """
        same as math.tan(angle.radian)

        Returns
        -------
        float
        """
        return tan(self.radian)

    @classmethod
    def asin(cls, value: float) -> 'Angle':
        """
        shortcut for Angle(asin(value))
        Parameters
        ----------
        value

        Returns
        -------
        angle instance
        """
        return cls(degrees(asin(value)))

    @classmethod
    def acos(cls, value: float) -> 'Angle':
        """
        shortcut for Angle(acos(value))
        Parameters
        ----------
        value

        Returns
        -------
        angle instance
        """
        return cls(degrees(acos(value)))

    @classmethod
    def atan(cls, value: float) -> 'Angle':
        """
        shortcut for Angle(atan(value))
        Parameters
        ----------
        value

        Returns
        -------
        angle instance
        """
        return cls(degrees(atan(value)))

    @classmethod
    def atan2(cls, y: float, x: float) -> 'Angle':
        """
        shortcut for Angle(atan2(y, x))
        Parameters
        ----------
        y: num
        x: num

        Returns
        -------
        angle instance
        """
        if x == 0 and y == 0:
            return cls(float('nan'))
        return cls(degrees(atan2(y, x)))

    def __bool__(self) -> bool:
        return not isnan(self._angle_degree)

    def complementary(self) -> 'Angle':
        """
        the complementary angle within given modulo space

        Returns
        -------
        Angle instance
        """
        return Angle(self._range[1] - self.degree, range_=self._range)

    def rotating_angle(self, angle: Union['Angle', float], direct: Literal['ccw', 'cw'] = 'ccw') -> 'Angle':
        """
        calculate the angle that cost by current angle to the given angle

        Parameters
        ----------
        angle: angle or float
        direct: rotating in counter clockwise(ccw) direction or clockwise(cw) direction

        Returns
        -------
        Angle instance
        """
        other = Angle(float(angle), range_=self._range)
        is_ccw: bool = direct.strip().lower() == 'ccw'
        rotating_angle_degree = (other.degree - self.degree) if is_ccw else (self.degree - other.degree)
        return Angle(rotating_angle_degree, range_=self._range)

    def including_angle(self, angle: Union['Angle', float]) -> 'Angle':
        """
        calculate the including angle between current and given angle

        Parameters
        ----------
        angle: float or angle

        Returns
        -------
        Angle instance
        """
        ccw_including = self.rotating_angle(angle)
        cw_including = self.rotating_angle(angle, direct='cw')
        including = min(ccw_including, cw_including, key=attrgetter('degree'))
        return Angle(self._range[0], range_=self._range) if including == self._range[1] else including

    def parallel_to(self, angle: Union['Angle', float], angle_tol: float = MATH_EPS) -> bool:
        """
        whether current angle is parallel to given angle within given angle tolerance
        Parameters
        ----------
        angle: angle instance or float
        angle_tol: float

        Returns
        -------
        bool
        """
        including_angle = Angle(self.including_angle(angle).degree, range_=(0, 360)).degree
        return isclose(including_angle, 0, abs_tol=angle_tol) or isclose(including_angle, 180, abs_tol=angle_tol)

    def perpendicular_to(self, angle: Union['Angle', float], angle_tol: float = MATH_EPS) -> bool:
        """
        whether current angle is perpendicular to given angle within given angle tolerance
        Parameters
        ----------
        angle: angle instance or float
        angle_tol: float

        Returns
        -------
        bool
        """
        including_angle = Angle(self.including_angle(angle).degree, range_=(0, 360)).degree
        return isclose(including_angle, 90, abs_tol=angle_tol) or isclose(including_angle, 270, abs_tol=angle_tol)

    def __float__(self):
        return float(self._angle_degree)

    def __int__(self):
        return int(self._angle_degree)

    def __floor__(self):
        return floor(float(self))

    def __ceil__(self):
        return ceil(float(self))

    def __add__(self, other: Union['Angle', float]) -> 'Angle':
        return Angle(float(self) + float(other), range_=self._range)

    def __radd__(self, other: Union['Angle', float]) -> 'Angle':
        _range = other._range if isinstance(other, Angle) else self._range
        return Angle(float(other) + float(self), range_=_range)

    def __iadd__(self, other: Union['Angle', float]) -> 'Angle':
        self._angle_degree += float(other)
        return self

    def __sub__(self, other: Union['Angle', float]) -> 'Angle':
        return Angle(float(self) - float(other), range_=self._range)

    def __rsub__(self, other: Union['Angle', float]) -> 'Angle':
        _range = other._range if isinstance(other, Angle) else self._range
        return Angle(float(other) - float(self), range_=_range)

    def __isub__(self, other: Union['Angle', float]) -> 'Angle':
        self._angle_degree -= float(other)
        return self

    def __mul__(self, other: float) -> 'Angle':
        return Angle(self._angle_degree * other, range_=self._range)

    def __rmul__(self, other: float) -> 'Angle':
        return Angle(self._angle_degree * other, range_=self._range)

    def __imul__(self, other: float) -> 'Angle':
        self._angle_degree *= other
        return self

    def __truediv__(self, other):
        if other == 0:
            raise ValueError('Angle cannot divide by 0')
        return Angle(self._angle_degree / other, range_=self._range)

    def __mod__(self, range_: Union[float, Tuple[float, float]]) -> 'Angle':
        if isinstance(range_, Num):
            range_ = tuple(sorted([0, range_]))
        return Angle(self._angle_degree, range_=range_)

    def __imod__(self, range_: Union[float, Tuple[float, float]]) -> 'Angle':
        if isinstance(range_, Num):
            range_ = tuple(sorted([0, range_]))
        self._assert_valid_range(range_)
        self._range = range_
        return self

    def __getitem__(self, item_or_slice: Union[int, slice]) -> 'Angle':
        ends = [0, item_or_slice] if isinstance(item_or_slice, Num) else [item_or_slice.start, item_or_slice.stop]
        range_ = tuple(sorted(ends))[:2]
        return Angle(self._angle_degree, range_=range_)

    @staticmethod
    def _angle_degree_of_other(other: Union['Angle', float]) -> float:
        return other if isinstance(other, Num) else other.degree

    def __eq__(self, other: Union['Angle', float]) -> bool:
        other_angle = self._angle_degree_of_other(other)
        return other_angle == self.degree

    def __hash__(self):
        return hash(('angle', self._angle_degree, self._range))

    def almost_equal(self, other: Union['Angle', float], angle_tol: float) -> bool:
        """
        whether current angle is almost equal to given angle within given angle tolerance
        Parameters
        ----------
        other: angle instance or float
        angle_tol: float

        Returns
        -------
        bool
        """
        including_angle = self.including_angle(Angle(other, self._range))
        return abs(including_angle.degree) <= angle_tol

    def __lt__(self, other: Union['Angle', float]) -> bool:
        other_angle = self._angle_degree_of_other(other)
        return self.degree < other_angle

    def __le__(self, other: Union['Angle', float]) -> bool:
        other_angle = self._angle_degree_of_other(other)
        return self.degree <= other_angle

    def __gt__(self, other: Union['Angle', float]) -> bool:
        other_angle = self._angle_degree_of_other(other)
        return self.degree > other_angle

    def __ge__(self, other: Union['Angle', float]) -> bool:
        other_angle = self._angle_degree_of_other(other)
        return self.degree >= other_angle

    def __abs__(self):
        return abs(self.degree)

    @classmethod
    def average(cls, angles: List[Union['Angle', float]], range_: Tuple[float, float]) -> 'Angle':
        angles = [Angle(angle, range_=range_) for angle in angles]
        if not angles:
            return cls(angle_degree=0, range_=range_)

        benchmark_angle = angles[0]
        ccw_angle_diff = sum([benchmark_angle.rotating_angle(angle, direct='ccw').degree for angle in angles])
        cw_angle_diff = sum([benchmark_angle.rotating_angle(angle, direct='cw').degree for angle in angles])
        smallest_angle_diff = min(ccw_angle_diff, cw_angle_diff)
        rotate_ccw = (smallest_angle_diff == ccw_angle_diff)

        average_angle = benchmark_angle + sign(rotate_ccw) * Angle(smallest_angle_diff / len(angles), range_=range_)
        return average_angle
