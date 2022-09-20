from typing import Optional

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.extension.predicator.predicator import Predicator
from shapely.extension.typing import Num
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry.base import BaseGeometry


class AlignmentPredicatorCreator:
    def __init__(self, geom: BaseGeometry,
                 direction: Optional[Vector] = None,
                 direction_dist_tol: Num = MATH_EPS,
                 angle_tol: Num = MATH_EPS):
        if not isinstance(geom, (Point, LineString, Polygon)):
            raise TypeError(f'{type(geom)} has not been supported')

        self._geom = geom
        self._direction = direction
        self._direction_dist_tol = direction_dist_tol
        self._angle_tol = angle_tol

    def alignable(self):
        def _func(geom: BaseGeometry):
            self_geom_alignment = self._geom.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                           angle_tol=self._angle_tol)
            given_geom_alignment = geom.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                      angle_tol=self._angle_tol)
            return self_geom_alignment.alignable_to(given_geom_alignment)

        return Predicator(_func)

    def shortest_distance(self):
        def shortest_alignment_distance(geom0: BaseGeometry, geom1: BaseGeometry):
            geom0_alignment = geom0.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                  angle_tol=self._angle_tol)
            geom1_alignment = geom1.ext.alignment(direction_dist_tol=self._direction_dist_tol,
                                                  angle_tol=self._angle_tol)
            if isinstance(geom0, (Point, LineString)):
                return geom0_alignment.distance(geom1_alignment)
            return min(geom0_alignment.distances_to(geom1_alignment), default=float('inf'))

        return DistancePredicatorCreator(self._geom, distance_mapper=shortest_alignment_distance)
