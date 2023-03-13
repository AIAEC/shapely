import io
import os
from typing import List

from shapely import wkt
from shapely.extension.model.stretch.stretch_v3 import Stretch
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

    def test_split_by_lines_cutting_across_0_closure(self, box_stretches):
        lines: List[LineString] = [LineString([(-100, 50), (75, 50)])]
        box_stretches.split(lines)
        assert len(box_stretches.closures) == 2
        closures = sorted(box_stretches.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 100))
        assert closures[1].shape.equals(box(100, 0, 200, 100))

    def test_split_by_lines_cutting_across_2_closure(self, box_stretches):
        lines: List[LineString] = [LineString([(-1000, 50), (1000, 50)])]
        box_stretches.split(lines)
        assert len(box_stretches.closures) == 4
        closures = sorted(box_stretches.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 50))
        assert closures[1].shape.equals(box(0, 50, 100, 100))
        assert closures[2].shape.equals(box(100, 0, 200, 50))
        assert closures[3].shape.equals(box(100, 50, 200, 100))

    def test_split_by_multilines_which_generate_new_closure(self, box_stretches):
        lines: MultiLineString = unary_union([LineString([(-100, 50), (75, 50)]),
                                              LineString([(50, -100), (50, 75)]),
                                              LineString([(25, -100), (25, 25)])])
        box_stretches.split(lines)
        assert len(box_stretches.closures) == 3
        closures = sorted(box_stretches.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 50, 50))
        assert closures[1].shape.equals(box(0, 0, 100, 100).difference(box(0, 0, 50, 50)))
        assert closures[2].shape.equals(box(100, 0, 200, 100))

    def test_split_by_multilines_which_cut_across_1_closure_and_gen_2_closures(self, box_stretches):
        lines: MultiLineString = unary_union([LineString([(-100, 50), (175, 50)]),
                                              LineString([(150, -100), (150, 75)]),
                                              LineString([(25, -100), (25, 25)])])
        box_stretches.split(lines)
        assert len(box_stretches.closures) == 4
        closures = sorted(box_stretches.closures, key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 100, 50))
        assert closures[1].shape.equals(box(0, 50, 100, 100))
        assert closures[2].shape.equals(box(100, 0, 150, 50))
        assert closures[3].shape.equals(box(100, 0, 200, 100).difference(box(100, 0, 150, 50)))

    def test_split_closures_without_removing_origin_cracks(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7

        stretch.split(LineString([(-1, 8), (5, 8)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8

        assert stretch.edge('(4,5)') in stretch.edges
        assert stretch.edge('(5,4)') in stretch.edges

        assert stretch.closures[0].shape.equals(loads('POLYGON ((0 0, 5 0, 5 5, 5 0, 10 0, 10 10, 0 10, 0 8, 0 0))'))

    def test_split_closures_without_removing_origin_cracks(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7

        stretch.split([LineString([(-1, 8), (5, 8)]), LineString([(5, 7), (5, 11)])])

        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 9
        assert len(stretch.edges) == 13

        assert stretch.edge('(4,5)') in stretch.edges
        assert stretch.edge('(5,4)') in stretch.edges

        closures = stretch.closures
        closures.sort(key=lambda c: c.shape.centroid.x)
        assert closures[0].shape.equals(loads('POLYGON ((0 10, 0 8, 5 8, 5 10, 0 10))'))
        assert closures[1].shape.equals(loads('POLYGON ((0 0, 5 0, 5 5, 5 0, 10 0, 10 10, 5 10, 5 8, 0 8, 0 0))'))

    def test_split_by_interior_available(self):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../data/stretch_for_split_by_interior_available.json'), 'rb') as fp:
            json_str = io.BufferedReader.read(fp).decode(encoding='utf-8')
            stretch = Stretch.loads(json_str)

        assert len(stretch.closures) == 1

        lines = wkt.loads('MULTILINESTRING ((-0.6056013352934357 13.666627785848709, -0.6056013352934357 -2.0475705548841665, -6.11130455784275 -2.0475705548841665), (-34.09569795693843 65.56023126700507, -6.682077083355665 65.56023126700507), (-6.682077083355665 65.56023126700507, -6.682077083355665 63.96885897313261), (30.69480698544408 -33.28352178738959, -5.936040470100707 -33.28352178738959), (-5.936040470100707 -33.28352178738959, -6.11130455784275 -33.28352178738959, -6.11130455784275 -2.0475705548841665), (-5.936040470100707 -65.6454290844602, -5.936040470100707 -33.28352178738959), (-0.6056013352934357 13.666627785848709, -6.682077083355665 13.666627785848709, -6.682077083355665 63.96885897313261), (-5.936040470100707 -65.6454290844602, -64.93766677696746 -65.6454290844602), (30.69480698544408 -33.28352178738959, 100.22993984428231 -33.28352178738959), (-0.6056013352934357 13.666627785848709, 73.26061136398828 13.666627785848709), (-6.682077083355665 65.56023126700507, 30.724034221469555 65.56023126700507), (-34.09569795693843 65.56023126700507, -34.09569795693843 63.96885897313261, -62.83766677696752 63.96885897313261), (-6.11130455784275 -2.0475705548841665, -64.93766677696749 -2.0475705548841665))')
        stretch.split(lines)

        assert len(stretch.closures) == 6
