# Guillotine League 2026

Draft and in-season tools for an 18-team, full-PPR fantasy football guillotine league.

In a guillotine league there are no head-to-head matchups. Every week the **lowest-scoring team is eliminated** and their entire roster hits waivers. Last team standing wins. With 18 teams the champion is crowned after **Week 17** (Jan 3, 2027).

That single rule changes everything: you aren't trying to win the week, you're trying not to lose it. These tools are built around floor rather than upside.

## What's in here

| File | What it is |
|---|---|
| **`index.html`** | Live draft room — 220-player board with pick tracking, roster-aware suggestions, scarcity meters, and stack/bye warnings. Self-contained, no build step, no dependencies. |
| **`Guillotine-Playbook-2026.md`** | Strategy guide written from zero football knowledge. Format rules, draft plan, FAAB spend curve, weekly routine, common mistakes. |
| **`Guillotine-FAAB-Tracker-2026.xlsx`** | Season tracker. Set the current week and it gives you bid ceilings by player tier, flags overspending or hoarding, and logs how close you came to the chop each week. |

## Using the draft room

Open `index.html` in any browser. Set your draft slot and league size in the header.

- **Click a row** — someone else took him
- **Click ★** — you took him
- **Type a name, press Enter** — marks taken. **Shift+Enter** — marks yours. This is the fast path on a 90-second clock.
- **Click a suggestion** — marks him as yours
- **Click a column header** — sort by that column

The right-hand panel recalculates on every pick: what to take next and why, what's running out, and what's wrong with your roster so far.

Picks, draft slot, and league size persist in the browser (`localStorage`), so a refresh won't wipe a live draft. Use **reset** to start over.

### Hosting it

The draft room is static HTML (`index.html` plus `playbook.html`). Deploy the repo on Vercel as a static site — no build step.

## Reading the board

| Column | Meaning |
|---|---|
| **PPG** | 2025 full-PPR points per game |
| **ST%** | Share of 2025 games with **10+ PPR points** |
| **BUST** | Share of 2025 games under 5 PPR points |

**ST% is the column to look at.** Season totals mostly measure durability — play 17 games and you'll out-total a better player who missed three. In a format where one dud week ends your season, what matters is how often a player clears a usable line.

### Grades

These are guillotine-specific and are editorial, not computed. A `RISK` grade often means a player ranked correctly for a normal league who is wrong for this one.

| Grade | Meaning |
|---|---|
| `FLOOR` | Boring and consistent. Draft these. |
| `OK` | Solid, no red flags. |
| `RISK` | Boom-bust, injury history, or unclear role. |
| `AVOID` | Injury or production profile that gets you chopped. |
| `CUFF` | Handcuff / insurance body. |

### Flags

- **`NEW TM`** — changed NFL teams for 2026, so the 2025 numbers came in a different offense.
- **`NO '25`** — no 2025 NFL production (rookie, or missed the year). Their ranking is a projection, not evidence. 30 of the 220 players carry this flag.

## Rebuilding after a news event

Injury news will break between now and Week 1. To update the board:

```bash
pip install -r requirements.txt   # first time only
./build.sh
```

That regenerates `index.html` and the tracker from source.

### What to edit

**`src/board.py`** — the file you'll actually touch. One tuple per player:

```python
(rank, "Name", "POS", "TEAM", "GRADE", "note shown on the board")
```

Change a grade, rewrite a note, reorder ranks, or add a player. Bye weeks are looked up from the team code automatically, so `TEAM` must be a valid abbreviation.

**`src/stats25.py`** — 2025 stats, keyed by player name:

```python
"Name": (total_pts, games, ppg, games_10plus, start_pct, boom_pct, bust_pct)
```

Also holds `ROOKIE` (no 2025 data) and `NEWTEAM` (changed teams) sets, which drive the flags.

**`src/merge.py`** — the `OV` dict, which overrides grades and notes from `board.py`. This is where the 83 data-driven regrades live, separated from the base board so you can see what the 2025 numbers changed and why.

**`src/build_app.py`** — the draft room itself: HTML, CSS, and the suggestion engine. The scoring function is `suggest()` — roughly:

```
score = (250 - overall_rank)
      + grade bonus            FLOOR +45 · RISK −35 · AVOID −140
      + positional need        empty starting slot +70, TE +75
      + scarcity               few startable left at the position +30
      + 2025 consistency       scaled from ST%, capped ±35
      + handcuff match         CUFF on the same NFL team as one of your RBs, +130 late
      − bye stacking           4+ already on that bye week
      − team stacking          2+ already from that NFL team
```

Tune the constants to taste — every one of them is a judgment call.

**`src/build_xlsx.py`** — the FAAB tracker. Formulas are written without cached values, so Excel recalculates on open.

## Sources

Rankings blend [Bleacher Report's 2026 PPR top 100](https://bleacherreport.com/articles/25458550-top-100-fantasy-football-rankings-ppr-leagues-2026) with [RotoWire's 2026 PPR cheat sheet](https://www.rotowire.com/football/article/2026-fantasy-football-cheat-sheet-for-ppr-leagues-printable-excel-128065) for ranks 100–250.

2025 statistics are derived from [nflverse](https://github.com/nflverse/nflverse-data) play-by-play data and cross-validated against [Pro-Football-Reference](https://www.pro-football-reference.com/years/2025/fantasy.htm) (~65 players spot-checked, all matched). Consistency metrics are computed from nflverse weekly data.

Injury status from [Yahoo's training camp tracker](https://sports.yahoo.com/fantasy/article/nfl-training-camp-injury-report-tracking-the-latest-news-updates-for-2026-fantasy-football-163938278.html), current as of **Aug 16, 2026**. Bye weeks from [NFL.com](https://www.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week).

Strategy draws on [Guillotine Leagues](https://guillotineleagues.com/public/overview), [Fantasy Life's FAAB-by-month analysis](https://www.fantasylife.com/articles/guillotine-leagues/how-to-manage-your-faab-in-guillotine-league-fantasy-football), [RotoWire](https://www.rotowire.com/football/article/guillotine-league-strategy-how-much-faab-should-you-bid-85174), [Draft Sharks](https://www.draftsharks.com/kb/best-guillotine-league-strategy), and [FantasyPros](https://www.fantasypros.com/2026/06/guillotine-league-draft-strategy-guide-2026-fantasy-football/).

Rankings and injury data go stale fast. Re-check before draft day.
