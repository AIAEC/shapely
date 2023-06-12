from typing import List

from cgal import Coord2D, regularize as cgal_regularize

from shapely.extension.util.func_util import lmap
from shapely.geometry import Polygon
from shapely.ops import unary_union


def regularize(poly: Polygon) -> Polygon:
    def regularize_helper(_poly: Polygon) -> Polygon:
        _poly = _poly.ext.legalize().ext.ccw().ext.shell
        coords: List[Coord2D] = cgal_regularize(lmap(Coord2D, _poly.exterior.coords[:-1]))
        return Polygon(lmap(lambda c: (c.x, c.y), coords))

    regularized_shell = regularize_helper(poly.ext.shell)
    regularized_holes = lmap(regularize_helper, poly.ext.holes)
    return regularized_shell.difference(unary_union(regularized_holes))
