from catalog import default_structure
from physics import ShakeSimulation


def test_default_catalog_cost_is_repeatable():
    structure = default_structure()
    assert structure.total_cost() == 48 + 18 + 18 + 32 + 24 + 16 + 16 + 29
    assert len(structure.supports) >= len(structure.pieces)


def test_simulation_has_one_body_per_piece():
    structure = default_structure()
    simulation = ShakeSimulation(structure)
    assert set(simulation.bodies) == {piece.piece_id for piece in structure.pieces}

