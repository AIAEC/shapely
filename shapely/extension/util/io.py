from typing import Optional, Union, Dict, Callable

from shapely.extension.util.func_util import lmap
from shapely.geometry import Point, LineString, shape, LinearRing, mapping
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.wkb import loads as shapely_wkb_loads
from shapely.wkt import loads as shapely_wkt_loads


def to_2d(geom: BaseGeometry):
    if not geom.has_z:
        return geom

    if isinstance(geom, BaseMultipartGeometry):
        return type(geom)([to_2d(single_geom) for single_geom in geom.geoms])

    if isinstance(geom, (Point, LineString)):
        return type(geom)(lmap(lambda coord: coord[:2], list(geom.coords)))

    return type(geom)(to_2d(geom.exterior), lmap(to_2d, list(geom.interiors)))


def wkt_load(wkt_str: str) -> Optional[BaseGeometry]:
    """
    先检测输入的wkt_str是否合法，然后
    Load a geometry from a WKT string
    失败返回None
    """
    if not isinstance(wkt_str, str):
        return None
    valid_wkt_prefixes = {'POINT', 'MULTIPOINT', 'LINEARRING', 'LINESTRING', 'MULTILINESTRING', 'POLYGON',
                          'MULTIPOLYGON',
                          'GEOMETRYCOLLECTION'}
    for valid_wkt_prefix in valid_wkt_prefixes:
        if wkt_str[:len(valid_wkt_prefix)].upper() == valid_wkt_prefix:
            try:
                geom = shapely_wkt_loads(wkt_str)
                return geom
            except Exception:
                break
    return None


def wkb_load(wkb_bytes: str) -> Optional[BaseGeometry]:
    """
    Load a geometry from a WKB byte string, or hex-encoded string if
    ``hex=True``
    失败返回None
    """
    if not isinstance(wkb_bytes, bytes):
        return None
    try:
        geom = shapely_wkb_loads(wkb_bytes)
        return geom
    except Exception:
        return None


def geojson_load(geojson: dict) -> Optional[BaseGeometry]:
    """
    根据geojson导入Geometry。失败返回None
    """
    if not isinstance(geojson, dict):
        return None

    valid_types = {'Point', 'MultiPoint', 'LineString', 'LinearRing', 'MultiLineString',
                   'Polygon', 'MultiPolygon', 'GeometryCollection'}
    has_valid_type = (geojson.get('type', None) in valid_types)
    if not has_valid_type:
        return None

    has_valid_coordinates = isinstance(geojson.get('coordinates', None), (tuple, list))
    has_valid_geometries = isinstance(geojson.get('geometries', None), (list, tuple))
    if not has_valid_coordinates and not has_valid_geometries:
        return None

    try:
        geom = shape(geojson)
        return geom
    except Exception:
        return None


def load(geom_data: Union[dict, bytes, str]) -> Optional[BaseGeometry]:
    """
    loads geojson, wkt or wkb into shapely geometry
    """
    if isinstance(geom_data, BaseGeometry):
        return geom_data

    if isinstance(geom_data, dict) and geom_data.get("type", None) == "LinearRing":
        geom_data["type"] = "LineString"  # LinearRing cannot be recognized, change it to LineString

    type_loader_mapping: Dict[type, Callable] = {dict: geojson_load, str: wkt_load, bytes: wkb_load}

    if loader := type_loader_mapping.get(type(geom_data), None):
        if geom := loader(geom_data):
            return to_2d(geom)

        raise ValueError("given data cannot load into shapely geometry object")

    raise TypeError(f'only accept geojson(dict), wkt(str), wkb(bytes), given {type(geom_data)}')


def geojson(geom: BaseGeometry, eliminate_linear_ring: bool = True) -> dict:
    if not isinstance(geom, BaseGeometry):
        raise TypeError("only support shapely geometry object")

    if eliminate_linear_ring and isinstance(geom, LinearRing):
        geom = LineString(geom)

    return mapping(geom)
