"""Seeded random baseline with balanced action-type sampling."""

from __future__ import annotations

import random

from scythe_sim.agents.base import Agent, Decision
from scythe_sim.game.actions import Action
from scythe_sim.game.state import GameState


class RandomAgent(Agent):
    def __init__(self, seed: int = 0, name: str = "RandomAgent"):
        self.name = name
        self._seed = seed

    def choose_action(
        self, game_state: GameState, legal_actions: tuple[Action, ...]
    ) -> Decision:
        if not legal_actions:
            raise ValueError("No legal actions were supplied")
        # Deriving the choice from saved state makes mid-game save/load
        # reproducible without serializing a hidden agent RNG object.
        decision_seed = (
            self._seed * 1_000_003
            + game_state.seed * 9_973
            + game_state.turn_number * 101
            + game_state.current_player
        )
        random_source = random.Random(decision_seed)
        active_actions = tuple(
            action for action in legal_actions if action.kind != "end_turn"
        ) or legal_actions
        action_kinds = sorted({action.kind for action in active_actions})
        selected_kind = random_source.choice(action_kinds)
        choices = [
            action for action in active_actions if action.kind == selected_kind
        ]
        index = random_source.randrange(len(choices))
        action = choices[index]
        return Decision(
            action=action,
            reason=(
                f"Random action type '{selected_kind}', "
                f"choice {index + 1} of {len(choices)}"
            ),
            scores={repr(candidate): 0.0 for candidate in legal_actions},
        )
