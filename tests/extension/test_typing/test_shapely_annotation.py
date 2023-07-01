import pytest
from pydantic import BaseModel, ValidationError

from shapely.extension.typing import PointT, LineStringT, PolygonT, MultiPointT, MultiLineStringT, MultiPolygonT, \
    GeometryCollectionT, PolygonTF, LinearRingT
from shapely.extension.typing.json_schema import json_schema
from shapely.geometry import shape, mapping, Polygon, Point, box
from shapely.wkb import dumps as wkb_dumps
from shapely.wkt import dumps as wkt_dumps


def do_test_serializing(model):
    assert isinstance(shape(model.model_dump()["geom"]), type(model.geom))
    assert isinstance(dict(model), dict)
    assert model.model_json_schema()["properties"]["geom"] == json_schema[model.geom.type]


def do_test_deserializing(geom, model_clz):
    geojson = mapping(geom)
    assert isinstance(model_clz.model_validate({"geom": geojson}), model_clz)

    wkt_str = wkt_dumps(geom)
    assert isinstance(model_clz.model_validate({"geom": wkt_str}), model_clz)

    wkb_bytes = wkb_dumps(geom)
    assert isinstance(model_clz.model_validate({"geom": wkb_bytes}), model_clz)

    assert isinstance(model_clz.model_validate({"geom": geom}), model_clz)


def do_test_validate_empty_geom(model_clz, typing):
    try:
        empty_geom = typing()
    except:
        return

    with pytest.raises(ValidationError):
        model_clz(geom=empty_geom)


def test_model(point, line, polygon, multi_point, multi_linestring, multi_polygon, geometry_collection):
    data_typing_pairs = [(point, PointT),
                         (line, LineStringT),
                         (polygon, PolygonT),
                         (multi_point, MultiPointT),
                         (multi_linestring, MultiLineStringT),
                         (multi_polygon, MultiPolygonT),
                         (geometry_collection, GeometryCollectionT)]

    for _geom, typing in data_typing_pairs:
        class _T(BaseModel):
            geom: typing

        do_test_serializing(_T(geom=_geom))
        do_test_deserializing(_geom, _T)
        do_test_validate_empty_geom(_T, typing)


def test_type_mismatch():
    point = Point(1, 2)

    class _T(BaseModel):
        geom: PolygonT

    with pytest.raises(ValidationError):
        _T(geom=point)


def test_invalid_polygon():
    poly = Polygon([(0, 0), (1, 0), (0, 1), (1, 1), (0, 0)])
    assert not poly.is_valid

    class _T(BaseModel):
        geom: PolygonT

    with pytest.raises(ValidationError):
        _T(geom=poly)


def test_tolerate_invalid():
    poly = Polygon([(0, 0), (1, 0), (0, 1), (1, 1), (0, 0)])
    assert not poly.is_valid

    class _T(BaseModel):
        geom: PolygonTF("S")

    assert isinstance(_T(geom=poly), _T)


def test_tolerate_empty():
    empty = Polygon()
    assert empty.is_empty

    class _T(BaseModel):
        geom: PolygonTF("V")

    assert isinstance(_T(geom=empty), _T)


def test_tolerate_invalid_and_empty():
    class _T(BaseModel):
        geom: PolygonTF(valid=False, non_empty=False)

    poly = Polygon([(0, 0), (1, 0), (0, 1), (1, 1), (0, 0)])
    assert not poly.is_valid
    assert isinstance(_T(geom=poly), _T)

    empty = Polygon()
    assert empty.is_empty
    assert isinstance(_T(geom=empty), _T)


def test_dump_linearring_to_linestring_geojson():
    ring = box(0, 0, 1, 1).exterior

    class _T(BaseModel):
        geom: LinearRingT

    model = _T(geom=ring)
    geojson = model.model_dump()

    assert geojson["geom"]["type"] == "LineString"


def test_only_load_2d_geometry():
    point = Point(0, 0, 0)
    assert point.has_z

    class _T(BaseModel):
        geom: PointT

    model = _T(geom=point)
    assert not model.geom.has_z
    assert model.geom == Point(0, 0)
