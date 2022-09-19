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
                 direction_dist_tol: Num = MATH_EPS):
        if not isinstance(geom, (Point, LineString, Polygon)):
            raise TypeError(f'{type(geom)} has not been supported')

        self._geom = geom
        self._direction = direction
        self._direction_dist_tol = direction_dist_tol

    def alignable(self):
        def _func(geom: BaseGeometry):
            return (self._geom.ext.alignment(self._direction_dist_tol)
                    .alignable_to(geom.ext.alignment(self._direction_dist_tol)))

        return Predicator(_func)

    def shortest_distance(self):
        def shortest_alignment_distance(geom0: BaseGeometry, geom1: BaseGeometry):
            if isinstance(geom0, (Point, LineString)):
                return geom0.ext.alignment().distance(geom1.ext.alignment())
            return min(geom0.ext.alignment().distances_to(geom1.ext.alignment()), default=float('inf'))

        return DistancePredicatorCreator(self._geom, distance_mapper=shortest_alignment_distance)
