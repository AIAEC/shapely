from collections.abc import Sequence
from typing import Union, Iterable, List, Tuple, Callable

from shapely.extension.model.aggregation import Aggregation
from shapely.extension.util.func_util import lconcat
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.validation import make_valid

__all__ = ['flatten']


def _flatten_helper(geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]) -> List[BaseGeometry]:
    """
    展平。对于各种数据结构的BaseGeometry以及BaseMultipartGeometry统一展平成list形式的BaseGeometry

    :param geom_or_geoms: 需要判断的BaseGeometry，也可以是Iterable
    :return: 返回满足条件的list形式的geom
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
            filter_valid: bool = True,
            validate: bool = True,
            filter_out_empty: bool = True) -> Aggregation:
    """
    展平并过滤geom

    :param geom_or_geoms: 需要判断的BaseGeometry。也可以是Iterable
    :param target_class_or_callable: 过滤的目标类型。也可以是一个判定函数进行过滤
    :param filter_valid: 是否过滤非法geometry
    :param make_valid: 是否需要标准化
    :param filter_out_empty: 是否需要清除（过滤掉）空geometry
    :return: 返回满足条件的list形式的geom
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
