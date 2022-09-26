from typing import Optional

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.typing import Num
from shapely.geometry import Point, LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union


class ShortestStraightPath:
    """
    求两个shapely.geometry对象在指定方向上的最短LineString的类
    """

    def __init__(self, direction: Optional[Vector] = None, dist_tol: Num = MATH_EPS):
        self._direction = direction
        self._dist_tol = dist_tol

    def of(self, geom0: BaseGeometry, geom1: BaseGeometry, directed: bool = False) -> LineString:
        """
        this function will find the shortest path between two geometries in a certain angle. if the angle is not given,
        the shortest path will be found.

        Parameters
        ----------
        geom0: BaseGeometry
        geom1: BaseGeometry
        directed: bool: if True, then only calculate the distance of geom0 -> geom1, not the other way around.

        Returns
        -------
        shapely.Linestring
        """
        if not geom0.is_valid or not geom1.is_valid:
            return LineString()

        if geom0.is_empty or geom1.is_empty:
            return LineString()

        if geom0.intersects(geom1):
            intersection = geom0.intersection(geom1)
            points = intersection.ext.decompose(Point)
            return LineString((points[0], points[0]))

        if geom0.contains(geom1) or geom1.contains(geom0):
            inner_polygon = geom0 if geom0.area < geom1.area else geom1
            return LineString((inner_polygon.exterior.coords[0], inner_polygon.exterior.coords[0]))

        if self._direction is None:
            return LineString(nearest_points(geom0, geom1))

        path_geom0_to_geom1 = (self._shortest_path_in_direction(geom0, geom1, self._direction)
                               or self._shortest_path_in_direction(geom1, geom0, self._direction.invert())
                               or LineString())
        if directed:
            return path_geom0_to_geom1

        path_geom1_to_geom0 = (self._shortest_path_in_direction(geom0, geom1, self._direction.invert())
                               or self._shortest_path_in_direction(geom1, geom0, self._direction)
                               or LineString())

        if path_geom0_to_geom1.is_empty:
            return path_geom1_to_geom0

        if path_geom1_to_geom0.is_empty:
            return path_geom0_to_geom1

        return path_geom0_to_geom1 if path_geom0_to_geom1.length < path_geom1_to_geom0.length else path_geom1_to_geom0

    def _shortest_path_in_direction(self, geom0: BaseGeometry,
                                    geom1: BaseGeometry,
                                    direction: Vector) -> Optional[LineString]:
        """
        this function will find the shortest path from a vertex in geom0 to the geom1 in a certain direction

        to implement this algorithm, we should notice that, one the end of the shortest path between two geometries must be
        a vertex of one geometries, so that we could draw a lines from all the vertexs from geom0 in a certain direction, and
        these lines will intersects geom1. The shortest path we want must be the shortest one among these lines.
        Parameters
        ----------
        geom0: BaseGeometry
        geom1: BaseGeometry
        direction: Vector

        Returns
        -------
        shapely.Linestring or None when failed
        """
        points_in_geom0 = geom0.ext.decompose(Point)

        shortest_path: Optional[LineString] = None
        envelope = unary_union((geom0, geom1)).envelope

        largest_distance = Point(envelope.exterior.coords[0]).distance(Point(envelope.exterior.coords[2]))
        shortest_path_length = largest_distance

        for point in points_in_geom0:

            distance = geom1.hausdorff_distance(point)
            start_point = point.coords[0]

            end_point = direction.unit(distance).apply_coord(start_point)

            line = LineString((start_point, end_point))
            intersection = self._intersection(line=line, geom=geom1)

            if intersection.is_valid and not intersection.is_empty:
                candidate_shortest_line = LineString(nearest_points(point, intersection))

                if not candidate_shortest_line.is_empty and candidate_shortest_line.length < shortest_path_length:
                    shortest_path = candidate_shortest_line
                    shortest_path_length = candidate_shortest_line.length

        return shortest_path

    def _intersection(self, line: LineString, geom: BaseGeometry) -> BaseGeometry:
        intersection = line.intersection(geom)
        if intersection:
            return intersection

        if geom.distance(line) < self._dist_tol:
            nearest_point_on_line = nearest_points(geom, line)[1]
            return nearest_point_on_line

        return Point()
