# Scythe AI Research Simulator

A deterministic, two-player strategy environment for studying AI decisions.
It is a deliberately small Scythe-inspired research model, not a full
implementation of the commercial board game. See [RULES.md](RULES.md) for the
exact rules and simplifications.

Version 0.1 includes a 19-hex board, localized resources, workers, characters,
movement, production, upgrades, structures, research stars, scoring, seeded
Random and Heuristic agents, JSON/CSV logs, replay verification, Pygame
visualization, and pytest tests. It does **not** include learning or combat.

## Setup

Python 3.12 or newer is required.

```bash
brew install uv
uv sync
```

`uv` creates and maintains `.venv` from `pyproject.toml` and `uv.lock`; manual
activation is not required. Commit `uv.lock`, but never commit `.venv`.

For a reproducible install that refuses to change the lockfile:

```bash
uv sync --locked
```

## Configuration

- `.python-version` selects Python 3.12.
- `pyproject.toml` defines the application dependencies and the `dev` group.
- `uv.lock` pins exact dependency versions for reproducible environments.
- `RULES.md` contains all game constants, scoring rules, and simplifications.

Add runtime and development packages with:

```bash
uv add PACKAGE
uv add --dev PACKAGE
```

Runtime behavior is configured with command-line flags:

- `--mode`: `visual`, `headless`, or `replay`
- `--matchup`: `random-random`, `random-heuristic`,
  `heuristic-random`, or `heuristic-heuristic`
- `--seed`: deterministic game seed
- `--games`: number of headless games
- `--speed`: normal visualization turns per second
- `--log`: JSON or JSONL output path
- `--csv-prefix`: optional game/action CSV path prefix
- `--replay-file`: game log to replay and verify

Show the complete CLI help at any time:

```bash
uv run python main.py --help
```

Heuristic weights can be configured through the Python API:

```python
from scythe_sim.agents import HeuristicAgent, HeuristicWeights

agent = HeuristicAgent(
    HeuristicWeights(resource_weight=1.5, territory_weight=3.0)
)
```

## Running

Visual Random-versus-Heuristic game:

```bash
uv run python main.py --mode visual --matchup random-heuristic --seed 42
```

Controls: Space plays/pauses, Right Arrow steps, R restarts, and F toggles fast
mode. The right panel shows the available action types, selected action, and
the Heuristic agent's real numerical score explanation.

One headless game:

```bash
uv run python main.py --mode headless --matchup random-heuristic --seed 42 \
  --log data/game_42.json
```

One hundred headless games:

```bash
uv run python main.py --mode headless --matchup random-heuristic --seed 100 \
  --games 100 --log data/batch.jsonl
```

Replay and verify every recorded state hash:

```bash
uv run python main.py --mode replay --replay-file data/game_42.json
```

Export game- and action-level CSVs for pandas:

```bash
uv run python main.py --mode headless --seed 42 --log data/game_42.json \
  --csv-prefix data/game_42
```

Run tests:

```bash
uv run pytest
```

## AI decisions

`RandomAgent` first chooses an available action type uniformly, then chooses
one legal action of that type uniformly. This prevents a large number of Move
variations from overwhelming every other action type. It only passes when no
non-pass action is available.

`HeuristicAgent` simulates each legal action on a cloned state and scores the
actual feature changes. Its configurable weights cover resources, territory,
upgrades, buildings, workers, stars, centerward mobility, future production
positions, and passing. Stable action ordering breaks equal scores, so
identical seeds and inputs reproduce the same game. It is intentionally a
one-step, self-focused baseline: it does not predict future turns or model the
opponent's goals.

Across consecutive seeds, setup rotates the starting player and faction
assignment to avoid tying an agent's measured win rate to one seat or faction.

Example explanation:

```text
Highest heuristic value = 7.9
(territory=+2.5, stars=+7.0, mobility=-1.6)
```

## Logs

JSON is the replay source. A game record contains its seed, initial state,
agents, every legal action offered, the selected action, all heuristic scores,
the selected score breakdown, before/after research metrics, unit positions,
results, and state hashes.

Abbreviated turn record:

```json
{
  "turn": 12,
  "player": 1,
  "agent": "P1 Heuristic",
  "action": {"type": "upgrade", "benefit": "produce", "discount": "build"},
  "reason": "Highest heuristic value = 4.0 (upgrades=+4.0)",
  "after": {
    "1": {"resources": 2, "territories": 4, "stars": 1, "upgrades": 1}
  },
  "after_hash": "..."
}
```

CSV is a convenience for analysis and is not used for replay.

## Project structure

```text
scythe_sim/
├── game/           board, actions, state, rules, engine, scoring, serialization
├── agents/         shared interface, RandomAgent, HeuristicAgent
├── logging/        research records, CSV export, replay verification
├── visualization/  asset-free Pygame view
└── runner.py       shared visual/headless game session
tests/              focused mechanics and reproducibility tests
data/               generated game logs
main.py             command-line entry point
RULES.md            authoritative research rules and simplifications
```

## Extension points

New factions belong in the data model and movement/action rule helpers. New
actions implement immutable action objects plus legal generation and engine
execution. Future learning agents should implement the same `Agent` interface;
they must choose from engine-supplied legal actions and never mutate state.
