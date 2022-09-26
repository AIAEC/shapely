from math import isclose
from typing import Optional, Callable

from toolz import identity

from shapely.extension.predicator.predicator import Predicator
from shapely.extension.typing import Num, GeomObj
from shapely.geometry.base import BaseGeometry


class DistancePredicatorCreator:
    """
    predicator creator for distance predication
    """

    def __init__(self, geom: BaseGeometry,
                 distance_mapper: Optional[Callable[[BaseGeometry, BaseGeometry], Num]] = None):
        self._geom = geom
        self._distance_mapper = distance_mapper or (lambda geom0, geom1: geom0.distance(geom1))

    def less_than(self, dist: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return self._distance_mapper(self._geom, attr_getter(geom_obj)) < dist

        return Predicator(_func)

    def __lt__(self, dist: Num):
        return self.less_than(dist)

    def less_equal(self, dist: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return self._distance_mapper(self._geom, attr_getter(geom_obj)) <= dist

        return Predicator(_func)

    def __le__(self, dist: Num):
        return self.less_equal(dist)

    def greater_than(self, dist: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return self._distance_mapper(self._geom, attr_getter(geom_obj)) > dist

        return Predicator(_func)

    def __gt__(self, dist: Num):
        return self.greater_than(dist)

    def greater_equal(self, dist: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return self._distance_mapper(self._geom, attr_getter(geom_obj)) >= dist

        return Predicator(_func)

    def __ge__(self, dist: Num):
        return self.greater_equal(dist)

    def almost_equal(self, dist: Num, dist_tol: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return isclose(self._distance_mapper(self._geom, attr_getter(geom_obj)), dist, abs_tol=dist_tol)

        return Predicator(_func)

    def equal(self, dist: Num):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            return self._distance_mapper(self._geom, attr_getter(geom_obj)) == dist

        return Predicator(_func)

    def __eq__(self, dist: Num):
        return self.equal(dist)
