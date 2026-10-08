from scythe_sim.game.actions import Build, EndTurn, Move, Produce, Upgrade
from scythe_sim.game.board import RIVER_EDGES, tile_id
from scythe_sim.game.models import (
    BuildingType,
    Faction,
    Resource,
    UpgradeBenefit,
    UpgradeDiscount,
)
from scythe_sim.game.rules import legal_actions
from scythe_sim.game.state import new_game


def test_board_is_compact_hex_map() -> None:
    state = new_game()
    assert len(state.board) == 19
    assert state.board["0,0"].terrain.value == "factory"
    assert len(RIVER_EDGES) == 4


def test_seed_balances_seat_and_faction_assignment() -> None:
    setups = [
        (
            new_game(seed).current_player,
            new_game(seed).players[0].faction,
        )
        for seed in range(4)
    ]
    assert len(set(setups)) == 4


def test_initial_legal_actions_have_basic_choices() -> None:
    actions = legal_actions(new_game())
    kinds = {action.kind for action in actions}
    assert kinds == {"move", "produce", "end_turn"}


def test_river_blocks_rusviet_but_nordic_workers_can_swim() -> None:
    state = new_game()
    crossing = Move("p0-worker-2", (tile_id(-1, 1),))
    assert crossing not in legal_actions(state)
    state.players[0].faction = Faction.NORDIC
    assert crossing in legal_actions(state)


def test_enemy_unit_blocks_movement_without_combat() -> None:
    state = new_game()
    state.units["p1-character"].location = tile_id(-1, 0)
    blocked = Move("p0-character", (tile_id(-1, 0),))
    assert blocked not in legal_actions(state)


def test_move_path_cannot_return_to_its_start() -> None:
    state = new_game()
    state.players[0].upgrades.append(
        (UpgradeBenefit.MOVE, UpgradeDiscount.BUILD)
    )
    for action in legal_actions(state):
        if isinstance(action, Move):
            assert action.path[-1] != state.units[action.unit_id].location
            assert len(action.path) == len(set(action.path))


def test_non_rusviet_cannot_repeat_action_but_rusviet_can() -> None:
    state = new_game()
    state.players[0].previous_action = "produce"
    state.players[0].faction = Faction.NORDIC
    assert not any(isinstance(action, Produce) for action in legal_actions(state))
    state.players[0].faction = Faction.RUSVIET
    assert any(isinstance(action, Produce) for action in legal_actions(state))


def test_resource_costs_gate_upgrade_and_build() -> None:
    state = new_game()
    assert not any(isinstance(action, Upgrade) for action in legal_actions(state))
    assert not any(isinstance(action, Build) for action in legal_actions(state))
    home = state.board[tile_id(-2, 0)]
    home.resources[Resource.OIL] = 3
    home.resources[Resource.WOOD] = 3
    actions = legal_actions(state)
    assert Upgrade(UpgradeBenefit.MOVE, UpgradeDiscount.BUILD) in actions
    assert Build(BuildingType.MILL, tile_id(-2, 0)) in actions
    assert EndTurn() in actions


def test_completed_upgrades_and_buildings_are_exhausted() -> None:
    state = new_game()
    state.players[0].upgrades = [
        (UpgradeBenefit.MOVE, UpgradeDiscount.BUILD),
        (UpgradeBenefit.PRODUCE, UpgradeDiscount.UPGRADE),
    ]
    state.players[0].buildings = set(BuildingType)
    state.board[tile_id(-2, 0)].resources[Resource.OIL] = 10
    state.board[tile_id(-2, 0)].resources[Resource.WOOD] = 10
    actions = legal_actions(state)
    assert not any(isinstance(action, Upgrade) for action in actions)
    assert not any(isinstance(action, Build) for action in actions)
