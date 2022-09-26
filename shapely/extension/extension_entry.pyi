from typing import Union

from shapely.extension.extension import BaseGeomExtension, LineStringExtension, PolygonExtension


def ext_entry() -> Union[BaseGeomExtension, LineStringExtension, PolygonExtension]: ...
