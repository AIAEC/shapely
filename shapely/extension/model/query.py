from abc import ABC, abstractmethod
from typing import Sequence, List

from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree


class GeomQueryContainer(ABC):
    @abstractmethod
    def query(self, geom: BaseGeometry) -> List[BaseGeometry]:
        raise NotImplementedError


class SeqQueryContainer(GeomQueryContainer):
    def __init__(self, geoms: List[BaseGeometry]):
        self._geoms = geoms

    def query(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.intersects(geom), self._geoms)


class Query:
    def __init__(self, geoms: Sequence[BaseGeometry], container_type: type = STRtree):
        if any(not isinstance(geom, BaseGeometry) for geom in geoms):
            raise TypeError('expect given geoms are all geometry objects')
        self._geoms = list(geoms)
        self._db = container_type(self._geoms)

    @classmethod
    def from_flatten(cls, geoms: Sequence[BaseGeometry], container_type: type = STRtree) -> 'Query':
        return cls(geoms=flatten(geoms).to_list(), container_type=container_type)

    def intersects(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.intersects(geom), self._db.query(geom))

    def contains(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.contains(geom), self._db.query(geom))

    def covers(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.covers(geom), self._db.query(geom))

    def covered_by(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.covered_by(geom), self._db.query(geom))

    def crosses(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.crosses(geom), self._db.query(geom))

    def disjoint(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.disjoint(geom), self._db.query(geom))

    def overlaps(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.overlaps(geom), self._db.query(geom))

    def touches(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.touches(geom), self._db.query(geom))

    def within(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.within(geom), self._db.query(geom))

    def relate_pattern(self, geom: BaseGeometry, pattern: str) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.relate_pattern(candidate, pattern), self._db.query(geom))
