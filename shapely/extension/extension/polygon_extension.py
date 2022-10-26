from itertools import product
from typing import Union, Optional, Iterable, Tuple

from shapely.extension.geometry.straight_segment import StraightSegment

from shapely.extension.constant import MATH_EPS
from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.decompose_strategy import BaseDecomposeStrategy
from shapely.extension.util.decompose import decompose
from shapely.geometry import Polygon, LineString, JOIN_STYLE, CAP_STYLE, MultiPolygon
from shapely.ops import unary_union


class PolygonExtension(BaseGeomExtension):
    @property
    def shell(self) -> Polygon:
        return Polygon(self._geom.exterior)

    def edge_pair_with(self, poly_or_line: Union[Polygon, LineString],
                       decompose_strategy: Optional[BaseDecomposeStrategy] = None
                       ) -> Iterable[Tuple[LineString, LineString]]:
        """
        return iterator of 2-tuple of current polygon's edges and given polygon's edges or linestring
        Parameters
        ----------
        poly_or_line: polygon or linestring
        decompose_strategy: decompose strategy, if None, use the default decompose strategy

        Returns
        -------
        iterator[linestring, linestring], with first item the edges of current polygon and second the edges of other geom
        """
        decompose_strategy = decompose_strategy
        target_lines = decompose(poly_or_line, StraightSegment, decompose_strategy)
        own_lines = self.decompose(StraightSegment, decompose_strategy)
        yield from product(own_lines, target_lines)

    def has_edge_parallel_to(self, poly_or_line: Union[Polygon, LineString],
                             decompose_strategy: Optional[BaseDecomposeStrategy] = None) -> bool:
        """
        whether current polygon has at least 1 edge parallel to the given polygon or linestring
        Parameters
        ----------
        poly_or_line: polygon or linestring
        decompose_strategy: decompose strategy, if None, use the default decompose strategy

        Returns
        -------
        bool
        """
        return any(
            line0.ext.is_parallel_to(line1) for line0, line1 in self.edge_pair_with(poly_or_line, decompose_strategy))

    def has_edge_perpendicular_to(self, poly_or_line: Union[Polygon, LineString],
                                  decompose_strategy: Optional[BaseDecomposeStrategy] = None):
        """
        whether current polygon has at least 1 edge perpendicular to the given polygon or linestring
        Parameters
        ----------
        poly_or_line: polygon or linestring
        decompose_strategy: decompose strategy, if None, use the default decompose strategy

        Returns
        -------
        bool
        """
        return any(line0.ext.is_perpendicular_to(line1) for line0, line1 in
                   self.edge_pair_with(poly_or_line, decompose_strategy))

    def has_edge_collinear_to(self, poly_or_line: Union[Polygon, LineString],
                              decompose_strategy: Optional[BaseDecomposeStrategy] = None):
        """
        whether current polygon has at least 1 edge collinear to the given polygon or linestring
        Parameters
        ----------
        poly_or_line: polygon or linestring
        decompose_strategy: decompose strategy, if None, use the default decompose strategy

        Returns
        -------
        bool
        """
        return any(
            line0.ext.is_collinear_to(line1) for line0, line1 in self.edge_pair_with(poly_or_line, decompose_strategy))

    def union(self, poly: Polygon,
              direction: Optional[Vector] = None,
              dist_tol: float = MATH_EPS) -> Union[Polygon, MultiPolygon]:
        """
        union current polygon with given polygon.
            if they don't intersect but with distance <= dist_tol, union the current polygon, given polygon and the
            shadow(current -> given polygon); otherwise use the native unary_union
        Parameters
        ----------
        poly
        direction
        dist_tol

        Returns
        -------
        polygon or multi-polygon
        """
        if self._geom.intersects(poly):
            return self._geom.union(poly)
        if self._geom.ext.distance(poly, direction) > dist_tol:
            return unary_union([self._geom, poly])

        shadow = self.projection_towards(poly, direction=direction).shadow().buffer(MATH_EPS,
                                                                                    join_style=JOIN_STYLE.mitre,
                                                                                    cap_style=CAP_STYLE.flat)
        return unary_union([self._geom, poly, shadow])
