import json

import pytest

from scythe_sim.agents.random_agent import RandomAgent
from scythe_sim.game.engine import GameEngine
from scythe_sim.game.serialization import (
    load_state,
    save_state,
    state_hash,
    state_to_dict,
)
from scythe_sim.game.state import new_game
from scythe_sim.logging import GameLogger, replay_game
from scythe_sim.logging.replay import ReplayError
from scythe_sim.runner import create_session


def test_state_json_round_trip(tmp_path) -> None:
    state = new_game(seed=123)
    path = tmp_path / "state.json"
    save_state(state, path)
    loaded = load_state(path)
    assert state_to_dict(loaded) == state_to_dict(state)
    assert state_hash(loaded) == state_hash(state)


def test_loaded_state_reproduces_next_random_decision(tmp_path) -> None:
    state = new_game(seed=123)
    path = tmp_path / "state.json"
    save_state(state, path)
    loaded = load_state(path)
    agent = RandomAgent(seed=77)
    first = agent.choose_action(state, GameEngine(state).legal_actions())
    second = agent.choose_action(loaded, GameEngine(loaded).legal_actions())
    assert first.action == second.action


def test_log_contains_research_fields_and_replays(tmp_path) -> None:
    path = tmp_path / "game.json"
    session = create_session("random-heuristic", seed=9)
    logger = GameLogger(
        path,
        session.state,
        "random-heuristic",
        {key: agent.name for key, agent in session.agents.items()},
    )
    session.logger = logger
    final_state = session.run()

    record = json.loads(path.read_text())
    assert record["summary"]["winner"] == final_state.winner
    assert record["turns"]
    first_turn = record["turns"][0]
    assert {
        "legal_actions",
        "action",
        "reason",
        "scores",
        "before",
        "after",
        "after_hash",
    } <= first_turn.keys()
    replayed = replay_game(path)
    assert state_hash(replayed) == state_hash(final_state)

    tampered = json.loads(json.dumps(record))
    tampered["turns"][0]["after_hash"] = "0" * 64
    with pytest.raises(ReplayError, match="After hash mismatch"):
        replay_game(tampered)


def test_csv_export(tmp_path) -> None:
    session = create_session("heuristic-heuristic", seed=2)
    logger = GameLogger(
        tmp_path / "game.json",
        session.state,
        "heuristic-heuristic",
        {key: agent.name for key, agent in session.agents.items()},
    )
    session.logger = logger
    session.run()
    game_csv, action_csv = logger.export_csv(tmp_path / "summary")
    assert game_csv.exists()
    assert action_csv.exists()
    assert "winner" in game_csv.read_text().splitlines()[0]
    assert "reason" in action_csv.read_text().splitlines()[0]
