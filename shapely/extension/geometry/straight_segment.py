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
