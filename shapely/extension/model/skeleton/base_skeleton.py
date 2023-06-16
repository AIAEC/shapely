from abc import ABC, abstractmethod
from typing import Union, List

from shapely.geometry import Point, LineString, Polygon


class BaseSkeleton(ABC):
    @abstractmethod
    def __init__(self, single_geom: Union[Point, LineString, Polygon]):
        raise NotImplementedError

    @abstractmethod
    def trunk_segments(self) -> List[LineString]:
        raise NotImplementedError

    @abstractmethod
    def branch_segments(self) -> List[LineString]:
        raise NotImplementedError

    @abstractmethod
    def full_segments(self) -> List[LineString]:
        raise NotImplementedError

    @abstractmethod
    def trunks(self) -> List[LineString]:
        raise NotImplementedError
