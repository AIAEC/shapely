class GeomExtensionEntry:
    def __get__(self, instance, owner):
        # This needs to be called here to avoid circular references
        from shapely.extension.extension.base_geom_extension import BaseGeomExtension
        from shapely.extension.extension.linestring_extension import LineStringExtension
        from shapely.extension.extension.polygon_extension import PolygonExtension

        ext_type = {'LineString': LineStringExtension,
                    'Polygon': PolygonExtension}.get(instance.type, BaseGeomExtension)

        return ext_type(instance)
