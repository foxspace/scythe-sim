"""The compact, fixed research board and hex helpers."""

from __future__ import annotations

from scythe_sim.game.models import Terrain, Tile

HEX_DIRECTIONS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def tile_id(q: int, r: int) -> str:
    return f"{q},{r}"


def parse_tile_id(value: str) -> tuple[int, int]:
    q, r = value.split(",")
    return int(q), int(r)


def canonical_edge(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first, second)))  # type: ignore[return-value]


RIVER_EDGES = {
    canonical_edge(tile_id(-2, 1), tile_id(-1, 1)),
    canonical_edge(tile_id(2, -1), tile_id(1, -1)),
    canonical_edge(tile_id(-1, 0), tile_id(0, 0)),
    canonical_edge(tile_id(1, 0), tile_id(0, 0)),
}


TERRAIN_LAYOUT: dict[tuple[int, int], Terrain] = {
    (-2, 0): Terrain.VILLAGE,
    (-2, 1): Terrain.FOREST,
    (-2, 2): Terrain.MOUNTAIN,
    (-1, -1): Terrain.TUNDRA,
    (-1, 0): Terrain.FARM,
    (-1, 1): Terrain.MOUNTAIN,
    (-1, 2): Terrain.TUNDRA,
    (0, -2): Terrain.FOREST,
    (0, -1): Terrain.FARM,
    (0, 0): Terrain.FACTORY,
    (0, 1): Terrain.FARM,
    (0, 2): Terrain.FOREST,
    (1, -2): Terrain.TUNDRA,
    (1, -1): Terrain.MOUNTAIN,
    (1, 0): Terrain.FARM,
    (1, 1): Terrain.TUNDRA,
    (2, -2): Terrain.MOUNTAIN,
    (2, -1): Terrain.FOREST,
    (2, 0): Terrain.VILLAGE,
}


def create_board() -> dict[str, Tile]:
    return {
        tile_id(q, r): Tile(
            id=tile_id(q, r),
            q=q,
            r=r,
            terrain=terrain,
        )
        for (q, r), terrain in TERRAIN_LAYOUT.items()
    }


def neighbors(board: dict[str, Tile], location: str) -> list[str]:
    q, r = parse_tile_id(location)
    result = []
    for dq, dr in HEX_DIRECTIONS:
        candidate = tile_id(q + dq, r + dr)
        if candidate in board:
            result.append(candidate)
    return sorted(result)


def has_river(first: str, second: str) -> bool:
    return canonical_edge(first, second) in RIVER_EDGES
