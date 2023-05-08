import shapely.wkt
from shapely.extension.model.stretch.stretch_v3 import Edge, Pivot
from shapely.geometry import Point, LineString, box


class TestQuery:
    def test_query_edges(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        edges = stretch.edges_by_query(Point(1, 1))
        assert isinstance(edges, list)
        assert len(edges) == 4

        edges = stretch.edges_by_query(LineString([(0.5, 1), (1.5, 1)]))
        assert isinstance(edges, list)
        assert len(edges) == 4

        edges = stretch.edges_by_query(box(0.5, 0.5, 1.5, 1))
        assert isinstance(edges, list)
        assert len(edges) == 4

    def test_query_pivots(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivots = stretch.pivots_by_query(Point(0, 0))
        assert isinstance(pivots, list)
        assert len(pivots) == 1

        pivots = stretch.pivots_by_query(LineString([(0, 0), (1, 1)]))
        assert isinstance(pivots, list)
        assert len(pivots) == 2

        pivots = stretch.pivots_by_query(box(0, 0, 1, 1))
        assert isinstance(pivots, list)
        assert len(pivots) == 4

    def test_query_closures(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        closures = stretch.closures_by_query(Point(0, 0))
        assert isinstance(closures, list)
        assert len(closures) == 1

        closures = stretch.closures_by_query(LineString([(0, 0), (1, 1)]))
        assert isinstance(closures, list)
        assert len(closures) == 2

        closures = stretch.closures_by_query(box(0, 0, 0.5, 1))
        assert isinstance(closures, list)
        assert len(closures) == 1

    def test_find_edge(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        edge = stretch.find_edge(Point(1, 1))
        assert isinstance(edge, Edge)

        edge = stretch.find_edge(LineString([(0.8, 1), (1.5, 1)]))
        assert isinstance(edge, Edge)
        assert edge == stretch.edge('(5,2)')

        edge = stretch.find_edge(box(0.2, 0.5, 1.2, 1))
        assert isinstance(edge, Edge)
        assert edge == stretch.edge('(2,3)')

        edge = stretch.find_edge(Point(-1, -1))
        assert edge is None

    def test_find_pivot(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        pivot = stretch.find_pivot(Point(0, 0))
        assert isinstance(pivot, Pivot)

        pivot = stretch.find_pivot(LineString([(0, 1), (1.5, 1)]))
        assert isinstance(pivot, Pivot)
        assert pivot == stretch.pivot('2')

        pivot = stretch.find_pivot(box(-1, -1, 1, 1))
        assert isinstance(pivot, Pivot)
        assert pivot == stretch.pivot('0')

        pivot = stretch.find_pivot(Point(-1, -1))
        assert pivot is None

    def test_find_edge_with_reverse_edge(self, stretch_002):
        query_line = shapely.wkt.loads(
            'LINESTRING (144.0640604486713 31.58116830738623, 102.2051447298799 31.5835747533993)')
        edge = stretch_002.find_edge(query_geom=query_line)
        assert isinstance(edge, Edge)
        assert edge.shape.ext.angle().including_angle(query_line.ext.angle()) < 1e-10
