import warnings
from collections.abc import Iterable
from operator import attrgetter
from typing import Union, Optional, Tuple, Callable, Dict

from shapely.affinity import rotate, scale
from shapely.extension.constant import MATH_EPS
from shapely.extension.model.aggregation import Aggregation
from shapely.extension.model.alignment import AlignPolygon, AlignLineString, AlignPoint, BaseAlignMultiPartGeom, \
    BaseAlignGeom
from shapely.extension.model.angle import Angle
from shapely.extension.model.envelope import EnvelopeCreator
from shapely.extension.model.projection import Projection, ProjectionTowards
from shapely.extension.model.stretch import Stretch
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.alignment_predicator_creator import AlignmentPredicatorCreator
from shapely.extension.predicator.angle_predicator_creator import AnglePredicatorCreator
from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.extension.predicator.relation_predicator_creator import RelationPredicatorCreator
from shapely.extension.strategy.angle_strategy import PolygonAngleStrategy, LineAngleStrategy, default_angle_strategy, \
    AngleStrategyType
from shapely.extension.strategy.decompose_strategy import BaseDecomposeStrategy
from shapely.extension.strategy.simplify_strategy import BaseSimplifyStrategy, NativeSimplifyStrategy
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
        self._cargo = {}

    @property
    def cargo(self) -> Dict:
        return self._cargo

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

    def flatten(self, target_class_or_callable: Union[type, Tuple[type], Callable[[BaseGeometry], bool], None] = None,
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

        return flatten(self._geom, target_class_or_callable=target_class_or_callable, validate=validate,
                       filter_valid=filter_valid, filter_out_empty=filter_out_empty)

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
        """
        move current geometry by vector
        Parameters
        ----------
        vector

        Returns
        -------
        moved geometry
        """
        return vector.apply(self._geom)

    def move_to(self, point_or_coord: Union[CoordType, Point], origin: Union[str, Point, CoordType] = 'center'):
        """
        move the 'canvas' to align the origin to given point_or_coord
        Parameters
        ----------
        point_or_coord: Coord | tuple[num, num] | Point instance
        origin: str(center) | Point | Coord | tuple[num, num]

        Returns
        -------
        moved geometry
        """
        origin = self._geom.centroid if origin == 'center' else Point(origin)
        target = Point(point_or_coord)
        return Vector.from_origin_to_target(origin=origin, target=target).apply(self._geom)

    def rotate_ccw(self, angle: float):
        """
        rotate the current geometry around its centroid
        Parameters
        ----------
        angle: ccw angle in degree format

        Returns
        -------
        rotated geometry
        """
        return rotate(self._geom, angle=angle)

    def scale(self, x_ratio: float = 1., y_ratio: float = 1.):
        """
        scale the current geometry from its centroid
        Parameters
        ----------
        x_ratio: float
        y_ratio: float

        Returns
        -------
        scaled geometry
        """
        return scale(self._geom, xfact=x_ratio, yfact=y_ratio)

    def ccw(self):
        """
        make polygon, linearRing and its corresponding multi-geometry ccw, otherwise stay unchanged
        notice: the interiors of polygon will be made cw for correctness
        Returns
        -------

        """
        return ccw(self._geom)

    def connect_path(self, geom: BaseGeometry, direction: Optional[Vector] = None) -> LineString:
        """
        return the shortest connecting linestring
        Parameters
        ----------
        geom: other geometry instance
        direction: the given connecting direction, if none, use the direction for nearest points on both geometries

        Returns
        -------
        shortest connecting linestring
        """
        if not direction:
            return LineString(nearest_points(self._geom, geom))

        return ShortestStraightPath(direction=direction).of(self._geom, geom)

    def difference(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                   self_buffer: Num = 0,
                   component_buffer: Num = 0):
        """
        current geometry difference given geometry or geometries
        Parameters
        ----------
        geom_or_geoms: given geometry(s)
        self_buffer: rect buffer distance of current geometry
        component_buffer: rect buffer distance of given geometry(s)

        Returns
        -------
        geometry or multi-geometry
        """
        self_geom = self._geom
        if self_buffer != 0:
            self_geom = self._geom.buffer(self_buffer, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)

        given_geom_union = unary_union(geom_or_geoms)
        if component_buffer != 0:
            given_geom_union = given_geom_union.buffer(component_buffer,
                                                       cap_style=CAP_STYLE.flat,
                                                       join_style=JOIN_STYLE.mitre)
        return self_geom.difference(given_geom_union)

    def intersection(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                     self_buffer: Num = 0,
                     component_buffer: Num = 0):
        """
        current geometry intersection with given geometry or geometries
        Parameters
        ----------
        geom_or_geoms: given geometry(s)
        self_buffer: rect buffer distance of current geometry
        component_buffer: rect buffer distance of given geometry(s)

        Returns
        -------
        geometry or multi-geometry
        """
        self_geom = self._geom
        if self_buffer != 0:
            self_geom = self._geom.buffer(self_buffer, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)

        given_geom_union = unary_union(geom_or_geoms)
        if component_buffer != 0:
            given_geom_union = given_geom_union.buffer(component_buffer,
                                                       cap_style=CAP_STYLE.flat,
                                                       join_style=JOIN_STYLE.mitre)
        return self_geom.intersection(given_geom_union)

    def is_(self, *conditions: Iterable[str]) -> bool:
        """
        the AND union of several condition for geometry
        Parameters
        ----------
        conditions: for base geometry: 'empty', 'simple', 'valid'; for linestring there are addition: 'ccw', 'ring'

        Returns
        -------
        bool(predicator0 && predicator1 && ..)
        """
        flag = True
        for condition in conditions:
            flag &= attrgetter(f'is_{condition}')(self._geom)
        return flag

    def angle(self, strategy: Optional[AngleStrategyType] = None) -> Angle:
        """
        return the calculated angle of current geometry
        for now, there is no strategy for multi-geometry, use minimum_rotated_rectangle for angle calculation
        parameters
        ----------
        strategy: None or angle strategy object(callable: BaseGeometry -> Num).
            if None, use the default default_angle_strategy.
            polygon strategy creator: PolygonAngleStrategy;
            linestring strategy creator: LineAngleStrategy;
            default strategy: default_angle_strategy;

        Returns
        -------
        angle instance
        """
        if strategy is None:
            strategy = {"Polygon": PolygonAngleStrategy(0).by_bounding_box_width(),
                        "LineString": LineAngleStrategy().end_to_end()}.get(self._geom.type, default_angle_strategy)
        return Angle(strategy(self._geom))

    def simplify(self, strategy: Optional[BaseSimplifyStrategy] = None):
        """
        return the simplified geometry
        Parameters
        ----------
        strategy: None or simplify strategy object(based on BaseSimplifyStrategy).
            if None, use the default DefaultSimplifyStrategy.
            DefaultSimplifyStrategy: use the native simplify method
            BufferSimplifyStrategy: buffer back and forth to simplify

        Returns
        -------
        simplified geometry
        """
        strategy = strategy or NativeSimplifyStrategy()
        return strategy.simplify(self._geom)

    def move_towards(self, geom: BaseGeometry, direction: Optional[Vector] = None, util: Optional = None):
        """
        move the current geometry to hit the given geometry
        Parameters
        ----------
        geom: other geometry
        direction: direction vector, if None, use the direction for nearest points
        util: not implemented

        Returns
        -------
        moved current geometry
        """
        warnings.warn("move_towards's util parameter is not implemented")

        move_vector = Vector.from_endpoints_of(self.connect_path(geom, direction=direction))
        return move_vector.apply(self._geom)

    def projection_towards(self, poly: Polygon, direction: Vector) -> ProjectionTowards:
        """
        project the current geometry onto the given polygon
        Parameters
        ----------
        poly: polygon
        direction: direction vector

        Returns
        -------
        ProjectionTowards that has shadow()
        """
        return Projection(self._geom).towards(poly, direction=direction)

    def distance(self, geom: BaseGeometry, direction: Optional[Vector] = None) -> float:
        """
        enhance the native distance with direction
        Parameters
        ----------
        geom: other geometry
        direction: None or vector, if None, use the native distance

        Returns
        -------
        float
        """
        return self.connect_path(geom, direction).length

    def alignment(self, direction_dist_tol: Num = MATH_EPS,
                  angle_tol: Num = MATH_EPS) -> Union[BaseAlignMultiPartGeom, BaseAlignGeom]:
        """
        return the alignment object.

        Parameters
        ----------
        direction_dist_tol: specify the distance tolerance of the endpoint of direction vector,
        angle_tol: specify the angle tolerance of the direction vector

        Returns
        -------
        instance of BaseAlignGeom or BaseAlignMultiPartGeom
        """
        if self._geom.type == 'Polygon':
            return AlignPolygon(self._geom, origin=self, direction_dist_tol=direction_dist_tol, angle_tol=angle_tol)
        elif self._geom.type == 'Point':
            return AlignPoint(self._geom, origin=self, direction_dist_tol=direction_dist_tol, angle_tol=angle_tol)
        elif self._geom.type in ['LineString', 'LinearRing']:
            return AlignLineString(self._geom, origin=self, direction_dist_tol=direction_dist_tol, angle_tol=angle_tol)

        raise NotImplementedError("MultiPartGeometry has no alignment support yet")

    def f_distance(self) -> DistancePredicatorCreator:
        """
        used for predicating the distance relationship between other geometry and current geometry
        Returns
        -------
        the instance of DistancePredicatorCreator
        """
        return DistancePredicatorCreator(self._geom)

    def f_relation(self) -> RelationPredicatorCreator:
        """
        used for predicating the geometry bool relationship between other geometry and current geometry
        Returns
        -------
        the instance of RelationPredicatorCreator
        """
        return RelationPredicatorCreator(self._geom)

    def f_alignment(self, direction: Optional[Vector] = None,
                    direction_dist_tol: Num = MATH_EPS,
                    angle_tol: Num = MATH_EPS) -> AlignmentPredicatorCreator:
        """
        used for predicating the alignment relationship between other geometry and current geometry
        Parameters
        ----------
        direction:
        direction_dist_tol:
        angle_tol:

        Returns
        -------
        the instance of AlignmentPredicatorCreator
        """
        return AlignmentPredicatorCreator(self._geom,
                                          direction=direction,
                                          direction_dist_tol=direction_dist_tol,
                                          angle_tol=angle_tol)

    def f_angle(self, strategy: Optional[Callable[[BaseGeometry], Num]] = None) -> AnglePredicatorCreator:
        """
        used for predicating the angle relationship between other geometry and current geometry
        Parameters
        ----------
        strategy:

        Returns
        -------

        """
        return AnglePredicatorCreator(self._geom, strategy)

    def almost_intersects(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                          dist_tol: Num = MATH_EPS) -> bool:
        """
        whether current geometry almost intersects with given geom(s)
        Parameters
        ----------
        geom_or_geoms: geometry(s)
        dist_tol: distance tolerance

        Returns
        -------
        bool
        """
        return unary_union(geom_or_geoms).distance(self._geom) <= dist_tol
