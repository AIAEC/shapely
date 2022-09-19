from typing import Union, Iterable

from shapely.extension.util.flatten import flatten
from shapely.geometry.base import BaseGeometry


class Stretch:
    def __init__(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]):
        self._geoms = flatten(geom_or_geoms).to_list()
