"""Immutable commands selected by people or AI agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from scythe_sim.game.models import BuildingType, UpgradeBenefit, UpgradeDiscount


@dataclass(frozen=True)
class Move:
    unit_id: str
    path: tuple[str, ...]
    kind: str = "move"


@dataclass(frozen=True)
class Produce:
    territories: tuple[str, ...]
    kind: str = "produce"


@dataclass(frozen=True)
class Upgrade:
    benefit: UpgradeBenefit
    discount: UpgradeDiscount
    kind: str = "upgrade"


@dataclass(frozen=True)
class Build:
    building: BuildingType
    territory: str
    kind: str = "build"


@dataclass(frozen=True)
class EndTurn:
    kind: str = "end_turn"


Action: TypeAlias = Move | Produce | Upgrade | Build | EndTurn


def action_sort_key(action: Action) -> str:
    return repr(action)


def action_to_dict(action: Action) -> dict:
    if isinstance(action, Move):
        return {"type": action.kind, "unit_id": action.unit_id, "path": list(action.path)}
    if isinstance(action, Produce):
        return {"type": action.kind, "territories": list(action.territories)}
    if isinstance(action, Upgrade):
        return {
            "type": action.kind,
            "benefit": action.benefit.value,
            "discount": action.discount.value,
        }
    if isinstance(action, Build):
        return {
            "type": action.kind,
            "building": action.building.value,
            "territory": action.territory,
        }
    return {"type": action.kind}


def action_from_dict(data: dict) -> Action:
    action_type = data["type"]
    if action_type == "move":
        return Move(data["unit_id"], tuple(data["path"]))
    if action_type == "produce":
        return Produce(tuple(data["territories"]))
    if action_type == "upgrade":
        return Upgrade(
            UpgradeBenefit(data["benefit"]),
            UpgradeDiscount(data["discount"]),
        )
    if action_type == "build":
        return Build(BuildingType(data["building"]), data["territory"])
    if action_type == "end_turn":
        return EndTurn()
    raise ValueError(f"Unknown action type: {action_type}")
