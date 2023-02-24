from copy import deepcopy
from typing import Union, List

from shapely.extension.functional import seq
from shapely.extension.model.stretch.stretch_v3 import Edge, Pivot, EdgeSeq


class Expansion:
    def __init__(self, edge: Edge):
        self._edge = edge

    def _expand_helper(self, replaced_edge_seq, replaced_reverse_edge_seq=None) -> EdgeSeq:
        # modify edge's closure if edge has one
        if self._edge.closure:
            origin_closure = self._edge.closure

            # first change the edge seq of closure, then update edges' back ref
            origin_edge_seq = origin_closure.seq_of_edge(self._edge)
            origin_edge_seq.replace_and_discard(self._edge, list(replaced_edge_seq))
            origin_edge_seq.set_closure(origin_closure)

        self._edge.stretch.discard_edge(self._edge)

        origin_reverse_closure = self._edge.reverse_closure
        if replaced_reverse_edge_seq:
            # modify the reverse edge's closure if it has one.
            # first change the edge seq of closure, then update edges' back ref
            if origin_reverse_closure:
                origin_reverse_edge_seq = origin_reverse_closure.seq_of_edge(self._edge.reverse)
                origin_reverse_edge_seq.replace_and_discard(self._edge.reverse, list(replaced_reverse_edge_seq))
                origin_reverse_edge_seq.set_closure(origin_reverse_closure)

            self._edge.stretch.discard_edge(self._edge.reverse)

        return replaced_edge_seq

    def _expand(self, pivots_in_seq: List[Pivot]) -> EdgeSeq:
        # remove from and to pivots from pivots_in_seq
        mid_pivots = (seq(pivots_in_seq)
                      .drop_while(lambda p: p is self._edge.from_pivot)
                      .take_while(lambda p: p is not self._edge.to_pivot)
                      .list())

        if not mid_pivots:
            return EdgeSeq([self._edge])

        # reconstruct pivots_in_seq by from_pivot, mid_pivots, to_pivot
        pivots_in_seq = [self._edge.from_pivot] + mid_pivots + [self._edge.to_pivot]

        replaced_edge_seq = Pivot.connect(pivots_in_seq)

        origin_cargo_dict = self._edge.cargo.data
        replaced_edge_seq[0].cargo.update(deepcopy(origin_cargo_dict))
        replaced_edge_seq[-1].cargo.update(deepcopy(origin_cargo_dict))

        if self._edge in replaced_edge_seq:
            raise ValueError('pivots given to expand edge contains pair of from_pivot and to_pivot of edge')

        replaced_reverse_edge_seq = None
        if self._edge.reverse:
            replaced_reverse_edge_seq = Pivot.connect(pivots_in_seq[::-1])

            reverse_cargo_dict = self._edge.reverse.cargo.data
            replaced_reverse_edge_seq[0].cargo.update(deepcopy(reverse_cargo_dict))
            replaced_reverse_edge_seq[-1].cargo.update(deepcopy(reverse_cargo_dict))

            if self._edge.reverse in replaced_reverse_edge_seq:
                raise ValueError('expand reverse edge by its origin from_pivot or to_pivot')

        edge_seq = self._expand_helper(replaced_edge_seq, replaced_reverse_edge_seq)

        # disable the self._edge, make it disposable
        self._edge = None

        return edge_seq

    def by_pivot(self, pivot: Pivot) -> EdgeSeq:
        pivots = [self._edge.from_pivot, pivot, self._edge.to_pivot]
        return self._expand(pivots)

    def by_pivots(self, pivots: List[Pivot]) -> EdgeSeq:
        return self._expand(pivots)

    def by_edge(self, edge: Edge) -> EdgeSeq:
        pivots = [self._edge.from_pivot, edge.from_pivot, edge.to_pivot, self._edge.to_pivot]
        return self._expand(pivots)

    def by_edge_seq(self, edge_seq: EdgeSeq) -> EdgeSeq:
        pivots = [self._edge.from_pivot, *edge_seq.pivots, self._edge.to_pivot]
        return self._expand(pivots)

    def by(self, splitter: Union[Pivot, Edge, EdgeSeq, List[Pivot]]) -> EdgeSeq:
        """
        [LOW LEVEL API] Expand the edge by splitter.
        If expansion failed for some reason, garbage closures will remain in the stretch.
        The stretch data might be corrupted!! and there is no recover recipe for that.
        Parameters
        ----------
        splitter

        Returns
        -------

        """
        if isinstance(splitter, Pivot):
            return self.by_pivot(splitter)
        elif isinstance(splitter, Edge):
            return self.by_edge(splitter)
        elif isinstance(splitter, EdgeSeq):
            return self.by_edge_seq(splitter)
        elif isinstance(splitter, list) and all(isinstance(item, Pivot) for item in splitter):
            return self.by_pivots(splitter)
        raise TypeError('splitter must be Pivot, Edge or EdgeSeq')
