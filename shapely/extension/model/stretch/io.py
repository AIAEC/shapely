from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List

from shapely.extension.model.stretch.stretch_v3 import Stretch, Pivot, Edge, Closure, EdgeSeq
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import Point


@dataclass
class PivotPack:
    origin: Point = field()
    pid: str = field()
    cargo: dict = field(default_factory=dict)
    pivot_type: str = field(default='')

    @classmethod
    def from_(cls, pivot: Pivot) -> 'PivotPack':
        return cls(origin=pivot.origin,
                   pid=pivot._id,
                   cargo=pivot.cargo.data)


@dataclass
class EdgePack:
    from_pid: str = field()
    to_pid: str = field()
    cargo: dict = field(default_factory=dict)
    edge_type: str = field(default='')

    @classmethod
    def from_(cls, edge: Edge) -> 'EdgePack':
        return cls(from_pid=edge.from_pid,
                   to_pid=edge.to_pid,
                   cargo=edge.cargo.data)


@dataclass
class ClosurePack:
    cid: str = field()
    exterior: List[str] = field(default_factory=list)
    interiors: List[List[str]] = field(default_factory=list)
    cargo: dict = field(default_factory=dict)
    closure_type: str = field(default='')

    @classmethod
    def from_(cls, closure: Closure) -> 'ClosurePack':
        return cls(cid=closure._id,
                   exterior=closure.exterior.pids,  # including redundant tail pid
                   interiors=[interior.pids for interior in closure.interiors],  # same as above
                   cargo=closure.cargo.data)


@dataclass
class StretchPack:
    pivot_packs: List[PivotPack] = field()
    edge_packs: List[EdgePack] = field()
    closure_packs: List[ClosurePack] = field()

    @classmethod
    def pack_from(cls, stretch: Stretch) -> 'StretchPack':
        pivot_packs = [PivotPack.from_(pivot) for pivot in stretch.pivots]
        edge_packs = [EdgePack.from_(edge) for edge in stretch.edges]
        closure_packs = [ClosurePack.from_(closure) for closure in stretch.closures]
        return cls(pivot_packs=pivot_packs,
                   edge_packs=edge_packs,
                   closure_packs=closure_packs)

    def unpack(self) -> Stretch:
        stretch = Stretch()

        pivots = [Pivot(origin=pivot_pack.origin,
                        stretch=stretch,
                        id_=pivot_pack.pid,
                        cargo_dict=pivot_pack.cargo) for pivot_pack in self.pivot_packs]

        stretch._pivot_map = OrderedDict([(pivot.id, pivot) for pivot in pivots])

        edges = [Edge(from_pid=edge_pack.from_pid,
                      to_pid=edge_pack.to_pid,
                      stretch=stretch,
                      cargo_dict=edge_pack.cargo) for edge_pack in self.edge_packs]
        stretch._edge_map = OrderedDict([(edge.id, edge) for edge in edges])

        def load_closure(closure_pack: ClosurePack, stretch) -> Closure:
            exterior = closure_pack.exterior
            exterior_seq = EdgeSeq([stretch.edge(f'({pid0},{pid1})')
                                    for pid0, pid1 in win_slice(exterior, win_size=2)])

            interior_seqs = []
            for interior in closure_pack.interiors:
                interior_seqs.append(EdgeSeq([stretch.edge(f'({pid0},{pid1})')
                                              for pid0, pid1 in win_slice(interior, win_size=2)]))

            return Closure(exterior=exterior_seq,
                           interiors=interior_seqs,
                           stretch=stretch,
                           id_=closure_pack.cid,
                           cargo_dict=closure_pack.cargo)

        closures = [load_closure(closure_pack, stretch) for closure_pack in self.closure_packs]
        stretch._closure_map = OrderedDict([(closure.id, closure) for closure in closures])
        stretch.shrink_id_gen()
        return stretch
