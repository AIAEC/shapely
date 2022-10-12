from abc import abstractmethod, ABC
from operator import truth
from typing import Union, Sequence, Callable, List

import numpy as np

from shapely.extension.model.coord import Coord
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lconcat
from shapely.extension.util.iter_util import win_slice, first
from shapely.geometry import MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection, Point
from shapely.geometry.base import BaseGeometry


class BaseDecomposeStrategy(ABC):
    def handler(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> Callable:
        return {MultiPoint: self.multipoint_to_point,
                LineString: self.linestring_to_multipoint,
                MultiLineString: self.multilinestring_to_linestring,
                Polygon: self.polygon_to_multilinestring,
                MultiPolygon: self.multipolygon_to_polygons}.get(self.type_of(geom_or_geoms), self.empty_handler)

    @staticmethod
    def decompose_order() -> List[type]:
        return [GeometryCollection, MultiPolygon, Polygon, MultiLineString, LineString, MultiPoint, Point]

    @classmethod
    def decomposing_index(cls, type_) -> int:
        try:
            return cls.decompose_order().index(type_)
        except:
            return len(cls.decompose_order())

    def can_be_handled(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> bool:
        try:
            return self.handler(geom_or_geoms) != self.empty_handler
        except:
            return False

    @staticmethod
    def empty_handler(_):
        return _

    @staticmethod
    def type_of(geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]):
        geom = geom_or_geoms
        if isinstance(geom_or_geoms, Sequence):
            if not geom_or_geoms:
                return None
            geom = list(geom_or_geoms)[0]
        return type(geom)

    @abstractmethod
    def multipolygon_to_polygons(
            self, multi_poly_or_polys: Union[MultiPolygon, Sequence[MultiPolygon]]) -> List[Polygon]:
        raise NotImplementedError

    @abstractmethod
    def polygon_to_multilinestring(self, poly_or_polys: Union[Polygon, Sequence[Polygon]]) -> List[MultiLineString]:
        raise NotImplementedError

    @abstractmethod
    def multilinestring_to_linestring(
            self, multi_line_or_lines: Union[MultiLineString, Sequence[MultiLineString]]) -> List[LineString]:
        raise NotImplementedError

    @abstractmethod
    def linestring_to_multipoint(self, line_or_lines: Union[LineString, Sequence[LineString]]) -> List[MultiPoint]:
        raise NotImplementedError

    @abstractmethod
    def multipoint_to_point(self, multi_point_or_points: Union[MultiPoint, Sequence[MultiPoint]]) -> List[Point]:
        raise NotImplementedError


class DefaultDecomposeStrategy(BaseDecomposeStrategy):
    """
    default decompose strategy
    """

    def multipolygon_to_polygons(
            self, multi_poly_or_polys: Union[MultiPolygon, Sequence[MultiPolygon]]) -> List[Polygon]:
        multi_polys = multi_poly_or_polys if isinstance(multi_poly_or_polys, Sequence) else [multi_poly_or_polys]
        return lconcat(multi_poly.geoms for multi_poly in multi_polys)

    def polygon_to_multilinestring(self, poly_or_polys: Union[Polygon, Sequence[Polygon]]) -> List[MultiLineString]:
        polys = poly_or_polys if isinstance(poly_or_polys, Sequence) else [poly_or_polys]

        multi_linestrings: List[MultiLineString] = []
        for poly in polys:
            # strip the duplicate tail point for linearRing
            lines = [LineString(list(line.coords)) for line in flatten(poly.boundary).to_list()]
            multi_linestrings.append(MultiLineString(lines))

        return multi_linestrings

    def multilinestring_to_linestring(
            self, multi_line_or_lines: Union[MultiLineString, Sequence[MultiLineString]]) -> List[LineString]:
        multi_lines = multi_line_or_lines if isinstance(multi_line_or_lines, Sequence) else [multi_line_or_lines]
        return lconcat(multi_line.geoms for multi_line in multi_lines)

    def linestring_to_multipoint(self, line_or_lines: Union[LineString, Sequence[LineString]]) -> List[MultiPoint]:
        lines = line_or_lines if isinstance(line_or_lines, Sequence) else [line_or_lines]
        multi_points: List[MultiPoint] = []
        for line in lines:
            multi_points.append(MultiPoint([Point(coord) for coord in line.coords]))
        return multi_points

    def multipoint_to_point(self, multi_point_or_points: Union[MultiPoint, Sequence[MultiPoint]]) -> List[Point]:
        multi_points = multi_point_or_points if isinstance(multi_point_or_points, Sequence) else [multi_point_or_points]
        return lconcat([multi_point.geoms for multi_point in multi_points])


class StraightSegmentDecomposeStrategy(DefaultDecomposeStrategy):
    """
    decompose strategy that cut multi-linestring into straight segments
    """

    def multilinestring_to_linestring(
            self, multi_line_or_lines: Union[MultiLineString, Sequence[MultiLineString]]) -> List[LineString]:
        multi_lines = multi_line_or_lines if isinstance(multi_line_or_lines, Sequence) else [multi_line_or_lines]

        straight_segments: List[LineString] = []
        for line in lconcat(multi_line.geoms for multi_line in multi_lines):
            straight_segments.extend([LineString(coords) for coords in win_slice(line.coords,
                                                                                 win_size=2,
                                                                                 tail_cycling=False,
                                                                                 head_cycling=False)])

        return straight_segments


class CurveDecomposeStrategy(DefaultDecomposeStrategy):
    """
    decompose strategy that cut multi-linestring into linestrings according to its turning angle
    """

    def __init__(self, min_cutting_angle: float):
        """
        Parameters
        ----------
        min_cutting_angle: angle degree, if turning angle larger than this, it will be a cutting point
        """
        self._min_cutting_angle = float(min_cutting_angle)

    def multilinestring_to_linestring(
            self, multi_line_or_lines: Union[MultiLineString, Sequence[MultiLineString]]) -> List[LineString]:
        multi_lines = multi_line_or_lines if isinstance(multi_line_or_lines, Sequence) else [multi_line_or_lines]

        def cutting_point(coord0, coord1, coord2) -> bool:
            return Coord.angle(coord0, coord1).including_angle(Coord.angle(coord1, coord2)) > self._min_cutting_angle

        def slice(list_, start, inclusive_end):
            if start <= inclusive_end:
                return list_[start: inclusive_end + 1]
            return list_[start:] + list_[:inclusive_end + 1]

        result: List[LineString] = []

        for line in lconcat(multi_line.geoms for multi_line in multi_lines):
            line_coords = list(line.coords)
            if line.is_ring:  # remove duplicate tail coordinate
                line_coords.pop()

            coords_3_tuple = win_slice(line_coords, win_size=3, tail_cycling=line.is_ring)

            # whether on we should cut on coord the index below
            cutting_coord_indices = [cutting_point(*triple_coords) for triple_coords in coords_3_tuple]
            if line.is_ring:
                # since cutting_point calculate the angle on coord1, thus we should right pan the cutting_coord_idx
                # in order to make it align on right coordinate indices
                cutting_coord_idxs = np.roll(cutting_coord_indices, 1)
            else:
                cutting_coord_idxs = [True, *cutting_coord_indices, True]

            if not any(cutting_coord_idxs):
                result.append(line)
                continue

            # start from first cutting coord and slice from start(last start idx) to end(i) inclusively
            start_idx = first(truth, cutting_coord_idxs, return_idx=True)
            last_start_idx = start_idx
            i = (last_start_idx + 1) % len(line_coords)

            while i != start_idx:
                if cutting_coord_idxs[i]:
                    if coords := slice(line_coords, last_start_idx, i):
                        result.append(LineString(coords))
                    last_start_idx = i
                i = (i + 1) % len(line_coords)

            if line.is_ring and (coords := slice(line_coords, last_start_idx, i)):
                result.append(LineString(coords))

        return result
