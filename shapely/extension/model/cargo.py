from collections import Counter
from copy import deepcopy
from operator import itemgetter
from typing import Any, Sequence, Union, Optional
from uuid import uuid4

from shapely.extension.util.iter_util import first


class Cargo:
    def __init__(self, data=None, host=None, default=None, verbose=True):
        self._data = data or {}
        self._id = uuid4()
        self._host = host
        self._default = default
        self._verbose = verbose

    def __repr__(self):
        return f'Cargo@{str(self._id)[:4]}{self._data}'

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if not isinstance(other, Cargo):
            return False
        return self._id == other._id

    def data_equals(self, other: Union['Cargo', dict]):
        if not isinstance(other, (dict, Cargo)):
            return False
        if isinstance(other, Cargo):
            other = dict(other)

        return self._data == other

    def __getitem__(self, item):
        return self._data.get(item, self._default)

    def __setitem__(self, key, value):
        if self._verbose:
            print(f'{self}: set {key} -> {value}')
        self._data[key] = value

    def __iter__(self):
        return iter(self._data)

    @property
    def host(self):
        return self._host

    def copy(self) -> 'Cargo':
        return Cargo(data=deepcopy(self._data), host=self._host, default=self._default)

    def setdefault(self, key, default):
        return self._data.setdefault(key, default)

    def pop(self, key) -> Any:
        if key not in self._data:
            return None

        if self._verbose:
            print(f'{self}: pop key {key}')
        return self._data.pop(key)

    def popitem(self) -> Any:
        if self._data:
            key, val = self._data.popitem()
            if self._verbose:
                print(f'{self}: popitem {key} -> {val}')
        return None, None

    def get(self, key, default=None):
        return self._data.get(key, default or self._default)

    def update(self, *args, **kwargs):
        if self._verbose:
            print(f'{self}: update by {args}, {kwargs}')
        self._data.update(*args, **kwargs)

    def values(self):
        return self._data.values()

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def clear(self):
        if self._verbose:
            print(f'{self}: remove all')
        self._data.clear()

    def __len__(self):
        return len(self._data)

    def overlap(self, cargo: 'Cargo', keys: Optional[Sequence[Any]] = None):
        if not isinstance(cargo, Cargo):
            raise TypeError(f'expect cargo instance, given {cargo}')

        if self._verbose:
            print(f'{self}: copy to {cargo}')

        data_copy = deepcopy(self._data)
        keys = keys or list(self._data.keys())

        for key in keys:
            if key in data_copy:
                cargo._data[key] = data_copy[key]


class ConsensusCargo(Cargo):
    def __init__(self, cargos: Sequence[Cargo]):
        self._cargos = cargos

        board = {}
        for cargo in cargos:
            for key, val in cargo.items():
                value_counts = board.setdefault(key, [])
                idx = first(lambda val_count_pair: val_count_pair[0] == val,
                            return_idx=True,
                            default=None,
                            iter=value_counts)
                if idx is None:
                    value_counts.append([val, 1])
                else:
                    value_counts[idx][1] += 1

        data = {key: max(value_counts, key=itemgetter(1))[0] for key, value_counts in board.items()}
        host = Counter([cargo._host for cargo in cargos]).most_common(1)[0][0]  # most common host
        default = Counter([cargo._default for cargo in cargos]).most_common(1)[0][0]  # most common default
        verbose = sum([cargo._verbose for cargo in cargos]) > len(cargos) / 2

        super().__init__(data, host, default, verbose)

    def sync(self, keys: Optional[Sequence[Any]] = None):
        for cargo in self._cargos:
            self.overlap(cargo, keys=keys)
