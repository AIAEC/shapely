from functools import cached_property


def ext_entry():
    """
    the extension entry which bundle extension descriptor as cached_property onto the BaseGeometry and all of its
    children types.

    Notice
    -------
    Since there are recursive import inside the implement of extension module, we use a magic trick to create the
    type hint (a.k.a. python stub file or *.pyi), which is:
    1. stubgen <extension-module>
    2. combine each pyi file of extension modules into extension_entry.pyi
    3. rewrite the type hint(stub) of current function in extension_entry.pyi

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
