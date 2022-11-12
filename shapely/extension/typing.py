from numbers import Real
from typing import Tuple, Union, Iterable, _SpecialGenericAlias

from shapely.extension.util import ordered_set
from shapely.geometry.base import BaseGeometry

Num = Real
CoordType = Union[Tuple[float, float], 'Coord']

GeomObj = Union[BaseGeometry, object]
GeomObjIter = Iterable[GeomObj]

OrderedSetType = _SpecialGenericAlias(ordered_set.OrderedSet, 1)
