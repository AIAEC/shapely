from shapely.extension.extension.base_geom_extension import BaseGeomExtension
from shapely.extension.strategy.polygonize_strategy import (
    ShapelyPolygonizeStrategy, ConvexHullStrategy, MouldStrategy, ClosingEndPointsStrategy)
from shapely.extension.util.polygonize import Polygonize
from shapely.geometry.base import BaseGeometry


class MultiPartGeomExtension(BaseGeomExtension):

    def polygonize(self, default_strategy=True) -> Polygonize:
        """
        poligonize the geom or geom list
        Parameters
        ----------
        default_strategy: True for auto adding 4 strategies, False for no strategy

        Returns
        -------
        Polygonize instance
        """
        geoms = self._geom
        if isinstance(self._geom, BaseGeometry):
            geoms = [self._geom]

        if default_strategy:
            return (Polygonize(geoms).add_strategy(ShapelyPolygonizeStrategy())
                    .add_strategy(ConvexHullStrategy())
                    .add_strategy(MouldStrategy())
                    .add_strategy(ClosingEndPointsStrategy()))
        return Polygonize(geoms)
