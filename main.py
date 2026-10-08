"""Command-line entry point for visual games, batches, and replays."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scythe_sim.logging import GameLogger, replay_game
from scythe_sim.runner import create_session


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--mode", choices=("visual", "headless", "replay"), default="visual"
    )
    result.add_argument(
        "--matchup",
        choices=(
            "random-random",
            "random-heuristic",
            "heuristic-random",
            "heuristic-heuristic",
        ),
        default="random-heuristic",
    )
    result.add_argument("--seed", type=int, default=0)
    result.add_argument("--games", type=int, default=1)
    result.add_argument("--speed", type=float, default=1.5)
    result.add_argument("--log", type=Path, default=Path("data/latest_game.json"))
    result.add_argument("--csv-prefix", type=Path)
    result.add_argument("--replay-file", type=Path)
    return result


def run_headless(args: argparse.Namespace) -> None:
    if args.games < 1:
        raise SystemExit("--games must be at least 1")
    winners: Counter[int] = Counter()
    scores = {0: [], 1: []}
    lengths: list[int] = []
    for offset in range(args.games):
        seed = args.seed + offset
        session = create_session(args.matchup, seed)
        if args.games == 1:
            log_path = args.log
        else:
            log_path = args.log.with_suffix(".jsonl")
        logger = GameLogger(
            log_path,
            session.state,
            args.matchup,
            {key: agent.name for key, agent in session.agents.items()},
        )
        session.logger = logger
        state = session.run()
        winners[state.winner] += 1  # type: ignore[index]
        for player_id in scores:
            scores[player_id].append(state.final_scores[player_id])
        lengths.append(state.turn_number)
        if args.csv_prefix and args.games == 1:
            logger.export_csv(args.csv_prefix)

    summary = {
        "games": args.games,
        "matchup": args.matchup,
        "wins": {str(key): value for key, value in sorted(winners.items())},
        "win_rates": {
            str(player_id): winners[player_id] / args.games for player_id in (0, 1)
        },
        "average_scores": {
            str(player_id): sum(values) / len(values)
            for player_id, values in scores.items()
        },
        "average_game_length": sum(lengths) / len(lengths),
        "log": str(log_path),
    }
    print(json.dumps(summary, indent=2))


def main() -> None:
    args = parser().parse_args()
    if args.mode == "visual":
        from scythe_sim.visualization.pygame_view import run_visual

        run_visual(args.matchup, args.seed, args.speed, args.log)
    elif args.mode == "headless":
        run_headless(args)
    else:
        source = args.replay_file or args.log
        state = replay_game(source)
        print(
            json.dumps(
                {
                    "winner": state.winner,
                    "scores": state.final_scores,
                    "turns": state.turn_number,
                    "final_state_verified": True,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
