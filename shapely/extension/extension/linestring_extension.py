from collections.abc import Sequence
from copy import deepcopy
from itertools import product, combinations
from typing import Union, Tuple, Optional, Iterable, Callable, List, overload, Literal

from shapely.extension.constant import MATH_EPS, LARGE_ENOUGH_DISTANCE
from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.angle import Angle
from shapely.extension.model.coord import Coord
from shapely.extension.model.interval import Interval
from shapely.extension.model.projection import Projection, ProjectionOnLine
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.bypassing_strategy import BaseBypassingStrategy, ShorterBypassingStrategy
from shapely.extension.strategy.linemerge_strategy import MergeLineStrategy, native_linemerge
from shapely.extension.strategy.offset_strategy import BaseOffsetStrategy, OffsetStrategy
from shapely.extension.strategy.polygonize_strategy import (
    ShapelyPolygonizeStrategy, ConvexHullStrategy, MouldStrategy, ClosingEndPointsStrategy)
from shapely.extension.typing import CoordType, Num
from shapely.extension.util.func_util import min_max
from shapely.extension.util.iter_util import win_slice
from shapely.extension.util.line_extent import LineExtent
from shapely.extension.util.polygonize import Polygonize
from shapely.extension.util.prolong import Prolong
from shapely.geometry import Point, LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import substring, unary_union, nearest_points


class LineStringExtension(BaseGeomExtension):
    def __getitem__(self, item):
        """
        quick way to get substring or point or coordinate
        Parameters
        ----------
        item: int or slice

        Returns
        -------
        point or linestring
        """
        if isinstance(item, int):
            return Point(list(self._geom.coords)[item])
        elif isinstance(item, slice):
            return LineString(list(self._geom.coords).__getitem__(item))
        raise TypeError(f'{item} is not supported index')

    def substring(self, interval: Union[Tuple[float, float], Interval],
                  absolute: bool = True,
                  allow_circle: bool = False):
        """
        calculate the substring of current linestring
        Parameters
        ----------
        interval
        absolute
        allow_circle: allow to cross the starting point if true

        Returns
        -------
        LineString
        """

        def new_start_point_line(distance: float, absolute: bool = True) -> LineString:

            is_valid_line_length: bool = ((absolute and 0 - MATH_EPS < distance < self._geom.length + MATH_EPS) or
                                          (not absolute and (0 - MATH_EPS < distance < 1 - MATH_EPS)))

            if not self._geom.is_closed or not is_valid_line_length or self._geom.length < MATH_EPS:
                return self._geom

            new_start_coord: Coord = self._geom.interpolate(distance=distance, normalized=not absolute).coords[0]
            origin_coords = list(self._geom.coords)
            new_start_index = Coord.get_insertion_coord_index_in_list(new_start_coord, origin_coords, tail_cycling=True)
            sorted_coords = ([new_start_coord] +
                             origin_coords[new_start_index:] +
                             origin_coords[:new_start_index] +
                             [new_start_coord])
            return LineString(sorted_coords).simplify(0)

        if isinstance(interval, Sequence):
            interval = Interval(interval[0], interval[1])
        else:
            interval = deepcopy(interval)
        origin_line = self._geom
        if allow_circle and origin_line.is_closed and interval.left > interval.right:
            origin_line = new_start_point_line(interval.left, absolute)
            if absolute:
                interval.right = self._geom.length - interval.left + interval.right
            else:
                interval.right = 1 - interval.left + interval.right
            interval.left = 0
        return substring(origin_line,
                         start_dist=float(interval.left),
                         end_dist=float(interval.right),
                         normalized=not absolute)

    def segments(self) -> List[StraightSegment]:
        return self.decompose(target_class=StraightSegment).to_list()

    def reverse(self) -> LineString:
        """
        same linestring with inverted coordinates
        Returns
        -------
        linestring
        """
        return LineString(list(self._geom.coords)[::-1])

    def start(self) -> Point:
        """
        return the first point of current linestring
        Returns
        -------
        point
        """
        return Point(self._geom.coords[0])

    def end(self) -> Point:
        """
        return the last point of current linestring
        Returns
        -------
        point
        """
        return Point(list(self._geom.coords)[-1])

    def prolong(self, absolute: bool = True) -> Prolong:
        """
        enter the prolong mode of the current linestring
        Parameters
        ----------
        absolute: bool

        Returns
        -------
        Prolong instance
        """
        return Prolong(self._geom, absolute=absolute)

    def bypass(self, geom: BaseGeometry, strategy: Optional[BaseBypassingStrategy] = None) -> LineString:
        """
        return the bypassing linestring of the current linestring given geom as obstacles
        Parameters
        ----------
        geom:
        strategy: if None, use the default bypassing strategy ShorterBypassingStrategy

        Returns
        -------
        linestring
        """
        strategy = strategy or ShorterBypassingStrategy()
        return strategy.bypass(self._geom, geom)

    def offset(self, dist: float,
               towards: Union[str, BaseGeometry] = 'left',
               invert_coords: bool = False,
               strategy: Optional[BaseOffsetStrategy] = None) -> LineString:
        """
        return the linestring after offset
        Parameters
        ----------
        dist: float, offset distance
        towards: string or target geometry, for string, only 'left', 'right' available.
        invert_coords: whether invert the return linestring's coordinates
        strategy: instance of the BaseOffsetStrategy, if None, use the default strategy OffsetStrategy

        Returns
        -------
        linestring
        """
        strategy = strategy or OffsetStrategy()

        if isinstance(towards, BaseGeometry):
            angle_from_start_to_move_target_centroid = Vector.from_origin_to_target(self.start(),
                                                                                    towards.centroid).angle
            at_left = self.angle().rotating_angle(angle_from_start_to_move_target_centroid, 'ccw') < 180
            towards = 'left' if at_left else 'right'

        return strategy.offset(line=self._geom,
                               dist=float(dist),
                               side=towards,
                               invert_coords=invert_coords)

    def is_parallel_to(self, other: LineString,
                       angle_tol: float = MATH_EPS,
                       angle_strategy: Optional[Callable[[BaseGeometry], Angle]] = None) -> bool:
        """
        whether parallel to other linestring
        Parameters
        ----------
        other: linestring
        angle_tol:
        angle_strategy: if None, use the default angle strategy

        Returns
        -------
        bool
        """
        return self.angle(angle_strategy).parallel_to(other.ext.angle(angle_strategy), angle_tol=angle_tol)

    def is_perpendicular_to(self, other: LineString,
                            angle_tol: float = MATH_EPS,
                            angle_strategy: Optional[Callable[[BaseGeometry], Angle]] = None) -> bool:
        """
        whether perpendicular to other linestring

        Parameters
        ----------
        other: linestring
        angle_tol:
        angle_strategy: if None, use the default angle strategy

        Returns
        -------
        bool
        """
        return ((self.angle(angle_strategy) - other.ext.angle(angle_strategy)) % 180).almost_equal(90, angle_tol)

    def is_collinear_to(self, other: LineString,
                        angle_tol: float = MATH_EPS,
                        angle_strategy: Optional[Callable[[BaseGeometry], Angle]] = None) -> bool:
        """
        whether collinear to other linestring
        Parameters
        ----------
        other: linestring
        angle_tol:
        angle_strategy: if None, use the default angle strategy

        Returns
        -------
        bool
        """
        lines = [LineString([pt0, pt1])
                 for pt0, pt1 in product([self.start(), self.end()], [other.ext.start(), other.ext.end()])
                 if not pt0.equals(pt1)]
        return all(
            line0.ext.is_parallel_to(other=line1, angle_tol=angle_tol, angle_strategy=angle_strategy)
            for line0, line1 in combinations(lines, 2))

    def is_straight(self, angle_tol: float = MATH_EPS) -> bool:
        """
        whether the linestring is a straight line
        Parameters
        ----------
        angle_tol

        Returns
        -------
        bool
        """
        min_angle, max_angle = min_max(
            [Coord.angle(*coord_tuple) for coord_tuple in win_slice(self._geom.coords, win_size=2)])
        return min_angle.including_angle(max_angle) <= angle_tol

    def extend_to_merge(self, line: LineString, extent_dist: float = LARGE_ENOUGH_DISTANCE) -> Optional[LineString]:
        """
        prolong current linestring and given linestring, and return merged linestring or None if they don't intersect
        Parameters
        ----------
        line: other linestring
        extent_dist: prolong distance of the current linestring and other linestring at most

        Returns
        -------
        linestring or None
        """
        if line_extent := LineExtent.of_sequence_curves(self._geom, line, float(extent_dist)):
            return line_extent.merged_curve

        if line_extent := LineExtent.of_sequence_curves(self._geom, line.ext.reverse(), float(extent_dist)):
            return line_extent.merged_curve

        return None

    def projection_by(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                      direction: Optional[Vector] = None,
                      out_of_geom: bool = False) -> ProjectionOnLine:
        """
        return the projection on current linestring
        Parameters
        ----------
        geom_or_geoms
        direction
        out_of_geom

        Returns
        -------
        instance of ProjectionOnLine
        """
        return Projection(unary_union(geom_or_geoms)).onto(self._geom, direction, out_of_geom)

    def projected_point(self, point_or_coord: Union[Point, CoordType], on_extension: bool = True) -> Point:
        """
        return the projected point of point_or_coord onto the current linestring or its extension line
        Parameters
        ----------
        point_or_coord: Point | Coord | tuple[num, num]
        on_extension: bool, whether return point that is on the extension segment of current linestring, default to True

        Returns
        -------
        point
        """

        def project_on_straight_line(line, point: Union[Point, CoordType]) -> Point:
            if point.equals(self.start()) or point.equals(self.end()):
                return point
            vec_start_to_pt = Vector.from_origin_to_target(self.start(), point)
            vec_line = Vector.from_endpoints_of(line)
            including_angle_cos = vec_start_to_pt.angle.including_angle(vec_line.angle).cos()
            return vec_line.unit(including_angle_cos * vec_start_to_pt.length).apply(self.start())

        def native_project(line, point: Union[Point, CoordType]) -> Point:
            return line.interpolate(line.project(Point(point)))

        if not on_extension:
            return native_project(self._geom, point_or_coord)

        if isinstance(self._geom, StraightSegment):  # speed up
            return project_on_straight_line(self._geom, point_or_coord)

        native_projected_pt = native_project(self._geom, point_or_coord)
        projected_pt_at_start = project_on_straight_line(self[:2], point_or_coord)
        projected_pt_at_end = project_on_straight_line(self[-2:], point_or_coord)

        given_point = Point(point_or_coord)
        return min([native_projected_pt,
                    projected_pt_at_start,
                    projected_pt_at_end], key=lambda pt: given_point.distance(pt))

    def perpendicular_line(self, point: Point,
                           length: float,
                           position: Literal['mid', 'left', 'right'] = 'mid') -> LineString:
        """
        project the given point onto the current linestring and return the perpendicular linestring(normal line)
        of the projected point
        Parameters
        ----------
        point: point
        length:
        position: mid | left | right

        Returns
        -------
        linestring
        """
        point_on_line = self.projected_point(point)
        project = self._geom.project(point)
        vector = Vector.from_origin_to_target(self._geom.ext.interpolate(project - MATH_EPS),
                                              self._geom.ext.interpolate(project + MATH_EPS))
        perpendicular_vec_ccw = vector.ccw_perpendicular
        perpendicular_vec_cw = vector.cw_perpendicular
        if position == 'mid':
            pt0 = perpendicular_vec_ccw.unit(length / 2).apply(point_on_line)
            pt1 = perpendicular_vec_cw.unit(length / 2).apply(point_on_line)
        elif position == 'left':
            pt0 = perpendicular_vec_ccw.unit(length).apply(point_on_line)
            pt1 = point_on_line
        else:
            pt0 = point_on_line
            pt1 = perpendicular_vec_cw.unit(length).apply(point_on_line)
        return LineString([pt0, pt1])

    def tangent_line(self, point: Point,
                     length: float,
                     position: Literal['mid', 'forward', 'backward'] = 'mid') -> LineString:
        """
        project the given point onto the current linestring and return the tangent linestring of the projected point
        Parameters
        ----------
        point:
        length:
        position: mid | forward | backward

        Returns
        -------
        linestring
        """
        point_on_line = self.projected_point(point)
        project = self._geom.project(point)
        vector = Vector.from_origin_to_target(self._geom.interpolate(project - MATH_EPS),
                                              self._geom.interpolate(project + MATH_EPS))
        if position == 'mid':
            start_point = vector.invert().unit(length / 2).apply(point_on_line)
        elif position == 'backward':
            start_point = vector.invert().unit(length).apply(point_on_line)
        else:
            start_point = point_on_line

        return vector.ray(start_point, length)

    def perpendicular_distance(self, geom: BaseGeometry) -> float:
        """
        Parameters
        ----------
        geom: Any geometry object

        Returns
        -------
        distance in direction of normal vector of current line to the given geom. if geom is empty, return 0
        """
        if not isinstance(geom, BaseGeometry):
            raise TypeError(f'expect given geom is an instance of BaseGeometry, given {geom}')
        if geom.is_empty:
            return 0
        return Vector.from_origin_to_target(*nearest_points(self._geom, geom)).sub_vector(self.normal_vector()).length

    @overload
    def interpolate(self, distance: Num, absolute: bool = True) -> Point:
        ...

    @overload
    def interpolate(self, distance: Iterable, absolute: bool = True) -> List[Point]:
        ...

    def interpolate(self, distance: Union[Num, Iterable], absolute: bool = True) -> Union[Point, List[Point]]:
        """
        Parameters
        ----------
        distance: number or iterator of numbers
        absolute: bool

        Returns
        -------
        point(s) of given interpolates distance(s)
        """
        result: List[Point] = []
        distances = []

        if isinstance(distance, (float, int)):
            distances.append(distance)
        elif isinstance(distance, Iterable):
            distances = distance
        else:
            raise TypeError(f'{distance} type is not supported')

        for dist in distances:
            if not isinstance(dist, (float, int)):
                raise TypeError(f'distance contains invalid type')

            dist = float(dist)
            if not absolute:
                dist = dist * self._geom.length

            if dist < 0:
                point = self.prolong(absolute=True).from_head(abs(dist)).ext.start()
            elif dist > self._geom.length:
                point = self.prolong(absolute=True).from_tail(dist - self._geom.length).ext.end()
            else:
                point = self._geom.interpolate(dist, normalized=False)

            result.append(point)

        return result[0] if isinstance(distance, Num) else result

    def endpoints_vector(self) -> Vector:
        """
        Returns
        -------
        Vector that created from start and end points of current linestring
        """
        return Vector.from_endpoints_of(self._geom)

    def normal_vector(self) -> Vector:
        """
        the normal vector of current linestring, a.k.a the perpendicular vector of endpoints_vector
        Returns
        -------
        Vector
        """
        return self.endpoints_vector().ccw_perpendicular

    def merge(self, line: LineString, merge_line_strategy: MergeLineStrategy = native_linemerge) -> LineString:
        """
        Parameters
        ----------
        line
        merge_line_strategy: function of MergeLineStrategy

        Returns
        -------
        return merged linestring, if success. otherwise return origin linestring
        """
        if not isinstance(line, LineString):
            raise TypeError(f'merge accept another linestring as parameter, given {line}')

        return merge_line_strategy(self._geom, line)

    def polygonize(self, default_strategy=True) -> Polygonize:
        """
        poligonize the geom or geom list
        Parameters
        ----------
        default_strategy: True for auto adding 4 strategies, False for no strategy

        Returns
        -------
        Polygonize instance
        """
        geoms = self._geom
        if isinstance(self._geom, BaseGeometry):
            geoms = [self._geom]

        if default_strategy:
            return (Polygonize(geoms).add_strategy(ShapelyPolygonizeStrategy())
                    .add_strategy(ConvexHullStrategy())
                    .add_strategy(MouldStrategy())
                    .add_strategy(ClosingEndPointsStrategy()))
        return Polygonize(geoms)
