"""Legal-action generation and read-only rule queries."""

from __future__ import annotations

from itertools import combinations

from scythe_sim.game.actions import Action, Build, EndTurn, Move, Produce, Upgrade
from scythe_sim.game.board import has_river, neighbors, tile_id
from scythe_sim.game.models import (
    BuildingType,
    Faction,
    Resource,
    Unit,
    UnitType,
    UpgradeBenefit,
    UpgradeDiscount,
)
from scythe_sim.game.state import GameState

MAX_WORKERS = 5
MAX_TURNS = 120
STARS_TO_END = 4


def units_at(state: GameState, territory: str) -> list[Unit]:
    return [unit for unit in state.units.values() if unit.location == territory]


def controlled_territories(state: GameState, player_id: int) -> set[str]:
    controlled: set[str] = set()
    for territory, tile in state.board.items():
        occupants = units_at(state, territory)
        owners = {unit.owner for unit in occupants}
        if player_id in owners:
            controlled.add(territory)
        elif not occupants and tile.building_owner == player_id:
            controlled.add(territory)
    return controlled


def controlled_resource_count(
    state: GameState, player_id: int, resource: Resource | None = None
) -> int:
    territories = controlled_territories(state, player_id)
    if resource is not None:
        return sum(state.board[tile].resources[resource] for tile in territories)
    return sum(sum(state.board[tile].resources.values()) for tile in territories)


def worker_count(state: GameState, player_id: int) -> int:
    return sum(
        unit.owner == player_id and unit.kind == UnitType.WORKER
        for unit in state.units.values()
    )


def action_type_allowed(state: GameState, kind: str) -> bool:
    player = state.players[state.current_player]
    return (
        kind == "end_turn"
        or player.faction == Faction.RUSVIET
        or player.previous_action != kind
    )


def _enemy_present(state: GameState, territory: str, player_id: int) -> bool:
    return any(unit.owner != player_id for unit in units_at(state, territory))


def _movement_neighbors(state: GameState, unit: Unit, location: str) -> list[str]:
    result: set[str] = set()
    for destination in neighbors(state.board, location):
        river = has_river(location, destination)
        can_swim = (
            state.players[unit.owner].faction == Faction.NORDIC
            and unit.kind == UnitType.WORKER
        )
        if not river or can_swim:
            result.add(destination)

    # A Mine is a private tunnel to the central Factory.
    mine_tiles = [
        tile.id
        for tile in state.board.values()
        if tile.building == BuildingType.MINE and tile.building_owner == unit.owner
    ]
    factory = tile_id(0, 0)
    if location == factory:
        result.update(mine_tiles)
    elif location in mine_tiles:
        result.add(factory)
    return sorted(result)


def _move_actions(state: GameState) -> list[Move]:
    player_id = state.current_player
    move_range = state.players[player_id].move_range
    actions: list[Move] = []

    def visit(
        unit: Unit,
        current: str,
        path: tuple[str, ...],
        visited: frozenset[str],
    ) -> None:
        if path:
            actions.append(Move(unit.id, path))
        if len(path) == move_range:
            return
        for destination in _movement_neighbors(state, unit, current):
            if destination in visited or _enemy_present(
                state, destination, player_id
            ):
                continue
            visit(
                unit,
                destination,
                path + (destination,),
                visited | {destination},
            )

    for unit in sorted(state.units.values(), key=lambda value: value.id):
        if unit.owner == player_id:
            visit(unit, unit.location, (), frozenset({unit.location}))
    return actions


def _produce_actions(state: GameState) -> list[Produce]:
    player_id = state.current_player
    eligible = sorted(
        territory
        for territory in controlled_territories(state, player_id)
        if any(
            unit.owner == player_id and unit.kind == UnitType.WORKER
            for unit in units_at(state, territory)
        )
    )
    limit = min(state.players[player_id].produce_limit, len(eligible))
    return [
        Produce(selection)
        for size in range(1, limit + 1)
        for selection in combinations(eligible, size)
    ]


def _upgrade_actions(state: GameState) -> list[Upgrade]:
    player = state.players[state.current_player]
    if controlled_resource_count(state, player.id, Resource.OIL) < player.upgrade_cost:
        return []
    used_benefits = {benefit for benefit, _ in player.upgrades}
    used_discounts = {discount for _, discount in player.upgrades}
    return [
        Upgrade(benefit, discount)
        for benefit in UpgradeBenefit
        for discount in UpgradeDiscount
        if benefit not in used_benefits and discount not in used_discounts
    ]


def _build_actions(state: GameState) -> list[Build]:
    player = state.players[state.current_player]
    if controlled_resource_count(state, player.id, Resource.WOOD) < player.build_cost:
        return []
    available = [building for building in BuildingType if building not in player.buildings]
    territories = sorted(
        territory
        for territory in controlled_territories(state, player.id)
        if state.board[territory].building is None
        and any(
            unit.owner == player.id and unit.kind == UnitType.WORKER
            for unit in units_at(state, territory)
        )
    )
    return [
        Build(building, territory)
        for building in available
        for territory in territories
    ]


def legal_actions(state: GameState) -> tuple[Action, ...]:
    if state.game_over:
        return ()
    actions: list[Action] = []
    generators = (
        ("move", _move_actions),
        ("produce", _produce_actions),
        ("upgrade", _upgrade_actions),
        ("build", _build_actions),
    )
    for kind, generator in generators:
        if action_type_allowed(state, kind):
            actions.extend(generator(state))
    actions.append(EndTurn())
    return tuple(sorted(actions, key=repr))
