from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE


class Buffer:
    def __init__(self, geom: BaseGeometry, single_sided: bool = False):
        self._geom = geom
        self._single_sided = single_sided

    def single_sided(self):
        return Buffer(self._geom, single_sided=True)

    def round(self, dist: float, resolution: int = 16) -> BaseGeometry:
        return self._geom.buffer(distance=dist,
                                 cap_style=CAP_STYLE.round,
                                 join_style=JOIN_STYLE.round,
                                 resolution=resolution,
                                 single_sided=self._single_sided)

    def rect(self, dist: float,
             cap_style=CAP_STYLE.flat,
             mitre_limit: float = 5.0) -> BaseGeometry:

        if isinstance(self._geom, Point) and dist > 0:
            x, y = self._geom.x, self._geom.y
            xmin, ymin, xmax, ymax = x - dist, y - dist, x + dist, y + dist
            return box(xmin, ymin, xmax, ymax)

        return self._geom.buffer(distance=dist,
                                 cap_style=cap_style,
                                 join_style=JOIN_STYLE.mitre,
                                 mitre_limit=mitre_limit,
                                 single_sided=self._single_sided)
