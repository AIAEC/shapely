import math
from itertools import count, takewhile
from math import isclose, cos, sin, radians
from typing import Union, Iterable

from shapely.affinity import rotate
from shapely.extension.constant import MATH_EPS, MATH_MIDDLE_EPS, ENOUGH_DISTANCE, MATH_LARGE_EPS
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.angle import Angle
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.angle_predicator_creator import AngleRangePredicator
from shapely.extension.typing import CoordType
from shapely.extension.util.func_util import sign, lfilter, lconcat
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points, unary_union


class Arc(LineString):
    """
    child type of Linestring that represent one segment of circle exterior
    """

    def __init__(self, center: Union[Point, CoordType] = (0, 0),
                 radius: float = 1,
                 start_angle: float = 0,
                 rotate_angle: float = 90,
                 angle_step: float = 16):
        """

        Parameters
        ----------
        center
        radius
        start_angle: in degree
        rotate_angle: positive for counter-clockwise, negative for clockwise
        angle_step: to control the resolution of the arc
        """
        self._center = Point(center)
        self._radius = float(radius)

        if self._radius <= 0:
            raise ValueError(f'radius should > 0, given {self._radius}')

        self._start_angle = Angle(start_angle)
        self._rotate_angle = float(rotate_angle)
        if abs(self._rotate_angle) > 360 + MATH_EPS:
            raise ValueError(f'rotate_angle should > 0, given {self._rotate_angle}')
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
            take_func = lambda _rotation: float(_rotation) <= rotate_angle
        else:
            take_func = lambda _rotation: float(_rotation) >= rotate_angle

        for rotation in takewhile(take_func, count(0, resolution)):
            yield start_angle + rotation
            last_angle = start_angle + rotation

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

    @classmethod
    def from_line(cls, linestring: LineString, fitting_angle_step: bool = False) -> 'Arc':
        """
        calculate the fitting arc from given linestring
        Parameters
        ----------
        linestring: linestring
        fitting_angle_step: whether fitting the angle_step of given linestring, if not use default angle_step of arc

        Returns
        -------
        arc instance
        """
        from shapely.extension.util.arc_parser import ArcParser
        parser = ArcParser(linestring)

        if fitting_angle_step:
            return parser.arc(parser.angle_step)

        return parser.arc()

    @property
    def rotate_angle(self) -> float:
        return self._rotate_angle

    @property
    def start_angle(self) -> float:
        return float(self._start_angle)

    @property
    def angle_step(self) -> float:
        return self._resolution

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
                   start_angle=float(self._start_angle + self._rotate_angle),
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
        # 计算弧真实起始角到所给角度所需要的旋转角, 如果该旋转角小于弧的旋转角, 则认为该角度在弧内部
        if self._rotate_angle > 0:
            start_angle = self._start_angle.degree
        else:
            start_angle = self._start_angle.degree + self._rotate_angle

        rotate_angle = (angle - start_angle) % 360

        return rotate_angle < abs(self._rotate_angle) + MATH_EPS

    def interpolate_by_angle(self, angle: Union[Angle, float]) -> Point:
        if not self.in_angle_range(angle):
            raise ValueError(f"{angle} is not in arc's angle range")

        return Point(self._center.x + self._radius * Angle(angle).cos(),
                     self._center.y + self._radius * Angle(angle).sin())

    @property
    def start_radius_line(self) -> LineString:
        """
        linestring from center to start point of the arc
        Returns
        -------
        linestring
        """
        return LineString([self.centroid, self.ext.start()])

    @property
    def end_radius_line(self) -> LineString:
        """
        linestring from center to end point of the arc
        Returns
        -------
        linestring
        """
        return LineString([self.centroid, self.ext.end()])

    def intersection(self, other):
        """
        重写求交方法
        :param other:
        :return:
        """
        if isinstance(other, Point):
            if self.is_point_on_arc(other):
                return other

        elif isinstance(other, Arc):
            return self._intersection_with_arc(other)

        elif isinstance(other, LineString):
            straight_segments = (other.ext.decompose(StraightSegment)
                                 .filter(lambda _line: _line.distance(self._center) < self._radius + MATH_MIDDLE_EPS)
                                 .to_list())
            return unary_union(
                [self._intersection_with_straight_segment_v2(straight) for straight in straight_segments])

        return super().intersection(other)

    def _intersection_with_arc(self, arc: 'Arc'):
        """
        弧和弧求交
        :param arc:
        :return:
        """
        if not isinstance(arc, Arc):
            raise ValueError(f'the given geom is not Arc, given {type(arc)}')
        dist = math.hypot(self._center.x - arc._center.x, self._center.y - arc._center.y)
        # 同心同半径弧求交
        if dist <= MATH_EPS:
            return self._intersection_with_concentric_arc(arc)
        if dist > self._radius + arc._radius + MATH_MIDDLE_EPS:
            return super().intersection(arc)
        x0, y0 = self._center.coords[0]
        x1, y1 = arc._center.coords[0]
        coefficient_x = 2 * (x1 - x0)
        coefficient_y = 2 * (y1 - y0)
        coefficient_c = (math.pow(x0, 2) - math.pow(x1, 2)
                         + math.pow(y0, 2) - math.pow(y1, 2)
                         - (math.pow(self._radius, 2) - math.pow(arc._radius, 2)))
        if math.isclose(coefficient_y, 0, abs_tol=MATH_EPS):
            result_x = -coefficient_c / coefficient_x
            d_value = math.pow(self._radius, 2) - math.pow(result_x - x0, 2)
            delta = math.sqrt(d_value) if d_value > MATH_MIDDLE_EPS else 0
            return unary_union(lfilter(lambda _point: self.is_point_on_arc(_point),
                                       [Point(result_x, y0 + delta), Point(result_x, y0 - delta)]))

        gradient = -coefficient_x / coefficient_y
        intercept = -coefficient_c / coefficient_y
        result = self._intersection_with_straight_line_by_gradient_and_intercept(gradient, intercept)
        if result is None:
            return super().intersection(arc)
        return unary_union(result)

    def _intersection_with_concentric_arc(self, arc: 'Arc'):
        if not isinstance(arc, Arc):
            raise ValueError(f'the given geom is not Arc, given {type(arc)}')

        if not math.isclose(self._radius, arc._radius, abs_tol=MATH_EPS):
            return unary_union([])

        result_arc = []
        is_ccw = self._rotate_angle > 0
        if is_ccw:
            self_start_angle = self._start_angle.degree
            self_end_angle = (self._start_angle + self._rotate_angle).degree
        else:
            self_start_angle = (self._start_angle + self._rotate_angle).degree
            self_end_angle = self._start_angle.degree

        if arc._rotate_angle > 0:
            other_start_angle = arc._start_angle.degree
            other_end_angle = (arc._start_angle + arc._rotate_angle).degree
        else:
            other_start_angle = (arc._start_angle + arc._rotate_angle).degree
            other_end_angle = arc._start_angle.degree

        rotate_and_start_angle_tuples = []

        if self.in_angle_range(other_start_angle):
            rotate_angle = (self_end_angle - other_start_angle) % 360
            if math.isclose(rotate_angle, 0, abs_tol=MATH_EPS):
                result_arc.append(arc.ext[0])
            else:
                rotate_and_start_angle_tuples.append((rotate_angle, other_start_angle))

        if self.in_angle_range(other_end_angle):
            rotate_angle = (other_end_angle - self_start_angle) % 360
            if math.isclose(rotate_angle, 0, abs_tol=MATH_EPS):
                result_arc.append(self.ext[0])
            else:
                rotate_and_start_angle_tuples.append((rotate_angle, self_start_angle))

        #  去重
        if (len(rotate_and_start_angle_tuples) == 2
                and math.isclose(rotate_and_start_angle_tuples[0][0],
                                 rotate_and_start_angle_tuples[1][0],
                                 abs_tol=MATH_EPS)
                and math.isclose(rotate_and_start_angle_tuples[0][1],
                                 rotate_and_start_angle_tuples[1][1],
                                 abs_tol=MATH_EPS)):
            rotate_and_start_angle_tuples = [rotate_and_start_angle_tuples[0]]

        for rotate_angle, start_angle in rotate_and_start_angle_tuples:
            if is_ccw:
                result_arc.append(Arc(center=self._center,
                                      radius=self._radius,
                                      start_angle=start_angle,
                                      rotate_angle=rotate_angle,
                                      angle_step=self.angle_step))
            else:
                result_arc.append(Arc(center=self._center,
                                      radius=self._radius,
                                      start_angle=start_angle + rotate_angle,
                                      rotate_angle=-rotate_angle,
                                      angle_step=self.angle_step))

        return unary_union(result_arc)

    def _intersection_with_straight_segment(self, line: StraightSegment):
        """
        计算弧和直线段的交点
        :param line:
        :return:
        """
        if not isinstance(line, StraightSegment):
            if len(line.coords) != 2:
                raise ValueError(f'line must be straight segment, given {type(line)}')
            line = StraightSegment(line.coords)

        if line.distance(self._center) > self._radius + MATH_MIDDLE_EPS:
            return super().intersection(line)

        x0, y0 = self._center.coords[0]
        x1, y1 = line.coords[0]
        x2, y2 = line.coords[-1]
        if math.isclose(line.ext.angle().degree, 90, abs_tol=MATH_EPS) or math.isclose(line.ext.angle().degree, 270,
                                                                                       abs_tol=MATH_EPS):
            d_value = math.pow(self._radius, 2) - math.pow(x1 - x0, 2)
            delta = math.sqrt(d_value) if d_value > MATH_MIDDLE_EPS else 0
            return unary_union(lfilter(lambda _point: self.is_point_on_arc(_point) and line.point_on_segment(_point),
                                       [Point(x1, y0 + delta), Point(x1, y0 - delta)]))

        gradient = (y1 - y2) / (x1 - x2)
        intercept = (y1 - gradient * x1 + y2 - gradient * x2) / 2
        result = self._intersection_with_straight_line_by_gradient_and_intercept(gradient, intercept)
        if result is None:
            return super().intersection(line)
        return unary_union(lfilter(line.point_on_segment, result))

    def _intersection_with_straight_segment_v2(self, line: StraightSegment):
        if not isinstance(line, StraightSegment):
            if len(line.coords) != 2:
                raise ValueError(f'line must be straight segment, given {type(line)}')
            line = StraightSegment(line.coords)
        prolong_line = line.ext.prolong().from_ends(ENOUGH_DISTANCE)
        dist = prolong_line.distance(self._center)
        if dist > self._radius + MATH_MIDDLE_EPS:
            return super().intersection(line)
        if dist < MATH_MIDDLE_EPS:
            start_point = Point(self._center.x + self._radius, self._center.y)
            line_angle = line.ext.angle().degree
            return unary_union(lfilter(line.point_on_segment, [rotate(start_point, line_angle, self._center),
                                                               rotate(start_point, 180 - line_angle, self._center)]))
        chord_midpoint = nearest_points(prolong_line, self._center)[0]
        d_value = math.pow(self._radius, 2) - math.pow(dist, 2)
        if d_value < MATH_MIDDLE_EPS:
            return chord_midpoint
        elif d_value > math.pow(self._radius, 2) - MATH_MIDDLE_EPS:
            move_dist = self._radius
        else:
            move_dist = math.sqrt(d_value)
        vector = Vector.from_endpoints_of(line).unit(move_dist)

        return unary_union(lfilter(lambda _point: self.is_point_on_arc(_point) and line.point_on_segment(_point),
                                   [vector.invert().apply(chord_midpoint), vector.apply(chord_midpoint)]))

    def _intersection_with_straight_line_by_gradient_and_intercept(self, gradient: float, intercept: float):
        """
        弧和已知斜率和截距的直线求交
        :param gradient:
        :param intercept:
        :return:
        """
        x0, y0 = self._center.coords[0]
        a = math.pow(gradient, 2) + 1
        b = 2 * gradient * (intercept - y0) - 2 * x0
        c = math.pow(x0, 2) + math.pow(y0 - intercept, 2) - math.pow(self._radius, 2)
        delta = math.pow(b, 2) - 4 * a * c
        # 降低误差
        delta = delta if delta / a > MATH_LARGE_EPS else 0
        if math.isclose(delta, 0, abs_tol=10 * MATH_MIDDLE_EPS):
            result_x = -b / (2 * a)
            result_y = gradient * result_x + intercept
            return lfilter(lambda _point: self.is_point_on_arc(_point), [Point(result_x, result_y)])

        elif delta > 0:
            result_x0 = (-b - math.sqrt(delta)) / (2 * a)
            result_x1 = (-b + math.sqrt(delta)) / (2 * a)
            result_y0 = gradient * result_x0 + intercept
            result_y1 = gradient * result_x1 + intercept
            return lfilter(lambda _point: self.is_point_on_arc(_point),
                           [Point(result_x0, result_y0), Point(result_x1, result_y1)])
        return None

    def is_point_on_arc(self, point: Point) -> bool:
        """
        判断点是否在弧上
        :param point:
        :return:
        """
        auxiliary_line = LineString([self._center, point])
        return (math.isclose(self._radius, auxiliary_line.length, abs_tol=MATH_MIDDLE_EPS)
                and self.in_angle_range(auxiliary_line.ext.angle()))

    def buffer(self,
               distance,
               resolution=16, quadsegs=None, cap_style=None, join_style=None, mitre_limit=5.0,
               single_sided=False):
        """
        重写buffer函数, 暂时只有distance和single_sided两个参数有效
        :param distance:
        :param resolution:
        :param quadsegs:
        :param cap_style:
        :param join_style:
        :param mitre_limit:
        :param single_sided:
        :return:
        """
        if math.isclose(distance, 0, abs_tol=MATH_EPS):
            return super().buffer(distance)

        new_polygon_coords_list = []
        new_arc_radius_list = ([self._radius + distance, self._radius] if single_sided else
                               [self._radius + distance, self._radius - distance])

        for new_radius in new_arc_radius_list:
            if new_radius < 0 + MATH_MIDDLE_EPS:
                new_polygon_coords_list.append([self.centroid.coords[0]])
                continue
            new_polygon_coords_list.append(Arc(center=self.centroid,
                                               radius=new_radius,
                                               start_angle=self.start_angle,
                                               rotate_angle=self.rotate_angle,
                                               angle_step=self.angle_step).coords)
        new_polygon_coords_list[1] = list(reversed(new_polygon_coords_list[1]))
        if self.rotate_angle > 360 - MATH_EPS:
            if new_arc_radius_list[0] < 0 + MATH_MIDDLE_EPS:
                return Polygon(new_polygon_coords_list[1])
            if new_arc_radius_list[1] < 0 + MATH_MIDDLE_EPS:
                return Polygon(new_polygon_coords_list[0])
            if new_arc_radius_list[0] > new_arc_radius_list[1]:
                return Polygon(new_polygon_coords_list[0], [new_polygon_coords_list[1]])
            return Polygon(new_polygon_coords_list[1], [new_polygon_coords_list[0]])
        return Polygon(lconcat(new_polygon_coords_list))
