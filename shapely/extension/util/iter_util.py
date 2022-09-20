"""
除标准库itertools, functools和常用库toolz之外的常用迭代器, 生成器和相关util
"""
from typing import Iterable, Tuple, Optional, Any, Callable, Union


def win_slice(iterable: Iterable,
              win_size: int = 1,
              step: int = 1,
              head_cycling: bool = False,
              tail_cycling: bool = False,
              enumerated: bool = False) -> Iterable[Tuple[Optional[Any]]]:
    """
    以窗口的形式遍历给定iterable的生成器
    Parameters
    ----------
    iterable: 可顺序遍历容器或迭代器/生成器
    win_size: 正整数, 窗口大小, 每一次迭代生成返回的值的个数.
    step: 若为True, 窗口左侧会遍历到最后一个元素, 若为False, 窗口右侧会遍历到最后一个元素. e.g. 给定[1,2,3], win_size
    head_cycling: 若为True, 窗口右侧会从第一个元素开始遍历; 若为False, 窗口左侧会从第一个元素开始遍历. e.g. 给定[1,2,3], win_size
        为2, step为1, 当head_cycling==True, 生成(3,1), (1,2), (2,3), 当head_cycling==False, 生成(1,2), (2,3)
    tail_cycling: 若为True, 窗口左侧会遍历到最后一个元素; 若为False, 窗口右侧会遍历到最后一个元素. e.g. 给定[1,2,3], win_size
        为2, step为1, 当tail_cycling==True, 生成(1,2), (2,3), (3,1), 当tail_cycling==False, 生成(1,2), (2,3)
    enumerated: 若为true, 返回值==enumerate(win_slice(...))的返回值, 若为False, 无此作用

    Returns
    -------
    iterator of tuple
    """

    def get(arr: list, idx: int, do_mod: bool):
        return arr[idx % len(arr)] if do_mod or 0 <= idx < len(arr) else None

    arr = list(iterable)
    start = 1 - win_size if head_cycling else 0
    for i in range(start, len(arr), step):
        if not tail_cycling and i + win_size - 1 >= len(arr):
            break

        do_mod = head_cycling or tail_cycling
        if enumerated:
            yield i, tuple(get(arr, j, do_mod) for j in range(i, i + win_size))
        else:
            yield tuple(get(arr, j, do_mod) for j in range(i, i + win_size))


def first(func: Callable[[Any], bool],
          iter: Iterable,
          return_idx: bool = False,
          reverse: bool = False,
          default: Optional[Any] = None
          ) -> Union[int, Any]:
    """
    返回给定容器或迭代器的第一个满足func条件的元素
    Parameters
    ----------
    func: 筛选条件, 入参为iter的元素, 返回值为bool, 若返回True, 则视为找到目标元素
    iter: 可迭代的对象, 一般为容器或迭代器
    return_idx: 若为True, 则不返回iter内的对象, 转而返回其index; 若为False, 则返回iter内对象
    reverse: 若为True, 则从后往前寻找; 若为False, 则从前往后寻找
    default: 若没有找到满足条件的元素, 返回的值, 默认为None

    Returns
    -------
    满足目标的元素或其在iter中的index, 若没有则返回给定default, 默认为None
    """

    items = list(iter)
    idx_iter = range(len(items)) if not reverse else range(len(items) - 1, -1, -1)
    for i in idx_iter:
        if func(items[i]):
            return i if return_idx else items[i]

    return default
