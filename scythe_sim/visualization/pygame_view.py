"""A simple, asset-free view of AI decisions and game state."""

from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Callable

import pygame

from scythe_sim.game.models import Terrain, UnitType
from scythe_sim.game.rules import controlled_resource_count, controlled_territories
from scythe_sim.game.scoring import score_player
from scythe_sim.logging.game_logger import GameLogger
from scythe_sim.runner import GameSession, create_session

WIDTH, HEIGHT = 1200, 800
BOARD_CENTER = (390, 390)
HEX_SIZE = 72

TERRAIN_COLORS = {
    Terrain.MOUNTAIN: (143, 143, 137),
    Terrain.FARM: (212, 183, 92),
    Terrain.FOREST: (83, 135, 91),
    Terrain.TUNDRA: (121, 154, 176),
    Terrain.VILLAGE: (176, 118, 81),
    Terrain.FACTORY: (105, 97, 118),
}
PLAYER_COLORS = {0: (185, 55, 55), 1: (50, 105, 190)}


def axial_to_pixel(q: int, r: int) -> tuple[float, float]:
    x = HEX_SIZE * math.sqrt(3) * (q + r / 2) + BOARD_CENTER[0]
    y = HEX_SIZE * 1.5 * r + BOARD_CENTER[1]
    return x, y


def hex_points(center: tuple[float, float]) -> list[tuple[float, float]]:
    return [
        (
            center[0] + HEX_SIZE * math.cos(math.radians(60 * index - 30)),
            center[1] + HEX_SIZE * math.sin(math.radians(60 * index - 30)),
        )
        for index in range(6)
    ]


class PygameView:
    def __init__(
        self,
        matchup: str,
        seed: int,
        speed: float = 1.5,
        log_path: str | Path | None = None,
    ):
        pygame.init()
        pygame.display.set_caption("Scythe AI Research Simulator")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.small = pygame.font.SysFont("arial", 14)
        self.title = pygame.font.SysFont("arial", 24, bold=True)
        self.matchup = matchup
        self.seed = seed
        self.normal_speed = max(0.2, speed)
        self.fast = False
        self.playing = True
        self.last_step_time = 0
        self.log_path = Path(log_path) if log_path else None
        self.session = self._new_session()
        self.buttons: dict[str, pygame.Rect] = {}

    def _new_session(self) -> GameSession:
        session = create_session(self.matchup, self.seed)
        if self.log_path:
            session.logger = GameLogger(
                self.log_path,
                session.state,
                self.matchup,
                {key: agent.name for key, agent in session.agents.items()},
            )
        return session

    def _restart(self) -> None:
        self.session = self._new_session()
        self.playing = True
        self.last_step_time = pygame.time.get_ticks()

    def _draw_text(
        self,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int] = (232, 232, 232),
        font: pygame.font.Font | None = None,
    ) -> None:
        self.screen.blit((font or self.font).render(text, True, color), position)

    def _draw_board(self) -> None:
        state = self.session.state
        for tile in state.board.values():
            center = axial_to_pixel(tile.q, tile.r)
            points = hex_points(center)
            pygame.draw.polygon(self.screen, TERRAIN_COLORS[tile.terrain], points)
            pygame.draw.polygon(self.screen, (40, 43, 48), points, 3)
            self._draw_text(
                tile.terrain.value.title(),
                (int(center[0] - 32), int(center[1] - 52)),
                (25, 25, 28),
                self.small,
            )
            resources = [
                f"{resource.value[0].upper()}:{amount}"
                for resource, amount in tile.resources.items()
                if amount
            ]
            if resources:
                self._draw_text(
                    " ".join(resources),
                    (int(center[0] - 34), int(center[1] + 28)),
                    (22, 22, 24),
                    self.small,
                )
            if tile.building:
                color = PLAYER_COLORS[tile.building_owner or 0]
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(int(center[0] - 14), int(center[1] - 10), 28, 22),
                    border_radius=3,
                )
                self._draw_text(
                    tile.building.value[0].upper(),
                    (int(center[0] - 5), int(center[1] - 10)),
                    font=self.small,
                )

            units = [
                unit
                for unit in sorted(state.units.values(), key=lambda value: value.id)
                if unit.location == tile.id
            ]
            for index, unit in enumerate(units):
                x = int(center[0] - 30 + (index % 4) * 19)
                y = int(center[1] + 3 + (index // 4) * 18)
                color = PLAYER_COLORS[unit.owner]
                if unit.kind == UnitType.CHARACTER:
                    pygame.draw.circle(self.screen, color, (x, y), 9)
                    pygame.draw.circle(self.screen, (245, 245, 245), (x, y), 9, 2)
                else:
                    pygame.draw.rect(
                        self.screen, color, pygame.Rect(x - 7, y - 7, 14, 14)
                    )

    def _draw_player_panel(self, player_id: int, top: int) -> None:
        state = self.session.state
        player = state.players[player_id]
        active = state.current_player == player_id and not state.game_over
        rect = pygame.Rect(790, top, 390, 145)
        pygame.draw.rect(self.screen, (47, 51, 58), rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            PLAYER_COLORS[player_id] if active else (88, 92, 100),
            rect,
            3,
            border_radius=8,
        )
        agent = self.session.agents[player_id]
        self._draw_text(
            f"Player {player_id + 1}: {agent.name}",
            (808, top + 10),
            font=self.title,
        )
        lines = [
            f"Faction: {player.faction.value.title()}    Score: {score_player(state, player_id)}",
            f"Territories: {len(controlled_territories(state, player_id))}    Resources: {controlled_resource_count(state, player_id)}",
            f"Workers: {sum(u.owner == player_id and u.kind == UnitType.WORKER for u in state.units.values())}    Stars: {len(player.stars)}",
            f"Upgrades: {len(player.upgrades)}    Buildings: {len(player.buildings)}",
        ]
        for index, line in enumerate(lines):
            self._draw_text(line, (808, top + 43 + 23 * index), font=self.small)

    def _draw_decision(self) -> None:
        rect = pygame.Rect(790, 340, 390, 280)
        pygame.draw.rect(self.screen, (38, 41, 47), rect, border_radius=8)
        self._draw_text("Decision", (808, 353), font=self.title)
        y = 388
        if self.session.state.game_over:
            state = self.session.state
            lines = [
                "Game over",
                f"Winner: Player {state.winner + 1 if state.winner is not None else '?'}",
                f"Scores: {state.final_scores}",
                f"Reason: {state.end_reason}",
            ]
        elif self.session.last_decision is None:
            player = self.session.state.current_player
            lines = [f"Player {player + 1} is deciding..."]
        else:
            decision = self.session.last_decision
            kinds = sorted({action.kind for action in self.session.last_legal_actions})
            lines = [
                f"Legal actions: {', '.join(kinds)}",
                f"Selected: {decision.action.kind}",
                "Reason:",
                *textwrap.wrap(decision.reason, 46),
            ]
        for line in lines:
            self._draw_text(line, (808, y), font=self.small)
            y += 22

    def _draw_controls(self) -> None:
        labels = [
            ("play", "Pause" if self.playing else "Play"),
            ("step", "Step"),
            ("restart", "Restart"),
            ("fast", f"Fast: {'On' if self.fast else 'Off'}"),
        ]
        x = 790
        for key, label in labels:
            width = 88 if key != "fast" else 105
            rect = pygame.Rect(x, 650, width, 42)
            self.buttons[key] = rect
            pygame.draw.rect(self.screen, (73, 83, 98), rect, border_radius=6)
            pygame.draw.rect(self.screen, (135, 145, 160), rect, 2, border_radius=6)
            self._draw_text(label, (x + 12, 661), font=self.small)
            x += width + 10
        self._draw_text(
            "Space: play/pause   →: step   R: restart   F: fast",
            (790, 710),
            (170, 175, 185),
            self.small,
        )

    def _handle_control(self, key: str) -> None:
        if key == "play":
            self.playing = not self.playing
        elif key == "step" and not self.session.state.game_over:
            self.session.step()
        elif key == "restart":
            self._restart()
        elif key == "fast":
            self.fast = not self.fast

    def run(self) -> None:
        running = True
        self.last_step_time = pygame.time.get_ticks()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    key_map = {
                        pygame.K_SPACE: "play",
                        pygame.K_RIGHT: "step",
                        pygame.K_r: "restart",
                        pygame.K_f: "fast",
                    }
                    if event.key in key_map:
                        self._handle_control(key_map[event.key])
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for key, rect in self.buttons.items():
                        if rect.collidepoint(event.pos):
                            self._handle_control(key)

            now = pygame.time.get_ticks()
            delay = 35 if self.fast else int(1000 / self.normal_speed)
            if (
                self.playing
                and not self.session.state.game_over
                and now - self.last_step_time >= delay
            ):
                self.session.step()
                self.last_step_time = now

            self.screen.fill((27, 30, 35))
            self._draw_board()
            self._draw_player_panel(0, 20)
            self._draw_player_panel(1, 180)
            self._draw_decision()
            self._draw_controls()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


def run_visual(
    matchup: str = "random-heuristic",
    seed: int = 0,
    speed: float = 1.5,
    log_path: str | Path | None = None,
) -> None:
    PygameView(matchup, seed, speed, log_path).run()
