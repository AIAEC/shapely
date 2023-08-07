from contextlib import suppress
from typing import Union

from shapely.geometry import Point, LineString, Polygon


def Skeleton(single_geom: Union[Point, LineString, Polygon]):
    """
    create a Skeleton object for the given geometry, either be CgalSkeleton or BotffySkeleton
    Parameters
    ----------
    single_geom: polygon, line or point

    Returns
    -------
    Skeleton object
    """
    from shapely.extension.model.skeleton.botffy_skeleton import BotffySkeleton
    from shapely.extension.model.skeleton.cgal_skeleton import CgalSkeleton

    with suppress(Exception):
        return CgalSkeleton(single_geom)

    with suppress(Exception):
        return BotffySkeleton(single_geom)

    raise ValueError("Cannot find a skeleton class for the given geometry, probably because the geometry is complex.")
