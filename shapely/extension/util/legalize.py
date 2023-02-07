from shapely.extension.geometry.empty import EMPTY_GEOM

from shapely.extension.util.flatten import flatten

from shapely.extension.util.iter_util import win_slice
from shapely.extension.constant import MATH_EPS
from shapely.extension.model.coord import Coord
from shapely.geometry import (
    GeometryCollection, MultiPolygon, MultiPoint, LinearRing, LineString, MultiLineString, Polygon, Point)
from shapely.geometry.base import BaseMultipartGeometry, BaseGeometry
from shapely.validation import make_valid


def legalize(geom: BaseGeometry) -> BaseGeometry:
    """
    Legalize the given geometry
    Parameters
    ----------
    geom: geometry

    Returns
    -------
    valid geometry
    """
    # shapely >= 1.8 has a default make_valid function, check shapely version if you cannot find this function
    try:
        return make_valid(geom)
    except ValueError:
        pass  # make_valid method failed, try our own tricks

    if isinstance(geom, BaseMultipartGeometry):
        sub_geoms = [legalize(g) for g in flatten(geom)]
        if all(isinstance(g, LineString) for g in
               sub_geoms):  # are sub geoms all lines
            geom = MultiLineString(sub_geoms)
        elif all(isinstance(g, Polygon) for g in
                 sub_geoms):  # area sub geoms all polygons
            polys = [legalize(poly) for poly in flatten(GeometryCollection(sub_geoms).buffer(0)) if
                     isinstance(poly, Polygon)]
            geom = MultiPolygon(polys)
        elif all(isinstance(g, Point) for g in
                 sub_geoms):  # area sub geoms all points
            geom = MultiPoint(sub_geoms)
        else:
            polys = []
            geoms = []
            for geometry in sub_geoms:
                if isinstance(geometry, Polygon):
                    polys.append(geometry)
                else:
                    geoms.append(geometry)
            geoms.extend([legalize(geometry) for geometry in flatten(GeometryCollection(polys).buffer(0))])
            geom = GeometryCollection(geoms)

    elif isinstance(geom, Polygon):
        parts = [geom for geom in flatten(geom.buffer(0)) if isinstance(geom, Polygon)]
        largest_part = max(parts, key=lambda g: g.area, default=GeometryCollection())
        geom = legalize(largest_part)

    elif isinstance(geom,
                    LinearRing):  # must be put before handling LineString because LinearRing is one kind of LineString
        # when LinearRing has duplicate coords(or coords too close so that considered as duplicate), it will be invalid
        origin_coords = list(geom.coords)
        deduplicated_coords = [origin_coords[0]]
        for coord0, coord1 in win_slice(origin_coords, win_size=2):
            if Coord.dist(coord0, coord1) > MATH_EPS:
                deduplicated_coords.append(coord1)
        return LinearRing(deduplicated_coords)

    elif isinstance(geom, LineString):
        # this LineString must be invalid, and all coords are the same coord
        if coords := list(geom.coords):
            geom = Point(coords[0])
        else:
            geom = LineString()

    return geom if geom.is_valid else EMPTY_GEOM
