from typing import Union, Iterable

from shapely.geometry.base import BaseGeometry


class Stretch:
    def __init__(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]):
        if isinstance(geom_or_geoms, BaseGeometry):
            geom_or_geoms = [geom_or_geoms]
        self._geoms = sum([geom.ext.flatten() for geom in geom_or_geoms], start=[])
