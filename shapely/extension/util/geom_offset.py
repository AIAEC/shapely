from typing import Optional, List, Set

from shapely.extension.constant import LARGE_ENOUGH_DISTANCE, MATH_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy
from shapely.extension.typing import CoordType
from shapely.extension.util.decompose import decompose
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lconcat, sign
from shapely.extension.util.line_extent import LineExtent
from shapely.geometry import LineString, JOIN_STYLE, Polygon, LinearRing, CAP_STYLE
from shapely.ops import linemerge


def _group_by_line_extent(curves: List[LineString], extent_dist: float = LARGE_ENOUGH_DISTANCE) -> List[LineString]:
    """
    给定一些曲线(相邻的曲线之间可相交亦可不相交), 拉伸/剪裁曲线, 将他们尽可能"联合"在一起, 组成若干曲线组
    :param curves:
    :param extent_dist:
    :return:
    """
    if not curves:
        return []

    groups: List[LineString] = []
    last_curve = curves[0]
    for i in range(1, len(curves)):
        curve = curves[i]
        # 当groups中没有group(说明目前所有的curve都能延展到一起), 且这是最后一条curve, 尝试将首尾 延展起来, 组成一个closed ring
        if ((extent := LineExtent.of_sequence_curves(curve_ab=last_curve,
                                                     curve_cd=curve,
                                                     extent_dist=extent_dist,
                                                     make_closed=(i == len(curves) - 1) and len(groups) == 0))
                and extent.both_extended_curve_valid):

            last_curve = extent.merged_curve
        else:
            groups.append(last_curve)
            last_curve = curve

    if groups and (extent := LineExtent.of_sequence_curves(curve_ab=last_curve,
                                                           curve_cd=groups[0],
                                                           extent_dist=extent_dist)):
        groups[0] = extent.merged_curve
    else:
        groups.append(last_curve)

    return groups


def offset(line: LineString,
           dist: float,
           side: str = 'left',
           invert_coords: bool = False,
           use_pan_if_failed: bool = True,
           eps: float = MATH_EPS) -> Optional[LineString]:
    """
    平移一条linestring. 因为原生的line.parallel_offset方法有时会生成MultiLineString, 这是GEOS的bug

    :param line: 被offset的线
    :param dist: offset的距离
    :param side: offset的方向, 只有'left'和'right'
    :param invert_coords: 是否反转结果的坐标顺序
    :param use_pan_if_failed: 所有方法失败后是否使用暴力平移法作为保底
    :param eps: line做simplify的eps
    :return: linestring或None
    """

    def modify_coords_order_if_use_parallel_offset(_line):
        if ((invert_coords and side == 'left') or
                (not invert_coords and side == 'right')):
            _line = type(_line)(list(_line.coords)[::-1])

        return _line

    def method_for_ring(_line):
        if not _line.is_closed:
            return None

        if not isinstance(_line, LinearRing):
            return None

        whether_do_buffer = _line.is_ccw ^ (side == 'left')
        buffered_poly = Polygon(_line).buffer(dist=sign(whether_do_buffer) * dist,
                                              join_style=JOIN_STYLE.mitre,
                                              cap_style=CAP_STYLE.flat)
        rings = sorted(flatten(buffered_poly, Polygon).to_list(), key=lambda poly: poly.area, reverse=True)

        if rings:
            result = rings[0].exterior
            if result.is_ccw != _line.is_ccw ^ invert_coords:
                result = LinearRing(list(result.coords)[::-1])

            return result

        return None

    def method0(_line):
        # 首先尝试offset简化后的line, 看是否能得到合法的offset line
        _line = _line.parallel_offset(distance=dist, side=side, join_style=JOIN_STYLE.mitre)
        if not isinstance(_line, LineString):
            return None
        return modify_coords_order_if_use_parallel_offset(_line)

    def method1(_line):
        # 尝试把得到的multilinestring进行linemerge, 看是否能得到合法的offset line
        _line = _line.parallel_offset(distance=dist, side=side, join_style=JOIN_STYLE.mitre)
        refactored_offset_line = linemerge(flatten(_line, LineString).to_list())
        if not isinstance(refactored_offset_line, LineString):
            return None
        return modify_coords_order_if_use_parallel_offset(refactored_offset_line)

    def method2(_line):
        # 如果抽取其坐标重构成LineString之后和offset line基本一致, 我们认为重构其坐标得到的linestring就是合法的offset line
        is_line_closed = _line.is_closed
        _line = _line.parallel_offset(distance=dist, side=side, join_style=JOIN_STYLE.mitre)
        coords: List[CoordType] = lconcat(list(l.coords) for l in flatten(_line, LineString).to_list())

        if is_line_closed:
            coords.append(coords[0])

        refactored_offset_line = LineString(coords)
        if not _line.buffer(MATH_EPS).contains(refactored_offset_line):
            return None
        return modify_coords_order_if_use_parallel_offset(refactored_offset_line)

    def method3(_line):
        # 如果半边膨胀得到的linestring和offset line基本一致, 则我们认为半边膨胀的linestring就是合法的offset line
        _line = _line.parallel_offset(distance=dist, side=side, join_style=JOIN_STYLE.mitre)
        coords: List[CoordType] = lconcat(list(l.coords) for l in flatten(_line, LineString).to_list())
        origin_coord_set: Set[CoordType] = set(coords)
        poly = _line.buffer(distance=dist * sign(side == 'left'), single_sided=True)
        poly_ext_coords = list(poly.exterior.coords)

        offset_line_coords_idx_groups: List[List[int]] = []
        cur_idx_group: List[int] = []
        for i, coord in enumerate(poly_ext_coords):
            if coord not in origin_coord_set:
                if len(cur_idx_group) <= 1:
                    cur_idx_group.append(i)
                else:  # len(cur_idx_group) == 2
                    cur_idx_group[1] = i
            else:
                if len(cur_idx_group) > 0:
                    offset_line_coords_idx_groups.append(cur_idx_group)
                    cur_idx_group = []

        if len(offset_line_coords_idx_groups) == 1:
            offset_coords = poly_ext_coords[
                            offset_line_coords_idx_groups[0][0]: offset_line_coords_idx_groups[0][1] + 1]
        else:  # len(offset_line_coords_idx_groups) == 2
            offset_coords = (
                    poly_ext_coords[offset_line_coords_idx_groups[1][0]: offset_line_coords_idx_groups[1][1] + 1] +
                    poly_ext_coords[offset_line_coords_idx_groups[0][0]: offset_line_coords_idx_groups[0][1] + 1])

        refactored_offset_line = LineString(offset_coords)
        if not _line.buffer(MATH_EPS).contains(refactored_offset_line):
            return None

        # don't use modify order function cause this offset line is generated from buffer
        if invert_coords:
            return LineString(list(refactored_offset_line.coords)[::-1])

        return refactored_offset_line

    def method4(_line):
        # 如果我们把_line的每一个直线段都offset之后, 调用group_by_line_extent能够返回一组merged line, 我们认为merged line就是offset line
        lines = decompose(_line, LineString, StraightSegmentDecomposeStrategy())
        offset_segments = [_offset for l in lines if (_offset := offset(l, dist=dist, side=side))]
        groups = _group_by_line_extent(offset_segments)
        if len(groups) != 1:
            return None

        return groups[0]

    def method_force(_line):
        # 实在不行, 使用vector对line进行暴力平移(跟offset效果稍有区别, 因为offset实际上会让线形状发生变化)
        line_vec = Vector.from_endpoints_of(_line)
        offset_vec = line_vec.ccw_perpendicular if side == 'left' else line_vec.cw_perpendicular
        _line = offset_vec.simplify(_line)

        # don't use modify order function cause this offset line is generated from buffer
        if invert_coords:
            return LineString(list(_line.coords)[::-1])

        return _line

    if not line:
        return line

    line = line.simplify(eps)
    extra_method = [method_force] if use_pan_if_failed else []
    for method in [method_for_ring, method0, method1, method2, method3, method4] + extra_method:
        try:
            if result := method(line):
                return result
        except Exception as e:
            pass

    return None
