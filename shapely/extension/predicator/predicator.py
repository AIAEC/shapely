from shapely.geometry.base import BaseGeometry


class Predicator:
    """
    concrete predicator that can predicate(directly call it) or combine to a complex predicator
    """

    def __init__(self, func):
        self._func = func

    def __call__(self, geom: BaseGeometry, *args, **kwargs):
        return self._func(geom, *args, **kwargs)

    def __and__(self, other: 'Predicator') -> 'Predicator':
        def composite_func(geom: BaseGeometry):
            return self(geom) and other(geom)

        return Predicator(composite_func)

    def __or__(self, other: 'Predicator') -> 'Predicator':
        def composite_func(geom: BaseGeometry):
            return self(geom) or other(geom)

        return Predicator(composite_func)
