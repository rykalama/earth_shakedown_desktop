from catalog import default_structure
from models import Structure
from physics import ShakeSimulation


def test_new_board_is_empty():
    assert Structure().pieces == []


def test_default_catalog_cost_is_repeatable():
    structure = default_structure()
    assert structure.total_cost() == 48 + 18 + 18 + 32 + 24 + 16 + 16 + 29
    assert len(structure.supports) >= len(structure.pieces)


def test_simulation_has_one_body_per_piece():
    structure = default_structure()
    simulation = ShakeSimulation(structure)
    assert set(simulation.bodies) == {piece.piece_id for piece in structure.pieces}


def test_support_tolerance_allows_initial_gaps_but_detects_separation():
    structure = default_structure()
    simulation = ShakeSimulation(structure)
    assert simulation.detect_failure(0.0) is None
    simulation.bodies[5].position = (simulation.bodies[4].position.x + 1000, simulation.bodies[4].position.y)
    failure = simulation.detect_failure(0.1)
    assert failure is not None
    assert failure.piece_id == 5


def test_each_support_relationship_fails_when_its_child_separates():
    for piece_id, parent_id in ((2, 1), (4, 2), (5, 4), (8, 5)):
        structure = default_structure()
        simulation = ShakeSimulation(structure)
        simulation.bodies[piece_id].position = (
            simulation.bodies[parent_id].position.x + 70 * 3,
            simulation.bodies[piece_id].position.y,
        )
        failure = simulation.detect_failure(0.1)
        assert failure is not None
        assert failure.piece_id == piece_id
        assert failure.reason == "required support disconnected"


def test_piece_outside_table_is_a_trial_failure():
    structure = default_structure()
    simulation = ShakeSimulation(structure)
    simulation.bodies[1].position = (400 * 3, simulation.bodies[1].position.y)
    failure = simulation.detect_failure(0.1)
    assert failure is not None
    assert failure.piece_id == 1
    assert failure.reason == "piece fell off the shake table"

