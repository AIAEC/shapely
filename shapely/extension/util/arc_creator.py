from bisect import bisect_left
from itertools import product
from math import isclose
from operator import truth
from typing import Union, List

from shapely.extension.constant import LARGE_ENOUGH_DISTANCE, MATH_EPS
from shapely.extension.geometry.arc import Arc
from shapely.extension.geometry.circle import Circle
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.extension.util.decompose import decompose
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lmap, lfilter
from shapely.extension.util.offset import offset
from shapely.extension.util.prolong import prolong
from shapely.geometry import Point, LineString, MultiPoint, GeometryCollection
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.ops import nearest_points


class FixedRadiusArcCreator:
    """
    helper class for arc or circle creation given fixed radius beforehand
    """

    def __init__(self, radius: float, angle_step: float = 16):
        """
        Parameters
        ----------
        radius: the radius of result arcs or circles
        """
        self._radius = float(radius)
        self._angle_step = angle_step
        self._geoms: List[BaseGeometry] = []
        self.constraints = None

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
            constraints = [Circle(center=geom, radius=self._radius, angle_step=self._angle_step)]

        elif isinstance(geom, Circle):
            # order matters, because Circle is child type of LineString, thus cannot modify order of if condition
            concentric_circles = [geom.concentric(geom.radius + self._radius)]
            if geom.radius > self._radius:
                concentric_circles.append(geom.concentric(geom.radius - self._radius))
            constraints = concentric_circles

        elif isinstance(geom, LineString):
            # order matters, because Circle is child type of LineString, thus cannot modify order of if condition
            if not geom.ext.is_straight():
                raise ValueError('only support straight linestring')
            line = prolong(geom, front_prolong_len=LARGE_ENOUGH_DISTANCE, end_prolong_len=LARGE_ENOUGH_DISTANCE)
            constraints = [offset(line, dist=self._radius, side='left'), offset(line, dist=self._radius, side='right')]
        else:
            raise NotImplementedError(f'{type(geom)} is not supported as constraint')

        if not self.constraints:
            self.constraints = constraints
        else:
            intersections = []
            for existed_single_constraint, other_single_constraint in product(flatten(self.constraints).to_list(),
                                                                              flatten(constraints).to_list()):
                intersection = existed_single_constraint.ext.intersection(other_single_constraint)
                if not intersection and existed_single_constraint.distance(other_single_constraint) < dist_tol:
                    intersection = LineString(
                        nearest_points(existed_single_constraint, other_single_constraint)).centroid
                intersections.append(intersection)

            self.constraints = flatten(intersections).to_list()

        return self

    def create_circles(self, touched_every_geoms: bool = False, dist_tol: float = MATH_EPS) -> List[Circle]:
        """
        create circles according to given constraints
        Parameters
        ----------
        touched_every_geoms: whether return circles that touched every given geometries, default to False
        dist_tol: distance tolerance for touching predicator.

        Returns
        -------
        list of circles
        """
        if not self.constraints:
            return []  # center hints have turned to be empty geometry  meaning too many constrains have been set
        if (not all([isinstance(constraint, (Point, MultiPoint, GeometryCollection))
                     for constraint in self.constraints])
                or not decompose(self.constraints, Point)):
            return []  # center hints cannot lead to center points, meaning not enough constrains set

        centers: List[Point] = decompose(self.constraints, Point)
        circles = lmap(lambda pt: Circle(center=pt, radius=self._radius, angle_step=self._angle_step), centers)

        if touched_every_geoms:
            return lfilter(lambda circle: all(circle.distance(geom) <= dist_tol for geom in self._geoms), circles)

        return circles

    def create_arcs(self, touched_every_geoms: bool = False, dist_tol: float = MATH_EPS) -> List[Arc]:
        """
        create arcs according to given constraints, arcs come from circles, cut by intersection points

        Parameters
        ----------
        touched_every_geoms: whether return arcs that touched every given geometries, default to False
        dist_tol: distance tolerance for touching predicator.

        Returns
        -------
        list of arcs
        """
        circles = self.create_circles()
        arcs: List[Arc] = []
        for circle in circles:
            # magic number 1e-4 here, it's related to the resolution of arc and circle, and relatively stable
            tangent_pts = lfilter(truth, [circle.intersection(geom) for geom in self._geoms])
            arcs.extend(circle.arc(tangent_pts))

        if touched_every_geoms:
            return lfilter(lambda arc: all(arc.distance(geom) <= dist_tol for geom in self._geoms), arcs)

        return arcs


class FixedCenterArcCreator:
    """
    helper class for arc or circle creation given fixed center point beforehand
    """

    def __init__(self, center: Union[Point, CoordType], angle_step: float = 16):
        """
        Parameters
        ----------
        center: the center of the result arcs or circles
        """
        self._center = Point(center)
        self._angle_step = angle_step
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

    def create_circles(self, touched_every_geoms: bool = False, dist_tol: float = MATH_EPS) -> List[Circle]:
        """
        create circles according to given constraints

        Parameters
        ----------
        touched_every_geoms: whether return circles that touched every given geometries, default to False
        dist_tol: distance tolerance for touching predicator.

        Returns
        -------
        list of circles
        """
        if not self._radius_candidates:
            raise RuntimeError('no radius candidates exists, probably because given too many constraints or no'
                               'constraint at all')
        circles = lmap(lambda radius: Circle(center=self._center, radius=radius), self._radius_candidates)

        if touched_every_geoms:
            return lfilter(lambda circle: all(circle.distance(geom) <= dist_tol for geom in self._geoms), circles)

        return circles

    def create_arcs(self, touched_every_geoms: bool = False, dist_tol: float = MATH_EPS) -> List[Arc]:
        """
        create arcs according to given constraints, arcs come from circles, cut by intersection points

        Parameters
        ----------
        touched_every_geoms: whether return arcs that touched every given geometries, default to False
        dist_tol: distance tolerance for touching predicator.

        Returns
        -------
        list of arcs
        """
        circles = self.create_circles()
        arcs: List[Arc] = []
        for circle in circles:
            tangent_pts = filter(truth, [circle.intersection(geom) for geom in self._geoms])
            arcs.extend(circle.arc(tangent_pts))

        if touched_every_geoms:
            return lfilter(lambda arc: all(arc.distance(geom) <= dist_tol for geom in self._geoms), arcs)

        return arcs


class ArcCreator:
    """
    entry class for creat arc and circle
    """

    def center(self, center: Union[Point, CoordType], angle_step: float = 16) -> FixedCenterArcCreator:
        """
        fix center beforehand and calculate the arc or circle with further intersected geometries given
        Parameters
        ----------
        center: Point | Coord | tuple[num, num]
        angle_step: float

        Returns
        -------
        instance of FixedCenterArcCreator, enter the fix center arc creation process
        """
        return FixedCenterArcCreator(center, angle_step)

    def radius(self, radius: float, angle_step: float = 16) -> FixedRadiusArcCreator:
        """
        fix the radius beforehand and calculate the arc or circle with further intersected geometries given
        Parameters
        ----------
        radius: number
        angle_step: float

        Returns
        -------
        instance of FixedRadiusArcCreator, enter the fix radius arc creation process
        """
        return FixedRadiusArcCreator(radius, angle_step)
