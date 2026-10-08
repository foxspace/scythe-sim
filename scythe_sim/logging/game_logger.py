"""Versioned, replayable game and action logging."""

from __future__ import annotations

import json
from pathlib import Path

from scythe_sim.agents.base import Decision
from scythe_sim.game.actions import Action, action_to_dict
from scythe_sim.game.engine import ActionResult
from scythe_sim.game.rules import (
    controlled_resource_count,
    controlled_territories,
    worker_count,
)
from scythe_sim.game.serialization import state_hash, state_to_dict
from scythe_sim.game.state import GameState

LOG_SCHEMA_VERSION = 1


def state_metrics(state: GameState) -> dict:
    return {
        str(player_id): {
            "score": state.final_scores.get(player_id),
            "resources": controlled_resource_count(state, player_id),
            "territories": len(controlled_territories(state, player_id)),
            "workers": worker_count(state, player_id),
            "stars": len(player.stars),
            "upgrades": len(player.upgrades),
            "buildings": len(player.buildings),
            "positions": {
                unit.id: unit.location
                for unit in sorted(state.units.values(), key=lambda item: item.id)
                if unit.owner == player_id
            },
        }
        for player_id, player in state.players.items()
    }


class GameLogger:
    def __init__(
        self,
        path: str | Path,
        initial_state: GameState,
        matchup: str,
        agent_names: dict[int, str],
    ):
        self.path = Path(path)
        self.record = {
            "schema_version": LOG_SCHEMA_VERSION,
            "matchup": matchup,
            "seed": initial_state.seed,
            "agents": {str(key): value for key, value in agent_names.items()},
            "initial_state": state_to_dict(initial_state),
            "initial_hash": state_hash(initial_state),
            "turns": [],
            "summary": None,
        }

    def record_turn(
        self,
        *,
        before: GameState,
        after: GameState,
        legal_actions: tuple[Action, ...],
        decision: Decision,
        result: ActionResult,
        agent_name: str,
    ) -> None:
        self.record["turns"].append(
            {
                "turn": before.turn_number,
                "player": result.player_id,
                "agent": agent_name,
                "legal_actions": [action_to_dict(action) for action in legal_actions],
                "action": action_to_dict(decision.action),
                "reason": decision.reason,
                "scores": decision.scores,
                "breakdown": decision.breakdown,
                "result": result.message,
                "before": state_metrics(before),
                "after": state_metrics(after),
                "before_hash": state_hash(before),
                "after_hash": state_hash(after),
            }
        )

    def finalize(self, state: GameState) -> None:
        self.record["summary"] = {
            "winner": state.winner,
            "final_scores": {
                str(key): value for key, value in state.final_scores.items()
            },
            "game_length": state.turn_number,
            "end_reason": state.end_reason,
            "stars": {
                str(key): sorted(player.stars)
                for key, player in state.players.items()
            },
            "final_hash": state_hash(state),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.suffix == ".jsonl":
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(self.record, sort_keys=True) + "\n")
        else:
            self.path.write_text(
                json.dumps(self.record, indent=2, sort_keys=True),
                encoding="utf-8",
            )

    def export_csv(self, prefix: str | Path) -> tuple[Path, Path]:
        """Write game- and action-level tables for quick pandas analysis."""

        import pandas as pd

        if self.record["summary"] is None:
            raise ValueError("The game must finish before CSV export")
        prefix = Path(prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        game_path = prefix.with_name(prefix.name + "_games.csv")
        action_path = prefix.with_name(prefix.name + "_actions.csv")
        summary = self.record["summary"]
        pd.DataFrame(
            [
                {
                    "seed": self.record["seed"],
                    "matchup": self.record["matchup"],
                    "winner": summary["winner"],
                    "game_length": summary["game_length"],
                    "end_reason": summary["end_reason"],
                    "score_0": summary["final_scores"]["0"],
                    "score_1": summary["final_scores"]["1"],
                }
            ]
        ).to_csv(game_path, index=False)
        pd.DataFrame(
            [
                {
                    "seed": self.record["seed"],
                    "turn": turn["turn"],
                    "player": turn["player"],
                    "agent": turn["agent"],
                    "action": turn["action"]["type"],
                    "reason": turn["reason"],
                    "result": turn["result"],
                    "resources_after": turn["after"][str(turn["player"])]["resources"],
                    "territories_after": turn["after"][str(turn["player"])][
                        "territories"
                    ],
                }
                for turn in self.record["turns"]
            ]
        ).to_csv(action_path, index=False)
        return game_path, action_path
