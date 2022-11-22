from typing import Sequence, List

from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree


class LinearFetcher:
    def __init__(self, geoms: List[BaseGeometry]):
        self._geoms = geoms

    def query(self, geom: BaseGeometry):
        return lfilter(lambda candidate: candidate.intersects(geom), self._geoms)


class Query:
    def __init__(self, geoms: Sequence[BaseGeometry], use_rtree: bool = True):
        if any(not isinstance(geom, BaseGeometry) for geom in geoms):
            raise TypeError('expect given geoms are all geometry objects')
        self._geoms = list(geoms)
        self._db = STRtree(self._geoms) if use_rtree else LinearFetcher(self._geoms)

    @classmethod
    def from_flatten(cls, geoms: Sequence[BaseGeometry], use_rtree: bool = True) -> 'Query':
        return cls(geoms=flatten(geoms).to_list(), use_rtree=use_rtree)

    def intersects(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.intersects(candidate), self._db.query(geom))

    def contains(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.contains(candidate), self._db.query(geom))

    def covers(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.covers(candidate), self._db.query(geom))

    def covered_by(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.covered_by(candidate), self._db.query(geom))

    def crosses(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.crosses(candidate), self._db.query(geom))

    def disjoint(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.disjoint(candidate), self._db.query(geom))

    def overlaps(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.overlaps(candidate), self._db.query(geom))

    def touches(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.touches(candidate), self._db.query(geom))

    def within(self, geom: BaseGeometry) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.within(candidate), self._db.query(geom))

    def relate_pattern(self, geom: BaseGeometry, pattern: str) -> List[BaseGeometry]:
        return lfilter(lambda candidate: geom.relate_pattern(candidate, pattern), self._db.query(geom))
