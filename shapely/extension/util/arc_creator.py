from bisect import bisect_left
from itertools import product
from math import isclose
from operator import truth
from typing import Union, List

from shapely.extension.constant import LARGE_ENOUGH_DISTANCE, MATH_EPS
from shapely.extension.geometry import Circle, Arc
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.extension.util.decompose import decompose
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lmap, lfilter
from shapely.extension.util.offset import offset
from shapely.extension.util.prolong import prolong
from shapely.geometry import Point, LineString, MultiLineString, MultiPoint, GeometryCollection
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.ops import nearest_points, unary_union


class FixedRadiusArcCreator:
    """
    helper class for arc or circle creation given fixed radius beforehand
    """
    def __init__(self, radius: float):
        """
        Parameters
        ----------
        radius: the radius of result arcs or circles
        """
        self._radius = float(radius)
        self._geoms: List[BaseGeometry] = []
        self.constraint = None

    def intersects_with(self, geom: BaseGeometry, dist_tol: float = MATH_EPS) -> 'FixedRadiusArcCreator':
        """
        specify geometry that intersected with result arcs or circles. If you specify too many geometries to intersect
        with, it might raise RuntimeError that no arc or circle will be created under these many intersection constraint

        Parameters
        ----------
        geom: geometry instance, for linestring only supports straight line
        dist_tol: the distance tolerance for intersection point calculation

        Returns
        -------
        self
        """
        if isinstance(geom, BaseMultipartGeometry):
            for sub_geom in geom.geoms:
                self.intersects_with(sub_geom)
            return self

        self._geoms.append(geom)

        if isinstance(geom, Point):
            constraint = Circle(center=geom, radius=self._radius)

        elif isinstance(geom, Circle):
            # order matters, because Circle is child type of LineString, thus cannot modify order of if condition
            concentric_circles = [geom.concentric(geom.radius + self._radius)]
            if geom.radius > self._radius:
                concentric_circles.append(geom.concentric(geom.radius - self._radius))
            constraint = MultiLineString(concentric_circles)

        elif isinstance(geom, LineString):
            # order matters, because Circle is child type of LineString, thus cannot modify order of if condition
            if not geom.ext.is_straight():
                raise ValueError('only support straight linestring')
            line = prolong(geom, front_prolong_len=LARGE_ENOUGH_DISTANCE, end_prolong_len=LARGE_ENOUGH_DISTANCE)
            constraint = MultiLineString([offset(line, dist=self._radius, side='left'),
                                          offset(line, dist=self._radius, side='right')])
        else:
            raise NotImplementedError(f'{type(geom)} is not supported as constraint')

        if not self.constraint:
            self.constraint = constraint
        else:
            intersections = []
            for existed_single_constraint, other_single_constraint in product(flatten(self.constraint).to_list(),
                                                                              flatten(constraint).to_list()):
                intersection = existed_single_constraint.intersection(other_single_constraint)
                if not intersection and existed_single_constraint.distance(other_single_constraint) < dist_tol:
                    intersection = LineString(
                        nearest_points(existed_single_constraint, other_single_constraint)).centroid
                intersections.append(intersection)

            self.constraint = unary_union(flatten(intersections).to_list())

        if not self.constraint:
            raise RuntimeError('center hints have turned to be empty geometry,'
                               ' meaning too many constrains have been set')

        return self

    def create_circles(self) -> List[Circle]:
        """
        create circles according to given constraints
        Returns
        -------
        list of circles
        """
        if not self.constraint:
            raise RuntimeError('center hints have turned to be empty geometry,'
                               ' meaning too many constrains have been set')
        if (not isinstance(self.constraint, (Point, MultiPoint, GeometryCollection))
                or not decompose(self.constraint, Point)):
            raise RuntimeError('center hints cannot lead to center points, '
                               'meaning not enough constrains set')

        centers: List[Point] = decompose(self.constraint, Point)
        return lmap(lambda pt: Circle(center=pt, radius=self._radius), centers)

    def create_arcs(self) -> List[Arc]:
        """
        create arcs according to given constraints, arcs come from circles, cut by intersection points
        Returns
        -------
        list of arcs
        """
        circles = self.create_circles()
        arcs: List[Arc] = []
        for circle in circles:
            # magic number 1e-4 here, it's related to the resolution of arc and circle, and relatively stable
            tangent_pts = lfilter(truth, [circle.tangent_point(geom, 1e-4) for geom in self._geoms])
            arcs.extend(circle.arc(tangent_pts))

        return arcs


class FixedCenterArcCreator:
    """
    helper class for arc or circle creation given fixed center point beforehand
    """
    def __init__(self, center: Union[Point, CoordType]):
        """
        Parameters
        ----------
        center: the center of the result arcs or circles
        """
        self._center = Point(center)
        self._radius_candidates: List[float] = []
        self._geoms: List[BaseGeometry] = []

    def intersects_with(self, geom: BaseGeometry, radius_dist_tol: float = MATH_EPS) -> 'FixedCenterArcCreator':
        """
        specify geometry that intersected with result arcs or circles. If you specify too many geometries to intersect
        with, it might raise RuntimeError that no arc or circle will be created under these many intersection constraint

        Parameters
        ----------
        geom: geometry instance, for linestring only supports straight line
        radius_dist_tol: the distance tolerance for intersection point calculation

        Returns
        -------
        self
        """
        if isinstance(geom, BaseMultipartGeometry):
            for sub_geom in geom.geoms:
                self.intersects_with(sub_geom)
            return self

        self._geoms.append(geom)

        if isinstance(geom, Point):
            radius = geom.distance(self._center)
            radius_candidates = [radius]

        elif isinstance(geom, Circle):
            dist_between_centers = geom.centroid.distance(self._center)
            radius_candidates = [dist_between_centers + geom.radius, abs(dist_between_centers - geom.radius)]

        elif isinstance(geom, LineString):
            if not geom.ext.is_straight():
                raise ValueError('only support straight linestring')
            line = prolong(geom, front_prolong_len=LARGE_ENOUGH_DISTANCE, end_prolong_len=LARGE_ENOUGH_DISTANCE)
            radius = line.ext.distance(self._center, Vector.from_endpoints_of(line).cw_perpendicular)
            radius_candidates = [radius]
        else:
            raise NotImplementedError(f'{type(geom)} is not supported to calculate radius candidates')

        radius_candidates = lfilter(lambda radius: radius > 0, sorted(radius_candidates))

        if not self._radius_candidates:
            self._radius_candidates = radius_candidates

        else:
            def is_closed_to_existed_radius_candidate(existed_radius):
                index = bisect_left(radius_candidates, existed_radius)

                is_closed = True
                is_closed &= (index < len(radius_candidates) and isclose(existed_radius,
                                                                         radius_candidates[index],
                                                                         abs_tol=radius_dist_tol))
                is_closed &= isclose(existed_radius, radius_candidates[index - 1], abs_tol=radius_dist_tol)
                return is_closed

            self._radius_candidates: List[float] = lfilter(is_closed_to_existed_radius_candidate,
                                                           self._radius_candidates)

        if not self._radius_candidates:
            raise RuntimeError('no radius candidates exists, probably because too many constraint specified')

        return self

    def create_circles(self) -> List[Circle]:
        """
        create circles according to given constraints
        Returns
        -------
        list of circles
        """
        if not self._radius_candidates:
            raise RuntimeError('no radius candidates exists, probably because given too many constraints or no'
                               'constraint at all')
        return lmap(lambda radius: Circle(center=self._center, radius=radius), self._radius_candidates)

    def create_arcs(self) -> List[Arc]:
        """
        create arcs according to given constraints, arcs come from circles, cut by intersection points
        Returns
        -------
        list of arcs
        """
        circles = self.create_circles()
        arcs: List[Arc] = []
        for circle in circles:
            tangent_pts = filter(truth, [circle.tangent_point(geom) for geom in self._geoms])
            arcs.extend(circle.arc(tangent_pts))

        return arcs


class ArcCreator:
    """
    entry class for creat arc and circle
    """
    def center(self, center: Union[Point, CoordType]) -> FixedCenterArcCreator:
        """
        fix center beforehand and calculate the arc or circle with further intersected geometries given
        Parameters
        ----------
        center: Point | Coord | tuple[num, num]

        Returns
        -------
        instance of FixedCenterArcCreator, enter the fix center arc creation process
        """
        return FixedCenterArcCreator(center)

    def radius(self, radius: float) -> FixedRadiusArcCreator:
        """
        fix the radius beforehand and calculate the arc or circle with further intersected geometries given
        Parameters
        ----------
        radius: number

        Returns
        -------
        instance of FixedRadiusArcCreator, enter the fix radius arc creation process
        """
        return FixedRadiusArcCreator(radius)
