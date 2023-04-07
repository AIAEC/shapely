from shapely.extension.functional import seq


class A:
    def __init__(self, x):
        self.x = x

    def __iter__(self):
        return self

    def __lt__(self, other):
        return self.x < other.x


class TestPipeLine:
    objs = [A(1), A(2), A(-3)]

    def test_min_max(self):
        max_by_element = seq(self.objs).max_by(lambda a: a.x ** 2)
        assert isinstance(max_by_element, A)
        assert max_by_element.x == -3
        assert max_by_element is self.objs[2]

        min_by_element = seq(self.objs).min_by(lambda a: a.x ** 2)
        assert isinstance(min_by_element, A)
        assert min_by_element.x == 1
        assert min_by_element is self.objs[0]

        max_element = seq(self.objs).max()
        assert isinstance(max_element, A)
        assert max_element.x == 2
        assert max_element is self.objs[1]

        min_element = seq(self.objs).min()
        assert isinstance(min_element, A)
        assert min_element.x == -3
        assert min_element is self.objs[2]

    def test_get_items(self):
        first_item = seq(self.objs)[0]
        assert isinstance(first_item, A)
        assert first_item.x == 1
        assert first_item is self.objs[0]

        first_item = seq(self.objs).first()
        assert isinstance(first_item, A)
        assert first_item.x == 1
        assert first_item is self.objs[0]

        first_item = seq(self.objs).head()
        assert isinstance(first_item, A)
        assert first_item.x == 1
        assert first_item is self.objs[0]

        last_item = seq(self.objs).last()
        assert isinstance(last_item, A)
        assert last_item.x == -3
        assert last_item is self.objs[2]


