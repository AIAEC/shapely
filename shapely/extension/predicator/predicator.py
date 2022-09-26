from typing import Callable

from shapely.extension.typing import GeomObj


class Predicator:
    """
    concrete predicator that can predicate(directly call it) or combine to a complex predicator
    """

    def __init__(self, func: Callable):
        self._func = func

    def __call__(self, geom_obj: GeomObj, *args, **kwargs):
        return self._func(geom_obj, *args, **kwargs)

    def __and__(self, other: 'Predicator') -> 'Predicator':
        def composite_func(geom_obj: GeomObj, *args, **kwargs):
            return self(geom_obj, *args, **kwargs) and other(geom_obj, *args, **kwargs)

        return Predicator(composite_func)

    def __or__(self, other: 'Predicator') -> 'Predicator':
        def composite_func(geom_obj: GeomObj, *args, **kwargs):
            return self(geom_obj, *args, **kwargs) or other(geom_obj, *args, **kwargs)

        return Predicator(composite_func)
