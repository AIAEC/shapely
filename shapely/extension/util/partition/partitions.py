from typing import List

from shapely.extension.util.func_util import lmap
from shapely.extension.util.partition._poly_decompose import polygonQuickDecomp
from shapely.geometry import Polygon


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
        math_poly = list(lmap(list, polygon.exterior.ext.ccw().coords[1:]))
        math_partitions = polygonQuickDecomp(math_poly)
        partitions = lmap(Polygon, math_partitions)
        return partitions
