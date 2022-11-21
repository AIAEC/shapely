from itertools import combinations
from typing import Callable

from shapely.extension.util.decompose import decompose
from shapely.geometry import LineString, Point
from shapely.ops import linemerge

MergeLineStrategy = Callable[[LineString, LineString], LineString]


def native_linemerge(origin_line: LineString, other_line: LineString) -> LineString:
    if other_line.is_empty:
        return origin_line

    merged_lines = linemerge([origin_line, other_line]).ext.decompose(LineString).to_list()
    if len(merged_lines) != 1:
        return origin_line

    return merged_lines[0]


def as_longest_straight_line(origin_line: LineString, other_line: LineString) -> LineString:
    if other_line.is_empty:
        return origin_line

    points = decompose([origin_line, other_line], Point)
    return LineString(max(combinations(points, 2), key=lambda pt_tuple: pt_tuple[0].distance(pt_tuple[1])))
