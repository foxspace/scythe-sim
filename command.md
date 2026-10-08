```
uv sync
uv run python main.py --mode visual

# Headless AI game
uv run python main.py --mode headless
# Choose agents and seed
uv run python main.py --mode visual \
  --matchup heuristic-heuristic \
  --seed 42
```