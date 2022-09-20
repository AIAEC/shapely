from typing import Union

from shapely.extension.geometry.arc import Arc
from shapely.extension.typing import CoordType, Num
from shapely.geometry import Point


class Circle(Arc):
    """
    child type of Arc representing the full exterior of circle exterior
    """

    def __init__(self, center: Union[Point, CoordType],
                 radius: Num = 1,
                 resolution: Num = 16):
        super().__init__(center, radius, 0, 360, resolution)
