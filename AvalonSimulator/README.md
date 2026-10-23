# Avalon Simulation — Version 1

A modular Monte Carlo simulator for the social deduction board game
*The Resistance: Avalon*. Version 1 is a probability-based baseline: every player acts on
fixed, tunable probabilities and uses only their private knowledge (their own role and, for
evil players, who their allies are). Nobody learns from the game history yet.

The goal is to build understanding of the game in steps. Each later version adds one layer of
nuance (beliefs, special roles, strategic play) on top of a rules engine that stays the same.

## Contents

```
Avalon
├── avalon_simulation_v1.ipynb   # V1 simulator, examples and parameter sweeps
└── README.md                    # This document
```

## Getting started

Requirements: Python 3.10+, Jupyter, `pandas`, `matplotlib`.

```bash
pip install jupyter pandas matplotlib
jupyter notebook avalon_simulation_v1.ipynb
```

Run the cells top to bottom. The minimal usage is:

```python
game = AvalonGame(7, probabilistic_factory(), rng=random.Random(42))
describe_game(game.play())                       # play-by-play of one game

df = simulate(5000, n_players=7, agent_factory=probabilistic_factory())
(df.winner == "good").mean()                     # good win rate

sweep("p_evil_fail", [0.0, 0.5, 1.0])            # vary one probability
```

## Rules implemented

| Rule | Implementation |
|---|---|
| Players and alignment | 5–10 players; 2, 2, 3, 3, 3, 4 evil players for 5–10 players |
| Team sizes | Official table per player count and quest (`QUEST_SIZES`) |
| Team vote | Every player votes in public, the leader included; strict majority approves, ties reject |
| Leadership | Passes clockwise after every proposal |
| Vote track | 5 consecutive rejections on one quest → evil wins |
| Quest cards | Good must play success; evil may fail; only the fail count is revealed |
| Double-fail quest | Quest 4 with 7+ players needs 2 fail cards to fail |
| Victory | First side to 3 quests |

**Scope note.** The official beginner game of Avalon also includes Merlin and the Assassin.
V1 leaves them out, so mechanically it plays like the core loop of *The Resistance*. They are
the first item in [Future scope](#future-scope).

## Architecture

The code is split into six layers. Each one only talks to its neighbour, so a later version
can replace one layer without touching the rest.

1. **Roles and rules** (`Alignment`, `Role`, `GameRules`): the static rulebook. Roles carry
   their alignment; `GameRules` answers "how big is this team?" and "how many fails sink
   this quest?".
2. **Game state and public log** (`GameState`, `Proposal`, `QuestResult`): `GameState` is
   the hidden ground truth, owned by the engine. `Proposal` and `QuestResult` are the public
   record: who voted which way, and how many fail cards each quest received.
3. **Information model** (`PlayerView`, `basic_knowledge`, `make_view`): the only thing an
   agent ever sees is a read-only `PlayerView` containing public info plus that player's
   private knowledge. Who-sees-whom is a single swappable function (`basic_knowledge`).
4. **Agents and policies** (`Agent`, `PolicyParams`, `ProbabilisticAgent`): any object with
   `propose_team`, `vote_on_team` and `play_quest_card` can play. Agents are created through
   a factory, so different agent types can be mixed.
5. **Engine** (`AvalonGame`): enforces the rules (validates teams, forces good players'
   cards to success, applies the vote track and double-fail rule, detects the winner).
6. **Simulation and analysis** (`simulate`, `sweep`, `game_record`, `describe_game`):
   runs many seeded games into a `pandas` DataFrame. `sweep` reuses the same seeds for every
   parameter value, which reduces noise when comparing them.

## Tunable parameters (`PolicyParams`)

| Parameter | Default | Meaning |
|---|---|---|
| `p_leader_includes_self` | 0.9 | Leader puts themself on the team |
| `p_evil_leader_adds_ally` | 0.3 | Evil leader also adds one known evil ally |
| `p_approve_own_team` | 1.0 | Leader approves their own proposal |
| `p_good_approve` | 0.55 | Good player approves any team (they can't tell teams apart in V1) |
| `p_evil_approve_with_evil` | 0.9 | Evil player approves a team containing evil |
| `p_evil_approve_no_evil` | 0.3 | Evil player approves an all-good team |
| `p_evil_fail` | 0.8 | Evil player on a quest plays a fail card (independent per player) |

Derive variants with `dataclasses.replace(PolicyParams(), p_evil_fail=0.5)`.

## Baseline results

With default parameters, good wins about **9%** of 7-player games (5,000 games). That is
expected: good players choose and approve teams essentially at random, so most quests
contain an evil player who fails 80% of the time. Treat this as the floor that smarter good
agents must beat. The notebook also sweeps `p_evil_fail` and `p_good_approve` across 5, 7 and
10 players.

## Limitations of V1

- Good players never use the public history (vote patterns, fail counts).
- Evil players don't coordinate, so two evil players on one team may both fail and reveal more
  than necessary.
- Strategy doesn't change with the score or the vote track.
- No special roles and no assassination phase.

## Future scope

### Agent intelligence

- **V2 — Belief tracking.** Good agents keep P(player *i* is evil), starting from the
  uniform prior `n_evil / (n − 1)` and updating exactly after each quest by Bayes over all
  possible evil subsets (at most C(9, 3) = 84 hypotheses). Proposals favour low-suspicion
  players; votes approve with probability `sigmoid(β · (threshold − expected evil on team))`.
  Add vote-track pressure (e.g. near-certain approval on the 5th attempt).
- **V4 — Strategic evil.** Coordinate so only one evil player fails a small team, play
  success early to build trust (a `p_evil_fail` per quest index), and vote to hide alignment.
- **V5 — Inference from votes.** Feed the public vote log into the belief tracker, with
  likelihoods such as P(approve | evil, evil on team) calibrated from simulated games.

### V3 — Special roles

The characters below are the main source of depth in Avalon. Each one changes **who knows
what** at the start of the game, so most of the work is in the information model.

| Role | Side | Knows | Seen by |
|---|---|---|---|
| **Merlin** | Good | All evil players, except Mordred | Percival (but confused with Morgana) |
| **Assassin** | Evil | Fellow evil players (not Oberon) | Merlin, evil teammates |
| **Percival** | Good | Merlin and Morgana, without knowing which is which | Nobody |
| **Morgana** | Evil | Fellow evil players (not Oberon) | Merlin, evil teammates; appears as Merlin to Percival |
| **Mordred** | Evil | Fellow evil players (not Oberon) | Evil teammates only; hidden from Merlin |
| **Oberon** | Evil | Nobody | Merlin only; unknown to the other evil players |

Notes on each role and what it would need in the code:

- **Merlin and the Assassin** (the official beginner setup). Merlin knows the evil team, so
  good can win more often, but if good completes 3 quests the Assassin gets one guess at
  Merlin's identity, and a correct guess means evil wins. This creates the central tension
  of the game: Merlin must guide good without being obvious.
  - Override `AvalonGame._end_of_game` to run an assassination step when good reaches 3 quests.
  - Add an `assassinate(view) -> int` method to the agent interface. A first version can
    guess uniformly among players the evil team doesn't know to be evil; a later version
    can target whoever most consistently rejected evil-containing teams.
  - Give Merlin a parameter such as `p_merlin_hint` that trades accurate voting/proposals
    against the risk of being identified.
- **Percival** protects Merlin. He knows which players are Merlin and Morgana but not which
  is which, so he can follow Merlin's lead and act as a decoy for the Assassin.
  - `known_evil: frozenset[int]` is no longer enough. Extend `PlayerView` with a richer
    knowledge object, e.g. `merlin_candidates: frozenset[int]`, and have the information
    model return that object.
- **Morgana** counters Percival by appearing as a second Merlin, forcing Percival to work out
  which of the two is genuine from their behaviour.
  - Morgana's policy can imitate Merlin's (approving "clean-looking" teams) to stay credible.
- **Mordred** is evil but invisible to Merlin, which weakens Merlin's information and gives
  evil a player who can look trustworthy even to the best-informed good player.
  - A one-line rule in the information model: exclude Mordred from Merlin's `known_evil`.
- **Oberon** is evil but isolated: he doesn't know the other evil players and they don't
  know him (Merlin does see him). This helps good, since evil can no longer coordinate fully.
  - Exclude Oberon from evil players' knowledge in both directions; his policy uses no allies,
    and teammates may accidentally double-fail with him.

Implementation checklist for V3:

1. Add the roles to the `Role` enum (one line each).
2. Make the role mix configurable: replace `GameRules.default_roles()` with a setup that
   picks which special roles are in play and fills the rest with generic servants/minions.
3. Replace `basic_knowledge` with a full information model returning a knowledge object
   (`known_evil`, `merlin_candidates`, …).
4. Add role-specific agents, or role-specific `PolicyParams`, via the agent factory.
5. Add the assassination phase to the engine and an `assassination` win reason to
   `game_record`, so analysis can separate "good lost on quests" from "Merlin was found".

### Other extensions

- **Lady of the Lake** (optional rule): after quests 2, 3 and 4, the holder privately inspects
  another player's alignment, then passes the token to them. Adds a private-information
  channel that belief tracking (V2) can consume.
- **Analysis:** win rates per role setup, how often the Assassin finds Merlin, and calibration
  of agent parameters against observed human play.
