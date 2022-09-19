from typing import Union, List

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.coord import Coord
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import separate, lfilter
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection, LinearRing
from shapely.ops import linemerge


class LineBypassing:
    def __init__(self, line: LineString):
        if not line.is_valid:
            raise ValueError(f'given line is not valid, with its length={line.length}')

        self._line = line

    def bypass(self, poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection],
               chosen_longer_path: bool = False) -> LineString:
        '''
        ┌─────┐
        │poly │
    ────│─────│───── linestring
        └─────┘

        long bypassing:
        ┌─────┐
        │poly │
    ────┴     ┘───── linestring


        LineString 绕过 Polygon
        返回的LineString包括：
        原有的LineString与Polygon相交，现在把LineString在Polygon内部的部分清除掉，加上Polygon的部分边沿(选择一条路径），得到 LineBypassing
        视觉效果上是LineString绕过Polygon
        有两种路径选择，如果chosen_longer_path=True
        则选择最长的path

        :param poly_or_multi_poly: Polygon或者多个Polygon
        :param chosen_longer_path: 选择最长的path
        :return: LineString (其中一种LineBypassing的方式）

        '''
        for poly in flatten(poly_or_multi_poly, Polygon).to_list():
            self._line = self.bypass_single(poly, chosen_longer_path=chosen_longer_path)

        return self._line

    @classmethod
    def cut_linearring_by_line(cls, ring: LinearRing, crossing_line: LineString) -> List[LineString]:
        """
        cut the linearRing by crossing line, and return the pieces of the ring

        this method cannot be replaced by ring.difference(crossing_line), because with difference, a circle ring cutting
        by a crossing line will return 3 pieces instead of 2 pieces.

        Why is that? when doing difference linearRing will been regarded as linestring, so that its first point and latest
        point, though exactly equal, will not be treated as connected

        :param ring:
        :param crossing_line:
        :return:
        """
        ring_pieces: List[LineString] = flatten(ring.difference(crossing_line), LineString).to_list()
        crossing_lines_inside: List[LineString] = flatten(Polygon(ring).intersection(crossing_line), LineString).to_list()

        def have_same_endpoints_with_any_crossing_seg(line):
            return any(
                cls.two_lines_have_same_endpoints(crossing_line, line) for crossing_line in crossing_lines_inside)

        valid_pieces, separated_pieces = separate(func=have_same_endpoints_with_any_crossing_seg, items=ring_pieces)
        return flatten(linemerge(separated_pieces), LineString).to_list() + valid_pieces

    @classmethod
    def two_lines_have_same_endpoints(cls, line0: LineString, line1: LineString) -> bool:
        coord00, coord01 = line0.coords[0], line0.coords[-1]
        coord10, coord11 = line1.coords[0], line1.coords[-1]
        return (Coord.dist(coord00, coord10) + Coord.dist(coord01, coord11) < MATH_EPS
                or Coord.dist(coord00, coord11) + Coord.dist(coord01, coord10) < MATH_EPS)

    def bypass_single(self, poly: Polygon, chosen_longer_path: bool = False) -> LineString:
        if not self._line.crosses(poly):
            return self._line

        exterior_pieces: List[LineString] = self.cut_linearring_by_line(poly.exterior, self._line)
        line_pieces: List[LineString] = flatten(self._line.difference(poly.exterior), LineString).to_list()

        line_pieces_inside, line_pieces_outside = separate(
            func=lambda line: line.intersection(poly).length > line.length / 2,
            items=line_pieces)

        valid_surroundings: List[LineString] = []
        for line_piece_inside in line_pieces_inside:
            chosen_func = max if chosen_longer_path else min
            if surrounding := chosen_func(
                    lfilter(lambda ext: self.two_lines_have_same_endpoints(ext, line_piece_inside), exterior_pieces),
                    key=lambda line: line.length,
                    default=None):
                valid_surroundings.append(surrounding)
            else:
                valid_surroundings.append(line_piece_inside)

        bypassing = linemerge(valid_surroundings + line_pieces_outside)

        # for sake of merging into multilinestring
        if piece := max(flatten(bypassing, LineString).to_list(), key=lambda line: line.length, default=None):
            bypassing = piece

        # reserve the coord order of the bypassing line
        bypassing_coords = list(bypassing.coords)
        origin_coords = list(self._line.coords)
        if (Coord.dist(bypassing_coords[0], origin_coords[-1]) < MATH_EPS
                or Coord.dist(bypassing_coords[-1], origin_coords[0]) < MATH_EPS):
            bypassing = LineString(list(bypassing.coords)[::-1])

        return bypassing
