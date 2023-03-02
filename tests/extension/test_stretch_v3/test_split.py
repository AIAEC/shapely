from typing import List

import pytest

from shapely.geometry import Polygon
from shapely.geometry import box, LineString, MultiLineString
from shapely.ops import unary_union


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

    def test_failed_split(self, stretch_2_boxes):
        lines: List[LineString] = [LineString([(-1.00, 0.50), (0.75, 0.50)])]
        stretch_2_boxes.split(lines)
        assert len(stretch_2_boxes.closures) == 2
        closures = sorted(stretch_2_boxes.closures,
                          key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 1, 1))
        assert closures[1].shape.equals(box(1, 0, 2, 1))

    def test_line_segment_split_two_regions_into_four(self, stretch_2_boxes):
        lines: List[LineString] = [LineString([(-10, 0.5), (10, 0.5)])]
        stretch_2_boxes.split(lines)
        assert len(stretch_2_boxes.closures) == 4
        closures = sorted(stretch_2_boxes.closures,
                          key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 1, 0.50))
        assert closures[1].shape.equals(box(0, 0.50, 1, 1))
        assert closures[2].shape.equals(box(1, 0, 2, 0.50))
        assert closures[3].shape.equals(box(1, 0.50, 2, 1))

    def test_multiline_split_left_region_together(self, stretch_2_boxes):
        lines: MultiLineString = unary_union(
            [LineString([(-1.00, 0.50), (0.75, 0.50)]), LineString([(0.50, -1), (.50, .75)]),
             LineString([(.25, -1.00), (.25, .25)])])
        stretch_2_boxes.split(lines)
        assert len(stretch_2_boxes.closures) == 3
        closures = sorted(stretch_2_boxes.closures,
                          key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, .50, .50))
        assert closures[1].shape.equals(box(0, 0, 1.00, 1.00).difference(box(0, 0, .50, .50)))
        assert closures[2].shape.equals(box(1.00, 0, 2.00, 1.00))

    def test_multiline_split_all_regions_together(self, stretch_2_boxes):
        lines: MultiLineString = unary_union(
            [LineString([(-1.00, .50), (1.75, .50)]), LineString([(1.50, -1.00), (1.50, .75)]),
             LineString([(.25, -1.00), (.25, .25)])])
        stretch_2_boxes.split(lines)
        assert len(stretch_2_boxes.closures) == 4
        closures = sorted(stretch_2_boxes.closures,
                          key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 1.00, .50))
        assert closures[1].shape.equals(box(0, .50, 1.00, 1.00))
        assert closures[2].shape.equals(box(1.00, 0, 1.50, .50))
        assert closures[3].shape.equals(box(1.00, 0, 2.00, 1.00).difference(box(1.00, 0, 1.50, .50)))

    @pytest.mark.skip("TODO expect split not to remove original cuts")
    def test_split_closures_not_remove_original_cuts(self, stretch_box_with_exterior_crack):
        lines = [LineString([(2, 0), (2, 3)]), LineString([(0, 2), (3, 2)])]
        stretch_box_with_exterior_crack.split(lines)

        assert len(stretch_box_with_exterior_crack.closures) == 2
        closures = sorted(stretch_box_with_exterior_crack.closures,
                          key=lambda region: (region.shape.centroid.x, region.shape.centroid.y))
        assert closures[0].shape.equals(box(0, 0, 2, 2))
        assert len(closures[0].edges) == 4
        assert len(closures[1].edges) == 9
        assert closures[1].shape == (
            Polygon([(10, 0), (10, 10), (0, 10), (0, 2), (2, 2), (2, 0), (5, 0), (5, 5), (5, 0), (10, 0)]))
