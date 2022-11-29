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

    @abstractmethod
    def add(self, geom: BaseGeometry):
        raise NotImplementedError

    @abstractmethod
    def remove(self, geom: BaseGeometry):
        raise NotImplementedError


class SeqQueryContainer(GeomQueryContainer):
    def __init__(self, geoms: List[BaseGeometry]):
        self._geoms = geoms

    def add(self, geom: BaseGeometry):
        if geom not in self._geoms:
            self._geoms.append(geom)

    def remove(self, geom: BaseGeometry):
        if geom in self._geoms:
            self._geoms.remove(geom)

    def query(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: candidate.intersects(geom), self._geoms)


class RTreeQueryContainer(GeomQueryContainer):
    def __init__(self, geoms: List[BaseGeometry]):
        self._db = STRtree(geoms)
        self._added: List[BaseGeometry] = []
        self._deleted: List[BaseGeometry] = []

    def query(self, geom: BaseGeometry) -> List[BaseGeometry]:
        result: List[BaseGeometry] = (
                list(self._db.query(geom))
                + lfilter(lambda candidate: candidate.intersects(geom), self._added))
        return lfilter(lambda candidate: candidate not in self._deleted, result)

    def add(self, geom: BaseGeometry):
        existed = self.query(geom)
        if geom not in existed and geom not in self._added:
            self._added.append(geom)
        if geom in self._deleted:
            self._deleted.remove(geom)

    def remove(self, geom: BaseGeometry):
        if geom not in self._deleted:
            self._deleted.append(geom)


class Query:
    def __init__(self, geoms: Sequence[BaseGeometry], container_type: type = RTreeQueryContainer):
        if any(not isinstance(geom, BaseGeometry) for geom in geoms):
            raise TypeError('expect given geoms are all geometry objects')
        self._geoms = list(geoms)
        self._db = container_type(self._geoms)

    def add(self, geom):
        self._db.add(geom)

    def remove(self, geom):
        self._db.remove(geom)

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
