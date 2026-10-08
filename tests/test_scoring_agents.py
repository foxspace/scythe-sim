from scythe_sim.agents.heuristic_agent import HeuristicAgent
from scythe_sim.agents.random_agent import RandomAgent
from scythe_sim.game.actions import EndTurn
from scythe_sim.game.engine import GameEngine
from scythe_sim.game.models import BuildingType, Resource
from scythe_sim.game.rules import controlled_territories
from scythe_sim.game.scoring import finish_game, score_player
from scythe_sim.game.serialization import state_hash
from scythe_sim.game.state import new_game
from scythe_sim.runner import run_game


def test_basic_scoring_rewards_development() -> None:
    state = new_game()
    baseline = score_player(state, 0)
    state.players[0].buildings.add(BuildingType.MONUMENT)
    state.players[0].stars.add("builder")
    state.board["-2,0"].resources[Resource.FOOD] = 2
    assert score_player(state, 0) == baseline + 11
    assert len(controlled_territories(state, 0)) == 2


def test_score_tie_break_order_is_deterministic() -> None:
    state = new_game()
    finish_game(state, "test")
    assert state.winner == 0

    state = new_game()
    state.board["2,0"].resources[Resource.FOOD] = 1
    finish_game(state, "test")
    assert state.final_scores[0] == state.final_scores[1]
    assert state.winner == 1

    state = new_game()
    state.units["p0-character"].location = "-1,-1"
    state.board["2,0"].resources[Resource.FOOD] = 4
    finish_game(state, "test")
    assert state.final_scores[0] == state.final_scores[1]
    assert state.winner == 0

    state = new_game()
    state.players[0].stars.add("test-star")
    state.board["2,0"].resources[Resource.FOOD] = 10
    finish_game(state, "test")
    assert state.final_scores[0] == state.final_scores[1]
    assert state.winner == 0


def test_agents_do_not_mutate_supplied_state() -> None:
    state = new_game()
    legal = GameEngine(state).legal_actions()
    before = state_hash(state)
    decision = HeuristicAgent().choose_action(state, legal)
    assert decision.action in legal
    assert "Highest heuristic value" in decision.reason
    assert state_hash(state) == before


def test_seeded_random_agent_is_reproducible() -> None:
    state = new_game()
    legal = GameEngine(state).legal_actions()
    first = RandomAgent(22).choose_action(state, legal)
    second = RandomAgent(22).choose_action(state, legal)
    assert first.action == second.action


def test_random_agent_avoids_passing_when_other_actions_exist() -> None:
    state = new_game()
    legal = GameEngine(state).legal_actions()
    for seed in range(20):
        decision = RandomAgent(seed).choose_action(state, legal)
        assert not isinstance(decision.action, EndTurn)


def test_same_seed_produces_identical_complete_game() -> None:
    first = run_game("random-random", 17)
    second = run_game("random-random", 17)
    assert state_hash(first) == state_hash(second)
    assert first.final_scores == second.final_scores


def test_heuristic_prefers_doing_something_over_passing() -> None:
    state = new_game()
    decision = HeuristicAgent().choose_action(
        state, (EndTurn(),) + GameEngine(state).legal_actions()
    )
    assert not isinstance(decision.action, EndTurn)
