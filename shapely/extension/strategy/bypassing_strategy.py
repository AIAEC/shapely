from abc import ABC, abstractmethod
from typing import Union

from shapely.extension.util.line_bypassing import LineBypassing
from shapely.geometry import LineString, GeometryCollection, MultiPolygon, Polygon


class BaseBypassingStrategy(ABC):
    @abstractmethod
    def bypass(self, line: LineString,
               poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection]) -> LineString:
        raise NotImplementedError


class ShorterBypassingStrategy(BaseBypassingStrategy):
    """
    the linestring bypassing strategy that chose the shorter bypass path
    """

    def bypass(self, line: LineString,
               poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection]) -> LineString:
        return LineBypassing(line).bypass(poly_or_multi_poly, chosen_longer_path=False)


class LongerBypassingStrategy(BaseBypassingStrategy):
    """
    the linestring bypassing strategy that choose the longer bypass path
    """

    def bypass(self, line: LineString,
               poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection]) -> LineString:
        return LineBypassing(line).bypass(poly_or_multi_poly, chosen_longer_path=True)
