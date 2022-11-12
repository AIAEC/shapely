from copy import deepcopy

import pytest

from shapely.extension.util.ordered_set import OrderedSet


class TestOrderedSet:
    def test_add(self):
        set_ = OrderedSet()
        assert len(set_) == 0

        set_.add(1)
        assert len(set_) == 1

        with pytest.raises(TypeError):
            set_.add([])

    def test_contains(self):
        set_ = OrderedSet([1, 2, 3])
        assert 1 in set_
        assert 2 in set_
        assert 3 in set_
        assert 4 not in set_

    def test_difference_update(self):
        set_ = OrderedSet([1, 2, 3])
        set_.difference_update({1, 2})
        assert len(set_) == 1
        assert 3 in set_

    def test_pop(self):
        set_ = OrderedSet([1, 2, 3])
        assert set_
        assert set_.pop() == 3
        assert set_.pop() == 2
        assert set_.pop() == 1
        assert not set_

    def test_iter(self):
        set_ = OrderedSet([1, 2, 3])
        for _ in range(10):
            assert [1, 2, 3] == list(set_)

    def test_discard(self):
        set_ = OrderedSet([1, 2, 3])
        set_.discard(5)
        assert len(set_) == 3

        set_.discard(1)
        assert len(set_) == 2
        assert 1 not in set_

    def test_deepcopy(self):
        set0 = OrderedSet([1, 2, 3])
        set1 = OrderedSet(set0)
        set0.discard(1)
        assert len(set1) == 3

        set2 = deepcopy(set1)
        set1.discard(1)
        assert len(set2) == 3

    def test_iter(self):
        set0 = OrderedSet([1, 2, 3])
        assert list(set0) == [1, 2, 3]
