from abc import ABC, abstractmethod
from typing import Sequence, List, Any, Union, Callable

from toolz import identity

from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, lmap
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

    @abstractmethod
    def items(self):
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

    def items(self):
        return self._geoms


class RTreeQueryContainer(GeomQueryContainer):
    def __init__(self, geoms: List[BaseGeometry]):
        self._geoms = geoms
        self._db = STRtree(geoms)
        self._added: List[BaseGeometry] = []
        self._deleted: List[BaseGeometry] = []

    def query(self, geom: BaseGeometry) -> List[BaseGeometry]:
        result: List[BaseGeometry] = (
                list(self._db.query(geom))
                + lfilter(lambda candidate: candidate.intersects(geom), self._added))
        return lfilter(lambda candidate: candidate not in self._deleted, result)

    def add(self, geom: BaseGeometry):
        existed = self._db.query(geom)
        if geom in self._deleted:
            self._deleted = lfilter(lambda candidate: not geom.equals(candidate), self._deleted)
        if geom not in existed and geom not in self._added:
            self._added.append(geom)

    def remove(self, geom: BaseGeometry):
        existed = self._db.query(geom)
        if geom in self._added:
            self._added = lfilter(lambda candidate: not geom.equals(candidate), self._added)
        if geom in existed and geom not in self._deleted:
            self._deleted.append(geom)

    def items(self):
        result = self._geoms
        result = lfilter(lambda candidate: candidate not in self._deleted, result)
        for add_candidate in self._added:
            if add_candidate not in result:
                result.append(add_candidate)
        return result


class Query:
    def __init__(self, geoms: Sequence[Union[BaseGeometry, Any]],
                 container_type: type = RTreeQueryContainer,
                 key: Callable[[Any], BaseGeometry] = identity):

        self._key = key

        inner_geoms = geoms

        if self._key != identity:
            inner_geoms = lmap(key, geoms)
            for geom, inner_geom in zip(geoms, inner_geoms):
                # TODO: possibly introduce cycling reference, check it later
                inner_geom.ext.cargo['_inner'] = geom

        if any(not isinstance(inner_geom, BaseGeometry) for inner_geom in inner_geoms):
            raise TypeError('expect inner geoms are all geometry objects')

        self._geoms = inner_geoms
        self._db = container_type(self._geoms)

    def add(self, geom):
        self._db.add(geom)

    def remove(self, geom):
        self._db.remove(geom)

    def items(self):
        return self._db.items()

    def unpack(self, geoms):
        if self._key is identity:
            return geoms

        return lmap(lambda geom: geom.ext.cargo['_inner'], geoms)

    @classmethod
    def from_flatten(cls, geoms: Sequence[BaseGeometry], container_type: type = STRtree) -> 'Query':
        return cls(geoms=flatten(geoms).to_list(), container_type=container_type)

    def intersects(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.intersects(geom), self._db.query(geom)))

    def contains(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.contains(geom), self._db.query(geom)))

    def covers(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.covers(geom), self._db.query(geom)))

    def covered_by(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.covered_by(geom), self._db.query(geom)))

    def crosses(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.crosses(geom), self._db.query(geom)))

    def overlaps(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.overlaps(geom), self._db.query(geom)))

    def touches(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.touches(geom), self._db.query(geom)))

    def within(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return self.unpack(lfilter(lambda candidate: candidate.within(geom), self._db.query(geom)))
