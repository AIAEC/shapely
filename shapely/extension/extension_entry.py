from functools import cached_property


def ext_entry():
    """
    the extension entry which bundle extension descriptor as cached_property onto the BaseGeometry and all of its
    children types.

    Notice
    -------
    Since there are recursive import inside the implement of extension module, we create a pyi file (stub file) of
    current module and add the return typing of current function

    Returns
    -------
    cached_property that has wrapped helper as its __get__
    """

    def helper(instance):
        # This needs to be called here to avoid circular references
        from shapely.extension.extension.base_geom_extension import BaseGeomExtension
        from shapely.extension.extension.linestring_extension import LineStringExtension
        from shapely.extension.extension.polygon_extension import PolygonExtension

        ext_type = {'LineString': LineStringExtension,
                    'LinearRing': LineStringExtension,
                    'Polygon': PolygonExtension}.get(instance.type, BaseGeomExtension)

        return ext_type(instance)

    return cached_property(helper)
