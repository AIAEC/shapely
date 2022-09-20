from shapely.geometry import LineString


class StraightSegment(LineString):
    """
    child type of LineString, that represent a straight line segment.
    constraint: only 2 coordinates are allowed to create straight segment instance
    """

    def __init__(self, coordinates=None):
        super().__init__(coordinates)
        coords_list = list(self.coords)
        if len(coords_list) != 2:
            raise ValueError(f'input coordinates must have 2 coordinates, given {coords_list}')
