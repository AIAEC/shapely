import warnings
from itertools import count, takewhile
from math import isclose, cos, sin, radians
from typing import Union, Optional, List, Iterable

from shapely.extension.constant import MATH_EPS, LARGE_ENOUGH_DISTANCE
from shapely.extension.model.angle import Angle
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType, Num
from shapely.extension.util.func_util import sign
from shapely.extension.util.prolong import prolong
from shapely.geometry import LineString, Point


class ArcCreator:
    warnings.warn('ArcCreator not tested!!')

    @classmethod
    def from_center_start_end(cls, center: Point,
                              start_point: Point,
                              end_point: Point,
                              radius: Optional[float] = None,
                              rotate_mode: str = "ccw",
                              radius_tol: float = MATH_EPS):
        if rotate_mode not in ["ccw", "cw"]:
            raise ValueError("rotate_mode必须为\"ccw\"或\"cw\"")
        vec1 = Vector.from_origin_to_target(center, start_point)
        vec2 = Vector.from_origin_to_target(center, end_point)
        if not isclose(vec1.length, vec2.length, abs_tol=radius_tol) and radius is None:
            return ValueError("半径不相等")

        radius = radius or vec1.length

        rotate_angle = vec1.angle.rotating_angle(vec2.angle, direct=rotate_mode)  # -360~360
        return Arc(center=center,
                   radius=radius,
                   start_angle=vec1.angle,
                   rotate_angle=rotate_angle)

    @classmethod
    def from_center_start_rotate_angle(cls, center_point: Point,
                                       start_point: Point,
                                       rotate_angle: float,
                                       radius: Optional[float] = None):
        """rotate_angle: 顺时针为正, 逆时针为负"""
        radius = radius or center_point.distance(start_point)
        start_angle = Vector.from_origin_to_target(center_point, start_point).angle
        return Arc(center=center_point,
                   radius=radius,
                   start_angle=start_angle,
                   rotate_angle=rotate_angle)

    @classmethod
    def from_two_lines(cls, line1: LineString,
                       line2: LineString, radius: float,
                       side1: str = "left",
                       side2: str = "left"):
        """分别从两条线给定的位置中创建相切的一条弧(只能是劣弧)"""

        if not line1.ext.is_straight() or not line2.ext.is_straight():
            raise ValueError("折线不能生成相切圆弧")
        if line1.ext.is_parallel_to(line2):
            raise ValueError("平行的两条线（包括共线）的无法确定圆心的具体位置")
        if side1 not in ["left", "right"] or side2 not in ["left", "right"]:
            raise ValueError("side1和side2必须是\"left\"或者\"right\"")

        offset_line1 = line1.parallel_offset(distance=radius, side=side1)
        offset_line2 = line2.parallel_offset(distance=radius, side=side2)
        extend_line1 = prolong(offset_line1, front_prolong_len=LARGE_ENOUGH_DISTANCE,
                               end_prolong_len=LARGE_ENOUGH_DISTANCE)
        extend_line2 = prolong(offset_line2, front_prolong_len=LARGE_ENOUGH_DISTANCE,
                               end_prolong_len=LARGE_ENOUGH_DISTANCE)
        intersect_pt: Point = extend_line1.intersection(extend_line2)
        if intersect_pt.is_empty:
            raise ValueError("无法生成相切圆")
        project_on_line1 = line1.ext.projected_point(intersect_pt)
        project_on_line2 = line2.ext.projected_point(intersect_pt)
        arc = cls.from_center_start_end(center=intersect_pt, start_point=project_on_line1, end_point=project_on_line2)
        return arc.get_minor_arc()

    @classmethod
    def from_line_circle(cls, line: LineString, circle: Union["Circle", "Arc"], arc_radius: float) -> List["Arc"]:
        """从一条线和一个圆生成若干段弧[0, 1, 2, 3, 4, 5, 6, 7, 8], 弧相切于线和圆, 存在无法生成的情况"""
        if not line.ext.is_straight():
            raise ValueError("不能为折线")
        if arc_radius <= 0:
            raise ValueError("圆弧半径不能为负数")

        line = prolong(line, front_prolong_len=LARGE_ENOUGH_DISTANCE, end_prolong_len=LARGE_ENOUGH_DISTANCE)
        parallel_lines = [line.parallel_offset(distance=arc_radius, side='left'),
                          line.parallel_offset(distance=arc_radius, side='right')]
        buffer_distances = [circle.radius + arc_radius, abs(circle.radius - arc_radius)] \
            if circle.radius != arc_radius else [circle.radius + arc_radius]

        arcs = []
        for parallel_line in parallel_lines:
            for buffer_radius in buffer_distances:
                arc_centers: List[Point] = (circle.centroid.buffer(buffer_radius).exterior
                                            .intersection(parallel_line)
                                            .ext.decompose(Point)
                                            .to_list())
                for arc_center in arc_centers:
                    arc_start: Point = line.interpolate(line.project(arc_center))
                    center_center_vec = Vector.from_origin_to_target(arc_center, Point(circle.center)).unit()
                    if buffer_radius < circle.radius and circle.radius > arc_radius:  # 圆弧在圆里面
                        arc_end: Point = center_center_vec.multiply(-arc_radius).apply(arc_center)
                    else:  # 圆弧在圆外面
                        arc_end: Point = center_center_vec.multiply(arc_radius).apply(arc_center)
                    arcs.append(
                        cls.from_center_start_end(center=arc_center, start_point=arc_start, end_point=arc_end))
        return arcs


class Arc(LineString):
    def __init__(self, center: Union[Point, CoordType],
                 radius: Num = 1,
                 start_angle: Num = 0,
                 rotate_angle: Num = 90,
                 resolution: Num = 16):
        self._center = Point(center)
        self._radius = float(radius)

        if self._radius <= 0:
            raise ValueError(f'radius should > 0, given {self._radius}')

        self._start_angle = Angle(start_angle)
        self._rotate_angle = float(rotate_angle)
        self._resolution = resolution
        coords = list(self._coord_iter(center_coord=self._center.coords[0],
                                       radius=radius,
                                       start_angle=start_angle,
                                       rotate_angle=self._rotate_angle,
                                       resolution=resolution))
        super(Arc, self).__init__(coords)

    @classmethod
    def _angle_iter(cls, start_angle: Num, rotate_angle: Num, resolution: Num) -> Iterable[float]:
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
                    radius: Num,
                    start_angle: Num,
                    rotate_angle: Num,
                    resolution: Num) -> Iterable[CoordType]:
        return ((center_coord[0] + radius * cos(radians(a)), center_coord[1] + radius * sin(radians(a)))
                for a in cls._angle_iter(start_angle, rotate_angle, resolution))

    @classmethod
    def creator(cls):
        return ArcCreator

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
                   resolution=self._resolution)

    @property
    def reverse(self) -> "Arc":
        return Arc(center=self._center,
                   radius=self.radius,
                   start_angle=self._start_angle + self._rotate_angle,
                   rotate_angle=-float(self._rotate_angle),
                   resolution=self._resolution)

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

    def in_angle_range(self, angle: Union[Angle, Num]) -> bool:
        end_angle = self._start_angle + self._rotate_angle
        if float(self._rotate_angle) > 0:
            return self._start_angle < Angle(angle) < end_angle

        return end_angle < Angle(angle) < self._start_angle

    def interpolate_by_angle(self, angle: Union[Angle, Num]) -> Point:
        if not self.in_angle_range(angle):
            raise ValueError(f"{angle} is not in arc's angle range")

        return Point(self._center.x + self._radius * Angle(angle).cos(),
                     self._center.y + self._radius * Angle(angle).sin())
