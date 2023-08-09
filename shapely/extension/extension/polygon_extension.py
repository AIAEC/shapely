from itertools import product
from typing import Union, Optional, Iterable, Tuple, List, Literal


from shapely.extension.constant import MATH_EPS, MATH_MIDDLE_EPS
from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.decompose_strategy import BaseDecomposeStrategy
from shapely.extension.util.convexity import corner_points
from shapely.extension.util.decompose import decompose
from shapely.extension.util.partition import PolygonPartitioner
from shapely.extension.util.polygon_cutter import PolygonCutter
from shapely.extension.util.regularize import regularize
from shapely.extension.util.union import tol_union
from shapely.geometry import Polygon, LineString, JOIN_STYLE, CAP_STYLE, MultiPolygon, Point
from shapely.ops import unary_union, nearest_points


class PolygonExtension(BaseGeomExtension):
    @property
    def shell(self) -> Polygon:
        """
        Returns
        -------
        the polygon made by exterior of current polygon without any holes
        """
        return Polygon(self._geom.exterior)

    @property
    def holes(self) -> Iterable[Polygon]:
        """
        Returns
        -------
        iterator of polygon made by interior of current polygon
        """
        for hole in self._geom.interiors:
            yield Polygon(hole)

    def convex_points(self, on_boundary: Literal["exterior", "interiors", "both"] = "both") -> List[Point]:
        """
        return the convex points in appointed polygon's boundary

        Parameters
        ----------
        on_boundary: get convex points from exterior polygon or interiors polygon or both.

        Returns
        -------
        convex points
        """
        return corner_points(self._geom, on_boundary=on_boundary, convex_corner=True)

    def concave_points(self, on_boundary: Literal["exterior", "interiors", "both"] = "both") -> List[Point]:
        """
        return the concave points on appointed polygon's boundary

        Parameters
        ----------
        on_boundary:get convex points from exterior polygon or interiors polygon or both.

        Returns
        -------
        concave points
        """
        return corner_points(self._geom, on_boundary=on_boundary, convex_corner=False)

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
        union_polys = tol_union([self._geom, poly], MATH_MIDDLE_EPS).ext.flatten(Polygon).list()
        if len(union_polys) == 1:
            return union_polys[0]

        direction = direction or Vector.from_origin_to_target(*nearest_points(self._geom, poly))
        if self._geom.ext.distance(poly, direction) > dist_tol:
            return unary_union([self._geom, poly])

        shadow = self.projection_towards(poly, direction=direction).shadow().buffer(MATH_EPS,
                                                                                    join_style=JOIN_STYLE.mitre,
                                                                                    cap_style=CAP_STYLE.flat)
        return unary_union([self._geom, poly, shadow])

    def cut(self, point: Point,
            vector: Vector,
            target_area: float,
            tolerance: float = MATH_EPS) -> Union[Polygon, MultiPolygon]:
        """
        cutting the given polygon to get specified area polygon by given vector

        Parameters
        ----------
        point: a point for generating cutting line.
            note that it cannot be too far away from polygon(less than polygon.length), or it will return empty polygon.
        vector: specify the cutting direction, and used for generating cutting line
            note that it cannot be opposite to the polygon，or it will return empty polygon.
        target_area: specified cutting area
        tolerance: tolerance scope

        Returns
        -------
        specified area polygon or multipolygon
        """
        return PolygonCutter(self._geom, point, vector, target_area, tolerance).cut()

    def partitions(self) -> List[Polygon]:
        """
        partition the current polygon into several valid convex sub polygons
        CAUTION: polygon with holes is NOT supported !

        Returns
        -------
        valid convex sub polygons
        """
        return PolygonPartitioner()(self._geom)

    @property
    def is_convex(self) -> bool:
        return self._geom.convex_hull.equals(self._geom)

    def regularized(self) -> Polygon:
        return regularize(self._geom)