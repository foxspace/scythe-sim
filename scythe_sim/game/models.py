"""Small data objects shared by the game modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Terrain(StrEnum):
    MOUNTAIN = "mountain"
    FARM = "farm"
    FOREST = "forest"
    TUNDRA = "tundra"
    VILLAGE = "village"
    FACTORY = "factory"


class Resource(StrEnum):
    METAL = "metal"
    FOOD = "food"
    WOOD = "wood"
    OIL = "oil"


class UnitType(StrEnum):
    WORKER = "worker"
    CHARACTER = "character"


class BuildingType(StrEnum):
    MILL = "mill"
    MINE = "mine"
    MONUMENT = "monument"


class Faction(StrEnum):
    RUSVIET = "rusviet"
    NORDIC = "nordic"


class UpgradeBenefit(StrEnum):
    MOVE = "move"
    PRODUCE = "produce"


class UpgradeDiscount(StrEnum):
    UPGRADE = "upgrade"
    BUILD = "build"


TERRAIN_RESOURCE: dict[Terrain, Resource | None] = {
    Terrain.MOUNTAIN: Resource.METAL,
    Terrain.FARM: Resource.FOOD,
    Terrain.FOREST: Resource.WOOD,
    Terrain.TUNDRA: Resource.OIL,
    Terrain.VILLAGE: None,
    Terrain.FACTORY: None,
}


@dataclass
class Tile:
    """One board hex and everything stored on it."""

    id: str
    q: int
    r: int
    terrain: Terrain
    resources: dict[Resource, int] = field(
        default_factory=lambda: {resource: 0 for resource in Resource}
    )
    building: BuildingType | None = None
    building_owner: int | None = None


@dataclass
class Unit:
    id: str
    owner: int
    kind: UnitType
    location: str


@dataclass
class PlayerState:
    id: int
    faction: Faction
    upgrades: list[tuple[UpgradeBenefit, UpgradeDiscount]] = field(default_factory=list)
    buildings: set[BuildingType] = field(default_factory=set)
    stars: set[str] = field(default_factory=set)
    previous_action: str | None = None

    @property
    def move_range(self) -> int:
        return 1 + sum(benefit == UpgradeBenefit.MOVE for benefit, _ in self.upgrades)

    @property
    def produce_limit(self) -> int:
        return 1 + sum(benefit == UpgradeBenefit.PRODUCE for benefit, _ in self.upgrades)

    @property
    def upgrade_cost(self) -> int:
        discount = sum(
            kind == UpgradeDiscount.UPGRADE for _, kind in self.upgrades
        )
        return max(1, 3 - discount)

    @property
    def build_cost(self) -> int:
        discount = sum(kind == UpgradeDiscount.BUILD for _, kind in self.upgrades)
        return max(1, 3 - discount)
