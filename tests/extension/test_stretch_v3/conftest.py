from collections import OrderedDict

import pytest

from shapely.extension.model.stretch.stretch_v3 import Stretch, Pivot, Edge, EdgeSeq, Closure
from shapely.wkt import loads


@pytest.fixture
def stretch_4_dangling_pivots() -> Stretch:
    """
    Returns
    -------
    3             2
     o           o


     o           o
    0             1
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_8_dangling_pivots() -> Stretch:
    """
    Returns
    -------
     3                 2
     o                 o

      7   6
       o o
       o o
      4   5
     o                 o
     0                 1
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((10, 0), stretch, '1'),
              Pivot((10, 10), stretch, '2'),
              Pivot((0, 10), stretch, '3'),
              Pivot((1, 1), stretch, '4'),
              Pivot((2, 1), stretch, '5'),
              Pivot((2, 2), stretch, '6'),
              Pivot((1, 2), stretch, '7')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])
    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_8_dangling_edges(stretch_8_dangling_pivots) -> Stretch:
    """
    Parameters
    ----------
    stretch_8_dangling_pivots: stretch fixture

    Returns
    -------
     3                 2
     o◄────────────────o
     │                 ▲
     │                 │
     │                 │
     │7   6            │
     │ o─►             │
     │ ▲ ▼             │
     │ ◄─o             │
     ▼4   5            │
     o────────────────►o
     0                 1
    """
    stretch = stretch_8_dangling_pivots
    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '7', stretch),
        Edge('7', '6', stretch),
        Edge('6', '5', stretch),
        Edge('5', '4', stretch),
    ]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_4_dangling_edge() -> Stretch:
    """
    Returns
    -------
     3             2
      o◄──────────o
      │           ▲
      ▼           │
      o──────────►o
     0             1
     """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [Edge('0', '1', stretch),
             Edge('1', '2', stretch),
             Edge('2', '3', stretch),
             Edge('3', '0', stretch)]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])
    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_back_and_forth_edge_seq() -> Stretch:
    """
    Returns
    -------
               o2
               ▲─┐
               │ │
               │ │
               │ │
     o┌───────►o◄┘
     0◄───────┘1
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('1', '0', stretch),
        Edge('2', '1', stretch)]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_box() -> Stretch:
    """
    Returns
    -------
     3             2
      ┌───────────┐
      │           │
      │           │
      └───────────┘
     0             1
     """
    stretch = Stretch()

    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [Edge('0', '1', stretch),
             Edge('1', '2', stretch),
             Edge('2', '3', stretch),
             Edge('3', '0', stretch)]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    exterior_seq = EdgeSeq(edges)

    closure = Closure(exterior_seq, stretch, '0')
    stretch._closure_map = OrderedDict([(closure.id, closure)])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_box_holes() -> Stretch:
    """
    Returns
    -------
     3                               2
      ┌─────────────────────────────┐
      │                             │
      │                             │
      │                             │
      │                       11  10│
      │                         ┌─┐ │
      │                         └─┘ │
      │                        8   9│
      │   7   6                     │
      │    ┌─┐                      │
      │    └─┘                      │
      │   4   5                     │
      └─────────────────────────────┘
     0                               1
    """
    stretch = Stretch()

    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((10, 0), stretch, '1'),
              Pivot((10, 10), stretch, '2'),
              Pivot((0, 10), stretch, '3'),
              Pivot((2, 2), stretch, '4'),
              Pivot((3, 2), stretch, '5'),
              Pivot((3, 3), stretch, '6'),
              Pivot((2, 3), stretch, '7'),
              Pivot((8, 5), stretch, '8'),
              Pivot((9, 5), stretch, '9'),
              Pivot((9, 6), stretch, '10'),
              Pivot((8, 6), stretch, '11')]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [Edge('0', '1', stretch),
             Edge('1', '2', stretch),
             Edge('2', '3', stretch),
             Edge('3', '0', stretch),
             Edge('7', '6', stretch),
             Edge('6', '5', stretch),
             Edge('5', '4', stretch),
             Edge('4', '7', stretch),
             Edge('11', '10', stretch),
             Edge('10', '9', stretch),
             Edge('9', '8', stretch),
             Edge('8', '11', stretch)]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])
    exterior_seq = EdgeSeq(edges[:4])
    interior_seq_1 = EdgeSeq(edges[4:8])
    interior_seq_2 = EdgeSeq(edges[8:])

    closure = Closure(exterior=exterior_seq,
                      interiors=[interior_seq_1, interior_seq_2],
                      stretch=stretch,
                      id_='0')
    stretch._closure_map = OrderedDict([(closure.id, closure)])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_box_with_inner_crack() -> Stretch:
    """
    Returns
    -------
      3              2
      ┌──────────────┐
      │              │
      │     6        │
      │    │         │
      │   5└─────4   │
      │              │
      └──────────────┘
      0              1
     """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((10, 0), stretch, '1'),
              Pivot((10, 10), stretch, '2'),
              Pivot((0, 10), stretch, '3'),
              Pivot((8, 3), stretch, '4'),
              Pivot((3, 3), stretch, '5'),
              Pivot((3, 6), stretch, '6')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '5', stretch),
        Edge('5', '4', stretch), ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    exterior_seq = EdgeSeq(edges[:4])
    interior_seq0 = EdgeSeq(edges[4:])
    closure = Closure(exterior=exterior_seq,
                      interiors=[interior_seq0],
                      stretch=stretch,
                      id_='0')
    stretch._closure_map = OrderedDict([(closure.id, closure)])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_box_with_exterior_crack() -> Stretch:
    """
    Returns
    -------
      3             2
      ┌─────────────┐
      │             │
      │             │
      │      │5     │
      │      │      │
      └──────┴──────┘
      0      4      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((10, 10), stretch, '2'),
        Pivot((0, 10), stretch, '3'),
        Pivot((5, 0), stretch, '4'),
        Pivot((5, 5), stretch, '5'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '4', stretch),
        Edge('4', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges), stretch=stretch, id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_2_disjoint_boxes() -> Stretch:
    """
    Returns
    -------
     3      2   7      6
     ┌──────┐   ┌──────┐
     │      │   │      │
     └──────┘   └──────┘
     0      1   4      5
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3'),
              Pivot((3, 0), stretch, '4'),
              Pivot((4, 0), stretch, '5'),
              Pivot((4, 1), stretch, '6'),
              Pivot((3, 1), stretch, '7')]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '4', stretch), ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]), stretch=stretch, id_='0'),
        Closure(exterior=EdgeSeq(edges[4:]), stretch=stretch, id_='1'), ]
    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_2_boxes() -> Stretch:
    """
    Returns
    -------
     3            2          5
     ┌───────────┬───────────┐
     │           │           │
     │           │           │
     └───────────┴───────────┘
     0            1          4
    """
    stretch = Stretch()

    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3'),
              Pivot((2, 0), stretch, '4'),
              Pivot((2, 1), stretch, '5')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [Edge('0', '1', stretch),
             Edge('1', '2', stretch),
             Edge('2', '3', stretch),
             Edge('3', '0', stretch),
             Edge('1', '4', stretch),
             Edge('4', '5', stretch),
             Edge('5', '2', stretch),
             Edge('2', '1', stretch),
             ]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    exterior_seq0 = EdgeSeq(edges[:4])
    exterior_seq1 = EdgeSeq(edges[4:])
    closure0 = Closure(exterior=exterior_seq0, stretch=stretch, id_='0')
    closure1 = Closure(exterior=exterior_seq1, stretch=stretch, id_='1')
    stretch._closure_map = OrderedDict([(closure0.id, closure0), (closure1.id, closure1)])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_with_2_adjacent_concave_boxes() -> Stretch:
    """
    Returns
    -------
     7            6           9
      ┌───────────┬──────────┐
      │           │          │
      │        4┌─┴─┐10      │
      │         │ 5 │        │
      │         │ 2 │        │
      │        3└─┬─┘11      │
      │           │          │
      └───────────┴──────────┘
     0            1           8
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 0.3), stretch, '2'),
              Pivot((0.8, 0.3), stretch, '3'),
              Pivot((0.8, 0.7), stretch, '4'),
              Pivot((1, 0.7), stretch, '5'),
              Pivot((1, 1), stretch, '6'),
              Pivot((0, 1), stretch, '7'),
              Pivot((2, 0), stretch, '8'),
              Pivot((2, 1), stretch, '9'),
              Pivot((1.2, 0.7), stretch, '10'),
              Pivot((1.2, 0.3), stretch, '11')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '0', stretch),
        Edge('1', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '6', stretch),
        Edge('6', '5', stretch),
        Edge('5', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '2', stretch),
        Edge('2', '1', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:8]), stretch=stretch, id_='0'),
        Closure(exterior=EdgeSeq(edges[8:]), stretch=stretch, id_='1'),
    ]
    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_outer_and_inner_closures() -> Stretch:
    """
    Returns
    -------
     3┌───────────────────────┐2
      │                       │
      │          7┌───┐6      │
      │           │ h │       │
      │          4└───┘5      │
      │                       │
      │                       │
     0└───────────────────────┘1
    """
    stretch = Stretch()
    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3'),
              Pivot((0.5, 0.5), stretch, '4'),
              Pivot((0.6, 0.5), stretch, '5'),
              Pivot((0.6, 0.6), stretch, '6'),
              Pivot((0.5, 0.6), stretch, '7')]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '7', stretch),
        Edge('7', '6', stretch),
        Edge('6', '5', stretch),
        Edge('5', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '4', stretch),
    ]
    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]), stretch=stretch, id_='0', interiors=[EdgeSeq(edges[4:8])]),
        Closure(exterior=EdgeSeq(edges[8:]), stretch=stretch, id_='1'),
    ]
    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_for_closure_strategy() -> Stretch:
    """
    Returns
    -------
     3                                          2
      ┌────────────────────────────────────────┐
      │                                        │
      │      22             15            14   │
      │       ┌─────────────┬────────────┐     │
      │       │  21     20  │            │     │
      │       │   ┌─────┐   │   16       │     │
      │       │   │ 18  │   │  /         │     │
      │       │   └──┬──┘   │ /          │     │
      │       │  17  │  19  │/           │     │
      │       ├──────┴──────┼────────────┤13   │
      │       │9     8     7│            │     │
      │       │             │     11     │     │
      │       │             │            │     │
      │       │             │     │      │     │
      │       │             │     │      │     │
      │  ─────┴─────────────┴─────┴──────┘     │
      │  4    5             6     10     12    │
      │                                        │
      └────────────────────────────────────────┘
     0                                          1
    """
    stretch = Stretch()
    multi_points = loads(
        'MULTIPOINT ((0 0), (40 0), (40 40), (0 40), (5 10), (10 10), (20 10), (20 20), (15 20), (10 20), (25 10), (25 15), (30 10), (30 20), (30 30), (20 30), (25 25), (13 23), (15 23), (17 23), (17 27), (13 27), (10 30))')
    pivots = [Pivot(point, stretch, str(i)) for i, point in enumerate(multi_points.geoms)]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    exterior_edges_of_largest = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
    ]

    interior_edges_of_largest = [
        Edge('22', '15', stretch),
        Edge('15', '14', stretch),
        Edge('14', '13', stretch),
        Edge('13', '12', stretch),
        Edge('12', '10', stretch),
        Edge('10', '6', stretch),
        Edge('6', '5', stretch),
        Edge('5', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '9', stretch),
        Edge('9', '22', stretch),
    ]

    edges_of_inner_normal = [
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '5', stretch),
    ]

    edges_of_closure_with_crack = [
        Edge('6', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '10', stretch),
        Edge('10', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '7', stretch),
        Edge('7', '6', stretch),
    ]

    edges_of_closure_with_skew_crack = [
        Edge('13', '14', stretch),
        Edge('14', '15', stretch),
        Edge('15', '7', stretch),
        Edge('7', '16', stretch),
        Edge('16', '7', stretch),
        Edge('7', '13', stretch),
    ]

    edges_of_closure_with_inner_loop = [
        Edge('7', '15', stretch),
        Edge('15', '22', stretch),
        Edge('22', '9', stretch),
        Edge('9', '8', stretch),
        Edge('8', '18', stretch),
        Edge('18', '17', stretch),
        Edge('17', '21', stretch),
        Edge('21', '20', stretch),
        Edge('20', '19', stretch),
        Edge('19', '18', stretch),
        Edge('18', '8', stretch),
        Edge('8', '7', stretch),
    ]

    all_edges = (exterior_edges_of_largest
                 + interior_edges_of_largest
                 + edges_of_inner_normal
                 + edges_of_closure_with_crack
                 + edges_of_closure_with_skew_crack
                 + edges_of_closure_with_inner_loop)
    stretch._edge_map = OrderedDict([(e.id, e) for e in all_edges])

    largest_closure = Closure(exterior=EdgeSeq(exterior_edges_of_largest),
                              interiors=[EdgeSeq(interior_edges_of_largest)],
                              stretch=stretch,
                              id_='0')
    inner_normal_closure = Closure(exterior=EdgeSeq(edges_of_inner_normal),
                                   stretch=stretch,
                                   id_='1')
    closure_with_crack = Closure(exterior=EdgeSeq(edges_of_closure_with_crack),
                                 stretch=stretch,
                                 id_='2')
    closure_with_skew_crack = Closure(exterior=EdgeSeq(edges_of_closure_with_skew_crack),
                                      stretch=stretch,
                                      id_='3')
    closure_with_inner_loop = Closure(exterior=EdgeSeq(edges_of_closure_with_inner_loop),
                                      stretch=stretch,
                                      id_='4')
    stretch._closure_map = OrderedDict([(largest_closure.id, largest_closure),
                                        (inner_normal_closure.id, inner_normal_closure),
                                        (closure_with_crack.id, closure_with_crack),
                                        (closure_with_skew_crack.id, closure_with_skew_crack),
                                        (closure_with_inner_loop.id, closure_with_inner_loop)])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_hit_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     0           1              2           3
    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 20), stretch, '4'),
        Pivot((0, 20), stretch, '5'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges), stretch=stretch, id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_hit_with_reverse_closure(stretch_exterior_offset_hit_hit_no_reverse_closure) -> Stretch:
    """
    Parameters
    ----------
    stretch_exterior_offset_hit_hit_no_reverse_closure

    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     │0          1              2          3│
     │                                      │
     o──────────────────────────────────────o
     6                                      7
    """
    stretch = stretch_exterior_offset_hit_hit_no_reverse_closure

    new_pivots = [
        Pivot((0, -10), stretch, '6'),
        Pivot((30, -10), stretch, '7'),
    ]

    stretch._pivot_map.update(OrderedDict([(p.id, p) for p in new_pivots]))

    new_edges = [
        Edge('6', '7', stretch),
        Edge('7', '3', stretch),
        Edge('3', '2', stretch),
        Edge('2', '1', stretch),
        Edge('1', '0', stretch),
        Edge('0', '6', stretch),
    ]

    stretch._edge_map.update(OrderedDict([(e.id, e) for e in new_edges]))

    new_closures = [
        Closure(exterior=EdgeSeq(new_edges), stretch=stretch, id_='1'),
    ]

    stretch._closure_map.update(OrderedDict([(c.id, c) for c in new_closures]))
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_in_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │                                      │
     │                                      │
     │                     6┌───────┐7      │
     │                      │   h   │       │
     │                      │       │       │
     │                     9└───────┘8      │
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     0           1              2           3
    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 20), stretch, '4'),
        Pivot((0, 20), stretch, '5'),
        Pivot((18, 12), stretch, '6'),
        Pivot((22, 12), stretch, '7'),
        Pivot((22, 8), stretch, '8'),
        Pivot((18, 8), stretch, '9'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '6', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]), interiors=[EdgeSeq(edges[6:])], stretch=stretch, id_='0'),
    ]
    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_in_with_reverse_closure(stretch_exterior_offset_hit_in_no_reverse_closure) -> Stretch:
    """
    Parameters
    ----------
    stretch_exterior_offset_hit_in_no_reverse_closure

    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │                                      │
     │                                      │
     │                     6┌───────┐7      │
     │                      │   h   │       │
     │                      │       │       │
     │                     9└───────┘8      │
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     │0          1              2          3│
     │                                      │
     o──────────────────────────────────────o
     10                                    11
    """
    stretch = stretch_exterior_offset_hit_in_no_reverse_closure

    new_pivots = [
        Pivot((0, -10), stretch, '10'),
        Pivot((30, -10), stretch, '11'),
    ]

    stretch._pivot_map.update(OrderedDict([(p.id, p) for p in new_pivots]))

    new_edges = [
        Edge('10', '11', stretch),
        Edge('11', '3', stretch),
        Edge('3', '2', stretch),
        Edge('2', '1', stretch),
        Edge('1', '0', stretch),
        Edge('0', '10', stretch),
    ]

    stretch._edge_map.update(OrderedDict([(e.id, e) for e in new_edges]))

    new_closures = [
        Closure(exterior=EdgeSeq(new_edges), stretch=stretch, id_='1'),
    ]

    stretch._closure_map.update(OrderedDict([(c.id, c) for c in new_closures]))
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_out_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
     7                  6
     o──────────────────o
     │                  │
     │                  │
     │                  │
     │                  │
     │                  │
     │                  │                   4
     │                5 o───────────────────o
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     0           1              2           3
    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 5), stretch, '4'),
        Pivot((15, 5), stretch, '5'),
        Pivot((15, 20), stretch, '6'),
        Pivot((0, 20), stretch, '7'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges), stretch=stretch, id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_exterior_offset_hit_out_with_reverse_closure(stretch_exterior_offset_hit_out_no_reverse_closure) -> Stretch:
    """
    Parameters
    ----------
    stretch_exterior_offset_hit_out_no_reverse_closure
    Returns
    -------
     7                  6
     o──────────────────o
     │                  │
     │                  │
     │                  │
     │                  │
     │                  │
     │                  │                   4
     │                5 o───────────────────o
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     │0          1              2          3│
     │                                      │
     o──────────────────────────────────────o
     8                                      9
    """
    stretch = stretch_exterior_offset_hit_out_no_reverse_closure

    new_pivots = [
        Pivot((0, -10), stretch, '8'),
        Pivot((30, -10), stretch, '9'),
    ]

    stretch._pivot_map.update(OrderedDict([(p.id, p) for p in new_pivots]))

    new_edges = [
        Edge('8', '9', stretch),
        Edge('9', '3', stretch),
        Edge('3', '2', stretch),
        Edge('2', '1', stretch),
        Edge('1', '0', stretch),
        Edge('0', '8', stretch),
    ]

    stretch._edge_map.update(OrderedDict([(e.id, e) for e in new_edges]))

    closures = [
        Closure(exterior=EdgeSeq(new_edges), stretch=stretch, id_='1'),
    ]

    stretch._closure_map.update(OrderedDict([(c.id, c) for c in closures]))

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_exterior_offset_in_in_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │                                      │
     │                                      │
     │     10┌───────┐11   6┌───────┐7      │
     │       │   h   │      │   h   │       │
     │       │       │      │       │       │
     │     13└───────┘12   9└───────┘8      │
     │                                      │
     │                                      │
     o───────────o──────────────o───────────o
     0           1              2           3
    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 20), stretch, '4'),
        Pivot((0, 20), stretch, '5'),
        Pivot((18, 12), stretch, '6'),
        Pivot((22, 12), stretch, '7'),
        Pivot((22, 8), stretch, '8'),
        Pivot((18, 8), stretch, '9'),
        Pivot((8, 12), stretch, '10'),
        Pivot((12, 12), stretch, '11'),
        Pivot((12, 8), stretch, '12'),
        Pivot((8, 8), stretch, '13'),
    ]
    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '6', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '10', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[EdgeSeq(edges[6:10]), EdgeSeq(edges[10:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_exterior_offset_in_out_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
      7                   6
      o───────────────────o
      │                   │
      │                   │
      │      8┌───────┐9  │
      │       │   h   │   │
      │       │       │   │5                 4
      │       └───────┘   o──────────────────o
      │      11      10                      │
      │                                      │
      o───────────o──────────────o───────────o
      0           1              2           3
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 8), stretch, '4'),
        Pivot((15, 8), stretch, '5'),
        Pivot((15, 20), stretch, '6'),
        Pivot((0, 20), stretch, '7'),
        Pivot((8, 12), stretch, '8'),
        Pivot((12, 12), stretch, '9'),
        Pivot((12, 8), stretch, '10'),
        Pivot((8, 8), stretch, '11'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '0', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '8', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:8]),
                interiors=[EdgeSeq(edges[8:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_exterior_offset_connected_in_in_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
      5                                      4
      o──────────────────────────────────────o
      │                                      │
      │     6┌───────────────────────┐7      │
      │      │                       │       │
      │      │                       │       │
      │      │           h           │       │
      │      │                       │       │
      │      │                       │       │
      │     9└───────────────────────┘8      │
      │                                      │
      o───────────o──────────────o───────────o
      0           1              2           3
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 20), stretch, '4'),
        Pivot((0, 20), stretch, '5'),
        Pivot((8, 18), stretch, '6'),
        Pivot((22, 18), stretch, '7'),
        Pivot((22, 2), stretch, '8'),
        Pivot((8, 2), stretch, '9'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '6', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[EdgeSeq(edges[6:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_exterior_offset_interrupted_hit_hit_no_reverse_closure() -> Stretch:
    """
    Returns
    -------
      5                                      4
      o──────────────────────────────────────o
      │                                      │
      │               6      7               │
      │                ┌────┐                │
      │                │ h  │                │
      │                │    │                │
      │                └────┘                │
      │               9      8               │
      │                                      │
      o───────────o──────────────o───────────o
      0           1              2           3
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((20, 0), stretch, '2'),
        Pivot((30, 0), stretch, '3'),
        Pivot((30, 20), stretch, '4'),
        Pivot((0, 20), stretch, '5'),
        Pivot((13, 18), stretch, '6'),
        Pivot((17, 18), stretch, '7'),
        Pivot((17, 2), stretch, '8'),
        Pivot((13, 2), stretch, '9'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '6', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[EdgeSeq(edges[6:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_interior_offset_hit_hit() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │   4                              5   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   9         8          7         6   │
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((25, 25), stretch, '5'),
        Pivot((25, 20), stretch, '6'),
        Pivot((20, 20), stretch, '7'),
        Pivot((10, 20), stretch, '8'),
        Pivot((5, 20), stretch, '9'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '4', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_interior_offset_interrupted_hit_hit(stretch_interior_offset_hit_hit) -> Stretch:
    """

    Parameters
    ----------
    stretch_interior_offset_hit_hit

    Returns
    -------
      3                                      2
      o──────────────────────────────────────o
      │   4                              5   │
      │   ┌──────────────────────────────┐   │
      │   │              h               │   │
      │   │                              │   │
      │   └─────────o──────────o─────────┘   │
      │   9         8          7         6   │
      │               10┌──┐11               │
      │                 │h │                 │
      │                 │  │                 │
      │               13└──┘12               │
      │                                      │
      o──────────────────────────────────────o
      0                                      1
    """
    stretch = stretch_interior_offset_hit_hit

    new_pivots = [
        Pivot((13, 12), stretch, '10'),
        Pivot((17, 12), stretch, '11'),
        Pivot((17, 8), stretch, '12'),
        Pivot((13, 8), stretch, '13'),
    ]

    stretch._pivot_map.update(OrderedDict([(p.id, p) for p in new_pivots]))

    closure = stretch.closure('0')
    new_edges = [
        Edge('10', '11', stretch, closure=closure),
        Edge('11', '12', stretch, closure=closure),
        Edge('12', '13', stretch, closure=closure),
        Edge('13', '10', stretch, closure=closure),
    ]

    stretch._edge_map.update(OrderedDict([(e.id, e) for e in new_edges]))

    stretch._closure_map['0'].interiors.append(EdgeSeq(new_edges))
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_interior_offset_hit_in() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │   4                              5   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   9         8          7         6   │
     │                    10┌──┐11          │
     │                      │h │            │
     │                      │  │            │
     │                    13└──┘12          │
     │                                      │
     │                                      │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((25, 25), stretch, '5'),
        Pivot((25, 20), stretch, '6'),
        Pivot((20, 20), stretch, '7'),
        Pivot((10, 20), stretch, '8'),
        Pivot((5, 20), stretch, '9'),
        Pivot((18, 18), stretch, '10'),
        Pivot((22, 18), stretch, '11'),
        Pivot((22, 12), stretch, '12'),
        Pivot((18, 12), stretch, '13'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '4', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '10', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:10]), EdgeSeq(edges[10:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_interior_offset_hit_out() -> Stretch:
    """
    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │   6                              7   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   11       10          9         8   │
     │                   o──────────────────o
     │                   │2                 3
     │                   │
     │                   │
     │                   │
     o───────────────────o
     0                   1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((15, 0), stretch, '1'),
        Pivot((15, 15), stretch, '2'),
        Pivot((30, 15), stretch, '3'),
        Pivot((30, 30), stretch, '4'),
        Pivot((0, 30), stretch, '5'),
        Pivot((5, 25), stretch, '6'),
        Pivot((25, 25), stretch, '7'),
        Pivot((25, 20), stretch, '8'),
        Pivot((20, 20), stretch, '9'),
        Pivot((10, 20), stretch, '10'),
        Pivot((5, 20), stretch, '11'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '6', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[EdgeSeq(edges[6:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_interior_offset_in_in() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │   4                              5   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   9         8          7         6   │
     │         10    11    14    15         │
     │          ┌─────┐    ┌─────┐          │
     │          │  h  │    │  h  │          │
     │          └─────┘    └─────┘          │
     │         13    12    17    16         │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((25, 25), stretch, '5'),
        Pivot((25, 20), stretch, '6'),
        Pivot((20, 20), stretch, '7'),
        Pivot((10, 20), stretch, '8'),
        Pivot((5, 20), stretch, '9'),
        Pivot((8, 12), stretch, '10'),
        Pivot((12, 12), stretch, '11'),
        Pivot((12, 8), stretch, '12'),
        Pivot((8, 8), stretch, '13'),
        Pivot((18, 12), stretch, '14'),
        Pivot((22, 12), stretch, '15'),
        Pivot((22, 8), stretch, '16'),
        Pivot((18, 8), stretch, '17'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '4', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '10', stretch),
        Edge('14', '15', stretch),
        Edge('15', '16', stretch),
        Edge('16', '17', stretch),
        Edge('17', '14', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:10]), EdgeSeq(edges[10:14]), EdgeSeq(edges[14:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_interior_offset_connected_in_in() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │   4                              5   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   9         8          7         6   │
     │                                      │
     │        10┌─────────────────┐11       │
     │          │       h         │         │
     │        13└─────────────────┘12       │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((25, 25), stretch, '5'),
        Pivot((25, 20), stretch, '6'),
        Pivot((20, 20), stretch, '7'),
        Pivot((10, 20), stretch, '8'),
        Pivot((5, 20), stretch, '9'),
        Pivot((8, 12), stretch, '10'),
        Pivot((22, 12), stretch, '11'),
        Pivot((22, 8), stretch, '12'),
        Pivot((8, 8), stretch, '13'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '4', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '10', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:10]), EdgeSeq(edges[10:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_interior_offset_connected_in_out() -> Stretch:
    """
    Returns
    -------
     5                                      4
     o──────────────────────────────────────o
     │   6                              7   │
     │   ┌──────────────────────────────┐   │
     │   │              h               │   │
     │   │                              │   │
     │   └─────────o──────────o─────────┘   │
     │   11        10         9         8   │
     │         12    13  o──────────────────o
     │          ┌─────┐  │2                 3
     │          │  h  │  │
     │          └─────┘  │
     │         15    14  │
     o───────────────────o
     0                   1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((15, 0), stretch, '1'),
        Pivot((15, 15), stretch, '2'),
        Pivot((30, 15), stretch, '3'),
        Pivot((30, 30), stretch, '4'),
        Pivot((0, 30), stretch, '5'),
        Pivot((5, 25), stretch, '6'),
        Pivot((25, 25), stretch, '7'),
        Pivot((25, 20), stretch, '8'),
        Pivot((20, 20), stretch, '9'),
        Pivot((10, 20), stretch, '10'),
        Pivot((5, 20), stretch, '11'),
        Pivot((8, 12), stretch, '12'),
        Pivot((12, 12), stretch, '13'),
        Pivot((12, 8), stretch, '14'),
        Pivot((8, 8), stretch, '15'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '6', stretch),
        Edge('12', '13', stretch),
        Edge('13', '14', stretch),
        Edge('14', '15', stretch),
        Edge('15', '12', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[EdgeSeq(edges[6:12]), EdgeSeq(edges[12:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_interior_offset_into_hole_in_hit() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │                                      │
     │     4┌────────────┐5                 │
     │      │            │                  │
     │      │            │                  │
     │      │           6└───────────┐7     │
     │      │                        │      │
     │      │           h            │      │
     │      │                        │      │
     │      └─────o────────────o─────┘8     │
     │     11     10           9            │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((15, 25), stretch, '5'),
        Pivot((15, 20), stretch, '6'),
        Pivot((25, 20), stretch, '7'),
        Pivot((25, 10), stretch, '8'),
        Pivot((20, 10), stretch, '9'),
        Pivot((10, 10), stretch, '10'),
        Pivot((5, 10), stretch, '11'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '4', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_interior_offset_into_hole_hit_hit_interrupted() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │                                      │
     │     4┌────────┐      ┌────────┐9     │
     │      │       5│      │8       │      │
     │      │        │      │        │      │
     │      │        └──────┘        │      │
     │      │       6        7       │      │
     │      │                        │      │
     │      │           h            │      │
     │      └─────o────────────o─────┘10    │
     │     13     12           11           │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((12, 25), stretch, '5'),
        Pivot((12, 20), stretch, '6'),
        Pivot((18, 20), stretch, '7'),
        Pivot((18, 25), stretch, '8'),
        Pivot((25, 25), stretch, '9'),
        Pivot((25, 10), stretch, '10'),
        Pivot((20, 10), stretch, '11'),
        Pivot((10, 10), stretch, '12'),
        Pivot((5, 10), stretch, '13'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '13', stretch),
        Edge('13', '4', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_0_for_strict_attach_offset_handler() -> Stretch:
    """
    Returns
    -------
                  5           4
                  ┌───────────┐
                  │           │
                  │           │
     7            │           │            2
     ┌────────────┘           └────────────┐
     │            6           3            │
     │                                     │
     │                                     │
     │                                     │
     └─────────────────────────────────────┘
     0                                     1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 10), stretch, '2'),
        Pivot((20, 10), stretch, '3'),
        Pivot((20, 20), stretch, '4'),
        Pivot((10, 20), stretch, '5'),
        Pivot((10, 10), stretch, '6'),
        Pivot((0, 10), stretch, '7'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:]),
                interiors=[],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_1_for_strict_attach_offset_handler() -> Stretch:
    """
    Returns
    -------
                  5           4
                  o───────────o
                  \          /
                   \        /
     7              \      /               2
     ┌───────────────o    o────────────────┐
     │               6    3                │
     │                                     │
     │                                     │
     │                                     │
     └─────────────────────────────────────┘
     0                                     1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 10), stretch, '2'),
        Pivot((17, 10), stretch, '3'),
        Pivot((20, 20), stretch, '4'),
        Pivot((10, 20), stretch, '5'),
        Pivot((13, 10), stretch, '6'),
        Pivot((0, 10), stretch, '7'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:]),
                interiors=[],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_2_for_strict_attach_offset_handler() -> Stretch:
    """
    Returns
    -------
     3                                      2
     o──────────────────────────────────────o
     │                 5 8                  │
     │     4┌──────────o o───────────┐9     │
     │      │         /   \          │      │
     │      │        /     \         │      │
     │      │       o───────o        │      │
     │      │       6       7        │      │
     │      │                        │      │
     │      │           h            │      │
     │    11└────────────────────────┘10    │
     │                                      │
     │                                      │
     o──────────────────────────────────────o
     0                                      1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((30, 0), stretch, '1'),
        Pivot((30, 30), stretch, '2'),
        Pivot((0, 30), stretch, '3'),
        Pivot((5, 25), stretch, '4'),
        Pivot((13, 25), stretch, '5'),
        Pivot((10, 20), stretch, '6'),
        Pivot((20, 20), stretch, '7'),
        Pivot((17, 25), stretch, '8'),
        Pivot((25, 25), stretch, '9'),
        Pivot((25, 10), stretch, '10'),
        Pivot((5, 10), stretch, '11'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '4', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[EdgeSeq(edges[4:])],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def stretch_offset_union_2_reverse_closure() -> Stretch:
    """
    Returns
    -------
     7┌────┐6   9┌────┐8
      │    │     │    │
      │    │     │    │
     5├────┴─────┴────┤2
      │    4     3    │
      │               │
      │               │
     0└───────────────┘1
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((12, 0), stretch, '1'),
        Pivot((12, 7), stretch, '2'),
        Pivot((8, 7), stretch, '3'),
        Pivot((4, 7), stretch, '4'),
        Pivot((0, 7), stretch, '5'),
        Pivot((4, 12), stretch, '6'),
        Pivot((0, 12), stretch, '7'),
        Pivot((12, 12), stretch, '8'),
        Pivot((8, 12), stretch, '9'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '0', stretch),
        Edge('5', '4', stretch),
        Edge('4', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '5', stretch),
        Edge('3', '2', stretch),
        Edge('2', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '3', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:6]),
                interiors=[],
                stretch=stretch,
                id_='0'),
        Closure(exterior=EdgeSeq(edges[6:10]),
                interiors=[],
                stretch=stretch,
                id_='1'),
        Closure(exterior=EdgeSeq(edges[10:]),
                interiors=[],
                stretch=stretch,
                id_='2'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()

    return stretch
