from typing import Union

from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.extension.linestring_extension import LineStringExtension
from shapely.extension.extension.polygon_extension import PolygonExtension
from shapely.extension.extension.multipart_geom_extension import MultiPartGeomExtension


def ext_entry() -> Union[BaseGeomExtension, LineStringExtension, PolygonExtension, MultiPartGeomExtension]: ...
