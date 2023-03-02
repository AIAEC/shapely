from typing import List

from shapely.geometry import Polygon
from shapely.geometry import box, LineString, MultiLineString
from shapely.ops import unary_union
from shapely.wkt import loads


class TestSplit:
    def test_split_across_stretch_box(self, stretch_box):
        stretch = stretch_box

        assert len(stretch.closures) == 1
        closure = stretch.closures[0]

        new_closures = closure.split(LineString([(0.5, -1), (0.5, 2)]))
        assert len(new_closures) == 2
        assert len(stretch.closures) == 2

        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        new_closures.sort(key=lambda c: c.shape.centroid.x)
        assert new_closures[0].shape.equals(Polygon([(0, 0), (0.5, 0), (0.5, 1), (0, 1)]))
        assert new_closures[1].shape.equals(Polygon([(0.5, 0), (1, 0), (1, 1), (0.5, 1)]))

    def test_split_with_line_not_go_across_stretch_box(self, stretch_box):
        stretch = stretch_box

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        closure = stretch.closures[0]

        new_closures = closure.split(LineString([(0.5, -1), (0.5, 0.5)]))
        assert len(new_closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5

        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        assert new_closures[0].shape.equals(Polygon([(0, 0), (0.5, 0), (1, 0), (1, 1), (0, 1)]))

    def test_split_with_line_go_to_the_interior_and_form_new_closure(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7

        closure = stretch.closures[0]
        new_closures = closure.split(LineString([(4, 5), (11, 5)]))
        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        assert len(new_closures) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 10

        new_closures.sort(key=lambda c: c.shape.centroid.x)
        assert len(new_closures[0].interiors) == 0
        assert new_closures[0].shape.equals(Polygon([(0, 0), (5, 0), (5, 5), (10, 5), (10, 10), (0, 10)]))

        assert len(new_closures[1].interiors) == 0
        assert new_closures[1].shape.equals(Polygon([(5, 0), (10, 0), (10, 5), (5, 5)]))

    def test_multiline_split_1(self, box_stretchs):
        lines: List[LineString] = [LineString([(-100, 50), (75, 50)])]
        box_stretchs.split(lines)
        assert len(box_stretchs.closures) == 2
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 100))
        assert closures[1].shape.equals(box(100, 0, 200, 100))

        lines: List[LineString] = [LineString([(-1000, 50), (1000, 50)])]
        box_stretchs.split(lines)
        assert len(box_stretchs.closures) == 4
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 50))
        assert closures[1].shape.equals(box(0, 50, 100, 100))
        assert closures[2].shape.equals(box(100, 0, 200, 50))
        assert closures[3].shape.equals(box(100, 50, 200, 100))

    def test_multiline_split_2(self, box_stretchs):
        lines: MultiLineString = unary_union([LineString([(-100, 50), (75, 50)]), LineString([(50, -100), (50, 75)]),
                                              LineString([(25, -100), (25, 25)])])
        box_stretchs.split(lines)
        assert len(box_stretchs.closures) == 3
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 50, 50))
        assert closures[1].shape.equals(box(0, 0, 100, 100).difference(box(0, 0, 50, 50)))
        assert closures[2].shape.equals(box(100, 0, 200, 100))

    def test_multiline_split_3(self, box_stretchs):
        lines: MultiLineString = unary_union([LineString([(-100, 50), (175, 50)]), LineString([(150, -100), (150, 75)]),
                                              LineString([(25, -100), (25, 25)])])
        box_stretchs.split(lines)
        assert len(box_stretchs.closures) == 4
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 50))
        assert closures[1].shape.equals(box(0, 50, 100, 100))
        assert closures[2].shape.equals(box(100, 0, 150, 50))
        assert closures[3].shape.equals(box(100, 0, 200, 100).difference(box(100, 0, 150, 50)))

    def test_split_closures_not_remove_original_cuts(self, box_stretchs):
        assert len(box_stretchs.closures) == 2
        box_stretchs.closures[0].cut(line=LineString([(25, -100), (25, 25)]))
        box_stretchs.closures[1].cut(line=LineString([(25, -100), (25, 25)]))
        assert len(box_stretchs.closures) == 2
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(loads('POLYGON ((0 0, 25 0, 25 25, 25 0, 100 0, 100 100, 0 100, 0 0))'))
        assert closures[1].shape.equals(box(100, 0, 200, 100))

        lines: MultiLineString = unary_union(
            [LineString([(-100, 50), (175, 50)]), LineString([(150, -100), (150, 75)])])

        closures[1].split(lines)

        box_stretchs.split(lines)
        assert len(box_stretchs.closures) == 4
        closures = sorted(box_stretchs.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 50))
        assert closures[1].shape.equals(box(0, 50, 100, 100))  # TODO expect split not to remove original cuts
        assert closures[2].shape.equals(box(100, 0, 150, 50))
        assert closures[3].shape.equals(box(100, 0, 200, 100).difference(box(100, 0, 150, 50)))
