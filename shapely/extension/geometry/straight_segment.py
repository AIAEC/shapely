from shapely.geometry import LineString


class StraightSegment(LineString):
    def __init__(self, coordinates=None):
        super().__init__(coordinates)
        coords_list = list(self.coords)
        if len(coords_list) != 2:
            raise ValueError(f'input coordinates must have 2 coordinates, given {coords_list}')
