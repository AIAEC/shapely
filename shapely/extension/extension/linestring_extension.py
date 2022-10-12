from collections.abc import Sequence
from itertools import product, combinations
from typing import Union, Tuple, Optional, Iterable, Callable

from shapely.extension.constant import MATH_EPS, LARGE_ENOUGH_DISTANCE
from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model import Angle
from shapely.extension.model.coord import Coord
from shapely.extension.model.interval import Interval
from shapely.extension.model.projection import Projection, ProjectionOnLine
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.bypassing_strategy import BaseBypassingStrategy, ShorterBypassingStrategy
from shapely.extension.strategy.offset_strategy import BaseOffsetStrategy, OffsetStrategy
from shapely.extension.typing import Num, CoordType
from shapely.extension.util.func_util import min_max
from shapely.extension.util.iter_util import win_slice
from shapely.extension.util.line_extent import LineExtent
from shapely.extension.util.prolong import Prolong
from shapely.geometry import Point, LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import substring, unary_union


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

    def substring(self, interval: Union[Tuple[float, float], Interval], absolute: bool = True):
        """
        calculate the substring of current linestring
        Parameters
        ----------
        interval
        absolute

        Returns
        -------
        LineString
        """
        if isinstance(interval, Sequence):
            interval = Interval(interval[0], interval[1])
        return substring(self._geom,
                         start_dist=float(interval.left),
                         end_dist=float(interval.right),
                         normalized=not absolute)

    def inverse(self) -> LineString:
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
        angle = self.angle(angle_strategy) - other.ext.angle(angle_strategy)
        return angle.almost_equal(180, angle_tol=angle_tol) or angle.almost_equal(0, angle_tol=angle_tol)

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

        if line_extent := LineExtent.of_sequence_curves(self._geom, line.ext.inverse(), float(extent_dist)):
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
            vec_start_to_pt = Vector.from_origin_to_target(self.start(), point)
            vec_line = Vector.from_endpoints_of(line)
            including_angle_cos = vec_start_to_pt.angle.including_angle(vec_line.angle).cos()
            return vec_line.unit(including_angle_cos * vec_start_to_pt.length).apply(self.start())

        def native_project(line, point: Union[Point, CoordType]) -> Point:
            return line.interpolate(line.project(Point(point)))

        if not on_extension:
            return native_project(self._geom, point_or_coord)

        if isinstance(self._geom, StraightSegment):
            return project_on_straight_line(self._geom, point_or_coord)

        native_projected_pt = native_project(self._geom, point_or_coord)
        projected_pt_at_start = project_on_straight_line(self[:2], point_or_coord)
        projected_pt_at_end = project_on_straight_line(self[-2:], point_or_coord)

        given_point = Point(point_or_coord)
        return min([native_projected_pt,
                    projected_pt_at_start,
                    projected_pt_at_end], key=lambda pt: given_point.distance(pt))

    def perpendicular_line(self, point: Point, length: float, position: str = 'mid') -> LineString:
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
        vector = Vector.from_origin_to_target(self._geom.interpolate(project - MATH_EPS),
                                              self._geom.interpolate(project + MATH_EPS))
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

    def tangent_line(self, point: Point, length: float, position: str = 'mid') -> LineString:
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
        perpendicular_direction = Vector.from_endpoints_of(self._geom).cw_perpendicular
        return self.distance(geom, direction=perpendicular_direction)

    # TODO: interpolate()
    # TODO: 等分(按长度, 按数量)
