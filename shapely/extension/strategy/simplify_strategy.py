from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from operator import attrgetter
from typing import List, Optional, Union

from functional.streams import seq

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lconcat
from shapely.geometry import Polygon, JOIN_STYLE, CAP_STYLE
from shapely.geometry.base import BaseGeometry


class BaseSimplifyStrategy(ABC):
    @abstractmethod
    def simplify(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> List[BaseGeometry]:
        raise NotImplementedError


class NativeSimplifyStrategy(BaseSimplifyStrategy):
    """
    simplify strategy that use native simplify api of shapely
    """

    def __init__(self, simplify_dist: float = 0):
        self._simplify_dist = simplify_dist

    def simplify(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> List[BaseGeometry]:
        return [geom.simplify(self._simplify_dist) for geom in flatten(geom_or_geoms).to_list()]


class ConservativeSimplifyStrategy(BaseSimplifyStrategy):
    """
    simplify strategy that repeatedly use native simplify api of shapely with a decreasing simplify_dist,
    until simplify_dist is small enough not to make an area difference in one geom exceed given tolerance.
    return flattened original geom if failed.
    """

    def __init__(self, initial_simplify_dist: float = MATH_MIDDLE_EPS, area_diff_tolerance: float = MATH_MIDDLE_EPS):
        self._initial_simplify_dist = initial_simplify_dist
        self._area_diff_tolerance = area_diff_tolerance

    def simplify(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> List[BaseGeometry]:
        return [self._conservative_simplify(geom, self._initial_simplify_dist, self._area_diff_tolerance)
                for geom in flatten(geom_or_geoms)]

    @staticmethod
    def _conservative_simplify(geom: BaseGeometry, simplify_dist: float, area_diff_tolerance: float) -> BaseGeometry:

        for _ in range(try_limit := 10):
            simplified_geom: BaseGeometry = geom.simplify(simplify_dist)
            if (area_diff := abs(geom.area - simplified_geom.area)) <= area_diff_tolerance:
                return simplified_geom
            simplify_dist *= 0.5

        return geom


class BufferSimplifyStrategy(BaseSimplifyStrategy):
    """
    simplify strategy that buffer the geometry back and forth to make its boundary smooth
    """

    @dataclass
    class BufferParam:
        buffer_dist: float = field(default=5)
        buffer_dist_decay: float = field(default=1.0)
        join_style: int = field(default=JOIN_STYLE.mitre)
        cap_style: int = field(default=CAP_STYLE.flat)
        mitre_limit: float = field(default=5)  # the default mitre limit of shapely

    def __init__(self, n_iter: int = 5, buffer_param: Optional[BufferParam] = None):
        self._n_iter = max(1, abs(n_iter))
        self._buffer_param = buffer_param or self.BufferParam()

    @classmethod
    def mitre(cls, buffer_dist: float = 5,
              buffer_dist_decay: float = 1.0,
              mitre_limit: float = 5,
              n_iter: int = 1) -> 'BufferSimplifyStrategy':
        """
        make a buffer strategy that use mitre as its join_style
        Parameters
        ----------
        buffer_dist
        buffer_dist_decay: buffer distance decay ratio for each iteration
        mitre_limit:
        n_iter: number of iteration

        Returns
        -------
        BufferSimplifyStrategy instance
        """
        buffer_param = cls.BufferParam(buffer_dist=buffer_dist,
                                       buffer_dist_decay=buffer_dist_decay,
                                       mitre_limit=mitre_limit,
                                       join_style=JOIN_STYLE.mitre)
        return cls(n_iter=n_iter, buffer_param=buffer_param)

    @classmethod
    def round(cls, buffer_dist: float = 5, buffer_dist_decay: float = 1.0, n_iter: int = 1) -> 'BufferSimplifyStrategy':
        """
        make a buffer strategy that use round as its join_style
        Parameters
        ----------
        buffer_dist
        buffer_dist_decay: buffer distance decay ratio for each iteration
        n_iter: number of iteration

        Returns
        -------
        BufferSimplifyStrategy instance
        """
        buffer_param = cls.BufferParam(buffer_dist=buffer_dist,
                                       buffer_dist_decay=buffer_dist_decay,
                                       join_style=JOIN_STYLE.round)
        return cls(n_iter=n_iter, buffer_param=buffer_param)

    def simplify(self, geom_or_geoms: Union[BaseGeometry, Sequence[BaseGeometry]]) -> List[BaseGeometry]:
        geoms = [geom_or_geoms] if isinstance(geom_or_geoms, BaseGeometry) else geom_or_geoms

        result: List[BaseGeometry] = lconcat(map(flatten, geoms))
        for _ in range(self._n_iter):
            for i, g in enumerate(result):
                if isinstance(g, Polygon):
                    for factor in [-1, 1]:
                        g = g.buffer(distance=self._buffer_param.buffer_dist * factor,
                                     join_style=self._buffer_param.join_style,
                                     cap_style=self._buffer_param.cap_style,
                                     mitre_limit=self._buffer_param.mitre_limit)

                    result[i] = g

                    self._buffer_param.buffer_dist *= self._buffer_param.buffer_dist_decay

        return (seq(result)
                .flat_map(flatten)
                .filter(attrgetter('is_valid'))
                .to_list())
