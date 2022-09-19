from math import isclose
from operator import truth
from typing import Union, Tuple, Optional, Callable

from shapely.extension.model.angle import Angle
from shapely.extension.predicator.predicator import Predicator
from shapely.extension.typing import Num, CoordType
from shapely.extension.util.func_util import min_max
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry


class IncludingAnglePredicatorCreator:
    def __init__(self, angle: Union[Num, Angle]):
        self._angle = Angle(angle)

    def less_than(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)) < angle

        return Predicator(_func)

    def __lt__(self, angle: Union[float, Angle]):
        return self.less_than(angle)

    def less_equal(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)) <= angle

        return Predicator(_func)

    def __le__(self, angle: Union[float, Angle]):
        return self.less_equal(angle)

    def greater_than(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)) > angle

        return Predicator(_func)

    def __gt__(self, angle: Union[float, Angle]):
        return self.greater_than(angle)

    def greater_equal(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)) >= angle

        return Predicator(_func)

    def __ge__(self, angle: Union[float, Angle]):
        return self.greater_equal(angle)

    def equal(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)) == angle

        return Predicator(_func)

    def __eq__(self, angle: Union[float, Angle]):
        return self.equal(angle)

    def almost_equal(self, angle: Union[float, Angle]):
        def _func(geom: BaseGeometry, strategy: Optional = None):
            return self._angle.including_angle(geom.ext.angle(strategy)).almost_equal(angle)

        return Predicator(_func)


class AngleRangePredicator:
    def __init__(self, pivot_degree: Union[Num, Angle],
                 ccw_range: Num = 0,
                 cw_range: Num = 0,
                 origin: Union[Point, CoordType, str] = 'origin'):
        """
        init angle range predicator instance

        Parameters
        ----------
        pivot_degree: given the angle range center in degree format
        ccw_range: the upper bound will be pivot_degree + ccw_degree
        cw_range: the lower bound will be pivot_degree - cw_degree
        origin: the default origin, default value will be origin, meaning origin is (0, 0)
        """
        self._pivot_degree = Angle(pivot_degree)
        self._ccw_range = ccw_range
        self._cw_range = cw_range
        self._origin = Point(0, 0) if isinstance(origin, str) else Point(origin)

    def geom_angle_range(self, geometry: BaseGeometry,
                         origin: Optional[Union[Point, CoordType, str]] = None) -> Tuple['Angle', 'Angle']:
        """
        calculate the geometry's angle range, according to given origin. the angle range is base on angle range [0, 360]

        Parameters
        ----------
        geometry: geometry instance
        origin: str, Point or Coord. override the given default origin, if given str, it could only be 'origin',
        which set (0, 0) as its origin

        Returns
        -------
        tuple[Angle, Angle], each angle is based on angle range [0, 360]. Denote returning as (a, b),
        If a <= b, it's the case of range [a, b]. if a > b, it's the case of range [a, 360] || [0, b]
        """
        origin = origin or self._origin

        point_angles = filter(truth, [Angle.atan2(pt.y - origin.y, pt.x - origin.x)
                                      for pt in geometry.ext.decompose(Point).to_list()])

        # here min_angle and max_angle are in [0, 360]
        min_angle, max_angle = min_max(point_angles)
        if (max_angle - min_angle) > (min_angle - max_angle):
            # given geometry is in angle range [max_angle, 360] || [0, min_angle]
            return max_angle, min_angle

        # given geometry is in angle range [min_angle, max_angle]
        return min_angle, max_angle

    @property
    def conditional_angle_range(self) -> Tuple['Angle', 'Angle']:
        """
        Returns
        -------
        tuple[Angle, Angle], the conditional angle range, the predicator holds
        """
        return Angle(self._pivot_degree - self._cw_range), Angle(self._pivot_degree + self._ccw_range)

    def intersects(self) -> Callable[[BaseGeometry], bool]:
        """
        Returns
        -------
        predicator function that given geometry instance, return whether it is intersected with given angle range
        """

        def _intersects(geometry: BaseGeometry):
            _geom_angle_min, _geom_angle_max = self.geom_angle_range(geometry)
            given_angle_min, given_angle_max = self.conditional_angle_range
            return _geom_angle_min <= given_angle_max and _geom_angle_max >= given_angle_min

        return _intersects

    def touches(self, abs_tol: float = 1e-12) -> Callable[[BaseGeometry], bool]:
        """
        Parameters
        ----------
        abs_tol: absolute tolerance of touch

        Returns
        -------
        predicator function that given geometry instance, return whether it is touched with given angle range
        """

        def _touches(geometry: BaseGeometry):
            _geom_angle_min, _geom_angle_max = self.geom_angle_range(geometry)
            given_angle_min, given_angle_max = self.conditional_angle_range
            return (isclose(_geom_angle_min, given_angle_max, abs_tol=abs_tol)
                    or isclose(_geom_angle_max, given_angle_min, abs_tol=abs_tol))

        return _touches

    def contains(self) -> Callable[[BaseGeometry], bool]:
        """
        Returns
        -------
        predicator function that given geometry instance, return whether it is contained by given angle range
        """

        def _contains(geometry: BaseGeometry):
            _geom_angle_min, _geom_angle_max = self.geom_angle_range(geometry)
            given_angle_min, given_angle_max = self.conditional_angle_range
            return given_angle_min <= _geom_angle_min and _geom_angle_max <= given_angle_max

        return _contains

    def contains_angle(self) -> Callable[[Union[Num, Angle]], bool]:
        def _contains(angle: Union[Num, Angle]):
            given_angle_min, given_angle_max = self.conditional_angle_range
            return given_angle_min <= angle and angle <= given_angle_max

        return _contains


class AnglePredicatorCreator:
    def __init__(self, geom: BaseGeometry, strategy: Optional[Callable[[BaseGeometry], Num]] = None):
        self._geom = geom
        self._strategy = strategy

    def including_angle(self) -> IncludingAnglePredicatorCreator:
        return IncludingAnglePredicatorCreator(self._geom.ext.angle(self._strategy))

    def angle_range_relation(self, ccw_range: Union[Num, Angle] = 0,
                             cw_range: Union[Num, Angle] = 0,
                             origin: Union[Point, CoordType, str] = 'origin') -> AngleRangePredicator:
        pivot_angle = self._geom.ext.angle(self._strategy)
        return AngleRangePredicator(pivot_degree=pivot_angle,
                                    ccw_range=ccw_range,
                                    cw_range=cw_range,
                                    origin=origin)
