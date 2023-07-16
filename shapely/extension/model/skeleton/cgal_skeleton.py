from typing import List, Union

from cgal import straight_skeleton

from shapely.extension.model.skeleton.base_skeleton import BaseSkeleton
from shapely.extension.util.func_util import separate
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import linemerge
from shapely.wkt import loads


class CgalSkeleton(BaseSkeleton):
    def __init__(self, single_geom: Union[Point, LineString, Polygon]):
        if not isinstance(single_geom, (Point, LineString, Polygon)):
            raise TypeError('only accept single geometry, like point, linestring or polygon')

        self._geom = single_geom

        self._trunk_segments: List[LineString] = []
        self._branch_segments: List[LineString] = []

        if isinstance(self._geom, LineString):
            self._branch_segments: List[LineString] = [self._geom]

        elif isinstance(self._geom, Polygon):
            poly_wkt = self._geom.ext.legalize().ext.ccw().wkt
            multilinestring_wkt = straight_skeleton(poly_wkt, num_decimals=8)
            lines: List[LineString] = loads(multilinestring_wkt).ext.flatten(LineString)
            geom_boundary = self._geom.boundary
            self._branch_segments, self._trunk_segments = separate(lambda line: geom_boundary.intersects(line),
                                                                   items=lines)

    def trunk_segments(self) -> List[LineString]:
        """
        filter raw trunk segments, with naive strategy that discard those segments whose reverse segments have been
        visited.

        Returns
        -------
        filtered trunk segments
        """
        return self._trunk_segments

    def branch_segments(self) -> List[LineString]:
        """
        filter raw branch segments, only keep those segments who point to outside, or we can define it as
        whose start point is closer to trunk than end point
        Returns
        -------
        trunk segments that have no "duplicated backwards segments"
        """
        return self._branch_segments

    def full_segments(self) -> List[LineString]:
        return self.trunk_segments() + self.branch_segments()

    def trunks(self) -> List[LineString]:
        return linemerge(self.trunk_segments()).ext.flatten(LineString).list()
