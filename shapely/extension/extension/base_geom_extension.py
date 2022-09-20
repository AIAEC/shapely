import warnings
from collections.abc import Iterable
from operator import attrgetter
from typing import Union, Optional, Tuple, Callable

from shapely.affinity import rotate, scale
from shapely.extension.constant import MATH_EPS
from shapely.extension.model.aggregation import Aggregation
from shapely.extension.model.alignment import AlignPolygon, AlignLineString, AlignPoint
from shapely.extension.model.angle import Angle
from shapely.extension.model.envelope import EnvelopeCreator
from shapely.extension.model.projection import Projection, ProjectionTowards
from shapely.extension.model.stretch import Stretch
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.alignment_predicator_creator import AlignmentPredicatorCreator
from shapely.extension.predicator.angle_predicator_creator import AnglePredicatorCreator
from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.extension.predicator.relation_predicator_creator import RelationPredicatorCreator
from shapely.extension.strategy.angle_strategy import PolygonAngleStrategy, LineAngleStrategy, default_angle_strategy
from shapely.extension.strategy.decompose_strategy import BaseDecomposeStrategy
from shapely.extension.strategy.simplify_strategy import BaseSimplifyStrategy, DefaultSimplifyStrategy
from shapely.extension.typing import CoordType, Num
from shapely.extension.util.ccw import ccw
from shapely.extension.util.decompose import decompose
from shapely.extension.util.divide import divide
from shapely.extension.util.flatten import flatten
from shapely.extension.util.shortest_path import ShortestStraightPath
from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE
from shapely.ops import nearest_points, unary_union


class BaseGeomExtension:
    def __init__(self, geom):
        self._geom = geom

    def stretch(self) -> Stretch:
        return Stretch(self._geom)

    def decompose(self, target_class: type, strategy: Optional[BaseDecomposeStrategy] = None) -> Aggregation:
        """
        decompose current geometry into lower dimensional geometries
        Parameters
        ----------
        target_class: target class of decomposing process. If the target class has dimension higher than current
            geometry, it will return the aggregation of current geometry immediately
        strategy: decompose strategy instance that specify the rule of decomposing

        Returns
        -------
        aggregation object of decomposed geometry instances
        """
        return Aggregation(decompose(self._geom, target_class=target_class, strategy=strategy))

    def flatten(self, target_class_or_callable: Union[type, Tuple[type], Callable[[BaseGeometry], bool]],
                validate: bool = True,
                filter_valid: bool = True,
                filter_out_empty: bool = True) -> Aggregation:
        """
        flatten current geometry into singular geometry list and filter it using various filter

        Parameters
        ----------
        target_class_or_callable: filter geometry that matches the given target class or satisfy the filter callable
        validate: make geometry valid if it's invalid, before any filtering
        filter_valid: filter geometry that are valid
        filter_out_empty: filter geometry that are empty

        Returns
        -------
        aggregation object of singular geometry instances
        """

        return flatten(self._geom,
                       target_class_or_callable=target_class_or_callable,
                       validate=validate,
                       filter_valid=filter_valid,
                       filter_out_empty=filter_out_empty)

    def envelope(self) -> EnvelopeCreator:
        """
        enter envelope creation process
        Returns
        -------
        object that has several methods to create envelope
        """
        return EnvelopeCreator(self._geom)

    def divided_by(self, line_or_lines: Union[LineString, Iterable[LineString], MultiLineString],
                   dist_tol: Num = MATH_EPS) -> Aggregation:
        """
        divide current geometry by linestring(s) or multi-linestring. If you want to do divide by other types of geometry
        use difference instead
        Parameters
        ----------
        line_or_lines: linestring(s) or multi-linestring
        dist_tol: maximum snapping distance for divider's ends attaching to current geometry's boundary

        Returns
        -------
        aggregation of divided geometries
        """
        return Aggregation(divide(self._geom, divider=line_or_lines, dist_tol=dist_tol))

    def move_by(self, vector: Vector):
        return vector.apply(self._geom)

    def move_to(self, point_or_coord: Union[CoordType, Point], origin: Union[str, Point, CoordType] = 'center'):
        origin = self._geom.centroid if origin == 'center' else Point(origin)
        target = Point(point_or_coord)
        return Vector.from_origin_to_target(origin=origin, target=target).apply(self._geom)

    def rotate_ccw(self, angle_degree: float):
        return rotate(self._geom, angle=angle_degree)

    def scale(self, x_ratio: float = 1., y_ratio: float = 1.):
        return scale(self._geom, xfact=x_ratio, yfact=y_ratio)

    def ccw(self):
        return ccw(self._geom)

    def connect_path(self, geom: BaseGeometry, direction: Optional[Vector] = None) -> LineString:
        if not direction:
            return LineString(nearest_points(self._geom, geom))

        return ShortestStraightPath(direction=direction).of(self._geom, geom)

    def difference(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                   self_buffer: Num = 0, component_buffer: Num = 0):
        self_geom = self._geom.buffer(self_buffer, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)
        given_geom_union = unary_union(geom_or_geoms).buffer(component_buffer,
                                                             cap_style=CAP_STYLE.flat,
                                                             join_style=JOIN_STYLE.mitre)
        return self_geom.difference(given_geom_union)

    def intersection(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                     self_buffer: Num = 0, other_buffer: Num = 0):
        self_geom = self._geom.buffer(self_buffer, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)
        given_geom_union = unary_union(geom_or_geoms).buffer(other_buffer,
                                                             cap_style=CAP_STYLE.flat,
                                                             join_style=JOIN_STYLE.mitre)
        return self_geom.intersection(given_geom_union)

    def is_(self, *conditions: Iterable[str]):
        flag = True
        for condition in conditions:
            flag &= attrgetter(f'is_{condition}')(self._geom)
        return flag

    def angle(self, strategy: Optional[Callable[[BaseGeometry], Num]] = None) -> Angle:
        if strategy is None:
            strategy = {"Polygon": PolygonAngleStrategy(0).by_bounding_box_width(),
                        "LineString": LineAngleStrategy().end_to_end()}.get(self._geom.type, default_angle_strategy)
        return Angle(strategy(self._geom))

    def simplify(self, strategy: Optional[BaseSimplifyStrategy] = None):
        strategy = strategy or DefaultSimplifyStrategy()
        return strategy.simplify(self._geom)

    def move_towards(self, geom: BaseGeometry, direction: Optional[Vector] = None, util: Optional = None):
        warnings.warn("move_towards's util parameter is not implemented")

        move_vector = Vector.from_endpoints_of(self.connect_path(geom, direction=direction))
        return move_vector.apply(self._geom)

    def projection_towards(self, poly: Polygon, direction: Vector) -> ProjectionTowards:
        return Projection(self._geom).towards(poly, direction=direction)

    def distance(self, geom: BaseGeometry, direction: Optional[Vector] = None):
        return self.connect_path(geom, direction).length

    def alignment(self, direction_dist_tol: Num = MATH_EPS):
        if self._geom.type == 'Polygon':
            return AlignPolygon(self._geom, origin=self, direction_dist_tol=direction_dist_tol)
        elif self._geom.type == 'Point':
            return AlignPoint(self._geom, origin=self, direction_dist_tol=direction_dist_tol)
        elif self._geom.type in ['LineString', 'LinearRing']:
            return AlignLineString(self._geom, origin=self, direction_dist_tol=direction_dist_tol)

        raise NotImplementedError("MultiPartGeometry has no alignment support yet")

    def f_distance(self) -> DistancePredicatorCreator:
        return DistancePredicatorCreator(self._geom)

    def f_relation(self) -> RelationPredicatorCreator:
        return RelationPredicatorCreator(self._geom)

    def f_alignment(self, direction: Optional[Vector] = None,
                    direction_dist_tol: Num = MATH_EPS) -> AlignmentPredicatorCreator:
        return AlignmentPredicatorCreator(self._geom, direction=direction, direction_dist_tol=direction_dist_tol)

    def f_angle(self, strategy: Optional[Callable[[BaseGeometry], Num]] = None) -> AnglePredicatorCreator:
        return AnglePredicatorCreator(self._geom, strategy)

    def almost_intersects(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                          dist_tol: Num = MATH_EPS) -> bool:
        return unary_union(geom_or_geoms).distance(self._geom) <= dist_tol
