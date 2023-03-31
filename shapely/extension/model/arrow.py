import math
from itertools import chain
from typing import Optional, List, Tuple, Callable, Union

from shapely.extension.constant import MATH_EPS, MATH_MIDDLE_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.extension.util.union import tol_union
from shapely.geometry import LineString, Polygon, Point
from shapely.geometry.base import BaseGeometry


class Arrow:
    def __init__(self, coordinates: Optional[Union[List[CoordType], List[Point]]] = None,
                 coords_widths: Optional[List[Tuple[float, float]]] = None):
        """
                                              │\
                   ┌──────────────────────────┤ \
                   └──────────────────────────┤ / ◄────────
                 ▲                            │/       end point
                 │                           ▲       s_w: half of head width
           start point                       │       e_w: unused
        s_w: unused                   turning point
        e_w: half of shaft width     s_w: half of shaft width
                                     e_w: half of head width

        The number of coordinates and coords_widths should be kept constant
        :param coordinates:
        :param coords_widths: list[(start_width, end_width)]
        """
        self._coordinates = coordinates or []
        self._coords_width_data = coords_widths or []

    def _validate(self):
        if len(self._coordinates) < 1:
            raise ValueError("Arrow must have at least 1 coordinate tuples")
        if len(self._coordinates) != len(self._coords_width_data):
            raise ValueError("Likely cause is invalidity of the geometry ")

    @property
    def shape(self) -> BaseGeometry:
        self._validate()
        if len(self._coordinates) < 2:
            return Point(self._coordinates[0])
        return tol_union(self._component_shape(), eps=MATH_MIDDLE_EPS)

    @property
    def is_closed(self) -> bool:
        self._validate()
        return self.axis.is_closed

    @property
    def axis(self) -> Union[Point, LineString]:
        self._validate()
        if len(self._coordinates) < 2:
            return Point(self._coordinates[0])
        return LineString(self._coordinates)

    @property
    def coords(self) -> List[CoordType]:
        self._validate()
        return self._coordinates

    def arrow_direction(self) -> List[Vector]:
        """Arrow pointing direction"""
        self._validate()
        if len(self._coordinates) < 2:
            return []

        arrow_vectors: List[Vector] = []
        for coord_index in range(1, len(self._coordinates)):
            pre_coord = self._coordinates[coord_index - 1]
            cur_coord = self._coordinates[coord_index]
            start_width = self._coords_width_data[coord_index - 1][0]
            end_width = self._coords_width_data[coord_index][1]
            if math.isclose(start_width, end_width, abs_tol=MATH_EPS):
                continue
            elif start_width > end_width:
                arrow_vectors.append(Vector.from_origin_to_target(pre_coord, cur_coord))
            else:
                arrow_vectors.append(Vector.from_origin_to_target(cur_coord, pre_coord))
        return arrow_vectors

    def heads(self) -> List[Polygon]:
        self._validate()
        return self._component_shape(lambda width0, width1: math.isclose(width0, width1, abs_tol=MATH_EPS))

    def shafts(self) -> List[Polygon]:
        self._validate()
        return self._component_shape(lambda width0, width1: not math.isclose(width0, width1, abs_tol=MATH_EPS))

    def _component_shape(self, filter_func: Optional[Callable[[float, float], bool]] = None) -> List[Polygon]:
        arrow_component: List[Polygon] = []

        arrow_coords: List[CoordType] = self._coordinates
        coord_datas: List[Tuple[float, float]] = self._coords_width_data
        for index in range(1, len(arrow_coords)):
            cur_vector = Vector.from_origin_to_target(arrow_coords[index - 1], arrow_coords[index])
            ccw_vector = cur_vector.ccw_perpendicular
            cw_vector = cur_vector.cw_perpendicular
            pre_width = coord_datas[index - 1][0] / 2
            cur_width = coord_datas[index][1] / 2
            if filter_func is not None and filter_func(pre_width, cur_width):
                continue
            left_coords = ([ccw_vector.unit(pre_width).apply_coord(arrow_coords[index - 1]),
                            ccw_vector.unit(cur_width).apply_coord(arrow_coords[index])])
            right_coords = ([cw_vector.unit(pre_width).apply_coord(arrow_coords[index - 1]),
                             cw_vector.unit(cur_width).apply_coord(arrow_coords[index])])
            arrow_component.append(Polygon(chain(reversed(left_coords), right_coords)))
        return arrow_component
