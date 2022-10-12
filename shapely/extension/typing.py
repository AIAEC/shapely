from numbers import Real
from typing import Tuple, Union, Iterable

from shapely.geometry.base import BaseGeometry

Num = Real
CoordType = Union[Tuple[float, float], 'Coord']

GeomObj = Union[BaseGeometry, object]
GeomObjIter = Iterable[GeomObj]
