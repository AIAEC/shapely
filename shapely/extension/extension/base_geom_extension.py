from collections.abc import Iterable
from operator import attrgetter
from typing import Union, Optional, Tuple, Callable, Dict, Sequence, List, Literal

from shapely.affinity import rotate, scale
from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry.arc import Arc
from shapely.extension.model.aggregation import Aggregation
from shapely.extension.model.alignment import AlignPolygon, AlignLineString, AlignPoint, BaseAlignMultiPartGeom, \
    BaseAlignGeom
from shapely.extension.model.angle import Angle
from shapely.extension.model.buffer import Buffer
from shapely.extension.model.envelope import EnvelopeCreator
from shapely.extension.model.mould import mould
from shapely.extension.model.projection import Projection, ProjectionTowards
from shapely.extension.model.raster import DEFAULT_SCALE_FACTOR, RasterFactory
from shapely.extension.model.skeleton import Skeleton, CgalSkeleton
from shapely.extension.model.skeleton.base_skeleton import BaseSkeleton
from shapely.extension.model.skeleton.botffy_skeleton import BotffySkeleton
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.extension.predicator.relation_predicator_creator import RelationPredicatorCreator
from shapely.extension.strategy.angle_strategy import PolygonAngleStrategy, LineAngleStrategy, default_angle_strategy, \
    AngleStrategyType
from shapely.extension.strategy.decompose_strategy import BaseDecomposeStrategy
from shapely.extension.strategy.simplify_strategy import BaseSimplifyStrategy, NativeSimplifyStrategy
from shapely.extension.typing import CoordType
from shapely.extension.util.ccw import ccw
from shapely.extension.util.decompose import decompose
from shapely.extension.util.divide import divide
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lmap
from shapely.extension.util.insertion.inserter import raster_inserter
from shapely.extension.util.legalize import legalize
from shapely.extension.util.shortest_path import ShortestStraightPath
from shapely.extension.util.similar import similar
from shapely.geometry import Point, LineString, MultiLineString, Polygon, GeometryCollection, MultiPolygon
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE
from shapely.ops import unary_union


class BaseGeomExtension:
    def __init__(self, geom):
        self._geom = geom
        self._cargo = {}

    @property
    def cargo(self) -> Dict:
        return self._cargo

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

    def largest_piece(self) -> Polygon:
        """
        flatten current geometry and return the one with largest area
        Returns
        -------
        largest polygon part of this geom or Polygon()
        """
        return flatten(self._geom, target_class_or_callable=Polygon).max_by(attrgetter('area'), default=Polygon())

    def envelope(self) -> EnvelopeCreator:
        """
        enter envelope creation process
        Returns
        -------
        object that has several methods to create envelope
        """
        return EnvelopeCreator(self._geom)

    def buffer(self) -> Buffer:
        return Buffer(self._geom)

    def rbuf(self, distance: float, single_sided=False, mitre_limit=5.0) -> BaseGeometry:
        return Buffer(self._geom, single_sided=single_sided).rect(dist=distance, mitre_limit=mitre_limit)

    def divided_by(self, line_or_lines: Union[LineString, Iterable[LineString], MultiLineString],
                   dist_tol: float = MATH_EPS) -> Aggregation:
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
        if isinstance(line_or_lines, Sequence):
            line_or_lines = unary_union(line_or_lines)
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

    def rotate_ccw(self, angle: float, origin='center'):
        """
        rotate the current geometry around its centroid
        Parameters
        ----------
        origin :The point of origin can be a keyword 'center' for the bounding box center (default),
        'centroid' for the geometry's centroid, a Point object or a coordinate tuple (x0, y0).
        angle: ccw angle in degree format

        Returns
        -------
        rotated geometry
        """
        return rotate(self._geom, angle=angle, origin=origin)

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

    def connect_path(self, geom: BaseGeometry,
                     direction: Optional[Vector] = None,
                     dist_tol: float = MATH_EPS,
                     bidirect: bool = True) -> LineString:
        """
        return the shortest connecting linestring
        Parameters
        ----------
        geom: other geometry instance
        direction: the given connecting direction, if none, use the direction for nearest points on both geometries
        bidirect: whether search in direction and its invert direction

        Returns
        -------
        shortest connecting linestring
        """
        return ShortestStraightPath(direction=direction, dist_tol=dist_tol).of(self._geom, geom, bidirect=bidirect)

    def difference(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                   self_buffer: float = 0,
                   component_buffer: float = 0):
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
                     self_buffer: float = 0,
                     component_buffer: float = 0):
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
        intersection_result = []
        self_geom = self._geom
        if self_buffer != 0:
            self_geom = self._geom.buffer(self_buffer, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)

        geoms = geom_or_geoms if isinstance(geom_or_geoms, Iterable) else [geom_or_geoms]
        if component_buffer != 0:
            geoms = lmap(lambda _geom: _geom.buffer(component_buffer,
                                                    cap_style=CAP_STYLE.flat,
                                                    join_style=JOIN_STYLE.mitre),
                         geoms)
        for _geom in geoms:
            if isinstance(_geom, Arc):
                intersection_result.append(_geom.intersection(self_geom))
            else:
                intersection_result.append(self_geom.intersection(_geom))

        return unary_union(intersection_result)

    def is_(self, *conditions: Iterable[str]) -> bool:
        """
        the AND union of several condition for geometry
        Parameters
        ----------
        conditions: for base geometry: 'empty', 'simple', 'valid'; for linestring there are addition: 'ccw', 'ring'
        add not_ as prefix to set negative conditions: 'not_empty'

        Returns
        -------
        bool(predicator0 && predicator1 && ..)
        """
        flag = True
        for condition in conditions:
            if str(condition).startswith("not_"):
                flag &= not attrgetter(f'is_{str(condition[4:])}')(self._geom)
            else:
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
                        "LineString": LineAngleStrategy(0).end_to_end()}.get(self._geom.type, default_angle_strategy)
        return Angle(strategy(self._geom))

    def simplify(self, strategy: Optional[BaseSimplifyStrategy] = None) -> List[BaseGeometry]:
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
        if geom.intersection(self._geom):
            return 0

        path = self.connect_path(geom, direction)
        if not path:
            return float('inf')

        return path.length

    def alignment(self, direction_dist_tol: float = MATH_EPS,
                  angle_tol: float = MATH_EPS) -> Union[BaseAlignMultiPartGeom, BaseAlignGeom]:
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

    def almost_intersects(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]],
                          dist_tol: float = MATH_EPS) -> bool:
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
        if not self._geom:
            return False
        union_geoms = unary_union(geom_or_geoms)
        if not union_geoms:
            return False
        return union_geoms.distance(self._geom) <= dist_tol

    def similar(self, geom: BaseGeometry, area_diff_tol: float) -> bool:
        """
        whether is similar to given geometry in area difference tolerance
        Parameters
        ----------
        geom: geometry instance
        area_diff_tol: tolerance of area difference

        Returns
        -------
        bool
        """
        return similar(self._geom, geom, area_diff_tol=area_diff_tol)

    def skeleton(self, type_: Literal["cgal", "botffy", "auto"] = "auto") -> BaseSkeleton:
        """
        generate the skeleton of given geometry
        Returns
        -------
        skeleton object
        """
        if type_ == 'cgal':
            return CgalSkeleton(self._geom)
        elif type_ == 'botffy':
            return BotffySkeleton(self._geom)

        return Skeleton(self._geom)

    def legalize(self) -> BaseGeometry:
        """
        make invalid geometry valid
        Returns
        ----------
        valid geometry
        """
        return legalize(self._geom)

    def mould(self, margin: float = 1.0) -> Union[Polygon, MultiPolygon, GeometryCollection]:
        return mould(self._geom, margin=margin)

    def raster(self, scale_factor: float = DEFAULT_SCALE_FACTOR):
        return RasterFactory(scale_factor).from_geom(self._geom)

    def insertion(self, geom: BaseGeometry,
                  inserter: Optional[Callable[[BaseGeometry], List[BaseGeometry]]] = None) -> List[BaseGeometry]:
        """
        find all possible space in geom to insert self._geom
        rect_insertion should be used when self._geom is a rectangle, otherwise may return an unwilling result
        raster_insertion can deal with more shape, but will have a loss of precision
        """
        if not inserter:
            inserter = raster_inserter(insert_geom=self._geom, scale_factor=DEFAULT_SCALE_FACTOR)
        return inserter(obstacle=geom)
