from app.domain.tournament_lifecycle import can_transition


def test_happy_path_transitions() -> None:
    assert can_transition("draft", "review", {})
    assert can_transition("review", "confirmed", {})
    assert can_transition("confirmed", "published", {})
    assert can_transition("published", "archived", {})


def test_forbidden_transition_without_required_controls() -> None:
    assert not can_transition("published", "review", {})


def test_controlled_correction_transition() -> None:
    context = {
        "reason": "Обнаружена ошибка в финальной сетке",
        "restore": True,
        "audit": {"actor": "qa.manager", "ticket": "OPS-142"},
    }
    assert can_transition("published", "review", context)
