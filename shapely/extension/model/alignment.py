from abc import ABC, abstractmethod
from functools import cached_property
from operator import attrgetter
from typing import Union, List, Optional

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.typing import Num, GeomObj
from shapely.extension.util.func_util import lmap, lconcat, lfilter
from shapely.geometry import Point, LineString, Polygon


class BaseAlignGeom(ABC):
    @property
    @abstractmethod
    def shape(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def align_point(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def origin(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def direction(self):
        raise NotImplementedError

    @abstractmethod
    def alignable_to(self, other: 'BaseAlignGeom') -> bool:
        raise NotImplementedError

    @abstractmethod
    def vector_to(self, other: 'BaseAlignGeom') -> Vector:
        raise NotImplementedError

    @abstractmethod
    def distance(self, other: 'BaseAlignGeom') -> float:
        raise NotImplementedError


class AlignPoint(BaseAlignGeom):
    def __init__(self, point: Point,
                 direction: Optional[Vector] = None,
                 origin: Optional[GeomObj] = None,
                 direction_dist_tol: Num = MATH_EPS,
                 angle_tol: Num = MATH_EPS):
        self._point = point
        self._direction = direction or Vector(1, 0)
        self._origin = origin or point
        self._direction_dist_tol = direction_dist_tol
        self._angle_tol = angle_tol

    @property
    def align_point(self):
        return self

    @property
    def shape(self):
        return self._point

    @property
    def origin(self):
        return self._origin

    @property
    def direction(self) -> Vector:
        return self._direction

    @direction.setter
    def direction(self, direct: Vector) -> None:
        self._direction = direct

    def alignable_to(self, other: 'BaseAlignGeom') -> bool:
        if not isinstance(other, BaseAlignGeom):
            raise TypeError("only support alignable to BaseAlignGeom")
        self_direction = self.direction.unit()
        other_direction = other.direction.unit()
        return self_direction.parallel_to(other_direction, dist_tol=self._direction_dist_tol, angle_tol=self._angle_tol)

    def assert_align_item_matched(self, other: 'BaseAlignGeom') -> None:
        if not self.alignable_to(other):
            raise ValueError(f'can only align to item that has same direction,'
                             f' given item.direction={other.direction} and self.direction={self.direction}')

    def distance(self, item: 'BaseAlignGeom') -> float:
        return self.vector_to(item).length

    def vector_to(self, item: 'BaseAlignGeom') -> Vector:
        self.assert_align_item_matched(item)

        dist = self.align_point.shape.distance(item.align_point.shape)
        cw_perp_vec = self.direction.cw_perpendicular
        ccw_perp_vec = self.direction.ccw_perpendicular
        connection_angle = Vector.from_origin_to_target(origin=self.align_point.shape,
                                                        target=item.align_point.shape).angle
        if connection_angle.including_angle(cw_perp_vec.angle) < connection_angle.including_angle(
                ccw_perp_vec.angle):
            vector = cw_perp_vec
        else:
            vector = ccw_perp_vec

        length = vector.ray(self.align_point.shape, dist).project(item.align_point.shape)
        return vector.unit(length)


class AlignLineString(BaseAlignGeom):
    def __init__(self, line: LineString,
                 origin: Optional[GeomObj] = None,
                 direction_dist_tol: Num = MATH_EPS,
                 angle_tol: Num = MATH_EPS):
        self._line = line
        self._direction = Vector.from_endpoints_of(self._line)
        self._origin = origin or line
        self._direction_dist_tol = direction_dist_tol
        self._angle_tol = angle_tol

    @property
    def shape(self):
        return self._line

    @property
    def align_point(self):
        return AlignPoint(self._line.centroid,
                          direction=self._direction,
                          origin=self._origin,
                          direction_dist_tol=self._direction_dist_tol,
                          angle_tol=self._angle_tol)

    @property
    def direction(self):
        return self._direction

    @property
    def origin(self):
        return self._origin

    def alignable_to(self, other: 'BaseAlignGeom') -> bool:
        return self.align_point.alignable_to(other)

    def vector_to(self, other: 'BaseAlignGeom') -> Vector:
        return self.align_point.vector_to(other.align_point)

    def distance(self, other: 'BaseAlignGeom') -> float:
        return self.vector_to(other).length


class BaseAlignMultiPartGeom(ABC):
    @property
    @abstractmethod
    def shape(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def origin(self):
        raise NotImplementedError

    @abstractmethod
    def align_points(self, direction: Vector) -> List[AlignPoint]:
        raise NotImplementedError

    @property
    @abstractmethod
    def align_linestrings(self) -> List[AlignLineString]:
        raise NotImplementedError

    @abstractmethod
    def alignable_to(self, other: Union['BaseAlignGeom', 'BaseAlignMultiPartGeom']) -> bool:
        raise NotImplementedError

    @abstractmethod
    def vectors_to(self, other: Union['BaseAlignGeom', 'BaseAlignMultiPartGeom']) -> List[Vector]:
        raise NotImplementedError

    @abstractmethod
    def vectors_from(self, other: Union['BaseAlignGeom', 'BaseAlignMultiPartGeom']) -> List[Vector]:
        raise NotImplementedError

    @abstractmethod
    def distances_to(self, other: Union['BaseAlignGeom', 'BaseAlignMultiPartGeom']) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    def distances_from(self, other: Union['BaseAlignGeom', 'BaseAlignMultiPartGeom']) -> List[float]:
        raise NotImplementedError


class AlignPolygon(BaseAlignMultiPartGeom):
    def __init__(self, poly: Polygon,
                 direction: Optional[Vector] = None,
                 origin: Optional[GeomObj] = None,
                 direction_dist_tol: Num = MATH_EPS,
                 angle_tol: Num = MATH_EPS):
        self._poly = poly
        self._direction = direction
        self._origin = origin
        self._direction_dist_tol = direction_dist_tol
        self._angle_tol = angle_tol

    @property
    def shape(self):
        return self._poly

    @property
    def origin(self):
        return self._origin

    def align_points(self, direction: Vector) -> List[AlignPoint]:
        return lmap(lambda pt: AlignPoint(point=pt,
                                          direction=direction,
                                          origin=self,
                                          direction_dist_tol=self._direction_dist_tol,
                                          angle_tol=self._angle_tol),
                    self._poly.ext.decompose(Point))

    @cached_property
    def align_linestrings(self) -> List[AlignLineString]:
        from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy
        align_lines = lmap(lambda line: AlignLineString(line=line,
                                                        origin=self,
                                                        direction_dist_tol=self._direction_dist_tol,
                                                        angle_tol=self._angle_tol),
                           self._poly.ext.decompose(LineString, StraightSegmentDecomposeStrategy()))

        if self._direction:
            return lfilter(lambda line: self._direction.parallel_to(line.direction,
                                                                    dist_tol=self._direction_dist_tol,
                                                                    angle_tol=self._angle_tol),
                           align_lines)

        return align_lines

    def alignable_to(self, other: Union['BaseAlignGeom', 'AlignPolygon']) -> bool:
        def _alignable_to_point_or_line(_other: 'BaseAlignGeom') -> bool:
            return any(align_edge.alignable_to(_other) for align_edge in self.align_linestrings)

        if isinstance(other, BaseAlignGeom):
            return _alignable_to_point_or_line(other)

        # other is in type AlignPolygon
        return any(_alignable_to_point_or_line(edge) for edge in other.align_linestrings)

    def vectors_to(self, other: Union['BaseAlignGeom', 'AlignPolygon']) -> List[Vector]:
        def _vectors_to_point_or_line(_other: 'BaseAlignGeom'):
            align_edges = filter(_other.alignable_to, self.align_linestrings)
            vectors = [align_edge.vector_to(_other) for align_edge in align_edges]
            return vectors

        def _vectors_to_poly(_other: 'AlignPolygon'):
            vectors = lconcat(_vectors_to_point_or_line(align_line) for align_line in _other.align_linestrings)
            return vectors

        if isinstance(other, BaseAlignGeom):
            return _vectors_to_point_or_line(other)

        return _vectors_to_poly(other)

    def vectors_from(self, other: Union['BaseAlignGeom', 'AlignPolygon']) -> List[Vector]:
        return [vec.invert() for vec in self.vectors_to(other)]

    def distances_to(self, other: Union['BaseAlignGeom', 'AlignPolygon']) -> List[float]:
        return lmap(attrgetter('length'), self.vectors_to(other))

    def distances_from(self, other: Union['BaseAlignGeom', 'AlignPolygon']) -> List[float]:
        return lmap(attrgetter('length'), self.vectors_from(other))
