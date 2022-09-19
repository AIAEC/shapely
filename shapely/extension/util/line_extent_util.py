from operator import attrgetter
from typing import List, Optional

from functional import seq

from shapely.extension.constant import LARGE_ENOUGH_DISTANCE
from shapely.extension.util.line_extent import LineExtent
from shapely.geometry import LineString, LinearRing, Polygon
from shapely.validation import make_valid


def closed_ring_rebuild(
        curves: List[LineString], extent_dist: float = LARGE_ENOUGH_DISTANCE) -> Optional[LinearRing]:
    """
    给定一些曲线(相邻曲线之间可相交亦可以不相交), 拉伸/剪裁 这些曲线, 将他们"联合"在一起组合成一个闭合的LinearRing
    :param curves: 待组合成多边形的曲线, 这些曲线的坐标顺序必须一致(ccw或cw均可)
    :param extent_dist: 最大拉伸距离, 默认为LARGE_ENOUGH_DISTANCE
    :return: extend过后的curves组成的linear ring, 若失败, 返回None
    """
    if not curves:
        return None

    merged_curve = curves[0]
    for i in range(1, len(curves)):
        curve = curves[i]
        if extent := LineExtent.of_sequence_curves(curve_ab=merged_curve,
                                                   curve_cd=curve,
                                                   extent_dist=extent_dist,
                                                   make_closed=(i == len(curves) - 1)):
            merged_curve = extent.merged_curve

    if merged_curve and not Polygon(merged_curve).is_valid:
        return make_valid(Polygon(merged_curve)).ext.flatten(Polygon).max_by(attrgetter('area')).exterior
    return merged_curve


def group_by_line_extent(curves: List[LineString],
                         extent_dist: float = LARGE_ENOUGH_DISTANCE,
                         parallel_as_separate_group: bool = False) -> List[LineString]:
    """
    给定一些曲线(相邻的曲线之间可相交亦可不相交), 拉伸/剪裁曲线, 将他们尽可能"联合"在一起, 组成若干曲线组
    :param curves: 多条曲线或直线
    :param extent_dist: 为了融合曲线而尝试延伸的距离
    :param parallel_as_separate_group: 是否将延伸后重合的曲线或直线看做两个不同组的
    :return:
    """
    if not curves:
        return []

    groups: List[LineString] = []
    last_curve = curves[0]
    for i in range(1, len(curves)):
        cur_curve = curves[i]
        line_extent = LineExtent.of_sequence_curves(curve_ab=last_curve,
                                                    curve_cd=cur_curve,
                                                    extent_dist=extent_dist,
                                                    make_closed=(i == len(curves) - 1) and len(groups) == 0,
                                                    ignore_parallel=parallel_as_separate_group)

        if not line_extent or not line_extent.both_extended_curve_valid:
            # last_curve doesn't connect with cur_curve after extending, we save last_curve
            # and reset last_curve to cur_curve
            groups.append(last_curve)
            last_curve = cur_curve
        else:
            # last_curve and cur_curve connect, meaning that cur_curve can merge into last_curve
            last_curve = line_extent.merged_curve

    if groups and (extent := LineExtent.of_sequence_curves(curve_ab=last_curve,
                                                           curve_cd=groups[0],
                                                           extent_dist=extent_dist,
                                                           ignore_parallel=parallel_as_separate_group)):
        groups[0] = extent.merged_curve
    else:
        groups.append(last_curve)

    return groups
