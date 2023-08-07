from typing import List, Optional

from shapely.extension.functional import seq
from shapely.extension.geometry.arc import Arc
from shapely.extension.model.vector import Vector
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import LineString, Point


class ArcParser:
    """
    recognize the inner arc from a given linestring
    """

    def __init__(self, linestring: LineString, num_repr_points: int = 3):
        if not linestring or not linestring.is_valid or linestring.is_empty or num_repr_points < 2:
            raise ValueError('expect valid, non-empty linestring')

        self._linestring = linestring
        self._repr_points = self.repr_points(linestring, num_repr_points)
        self._segments = [LineString([*points]) for points in win_slice(self._repr_points, win_size=2)]

    @staticmethod
    def repr_points(line: LineString, num_repr_points: int) -> List[Point]:
        points = [Point(coord) for coord in line.coords]
        sample_step: int = int(len(points) / (num_repr_points - 1))
        # avoid repeating the last point
        if len(points) % (num_repr_points - 1) == 1:
            return points[::sample_step]
        return points[::sample_step] + points[-1:]

    @property
    def center(self) -> Point:
        """
        the fitting center
        Returns
        -------
        point
        """
        center_candidates: List[Point] = []
        for seg, next_seg in win_slice(self._segments, win_size=2):
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
        return seq(self._repr_points).map(center.distance).average()

    @property
    def angle_step(self) -> float:
        """
        fitting angle step
        Returns
        -------
        float
        """
        angles = []
        for seg, next_seg in win_slice(self._segments, win_size=2):
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

    @classmethod
    def is_arc(cls, linestring: LineString,
               num_repr_points: int = 3,
               length_overlapping_ratio: float = 0.9) -> bool:
        if len(linestring.coords) <= 2:
            return False

        arc_parser = cls(linestring, num_repr_points=num_repr_points)

        try:
            fitting_arc = arc_parser.arc()
        except ValueError:
            return False

        buffer_dist = arc_parser.radius / 100
        overlapping_arc = linestring.buffer(buffer_dist).intersection(fitting_arc)
        return overlapping_arc.length / fitting_arc.length > length_overlapping_ratio
