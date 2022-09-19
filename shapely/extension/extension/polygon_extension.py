from itertools import product
from typing import Union, Optional, Iterable, Tuple

from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy, BaseDecomposeStrategy
from shapely.extension.util.decompose import decompose
from shapely.geometry import Polygon, LineString, JOIN_STYLE, CAP_STYLE
from shapely.ops import unary_union


class PolygonExtension(BaseGeomExtension):
    def edge_pair_with(self, poly_or_line: Union[Polygon, LineString],
                       strategy: Optional[BaseDecomposeStrategy] = None) -> Iterable[Tuple[LineString, LineString]]:
        decompose_strategy = strategy or StraightSegmentDecomposeStrategy()
        target_lines = decompose(poly_or_line, LineString, decompose_strategy)
        own_lines = self.decompose(LineString, decompose_strategy)
        yield from product(own_lines, target_lines)

    def has_edge_parallel_to(self, poly_or_line: Union[Polygon, LineString],
                             strategy: Optional[BaseDecomposeStrategy] = None) -> bool:
        return any(line0.ext.is_parallel_to(line1) for line0, line1 in self.edge_pair_with(poly_or_line, strategy))

    def has_edge_perpendicular_to(self, poly_or_line: Union[Polygon, LineString],
                                  strategy: Optional[BaseDecomposeStrategy] = None):
        return any(line0.ext.is_perpendicular_to(line1) for line0, line1 in self.edge_pair_with(poly_or_line, strategy))

    def has_edge_collinear_to(self, poly_or_line: Union[Polygon, LineString],
                              strategy: Optional[BaseDecomposeStrategy] = None):
        return any(line0.ext.is_collinear_to(line1) for line0, line1 in self.edge_pair_with(poly_or_line, strategy))

    def union(self, poly: Polygon, direction: Optional[Vector] = None, dist_tol: float = 1e-16):
        if self._geom.intersects(poly):
            return self._geom.union(poly)
        if self._geom.distance(poly) > dist_tol:
            return unary_union([self._geom, poly])

        shadow = self.projection_towards(poly, direction=direction).shadow().buffer(dist_tol,
                                                                                    join_style=JOIN_STYLE.mitre,
                                                                                    cap_style=CAP_STYLE.flat)
        return unary_union([self._geom, poly, shadow])
