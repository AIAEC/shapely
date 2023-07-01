from numbers import Real
from typing import Tuple, Union, Iterable, _SpecialGenericAlias

from shapely.extension.typing.geom_typing import PointT, LineStringT, LinearRingT, PolygonT, MultiPointT, \
    MultiLineStringT, MultiPolygonT, GeometryCollectionT, PointTF, LineStringTF, LinearRingTF, PolygonTF, MultiPointTF, \
    MultiLineStringTF, MultiPolygonTF, GeometryCollectionTF
from shapely.extension.util import ordered_set
from shapely.geometry.base import BaseGeometry

Num = Real
CoordType = Union[Tuple[float, float], 'Coord']

GeomObj = Union[BaseGeometry, object]
GeomObjIter = Iterable[GeomObj]

OrderedSetType = _SpecialGenericAlias(ordered_set.OrderedSet, 1)

__all__ = [
    "PointT",
    "PointTF",
    "LineStringT",
    "LineStringTF",
    "LinearRingT",
    "LinearRingTF",
    "PolygonT",
    "PolygonTF",
    "MultiPointT",
    "MultiPointTF",
    "MultiLineStringT",
    "MultiLineStringTF",
    "MultiPolygonT",
    "MultiPolygonTF",
    "GeometryCollectionT",
    "GeometryCollectionTF",
    "Num",
    "CoordType",
    "GeomObj",
    "GeomObjIter",
    "OrderedSetType"
]
