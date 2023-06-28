from typing import List, Optional, Union

from shapely.extension.constant import END_ATTACH_RATIO_DIGIT, STRETCH_EPS
from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.creator import ClosureReconstructor
from shapely.extension.model.stretch.stretch_v3 import Closure, Edge
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import LineString, MultiLineString


class Cut:
    def __init__(self, closures: List[Closure], closure_strategy: Optional[ClosureStrategy] = None):
        self._closures = closures
        self._closure_strategy = closure_strategy or ClosureStrategy()

    def by(self, line: Union[LineString, MultiLineString],
           dist_tol_to_pivot: float = STRETCH_EPS,
           dist_tol_to_edge: float = STRETCH_EPS,
           end_attach_ratio_digit: int = END_ATTACH_RATIO_DIGIT) -> 'Cut':

        new_closures: List[Closure] = []

        for closure in self._closures:
            # extra each linestring in the intersection of closure and line
            # due to SHAPELY DARK LAW, the resulting linestrings are not guaranteed to be inside closure strictly,
            # and it might partially sit on the boundary of closure.
            # in any case, this should not cause problem, since we assume cut_closure_by_lines may handle it.
            segments: List[LineString] = closure.shape.intersection(line).ext.flatten(LineString).list()

            if not segments:
                new_closures.append(closure)
                continue

            new_closures.extend(self._cut_closure_by_lines(closure=closure,
                                                           lines=segments,
                                                           dist_tol_to_pivot=dist_tol_to_pivot,
                                                           dist_tol_to_edge=dist_tol_to_edge,
                                                           end_attach_ratio_digit=end_attach_ratio_digit))

        self._closures = new_closures
        return self

    def _cut_closure_by_line(self, closure: Closure,
                             line_inside: LineString,
                             dist_tol_to_pivot: float = STRETCH_EPS,
                             dist_tol_to_edge: float = STRETCH_EPS,
                             end_attach_ratio_digit: int = END_ATTACH_RATIO_DIGIT) -> List[Closure]:
        new_edges: List[Edge] = []
        new_edges.extend(closure.stretch.add_edge(line=line_inside,
                                                  dist_tol_to_pivot=dist_tol_to_pivot,
                                                  dist_tol_to_edge=dist_tol_to_edge,
                                                  end_attach_ratio_digit=end_attach_ratio_digit))
        new_edges.extend(closure.stretch.add_edge(line=line_inside.ext.reverse(),
                                                  dist_tol_to_pivot=dist_tol_to_pivot,
                                                  dist_tol_to_edge=dist_tol_to_edge,
                                                  end_attach_ratio_digit=end_attach_ratio_digit))

        unique_new_edges = list(OrderedSet(new_edges + closure.edges))
        stretch = closure.stretch

        # remove current closure from stretch
        closure.stretch.delete_closure(closure, gc=False)

        return (ClosureReconstructor(stretch)
                .cargo(closure.cargo.data)
                .from_edges(unique_new_edges, self._closure_strategy)
                .reconstruct(dist_tol_to_pivot=dist_tol_to_pivot,
                             dist_tol_to_edge=dist_tol_to_edge,
                             end_attach_ratio_digit=end_attach_ratio_digit))

    def _cut_closure_by_lines(self, closure: Closure,
                              lines: List[LineString],
                              dist_tol_to_pivot: float = STRETCH_EPS,
                              dist_tol_to_edge: float = STRETCH_EPS,
                              end_attach_ratio_digit: int = END_ATTACH_RATIO_DIGIT) -> List[Closure]:

        closures: List[Closure] = [closure]
        new_closures: List[Closure] = []

        for line in lines:
            for closure in closures:
                if not closure.shape.intersects(line):
                    new_closures.append(closure)
                    continue

                new_closures.extend(self._cut_closure_by_line(closure=closure,
                                                              line_inside=line,
                                                              dist_tol_to_pivot=dist_tol_to_pivot,
                                                              dist_tol_to_edge=dist_tol_to_edge,
                                                              end_attach_ratio_digit=end_attach_ratio_digit))

            closures = new_closures
            new_closures = []

        return closures

    def closures(self) -> List[Closure]:
        return self._closures
