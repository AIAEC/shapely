from typing import Callable

from toolz import identity

from shapely.extension.predicator.predicator import Predicator
from shapely.extension.typing import GeomObj
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE


class RelationPredicatorCreator:
    """
    predicator creator for geometry bool predication
    """

    def __init__(self, geom: BaseGeometry):
        self._geom = geom

    @staticmethod
    def rect_buffer(geom: BaseGeometry, buffer_dist: float):
        return geom.buffer(float(buffer_dist),
                           cap_style=CAP_STYLE.flat,
                           join_style=JOIN_STYLE.mitre)

    def _predicator_func(self, method_name: str, self_buffer: float = 0., other_buffer: float = 0.):
        def _func(geom_obj: GeomObj, attr_getter: Callable[[object], BaseGeometry] = identity):
            self_geom_buffered = self.rect_buffer(self._geom, self_buffer)
            other_geom_buffered = self.rect_buffer(attr_getter(geom_obj), other_buffer)
            return getattr(self_geom_buffered, method_name)(other_geom_buffered)

        return _func

    def intersects(self, self_buffer: float = 0., component_buffer: float = 0.) -> Predicator:
        """
        create predicator that predicate the geometry bool relationship of current geometry and further given geometry
        Parameters
        ----------
        self_buffer: current geometry's buffer distance
        component_buffer: further given geometry's buffer distance

        Returns
        -------
        predicator instance
        """
        return Predicator(self._predicator_func('intersects', self_buffer, component_buffer))
