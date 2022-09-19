from collections import defaultdict
from copy import deepcopy
from functools import partial
from itertools import filterfalse, chain
from operator import attrgetter
from typing import Iterable, Any, Callable, Tuple, List, Set, Union, Optional, Sequence, Dict


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

    :param grouping_func: 函数入参为item0, item1, 返回值为bool, 如果item0, item1应该在一个组, 则返回True, 否则返回False
    :param items: list, set, tuple等iterable的容器
    :param strict_mode: 默认为False, 如果为True(使用严格模式), 一个组内任意两个元素均满足grouping_func; 如果为False(宽松模式),
        一个组中每一个元素, 至少存在另一个元素与其满足grouping_func
    :return: [[items of group0], [items of group1], ...], 满足成组条件的items聚合成组(list), 返回所有的组(list); 注意若一个元素
        不与其他元素成组, 则他会被包含在只有一个元素的组内.
    """

    def group_helper(grouping_func: Callable[[Any, Any], bool], items: List[Any]) -> List[List[Any]]:
        result: List[List[Any]] = []

        ungrouped_indices: Set[int] = set(range(len(items)))
        seen: Set[int] = set()
        while len(ungrouped_indices) > 0:
            cur_idx = ungrouped_indices.pop()
            cur_group: List[Any] = []
            group_candidate = {cur_idx}

            while len(group_candidate) > 0:
                cand_idx = group_candidate.pop()
                seen.add(cand_idx)
                cur_group.append(items[cand_idx])

                idx_nearby_cands = set()
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


def fuse(predicate_func: Callable[[Any, Any], bool],
         fuse_func: Callable[[Any, Any], Any],
         items: Iterable[Any]) -> List[Any]:
    """
    迭代items, 将满足predicate_func的两个item通过fuse_func融合到一起, 持续迭代直到没有fuse发生
    :param predicate_func: 判定两个item是否应该融合的方法
    :param fuse_func: 计算两个item融合结果的方法
    :param items: items
    :return: list of fused items
    """
    fusing_candidates = items

    fusing_finished: bool = False
    while not fusing_finished:
        fusion_items = []

        for i, fusing_cand in enumerate(fusing_candidates):
            for j, fusion_item in enumerate(fusion_items):
                if predicate_func(fusing_cand, fusion_item):
                    fusion_items[j] = fuse_func(fusing_cand, fusion_item)
                    break
            else:  # left_item cannot be converged into any converged_item
                fusion_items.append(fusing_cand)

        fusing_finished = len(fusion_items) == len(fusing_candidates)
        fusing_candidates = fusion_items

    return fusion_items


def lfilter(func: Callable, iter: Iterable) -> List[Any]:
    """
    shortcut for list(filter(func, iter))

    :param func: callable对象
    :param iter: 容器或迭代器
    :return: list of filter(func, iter)
    """
    return list(filter(func, iter))


def lfilter_out(func: Callable, iter: Iterable) -> List[Any]:
    """
    shortcut for list(filterfalse(func, iter))

    :param func: callable对象
    :param iter: 容器或迭代器
    :return: list of filterfalse(func, iter)
    """
    return list(filterfalse(func, iter))


def lmap(func: Callable, *iter: Iterable) -> List[Any]:
    """
    shortcut for list(map(func, iter))

    :param func: callable对象
    :param iter: 容器或迭代器
    :return: list of map(func, iter)
    """
    return list(map(func, *iter))


def for_each(func: Callable, iterable: Iterable, raise_on_error: bool = True) -> None:
    """

    :param func: callable对象
    :param iterable: 容器或迭代器
    :param raise_on_error: 设为false时忽略error,继续执行剩余的迭代器
    :return: None
    """
    for element in iterable:
        try:
            func(element)
        except Exception:
            if raise_on_error:
                raise Exception
            continue


def lconcat(iter: Iterable) -> List[Any]:
    return list(chain.from_iterable(iter))


def map_by(func: Callable) -> Callable[[Iterable[Any]], Iterable[Any]]:
    """
    返回函数 partial(map, func), 主要用于方便生成一些偏函数
    :param func:
    :return:
    """
    return partial(map, func)


def be_type(type_or_type_tuple: Union[type, Tuple[type]]) -> Callable[[Any], bool]:
    """
    返回判定类型的偏函数, 返回函数等同于lambda item: isinstance(item, type_or_type_tuple)
    :param type_or_type_tuple:
    :return:
    """

    def predicator(item):
        return isinstance(item, type_or_type_tuple)

    return predicator


def min_max(iter: Iterable, key: Callable[[Any], Union[int, float, tuple]] = None, copied: bool = True):
    """
    一次遍历返回容器/迭代器内的最小和最大值

    :param iter: iterable的容器或者迭代器
    :param key: None或lambda, 如果为None, 则排序的key为容器内元素自身. 如果不为None, 则要求key的返回值为一个可排序的元素
    :param copied: 为True则返回最小和最大值的deepcopy, 为False则返回引用本身.
    :return: tuple of 2 items, (min_item, max_item)
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


class Countdown:
    """
    通用倒数计数器, 可用于编写安全的while语句
    """

    def __init__(self, time: int, count_to_0_callback_func: Optional[Callable] = None):
        """
        倒计时次数

        :param time: 正整数, 若设定为0或负数, 则计数会直接停止(tick() == False), 若传入float, 则仅取其整数部分
        """
        self._time = time
        self._count_to_0_callback_func: Optional[Callable] = count_to_0_callback_func

    def __repr__(self):
        return f'Countdown({self._time})'

    def set_count_to_0_callback(self, func) -> 'Countdown':
        self._count_to_0_callback_func = func
        return self

    def tick(self) -> bool:
        """
        倒数一次

        :return: 若计数大于0, 则返回True; 若计数<=0, 则返回False
        """
        time = self._time
        self._time -= 1

        if time <= 0 and self._count_to_0_callback_func:
            self._count_to_0_callback_func()

        return time > 0

    def __call__(self, condition: bool):
        """
        若计数大于0且condition为True, 则返回True. 类似于给condition增加安全计数属性.

        常见用法:

        >>> safe_guard = Countdown(10)
        ... while safe_guard(True):  # safe_guard embraces a bool expr
        ...     pass

        :param condition: boolean value
        :return: boolean value
        """

        return bool(condition) and self.tick()

    def __bool__(self):
        """
        和调用tick相同, 仅将此对象放入bool表达式中就会有调用tick的效果

        :return:
        """
        return self.tick()


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
    符号函数
    :param expr: bool表达式
    :param reverse: 若翻转, 则会对表达式求反
    :return: expr为True, 返回1, expr为False, 返回-1
    """
    return 1 if expr ^ reverse else -1
