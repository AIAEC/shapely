from typing import Union, Optional

from shapely.extension.geometry.empty import EMPTY_GEOM

from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.vector import Vector
from shapely.geometry import Polygon, Point, LineString, MultiPolygon


class PolygonCutter:
    def __init__(self, polygon: Polygon, point: Point, vector: Vector, target_area: float, tolerance: float = MATH_EPS):
        """
        Parameters
        ----------
        point: a point for generating cutting line.
            note that it cannot be too far away from polygon(less than polygon.length), or it will return empty polygon.
        vector: specify the cutting direction, and used for generating cutting line.
            note that it cannot be opposite to the polygon，or it will return empty polygon.
        target_area: specified cutting area
        """
        self._polygon = polygon
        self._point = point
        self._vector = vector
        self._target_area = target_area
        self._tolerance = tolerance

    def cut(self) -> Union[Polygon, MultiPolygon]:
        if self._target_area <= 0:
            return EMPTY_GEOM

        # generate cutting line according to the given point
        vector_line = self._vector.ray(self._point, 1)
        cutting_line = vector_line.ext.perpendicular_line(self._point, self._polygon.length, 'mid')
        # get cutting direction according to vector line and cutting line
        straight_cutting_line = StraightSegment(cutting_line.coords)
        direction_point = Point(vector_line.coords[1])
        direction = 1 if straight_cutting_line.point_on_left(direction_point) else -1
        # buffer max, used for finding polygon
        max_buffer = cutting_line.ext.buffer().single_sided().rect(direction * self._polygon.length * 2)
        max_intersect_poly = max_buffer.intersection(self._polygon)

        if not cutting_line.intersects(self._polygon):
            # when polygon cannot be found according to given point and vector
            # this always because the given point is too far or given the opposite vector.
            if max_intersect_poly.is_empty:
                return max_intersect_poly
            return self._binary_cutting(cutting_line, direction, self._target_area, self._tolerance)
        else:
            if self._target_area >= max_intersect_poly.area:
                return max_intersect_poly
            return self._binary_cutting(cutting_line, direction, self._target_area, self._tolerance)

    def _binary_cutting(self, cutting_line: LineString,
                        direction: float,
                        target_area: float,
                        tolerance: float = MATH_EPS) -> Union[Polygon, MultiPolygon]:
        """
        Parameters
        ----------
        cutting_line: a LineString used for cutting polygon.
            note that it must be long enough, or it may return wrong polygon.
        direction: cutting direction. if given 1, it means cutting direction is on the left of cutting line.
            if given -1, it means cutting direction is on the right of cutting line.
        target_area: specified cutting area

        Returns
        -------
        specified area polygon or multipolygon
        """
        # nearest and furthest distance between cutting_line and polygon
        left = cutting_line.distance(self._polygon)
        right = self._polygon.ext.decompose(Point).map(cutting_line.distance).max()

        # use binary search to cut specified area polygon
        max_count = 100
        count = 0
        while left < right and count < max_count:
            count = count + 1
            mid = (right - left) / 2 + left
            select_buffer = cutting_line.ext.buffer().single_sided().rect(direction * mid)
            intersect_poly = select_buffer.intersection(self._polygon)
            if abs(intersect_poly.area - target_area) <= tolerance:
                return intersect_poly
            elif intersect_poly.area > target_area:
                right = mid
            else:
                left = mid

        raise ValueError(
            'Cannot cut polygon to the given area within the allowed error range, you can increase the tolerance.')
