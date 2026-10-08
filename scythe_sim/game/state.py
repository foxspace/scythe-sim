"""Complete, cloneable state for one reproducible game."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from scythe_sim.game.board import create_board, tile_id
from scythe_sim.game.models import Faction, PlayerState, Tile, Unit, UnitType


@dataclass
class GameState:
    seed: int
    board: dict[str, Tile]
    players: dict[int, PlayerState]
    units: dict[str, Unit]
    current_player: int = 0
    turn_number: int = 1
    game_over: bool = False
    winner: int | None = None
    final_scores: dict[int, int] = field(default_factory=dict)
    end_reason: str | None = None

    def clone(self) -> "GameState":
        return deepcopy(self)


def new_game(seed: int = 0) -> GameState:
    """Create the standard mirrored two-player setup."""

    factions = (Faction.RUSVIET, Faction.NORDIC)
    if (seed // 2) % 2:
        factions = tuple(reversed(factions))
    players = {
        0: PlayerState(id=0, faction=factions[0]),
        1: PlayerState(id=1, faction=factions[1]),
    }
    units = {
        "p0-character": Unit("p0-character", 0, UnitType.CHARACTER, tile_id(-2, 0)),
        "p0-worker-1": Unit("p0-worker-1", 0, UnitType.WORKER, tile_id(-2, 0)),
        "p0-worker-2": Unit("p0-worker-2", 0, UnitType.WORKER, tile_id(-2, 1)),
        "p1-character": Unit("p1-character", 1, UnitType.CHARACTER, tile_id(2, 0)),
        "p1-worker-1": Unit("p1-worker-1", 1, UnitType.WORKER, tile_id(2, 0)),
        "p1-worker-2": Unit("p1-worker-2", 1, UnitType.WORKER, tile_id(2, -1)),
    }
    return GameState(
        seed=seed,
        board=create_board(),
        players=players,
        units=units,
        current_player=seed % 2,
    )
