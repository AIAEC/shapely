from typing import List, Optional, Union

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.creator import ClosureReconstructor
from shapely.extension.model.stretch.stretch_v3 import Closure, Edge
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import LineString, MultiLineString, Point


class Cut:
    def __init__(self, closures: List[Closure], closure_strategy: Optional[ClosureStrategy] = None):
        self._closures = closures
        self._closure_strategy = closure_strategy or ClosureStrategy()

    def by(self, line: Union[LineString, MultiLineString],
           dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
           dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> 'Cut':

        new_closures: List[Closure] = []

        for closure in self._closures:
            segments: List[LineString] = self.segments_inside_closure(line, closure)
            if not segments:
                new_closures.append(closure)
                continue

            new_closures.extend(self.cut_closure_by_lines(closure=closure,
                                                          lines_inside=segments,
                                                          dist_tol_to_pivot=dist_tol_to_pivot,
                                                          dist_tol_to_edge=dist_tol_to_edge))

        self._closures = new_closures
        return self

    @staticmethod
    def segments_inside_closure(line: Union[LineString, MultiLineString], closure: Closure) -> List[LineString]:
        closure_poly = closure.shape

        # filter only the segments laid in the interior space of closure not on the boundary
        return (closure_poly.intersection(line)
                .ext.flatten(LineString)
                .filter(closure_poly.contains)
                .list())

    def cut_closure_by_line(self, closure: Closure,
                            line_inside: LineString,
                            dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                            dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> List[Closure]:
        new_edges: List[Edge] = []
        new_edges.extend(closure.stretch.add_edge(line=line_inside,
                                                  dist_tol_to_pivot=dist_tol_to_pivot,
                                                  dist_tol_to_edge=dist_tol_to_edge))
        new_edges.extend(closure.stretch.add_edge(line=line_inside.ext.reverse(),
                                                  dist_tol_to_pivot=dist_tol_to_pivot,
                                                  dist_tol_to_edge=dist_tol_to_edge))

        unique_new_edges = list(OrderedSet(new_edges + closure.edges))
        stretch = closure.stretch

        # remove current closure from stretch
        closure.stretch.delete_closure(closure, gc=False)

        return (ClosureReconstructor(stretch)
                .cargo(closure.cargo.data)
                .from_edges(unique_new_edges, self._closure_strategy)
                .reconstruct(dist_tol_to_pivot=dist_tol_to_pivot, dist_tol_to_edge=dist_tol_to_edge))

    def cut_closure_by_lines(self, closure: Closure,
                             lines_inside: List[LineString],
                             dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                             dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> List[Closure]:

        closures: List[Closure] = [closure]
        new_closures: List[Closure] = []
        for line_inside in lines_inside:
            for closure in closures:
                if not closure.shape.contains(line_inside):
                    new_closures.append(closure)
                    continue

                new_closures.extend(self.cut_closure_by_line(closure=closure,
                                                             line_inside=line_inside,
                                                             dist_tol_to_pivot=dist_tol_to_pivot,
                                                             dist_tol_to_edge=dist_tol_to_edge))

            closures = new_closures
            new_closures = []

        return closures

    def closures(self) -> List[Closure]:
        return self._closures
