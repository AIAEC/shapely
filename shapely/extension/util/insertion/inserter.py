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
                    scale_factor: float = DEFAULT_SCALE_FACTOR) -> List[BaseGeometry]:
    if not obstacle:
        obstacle = Polygon()
        if not space:
            return [Polygon()]

    if not space:
        space = obstacle.envelope

    boundary_mound = space.ext.mould(1)
    obstacle_for_insertion = unary_union([boundary_mound, obstacle.intersection(space)])

    return obstacle_for_insertion.ext.raster(scale_factor).convolution(insert_geom.ext.raster(scale_factor)).vectorize()


@curry
def rect_inserter(insert_geom: BaseGeometry, space: Polygon, obstacle: Optional[BaseGeometry] = None) -> List[Polygon]:
    # TODO 尝试把space和obstacle统一输入
    insert_envelope = insert_geom.ext.envelope().tightened()
    return Insertion(inserter=insert_envelope).of(space=space, obstacle=obstacle)
