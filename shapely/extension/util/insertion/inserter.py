from typing import Optional, List

from toolz import curry

from shapely.extension.model.raster import DEFAULT_SCALE_FACTOR
from shapely.extension.util.insertion.minkowski_insertion import MinkowskiInsertion
from shapely.extension.util.insertion.rect_insertion import RectInsertion
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


def _obstacle(obstacle: Optional[BaseGeometry] = None,
              space: Optional[BaseGeometry] = None) -> Optional[BaseGeometry]:
    if not obstacle and not space:
        return None

    if not obstacle:
        obstacle = Polygon()

    if not space:
        space = obstacle.envelope

    boundary_mound = space.ext.mould(1)
    return unary_union([boundary_mound, obstacle.intersection(space)])


@curry
def raster_inserter(insert_poly: Polygon,
                    obstacle: Optional[BaseGeometry] = None,
                    space: Optional[Polygon] = None,
                    scale_factor: float = DEFAULT_SCALE_FACTOR) -> List[BaseGeometry]:
    obstacle_for_insertion = _obstacle(obstacle, space)
    if not obstacle_for_insertion:
        return []

    return obstacle_for_insertion.ext.raster(scale_factor).convolution(insert_poly.ext.raster(scale_factor)).vectorize()


@curry
def rect_inserter(insert_poly: Polygon, space: Polygon, obstacle: Optional[BaseGeometry] = None) -> List[Polygon]:
    insert_envelope = insert_poly.ext.envelope().tightened()
    return RectInsertion(inserter=insert_envelope).of(space=space, obstacle=obstacle)


@curry
def minkowski_inserter(insert_poly: Polygon,
                       obstacle: Optional[BaseGeometry] = None,
                       space: Optional[Polygon] = None) -> List[Polygon]:
    obstacle_for_insertion = _obstacle(obstacle, space)
    if not obstacle_for_insertion:
        return []

    space = space if space else obstacle_for_insertion.envelope

    return MinkowskiInsertion(insert_poly=insert_poly).of(space=space, obstacle=obstacle_for_insertion)
