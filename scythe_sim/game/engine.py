"""Validated state transitions. Agents never mutate state directly."""

from __future__ import annotations

from dataclasses import dataclass

from scythe_sim.game.actions import Action, Build, EndTurn, Move, Produce, Upgrade
from scythe_sim.game.models import BuildingType, Resource, TERRAIN_RESOURCE, Unit, UnitType
from scythe_sim.game.rules import (
    MAX_TURNS,
    MAX_WORKERS,
    STARS_TO_END,
    controlled_territories,
    legal_actions,
    units_at,
    worker_count,
)
from scythe_sim.game.scoring import finish_game, update_stars
from scythe_sim.game.state import GameState


class IllegalActionError(ValueError):
    """Raised when an action is not in the engine-generated legal set."""


@dataclass(frozen=True)
class ActionResult:
    player_id: int
    action: Action
    message: str


class GameEngine:
    def __init__(self, state: GameState):
        self.state = state

    def legal_actions(self) -> tuple[Action, ...]:
        return legal_actions(self.state)

    def observation(self) -> GameState:
        """Return a defensive copy safe for an agent to inspect."""

        return self.state.clone()

    def _spend(self, player_id: int, resource: Resource, amount: int) -> None:
        remaining = amount
        for territory in sorted(controlled_territories(self.state, player_id)):
            available = self.state.board[territory].resources[resource]
            spent = min(available, remaining)
            self.state.board[territory].resources[resource] -= spent
            remaining -= spent
            if remaining == 0:
                return
        raise RuntimeError("Legal action did not have enough controlled resources")

    def _produce_tile(self, player_id: int, territory: str, producers: int) -> str:
        tile = self.state.board[territory]
        if tile.terrain.value == "village":
            available = MAX_WORKERS - worker_count(self.state, player_id)
            created = min(available, producers)
            for _ in range(created):
                next_number = (
                    max(
                        (
                            int(unit.id.rsplit("-", 1)[-1])
                            for unit in self.state.units.values()
                            if unit.owner == player_id and unit.kind == UnitType.WORKER
                        ),
                        default=0,
                    )
                    + 1
                )
                unit_id = f"p{player_id}-worker-{next_number}"
                self.state.units[unit_id] = Unit(
                    unit_id, player_id, UnitType.WORKER, territory
                )
            return f"{created} worker(s)"
        resource = TERRAIN_RESOURCE[tile.terrain]
        if resource is None:
            return "nothing"
        tile.resources[resource] += producers
        return f"{producers} {resource.value}"

    def _apply_produce(self, player_id: int, action: Produce) -> str:
        production: dict[str, int] = {}
        for territory in action.territories:
            production[territory] = sum(
                unit.owner == player_id and unit.kind == UnitType.WORKER
                for unit in units_at(self.state, territory)
            )

        # The Mill produces as one extra worker and may be a bonus territory.
        for tile in self.state.board.values():
            if (
                tile.building == BuildingType.MILL
                and tile.building_owner == player_id
                and tile.id in controlled_territories(self.state, player_id)
            ):
                production[tile.id] = production.get(tile.id, 0) + 1

        details = [
            f"{territory}: {self._produce_tile(player_id, territory, producers)}"
            for territory, producers in sorted(production.items())
            if producers > 0
        ]
        return "Produced " + ", ".join(details)

    def apply_action(self, action: Action) -> ActionResult:
        if self.state.game_over:
            raise IllegalActionError("The game is already over")
        available = self.legal_actions()
        if action not in available:
            raise IllegalActionError(f"Illegal action: {action!r}")

        player_id = self.state.current_player
        player = self.state.players[player_id]

        if isinstance(action, Move):
            unit = self.state.units[action.unit_id]
            origin = unit.location
            unit.location = action.path[-1]
            message = f"Moved {unit.id} from {origin} to {unit.location}"
        elif isinstance(action, Produce):
            message = self._apply_produce(player_id, action)
        elif isinstance(action, Upgrade):
            cost = player.upgrade_cost
            self._spend(player_id, Resource.OIL, cost)
            player.upgrades.append((action.benefit, action.discount))
            message = (
                f"Upgraded {action.benefit.value}; "
                f"discounted {action.discount.value} for {cost} oil"
            )
        elif isinstance(action, Build):
            cost = player.build_cost
            self._spend(player_id, Resource.WOOD, cost)
            tile = self.state.board[action.territory]
            tile.building = action.building
            tile.building_owner = player_id
            player.buildings.add(action.building)
            message = f"Built {action.building.value} for {cost} wood"
        elif isinstance(action, EndTurn):
            message = "Passed"
        else:  # pragma: no cover - exhaustive type guard
            raise TypeError(action)

        player.previous_action = action.kind
        update_stars(self.state)
        if len(player.stars) >= STARS_TO_END:
            finish_game(self.state, "stars")
        elif self.state.turn_number >= MAX_TURNS:
            finish_game(self.state, "turn_limit")
        else:
            self.state.current_player = 1 - player_id
            self.state.turn_number += 1
        return ActionResult(player_id, action, message)
