from catalog import default_structure
from workfiles import structure_from_dict, structure_to_dict


def test_work_file_round_trip_preserves_structure():
    original = default_structure()
    data = structure_to_dict(original)
    restored = structure_from_dict(data)
    assert [(piece.piece_id, piece.definition.key, piece.x_in, piece.y_in, piece.angle_deg)
            for piece in restored.pieces] == [
                (piece.piece_id, piece.definition.key, piece.x_in, piece.y_in, piece.angle_deg)
                for piece in original.pieces
            ]
    assert restored.supports == original.supports
    assert restored.welds == original.welds


def test_work_file_rejects_unknown_piece_type():
    data = structure_to_dict(default_structure())
    data["pieces"][0]["type"] = "not-a-piece"
    try:
        structure_from_dict(data)
    except ValueError as error:
        assert "Unknown catalog piece type" in str(error)
    else:
        raise AssertionError("Unknown piece type was accepted")

