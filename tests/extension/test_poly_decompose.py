#!/usr/bin/env python

from shapely.extension.util.partition import _poly_decompose

line1 = [[0, 0], [5, 5]]
line2 = [[5, 0], [0, 5]]
line3 = [[-1, -1], [-5, -5]]
poly = [[0, 0], [5, 0], [5, 5], [2.5, 2.5], [0, 5]]


class TestPoly_Decomp:
    def test_line_intersection(self):
        assert _poly_decompose.lineInt(line1, line2) == [2.5, 2.5]

    def test_no_line_intersection(self):
        assert _poly_decompose.lineInt(line1, line3) == [0, 0]

    def test_line_segments_intersect(self):
        assert _poly_decompose.lineSegmentsIntersect(line1[0], line1[1], line2[0], line2[1]) == True

    def test_no_line_segments_intersect(self):
        assert _poly_decompose.lineSegmentsIntersect(line1[0], line1[1], line3[0], line3[1]) == False

    def test_collinear(self):
        assert _poly_decompose.collinear([0, 0], [5, 0], [10, 0]) == True

    def test_not_collinear(self):
        assert _poly_decompose.collinear([0, 0], [5, 1], [10, 0]) == False

    def test_polygonAt(self):
        index = 2
        assert _poly_decompose.polygonAt(poly, index) == [5, 5]

    def test_polygonAt_negative_index(self):
        index = -2
        assert _poly_decompose.polygonAt(poly, index) == [2.5, 2.5]

    def test_polygonClear(self):
        _poly_decompose.polygonClear(poly)
        assert len(poly) == 0

    def test_polygonAppend(self):
        source = [[0, 5], [2.5, 2.5], [5, 5], [5, 0], [0, 0]]
        _poly_decompose.polygonAppend(poly, source, 0, 5)
        assert poly == source

    def test_polygonMakeCCW(self):
        _poly_decompose.polygonMakeCCW(poly)
        assert poly == [[0, 0], [5, 0], [5, 5], [2.5, 2.5], [0, 5]]

    def test_polygonIsReflex(self):
        assert _poly_decompose.polygonIsReflex(poly, 3) == True

    def test_not_polygonIsReflex(self):
        assert _poly_decompose.polygonIsReflex(poly, 4) == False

    def test_polygonCanSee(self):
        assert _poly_decompose.polygonCanSee(poly, 0, 4) == True

    def test_not_polygonCanSee(self):
        assert _poly_decompose.polygonCanSee(poly, 3, 4) == False

    def test_polygonCopy(self):
        assert _poly_decompose.polygonCopy(poly, 2, 3) == [[5, 5], [2.5, 2.5]]

    def test_polygonCutEdges(self):
        assert _poly_decompose.polygonGetCutEdges(poly) == [[[2.5, 2.5], [0, 0]]]

    def test_polygonDecomp(self):
        assert _poly_decompose.polygonDecomp(poly) == [[[0, 0], [2.5, 2.5], [0, 5]],
                                                       [[0, 0], [5, 0], [5, 5], [2.5, 2.5]]]

    def test_not_polygonIsSimple(self):
        nonsimple_poly = [[0, 0], [5, 0], [0, 5], [5, 5]]
        assert _poly_decompose.polygonIsSimple(nonsimple_poly) == False

    def test_polygonIsSimple(self):
        assert _poly_decompose.polygonIsSimple(poly) == True

    def test_getIntersectionPoint(self):
        assert _poly_decompose.getIntersectionPoint(line1[0], line1[1], line2[0], line2[1]) == [2.5, 2.5]

    def test_polygonQuickDecomp(self):
        assert _poly_decompose.polygonQuickDecomp(poly) == [[[5, 0], [5, 5], [2.5, 2.5]],
                                                            [[2.5, 2.5], [0, 5], [0, 0], [5, 0]]]

    def test_polygonRemoveCollinearPoints(self):
        collinear_poly = [[0, 0], [5, 0], [10, 0], [5, 5]]
        _poly_decompose.polygonRemoveCollinearPoints(collinear_poly)
        assert collinear_poly == [[0, 0], [10, 0], [5, 5]]
