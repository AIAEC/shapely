from typing import Union

from shapely.extension.geometry.arc import Arc
from shapely.extension.typing import CoordType, Num
from shapely.geometry import Point


class Circle(Arc):
    def __init__(self, center: Union[Point, CoordType],
                 radius: Num = 1,
                 resolution: Num = 16):
        super().__init__(center, radius, 0, 360, resolution)
