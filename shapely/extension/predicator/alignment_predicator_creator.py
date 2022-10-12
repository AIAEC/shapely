from typing import Optional, Callable

from toolz import identity

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.extension.predicator.predicator import Predicator
from shapely.extension.typing import Num, GeomObj
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry.base import BaseGeometry


class AlignmentPredicatorCreator:
    def __init__(self, geom: BaseGeometry,
                 direction: Optional[Vector] = None,
                 direction_dist_tol: float = MATH_EPS,
                 angle_tol: float = MATH_EPS):
        if not isinstance(geom, (Point, LineString, Polygon)):
            raise TypeError(f'{type(geom)} has not been supported')

        self._geom = geom
        self._direction = direction
        self._direction_dist_tol = direction_dist_tol
        self._angle_tol = angle_tol

    def alignable(self) -> Callable[[BaseGeometry], bool]:
        """
        Returns
        -------
        filter function that given geometry instance to check if it's alignable to current geometry
        """

        def _func(geom_obj: GeomObj, attr_getter: Optional[Callable[[object], BaseGeometry]] = None):
            attr_getter = attr_getter or identity
            self_geom_alignment = self._geom.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                           angle_tol=self._angle_tol)
            given_geom_alignment = attr_getter(geom_obj).ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                                       angle_tol=self._angle_tol)
            return self_geom_alignment.alignable_to(given_geom_alignment)

        return Predicator(_func)

    def shortest_distance(self) -> DistancePredicatorCreator:
        """
        Returns
        -------
        return DistancePredicatorCreator of the shortest distance of alignment direction for further predication
        """

        def shortest_alignment_distance(geom0: BaseGeometry, geom1: BaseGeometry):
            geom0_alignment = geom0.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                  angle_tol=self._angle_tol)
            geom1_alignment = geom1.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                  angle_tol=self._angle_tol)
            if isinstance(geom0, (Point, LineString)):
                return geom0_alignment.distance(geom1_alignment)
            return min(geom0_alignment.distances_to(geom1_alignment), default=float('inf'))

        return DistancePredicatorCreator(self._geom, distance_mapper=shortest_alignment_distance)
