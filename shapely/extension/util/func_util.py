from collections import defaultdict
from copy import deepcopy
from itertools import chain
from operator import attrgetter
from typing import Iterable, Any, Callable, Tuple, List, Union, Sequence, Dict

from shapely.extension.util.ordered_set import OrderedSet


def separate(func: Callable[[Any], bool], items: Iterable[Any]) -> Tuple[List[Any], List[Any]]:
    """
    separate items into two list using given func, with all items of first list returns True, and all items of second
    list returns False

    Parameters
    ----------
    func: callable
    items: iterable of items

    Returns
    -------
    (List[Any], List[Any])
    """
    positive_items, negative_items = [], []
    for item in items:
        if func(item):
            positive_items.append(item)
        else:
            negative_items.append(item)
    return positive_items, negative_items


def group(grouping_func: Callable[[Any, Any], bool], items: List[Any], strict_mode: bool = False) -> List[List[Any]]:
    """
    将给定items聚类成组, 返回每一个组
    Parameters
    ----------
    grouping_func: 函数入参为item0, item1, 返回值为bool, 如果item0, item1应该在一个组, 则返回True, 否则返回False
    items: list, set, tuple等iterable的容器
    strict_mode: 默认为False, 如果为True(使用严格模式), 一个组内任意两个元素均满足grouping_func; 如果为False(宽松模式),
        一个组中每一个元素, 至少存在另一个元素与其满足grouping_func

    Returns
    -------
    [[items of group0], [items of group1], ...], 满足成组条件的items聚合成组(list), 返回所有的组(list); 注意若一个元素
    不与其他元素成组, 则他会被包含在只有一个元素的组内.
    """

    def group_helper(grouping_func: Callable[[Any, Any], bool], items: List[Any]) -> List[List[Any]]:
        result: List[List[Any]] = []

        ungrouped_indices: OrderedSet = OrderedSet(range(len(items)))
        seen: OrderedSet = OrderedSet()
        while len(ungrouped_indices) > 0:
            cur_idx = ungrouped_indices.pop()
            cur_group: List[Any] = []
            group_candidate = {cur_idx}

            while len(group_candidate) > 0:
                cand_idx = group_candidate.pop()
                seen.add(cand_idx)
                cur_group.append(items[cand_idx])

                idx_nearby_cands: OrderedSet = OrderedSet()
                for ungrouped_idx in ungrouped_indices:
                    if ungrouped_idx not in seen and grouping_func(items[ungrouped_idx], items[cand_idx]):
                        idx_nearby_cands.add(ungrouped_idx)

                ungrouped_indices.difference_update(idx_nearby_cands)
                group_candidate.update(idx_nearby_cands)

            result.append(cur_group)
        return result

    def strict_group_helper(grouping_func: Callable[[Any, Any], bool], items: List[Any]) -> List[List[Any]]:
        result: List[List[Any]] = []
        for item in items:
            for cur_group in result:
                if all(grouping_func(item, cur_item) for cur_item in cur_group):
                    cur_group.append(item)
                    break
            else:  # non cur_group satisfy if check
                result.append([item])
        return result

    return strict_group_helper(grouping_func, items) if strict_mode else group_helper(grouping_func, items)


def lfilter(func: Callable, iter: Iterable) -> List[Any]:
    """
    shortcut for list(filter(func, iter))

    Parameters
    ----------
    func: callable对象
    iter: 容器或迭代器

    Returns
    -------
    list of filter(func, iter)
    """
    return list(filter(func, iter))


def lmap(func: Callable, *iter: Iterable) -> List[Any]:
    """
    shortcut for list(map(func, iter))

    Parameters
    ----------
    func: callable对象
    iter: 容器或迭代器

    Returns
    -------
    list of map(func, iter)
    """
    return list(map(func, *iter))


def lconcat(iter: Iterable) -> List[Any]:
    """
    shortcut for list(chain.from_iterable(iter))

    Parameters
    ----------
    iter: iterable

    Returns
    -------
    list of flatten objects
    """
    return list(chain.from_iterable(iter))


def be_type(type_or_type_tuple: Union[type, Tuple[type]]) -> Callable[[Any], bool]:
    """
    return predicator function of given type or tuple[type...]

    Parameters
    ----------
    type_or_type_tuple: type | tuple[type..]

    Returns
    -------
    Callable[[Any], bool]
    """

    def predicator(item):
        return isinstance(item, type_or_type_tuple)

    return predicator


def min_max(iter: Iterable, key: Callable[[Any], Union[int, float, tuple]] = None, copied: bool = True):
    """
    一次遍历返回容器/迭代器内的最小和最大值
    Parameters
    ----------
    iter: iterable的容器或者迭代器
    key: None或lambda, 如果为None, 则排序的key为容器内元素自身. 如果不为None, 则要求key的返回值为一个可排序的元素
    copied: 为True则返回最小和最大值的deepcopy, 为False则返回引用本身.

    Returns
    -------
    tuple of 2 items, (min_item, max_item)
    """
    key = key or (lambda v: v)
    min_v, max_v = float('inf'), float('-inf')
    min_item, max_item = None, None
    for item in iter:
        item_v = key(item)
        if item_v < min_v:
            min_item = item
            min_v = item_v

        if item_v > max_v:
            max_item = item
            max_v = item_v

    if copied:
        min_item = deepcopy(min_item)
        max_item = deepcopy(max_item)

    return [min_item, max_item]


def groupby(key: Callable[[object], object], seq: Sequence[object]) -> Dict[object, List[object]]:
    """
    group the item of the given sequence by return of key function

    Parameters
    ----------
    key: callable, given single object, returns hashable object
    seq: sequence of objects

    Returns
    -------
    Dict[object, List[object]], with key being the mapped value, value to be the list of objects
    """
    if not callable(key):
        key = attrgetter(key)
    d = defaultdict(lambda: [].append)
    for item in seq:
        d[key(item)](item)
    rv = {}
    for k, v in d.items():
        rv[k] = v.__self__
    return rv


def sign(expr: Any, reverse: bool = False) -> int:
    """
    shortcut for (expr ? 1 : -1)
    Parameters
    ----------
    expr: expression
    reverse: whether do (expr ? -1: 1) instead

    Returns
    -------
    1 or -1
    """
    return 1 if expr ^ reverse else -1
