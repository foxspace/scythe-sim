# Rules: Scythe Research Simulator 0.1

This is a small research environment inspired by *Scythe*, not a complete
digital edition. The official rules are the design reference, but the rules
below are the authority for this simulator.

## Goal and game end

Two factions build an economy and spread over a fixed 19-hex map. A game ends
immediately when a player owns 4 research stars, or after turn 120. The turn
limit is a safety fallback; normal games are intended to end through stars.

For unbiased batches, the seed deterministically rotates the starting player
and swaps faction assignments over each block of four seeds. A single seed
always recreates exactly the same setup.

Final score:

- 5 points per star
- 2 points per controlled territory
- 1 point per pair of controlled resource tokens
- 3 points per building
- 2 additional points for the Monument
- 2 points per upgrade
- 1 point per worker beyond the starting two

Highest score wins. Ties are broken by stars, territories, resources, then the
lower player number. The tie-break is deliberately deterministic.

## Board, control, and resources

The board uses axial `(q, r)` coordinates. Mountain produces metal, farm
produces food, forest produces wood, tundra produces oil, and village produces
workers. The central Factory does not produce.

A player controls a hex containing one of their units. An empty hex containing
their building is also controlled. Resources stay on their hex and can only be
spent while that hex is controlled. Costs are removed in sorted coordinate
order so replays are deterministic.

Characters and workers are units. Enemy-occupied hexes cannot be entered in
version 0.1 because combat is not implemented. This makes every unit an
invulnerable territorial blocker, which is a known strategic distortion that
will be removed when combat is added.

## Turns and actions

Players alternate turns and choose exactly one legal action:

### Move

Move one unit along a legal path. Units begin with range 1. The Move upgrade
raises range to 2. A unit cannot revisit any hex, including its starting hex,
in one move or enter an enemy-occupied hex. Marked river edges block movement
unless a faction ability says otherwise.

### Produce

Choose one controlled hex containing a worker. Every worker there produces one
item matching the terrain. A village creates workers, up to 5 workers per
player. The Produce upgrade permits choosing two hexes.

An owned, controlled Mill always produces as one extra worker when its owner
uses Produce. Its hex is a free bonus production hex if it was not selected.

### Upgrade

Spend 3 controlled oil. Choose one unused benefit and one unused discount:

- Benefits: increase Move range or Produce territory limit.
- Discounts: reduce future Upgrade cost or Build cost by 1.

Each benefit and discount can be selected once, so a player can complete two
upgrades. A discount never reduces a cost below 1.

### Build

Spend 3 controlled wood, reduced by a Build discount. Place one unused
building on a controlled hex containing a worker. Only one building may occupy
a hex.

- **Mill:** bonus production described above.
- **Mine:** connects its hex to the central Factory for its owner's movement.
- **Monument:** contributes 2 additional end-game points.

Buildings are permanent.

### End Turn

Pass without changing the board. This guarantees that the legal action list is
never empty.

Except for Rusviet, a player cannot choose the same non-pass action type on two
consecutive turns.

## Factions

- **Rusviet — Relentless:** may repeat the previous action type.
- **Nordic — Swim:** workers may cross marked river edges.

The factions, board, and rules are represented as data so more asymmetry can be
added later.

## Research stars

Stars are permanent once earned:

- **Innovator:** complete 2 upgrades.
- **Builder:** build all 3 buildings.
- **Expansion:** control at least 6 territories.
- **Workforce:** have 5 workers.
- **Stockpile:** control at least 8 resource tokens.

## Differences from commercial Scythe

The commercial game uses four player-mat sections, optional paired top- and
bottom-row actions, coins, popularity-dependent scoring, six stars, more units,
and a much larger map. This version instead uses one explicit action per turn,
research scoring, 4 stars, 5 workers, 2 upgrades, and 3 buildings.

Version 0.1 intentionally omits trade, bolster, power, popularity, mechs,
combat, combat cards, enlistment, objectives, encounters, the Factory card,
resource transport, worker retreat, player mats, coins, structure bonuses,
Automa rules, and all expansion rules.

The Mine and Monument are simplified. The faction abilities are recognizable
subsets of the originals, but the map and economy are newly balanced for this
research environment. No claim is made that results transfer directly to the
commercial board game.
