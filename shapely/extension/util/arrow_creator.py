from typing import Union

from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.arrow import Arrow
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.geometry import Point, LineString


class FixHeadArrowFactory:
    def __init__(self, head_length: float, head_width: float, shaft_width: float):
        self._head_length = head_length
        self._head_width = head_width
        self._shaft_width = shaft_width
        if self._head_length <= 0:
            raise ValueError('The result is straight line')
        if self._head_width <= self._shaft_width or self._head_width <= 0:
            raise ValueError('The result is not arrow')

    def from_origin_and_vector(self, origin: Union[Point, CoordType],
                               direction: Vector,
                               arrow_length: float,
                               reverse: bool = False) -> Arrow:
        if arrow_length < self._head_length:
            raise ValueError('The result is triangle')
        shaft_length = self._head_length if reverse else arrow_length - self._head_length
        start_coord = origin.coords[0] if isinstance(origin, Point) else origin
        turning_coord = direction.unit(shaft_length).apply_coord(start_coord)
        end_coord = direction.unit(arrow_length).apply_coord(start_coord)
        shaft_width = self._shaft_width / 2
        head_width = self._head_width / 2
        coords = [start_coord, turning_coord, end_coord]
        if reverse:
            coords.reverse()
        return Arrow(coords,
                     [(shaft_width, 0), (head_width, shaft_width), (0, 0)])

    def from_straight_line(self, straight_line: Union[StraightSegment, LineString], reverse: bool = False) -> Arrow:
        if isinstance(straight_line, LineString):
            simplified_lines = straight_line.ext.simplify()
            if len(simplified_lines) != 1:
                raise ValueError('line is not straight line')
            straight_lines = simplified_lines[0].ext.decompose(StraightSegment).to_list()
            if len(straight_lines) != 1:
                raise ValueError('line is not straight line')
            straight_line = straight_lines[0]
        elif not isinstance(straight_line, StraightSegment):
            raise ValueError('line is not straight line')

        return self.from_origin_and_vector(origin=straight_line.ext.start(),
                                           direction=Vector.from_endpoints_of(straight_line),
                                           arrow_length=straight_line.length,
                                           reverse=reverse)

    def from_line(self, line: LineString, reverse: bool = False) -> Arrow:
        shaft_width = self._shaft_width / 2
        head_width = self._head_width / 2
        coords = line.coords[:]
        if len(coords) < 3:
            raise ValueError('invalid line')
        if reverse:
            coords.reverse()
        coords_widths = [(shaft_width, 0)]
        if len(coords) == 3:
            coords_widths.extend([(head_width, shaft_width), (0, 0)])
        else:
            num_middle_points = len(coords) - 3
            for i in range(0, num_middle_points):
                coords_widths.append((shaft_width, shaft_width))
            coords_widths.append((head_width, shaft_width))
            coords_widths.append((0, 0))
        return Arrow(coords,
                     coords_widths)


class FixRatioArrowFactory:
    def __init__(self, shaft_total_length_ratio: float, head_shaft_width_ratio: float):
        """

        :param shaft_total_length_ratio: ratio of shaft length to total length
        :param head_shaft_width_ratio:  ratio of head length to shaft length
        """
        self._shaft_length_ratio = shaft_total_length_ratio
        self._width_ratio = head_shaft_width_ratio
        if self._shaft_length_ratio >= 1:
            raise ValueError('The result is straight line')
        if self._shaft_length_ratio <= 0:
            raise ValueError('The result is triangle')
        if self._width_ratio <= 1:
            raise ValueError('The result is not arrow')

    def from_origin_and_vector(self, origin: Union[Point, CoordType],
                               direction: Vector,
                               arrow_length: float,
                               shaft_width: float,
                               reverse: bool = False) -> Arrow:
        turning_ratio = self._shaft_length_ratio
        if reverse:
            turning_ratio = 1 - turning_ratio
        shaft_length = arrow_length * turning_ratio
        start_coord = origin.coords[0] if isinstance(origin, Point) else origin
        turning_coord = direction.unit(shaft_length).apply_coord(start_coord)
        end_coord = direction.unit(arrow_length).apply_coord(start_coord)
        shaft_width = shaft_width / 2
        head_width = shaft_width * self._width_ratio
        coords = [start_coord, turning_coord, end_coord]
        if reverse:
            coords.reverse()
        return Arrow(coords,
                     [(shaft_width, 0), (head_width, shaft_width), (0, 0)])

    def from_straight_line(self,
                           straight_line: Union[StraightSegment, LineString],
                           shaft_width: float,
                           reverse: bool = False) -> Arrow:
        if isinstance(straight_line, LineString):
            simplified_lines = straight_line.ext.simplify()
            if len(simplified_lines) != 1:
                raise ValueError('line is not straight line')
            straight_lines = simplified_lines[0].ext.decompose(StraightSegment).to_list()
            if len(straight_lines) != 1:
                raise ValueError('line is not straight line')
            straight_line = straight_lines[0]
        elif not isinstance(straight_line, StraightSegment):
            raise ValueError('line is not straight line')

        return self.from_origin_and_vector(origin=straight_line.ext.start(),
                                           direction=Vector.from_endpoints_of(straight_line),
                                           arrow_length=straight_line.length,
                                           shaft_width=shaft_width,
                                           reverse=reverse)
