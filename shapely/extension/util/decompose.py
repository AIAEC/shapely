from collections.abc import Sequence
from typing import Optional, List, Union

from shapely.extension.strategy.decompose_strategy import DefaultDecomposeStrategy
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import groupby, separate, be_type
from shapely.geometry import GeometryCollection
from shapely.geometry.base import BaseGeometry


def decompose(geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
              target_class: type,
              strategy: Optional[DefaultDecomposeStrategy] = None) -> List:
    """
    Decompose the given geom or geoms according to decomposing order.

    NOTICE: If given geom or geoms has decomposing order > target class, then it will immediately return given geoms
    (which might collect from geom)

    Decomposing order:
    GeometryCollection
    --> MultiPolygon
    --> Polygon
    --> MultiLineString
    --> LineString
    --> MultiPoint
    --> Point

    Parameters
    ----------
    geom_or_geoms
    target_class
    strategy

    Returns
    -------
    list of geometry instance of target class
    """
    strategy = strategy or DefaultDecomposeStrategy()

    # unify the input parameter to iterable
    geoms = geom_or_geoms if isinstance(geom_or_geoms, Sequence) else [geom_or_geoms]

    def _decompose_single_type(geoms: Union[BaseGeometry, Sequence[BaseGeometry]], target_class: type):
        while (strategy.decomposing_index(strategy.type_of(geoms)) < strategy.decomposing_index(target_class)
               and strategy.can_be_handled(geoms)):
            geoms = strategy.handler(geoms)(geoms)

        return geoms

    # pick those geometry collections out, flatten it and add result back to geoms
    # since there's no strategy for geometry collection
    geom_collects, geoms = separate(be_type(GeometryCollection), geoms)
    geoms.extend(flatten(geom_collects).to_list())

    result = []
    for gs in groupby(type, geoms).values():
        result.extend(_decompose_single_type(gs, target_class=target_class))

    return result
