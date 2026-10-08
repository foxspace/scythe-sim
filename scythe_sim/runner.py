"""Shared AI-v-AI loop for headless and visual play."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scythe_sim.agents.base import Agent, Decision
from scythe_sim.agents.heuristic_agent import HeuristicAgent
from scythe_sim.agents.random_agent import RandomAgent
from scythe_sim.game.engine import ActionResult, GameEngine
from scythe_sim.game.state import GameState, new_game


@dataclass
class GameSession:
    engine: GameEngine
    agents: dict[int, Agent]
    logger: Any | None = None
    last_decision: Decision | None = None
    last_result: ActionResult | None = None
    last_legal_actions: tuple = ()

    @property
    def state(self) -> GameState:
        return self.engine.state

    def step(self) -> ActionResult | None:
        if self.state.game_over:
            return None
        before = self.state.clone() if self.logger is not None else None
        legal = self.engine.legal_actions()
        player_id = self.state.current_player
        decision = self.agents[player_id].choose_action(
            self.engine.observation(), legal
        )
        result = self.engine.apply_action(decision.action)
        self.last_decision = decision
        self.last_result = result
        self.last_legal_actions = legal
        if self.logger is not None:
            assert before is not None
            self.logger.record_turn(
                before=before,
                after=self.state,
                legal_actions=legal,
                decision=decision,
                result=result,
                agent_name=self.agents[player_id].name,
            )
            if self.state.game_over:
                self.logger.finalize(self.state)
        return result

    def run(self) -> GameState:
        while not self.state.game_over:
            self.step()
        return self.state


def make_agents(matchup: str, seed: int) -> dict[int, Agent]:
    normalized = matchup.lower().replace("_", "-")
    choices: dict[str, tuple[str, str]] = {
        "random-random": ("random", "random"),
        "random-heuristic": ("random", "heuristic"),
        "heuristic-random": ("heuristic", "random"),
        "heuristic-heuristic": ("heuristic", "heuristic"),
    }
    if normalized not in choices:
        raise ValueError(f"Unknown matchup: {matchup}")
    names = choices[normalized]

    def create(kind: str, player_id: int) -> Agent:
        if kind == "random":
            return RandomAgent(seed=seed * 101 + player_id, name=f"P{player_id} Random")
        return HeuristicAgent(name=f"P{player_id} Heuristic")

    return {player_id: create(kind, player_id) for player_id, kind in enumerate(names)}


def create_session(
    matchup: str = "random-heuristic",
    seed: int = 0,
    logger: Any | None = None,
) -> GameSession:
    return GameSession(GameEngine(new_game(seed)), make_agents(matchup, seed), logger)


def run_game(
    matchup: str = "random-heuristic",
    seed: int = 0,
    logger: Any | None = None,
) -> GameState:
    return create_session(matchup, seed, logger).run()
