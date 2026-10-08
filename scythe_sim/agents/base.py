"""The common interface used by every strategy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from scythe_sim.game.actions import Action
from scythe_sim.game.state import GameState


@dataclass(frozen=True)
class Decision:
    action: Action
    reason: str
    scores: dict[str, float] = field(default_factory=dict)
    breakdown: dict[str, float] = field(default_factory=dict)


class Agent(ABC):
    name: str

    @abstractmethod
    def choose_action(
        self, game_state: GameState, legal_actions: tuple[Action, ...]
    ) -> Decision:
        """Choose one of the supplied actions without mutating state."""
