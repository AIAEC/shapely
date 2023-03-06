from shapely.extension.model.stretch.io import StretchPack


def test_create_stretch_pack_from_stretch(stretch_box):
    stretch_box.pivots[0].cargo['test'] = 'pivot'
    stretch_box.edges[0].cargo['test'] = 'edge'
    stretch_box.closures[0].cargo['test'] = 'closure'

    stretch_pack = StretchPack.pack_from(stretch_box)
    assert isinstance(stretch_pack, StretchPack)
    assert len(stretch_pack.pivot_packs) == 4
    assert len(stretch_pack.edge_packs) == 4
    assert len(stretch_pack.closure_packs) == 1

    assert stretch_pack.pivot_packs[0].cargo['test'] == 'pivot'
    assert stretch_pack.edge_packs[0].cargo['test'] == 'edge'
    assert stretch_pack.closure_packs[0].cargo['test'] == 'closure'


def test_create_stretch_from_stretch_pack(stretch_box_holes):
    stretch = stretch_box_holes

    stretch.pivots[0].cargo['test'] = 'pivot'
    stretch.edges[0].cargo['test'] = 'edge'
    stretch.closures[0].cargo['test'] = 'closure'

    assert len(stretch.pivots) == 12
    assert len(stretch.edges) == 12
    assert len(stretch.closures) == 1
    assert len(stretch.closures[0].interiors) == 2

    stretch_pack = StretchPack.pack_from(stretch)
    stretch_recovered = stretch_pack.unpack()

    assert len(stretch_recovered.pivots) == 12
    assert len(stretch_recovered.edges) == 12
    assert len(stretch_recovered.closures) == 1
    assert len(stretch_recovered.closures[0].interiors) == 2

    assert stretch_recovered.pivots[0].cargo['test'] == 'pivot'
    assert stretch_recovered.edges[0].cargo['test'] == 'edge'
    assert stretch_recovered.closures[0].cargo['test'] == 'closure'

    assert stretch is not stretch_recovered
    for pivot, pivot_recover in zip(stretch.pivots, stretch_recovered.pivots):
        assert pivot is not pivot_recover
        assert pivot.origin == pivot_recover.origin
        assert pivot.id == pivot_recover.id
        assert pivot.cargo.data == pivot_recover.cargo.data

    for edge, edge_recover in zip(stretch.edges, stretch_recovered.edges):
        assert edge is not edge_recover
        assert edge.from_pid == edge_recover.from_pid
        assert edge.to_pid == edge_recover.to_pid
        assert edge.cargo.data == edge_recover.cargo.data

    for closure, closure_recover in zip(stretch.closures, stretch_recovered.closures):
        assert closure is not closure_recover
        assert closure.exterior.pids == closure_recover.exterior.pids
        assert closure.cargo.data == closure_recover.cargo.data
        for interior, interior_recover in zip(closure.interiors, closure_recover.interiors):
            assert interior.pids == interior_recover.pids
            assert interior.shape.equals(interior_recover.shape)

        assert closure.shape.equals(closure_recover.shape)
