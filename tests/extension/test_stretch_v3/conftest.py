from collections import OrderedDict

import pytest

from shapely.extension.model.stretch.stretch_v3 import Stretch, Pivot, Edge, EdgeSeq, Closure
from shapely.wkt import loads


@pytest.fixture
def stretch_dangling_pivots_in_a_row() -> Stretch:
    """
    Returns
    -------
    0    1    2
    o    o    o
      o    o
      3    4
    """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((2, 0), stretch, '1'),
        Pivot((4, 0), stretch, '2'),
        Pivot((1, -1), stretch, '3'),
        Pivot((3, -1), stretch, '4'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])
    stretch.shrink_id_gen()

    return stretch


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
def stretch_2_groups_dangling_edges() -> Stretch:
    """
    Returns
    -------
     3         2         5
     o◄────────o◄────────o
     │         ▲         ▲
     │         │         │
     │         │         │
     ▼         ▼         │
     o────────►o────────►o
     0         1         4
    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((10, 10), stretch, '2'),
        Pivot((0, 10), stretch, '3'),
        Pivot((20, 0), stretch, '4'),
        Pivot((20, 10), stretch, '5'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('2', '1', stretch),
        Edge('4', '5', stretch),
        Edge('1', '4', stretch),
        Edge('5', '2', stretch),
    ]

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
def stretch_back_and_forth_edge_seq_straight() -> Stretch:
    """
    Returns
    -------
     o┌───────►o───────►o───────►o
     0◄───────┘1◄──────┘2◄───────┘3
    """
    stretch = Stretch()

    pivots = [
        Pivot((-16.741118015258667, -23.73459795490389), stretch, '0'),
        Pivot((-15.106879141804978, -14.682014325325804), stretch, '1'),
        Pivot((-13.249485717477986, -4.39330465143675), stretch, '2'),
        Pivot((-7.799375724810199, 25.796637162123016), stretch, '3')
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '2', stretch),
        Edge('2', '1', stretch),
        Edge('1', '0', stretch),
    ]

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
def stretch_box_duplicate_pivots() -> Stretch:
    """
    Returns
    -------
     3             2
      ┌───────────┐
      │           │
      │           │
      └──o────────┘
     0   4         1
     """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((1, 0), stretch, '1'),
        Pivot((1, 1), stretch, '2'),
        Pivot((0, 1), stretch, '3'),
        Pivot((0.3, 0), stretch, '4'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '4', stretch),
        Edge('4', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(EdgeSeq(edges), stretch, '0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

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
def stretch_3_boxes() -> Stretch:
    """
      3        2        5        7
      ┌────────┬────────┬────────┐
      │        │        │        │
      │        │        │        │
      └────────┴────────┴────────┘
      0        1        4        6
    Returns
    -------

    """
    stretch = Stretch()

    pivots = [Pivot((0, 0), stretch, '0'),
              Pivot((1, 0), stretch, '1'),
              Pivot((1, 1), stretch, '2'),
              Pivot((0, 1), stretch, '3'),
              Pivot((2, 0), stretch, '4'),
              Pivot((2, 1), stretch, '5'),
              Pivot((3, 0), stretch, '6'),
              Pivot((3, 1), stretch, '7')]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),
        Edge('1', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '2', stretch),
        Edge('2', '1', stretch),
        Edge('4', '6', stretch),
        Edge('6', '7', stretch),
        Edge('7', '5', stretch),
        Edge('5', '4', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]), stretch=stretch, id_='0'),
        Closure(exterior=EdgeSeq(edges[4:8]), stretch=stretch, id_='1'),
        Closure(exterior=EdgeSeq(edges[8:]), stretch=stretch, id_='2'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

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


@pytest.fixture
def stretch_of_three_closures() -> Stretch:
    """
       6┌─────────────────────┐7
        │                     │
        │                     │
        │                     │
        │                     │
        │                     │
        │              4      │
       3├──────────────┬──────┤5
        │              │      │
        │              │      │
        └──────────────┴──────┘
        0              1      2
    """

    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((75, 0), stretch, '1'),
        Pivot((100, 0), stretch, '2'),
        Pivot((0, 10), stretch, '3'),
        Pivot((75, 10), stretch, '4'),
        Pivot((100, 10), stretch, '5'),
        Pivot((0, 200), stretch, '6'),
        Pivot((100, 200), stretch, '7'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '4', stretch),
        Edge('4', '3', stretch),
        Edge('3', '0', stretch),
        Edge('1', '2', stretch),
        Edge('2', '5', stretch),
        Edge('5', '4', stretch),
        Edge('4', '1', stretch),
        Edge('5', '7', stretch),
        Edge('7', '6', stretch),
        Edge('6', '3', stretch),
        Edge('3', '4', stretch),
        Edge('4', '5', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges[:4]),
                interiors=[],
                stretch=stretch,
                id_='0'),
        Closure(exterior=EdgeSeq(edges[4:8]),
                interiors=[],
                stretch=stretch,
                id_='1'),
        Closure(exterior=EdgeSeq(edges[8:]),
                interiors=[],
                stretch=stretch,
                id_='2'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_for_offset_attaching_to_edge() -> Stretch:
    """
    Returns
    -------
     12┌──────┐11
       │      │
       │  9┌──┘10
       │   │
       │  8└──┐7
       │      │
       │  5┌──┘6
       │   │
       │  4└──┐3
       │      │
       └───x──┘
      0    1   2
      """
    stretch = Stretch()

    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((5, 0), stretch, '1'),
        Pivot((10, 0), stretch, '2'),
        Pivot((10, 5), stretch, '3'),
        Pivot((5, 5), stretch, '4'),
        Pivot((5, 10), stretch, '5'),
        Pivot((10, 10), stretch, '6'),
        Pivot((10, 15), stretch, '7'),
        Pivot((5, 15), stretch, '8'),
        Pivot((5, 20), stretch, '9'),
        Pivot((10, 20), stretch, '10'),
        Pivot((10, 25), stretch, '11'),
        Pivot((0, 25), stretch, '12'),
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
        Edge('7', '8', stretch),
        Edge('8', '9', stretch),
        Edge('9', '10', stretch),
        Edge('10', '11', stretch),
        Edge('11', '12', stretch),
        Edge('12', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges),
                interiors=[],
                stretch=stretch,
                id_='0'),
    ]

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])

    stretch.shrink_id_gen()
    return stretch


@pytest.fixture
def box_stretches() -> Stretch:
    """"
      ┌─────┐──────┐
      │     │      │
      │     │      │
      └─────┘──────┘

    Returns
    -------

    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((100, 0), stretch, '1'),
        Pivot((100, 100), stretch, '2'),
        Pivot((0, 100), stretch, '3'),
        Pivot((200, 0), stretch, '4'),
        Pivot((200, 100), stretch, '5'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges1 = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '0', stretch),

    ]

    edges2 = [
        Edge('1', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '2', stretch),
        Edge('2', '1', stretch), ]

    edges = edges1 + edges2

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])

    closures = [
        Closure(exterior=EdgeSeq(edges1), stretch=stretch, id_='0'),
        Closure(exterior=EdgeSeq(edges2), stretch=stretch, id_='1'),
    ]

    assert len(closures) == 2

    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch


@pytest.fixture
def stretch_002() -> Stretch:
    return Stretch.loads(
        '{"pivot": {"0": [-107.35919009521606, 4.3175316568887485], "1": [-108.75519247616947, 27.102819230527743], "2": [-113.34658312236718, 26.82151524191516], "10": [116.51622322275124, 8.18781476413892], "11": [115.79331859138435, 16.20528998355484], "12": [87.41960546281186, 13.646942365757337], "13": [89.25868902944137, -6.749581037828033], "14": [94.53727500913122, -6.2736293018064515], "15": [95.73752621107327, -19.58197122503787], "16": [96.02617266215385, -23.39413989135904], "17": [-110.85922990809489, -41.999835168942816], "18": [-112.4480894068256, -24.37601587373924], "19": [-108.48314483113373, -8.386709249104658], "20": [-17.542348061960894, 31.59045897081526], "21": [144.0640604486713, 31.58116830738623], "22": [144.06432490013762, 36.181168299785305], "23": [-51.655086762783576, 36.19242010097964], "24": [-51.6555495528497, 28.14242011428238], "25": [-17.542546400560653, 28.140458976517085], "26": [-97.42506135593212, 28.97929035766782], "27": [-97.42502917683319, 30.779563813321545], "28": [-100.67511129772899, 30.779286107349606], "29": [-100.67502410768111, 31.229171221275124], "30": [-102.12503258328277, 31.2292903787241], "31": [-102.12511984054498, 27.82929038081801], "32": [-113.40832719704719, 27.82929038347072], "33": [146.82488047567938, 10.920628785888823], "34": [146.82487281109692, 36.181009597406046], "35": [-51.65537209037815, 31.22929037836201], "36": [-56.73512112358688, 31.22929037834774], "37": [-56.73512112360197, 30.77928902193878], "38": [-59.58502599795051, 30.779211709870026], "39": [-59.58891397548879, 27.829289879367195], "40": [-65.80511967539181, 27.829289879367195], "41": [-65.80508645134128, 28.976563020899164], "42": [-85.05512112368118, 28.979204220099575], "43": [-85.05512112368118, 28.37919456192583], "44": [-91.5052005181231, 28.378833679165098], "45": [-91.5050496091755, 28.979290356267143], "59": [103.68632421774541, 15.113649278155023], "60": [102.2051447298799, 31.5835747533993], "69": [-108.70346897456655, -9.275203455998485], "73": [-19.580073905923882, -1.2601250088555278], "75": [-22.224162408187617, 28.140728120043207], "77": [-35.71495719303, -2.711173357967965], "78": [-38.489626012353284, 28.14166321258847], "79": [59.72122749481073, -26.659129776876036], "81": [56.81913079705263, 5.61063679865935], "82": [54.48307611130879, 31.58631826884376], "83": [-75.84020971921065, -6.319732552341786], "84": [-72.9381130219703, -38.589499124913324], "85": [57.06756933154884, 2.848132874253957], "87": [88.14143345823597, 5.64144339378107], "88": [98.4796769562001, -19.374343454736174], "89": [96.23140566400028, 5.560313620101062], "90": [94.45002658598372, 5.39969358070098], "91": [95.49487474183293, -6.188289921728826], "92": [-111.97163789125746, 4.379918504210944], "93": [-113.03380188344988, -7.625891696385357], "94": [-117.09891779592085, -24.01915609964698], "95": [-114.71793106163467, -50.42934528717445], "96": [99.37323557552628, -31.175618545495958], "97": [105.74121118855447, 15.298930462989397], "98": [106.26445142249725, 9.495861250682736], "99": [100.96435844841034, 9.017972432503845], "100": [101.16402284579465, 6.803566425298105], "101": [87.54543191567852, 12.251452657049589], "102": [94.03718084554615, 12.23667842798737], "103": [94.90677708071307, 14.322031578998507]}, "pivot_cargo": {"0": {}, "1": {}, "2": {}, "10": {}, "11": {}, "12": {}, "13": {}, "14": {}, "15": {}, "16": {}, "17": {}, "18": {}, "19": {}, "20": {}, "21": {}, "22": {}, "23": {}, "24": {}, "25": {}, "26": {}, "27": {}, "28": {}, "29": {}, "30": {}, "31": {}, "32": {}, "33": {}, "34": {}, "35": {}, "36": {}, "37": {}, "38": {}, "39": {}, "40": {}, "41": {}, "42": {}, "43": {}, "44": {}, "45": {}, "59": {}, "60": {}, "69": {}, "73": {}, "75": {}, "77": {}, "78": {}, "79": {}, "81": {}, "82": {}, "83": {}, "84": {}, "85": {}, "87": {}, "88": {}, "89": {}, "90": {}, "91": {}, "92": {}, "93": {}, "94": {}, "95": {}, "96": {}, "97": {}, "98": {}, "99": {}, "100": {}, "101": {}, "102": {}, "103": {}}, "edge_cargo": {"(21,22)": {"width": 0, "is_fixed": true, "is_starting": false}, "(22,23)": {"width": 0, "is_fixed": true, "is_starting": false}, "(25,20)": {"width": 4.2064166252698225, "is_fixed": true, "is_starting": false}, "(23,35)": {"width": 0, "is_fixed": true, "is_starting": false}, "(35,24)": {"width": 0, "is_fixed": true, "is_starting": false}, "(26,27)": {"width": 0, "is_fixed": false, "is_starting": false}, "(27,28)": {"width": 0, "is_fixed": false, "is_starting": false}, "(28,29)": {"width": 0, "is_fixed": false, "is_starting": false}, "(29,30)": {"width": 0, "is_fixed": false, "is_starting": false}, "(30,31)": {"width": 0, "is_fixed": false, "is_starting": false}, "(31,32)": {"width": 0, "is_fixed": false, "is_starting": false}, "(32,2)": {"width": 0, "is_fixed": false, "is_starting": false}, "(2,1)": {"width": 0, "is_fixed": true, "is_starting": false}, "(1,0)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(18,17)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(16,15)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(15,14)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(14,13)": {"width": 4.973479230783974, "is_fixed": true, "is_starting": false}, "(11,10)": {"width": 0, "is_fixed": true, "is_starting": false}, "(10,33)": {"width": 0, "is_fixed": false, "is_starting": false}, "(33,34)": {"width": 0, "is_fixed": false, "is_starting": false}, "(34,22)": {"width": 0, "is_fixed": false, "is_starting": false}, "(22,21)": {"width": 0, "is_fixed": true, "is_starting": false}, "(20,25)": {"width": 1.2935833747301775, "is_fixed": true, "is_starting": false}, "(24,35)": {"width": 0, "is_fixed": true, "is_starting": false}, "(36,37)": {"width": 0, "is_fixed": false, "is_starting": false}, "(37,38)": {"width": 0, "is_fixed": false, "is_starting": false}, "(39,40)": {"width": 0, "is_fixed": false, "is_starting": false}, "(40,41)": {"width": 0, "is_fixed": false, "is_starting": false}, "(41,42)": {"width": 0, "is_fixed": false, "is_starting": false}, "(42,43)": {"width": 0, "is_fixed": false, "is_starting": false}, "(43,44)": {"width": 0, "is_fixed": false, "is_starting": false}, "(44,45)": {"width": 0, "is_fixed": false, "is_starting": false}, "(45,26)": {"width": 0, "is_fixed": false, "is_starting": false}, "(60,21)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(21,60)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(59,60)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(60,59)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(35,36)": {"width": 0, "is_fixed": false, "is_starting": false}, "(38,39)": {"width": 0, "is_fixed": false, "is_starting": false}, "(19,69)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(69,18)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(75,25)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(25,75)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(73,77)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(77,73)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(24,78)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(78,75)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(75,78)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(78,24)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(0,19)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(75,73)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(73,75)": {"width": 2.75, "is_fixed": false, "is_starting": true}, "(78,77)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(77,78)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(81,73)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(73,81)": {"width": 2.75, "is_fixed": false, "is_starting": true}, "(20,82)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(82,20)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(81,82)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(82,81)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(77,83)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(83,77)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(84,79)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(83,84)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(84,83)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(85,81)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(81,85)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(13,87)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(79,16)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(17,84)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(82,60)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(60,82)": {"width": 3.6, "is_fixed": true, "is_starting": false}, "(69,83)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(83,69)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(79,85)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(85,79)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(85,87)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(87,85)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(88,89)": {"width": 0, "is_fixed": true, "is_starting": false}, "(89,90)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(90,91)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(91,14)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(14,15)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(15,16)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(16,79)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(79,84)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(84,17)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(17,18)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(18,69)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(69,19)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(19,0)": {"width": 1.9, "is_fixed": true, "is_starting": false}, "(0,1)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(1,2)": {"width": 0, "is_fixed": true, "is_starting": false}, "(2,92)": {"width": 0, "is_fixed": true, "is_starting": false}, "(92,93)": {"width": 0, "is_fixed": true, "is_starting": false}, "(93,94)": {"width": 0, "is_fixed": true, "is_starting": false}, "(94,95)": {"width": 0, "is_fixed": true, "is_starting": false}, "(95,96)": {"width": 0, "is_fixed": true, "is_starting": false}, "(96,88)": {"width": 0, "is_fixed": true, "is_starting": false}, "(59,97)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(97,11)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(11,97)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(97,98)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(98,99)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(99,100)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(100,10)": {"width": 0, "is_fixed": true, "is_starting": false}, "(10,11)": {"width": 0, "is_fixed": true, "is_starting": false}, "(87,101)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(101,12)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(12,103)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(103,59)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(12,101)": {"width": 2.75, "is_fixed": true, "is_starting": false}, "(101,102)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(102,103)": {"width": 2.75, "is_fixed": false, "is_starting": false}, "(103,12)": {"width": 2.75, "is_fixed": true, "is_starting": false}}, "closure": {"1": {"exterior": ["20", "82", "60", "21", "22", "23", "35", "24", "78", "75", "25", "20"], "interiors": []}, "27": {"exterior": ["10", "33", "34", "22", "21", "60", "59", "97", "11", "10"], "interiors": []}, "87": {"exterior": ["73", "75", "78", "77", "73"], "interiors": []}, "88": {"exterior": ["0", "19", "69", "83", "77", "78", "24", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "26", "27", "28", "29", "30", "31", "32", "2", "1", "0"], "interiors": []}, "96": {"exterior": ["20", "25", "75", "73", "81", "82", "20"], "interiors": []}, "99": {"exterior": ["73", "77", "83", "84", "79", "85", "81", "73"], "interiors": []}, "100": {"exterior": ["17", "84", "83", "69", "18", "17"], "interiors": []}, "105": {"exterior": ["12", "103", "59", "60", "82", "81", "85", "87", "101", "12"], "interiors": []}, "106": {"exterior": ["13", "87", "85", "79", "16", "15", "14", "13"], "interiors": []}, "107": {"exterior": ["0", "1", "2", "92", "93", "94", "95", "96", "88", "89", "90", "91", "14", "15", "16", "79", "84", "17", "18", "69", "19", "0"], "interiors": []}, "108": {"exterior": ["10", "11", "97", "98", "99", "100", "10"], "interiors": []}, "109": {"exterior": ["101", "102", "103", "12", "101"], "interiors": []}}, "closure_cargo": {"1": {"angle": 0, "region_type": "surrounding", "clamp": false, "seene8338653-5cf2-40": true}, "27": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": true}, "87": {"angle": -84.86107905049698, "region_type": "core", "clamp": true, "seene8338653-5cf2-40": false}, "88": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": false}, "96": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": false}, "99": {"angle": 5.13892094950298, "region_type": "core", "clamp": false, "seene8338653-5cf2-40": false}, "100": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": false}, "105": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": false}, "106": {"angle": 5.13892094950298, "region_type": "building", "clamp": false, "seene8338653-5cf2-40": false}, "107": {"angle": 0, "region_type": "surrounding", "clamp": false, "seene8338653-5cf2-40": true}, "108": {"angle": 0, "region_type": "surrounding", "clamp": false, "seene8338653-5cf2-40": true}, "109": {"angle": 0, "region_type": "surrounding", "clamp": false, "seene8338653-5cf2-40": true}}}')


@pytest.fixture
def stretch_with_inner_continue_edges() -> Stretch:
    """
    Returns
    -------
        6                   5
        o◄──────────────────o
        │                   ▲
        │         o 3       │
        │         ▲         │
        │         │         │
        │         ▼         │
        │         o 2       │
        │         ▲         │
        │         │         │
        │         │         │
        ▼         ▼         │
        o────────►o────────►o
        0         1         4

    """
    stretch = Stretch()
    pivots = [
        Pivot((0, 0), stretch, '0'),
        Pivot((10, 0), stretch, '1'),
        Pivot((10, 10), stretch, '2'),
        Pivot((10, 15), stretch, '3'),
        Pivot((20, 0), stretch, '4'),
        Pivot((20, 20), stretch, '5'),
        Pivot((0, 20), stretch, '6'),
    ]

    stretch._pivot_map = OrderedDict([(p.id, p) for p in pivots])

    edges = [
        Edge('0', '1', stretch),
        Edge('1', '2', stretch),
        Edge('2', '3', stretch),
        Edge('3', '2', stretch),
        Edge('2', '1', stretch),
        Edge('1', '4', stretch),
        Edge('4', '5', stretch),
        Edge('5', '6', stretch),
        Edge('6', '0', stretch),
    ]

    stretch._edge_map = OrderedDict([(e.id, e) for e in edges])
    closures = [Closure(EdgeSeq(edges), stretch, '0')]
    stretch._closure_map = OrderedDict([(c.id, c) for c in closures])
    stretch.shrink_id_gen()

    return stretch
