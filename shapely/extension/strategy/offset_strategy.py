from abc import ABC, abstractmethod

from shapely.extension.util.offset import offset
from shapely.geometry import LineString, JOIN_STYLE


class BaseOffsetStrategy(ABC):
    @abstractmethod
    def offset(self,
               line: LineString,
               dist: float,
               side: str = 'left',
               invert_coords: bool = False):
        raise NotImplementedError


class OffsetStrategy(BaseOffsetStrategy):
    """
    offset strategy that use the latest offset util
    """

    def __init__(self, join_style: int = JOIN_STYLE.mitre):
        self._join_style = join_style

    def offset(self, line: LineString, dist: float, side: str = 'left', invert_coords: bool = False):
        return offset(line=line,
                      dist=dist,
                      side=side,
                      invert_coords=invert_coords,
                      join_style=self._join_style)
