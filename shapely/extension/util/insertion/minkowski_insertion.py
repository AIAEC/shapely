from typing import List, Union

from cgal import minkowski_sum

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union
from shapely.wkt import loads


class MinkowskiInsertion:
    def __init__(self, insert_poly: Polygon):
        self._reversed_insert_poly = transform(lambda x, y, z=None: (-x, -y), insert_poly).ext.ccw().ext.move_to((0, 0))

    def of(self, space: Polygon, obstacle: Union[Polygon, MultiPolygon]) -> List[Polygon]:
        assert not self._reversed_insert_poly.is_empty and isinstance(self._reversed_insert_poly, Polygon)

        occupations: List[BaseGeometry] = []
        reversed_insertion_wkt = self._reversed_insert_poly.wkt

        for piece in obstacle.ext.flatten(Polygon):
            piece_wkt = piece.ext.ccw().wkt
            try:
                obstacle_wkt = minkowski_sum(geom_wkt=piece_wkt, kernel_poly_wkt=reversed_insertion_wkt, num_decimals=8)
            except (RuntimeError, ValueError):
                # to avoid self intersects case which is valid and simple in shapely, but cause runtime error in cgal
                piece_wkt = piece.ext.rbuf(MATH_MIDDLE_EPS).ext.ccw().wkt
                obstacle_wkt = minkowski_sum(geom_wkt=piece_wkt, kernel_poly_wkt=reversed_insertion_wkt, num_decimals=8)

            occupations.append(loads(obstacle_wkt))

        insertion_candidate = space.difference(unary_union(occupations + [obstacle]))

        return insertion_candidate.ext.flatten(Polygon).list()
