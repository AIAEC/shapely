import math
from functools import partial
from operator import itemgetter
from typing import Optional, Callable

from shapely.extension.model.angle import Angle
from shapely.extension.model.coord import Coord
from shapely.extension.util.easy_enum import EasyEnum
from shapely.extension.util.func_util import group
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry

AngleStrategyType = Callable[[Polygon], float]


class PolygonAngleStrategy:
    """
    polygon angle strategy factory
    """

    def __init__(self, default_angle: float):
        self._default = default_angle

    def by_prevailing_edge(self, same_angle_tol: float = 2) -> AngleStrategyType:
        """
        return angle strategy for polygon that using prevail edges' average angle as the angle of the polygon.
        it will do statistics through all edges and pick the angle cluster that has the longest edge length sum.
        Parameters
        ----------
        same_angle_tol: angle degree tolerance that one angle cluster holds

        Returns
        -------
        angle strategy instance for polygon angle calculation
        """

        def _angle_calculator(polygon: Polygon) -> float:
            if not isinstance(polygon, Polygon):
                polygon = polygon.convex_hull

            if not polygon.is_valid:
                polygon = polygon.minimum_rotated_rectangle

            polygon = polygon.simplify(0)

            if polygon.is_empty:
                return self._default

            coords = list(polygon.exterior.coords)[:-1]

            if len(coords) <= 1:
                return self._default

            radian_length_map = {}
            from shapely.extension.model.vector import Vector
            for i in range(len(coords)):
                radian = Vector.from_origin_to_target(coords[i - 1], coords[i]).angle.radian
                length = Coord.dist(coords[i - 1], coords[i])
                radian_length_map[radian] = radian_length_map.get(radian, 0) + length

            if not radian_length_map:
                return self._default

            radian_length_groups = group(
                grouping_func=lambda pair1, pair2: abs(pair1[0] - pair2[0]) < Angle(same_angle_tol).radian,
                items=list(radian_length_map.items()))

            main_angle = self._default
            max_length = float('-inf')
            for radian_length_group in radian_length_groups:
                angle_radian_average = sum(map(itemgetter(0), radian_length_group)) / len(radian_length_group)
                length_sum = sum(map(itemgetter(1), radian_length_group))

                if length_sum > max_length:
                    max_length = length_sum
                    main_angle = math.degrees(angle_radian_average)

            return main_angle

        return _angle_calculator

    def by_bounding_box_width(self) -> AngleStrategyType:
        """
        return angle strategy for polygon that using minimum_rotated_rectangle's angle as its angle

        Returns
        -------
        angle strategy instance for polygon angle calculation
        """

        def _angle_calculator(polygon: Polygon):
            bounding_box = polygon.minimum_rotated_rectangle.simplify(0)

            if not isinstance(bounding_box, Polygon):
                return self._default

            box_coords = list(bounding_box.exterior.coords)

            longest_edge_len: float = 0
            longest_edge_angle: Optional[float] = None

            from shapely.extension.model.vector import Vector
            for coord0, coord1 in win_slice(box_coords, win_size=2):
                if (edge_len := Coord.dist(coord0, coord1)) >= longest_edge_len:
                    longest_edge_len = edge_len
                    longest_edge_angle = Vector.from_origin_to_target(coord0, coord1).angle.degree

            return longest_edge_angle or self._default

        return _angle_calculator


class LineAngleStrategy:
    """
    angle strategy creator for linestring
    """

    class LineCalMode(EasyEnum):
        AVERAGE = 'average'  # 按线条的每两个坐标的角度,平权求平均
        END_TO_END = 'end_to_end'  # 首尾两个坐标构成线段的角度

    def _angle_calculator(self, line: LineString, cal_mode: LineCalMode) -> float:
        """
        calculate the angle of the given linestring

        Parameters
        ----------
        line: linestring
        cal_mode: LineCalMode instance

        Returns
        -------
        angle degree in float
        """
        if not line.is_valid:
            raise ValueError("input line is not a valid lineString")

        if line.is_empty:
            return self.default

        coords = list(line.coords)

        if cal_mode == self.LineCalMode.END_TO_END:
            coord_pairs = [(coords[0], coords[-1])]
        else:
            coord_pairs = [(coords[i - 1], coords[i]) for i in range(1, len(coords))]

        angle: float = 0
        total_length: float = 0
        for coord_pair in coord_pairs:
            cur_pair_length = math.sqrt((coord_pair[0][0] - coords[1][0]) ** 2 +
                                        (coord_pair[0][1] - coords[1][1]) ** 2)
            total_length += cur_pair_length
            angle += Coord.angle(*coord_pair) * cur_pair_length

        return angle / total_length

    def end_to_end(self) -> AngleStrategyType:
        """
        create angle strategy for linestring that use its endpoints only to calculate the angle
        Returns
        -------
        angle strategy instance for linestring
        """
        return partial(self._angle_calculator, cal_mode=self.LineCalMode.END_TO_END)

    def average(self) -> AngleStrategyType:
        """
        create angle strategy for linestring that use average angle of each straight segments of it as the angle
        Returns
        -------
        angle strategy instance for linestring
        """
        return partial(self._angle_calculator, cal_mode=self.LineCalMode.AVERAGE)


def default_angle_strategy(geom: BaseGeometry) -> float:
    """
    default angle calculate strategy. use its minimum_rotated_rectangle's angle as its angle
    Parameters
    ----------
    geom: any geometry instance

    Returns
    -------
    angle strategy for any geometry
    """
    rect = geom.minimum_rotated_rectangle
    if isinstance(rect, Polygon):
        return float(PolygonAngleStrategy(0).by_bounding_box_width()(rect))
    elif isinstance(rect, LineString):
        return float(LineAngleStrategy().end_to_end()(rect))
    return 0
