from itertools import count, takewhile
from math import isclose, cos, sin, radians
from typing import Union, Iterable

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.angle import Angle
from shapely.extension.predicator.angle_predicator_creator import AngleRangePredicator
from shapely.extension.typing import CoordType
from shapely.extension.util.func_util import sign
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


class Arc(LineString):
    """
    child type of Linestring that represent one segment of circle exterior
    """

    def __init__(self, center: Union[Point, CoordType],
                 radius: float = 1,
                 start_angle: float = 0,
                 rotate_angle: float = 90,
                 angle_step: float = 1):
        self._center = Point(center)
        self._radius = float(radius)

        if self._radius <= 0:
            raise ValueError(f'radius should > 0, given {self._radius}')

        self._start_angle = Angle(start_angle)
        self._rotate_angle = float(rotate_angle)
        self._resolution = angle_step
        coords = list(self._coord_iter(center_coord=self._center.coords[0],
                                       radius=radius,
                                       start_angle=start_angle,
                                       rotate_angle=self._rotate_angle,
                                       resolution=angle_step))
        super(Arc, self).__init__(coords)

    @classmethod
    def _angle_iter(cls, start_angle: float, rotate_angle: float, resolution: float) -> Iterable[float]:
        end_angle = start_angle + rotate_angle
        resolution = sign(float(rotate_angle) > 0) * resolution
        last_angle = None

        if resolution > 0:
            stop_func = lambda angle: float(angle) <= end_angle
        else:
            stop_func = lambda angle: float(angle) >= end_angle

        for angle in takewhile(stop_func, count(start_angle, resolution)):
            yield angle
            last_angle = angle

        if last_angle != float(end_angle):
            yield float(end_angle)

    @classmethod
    def _coord_iter(cls, center_coord: CoordType,
                    radius: float,
                    start_angle: float,
                    rotate_angle: float,
                    resolution: float) -> Iterable[CoordType]:
        return ((center_coord[0] + radius * cos(radians(a)), center_coord[1] + radius * sin(radians(a)))
                for a in cls._angle_iter(start_angle, rotate_angle, resolution))

    @classmethod
    def creator(cls):
        from shapely.extension.util.arc_creator import ArcCreator
        return ArcCreator

    @property
    def rotate_angle(self) -> float:
        return self._rotate_angle

    @property
    def start_angle(self) -> float:
        return float(self._start_angle)

    @property
    def end_angle(self) -> float:
        return float(self._start_angle) + self._rotate_angle

    @property
    def centroid(self) -> Point:
        return self._center

    @property
    def is_ccw(self) -> bool:
        return self._rotate_angle > 0

    @property
    def is_cw(self) -> bool:
        return self._rotate_angle < 0

    @property
    def angle(self) -> Angle:
        return Angle(self._rotate_angle)

    @property
    def radius(self) -> float:
        return self._radius

    @property
    def length(self) -> float:
        return radians(self._rotate_angle) * self._radius

    @property
    def is_minor_arc(self) -> bool:
        return self.angle < 180 - MATH_EPS

    @property
    def is_half_circle(self) -> bool:
        return isclose(self.angle, 180, abs_tol=MATH_EPS)

    @property
    def is_prior_arc(self) -> bool:
        return self.angle > 180 + MATH_EPS

    @property
    def complementary(self) -> "Arc":
        """互补的弧, 与原来的弧方向相同"""
        rotate_angle = float(self.angle.complementary())
        return Arc(center=self._center,
                   radius=self.radius,
                   start_angle=(self._start_angle + self._rotate_angle).degree,
                   rotate_angle=rotate_angle,
                   angle_step=self._resolution)

    @property
    def reverse(self) -> "Arc":
        return Arc(center=self._center,
                   radius=self.radius,
                   start_angle=self._start_angle + self._rotate_angle,
                   rotate_angle=-float(self._rotate_angle),
                   angle_step=self._resolution)

    def tangential(self, geom, dist_tol: float = MATH_EPS) -> bool:
        if not isclose(self._center.distance(geom), self._radius, abs_tol=dist_tol):
            return False

        ccw_range, cw_range = 0, 0
        if self._rotate_angle > 0:
            ccw_range = self._rotate_angle
        else:
            cw_range = abs(self._rotate_angle)

        angle_in_range_predicator = AngleRangePredicator(pivot_degree=self._start_angle,
                                                         ccw_range=ccw_range,
                                                         cw_range=cw_range).contains_angle()
        return angle_in_range_predicator(LineString(nearest_points(self._center, geom)).ext.angle())

    def tangent_point(self, geom, dist_tol: float = MATH_EPS) -> Point:
        if not self.tangential(geom, dist_tol):
            return Point()
        return self.interpolate_by_angle(LineString(nearest_points(self._center, geom)).ext.angle())

    def get_minor_arc(self) -> "Arc":
        return self if self.is_minor_arc else self.complementary

    def get_prior_arc(self) -> "Arc":
        return self if self.is_prior_arc else self.complementary

    def interpolate(self, distance, normalized=False) -> Point:
        distance = max(0, distance)

        if normalized:
            distance = distance * self.length

        center_coord = self._center.coords[0]
        angle = self._start_angle + distance / self._radius
        return Point(center_coord[0] + self._radius * angle.cos(), center_coord[1] + self._radius * angle.sin())

    def in_angle_range(self, angle: Union[Angle, float]) -> bool:
        end_angle = self._start_angle + self._rotate_angle
        if float(self._rotate_angle) > 0:
            return self._start_angle <= Angle(angle) <= end_angle

        return end_angle <= Angle(angle) <= self._start_angle

    def interpolate_by_angle(self, angle: Union[Angle, float]) -> Point:
        if not self.in_angle_range(angle):
            raise ValueError(f"{angle} is not in arc's angle range")

        return Point(self._center.x + self._radius * Angle(angle).cos(),
                     self._center.y + self._radius * Angle(angle).sin())
