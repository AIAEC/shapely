from typing import List, Optional

from functional import seq

from shapely.extension.geometry.arc import Arc
from shapely.extension.model.vector import Vector
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import LineString, Point


class ArcParser:
    """
    recognize the inner arc from a given linestring
    """
    def __init__(self, linestring: LineString):
        if not linestring or not linestring.is_valid or linestring.is_empty:
            raise ValueError('expect valid, non-empty linestring')

        self._linestring = linestring

    @property
    def center(self) -> Point:
        """
        the fitting center
        Returns
        -------
        point
        """
        center_candidates: List[Point] = []
        for seg, next_seg in win_slice(self._linestring.ext.segments(), win_size=2):
            if seg.is_empty or next_seg.is_empty:
                continue

            assert isinstance(seg, LineString)
            assert isinstance(next_seg, LineString)

            for i in [-1, 1]:
                normal_line_of_seg = seg.ext.normal_vector().unit(i).ray(seg.centroid)
                normal_line_of_next_seg = next_seg.ext.normal_vector().unit(i).ray(next_seg.centroid)
                if center_candidate := normal_line_of_seg.intersection(normal_line_of_next_seg):
                    if isinstance(center_candidate, Point):
                        center_candidates.append(center_candidate)
                        break

        if not center_candidates:
            # should never happen
            raise ValueError('given linestring is probably empty, or straight, which cannot deduce to arc')

        x = sum([center.x for center in center_candidates]) / len(center_candidates)
        y = sum([center.y for center in center_candidates]) / len(center_candidates)

        return Point(x, y)

    @property
    def radius(self) -> float:
        """
        fitting radius
        Returns
        -------
        float
        """
        center = self.center
        return self._linestring.ext.decompose(Point).map(center.distance).average()

    @property
    def angle_step(self) -> float:
        """
        fitting angle step
        Returns
        -------
        float
        """
        angles = []
        for seg, next_seg in win_slice(self._linestring.ext.segments(), win_size=2):
            if seg.is_empty or next_seg.is_empty:
                continue

            assert isinstance(seg, LineString)
            assert isinstance(next_seg, LineString)

            angles.append(seg.ext.angle().including_angle(next_seg.ext.angle()).degree)

        return seq(angles).average()

    def arc(self, angle_step: Optional[float] = 1) -> Arc:
        """
        Parameters
        ----------
        angle_step: angle_step of result arc, default to 1 degree, which is in most cases better than fitting angle_step

        Returns
        -------
        instance of arc
        """
        center = self.center
        start_angle = Vector.from_origin_to_target(origin=center, target=self._linestring.ext.start()).angle
        end_angle = Vector.from_origin_to_target(origin=center, target=self._linestring.ext.end()).angle
        rotate_angle = start_angle.rotating_angle(end_angle, direct='ccw')
        return Arc(center=center,
                   radius=self.radius,
                   start_angle=start_angle.degree,
                   rotate_angle=rotate_angle.degree,
                   angle_step=angle_step or self.angle_step)
