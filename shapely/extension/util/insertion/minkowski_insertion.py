from typing import List, Union

from cgal import minkowski_sum

from shapely.extension.model.cgal.polygon_2d import to_cgal, to_shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union


class MinkowskiInsertion:
    def __init__(self, insert_poly: Polygon):
        self._reversed_insert_poly = transform(lambda x, y, z=None: (-x, -y), insert_poly).ext.ccw().ext.move_to((0, 0))

    def of(self, space: Polygon, obstacle: Union[Polygon, MultiPolygon]) -> List[Polygon]:
        assert not self._reversed_insert_poly.is_empty and isinstance(self._reversed_insert_poly, Polygon)

        occupations: List[BaseGeometry] = []
        for piece in obstacle.ext.flatten(Polygon):
            occupations.append(to_shapely(minkowski_sum(to_cgal(self._reversed_insert_poly), to_cgal(piece))))

        insertion_candidate = space.difference(unary_union(occupations))

        return insertion_candidate.ext.flatten(Polygon).list()
