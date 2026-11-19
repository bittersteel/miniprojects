# Avalon Simulation

A modular Monte Carlo simulator for the social deduction board game
*The Resistance: Avalon*, built up in versions:

- **[Version 1](#version-1--probability-based-baseline)** is a probability-based baseline:
  every player acts on fixed, tunable probabilities and uses only their private knowledge
  (their own role and, for evil players, who their allies are). Nobody learns from the game history.
- **[Version 2](#version-2--belief-tracking)** adds belief tracking: every player learns from
  team votes and quest outcomes, and every decision uses those beliefs.

The goal is to build understanding of the game in steps. Each version adds one layer of
nuance (beliefs, special roles, strategic play) on top of a rules engine that stays the same.

## Contents

```
AvalonSimulator
├── avalon_simulation_v1.ipynb   # V1 simulator, examples and parameter sweeps
├── avalon_simulation_v2.ipynb   # V2 belief tracking, V1-vs-V2 comparisons and sweeps
└── README.md                    # This document
```

## Getting started

Requirements: Python 3.10+, Jupyter, `numpy`, `pandas`, `matplotlib`.

```bash
pip install jupyter numpy pandas matplotlib
jupyter notebook avalon_simulation_v1.ipynb      # or avalon_simulation_v2.ipynb
```

Each notebook is self-contained; run its cells top to bottom. The V1 notebook runs in seconds,
the V2 notebook in about 4 minutes (it simulates roughly 90,000 games). The minimal V1 usage is:

```python
game = AvalonGame(7, probabilistic_factory(), rng=random.Random(42))
describe_game(game.play())                       # play-by-play of one game

df = simulate(5000, n_players=7, agent_factory=probabilistic_factory())
(df.winner == "good").mean()                     # good win rate

sweep("p_evil_fail", [0.0, 0.5, 1.0])            # vary one probability
```

For V2, swap in `belief_factory()` (see [Version 2](#version-2--belief-tracking)).

## Rules implemented

Both versions share the same rules engine.

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
V1 and V2 leave them out, so mechanically they play like the core loop of *The Resistance*.
They are the first item in [Future scope](#future-scope).

## Version 1 — Probability-based baseline

### Architecture

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

### Tunable parameters (`PolicyParams`)

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

### Baseline results

With default parameters, good wins about **9%** of 7-player games (5,000 games). That is
expected: good players choose and approve teams essentially at random, so most quests
contain an evil player who fails 80% of the time. Treat this as the floor that smarter good
agents must beat. The notebook also sweeps `p_evil_fail` and `p_good_approve` across 5, 7 and
10 players.

### Limitations of V1

- Good players never use the public history (vote patterns, fail counts).
- Evil players don't coordinate, so two evil players on one team may both fail and reveal more
  than necessary.
- Strategy doesn't change with the score or the vote track.
- No special roles and no assassination phase.

## Version 2 — Belief tracking

V2 addresses the first and third V1 limitations. Every player learns from the public record,
and every decision draws on what they've learned:

- **Team votes** are public. Evil players tend to approve teams that contain evil and reject
  all-good teams, so voting patterns are noisy evidence about who is evil.
- **Quest outcomes** reveal the number of fail cards. Good players can't fail, so a quest with
  *f* fails had at least *f* evil players on it.

### What changed from V1

| Layer | V2 status |
|---|---|
| Roles & rules, game state, engine | Unchanged |
| Information model | `PlayerView` adds three public rule constants: `n_evil`, `max_rejections`, `quests_to_win` |
| Belief tracking | **New:** `BeliefModel`, `BeliefTracker` |
| Agents | **New:** `V2Params`, `BeliefAgent`; the V1 `ProbabilisticAgent` is kept as a baseline |
| Analysis | Adds `run_games`, `replay_beliefs`, `belief_metrics`, matchups between agent types |

### The belief tracker

A **hypothesis** is one possible evil team. `BeliefTracker` holds an exact Bayesian posterior
over every hypothesis consistent with what its owner knows (C(6, 3) = 20 for a good player in a
7-player game, at most C(10, 4) = 210 in any game), stored as log-probabilities to avoid underflow.

- **Quest evidence:** with *k* evil players on the team under a hypothesis, *f* fail cards
  have likelihood C(k, f) · aᶠ · (1 − a)ᵏ⁻ᶠ, where *a* is the assumed evil fail rate.
  Hypotheses with *f* > *k* are eliminated.
- **Vote evidence:** each non-leader vote is scored under a simple model of how good and evil
  players vote. Because that model is approximate, its log-likelihood is multiplied by
  `vote_weight` (0 = ignore votes, 1 = full Bayes).
- **Queries:** `p_evil()` gives each player's marginal suspicion; `p_team_safe(team, fails)`
  gives the exact probability that a team has too few evil players to sink the quest.

A good player's tracker rules out only themself. An evil player already knows the truth, so
their tracker is a **public observer** (no exclusions): a model of what the table can infer.
It must not rule out the evil player, or the true hypothesis could be eliminated and the
posterior would break.

### How decisions use beliefs

| Decision | V2 behaviour |
|---|---|
| Good leader proposes | Includes self, then samples remaining seats with weight exp(−`propose_beta` · P(evil)) |
| Good player votes | Approves with probability σ(`vote_beta` · (safe(team) − safe(own best team) + `vote_tolerance` + `vote_leniency` · rejections)); approves with `p_final_attempt_approve` on the 5th attempt |
| Evil leader proposes | Self and maybe one ally, then the good players the table trusts most, so the team looks clean |
| Evil player votes | Approves teams with evil at 90%; on all-good teams sometimes votes as a good player would (`p_evil_blend_in`) |
| Evil quest card | Fails at `p_evil_fail`; always fails when one more failed quest wins the game |

Vote approval compares the team with the voter's *own best team* rather than a fixed threshold,
because early in the game every team is risky and an absolute threshold would reject almost
everything.

### Usage

```python
game = AvalonGame(7, belief_factory(), rng=random.Random(16))
state = game.play()
replay_beliefs(state)                            # public P(evil) per player after each quest

simulate(5000, 7, belief_factory())              # both sides V2
simulate(5000, 7, mixed_factory(good=belief_factory(), evil=probabilistic_factory()))

sweep("propose_beta", [0, 4, 8, 16])             # V2Params field
sweep("belief.vote_weight", [0, 0.5, 1])         # BeliefModel field
```

### Tunable parameters (`V2Params` and `BeliefModel`)

| Parameter | Default | Meaning |
|---|---|---|
| `propose_beta` | 8.0 | How strongly a good leader prefers low-suspicion players (0 = random, like V1) |
| `vote_beta` | 12.0 | Steepness of the good approval curve |
| `vote_tolerance` | 0.1 | How much less safe than their own best team a good voter accepts |
| `vote_leniency` | 0.05 | Extra tolerance per rejection already on the vote track |
| `p_final_attempt_approve` | 0.95 | Good approval on the 5th attempt (rejecting loses the game) |
| `evil_propose_beta` | 8.0 | How strongly an evil leader picks publicly trusted good players |
| `p_evil_blend_in` | 0.3 | Chance an evil player votes on an all-good team as a good player would |
| `p_evil_fail` / `p_evil_fail_decisive` | 0.8 / 1.0 | Evil fail rate, normally and when a fail would win the game |
| `belief.assumed_evil_fail` | 0.8 | Evil fail rate the trackers assume |
| `belief.vote_*` | 0.6 / 0.9 / 0.3 | Assumed approval rates: good voter; evil voter on a team with / without evil |
| `belief.vote_weight` | 0.5 | Tempering of vote evidence |

V2 also keeps `p_good_leader_includes_self`, `p_approve_own_team`,
`p_evil_leader_includes_self`, `p_evil_leader_adds_ally` and the evil approval rates from V1.

### Results (7 players unless stated)

| Metric | V1 | V2 |
|---|---|---|
| Good win rate (5,000 games) | 9.2% | 96.3% |
| Quest teams with no evil player | 6.9% | 61.2% |
| Proposals / rejections per game | 4.3 / 0.5 | 7.2 / 3.2 |
| Evil wins on 5 rejections | 0.0% | 0.2% |

- **Learning helps at every size:** good wins 87–96% for 5 to 10 players in V2, against 4–10% in V1.
- **The beliefs are accurate.** The three most-suspected players are the evil ones 63% of the
  time after quest 1, 86% after quest 2 and 93% after quest 3 (random guessing: 43%).
- **Votes carry most of the signal.** With `vote_weight = 0` (fail counts only) good wins 43%;
  with random team picks (`propose_beta = 0`) good wins 25%.
- **Failing less doesn't help evil hide.** Across `p_evil_fail` from 0.2 to 1.0, good's win
  rate only moves from 99% to 94.5%, because evil's votes give it away regardless.
- **Evil's vote pattern is the main tell.** If evil votes less revealingly than good's model
  expects, good's win rate falls to 76% at most. It doesn't fall further because evil also
  stops voting its own teams through.

### Limitations of V2

- **Evil is still naive.** It backs its own teams 90% of the time, fails at the first chance and
  doesn't coordinate fail cards. The 96% win rate reflects that, not real Avalon balance.
- **Good knows evil's voting habits exactly.** By default the `BeliefModel` vote rates match
  V2 evil's real behaviour.
- **Good voters are modelled at a flat approval rate,** although V2 good players actually vote
  on their beliefs.
- **Team proposals are not used as evidence** (e.g. an evil leader picking an ally).
- **No special roles and no assassination phase,** which in real Avalon is evil's main way back.

## Future scope

### Agent intelligence

- **V2 — Belief tracking.** Done; see [Version 2](#version-2--belief-tracking).
- **V4 — Strategic evil.** Coordinate so only one evil player fails a small team, play
  success early to build trust (a `p_evil_fail` per quest index), and vote to hide alignment.
  This is the main counter to V2's good players, whose edge comes from evil's voting pattern.
- **V5 — Learned vote models.** V2 already feeds votes into the belief tracker, but with
  hand-set likelihoods. Fit P(approve | alignment, evil on team) from simulated games instead,
  model good voters' belief-driven votes, and use team proposals as evidence too.

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
