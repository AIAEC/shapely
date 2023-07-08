from cgal import Coord2D, Polygon2D

from shapely.geometry import Polygon


def to_cgal(poly: Polygon) -> Polygon2D:
    poly = poly.ext.ccw()
    shell = [Coord2D(coord) for coord in poly.exterior.coords]
    holes = []
    for interior in poly.interiors:
        holes.append([Coord2D(coord) for coord in interior.coords])
    return Polygon2D(shell, holes)


def to_shapely(poly_2d: Polygon2D) -> Polygon:
    shell = [(coord.x, coord.y) for coord in poly_2d.shell]
    holes = []
    for hole in poly_2d.holes:
        holes.append([(coord.x, coord.y) for coord in hole])
    return Polygon(shell, holes)
