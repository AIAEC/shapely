from typing import Optional, List

from shapely.ops import unary_union

from shapely.extension.model.raster import DEFAULT_SCALE_FACTOR
from shapely.extension.util.insertion.insertion import Insertion
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from toolz import curry


@curry
def raster_inserter(insert_geom: BaseGeometry,
                    obstacle: Optional[BaseGeometry],
                    space: Optional[Polygon] = None,
                    scale_factor: float = DEFAULT_SCALE_FACTOR) -> BaseGeometry:
    if not obstacle:
        if not space:
            return Polygon()
        boundary_mound = space.envelope.ext.mould(1).difference(space)
        return boundary_mound.ext.raster(scale_factor).convolution(insert_geom.ext.raster(scale_factor)).vectorize()

    if not space:
        space = obstacle.envelope

    interior_polys: List[Polygon] = []
    for interior in space.interiors:
        interior_polys.append(Polygon(interior))

    boundary_mound = space.envelope.ext.mould(1).difference(space)
    obstacle_for_insertion = unary_union([boundary_mound, obstacle, *interior_polys])

    return obstacle_for_insertion.ext.raster(scale_factor).convolution(insert_geom.ext.raster(scale_factor)).vectorize()


@curry
def rect_inserter(insert_geom: BaseGeometry, space: Polygon, obstacle: Optional[BaseGeometry] = None) -> List[Polygon]:
    # TODO 尝试把space和obstacle统一输入
    insert_envelope = insert_geom.ext.envelope().tightened()
    return Insertion(inserter=insert_envelope).of(space=space, obstacle=obstacle)
