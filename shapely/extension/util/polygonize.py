from itertools import chain
from typing import List

from shapely.extension.constant import LARGE_EPS
from shapely.extension.functional import seq
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import separate, group
from shapely.geometry import Polygon, LineString, LinearRing
from shapely.geometry.base import BaseGeometry


class Polygonize:

    def __init__(self, geoms: List[BaseGeometry] = None):
        self._geoms = geoms or []
        self._strategies = []

    def add_strategy(self, polygonize_strategy):
        self._strategies.append(polygonize_strategy.compose)
        return self

    def do(self, math_eps: float = LARGE_EPS, keep_origin_polygon: bool = False) -> List[Polygon]:
        """
        poligonize the geom list. Firstly, it will flatten each geom. Then, if the geoms are all polygon type, return
        geoms directly. If the keep_origin_polygon is True, keep the polygons and geom which can be polygonized in
        given geoms, otherwise go to next step directly. Lastly, polygonize each geom according to specified strategies.
        Parameters
        ----------
        math_eps: math err tolerance
        keep_origin_polygon: keep the polygons in given geoms and only find polygons within those non-polygons

        Returns
        -------
        Polygonize instance
        """
        if not self._geoms:
            return []

        single_geoms = list(chain.from_iterable(flatten(geom) for geom in self._geoms))
        having_only_polygons = all(isinstance(geom, Polygon) for geom in single_geoms)
        if having_only_polygons:
            return [poly for poly in single_geoms if not poly.is_empty]

        origin_polygons = []
        if keep_origin_polygon:
            def can_be_polygonized(geom):
                return (isinstance(geom, Polygon)
                        or isinstance(geom, LinearRing)
                        # geom.is_ring fails for self-intersecting line
                        or (isinstance(geom, LineString) and geom.is_closed))

            poly_candidates, single_geoms = separate(can_be_polygonized, single_geoms)
            origin_polygons = [Polygon(p) for p in poly_candidates]
            origin_polygons: List[BaseGeometry] = flatten(geom_or_geoms=origin_polygons,
                                                          target_class_or_callable=Polygon,
                                                          validate=True).to_list()

        lines: List[LineString] = (seq(single_geoms)
                                   .flat_map(lambda geom: geom.ext.decompose(LineString).list())
                                   .list())
        line_groups: List[List[LineString]] = group(lambda l1, l2: l1.distance(l2) < math_eps, lines)

        result: List[Polygon] = []
        for line_group in line_groups:
            for compose_polygon in self._strategies:
                possible_polygons: List[Polygon] = compose_polygon(line_group)
                if possible_polygons:
                    result.extend(possible_polygons)
                    break

        return result + origin_polygons
