import warnings
from abc import ABC, abstractmethod

from shapely.extension.constant import MATH_EPS
from shapely.extension.typing import Num
from shapely.extension.util.geom_offset import offset as offset_v1
from shapely.extension.util.geom_offset_v2 import offset as offset_v2
from shapely.geometry import LineString, JOIN_STYLE


class BaseOffsetStrategy(ABC):
    @abstractmethod
    def offset(self,
               line: LineString,
               dist: float,
               side: str = 'left',
               invert_coords: bool = False):
        raise NotImplementedError


class LegacyOffsetStrategy(BaseOffsetStrategy):
    """
    offset strategy that use the legacy offset util
    """

    def __init__(self, use_pan_if_failed: bool = True, eps: Num = MATH_EPS):
        self._use_pan_if_failed = use_pan_if_failed
        self._eps = eps

    def offset(self, line: LineString, dist: float, side: str = 'left', invert_coords: bool = False):
        warnings.warn('legacy offset might be removed soon')
        return offset_v1(line=line,
                         dist=dist,
                         side=side,
                         invert_coords=invert_coords,
                         use_pan_if_failed=self._use_pan_if_failed,
                         eps=float(self._eps))


class OffsetStrategy(BaseOffsetStrategy):
    """
    offset strategy that use the latest offset util
    """

    def __init__(self, join_style: int = JOIN_STYLE.mitre):
        self._join_style = join_style

    def offset(self, line: LineString, dist: float, side: str = 'left', invert_coords: bool = False):
        return offset_v2(line=line,
                         dist=dist,
                         side=side,
                         invert_coords=invert_coords,
                         join_style=self._join_style)
