"""Tests for season-level league transitions (P1-17)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.database import get_connection
from app.db.repositories import PlayerRepository, ResultRepository, TournamentRepository
from app.services.audit_log import SEASON_TRANSFER_APPLIED
from app.services.season_transfer import (
    apply_season_transfers,
    compute_season_transfer_candidates,
)
from app.services.tournament_lifecycle import transition_tournament_status


pytestmark = pytest.mark.integration


def _create_player(player_repo: PlayerRepository, *, last_name: str, first_name: str) -> int:
    return player_repo.create(
        {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": None,
            "birth_date": None,
            "gender": None,
            "coach": None,
            "club": None,
            "notes": None,
        }
    )


def _create_published_tournament_with_players(
    *,
    connection,
    league_code: str,
    tournament_date: str,
    players_data: list[tuple[str, str, int]],
) -> tuple[int, list[int]]:
    """Create a published tournament with players and results.

    players_data: list of (last_name, first_name, points_total)
    """
    tournaments = TournamentRepository(connection)
    players = PlayerRepository(connection)
    results = ResultRepository(connection)

    tournament_id = tournaments.create(
        {
            "name": f"Tournament {league_code} {tournament_date}",
            "date": tournament_date,
            "category_code": "U18",
            "league_code": league_code,
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "published",
            "has_draft_changes": 0,
        }
    )

    player_ids: list[int] = []
    for place, (last_name, first_name, points_total) in enumerate(players_data, start=1):
        player_id = _create_player(players, last_name=last_name, first_name=first_name)
        player_ids.append(player_id)
        results.create(
            {
                "tournament_id": tournament_id,
                "player_id": player_id,
                "place": place,
                "score_set": 0,
                "score_sector20": 0,
                "score_big_round": 0,
                "rank_set": None,
                "rank_sector20": None,
                "rank_big_round": None,
                "points_classification": 0,
                "points_place": points_total,
                "points_total": points_total,
                "calc_version": "tests",
            }
        )

    return tournament_id, player_ids


def test_compute_candidates_returns_bottom4_premier_top4_first(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-basic.db")

    # 8 players in PREMIER with descending points
    _create_published_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
            ("Premier", "P3", 80),
            ("Premier", "P4", 70),
            ("Premier", "P5", 60),
            ("Premier", "P6", 50),
            ("Premier", "P7", 40),
            ("Premier", "P8", 30),
        ],
    )

    # 8 players in FIRST with descending points
    _create_published_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
            ("First", "F6", 50),
            ("First", "F7", 40),
            ("First", "F8", 30),
        ],
    )

    preview = compute_season_transfer_candidates(
        connection=connection, n=1, transfer_count=4
    )

    assert preview.available is True
    assert preview.reason is None

    # Bottom 4 of PREMIER: positions 5,6,7,8 (points 60,50,40,30)
    assert len(preview.relegated) == 4
    relegated_points = sorted([c.rating_points for c in preview.relegated])
    assert relegated_points == [30, 40, 50, 60]

    # Top 4 of FIRST: positions 1,2,3,4 (points 100,90,80,70)
    assert len(preview.promoted) == 4
    promoted_points = sorted([c.rating_points for c in preview.promoted], reverse=True)
    assert promoted_points == [100, 90, 80, 70]


def test_fewer_than_4_players_transfers_all_available(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-fewer.db")

    # Only 2 players in PREMIER
    _create_published_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
        ],
    )

    # 8 players in FIRST
    _create_published_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
            ("First", "F6", 50),
            ("First", "F7", 40),
            ("First", "F8", 30),
        ],
    )

    preview = compute_season_transfer_candidates(
        connection=connection, n=1, transfer_count=4
    )

    assert preview.available is True
    # Both PREMIER players should be relegated
    assert len(preview.relegated) == 2
    # Warning about fewer players
    assert any("менее 4 игроков" in w for w in preview.warnings)


def test_tie_at_boundary_includes_all_tied(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-tie.db")

    # 8 players in PREMIER: positions 5 and 6 have same points (50)
    _create_published_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
            ("Premier", "P3", 80),
            ("Premier", "P4", 70),
            ("Premier", "P5", 50),
            ("Premier", "P6", 50),
            ("Premier", "P7", 40),
            ("Premier", "P8", 30),
        ],
    )

    # 8 players in FIRST
    _create_published_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
            ("First", "F6", 50),
            ("First", "F7", 40),
            ("First", "F8", 30),
        ],
    )

    preview = compute_season_transfer_candidates(
        connection=connection, n=1, transfer_count=4
    )

    assert preview.available is True
    # Bottom 4 from PREMIER would be positions 5,6,7,8 (50,50,40,30)
    # But position 4 has 70 which is different, so no extra tie
    # Positions 5 and 6 both have 50, but they are already inside the bottom 4
    # The boundary is at position 5 (from the end). Let me trace:
    # snapshot sorted by points desc: P1(100), P2(90), P3(80), P4(70), P5(50), P6(50), P7(40), P8(30)
    # total=8, transfer_count=4, cutoff_index=4 (index 4 = P5 with 50 pts)
    # boundary_points = 50
    # Check above: index 3 = P4 with 70 != 50, so start_index stays at 4
    # selected = snapshot[4:] = [P5, P6, P7, P8] -- 4 items
    # len(selected) == transfer_count, no extra warning for tie
    # Actually the tie is within the selected group, not at boundary
    assert len(preview.relegated) == 4

    # Now test a real boundary tie: positions 4 and 5 have same points
    connection2 = get_connection(tmp_path / "season-transfer-tie2.db")

    _create_published_tournament_with_players(
        connection=connection2,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
            ("Premier", "P3", 80),
            ("Premier", "P4", 60),
            ("Premier", "P5", 60),
            ("Premier", "P6", 50),
            ("Premier", "P7", 40),
            ("Premier", "P8", 30),
        ],
    )

    _create_published_tournament_with_players(
        connection=connection2,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
            ("First", "F6", 50),
            ("First", "F7", 40),
            ("First", "F8", 30),
        ],
    )

    preview2 = compute_season_transfer_candidates(
        connection=connection2, n=1, transfer_count=4
    )

    assert preview2.available is True
    # snapshot: P1(100), P2(90), P3(80), P4(60), P5(60), P6(50), P7(40), P8(30)
    # cutoff_index = 4, snapshot[4] = P5(60), boundary_points = 60
    # Check above: snapshot[3] = P4(60) == 60, so start_index goes to 3
    # Check above: snapshot[2] = P3(80) != 60, stop
    # selected = snapshot[3:] = [P4, P5, P6, P7, P8] -- 5 items
    assert len(preview2.relegated) == 5
    assert any("Равенство очков" in w for w in preview2.warnings)


def test_empty_season_returns_unavailable(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-empty.db")

    preview = compute_season_transfer_candidates(connection=connection, n=1)

    assert preview.available is False
    assert preview.reason is not None
    assert "Нет опубликованных результатов" in preview.reason


def test_apply_season_transfers_creates_events_and_audit(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-apply.db")

    _create_published_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
            ("Premier", "P3", 80),
            ("Premier", "P4", 70),
            ("Premier", "P5", 60),
            ("Premier", "P6", 50),
            ("Premier", "P7", 40),
            ("Premier", "P8", 30),
        ],
    )

    _create_published_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
            ("First", "F6", 50),
            ("First", "F7", 40),
            ("First", "F8", 30),
        ],
    )

    preview = compute_season_transfer_candidates(
        connection=connection, n=1, transfer_count=4
    )
    assert preview.available is True

    result = apply_season_transfers(connection=connection, preview=preview)

    assert result.applied_count == 8  # 4 relegated + 4 promoted

    # Verify league_transfer_events
    rows = connection.execute(
        "SELECT * FROM league_transfer_events WHERE reason = 'season_transfer'"
    ).fetchall()
    assert len(rows) == 8

    # Verify audit log
    audit_rows = connection.execute(
        "SELECT * FROM audit_log WHERE event_type = ?",
        (SEASON_TRANSFER_APPLIED,),
    ).fetchall()
    assert len(audit_rows) == 8


def test_apply_creates_restore_point_before_changes(tmp_path: Path) -> None:
    connection = get_connection(tmp_path / "season-transfer-restore.db")

    _create_published_tournament_with_players(
        connection=connection,
        league_code="PREMIER",
        tournament_date="2026-05-01",
        players_data=[
            ("Premier", "P1", 100),
            ("Premier", "P2", 90),
            ("Premier", "P3", 50),
            ("Premier", "P4", 40),
            ("Premier", "P5", 30),
        ],
    )

    _create_published_tournament_with_players(
        connection=connection,
        league_code="FIRST",
        tournament_date="2026-05-01",
        players_data=[
            ("First", "F1", 100),
            ("First", "F2", 90),
            ("First", "F3", 80),
            ("First", "F4", 70),
            ("First", "F5", 60),
        ],
    )

    preview = compute_season_transfer_candidates(
        connection=connection, n=1, transfer_count=4
    )
    result = apply_season_transfers(connection=connection, preview=preview)

    # Verify restore point was created
    rp_rows = connection.execute(
        "SELECT * FROM restore_points WHERE reason = 'season_transfer'"
    ).fetchall()
    assert len(rp_rows) == 1
    assert rp_rows[0]["operation_group_id"] == result.operation_group_id


def test_existing_publish_flow_not_broken(tmp_path: Path) -> None:
    """Ensure the existing per-tournament league transfer on publish still works."""
    connection = get_connection(tmp_path / "season-transfer-existing-flow.db")

    tournaments = TournamentRepository(connection)
    players_repo = PlayerRepository(connection)
    results_repo = ResultRepository(connection)

    tournament_id = tournaments.create(
        {
            "name": "League Tournament 2026-06-01",
            "date": "2026-06-01",
            "category_code": "U18",
            "league_code": "PREMIER",
            "is_adult_mode": 0,
            "source_files": "[]",
            "status": "draft",
            "has_draft_changes": 1,
        }
    )

    player_id = _create_player(players_repo, last_name="Test", first_name="Player")
    results_repo.create(
        {
            "tournament_id": tournament_id,
            "player_id": player_id,
            "place": 1,
            "score_set": 0,
            "score_sector20": 0,
            "score_big_round": 0,
            "rank_set": None,
            "rank_sector20": None,
            "rank_big_round": None,
            "points_classification": 0,
            "points_place": 100,
            "points_total": 100,
            "calc_version": "tests",
        }
    )

    for target in ("review", "confirmed", "published"):
        result = transition_tournament_status(
            connection=connection,
            tournament_id=tournament_id,
            to_status=target,
            context={"actor": "tests", "operation_group_id": "op-existing"},
        )
        assert result["ok"] is True

    from app.services.league_transfer import list_player_league_transfers

    events = list_player_league_transfers(connection, player_id)
    assert len(events) == 1
    assert events[0].to_league_code == "PREMIER"
