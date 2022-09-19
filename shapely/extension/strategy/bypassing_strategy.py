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
    def bypass(self, line: LineString,
               poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection]) -> LineString:
        return LineBypassing(line).bypass(poly_or_multi_poly, chosen_longer_path=False)


class LongerBypassingStrategy(BaseBypassingStrategy):
    def bypass(self, line: LineString,
               poly_or_multi_poly: Union[Polygon, MultiPolygon, GeometryCollection]) -> LineString:
        return LineBypassing(line).bypass(poly_or_multi_poly, chosen_longer_path=True)
