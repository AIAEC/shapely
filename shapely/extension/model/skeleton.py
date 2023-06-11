from typing import List, Union, Tuple

from shapely.extension.util.func_util import lmap
from shapely.geometry import LineString, Polygon, Point
from cgal import find_skeleton_of_poly, find_skeleton_of_poly_with_holes, Coord2D

from shapely.ops import linemerge


class Skeleton:
    def __init__(self, single_geom: Union[Point, LineString, Polygon]):
        if not isinstance(single_geom, (Point, LineString, Polygon)):
            raise TypeError('only accept single geometry, like point, linestring or polygon')

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

            self._trunk_segments: List[LineString] = self.linestring_from(skeleton.sticks)
            self._branch_segments: List[LineString] = self.linestring_from(skeleton.branches)

    @staticmethod
    def linestring_from(coord_pairs: List[Tuple[Coord2D, Coord2D]]) -> List[LineString]:
        return [LineString([(coord0.x, coord0.y), (coord1.x, coord1.y)]) for coord0, coord1 in coord_pairs]
    @staticmethod
    def cgal_shell(polygon: Polygon) -> List[Coord2D]:
        polygon = polygon.ext.legalize().ext.ccw()
        return lmap(Coord2D, list(polygon.exterior.coords)[:-1])

    @staticmethod
    def cgal_holes(polygon: Polygon) -> List[List[Coord2D]]:
        polygon = polygon.ext.legalize().ext.ccw()
        holes: List[List[Coord2D]] = []
        for interior in polygon.interiors:
            holes.append(lmap(Coord2D, list(interior.coords)[:-1]))
        return holes

    def trunk_segments(self) -> List[LineString]:
        return self._trunk_segments

    def branch_segments(self) -> List[LineString]:
        return self._branch_segments

    def full_segments(self) -> List[LineString]:
        return self.trunk_segments() + self.branch_segments()

    def trunks(self) -> List[LineString]:
        return linemerge(self.trunk_segments()).ext.flatten(LineString).list()
