from shapely.extension.model.cargo import Cargo, ConsensusCargo


def test_cargo_usage_as_dict():
    assert Cargo(default=10).get('none') == 10

    cargo = Cargo()
    assert cargo['test'] is None

    cargo['test'] = 1
    assert cargo['test'] == 1

    cargo.update(Cargo({'test': 1, 'test1': 0}))
    assert cargo.get('test') == 1
    assert cargo.get('test1') == 0
    cargo.update({'test': 0, 'test1': 1})
    assert cargo.get('test') == 0
    assert cargo.get('test1') == 1

    copied = cargo.copy()
    assert copied.get('test') == 0
    assert copied.get('test1') == 1
    assert copied != cargo
    assert copied.host == cargo.host

    assert cargo.get('test1') == 1
    cargo.pop('test1')
    assert cargo.get('test1') is None

    assert list(cargo.values()) == [0]
    assert list(cargo.keys()) == ['test']
    assert list(cargo.items()) == [('test', 0)]

    assert cargo.setdefault('test1', 1) == 1
    assert cargo.get('test1') == 1

    cargo.clear()
    assert cargo.get('test') is None
    assert cargo.get('test1') is None
    assert len(cargo) == 0

    cargo.pop('test')


def test_cargo_to_dict():
    cargo = Cargo({'test0': 0, 'test1': 1})
    assert {'test0': 0, 'test1': 1} == dict(cargo)
    cargo_dict = dict(cargo)
    cargo_dict['test2'] = 2

    # cargo_dict is a copy
    assert cargo.get('test2') is None


def test_consensus_cargo():
    cargos = [Cargo({'test0': 0, 'test1': 1}),
              Cargo({'test0': 1, 'test2': 2}),
              Cargo({'test0': 0, 'test1': 3}),
              Cargo({'test1': 1})]

    cargo = ConsensusCargo(cargos)
    assert len(cargo) == 3
    assert cargo['test0'] == 0
    assert cargo['test1'] == 1
    assert cargo['test2'] == 2
