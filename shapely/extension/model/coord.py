from dataclasses import dataclass
from math import hypot
from typing import List, Tuple, Sequence, Union

from shapely.extension.model.angle import Angle
from shapely.extension.typing import Num, CoordType
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import Point


@dataclass
class Coord:
    def __init__(self, *args):
        self.x, self.y = self._setup(args)

    def _setup(self, arg_list) -> Tuple[Num, Num]:
        if len(arg_list) < 1:
            raise ValueError(f'{arg_list} cannot be used to initialize Coord object')
        if (isinstance(arg_list[0], Sequence)
                and len(arg_list[0]) >= 2
                and isinstance(arg_list[0][0], Num)
                and isinstance(arg_list[0][1], Num)):
            return arg_list[0][:2]
        if isinstance(arg_list[0], Num) and isinstance(arg_list[1], Num):
            return arg_list[:2]

        raise ValueError(f'{arg_list} cannot be used to initialize Coord object')

    def __repr__(self):
        return f'({self.x}, {self.y})'

    def __getitem__(self, idx):
        if idx == 0:
            return self.x
        if idx == 1:
            return self.y
        raise ValueError('idx can only be 0 or 1')

    def __len__(self):
        return 2

    def __iter__(self):
        return iter([self.x, self.y])

    def __add__(self, other: CoordType):
        return Coord(self.x + other[0], self.y + other[1])

    def __radd__(self, other: CoordType):
        return Coord(other[0] + self.x, other[1] + self.y)

    def __iadd__(self, other: CoordType):
        self.x += other[0]
        self.y += other[1]
        return self

    def __sub__(self, other: CoordType):
        return Coord(self.x - other[0], self.y - other[1])

    def __rsub__(self, other: CoordType):
        return Coord(other[0] - self.x, other[1] - self.y)

    def __isub__(self, other: CoordType):
        self.x -= other[0]
        self.y -= other[1]
        return self

    def __mul__(self, num: Num):
        return Coord(self.x * num, self.y * num)

    def __rmul__(self, num: Num):
        return Coord(self.x * num, self.y * num)

    def __imul__(self, num: Num):
        self.x *= num
        self.y *= num
        return self

    def __truediv__(self, num: Num):
        if num == 0:
            raise ValueError('divider cannot be 0')
        return Coord(self.x / num, self.y / num)

    def __itruediv__(self, num: Num):
        self.x /= num
        self.y /= num
        return self

    def __abs__(self):
        return self.hypot

    @property
    def hypot(self) -> float:
        return hypot(self.x, self.y)

    @staticmethod
    def dist(coord0: CoordType, coord1: CoordType) -> float:
        """
        输入两个坐标，计算之间的距离

        :param coord0:第一个坐标
        :param coord1:第二个坐标
        :return:两个坐标之间距离
        """
        return hypot(coord1[0] - coord0[0], coord1[1] - coord0[1])

    def dist_to(self, coord: CoordType) -> float:
        return self.dist(self, coord)

    @property
    def angle_to(self, origin: Union[str, CoordType, Point] = 'origin') -> Angle:
        if origin == 'origin':
            origin = Point(0, 0)
        else:
            origin = Point(origin)

        return self.angle(origin, self)

    @staticmethod
    def angle(coord0: CoordType, coord1: CoordType) -> Angle:
        coord = Coord(coord1) - Coord(coord0)
        return Angle.atan2(coord.y, coord.x)

    @staticmethod
    def including_angles(coords_in_ccw_order: List[CoordType],
                         head_cycling: bool = False,
                         tail_cycling: bool = False) -> List[Angle]:
        if len(coords_in_ccw_order) < 3:
            raise ValueError(f'need at least 3 coords to calculate angle, given {len(coords_in_ccw_order)} coords')

        angles: List[Angle] = []
        for coord0, coord1, coord2 in win_slice(coords_in_ccw_order,
                                                win_size=3,
                                                head_cycling=head_cycling,
                                                tail_cycling=tail_cycling):
            coord01_angle = Coord.angle(coord0, coord1)
            coord12_angle = Coord.angle(coord1, coord2)
            angles.append(180 - coord01_angle.rotating_angle(coord12_angle, direct='ccw'))

        return angles
