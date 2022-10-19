from collections.abc import Sequence
from typing import Union, Iterable, List, Tuple, Callable

from shapely.extension.model import Aggregation
from shapely.extension.util.func_util import lconcat
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.validation import make_valid

__all__ = ['flatten']


def _flatten_helper(geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]) -> List[BaseGeometry]:
    """
    对于各种数据结构的BaseGeometry以及BaseMultipartGeometry统一展平成list形式的BaseGeometry
    Parameters
    ----------
    geom_or_geoms: geometry(s)

    Returns
    -------
    list of singular geometries
    """
    if isinstance(geom_or_geoms, BaseGeometry) and not isinstance(geom_or_geoms, BaseMultipartGeometry):
        return [geom_or_geoms]

    if isinstance(geom_or_geoms, BaseMultipartGeometry):
        return lconcat(_flatten_helper(g) for g in geom_or_geoms.geoms)

    if isinstance(geom_or_geoms, Sequence):
        return lconcat(_flatten_helper(g) for g in geom_or_geoms)

    return []


def flatten(geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
            target_class_or_callable: Union[type, Tuple[type], Callable[[BaseGeometry], bool]] = None,
            validate: bool = True,
            filter_valid: bool = True,
            filter_out_empty: bool = True) -> Aggregation:
    """
    flatten and filter, return the aggregation of geometry instances
    Parameters
    ----------
    geom_or_geoms: geometry(s)
    target_class_or_callable: geometry class or filter function
    validate: bool, whether do make_valid to make singular geometry valid
    filter_valid: bool, whether return only the valid geometry
    filter_out_empty: bool, whether filter out the empty geometry

    Returns
    -------
    Aggregation of geometry instances
    """

    def fit(geom):
        if target_class_or_callable is None:
            return True

        if isinstance(target_class_or_callable, (list, tuple)):
            return isinstance(geom, target_class_or_callable)

        if type(target_class_or_callable).__name__ == 'type' and issubclass(target_class_or_callable, BaseGeometry):
            # given Geometry type
            return isinstance(geom, target_class_or_callable)

        return callable(target_class_or_callable) and target_class_or_callable(geom)

    geoms = Aggregation(_flatten_helper(geom_or_geoms))
    if validate:
        geoms = geoms.flat_map(lambda g: _flatten_helper(make_valid(g)))

    geoms = geoms.filter(fit)
    if filter_valid:
        geoms = geoms.filter(lambda g: g.is_valid)

    if filter_out_empty:
        geoms = geoms.filter_not(lambda g: g.is_empty)

    return geoms
