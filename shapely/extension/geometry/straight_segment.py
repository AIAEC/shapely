import math

from shapely.extension.constant import MATH_EPS
from shapely.geometry import LineString


class StraightSegment(LineString):
    """
    child type of LineString, that represent a straight line segment.
    constraint: only 2 coordinates are allowed to create straight segment instance
    """

    def __init__(self, coordinates=None):
        super().__init__(coordinates)
        coords_list = list(self.coords)
        if len(coords_list) != 2 and coordinates is not None:
            raise ValueError(f'input coordinates must have 2 coordinates, given {coords_list}')

    def point_on_left(self, point: 'Point') -> bool:
        """
        check if given point is on the left side of this segment
        Parameters
        ----------
        point: Point

        Returns
        -------
        bool
        """
        coords = list(self.coords)
        return (coords[1][0] - coords[0][0]) * (point.y - coords[0][1]) - (coords[1][1] - coords[0][1]) * (point.x - coords[0][0]) > 0

    def point_on_right(self, point: 'Point') -> bool:
        """
        check if given point is on the right side of this segment
        Parameters
        ----------
        point: Point

        Returns
        -------
        bool
        """
        coords = list(self.coords)
        return (coords[1][0] - coords[0][0]) * (point.y - coords[0][1]) - (coords[1][1] - coords[0][1]) * (point.x - coords[0][0]) < 0

    def point_on_line(self, point: 'Point') -> bool:
        """
        check if given point is on the line of this segment
        Parameters
        ----------
        point: Point

        Returns
        -------
        bool
        """
        coords = list(self.coords)
        return (coords[1][0] - coords[0][0]) * (point.y - coords[0][1]) - (coords[1][1] - coords[0][1]) * (point.x - coords[0][0]) == 0

    def point_on_segment(self, point: 'Point', tol: float = MATH_EPS) -> bool:
        """
        check if given point is on this segment
        Parameters
        ----------
        point: Point
        tol: Distance tolerance

        Returns
        -------
        bool
        """
        coords = list(self.coords)
        dist_between_start_and_point: float = math.hypot(coords[0][0] - point.x, coords[0][1] - point.y)
        dist_between_end_and_point: float = math.hypot(coords[1][0] - point.x, coords[1][1] - point.y)
        return math.isclose(dist_between_start_and_point + dist_between_end_and_point, self.length, abs_tol=tol)

