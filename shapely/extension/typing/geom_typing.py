from typing import Any, Callable, Annotated

from typing_extensions import Type

from shapely.extension.typing.json_schema import json_schema
from shapely.extension.util.io import load, geojson, to_2d
from shapely.geometry import Point, LineString, LinearRing, Polygon, MultiPoint, MultiLineString, MultiPolygon, \
    GeometryCollection
from shapely.geometry.base import BaseGeometry


def _annotation(type_: Type[BaseGeometry], assert_valid: bool = True, assert_non_empty: bool = True):
    from pydantic import GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import core_schema

    class Annotation:
        @classmethod
        def __get_pydantic_core_schema__(
                cls,
                _source_type: Any,
                _handler: Callable[[Any], core_schema.CoreSchema],
        ) -> core_schema.CoreSchema:
            geojson_schema = core_schema.no_info_after_validator_function(load, core_schema.dict_schema())
            wkt_schema = core_schema.no_info_after_validator_function(load, core_schema.str_schema())
            wkb_schema = core_schema.no_info_after_validator_function(load, core_schema.bytes_schema())
            shapely_schema = core_schema.no_info_after_validator_function(to_2d, core_schema.is_instance_schema(type_))

            def validate(geom: BaseGeometry) -> BaseGeometry:
                if assert_valid:
                    assert geom.is_valid, "geom is not valid"
                if assert_non_empty:
                    assert not geom.is_empty, "geom is empty"

                return geom

            python_schema = core_schema.chain_schema([
                core_schema.union_schema([shapely_schema, geojson_schema, wkt_schema, wkb_schema]),
                core_schema.no_info_after_validator_function(validate, shapely_schema)],
                serialization=core_schema.plain_serializer_function_ser_schema(geojson)
            )

            return python_schema

        @classmethod
        def __get_pydantic_json_schema__(
                cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return json_schema[type_.__name__]

    return Annotation


def _typing_factory(type_: Type[BaseGeometry]):
    if type_ is LinearRing:
        # process linear ring as linestring, because linear ring is shapely made type, not well know type of geojson
        type_ = LineString

    if type_ not in (Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection):
        raise TypeError(f"only accept shapely geometry type, given {type_}")

    def _t(tag: str = "VS", valid: bool = True, non_empty: bool = True):
        """
        typing annotation factory
        Parameters
        ----------
        tag: only support char 'V' and 'S', in which 'V' stands for valid geometry and 'S' stands for non-empty(solid) geometry
        valid: another way to specify valid
        non_empty: another way to specify non-empty(solid)

        Returns
        -------
        typing annotation with pydantic validator, serializer and deserializer
        """
        tag = tag.upper()
        valid = valid and "V" in tag
        non_empty = non_empty and "S" in tag

        return Annotated[type_, _annotation(type_, assert_valid=valid, assert_non_empty=non_empty)]

    return _t


PointTF = _typing_factory(Point)
PointT = PointTF()

LineStringTF = _typing_factory(LineString)
LineStringT = LineStringTF()

LinearRingTF = _typing_factory(LinearRing)
LinearRingT = LinearRingTF()

PolygonTF = _typing_factory(Polygon)
PolygonT = PolygonTF()

MultiPointTF = _typing_factory(MultiPoint)
MultiPointT = MultiPointTF()

MultiLineStringTF = _typing_factory(MultiLineString)
MultiLineStringT = MultiLineStringTF()

MultiPolygonTF = _typing_factory(MultiPolygon)
MultiPolygonT = MultiPolygonTF()

GeometryCollectionTF = _typing_factory(GeometryCollection)
GeometryCollectionT = GeometryCollectionTF()
