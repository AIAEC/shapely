from typing import Union

from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely.geometry.base import BaseGeometry


def mould(geom: BaseGeometry, margin: float) -> Union[Polygon, MultiPolygon, GeometryCollection]:
    """
    return the mould geometry of the given geometry
    Parameters
    ----------
    geom: given geometry
    margin: distance from envelope edges of given geom to the mould edge

    Returns
    -------
    mould geometry
    """
    return geom.envelope.ext.rbuf(margin).difference(geom)
