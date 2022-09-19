from shapely.extension.util.flatten import flatten
from shapely.geometry import Point, LinearRing, LineString, Polygon, MultiPoint
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient


def ccw(geom: BaseGeometry) -> BaseGeometry:
    """
    将几何图形的坐标顺序变成逆时针的. 注意: Point, MultiPoint, LineString没有逆时针的概念, 将返回其自身. Polygon的exterior会变成逆时针,
    但是其interiors会都变成顺时针. LinearRing会变成逆时针

    :param geom: shapely geometry
    :return: geometry object with same type
    """
    if isinstance(geom, Polygon):
        return orient(geom, sign=1.0)

    if isinstance(geom, LinearRing):
        return geom if geom.is_ccw else LinearRing(list(geom.coords)[::-1])

    if isinstance(geom, LineString) and geom.is_closed:  # 封闭的linestring
        return geom if LinearRing(geom).is_ccw else LineString(list(geom.coords)[::-1])

    # must put below checking LinearRing
    if isinstance(geom, (Point, MultiPoint, LineString)):
        return geom

    return type(geom)([ccw(sub) for sub in flatten(geom).to_list()])
