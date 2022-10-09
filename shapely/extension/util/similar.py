from shapely.extension.constant import MATH_EPS
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint, CAP_STYLE, \
    JOIN_STYLE, GeometryCollection

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


def similar(geom1: BaseGeometry, geom2: BaseGeometry, area_diff_tol: float = MATH_EPS) -> bool:
    """
    predicate whether 2 geometries are similar to each other

    Parameters
    ----------
    geom1: geometry instance 1
    geom2:  geometry instance 2
    area_diff_tol: area tolerance of 2 geometries

    Returns
    -------
    True if 2 geometries are in area tolerance
    """
    if not isinstance(geom1, BaseGeometry) or not isinstance(geom2, BaseGeometry):
        return False

    if geom1.is_empty and geom2.is_empty:
        return True

    categories = [(Point, MultiPoint), (Polygon, MultiPolygon), (LineString, MultiLineString), GeometryCollection]
    if not any(isinstance(geom1, category) and isinstance(geom2, category) for category in categories):
        return False

    if isinstance(geom1, (Polygon, MultiPolygon)):
        return geom1.symmetric_difference(geom2).area < area_diff_tol
    elif isinstance(geom1, (LineString, MultiLineString, Point, MultiPoint)):
        buffered_line1 = geom1.buffer(area_diff_tol, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre)
        buffered_line2 = geom2.buffer(area_diff_tol, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre)
        return buffered_line1.contains(geom2) or buffered_line2.contains(geom1)

    # GeometryCollection
    geoms_of_geom1 = list(getattr(geom1, 'geoms'))
    geoms_of_geom2 = list(getattr(geom2, 'geoms'))
    if len(geoms_of_geom1) != len(geoms_of_geom2):
        return False
    points1 = unary_union([geom for geom in geoms_of_geom1 if isinstance(geom, Point)])
    lines1 = unary_union([geom for geom in geoms_of_geom1 if isinstance(geom, LineString)])
    polygon1 = unary_union([geom for geom in geoms_of_geom1 if isinstance(geom, Polygon)])

    points2 = unary_union([geom for geom in geoms_of_geom2 if isinstance(geom, Point)])
    lines2 = unary_union([geom for geom in geoms_of_geom2 if isinstance(geom, LineString)])
    polygon2 = unary_union([geom for geom in geoms_of_geom2 if isinstance(geom, Polygon)])

    return (similar(points1, points2, area_diff_tol)
            and similar(lines1, lines2, area_diff_tol)
            and similar(polygon1, polygon2, area_diff_tol))
