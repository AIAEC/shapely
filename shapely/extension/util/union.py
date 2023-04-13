from typing import List

from shapely.extension.constant import MATH_EPS
from shapely.extension.util.legalize import legalize
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE
from shapely.ops import unary_union


def tol_union(geom_list: List[BaseGeometry], eps: float = MATH_EPS):
    """
    先把所有的geom用eps分别buffer一下，再union到一起，然后simplify，再用-eps buffer回来

    :param geom_list: 要融合的List[BaseGeometry]
    :param eps: 融合距离阈值
    :return: 融合成一个之后的geom
    """
    buffered_geom_list = [geom.buffer(eps, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre) for geom in geom_list]
    geom_union = unary_union(buffered_geom_list)
    return legalize(geom_union.simplify(eps).buffer(-eps, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre))
