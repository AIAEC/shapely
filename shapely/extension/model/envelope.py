from collections.abc import Sequence
from itertools import product
from typing import Tuple, Optional, Union, Callable

from shapely.affinity import rotate
from shapely.extension.model.angle import Angle
from shapely.extension.typing import CoordType, Num
from shapely.extension.util.easy_enum import EasyEnum
from shapely.extension.util.func_util import lmap
from shapely.geometry import Point, Polygon, LineString, MultiPoint
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


class PointPosition(EasyEnum):
    # TODO(WIP): add comment
    LEFT_BOTTOM = 'left_bottom'
    MID_BOTTOM = 'mid_bottom'
    RIGHT_BOTTOM = 'right_bottom'
    LEFT_HORIZON = 'left_horizon'
    MID_HORIZON = 'mid_horizon'
    RIGHT_HORIZON = 'right_horizon'
    LEFT_TOP = 'left_top'
    MID_TOP = 'mid_top'
    RIGHT_TOP = 'right_top'


class EdgePosition(EasyEnum):
    # TODO(WIP): add comment
    LEFT = 'left'
    MID = 'mid'
    RIGHT = 'right'
    BOTTOM = 'bottom'
    HORIZON = 'horizon'
    TOP = 'top'


class HalfEdgePosition(EasyEnum):
    LEFT_BTM_TO_MID_BTM = 'left_bottom->mid_bottom'
    MID_BTM_TO_MID_HOR = 'mid_bottom->mid_horizon'
    MID_HOR_TO_LEFT_HOR = 'mid_horizon->left_horizon'
    LEFT_HOR_TO_LEFT_BTM = 'left_horizon->left_bottom'

    MID_BTM_TO_RIGHT_BTM = 'mid_bottom->right_bottom'
    RIGHT_BTM_TO_RIGHT_HOR = 'right_bottom->right_horizon'
    RIGHT_HOR_TO_MID_HOR = 'right_horizon->mid_horizon'
    MID_HOR_TO_MID_BTM = 'mid_horizon->mid_bottom'

    MID_HOR_TO_RIGHT_HOR = 'mid_horizon->right_horizon'
    RIGHT_HOR_TO_RIGHT_TOP = 'right_horizon->right_top'
    RIGHT_TOP_TO_MID_TOP = 'right_top->mid_top'
    MID_TOP_TO_MID_HOR = 'mid_top->mid_horizon'

    LEFT_HOR_TO_MID_HOR = 'left_horizon->mid_horizon'
    MID_HOR_TO_MID_TOP = 'mid_horizon->mid_top'
    MID_TOP_TO_LEFT_TOP = 'mid_top->left_top'
    LEFT_TOP_TO_LEFT_HOR = 'left_top->left_horizon'


class DiagonalPosition(EasyEnum):
    FROM_LEFT_BOTTOM = 'left_bottom'
    FROM_LEFT_TOP = 'left_top'


class HalfDiagonalPosition(EasyEnum):
    LEFT_BOT_TO_MID_HOR = 'left_bottom->mid_horizon'
    MID_HOR_TO_RIGHT_TOP = 'mid_horizon->right_top'
    LEFT_TOP_TO_MID_HOR = 'left_top->mid_horizon'
    MID_HOR_TO_RIGHT_BOT = 'mid_horizon->right_bottom'


class Envelope:
    def __init__(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
                 angle: Optional[Union[Num, Angle]] = None):
        self._angle = self._setup_angle(geom_or_geoms, angle)
        (self.left_bottom,
         self.right_bottom,
         self.right_top,
         self.left_top) = self._setup_endpoints(geom_or_geoms, self._angle)
        self.mid_bottom = self._mid_point(self.left_bottom, self.right_bottom)
        self.left_horizon = self._mid_point(self.left_top, self.left_bottom)
        self.right_horizon = self._mid_point(self.right_top, self.right_bottom)
        self.mid_horizon = self._mid_point(self.left_horizon, self.right_horizon)
        self.mid_top = self._mid_point(self.left_top, self.right_top)

    def _setup_endpoints(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]], angle: Angle):
        geom = unary_union(geom_or_geoms) if isinstance(geom_or_geoms, Sequence) else geom_or_geoms
        rotate_center = geom.centroid
        # rotate geom to x-y axis aligned direction to calculate the bounding points
        x_min, y_min, x_max, y_max = rotate(geom, angle=-angle.degree, origin=rotate_center).bounds
        multi_point = MultiPoint([Point(x_min, y_min), Point(x_max, y_min), Point(x_max, y_max), Point(x_min, y_max)])
        # rotate multi-point back to origin direction
        return list(rotate(multi_point, angle=angle.degree, origin=rotate_center).geoms)

    def _setup_angle(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
                     angle: Union[Num, Angle]) -> Angle:
        # if given angle, then return this angle
        if angle is not None:
            return Angle(angle)

        # if not given angle, return calculate the angle of the geometry
        if isinstance(geom_or_geoms, Point):
            return Angle(0)

        if isinstance(geom_or_geoms, (LineString, Polygon)):
            return geom_or_geoms.ext.angle()

        # use the minimumn rotated rectangle's angle as its angle
        return unary_union(geom_or_geoms).minimum_rotated_rectangle.ext.angle()

    @property
    def shape(self) -> Polygon:
        return Polygon([self.left_bottom, self.right_bottom, self.right_top, self.left_top])

    @property
    def angle(self) -> Angle:
        return self._angle

    def _mid_point(self, point0: Point, point1: Point) -> Point:
        return Point((point0.x + point1.x) / 2, (point0.y + point1.y) / 2)

    def point(self, position: PointPosition) -> Point:
        # TODO(WIP): add docstring here
        return getattr(self, position.value)

    def coord(self, idx_or_position: Union[int, PointPosition]) -> CoordType:
        return self.point(idx_or_position).coords[0]

    def edge(self, position: EdgePosition) -> LineString:
        """
        返回矩形的边
        注意：边的方向总是从矩形的左边开始到矩形右边结束
        """
        vertical_choices = ['left', 'right', 'mid']
        horizontal_choices = ['bottom', 'top', 'horizon']

        if position.value in vertical_choices:
            vertical_choices = {position.value}
            horizontal_choices.remove('horizon')
        elif position.value in horizontal_choices:
            horizontal_choices = {position.value}
            vertical_choices.remove('mid')

        return LineString([getattr(self, f'{v}_{h}') for v, h in product(list(vertical_choices),
                                                                         list(horizontal_choices))])

    def half_edge(self, position: HalfEdgePosition) -> LineString:
        # TODO(WIP): add docstring here, notice the linestring direction
        start, end = position.value.split('->')
        start_point = getattr(self, start)
        end_point = getattr(self, end)
        return LineString([start_point, end_point])

    def diagonal(self, position: DiagonalPosition) -> LineString:
        if position == DiagonalPosition.FROM_LEFT_BOTTOM:
            return LineString([self.left_bottom, self.right_top])
        return LineString([self.left_top, self.right_bottom])

    def half_diagonal(self, position: HalfDiagonalPosition) -> LineString:
        start, end = position.value.split('->')
        start_point = getattr(self, start)
        end_point = getattr(self, end)
        return LineString([start_point, end_point])

    @property
    def longer_length(self) -> Num:
        return max(self.edge(EdgePosition.BOTTOM).length, self.edge(EdgePosition.LEFT).length)

    @property
    def shorter_length(self) -> Num:
        return min(self.edge(EdgePosition.BOTTOM).length, self.edge(EdgePosition.LEFT).length)

    @property
    def aspect_ratio(self) -> Num:
        if self.longer_length == 0:
            return float('inf')
        return self.shorter_length / self.longer_length

    @property
    def longer_edges(self) -> Tuple[LineString, LineString]:
        if self.edge(EdgePosition.BOTTOM).length > self.edge(EdgePosition.LEFT).length:
            return self.edge(EdgePosition.BOTTOM), self.edge(EdgePosition.TOP)
        return self.edge(EdgePosition.LEFT), self.edge(EdgePosition.RIGHT)

    @property
    def shorter_edges(self) -> Tuple[LineString, LineString]:
        if self.edge(EdgePosition.BOTTOM).length <= self.edge(EdgePosition.LEFT).length:
            return self.edge(EdgePosition.BOTTOM), self.edge(EdgePosition.TOP)
        return self.edge(EdgePosition.LEFT), self.edge(EdgePosition.RIGHT)

    @property
    def longer_mid_line(self) -> LineString:
        if self.edge(EdgePosition.MID).length > self.edge(EdgePosition.HORIZON).length:
            return self.edge(EdgePosition.MID)
        return self.edge(EdgePosition.HORIZON)

    @property
    def shorter_mid_line(self) -> LineString:
        if self.edge(EdgePosition.MID).length <= self.edge(EdgePosition.HORIZON).length:
            return self.edge(EdgePosition.MID)
        return self.edge(EdgePosition.HORIZON)


class EnvelopeCreator:
    def __init__(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry], object, Sequence[object]],
                 attr_getter: Optional[Callable[[object], BaseGeometry]] = None):
        geoms = geom_or_geoms if isinstance(geom_or_geoms, Sequence) else [geom_or_geoms]
        if attr_getter:
            geoms = lmap(attr_getter, geoms)
        if not all(isinstance(geom, BaseGeometry) for geom in geoms):
            raise TypeError('geom_or_geoms is not geometry or geometry sequence, or attr_getter cannot get geometry'
                            'from given object or object sequence')
        self._geoms = geoms

    def of_angle(self, ccw_angle: Optional[Num] = None) -> Envelope:
        """
        create Envelope of given angle
        Parameters
        ----------
        ccw_angle: None or Num, if None, it will use the default angle 0

        Returns
        -------
        instance of Envelope
        """
        return Envelope(self._geoms, angle=ccw_angle or 0)

    def tightened(self) -> Envelope:
        """
        create the smallest Envelope, in most cases its shape is equal to the minimum rotated rectangle
        Returns
        -------
        instance of Envelope
        """
        return Envelope(self._geoms)
