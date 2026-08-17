# -*- coding: utf-8 -*-
"""Merge the 2026 board with 2025 stats and re-grade where the data disagrees with me."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

import json, sys
board = json.load(open(str(DATA_DIR / "board.json")))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats25 import S, ROOKIE, NEWTEAM

# Grade changes forced by the 2025 weekly data. name -> (grade, note or None to keep)
OV = {
 # --- promoted: the data says the floor is real ---
 "De'Von Achane": ("FLOOR","Hit 10+ PPR in all 16 games he played in 2025, zero bust weeks. Elite floor."),
 "Drake Maye": ("FLOOR","Scored 10+ in all 17 games in 2025 — the only QB on the board who did. Best floor at the position."),
 "Chase Brown": ("FLOOR","Zero bust weeks in 17 games. Boring and reliable, exactly the profile."),
 "Javonte Williams": ("FLOOR","Zero bust weeks in 16 games. Under-the-radar floor play."),
 "Zay Flowers": ("FLOOR","10+ PPR in 14 of 17 games. Quietly one of the steadiest WRs in the league."),
 "Chris Olave": ("FLOOR","Zero bust weeks in 16 games. Target share is the whole reason."),
 "Tee Higgins": ("FLOOR","10+ in 10 of 15 games, one bust week all year."),
 "Tetairoa McMillan": ("FLOOR","10+ in 12 of 17 games as a rookie. Volume on a weak offense is a feature here."),
 "D'Andre Swift": ("FLOOR","One bust week in 16 games. Receiving work keeps the floor up."),
 "Bucky Irving": ("FLOOR","Zero bust weeks. Only played 10 games, but he was reliable in all of them."),
 "Travis Etienne Jr.": ("FLOOR","10+ in 12 of 17 games, one bust week. New offense in NO is the only question."),

 # --- demoted: I called these floor plays and the data says otherwise ---
 "David Montgomery": ("OK","I had this wrong. Only 7 of 17 games above 10 PPR in 2025 and 9.8 per game — that is not a floor play. Also changed teams."),
 "Kenny Gainwell": ("OK","The target volume is real but only 7 of 17 games cleared 10 PPR. Boom-ier than his reputation."),
 "Ladd McConkey": ("OK","10+ in only half his games and a 31% bust rate. Less steady than the target share suggests."),
 "Khalil Shakir": ("OK","Decent but not elite: 10+ in 9 of 16 games."),
 "Justin Jefferson": ("OK","Down year — 11.9 per game and exactly one 20-point week in 17 games. Talent is not the issue; the offense was."),
 "Garrett Wilson": ("OK","Only 7 games in 2025 and a 29% bust rate in them. Talent is real, sample is thin."),
 "Brock Bowers": ("OK","Missed 5 games and cleared 10 PPR in only 7 of 12. Still a top TE, just not the lock the ranking implies."),
 "Lamar Jackson": ("OK","Rushing floor is real but 2025 was volatile — 6 bust weeks in 13 games. Injury-shortened season."),
 "Emeka Egbuka": ("RISK","Only 7 of 17 games above 10 PPR. Boom-bust rookie season."),
 "DeVonta Smith": ("RISK","10+ in only 7 of 17 games with a 24% bust rate. Shares targets and it shows."),
 "DJ Moore": ("RISK","41% start rate and a 35% bust rate. Genuinely boom-bust."),
 "Michael Wilson": ("RISK","Good totals, bad distribution — only 7 of 17 games above 10 PPR."),

 # --- injury/age calls the data forces me to revisit ---
 "Christian McCaffrey": ("RISK","Honest correction: he played all 17 games in 2025 and led all backs at 24.5 per game with zero bust weeks. The injury history is still real, but AVOID was too strong."),
 "Derrick Henry": ("RISK","Floor held up better than expected — 10+ in 14 of 17 games. Age is the risk, not consistency."),
 "Saquon Barkley": ("RISK","Zero bust weeks in 16 games, but only two 20-point games. The floor is fine; the ceiling has gone."),
 "George Pickens": ("OK","2025 says I was harsh — 10+ in 13 of 17 games, one bust week. New team is the real question."),
 "DK Metcalf": ("OK","Better floor than his reputation: 10+ in 9 of 15 games, one bust week."),

 # --- data says avoid ---
 "Chuba Hubbard": ("AVOID","Brutal 2025: 10+ PPR in 3 of 15 games, 47% bust rate, 8.4 per game. Add the hamstring and there is nothing to like."),
 "Bhayshul Tuten": ("AVOID","Cleared 10 PPR twice in 15 games. 53% bust rate."),
 "Tre' Harris": ("AVOID","Did not clear 10 PPR once in 16 games in 2025. Zero."),
 "Rashod Bateman": ("AVOID","One game above 10 PPR in 13. 77% bust rate."),
 "Darnell Mooney": ("AVOID","One game above 10 PPR in 15."),
 "Jalen Tolbert": ("AVOID","67% bust rate, 3.9 per game."),
 "Calvin Ridley": ("AVOID","One game above 10 PPR in 7. Rankings are all over the place on him for a reason."),
 "Evan Engram": ("AVOID","2 of 16 games above 10 PPR."),
 "Geno Smith": ("AVOID","80% bust rate in 2025 — under 15 points in 12 of 15 games."),

 # --- risk downgrades from weak floors ---
 "Kenneth Walker III": ("RISK","10+ in only 8 of 17 games. New team may help, but the 2025 floor was poor."),
 "Breece Hall": ("RISK","Half his games under 10 PPR."),
 "TreVeyon Henderson": ("RISK","53% start rate with a 24% bust rate as a rookie."),
 "Rico Dowdle": ("RISK","24% bust rate and a new team."),
 "RJ Harvey": ("RISK","Boom-bust: 24% boom, 24% bust."),
 "Rachaad White": ("RISK","4 of 17 games above 10 PPR."),
 "Kyle Monangai": ("RISK","35% start rate, 35% bust rate."),
 "Jacory Croskey-Merritt": ("RISK","47% bust rate."),
 "Marvin Harrison Jr.": ("RISK","Half his games under 10 PPR and only one 20-point week in 12."),
 "Brian Thomas Jr.": ("RISK","Down year — 10+ in only 5 of 14 games."),
 "Terry McLaurin": ("RISK","Only 10 games and half of them under 10 PPR."),
 "Michael Pittman Jr.": ("RISK","29% bust rate, plus a new team for 2026."),
 "Chris Godwin Jr.": ("RISK","Nine games, 44% start rate. Health is the whole question."),
 "Matthew Golden": ("RISK","64% bust rate as a rookie. 5.0 per game."),
 "Jayden Higgins": ("RISK","35% start rate, 35% bust rate."),
 "Jerry Jeudy": ("RISK","4 of 17 games above 10 PPR, 47% bust rate."),
 "Adonai Mitchell": ("RISK","62% bust rate."),
 "Kayshon Boutte": ("RISK","50% bust rate."),
 "Malik Washington": ("RISK","3 of 17 games above 10 PPR."),
 "Darius Slayton": ("RISK","21% start rate."),
 "Devaughn Vele": ("RISK","44% bust rate."),
 "Tory Horton": ("RISK","50% start rate but also a 50% bust rate in 8 games. Pure volatility."),
 "Isaac TeSlaa": ("RISK","57% bust rate."),
 "Jaylin Noel": ("RISK","71% bust rate as a rookie."),
 "Andrei Iosivas": ("RISK","53% bust rate."),
 "Jalen Nailor": ("RISK","2 of 17 games above 10 PPR."),
 "Xavier Worthy": ("RISK","36% start rate. The speed has not turned into steady points."),
 "Colston Loveland": ("RISK","Only 6 of 16 games above 10 PPR as a rookie. Ranking is betting on year two."),
 "Mark Andrews": ("RISK","47% bust rate. The decline is in the numbers."),
 "Isaiah Likely": ("RISK","2 of 12 games above 10 PPR, 58% bust rate. New team, unproven as a starter."),
 "Chig Okonkwo": ("RISK","24% start rate."),
 "T.J. Hockenson": ("RISK","27% start rate."),
 "Gunnar Helm": ("RISK","19% start rate, 50% bust rate."),
 "Terrance Ferguson": ("RISK","64% bust rate."),
 "Greg Dulcich": ("RISK","1 of 9 games above 10 PPR."),
 "Pat Freiermuth": ("RISK","20% start rate."),
 "Cade Otton": ("RISK","40% bust rate."),
 "Mike Gesicki": ("RISK","67% bust rate."),
 "David Njoku": ("RISK","27% start rate, and a new team."),
 "Oronde Gadsden": ("RISK","47% bust rate as a rookie."),
 "Sam Darnold": ("RISK","47% bust rate."),
 "C.J. Stroud": ("RISK","64% bust rate — under 15 points in 9 of 14 games."),
 "Jordan Love": ("RISK","53% bust rate."),
 "Kyler Murray": ("RISK","Only 5 games in 2025 and a new team. Almost no usable signal."),
 "Joe Burrow": ("OK","Injury-shortened 2025 (8 games). Elite when playing, but the sample is thin and the injury risk is not."),
 "Tyler Warren": ("OK","Zero 20-point games in 17 as a rookie. Steady-ish, but no upside yet."),
}

STAT_FIX = {  # board name -> stats key, where they differ
}

out = []
for p in board["players"]:
    n = p["n"]
    if n in OV:
        g, note = OV[n]
        p["g"] = g
        if note: p["note"] = note
    st = S.get(n) or S.get(STAT_FIX.get(n, ""))
    if st:
        tot, gp, ppg, ten, sp, bm, bs = st
        p["s"] = {"tot":tot,"g":gp,"ppg":ppg,"ten":ten,"sp":sp,"bm":bm,"bs":bs}
    else:
        p["s"] = None
    p["flag"] = "R" if (n in ROOKIE or p["s"] is None) else ("N" if n in NEWTEAM else "")
    out.append(p)

# tier buckets used by the scarcity panel
for p in out:
    r = p["r"]
    p["tier"] = 1 if r<=18 else 2 if r<=36 else 3 if r<=72 else 4 if r<=126 else 5

json.dump({"players": out}, open(str(DATA_DIR / "board2.json"),"w"), separators=(",",":"))

have = sum(1 for p in out if p["s"])
print(f"{len(out)} players, {have} with 2025 stats, {len(out)-have} without")
print("regrades applied:", sum(1 for p in out if p['n'] in OV))
from collections import Counter
print(Counter(p["g"] for p in out))
print("no-stat players:", [p["n"] for p in out if not p["s"]][:50])
