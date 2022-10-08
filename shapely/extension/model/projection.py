from dataclasses import dataclass, field
from itertools import combinations
from typing import Union, List, Optional

from shapely.extension.constant import MATH_EPS, LARGE_ENOUGH_DISTANCE, ANGLE_AROUND_EPS
from shapely.extension.model.interval import Interval
from shapely.extension.model.vector import Vector
from shapely.extension.typing import Num
from shapely.extension.util.func_util import lfilter, min_max, lconcat
from shapely.geometry import LineString, Point, Polygon, MultiPolygon, MultiLineString, GeometryCollection, LinearRing
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry, JOIN_STYLE, CAP_STYLE
from shapely.ops import unary_union, substring


def rect_buffer(geom: BaseGeometry, dist: Num):
    return geom.buffer(float(dist), join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.flat)


def shadow(geom: BaseGeometry,
           direction: Vector,
           shadow_len: float) -> Union[Polygon, LineString, MultiPolygon, MultiLineString, GeometryCollection]:
    """
    计算geom按照direct指定的方向, 投影长度为shadow_len的投影

    :param geom: 任意几何图形
    :param direction: 投影方向的向量
    :param shadow_len: 投影长度
    :return:
    """

    def shadow_of_single_geom(single_geom: Union[Point, Polygon, LineString]) -> Union[LineString, Polygon]:
        from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy
        shadow_peak = direction.unit(shadow_len).apply(single_geom)

        if isinstance(single_geom, Point):
            return LineString([shadow_peak, single_geom])

        shadow_pieces: List[Polygon] = []
        decompose_strategy = StraightSegmentDecomposeStrategy()
        segments0 = single_geom.ext.decompose(LineString, strategy=decompose_strategy).to_list()
        segments1 = shadow_peak.ext.decompose(LineString, strategy=decompose_strategy).to_list()
        for seg0, seg1 in zip(segments0, segments1):
            shadow_pieces.append(unary_union([seg0, seg1]).convex_hull)

        return unary_union(shadow_pieces)

    return unary_union([shadow_of_single_geom(single_geom) for single_geom in geom.ext.flatten().to_list()])


@dataclass
class ProjectionOnRingLine:
    projector: BaseGeometry = field()
    target_line: LineString = field()

    def segments(self) -> List[LineString]:
        return [substring(self.target_line, float(interval.left), float(interval.right))
                for interval in self.positive_intervals()]

    def positive_intervals(self, normalized=False) -> List[Interval]:
        """
        目标线上被投影到的区间

        :param normalized: 是否按目标线的长度归一化
        """
        if self.target_line is None:
            raise TypeError('target_line has not been set, try calling onto method')

        if self.projector.is_empty:
            return []

        if isinstance(self.projector, BaseMultipartGeometry):
            return lconcat(
                [Projection(sub_geom).onto(self.target_line).positive_intervals() for sub_geom in self.projector.geoms])

        points = self.projector.ext.decompose(Point)
        return [Interval(*min_max([self.target_line.project(p, normalized=normalized) for p in points]))]

    def negative_intervals(self, normalized=False, eps: float = MATH_EPS) -> List[Interval]:
        """
        目标线上未被投影到的区间

        :param normalized: 是否按目标线的长度归一化
        :param eps: 最小误差, 生成的interval如果长度小于该误差则我们认为该interval是因为误差而生成, 故去除
        """
        overall_interval = Interval(0, 1 if normalized else self.target_line.length)
        return lfilter(lambda interval: interval.length > eps, overall_interval - self.positive_intervals(normalized))


@dataclass
class ProjectionOnLine:
    projector: BaseGeometry = field()
    target_line: LineString = field()
    direction: Vector = field()
    is_out_of_target: bool = field(default=False)

    @property
    def segments(self) -> List[LineString]:
        """
        目标直线段上的投影线段. 若is_out_of_target=True, 则投影线段可以落在目标直线段之外.
        """
        if self.target_line is None:
            raise TypeError('target_line has not been set, try calling onto method')

        if self.projector.is_empty:
            return []

        if isinstance(self.projector, BaseMultipartGeometry):
            return lconcat(
                [Projection(sub_geom).onto(target_line=self.target_line,
                                           direction=self.direction,
                                           is_out_of_target=self.is_out_of_target).segments
                 for sub_geom in self.projector.geoms])

        if isinstance(self.projector, Polygon):
            self.projector = self.projector.exterior

        target_pro_line = self.target_line.ext.prolong().from_ends(LARGE_ENOUGH_DISTANCE)

        # cal rays which cross coords of projector in direct
        cross_lines = [self.direction.ray(origin=coord) for coord in self.projector.coords]

        # TODO: maybe add a selection which is unidirectional or bidirectional extension
        cross_lines = [end_vertical.ext.prolong().from_head(LARGE_ENOUGH_DISTANCE)
                       for end_vertical in cross_lines]

        # 投影方向与目标直线平行时:
        # 1. 若cross_lines的凸包与target_line不相交, 则返回空list
        # 2. 否则, 可视为geom全部投影至target_line上, 返回[target_line]
        if self.direction.angle.including_angle(self.target_line.ext.angle()) < ANGLE_AROUND_EPS:
            return [self.target_line] if unary_union(cross_lines).convex_hull.intersects(self.target_line) else []

        # 投影方向与目标直线不平行时, cross_line必与target_pro_line相交
        projected_points = [cross_line.intersection(target_pro_line) for cross_line in cross_lines]

        if not projected_points:
            return []

        projected_seg = LineString(max(combinations(projected_points, 2),
                                       key=lambda pts: pts[0].distance(pts[1]),
                                       default=(projected_points[0], projected_points[0])))

        if self.is_out_of_target:
            return [projected_seg]

        if projected_seg.length == 0:
            projected_seg = Point(projected_seg.coords[0])
        else:
            projected_seg = rect_buffer(projected_seg, MATH_EPS)

        projected_seg = projected_seg.intersection(self.target_line)

        if isinstance(projected_seg, Point) and not projected_seg.is_empty:
            projected_seg = LineString([projected_seg, projected_seg])

        return [] if projected_seg.is_empty else [projected_seg]

    def positive_intervals(self, normalized: bool = False) -> List[Interval]:
        """
        目标线上被投影到的区间

        :param normalized: 是否按目标线的长度归一化
        """
        return [Interval(*min_max([self._location(Point(coord), normalized=normalized)
                                   for coord in projected_segment.coords]))
                for projected_segment in self.segments] or [Interval.empty()]

    def negative_intervals(self, normalized=False, eps: float = MATH_EPS) -> List[Interval]:
        """
        目标线上未被投影到的区间

        :param normalized: 是否按目标线的长度归一化
        :param eps: 最小误差, 生成的interval如果长度小于该误差则我们认为该interval是因为误差而生成, 故去除
        """
        overall_interval = Interval(0, 1 if normalized else self.target_line.length)
        return lfilter(lambda interval: interval.length >= eps,
                       overall_interval.minus(self.positive_intervals(normalized)))

    def _location(self, point: Point, normalized: bool = False) -> float:
        """
        点在目标线上的位置(距目标线起始点的距离). 点位于目标线正方向上时结果为正数, 位于负方向上时结果为负数.

        :param point: target_line上待确定位置的点
        :param normalized: 是否按目标线的长度归一化
        :return:
        """
        origin = Point(self.target_line.coords[0])
        target_ray = Vector.from_endpoints_of(self.target_line).ray(origin)
        dist = origin.distance(point)

        location = dist if rect_buffer(target_ray, MATH_EPS).covers(point) else -dist

        if normalized:
            location /= self.target_line.length

        return location


@dataclass
class ProjectionTowards:
    projector: BaseGeometry = field()
    target: BaseGeometry = field()
    direction: Vector = field()

    def shadow(self) -> Union[Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection]:
        dist_of_projector_and_target = self.projector.hausdorff_distance(self.target)

        shadow_of_projector = shadow(geom=self.projector,
                                     direction=self.direction,
                                     shadow_len=2 * dist_of_projector_and_target)
        reverse_shadow_of_target = shadow(geom=self.target,
                                          direction=self.direction.invert(),
                                          shadow_len=2 * dist_of_projector_and_target)

        raw_shadow = shadow_of_projector.intersection(reverse_shadow_of_target)

        shadows = (raw_shadow
                   .difference(rect_buffer(self.projector, MATH_EPS))
                   .difference(rect_buffer(self.target, MATH_EPS)).ext.flatten(
            target_class_or_callable=(LineString, Polygon)).to_list())
        valid_shadows = lfilter(lambda shadow: (shadow.distance(self.projector) < MATH_EPS * 2
                                                and shadow.distance(self.target) < MATH_EPS * 2), shadows)

        return unary_union(valid_shadows)


@dataclass
class Projection:
    """
    投影几何对象
    """

    def __init__(self, projector: BaseGeometry):
        self._projector = projector

    def onto(self, target_line: LineString,
             direction: Optional[Union[Vector, float]] = None,
             is_out_of_target: bool = False) -> ProjectionOnLine:
        """
        将几何图形按照直线法向量投影到目标直线上, 得到投影上去的intervals

        :param target_line: 需要投射到的目标直线段(非折线)
        :param direction: 投影方向. 参数类型为Vector或float： 若为None, 则取target_line法向量方向;
        若为float类型, 则所传方向必须为角度值(即单位为degree), 该角度值为与x轴正方向的逆时针夹角
        :param is_out_of_target: 是否投影在target_line之外
        :return:
        """
        if direction is None:
            direction = Vector.from_endpoints_of(target_line).ccw_perpendicular.unit()

        if not isinstance(direction, Vector):
            direction = Vector.from_angle(direction)

        return ProjectionOnLine(target_line=target_line,
                                projector=self._projector,
                                direction=direction,
                                is_out_of_target=is_out_of_target)

    def onto_ringline(self, target_line: Union[LineString, LinearRing]) -> ProjectionOnRingLine:
        """
        将几何图形按照直线法向量投影到目标直线上, 得到投影上去的intervals

        :param target_line: 需要投射到的目标线
        :return: self
        """
        return ProjectionOnRingLine(target_line=target_line, projector=self._projector)

    def towards(self, target: Polygon, direction: Vector) -> ProjectionTowards:
        """
        按照方向将几何图形投影到目标多边形上, 得到投影对象, 可从该对象获得一系列属性

        :param target: 目标多边形
        :param direction: 投影方向
        :return:
        """
        return ProjectionTowards(target=target, projector=self._projector, direction=direction)
