import math
from dataclasses import dataclass, field
from typing import Optional, List, Union

from shapely.extension.constant import MATH_EPS, MATH_MIDDLE_EPS
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.extension.util.union import tol_union
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import LineString, Polygon, Point
from shapely.geometry.base import BaseGeometry


@dataclass
class ArrowJoint:
    """
                                [s
                                [t\
        e]                      [a \
        n]──────────────────────[r  \
        d][start_width         ][t   \
 ────────]@────────────────────@[─────@
         ][           end_width][    /
         ]──────────────────────[   /
         ]                      [  /
                                [ /
                                [/

      ArrowJoint──────────────────────────────────────┐
      │coordinates: (x,y)                             │
      │start_width: width at the start of a segment   │
      │end_width: width at the end of a segment       │
      └───────────────────────────────────────────────┘

    """

    coord: CoordType = field()
    start_width: float = field()
    end_width: float = field()


class Arrow:
    def __init__(self, joints: Optional[List[ArrowJoint]] = None):
        self._joints = joints or []
        self._validate()

    def _validate(self):
        if len(self._joints) < 1:
            raise ValueError("Arrow must have at least 1 coordinate tuples")
        for pre_joint, cur_joint in (self._joints[i : i + 2] for i in range(len(self._joints) - 1)):
            if pre_joint.coord == cur_joint.coord:
                raise ValueError("consecutive same points detected")

    @property
    def shape(self) -> BaseGeometry:
        if len(self._joints) < 2:
            return Point(self._joints[0].coord)

        return tol_union(self._component_shape(), eps=MATH_MIDDLE_EPS)

    @property
    def is_closed(self) -> bool:
        return self.axis.is_closed

    @property
    def axis(self) -> Union[Point, LineString]:
        if len(self.coords) < 2:
            return Point(self.coords[0])
        return LineString(self.coords)

    @property
    def coords(self) -> List[CoordType]:
        return [jt.coord for jt in self._joints]

    def arrow_direction(self) -> List[Vector]:
        """Arrow pointing direction"""
        if len(self.coords) < 2:
            return []

        arrow_vectors: List[Vector] = []

        for pre_joint, cur_joint in win_slice(self._joints, 2):
            if self._is_continuous_shaft(pre_joint.start_width, cur_joint.end_width):
                continue
            if pre_joint.start_width > cur_joint.end_width:
                arrow_vectors.append(Vector.from_origin_to_target(pre_joint.coord, cur_joint.coord))
            else:
                arrow_vectors.append(Vector.from_origin_to_target(cur_joint.coord, pre_joint.coord))

        return arrow_vectors

    @staticmethod
    def _is_continuous_shaft(pre_width, cur_width) -> bool:
        return math.isclose(pre_width, cur_width, abs_tol=MATH_EPS)

    def _heads(self) -> List[Polygon]:
        heads: List[Polygon] = []

        for pre_joint, cur_joint in win_slice(self._joints, 2):
            if self._is_continuous_shaft(pre_joint.start_width, cur_joint.end_width):
                continue

            cur_vector = Vector.from_origin_to_target(pre_joint.coord, cur_joint.coord)
            ccw_vector = cur_vector.ccw_perpendicular

            heads.append(
                Polygon(
                    [
                        ccw_vector.unit(pre_joint.start_width / 2).apply_coord(pre_joint.coord),
                        ccw_vector.unit(-pre_joint.start_width / 2).apply_coord(pre_joint.coord),
                        ccw_vector.unit(cur_joint.end_width / 2).apply_coord(cur_joint.coord),
                        ccw_vector.unit(-cur_joint.end_width / 2).apply_coord(cur_joint.coord),
                    ]
                )
            )

        return heads

    def _shafts(self):
        shafts: List[Polygon] = []
        cur_shaft_coords: List[CoordType] = []
        cur_shaft_widths: List[float] = []

        for pre_joint, cur_joint in win_slice(self._joints, 2):
            if self._is_continuous_shaft(pre_joint.start_width, cur_joint.end_width):
                cur_shaft_coords.append(pre_joint.coord)
                cur_shaft_widths.append(pre_joint.start_width / 2)
                continue

            if cur_shaft_coords:
                cur_shaft_coords.append(pre_joint.coord)
                _shaft = LineString(cur_shaft_coords)
                _shaft = _shaft.ext.rbuf(sum(cur_shaft_widths) / len(cur_shaft_widths))
                shafts.append(_shaft)

                cur_shaft_coords = []
                cur_shaft_widths = []

        if cur_shaft_coords:
            cur_shaft_coords.append(self._joints[-1].coord)
            _shaft = LineString(cur_shaft_coords)
            _shaft = _shaft.ext.rbuf(sum(cur_shaft_widths) / len(cur_shaft_widths))
            shafts.append(_shaft)

        return shafts

    def _component_shape(self) -> List[Polygon]:
        return self._heads() + self._shafts()
