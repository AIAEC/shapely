from copy import deepcopy

from shapely.extension.model.stretch.stretch_v3 import Stretch


class TestDeepcopy:
    def test_deepcopy_default_cargo_dict(self):
        stretch = Stretch(default_pivot_cargo_dict={'a': 1}, default_edge_cargo_dict={'b': 2},
                          default_closure_cargo_dict={'c': 3})
        copy = deepcopy(stretch)
        assert copy._default_pivot_cargo_dict == {'a': 1}
        assert copy._default_edge_cargo_dict == {'b': 2}
        assert copy._default_closure_cargo_dict == {'c': 3}
