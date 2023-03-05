import math
from collections.abc import Iterable as IterableType
from contextlib import suppress
from copy import deepcopy
from operator import attrgetter
from typing import Sequence, Tuple, Union, Optional, List, Iterable as IterableTyping, Callable

from shapely.affinity import translate
from shapely.extension.constant import MATH_EPS
from shapely.extension.model.angle import Angle
from shapely.extension.typing import Num, CoordType, GeomObj, GeomObjIter
from shapely.geometry import Point, LineString
from shapely.geometry.base import BaseGeometry


class Vector:
    """
    vector in 2D space. vector is mostly used as direction denotation or moving applier. it can also be used as angle
    calculator in some case.
    """

    def __init__(self, x: float = 0., y: float = 0.):
        """
        init a vector instance

        Parameters
        ----------
        x: number type(int, float)
        y: number type(int, float)
        """
        if not (isinstance(x, Num) and isinstance(y, Num)):
            if isinstance(x, Sequence):
                x, y, *_ = x
            elif isinstance(x, dict):
                x, y = x['x'], x['y']
            else:
                raise TypeError(f'x, y should only be number, given x={x}, y={y}')

        self.x = x
        self.y = y

    def __repr__(self):
        return f"vector({self.x}, {self.y})"

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __hash__(self):  # __eq__ has been created by dataclass internally
        return hash(('vector', self.x, self.y))

    def __bool__(self):
        return not (self.x == 0 and self.y == 0)

    def __reduce__(self):
        return type(self), (self.x, self.y)

    def __abs__(self):
        return self.length

    def __iter__(self):
        return iter([self.x, self.y])

    @classmethod
    def zero(cls) -> 'Vector':
        """
        Returns
        -------
        zero vector
        """
        return Vector(0, 0)

    @classmethod
    def from_tuple(cls, num_tuple: CoordType) -> 'Vector':
        """
        create vector from tuple of two number values

        Parameters
        ----------
        num_tuple: tuple[num, num]

        Returns
        -------
        vector(tuple[0], tuple[1])
        """
        if not cls._is_coord(num_tuple):
            raise ValueError(f'{num_tuple} is not valid number tuple for vector creation')
        return cls(num_tuple[0], num_tuple[1])

    @classmethod
    def from_point(cls, point: Point) -> 'Vector':
        return cls(point.x, point.y)

    @classmethod
    def from_origin_to_target(cls, origin: Union[CoordType, Point], target: Union[CoordType, Point]) -> 'Vector':
        """
        create vector from origin to target

        Parameters
        ----------
        origin: Coordinate or Point
        target: Coordinate or Point

        Returns
        -------
        vector from origin to target
        """
        if not (cls._is_coord(origin) or isinstance(origin, Point)):
            raise ValueError(f"{origin} is not valid coordinate or point")
        if not (cls._is_coord(target) or isinstance(target, Point)):
            raise ValueError(f"{target} is not valid coordinate or point")

        if isinstance(origin, Point):
            origin = origin.coords[0]
        if isinstance(target, Point):
            target = target.coords[0]

        return cls(x=target[0] - origin[0], y=target[1] - origin[1])

    @classmethod
    def from_angle(cls, angle_degree: float = 0.0, length: float = 1.0) -> 'Vector':
        """
        create vector has specific angle and length

        Parameters
        ----------
        angle_degree: angle in degree
        length: length of the vector

        Returns
        -------
        vector
        """
        radian = math.radians(angle_degree)
        to_x: float = math.cos(radian) * length
        to_y: float = math.sin(radian) * length
        return cls.from_origin_to_target((0, 0), (to_x, to_y))

    @classmethod
    def from_endpoints_of(cls, linestring: LineString) -> 'Vector':
        """
        create vector from start point of the given linestring to the end point
        Parameters
        ----------
        linestring: linestring

        Returns
        -------
        vector
        """
        if not linestring.is_valid or linestring.is_empty:
            raise ValueError("input linestring is invalid or empty")
        coords = list(linestring.coords)
        return cls.from_origin_to_target(coords[0], coords[-1])

    @property
    def length(self) -> float:
        """
        Returns
        -------
        float, the length of the vector
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def unit(self, n_unit: float = 1) -> 'Vector':
        """
        return the unit vector of current vector

        Parameters
        ----------
        n_unit: the basic length of 1 unit

        Returns
        -------
        vector
        """
        length = self.length
        if length == 0:
            raise ValueError('zero vector has no unit vector')
        return Vector(n_unit * self.x / length, n_unit * self.y / length)

    def __eq__(self, other: 'Vector') -> bool:
        self.assert_vector_type(other)
        return self.x == other.x and self.y == other.y

    def almost_equal(self, other: 'Vector', dist_tol: float = 1e-6) -> bool:
        """
        predicate whether given vector is almost equal to current vector

        Parameters
        ----------
        other: other vector given
        dist_tol: the tolerance of Euclidean distance between current vector and given vector

        Returns
        -------
        bool
        """
        self.assert_vector_type(other)
        return (self - other).length <= float(dist_tol)

    def __lt__(self, other: 'Vector') -> bool:
        return tuple(self) < tuple(other)

    def __gt__(self, other: 'Vector') -> bool:
        return tuple(self) > tuple(other)

    @property
    def angle(self) -> 'Angle':
        """
        return the angle of current vector
        Returns
        -------
        Angle instance
        """
        return Angle.atan2(self.y, self.x)

    def ray(self, origin: Union[Point, CoordType], length: float = 1e9) -> LineString:
        """
        return linestring that goes along the vector from the given origin

        Parameters
        ----------
        origin: point or coordinate
        length: float, default to a large enough value(1e16)

        Returns
        -------
        linestring
        """
        if isinstance(origin, Point):
            origin = origin.coords[0]

        vector = self.unit().multiply(length)
        return LineString([origin, vector.apply_coord(origin)])

    @property
    def ccw_perpendicular(self) -> 'Vector':
        """
        Returns
        -------
        vector that rotate 90 degree in counter clockwise
        """
        perpendicular_vector = type(self)(x=-self.y, y=self.x)
        return perpendicular_vector

    @property
    def cw_perpendicular(self) -> 'Vector':
        """
        Returns
        -------
        vector that rotate 90 degree in clockwise
        """
        return self.ccw_perpendicular.invert()

    def perpendicular_to(self, other: 'Vector', dist_tol: float = MATH_EPS, angle_tol: float = MATH_EPS) -> bool:
        """
        return whether perpendicular to given vector. return True if it satisfies any tolerance

        Parameters
        ----------
        other: vector
        dist_tol
        angle_tol

        Returns
        -------
        bool
        """
        return abs(self @ other) < dist_tol or self.angle.perpendicular_to(other.angle, angle_tol=float(angle_tol))

    def parallel_to(self, other: 'Vector', dist_tol: float = MATH_EPS, angle_tol: float = MATH_EPS):
        """
        return whether parallel to given vector. 2 vectors are parallel even when they are in inverse direction.
        return True if it satisfies any tolerance.

        Parameters
        ----------
        other: vector
        dist_tol
        angle_tol

        Returns
        -------

        """
        return abs(self.cross_prod(other)) < dist_tol or self.angle.parallel_to(other.angle, angle_tol=float(angle_tol))

    def rotate(self, ccw_angle_degree: float) -> 'Vector':
        """
        return vector that rotate given angle degree in counter clockwise

        Parameters
        ----------
        ccw_angle_degree: the angle that returned vector rotated from current vector

        Returns
        -------
        vector
        """

        return Vector.from_angle(angle_degree=self.angle.degree + ccw_angle_degree, length=self.length)

    def invert(self) -> 'Vector':
        """
        Returns
        -------
        the reversed vector
        """
        return Vector(-self.x, -self.y)

    @property
    def slope(self) -> float:
        """
        Returns
        -------
        float, slope, namely the value of y / x. when x == 0, return infinite
        """
        return self.y / self.x if self.x != 0 else float('inf')

    def _apply_to_obj(self, geom_obj: object, attr_getter: attrgetter, apply_method: Callable):
        """
        use to implement apply and apply_coord, handle attr_getter and move geometry inside geom_obj

        Parameters
        ----------
        geom_obj: object that contains geometry instance
        attr_getter: callable that given object return a BaseGeometry instance
        apply_method: method that calculate new geometry from the origin geometry

        Returns
        -------
        new instance in type same as geom_obj, with geometry instance modified
        """
        attr_getter_parameters: Tuple[str] = attr_getter.__reduce__()[1]

        geom_obj_copy = deepcopy(geom_obj)
        origin_geoms = attr_getter(geom_obj_copy)
        if not isinstance(origin_geoms, IterableType):
            origin_geoms = [origin_geoms]

        for attr_path, origin_geom in zip(attr_getter_parameters, origin_geoms):
            # attr_path is a string with format 'a.b.c' or 'a' for simple case
            # after rsplit, 'a.b.c' -> ['a.b', 'c'], 'a' -> ['a']
            attr_path_parts: List[str] = attr_path.rsplit('.', maxsplit=1)

            # attr_path_parts is a list that can only have 1 or 2 item
            if len(attr_path_parts) > 1:  # attr_path_parts have 2 item
                sub_obj_path = attr_path_parts[0]
                changing_obj = attrgetter(sub_obj_path)(geom_obj_copy)
            else:  # attr_path_parts have 1 item
                changing_obj = geom_obj_copy

            if field_name := attr_path_parts[-1]:
                with suppress(Exception):
                    setattr(changing_obj, field_name, apply_method(origin_geom))

        return geom_obj_copy

    def apply(self, geom_obj: Union[GeomObj, GeomObjIter], attr_getter: Optional[attrgetter] = None):
        """
        use vector to move geometry

        Parameters
        ----------
        geom_obj: BaseGeometry instance or object that contains any BaseGeometry instance as its field
        attr_getter: callable that given object return a BaseGeometry instance, default to None

        Returns
        -------
        instance with same type as given geom_obj, and its geometry changed
        """
        if isinstance(geom_obj, BaseGeometry):
            return translate(geom_obj, xoff=self.x, yoff=self.y)
        elif isinstance(geom_obj, Sequence):
            return type(geom_obj)([self.apply(obj) for obj in geom_obj])

        # must be an object, in this case, attr_getter must be specified
        if not attr_getter:
            raise ValueError('if given geom_obj is an object(not instance of BaseGeometry), attrgetter must be given')

        return self._apply_to_obj(geom_obj=geom_obj, attr_getter=attr_getter, apply_method=self.apply)

    def apply_coord(self, coord_obj: Union[CoordType, IterableTyping[CoordType], object],
                    attr_getter: Optional[attrgetter] = None):
        """
        use vector to move 2D coordinates

        Parameters
        ----------
        coord_obj
        attr_getter

        Returns
        -------
        instance with same type as given geom_obj, and its coordinates changed
        """
        if self._is_coord(coord_obj):
            return coord_obj[0] + self.x, coord_obj[1] + self.y
        elif isinstance(coord_obj, IterableType):
            return type(coord_obj)([self.apply_coord(item) for item in coord_obj])

        # must be an object, in this case, attr_getter must be specified
        if not attr_getter:
            raise ValueError('if given geom_obj is an object(not instance of BaseGeometry), attrgetter must be given')

        return self._apply_to_obj(geom_obj=coord_obj, attr_getter=attr_getter, apply_method=self.apply_coord)

    @staticmethod
    def _is_coord(seq) -> bool:
        return (isinstance(seq, IterableType)
                and len(seq) == 2
                and isinstance(seq[0], Num)
                and isinstance(seq[1], Num))

    def multiply(self, multiple: float) -> 'Vector':
        """
        multiple vector by scalar number

        Parameters
        ----------
        multiple: number

        Returns
        -------
        new vector
        """
        return Vector(self.x * multiple, self.y * multiple)

    def __mul__(self, other: float):
        if not isinstance(other, Num):
            raise TypeError(f'expect vector * num, given {other}')
        return self.multiply(other)

    def __rmul__(self, other: float):
        if not isinstance(other, Num):
            raise TypeError(f'expect vector * num, given {other}')
        return self.multiply(other)

    def __imul__(self, other: float):
        if not isinstance(other, Num):
            raise TypeError(f'expect vector * num, given {other}')

        self.x *= other
        self.y *= other
        return self

    def __truediv__(self, other: float):
        if not isinstance(other, Num) or other == 0:
            return self

        return self.multiply(1 / other)

    def cross(self, _) -> 'Vector':
        """
        for 2D vector, any 2 vectors have cross vector being zero vector

        Parameters
        ----------
        _: other vector

        Returns
        -------
        zero vector
        """
        return self.zero()

    def cross_prod(self, other: 'Vector') -> float:
        """
        calculate the cross product(a scalar) of 2 vectors

        Parameters
        ----------
        other: other vector

        Returns
        -------
        a number
        """
        return self.x * other.y - self.y * other.x

    @classmethod
    def assert_vector_type(cls, possible_vector):
        """
        assert valid vector type

        Parameters
        ----------
        possible_vector: object

        Returns
        -------
        None
        """
        if not isinstance(possible_vector, cls):
            raise TypeError(f"{possible_vector} is of type {type(possible_vector)}, expect Vector")

    def dot(self, other: 'Vector') -> float:
        """
        calculate 2 vector dot product

        Parameters
        ----------
        other: other vector

        Returns
        -------
        a number
        """
        self.assert_vector_type(other)
        return self.x * other.x + self.y * other.y

    def __matmul__(self, other: 'Vector') -> float:
        return self.dot(other)

    def __rmatmul__(self, other: 'Vector') -> float:
        return self.dot(other)

    def plus(self, other: 'Vector') -> 'Vector':
        """
        vector plus vector

        Parameters
        ----------
        other: another vector

        Returns
        -------
        a vector
        """
        self.assert_vector_type(other)
        return Vector(self.x + other.x, self.y + other.y)

    def __add__(self, other: 'Vector') -> 'Vector':
        self.assert_vector_type(other)

        return self.plus(other)

    def __radd__(self, other: 'Vector') -> 'Vector':
        self.assert_vector_type(other)

        return self.plus(other)

    def __iadd__(self, other: 'Vector') -> 'Vector':
        self.assert_vector_type(other)

        self.x += other.x
        self.y += other.y
        return self

    def sub(self, other: 'Vector') -> 'Vector':
        """
        vector subtract vector

        Parameters
        ----------
        other: another vector

        Returns
        -------
        vector
        """
        return Vector(self.x - other.x, self.y - other.y)

    def __sub__(self, other: 'Vector') -> 'Vector':
        return self.sub(other)

    def __rsub__(self, other: 'Vector') -> 'Vector':
        return other.sub(self)

    def __isub__(self, other: 'Vector') -> 'Vector':
        self.x -= other.x
        self.y -= other.y
        return self

    def sub_vector(self, direction: 'Vector') -> 'Vector':
        if not isinstance(direction, Vector):
            raise TypeError('expect given direction is an instance of Vector')

        return direction.unit(self @ direction.unit())

    def __or__(self, direction: 'Vector') -> 'Vector':
        return self.sub_vector(direction)
