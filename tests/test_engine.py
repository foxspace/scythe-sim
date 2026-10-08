import pytest

from scythe_sim.game.actions import Build, EndTurn, Move, Produce, Upgrade
from scythe_sim.game.board import tile_id
from scythe_sim.game.engine import GameEngine, IllegalActionError
from scythe_sim.game.models import (
    BuildingType,
    Resource,
    Unit,
    UnitType,
    UpgradeBenefit,
    UpgradeDiscount,
)
from scythe_sim.game.rules import MAX_TURNS, worker_count
from scythe_sim.game.state import new_game


def test_move_changes_location_and_player() -> None:
    engine = GameEngine(new_game())
    action = next(
        action
        for action in engine.legal_actions()
        if isinstance(action, Move) and action.unit_id == "p0-character"
    )
    destination = action.path[-1]
    engine.apply_action(action)
    assert engine.state.units["p0-character"].location == destination
    assert engine.state.current_player == 1
    assert engine.state.turn_number == 2


def test_production_creates_local_resource_and_worker() -> None:
    state = new_game()
    engine = GameEngine(state)
    engine.apply_action(Produce((tile_id(-2, 1),)))
    assert state.board[tile_id(-2, 1)].resources[Resource.WOOD] == 1

    state.current_player = 0
    state.players[0].previous_action = None
    before = worker_count(state, 0)
    engine.apply_action(Produce((tile_id(-2, 0),)))
    assert worker_count(state, 0) == before + 1


def test_village_production_respects_worker_cap() -> None:
    state = new_game()
    for number in range(3, 6):
        unit_id = f"p0-worker-{number}"
        state.units[unit_id] = Unit(
            unit_id, 0, UnitType.WORKER, tile_id(-2, 0)
        )
    assert worker_count(state, 0) == 5
    GameEngine(state).apply_action(Produce((tile_id(-2, 0),)))
    assert worker_count(state, 0) == 5


def test_upgrade_spends_oil_and_changes_costs() -> None:
    state = new_game()
    home = state.board[tile_id(-2, 0)]
    home.resources[Resource.OIL] = 3
    engine = GameEngine(state)
    engine.apply_action(Upgrade(UpgradeBenefit.MOVE, UpgradeDiscount.BUILD))
    assert home.resources[Resource.OIL] == 0
    assert state.players[0].move_range == 2
    assert state.players[0].build_cost == 2


def test_build_and_mill_bonus_production() -> None:
    state = new_game()
    forest = state.board[tile_id(-2, 1)]
    forest.resources[Resource.WOOD] = 3
    engine = GameEngine(state)
    engine.apply_action(Build(BuildingType.MILL, tile_id(-2, 1)))
    assert forest.building == BuildingType.MILL
    assert forest.resources[Resource.WOOD] == 0

    state.current_player = 0
    state.players[0].previous_action = None
    engine.apply_action(Produce((tile_id(-2, 1),)))
    assert forest.resources[Resource.WOOD] == 2


def test_mine_creates_private_factory_link() -> None:
    state = new_game()
    home = state.board[tile_id(-2, 0)]
    home.resources[Resource.WOOD] = 3
    engine = GameEngine(state)
    engine.apply_action(Build(BuildingType.MINE, tile_id(-2, 0)))
    state.current_player = 0
    state.players[0].previous_action = None
    assert Move("p0-character", (tile_id(0, 0),)) in engine.legal_actions()


def test_invalid_action_is_rejected_without_mutation() -> None:
    state = new_game()
    engine = GameEngine(state)
    with pytest.raises(IllegalActionError):
        engine.apply_action(Move("p0-character", (tile_id(2, 0),)))
    assert state.units["p0-character"].location == tile_id(-2, 0)


def test_star_and_turn_limit_end_games() -> None:
    state = new_game()
    state.players[0].stars = {"a", "b", "c"}
    state.board[tile_id(-2, 0)].resources[Resource.FOOD] = 8
    GameEngine(state).apply_action(EndTurn())
    assert state.game_over
    assert state.end_reason == "stars"
    assert state.winner in (0, 1)

    state = new_game()
    state.turn_number = MAX_TURNS
    GameEngine(state).apply_action(EndTurn())
    assert state.game_over
    assert state.end_reason == "turn_limit"
