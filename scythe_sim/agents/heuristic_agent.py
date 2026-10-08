"""Explainable one-step heuristic baseline."""

from __future__ import annotations

from dataclasses import dataclass

from scythe_sim.agents.base import Agent, Decision
from scythe_sim.game.actions import Action, EndTurn, action_sort_key
from scythe_sim.game.board import parse_tile_id
from scythe_sim.game.engine import GameEngine
from scythe_sim.game.models import Terrain, UnitType
from scythe_sim.game.rules import (
    controlled_resource_count,
    controlled_territories,
    worker_count,
)
from scythe_sim.game.state import GameState


@dataclass(frozen=True)
class HeuristicWeights:
    resource_weight: float = 1.0
    territory_weight: float = 2.5
    upgrade_weight: float = 4.0
    building_weight: float = 7.0
    worker_weight: float = 2.0
    star_weight: float = 7.0
    mobility_weight: float = 0.4
    production_position_weight: float = 1.0
    pass_penalty: float = -6.0


def _hex_distance_from_center(location: str) -> int:
    q, r = parse_tile_id(location)
    return (abs(q) + abs(r) + abs(q + r)) // 2


def _features(state: GameState, player_id: int) -> dict[str, float]:
    player = state.players[player_id]
    units = [unit for unit in state.units.values() if unit.owner == player_id]
    closeness = -sum(_hex_distance_from_center(unit.location) for unit in units)
    workers = [unit for unit in units if unit.kind == UnitType.WORKER]
    production_position = 0.0
    for worker in workers:
        terrain = state.board[worker.location].terrain
        if terrain == Terrain.FOREST and len(player.buildings) < 3:
            production_position += 3.0
        elif terrain == Terrain.TUNDRA and len(player.upgrades) < 2:
            production_position += 3.0
        elif terrain == Terrain.VILLAGE and len(workers) < 5:
            production_position += 2.0
        elif terrain not in (Terrain.FACTORY, Terrain.VILLAGE):
            production_position += 0.5
    return {
        "resource": float(controlled_resource_count(state, player_id)),
        "territory": float(len(controlled_territories(state, player_id))),
        "upgrade": float(len(player.upgrades)),
        "building": float(len(player.buildings)),
        "worker": float(worker_count(state, player_id)),
        "star": float(len(player.stars)),
        "mobility": float(closeness),
        "production_position": production_position,
    }


class HeuristicAgent(Agent):
    """One-step baseline that scores only the acting player's immediate gains."""

    def __init__(
        self,
        weights: HeuristicWeights | None = None,
        name: str = "HeuristicAgent",
    ):
        self.name = name
        self.weights = weights or HeuristicWeights()

    def _score(
        self, state: GameState, action: Action, player_id: int
    ) -> tuple[float, dict[str, float]]:
        before = _features(state, player_id)
        simulated = state.clone()
        GameEngine(simulated).apply_action(action)
        after = _features(simulated, player_id)
        weighted = {
            "resources": (after["resource"] - before["resource"])
            * self.weights.resource_weight,
            "territory": (after["territory"] - before["territory"])
            * self.weights.territory_weight,
            "upgrades": (after["upgrade"] - before["upgrade"])
            * self.weights.upgrade_weight,
            "buildings": (after["building"] - before["building"])
            * self.weights.building_weight,
            "workers": (after["worker"] - before["worker"])
            * self.weights.worker_weight,
            "stars": (after["star"] - before["star"]) * self.weights.star_weight,
            "mobility": (after["mobility"] - before["mobility"])
            * self.weights.mobility_weight,
            "production_position": (
                after["production_position"] - before["production_position"]
            )
            * self.weights.production_position_weight,
        }
        if isinstance(action, EndTurn):
            weighted["pass"] = self.weights.pass_penalty
        return sum(weighted.values()), weighted

    def choose_action(
        self, game_state: GameState, legal_actions: tuple[Action, ...]
    ) -> Decision:
        if not legal_actions:
            raise ValueError("No legal actions were supplied")
        player_id = game_state.current_player
        evaluations = [
            (self._score(game_state, action, player_id), action)
            for action in legal_actions
        ]
        evaluations.sort(key=lambda item: action_sort_key(item[1]))
        (best_score, breakdown), selected = max(
            evaluations, key=lambda item: item[0][0]
        )
        scores = {
            repr(action): round(score, 3)
            for (score, _), action in evaluations
        }
        useful_parts = [
            f"{name}={value:+.1f}"
            for name, value in breakdown.items()
            if value
        ]
        detail = ", ".join(useful_parts) or "no immediate feature change"
        return Decision(
            action=selected,
            reason=f"Highest heuristic value = {best_score:.1f} ({detail})",
            scores=scores,
            breakdown={key: round(value, 3) for key, value in breakdown.items()},
        )
