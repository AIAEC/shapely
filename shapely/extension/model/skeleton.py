from typing import List, Union, Tuple, Set

from cgal import find_skeleton_of_poly, find_skeleton_of_poly_with_holes, Coord2D

from shapely.extension.util.func_util import lmap, lfilter
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import linemerge, unary_union


class Skeleton:
    def __init__(self, single_geom: Union[Point, LineString, Polygon]):
        if not isinstance(single_geom, (Point, LineString, Polygon)):
            raise TypeError('only accept single geometry, like point, linestring or polygon')

        self._geom = single_geom

        self._trunk_segments: List[LineString] = []
        self._branch_segments: List[LineString] = []

        if isinstance(self._geom, LineString):
            self._branch_segments: List[LineString] = [self._geom]

        elif isinstance(self._geom, Polygon):
            shell = self.cgal_shell(self._geom)
            holes = self.cgal_holes(self._geom)
            if holes:
                skeleton = find_skeleton_of_poly_with_holes(shell, holes)
            else:
                skeleton = find_skeleton_of_poly(shell)

            # raw segments below contains both segments (A, B) and (B, A), in which A, B are points
            # thus we need to filter these segments and for (A, B) and (B, A)
            self._trunk_segments: List[LineString] = self.linestring_from(skeleton.sticks)
            self._branch_segments: List[LineString] = self.linestring_from(skeleton.branches)

    @staticmethod
    def linestring_from(coord_pairs: List[Tuple[Coord2D, Coord2D]]) -> List[LineString]:
        return [LineString([(coord0.x, coord0.y), (coord1.x, coord1.y)]) for coord0, coord1 in coord_pairs]

    @staticmethod
    def cgal_shell(polygon: Polygon) -> List[Coord2D]:
        polygon = polygon.ext.legalize().ext.ccw()
        return lmap(Coord2D, list(polygon.exterior.coords)[:-1])  # cgal polygon should be without duplicate tail

    @staticmethod
    def cgal_holes(polygon: Polygon) -> List[List[Coord2D]]:
        polygon = polygon.ext.legalize().ext.ccw()
        holes: List[List[Coord2D]] = []
        for interior in polygon.interiors:
            holes.append(lmap(Coord2D, list(interior.coords)[:-1]))  # cgal polygon should be without duplicate tail
        return holes

    def trunk_segments(self) -> List[LineString]:
        """
        filter raw trunk segments, with naive strategy that discard those segments whose reverse segments have been
        visited.

        Returns
        -------
        filtered trunk segments
        """
        segments: OrderedSet = OrderedSet()

        for trunk_segment in self._trunk_segments:
            if trunk_segment.ext.reverse() not in segments:
                segments.add(trunk_segment)

        return list(segments)

    def branch_segments(self) -> List[LineString]:
        """
        filter raw branch segments, only keep those segments who point to outside, or we can define it as
        whose start point is closer to trunk than end point
        Returns
        -------
        trunk segments that have no "duplicated backwards segments"
        """
        trunk_union = unary_union(self.trunk_segments())
        return lfilter(lambda seg: trunk_union.distance(seg.ext.start()) < trunk_union.distance(seg.ext.end()),
                       self._branch_segments)

    def full_segments(self) -> List[LineString]:
        return self.trunk_segments() + self.branch_segments()

    def trunks(self) -> List[LineString]:
        return linemerge(self.trunk_segments()).ext.flatten(LineString).list()
