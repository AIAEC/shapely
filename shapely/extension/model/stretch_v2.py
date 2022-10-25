from typing import Union, Optional, List, Sequence
from uuid import uuid4
from weakref import ref, ReferenceType

from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry import StraightSegment
from shapely.extension.model import Coord, Vector, Stretch
from shapely.geometry import Point, LineString, MultiLineString
from shapely.geometry.base import BaseGeometry


class Pivot:
    """
    node of stretch
    """

    def __init__(self, origin: Union[Coord, Point]):
        try:
            self._origin = Point(origin)
        except Exception:
            raise TypeError(f'given origin cannot form a point, given {origin}')

        if not self._origin.is_valid or self._origin.is_empty:
            raise ValueError(f'origin is invalid point, given {origin}')

        self.in_edges = []
        self.out_edges = []
        self._stretch: Optional[ReferenceType['Stretch']] = None
        self.cargo = {}
        self.id = uuid4()

    def __hash__(self):
        return hash(('pivot', self.id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return f'Pivot({self.shape.x}, {self.shape.y})@{self.id[:4]}'

    @property
    def stretch(self) -> Optional['Stretch']:
        return self._stretch() if self._stretch else None

    @stretch.setter
    def stretch(self, stretch):
        if not isinstance(stretch, Stretch):
            self._stretch = None

        self._stretch = ref(stretch)

    @property
    def shape(self) -> Point:
        return self._origin

    @property
    def is_valid(self) -> bool:
        return len(self.in_edges) == len(self.out_edges)

    def move_to(self, target: Union[Point, Coord]) -> None:
        try:
            target = Point(target)
        except Exception:
            raise TypeError(f'target cannot form a point, given {target}')
        self._origin = target

    def move_by(self, direct: Vector) -> None:
        if not isinstance(direct, Vector):
            raise TypeError(f'direct must be vector, given {direct}')

        self._origin = direct.apply(self._origin)


class DirectEdge:
    def __init__(self, from_pivot: Pivot, to_pivot: Pivot, reverse_edge: Optional['DirectEdge'] = None):
        self.from_pivot = from_pivot
        self.to_pivot = to_pivot
        self.reverse_edge = reverse_edge
        self._stretch: Optional[ReferenceType['Stretch']] = None
        self.cargo = {}

        if self not in self.from_pivot.out_edges:
            self.from_pivot.out_edges.append(self)
        if self not in self.to_pivot.in_edges:
            self.to_pivot.in_edges.append(self)

    def __hash__(self):
        return hash((hash(self.from_pivot), hash(self.to_pivot)))

    def __eq__(self, other):
        return self.from_pivot == other.from_pivot and self.to_pivot == other.to_pivot

    def __repr__(self):
        return f'Edge(({self.from_pivot})->({self.to_pivot}))'

    @property
    def stretch(self) -> Optional['Stretch']:
        return self._stretch() if self._stretch else None

    @stretch.setter
    def stretch(self, stretch):
        if not isinstance(stretch, Stretch):
            self._stretch = None

        self._stretch = ref(stretch)

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_pivot.shape, self.to_pivot.shape])

    def offset(self, strategy) -> None:
        pass

    def intersection(self, other: 'DirectEdge') -> Union[Pivot, 'DirectEdge', None]:
        pass

    def expand(self, point: Point) -> List['DirectEdge']:
        pass

    def interpolate(self, dist: float, absolute: bool = True):
        pass


class Closure:
    @property
    def stretch(self):
        pass

    @property
    def edges(self) -> List[DirectEdge]:
        pass

    @property
    def pivots(self) -> List[Pivot]:
        pass


class ClosureSnapshot:
    def __init__(self, closures: List[Closure]):
        self.closures = closures

    @classmethod
    def create_from(cls, stretch):
        pass

    @property
    def occupation(self) -> BaseGeometry:
        pass

    def query_closures(self, geom: BaseGeometry):
        pass


class Stretch:
    def __init__(self, pivots: List[Pivot], edges: List[DirectEdge]):
        self.pivots = pivots
        self.edges = edges
        self.id = uuid4()

    def closure_snapshot(self):
        pass

    def append(self, item: Union[Pivot, DirectEdge]):
        pass

    def remove(self, item: Union[Pivot, DirectEdge]):
        pass

    def query_pivots(self, geom: BaseGeometry):
        pass

    def query_edges(self, geom: BaseGeometry):
        pass

    def divided_by(self, divider: Union[LineString, MultiLineString, Sequence[Union[LineString, MultiLineString]]]):
        pass


class StretchFactory:
    def __init__(self, dist_tol: float = MATH_EPS):
        self._dist_tol = dist_tol

    def create(self, geom_or_geoms: Union[BaseGeometry]) -> Stretch:
        pass
