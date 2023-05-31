from typing import Literal, List

from py2d import Math

from shapely.extension.util.func_util import lmap
from shapely.geometry import Polygon

PARTITION_MODE = Literal['convex']


class PolygonPartitioner:

    def __call__(self, polygon: Polygon) -> List[Polygon]:
        if not isinstance(polygon, Polygon) or not polygon.is_valid or polygon.is_empty:
            return [polygon]

        return self.convex_partition(polygon)

    def convex_partition(self, polygon: Polygon) -> List[Polygon]:
        """

        Parameters
        ----------
        polygon

        Returns
        -------
        valid convex polygons
        """
        if polygon.interiors:
            raise NotImplementedError('holes are not supported')
        math_poly = Math.Polygon.from_tuples(polygon.exterior.coords[1:])
        math_partitions = math_poly.convex_decompose(math_poly)
        partitions = lmap(lambda math_poly_: Polygon([(p.x, p.y) for p in math_poly_.points]), math_partitions)
        return partitions
