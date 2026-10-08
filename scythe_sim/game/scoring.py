"""Research milestones, final score, and deterministic tie-breaking."""

from __future__ import annotations

from scythe_sim.game.rules import (
    controlled_resource_count,
    controlled_territories,
    worker_count,
)
from scythe_sim.game.models import BuildingType
from scythe_sim.game.state import GameState


def earned_stars(state: GameState, player_id: int) -> set[str]:
    player = state.players[player_id]
    stars: set[str] = set()
    territories = len(controlled_territories(state, player_id))
    resources = controlled_resource_count(state, player_id)
    workers = worker_count(state, player_id)
    if len(player.upgrades) >= 2:
        stars.add("innovator")
    if len(player.buildings) >= 3:
        stars.add("builder")
    if territories >= 6:
        stars.add("expansion")
    if workers >= 5:
        stars.add("workforce")
    if resources >= 8:
        stars.add("stockpile")
    return stars


def update_stars(state: GameState) -> None:
    for player_id, player in state.players.items():
        player.stars.update(earned_stars(state, player_id))


def score_player(state: GameState, player_id: int) -> int:
    player = state.players[player_id]
    territories = len(controlled_territories(state, player_id))
    resources = controlled_resource_count(state, player_id)
    extra_workers = max(0, worker_count(state, player_id) - 2)
    return (
        5 * len(player.stars)
        + 2 * territories
        + resources // 2
        + 3 * len(player.buildings)
        + (2 if BuildingType.MONUMENT in player.buildings else 0)
        + 2 * len(player.upgrades)
        + extra_workers
    )


def ranking_key(state: GameState, player_id: int) -> tuple[int, int, int, int, int]:
    return (
        score_player(state, player_id),
        len(state.players[player_id].stars),
        len(controlled_territories(state, player_id)),
        controlled_resource_count(state, player_id),
        -player_id,
    )


def finish_game(state: GameState, reason: str) -> None:
    state.game_over = True
    state.end_reason = reason
    state.final_scores = {
        player_id: score_player(state, player_id) for player_id in state.players
    }
    state.winner = max(state.players, key=lambda player_id: ranking_key(state, player_id))
