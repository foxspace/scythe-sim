"""Rebuild a game from its action log and verify every state hash."""

from __future__ import annotations

import json
from pathlib import Path

from scythe_sim.game.actions import action_from_dict
from scythe_sim.game.engine import GameEngine
from scythe_sim.game.serialization import state_from_dict, state_hash
from scythe_sim.game.state import GameState


class ReplayError(ValueError):
    pass


def _read_record(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".jsonl":
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) != 1:
            raise ReplayError("Choose a single-game JSON log for replay")
        return json.loads(lines[0])
    return json.loads(text)


def replay_game(source: str | Path | dict) -> GameState:
    record = source if isinstance(source, dict) else _read_record(source)
    state = state_from_dict(record["initial_state"])
    if state_hash(state) != record["initial_hash"]:
        raise ReplayError("Initial state hash does not match")
    engine = GameEngine(state)
    for turn in record["turns"]:
        if state_hash(state) != turn["before_hash"]:
            raise ReplayError(f"Before hash mismatch on turn {turn['turn']}")
        engine.apply_action(action_from_dict(turn["action"]))
        if state_hash(state) != turn["after_hash"]:
            raise ReplayError(f"After hash mismatch on turn {turn['turn']}")
    summary = record.get("summary")
    if summary and state_hash(state) != summary["final_hash"]:
        raise ReplayError("Final hash does not match")
    return state
