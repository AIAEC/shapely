from collections.abc import Iterable
from typing import Union, List

from shapely.extension.geometry.arc import Arc
from shapely.extension.typing import CoordType
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import Point, LineString


class Circle(Arc):
    """
    child type of Arc representing the full exterior of circle exterior
    """

    def __init__(self, center: Union[Point, CoordType] = (0, 0),
                 radius: float = 1,
                 angle_step: float = 1):
        if radius <= 0:
            raise ValueError(f'radius must be greater than 0, given {radius}')

        super().__init__(center, radius, 0, 360, angle_step)

    def concentric(self, radius: float) -> 'Circle':
        return Circle(center=self._center, radius=radius, angle_step=self._resolution)

    def arc(self, cutting_point_or_points: Union[Union[Point, CoordType], Iterable[Union[Point, CoordType]]]
            ) -> List[Arc]:
        cutting_points = (list(cutting_point_or_points) if isinstance(cutting_point_or_points, Iterable)
                          else [cutting_point_or_points])
        angles = [LineString([self._center, Point(cutting_pt)]).ext.angle() for cutting_pt in cutting_points]
        angles.sort()

        arcs: List[Arc] = []

        for angle, next_angle in win_slice(angles, win_size=2, tail_cycling=True):
            if angle is next_angle:
                rotating_angle = 360
            else:
                rotating_angle = angle.rotating_angle(next_angle, direct='ccw').degree

            arcs.append(Arc(center=self._center,
                            radius=self._radius,
                            start_angle=angle.degree,
                            rotate_angle=rotating_angle,
                            angle_step=self._resolution))

        return arcs
