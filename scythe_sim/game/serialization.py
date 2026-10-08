"""Versioned JSON conversion for save files and reproducible hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scythe_sim.game.models import (
    BuildingType,
    Faction,
    PlayerState,
    Resource,
    Terrain,
    Tile,
    Unit,
    UnitType,
    UpgradeBenefit,
    UpgradeDiscount,
)
from scythe_sim.game.state import GameState

STATE_SCHEMA_VERSION = 1


def state_to_dict(state: GameState) -> dict:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "seed": state.seed,
        "current_player": state.current_player,
        "turn_number": state.turn_number,
        "game_over": state.game_over,
        "winner": state.winner,
        "final_scores": {str(key): value for key, value in state.final_scores.items()},
        "end_reason": state.end_reason,
        "board": {
            tile_id: {
                "q": tile.q,
                "r": tile.r,
                "terrain": tile.terrain.value,
                "resources": {
                    resource.value: tile.resources[resource] for resource in Resource
                },
                "building": tile.building.value if tile.building else None,
                "building_owner": tile.building_owner,
            }
            for tile_id, tile in sorted(state.board.items())
        },
        "players": {
            str(player_id): {
                "faction": player.faction.value,
                "upgrades": [
                    [benefit.value, discount.value]
                    for benefit, discount in player.upgrades
                ],
                "buildings": sorted(building.value for building in player.buildings),
                "stars": sorted(player.stars),
                "previous_action": player.previous_action,
            }
            for player_id, player in sorted(state.players.items())
        },
        "units": {
            unit_id: {
                "owner": unit.owner,
                "kind": unit.kind.value,
                "location": unit.location,
            }
            for unit_id, unit in sorted(state.units.items())
        },
    }


def state_from_dict(data: dict) -> GameState:
    if data.get("schema_version") != STATE_SCHEMA_VERSION:
        raise ValueError("Unsupported state schema version")
    board = {
        tile_id: Tile(
            id=tile_id,
            q=tile["q"],
            r=tile["r"],
            terrain=Terrain(tile["terrain"]),
            resources={
                Resource(name): amount for name, amount in tile["resources"].items()
            },
            building=BuildingType(tile["building"]) if tile["building"] else None,
            building_owner=tile["building_owner"],
        )
        for tile_id, tile in data["board"].items()
    }
    players = {
        int(player_id): PlayerState(
            id=int(player_id),
            faction=Faction(player["faction"]),
            upgrades=[
                (UpgradeBenefit(benefit), UpgradeDiscount(discount))
                for benefit, discount in player["upgrades"]
            ],
            buildings={BuildingType(value) for value in player["buildings"]},
            stars=set(player["stars"]),
            previous_action=player["previous_action"],
        )
        for player_id, player in data["players"].items()
    }
    units = {
        unit_id: Unit(
            id=unit_id,
            owner=unit["owner"],
            kind=UnitType(unit["kind"]),
            location=unit["location"],
        )
        for unit_id, unit in data["units"].items()
    }
    return GameState(
        seed=data["seed"],
        board=board,
        players=players,
        units=units,
        current_player=data["current_player"],
        turn_number=data["turn_number"],
        game_over=data["game_over"],
        winner=data["winner"],
        final_scores={int(key): value for key, value in data["final_scores"].items()},
        end_reason=data["end_reason"],
    )


def state_hash(state: GameState) -> str:
    encoded = json.dumps(
        state_to_dict(state), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def save_state(state: GameState, path: str | Path) -> None:
    Path(path).write_text(json.dumps(state_to_dict(state), indent=2), encoding="utf-8")


def load_state(path: str | Path) -> GameState:
    return state_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
