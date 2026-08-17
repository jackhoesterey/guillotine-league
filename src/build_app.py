# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

import json
D = json.load(open(str(DATA_DIR / "board2.json")))["players"]
DATA = json.dumps(D, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guillotine Draft Room 2026</title>
<style>
:root{
 --bg:#0f1115;--panel:#171a21;--panel2:#1d212a;--line:#2a2f3a;--line2:#232833;
 --tx:#e8eaef;--tx2:#9aa2b1;--tx3:#6b7382;
 --floor:#3fb950;--ok:#8b93a1;--risk:#d29922;--avoid:#f85149;--cuff:#58a6ff;
 --accent:#f0883e;--mine:#3fb950;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--tx);
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.top{position:sticky;top:0;z-index:60;background:var(--bg);border-bottom:1px solid var(--line);
 padding:10px 18px}
.topin{max-width:1560px;margin:0 auto;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
h1{font-size:17px;margin:0;letter-spacing:-.02em;white-space:nowrap}
h1 span{color:var(--tx3);font-weight:400;font-size:12px;margin-left:8px}
.setup{display:flex;gap:6px;align-items:center;font-size:12px;color:var(--tx3)}
.setup input{width:44px;background:var(--panel2);border:1px solid var(--line);color:var(--tx);
 padding:4px 6px;border-radius:6px;font-size:12.5px;text-align:center;outline:none}
.setup input:focus{border-color:var(--accent)}
.pill{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:5px 11px;
 font-size:12px;color:var(--tx2);white-space:nowrap}
.pill b{color:var(--tx);font-weight:600}
.pill.hot{border-color:var(--accent);background:rgba(240,136,62,.1)}
.pill.hot b{color:var(--accent)}

.layout{max-width:1560px;margin:0 auto;padding:14px 18px 70px;display:grid;
 grid-template-columns:1fr 350px;gap:18px;align-items:start}

.ctl{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
button.f{background:var(--panel2);border:1px solid var(--line);color:var(--tx2);
 padding:5px 12px;border-radius:999px;font-size:12.5px;cursor:pointer;font-weight:500}
button.f:hover{border-color:#3d4250;color:var(--tx)}
button.f.on{background:var(--tx);color:var(--bg);border-color:var(--tx);font-weight:600}
input#q{background:var(--panel2);border:1px solid var(--line);color:var(--tx);
 padding:6px 12px;border-radius:8px;font-size:13px;min-width:230px;outline:none}
input#q:focus{border-color:var(--accent)}
.hint{font-size:11.5px;color:var(--tx3);margin-left:auto}
kbd{background:var(--panel2);border:1px solid var(--line);border-radius:4px;padding:1px 5px;
 font-size:10.5px;font-family:inherit;color:var(--tx2)}

table{width:100%;border-collapse:collapse;font-size:13.5px}
thead th{position:sticky;top:52px;background:var(--bg);text-align:left;font-size:10px;
 letter-spacing:.08em;text-transform:uppercase;color:var(--tx3);font-weight:600;
 padding:8px 6px;border-bottom:1px solid var(--line);z-index:20;cursor:pointer;user-select:none}
thead th:hover{color:var(--tx)}
thead th.nos{cursor:default}
thead th.nos:hover{color:var(--tx3)}
tbody td{padding:7px 6px;border-bottom:1px solid var(--line2);vertical-align:top}
tbody tr{cursor:pointer}
tbody tr:hover td{background:#161a21}
tbody tr.taken{opacity:.22}
tbody tr.taken .nm{text-decoration:line-through}
tbody tr.mine td{background:rgba(63,185,80,.07)}
tbody tr.mine:hover td{background:rgba(63,185,80,.12)}
tbody tr.mine .nm::after{content:" ★";color:var(--mine);font-size:11px}
.rk{color:var(--tx3);font-variant-numeric:tabular-nums;width:32px;font-size:12.5px}
tbody td:nth-child(2){min-width:218px;white-space:nowrap}
.nm{font-weight:600;letter-spacing:-.01em}
.tm{color:var(--tx3);font-size:11.5px;margin-left:6px;font-weight:400}
.pr{color:var(--tx2);font-size:12px;width:48px;font-variant-numeric:tabular-nums}
.by{color:var(--tx3);font-size:12px;width:34px;text-align:center}
.nt{color:var(--tx2);font-size:12px;line-height:1.4;min-width:200px}
.num{font-variant-numeric:tabular-nums;text-align:right;width:52px;font-size:12.5px}
.num.dim{color:var(--tx3)}
.g{display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:.05em;
 padding:2px 6px;border-radius:4px;white-space:nowrap}
.g.FLOOR{background:rgba(63,185,80,.13);color:var(--floor)}
.g.OK{background:rgba(139,147,161,.11);color:var(--ok)}
.g.RISK{background:rgba(210,153,34,.13);color:var(--risk)}
.g.AVOID{background:rgba(248,81,73,.13);color:var(--avoid)}
.g.CUFF{background:rgba(88,166,255,.13);color:var(--cuff)}
td.gc{width:58px}
.flag{display:inline-block;font-size:9px;font-weight:700;letter-spacing:.04em;padding:1px 4px;
 border-radius:3px;margin-left:5px;vertical-align:1px}
.flag.R{background:rgba(139,147,161,.14);color:var(--tx3)}
.flag.N{background:rgba(240,136,62,.14);color:var(--accent)}
.star{background:none;border:1px solid var(--line);color:var(--tx3);border-radius:5px;
 width:22px;height:22px;font-size:11px;cursor:pointer;line-height:1;padding:0}
.star:hover{border-color:var(--mine);color:var(--mine)}
td.act{width:30px}

.side{position:sticky;top:64px;display:flex;flex-direction:column;gap:12px;max-height:calc(100vh - 78px);overflow-y:auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 14px}
.card h3{margin:0 0 9px;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
 color:var(--tx3);font-weight:600}
.sug{padding:8px 0;border-bottom:1px solid var(--line2);cursor:pointer}
.sug:last-child{border-bottom:none}
.sug:hover .sn{color:var(--accent)}
.sn{font-weight:600;font-size:13.5px}
.sn small{color:var(--tx3);font-weight:400;margin-left:6px;font-size:11.5px}
.sr{color:var(--tx2);font-size:11.5px;margin-top:2px;line-height:1.4}
.slots{display:grid;grid-template-columns:repeat(2,1fr);gap:5px}
.slot{background:var(--panel2);border:1px solid var(--line2);border-radius:6px;padding:5px 8px;font-size:11.5px}
.slot .lb{color:var(--tx3);font-size:9.5px;letter-spacing:.06em;text-transform:uppercase}
.slot .vl{color:var(--tx);font-weight:600;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.slot.empty{border-style:dashed}
.slot.empty .vl{color:var(--tx3);font-weight:400}
.scar{display:flex;justify-content:space-between;align-items:center;padding:4px 0;font-size:12.5px}
.scar .lb{color:var(--tx2)}
.bar{height:4px;background:var(--panel2);border-radius:2px;flex:1;margin:0 10px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--floor);border-radius:2px}
.bar i.low{background:var(--risk)} .bar i.crit{background:var(--avoid)}
.scar .vl{color:var(--tx);font-variant-numeric:tabular-nums;font-weight:600;min-width:44px;text-align:right}
.warn{background:rgba(248,81,73,.09);border:1px solid rgba(248,81,73,.3);border-radius:7px;
 padding:7px 10px;font-size:12px;color:#ffb4ae;margin-bottom:6px;line-height:1.4}
.warn:last-child{margin-bottom:0}
.warn.amb{background:rgba(210,153,34,.09);border-color:rgba(210,153,34,.3);color:#f5d478}
.warn b{color:#fff}
.ok{color:var(--tx3);font-size:12px}
.mini{font-size:11px;color:var(--tx3);margin-top:8px;line-height:1.45}
.legend{margin-top:16px;font-size:11.5px;color:var(--tx3);line-height:1.9}
.legend b{font-weight:600}
@media(max-width:1180px){
 .layout{grid-template-columns:1fr}
 .side{position:static;max-height:none}
 .nt{display:none}
}
@media(max-width:700px){ .by,.num.t,.num.b{display:none} }
</style></head><body>

<div class="top"><div class="topin">
  <h1>Guillotine Draft Room <span>18 teams · full PPR · 18 rounds</span></h1>
  <div class="setup">slot
    <input id="slot" type="number" min="1" max="18" value="1">
    of <input id="teams" type="number" min="2" max="20" value="18">
  </div>
  <span class="pill">pick <b id="pk">1</b> · rd <b id="rd">1</b></span>
  <span class="pill hot" id="nextp">your pick: <b>#1</b></span>
  <span class="pill">roster <b id="rc">0</b>/14</span>
  <span class="pill" style="cursor:pointer" id="undo">undo</span>
  <span class="pill" style="cursor:pointer" id="reset">reset</span>
  <a class="pill" href="/playbook.html" style="text-decoration:none;color:inherit">playbook</a>
</div></div>

<div class="layout">
<div>
  <div class="ctl">
    <button class="f on" data-p="ALL">All</button>
    <button class="f" data-p="QB">QB</button><button class="f" data-p="RB">RB</button>
    <button class="f" data-p="WR">WR</button><button class="f" data-p="TE">TE</button>
    <span style="width:6px"></span>
    <button class="f" data-g="FLOOR">Floor</button>
    <button class="f" data-g="CUFF">Cuffs</button>
    <button class="f on" data-x="hide">Hide taken</button>
    <input id="q" placeholder="Search — Enter = taken, Shift+Enter = mine" autocomplete="off">
    <span class="hint"><kbd>click</kbd> taken · <kbd>★</kbd> mine</span>
  </div>
  <table><thead><tr>
    <th class="rk" data-s="r">#</th><th class="nos">Player</th><th class="pr" data-s="pr">Pos</th>
    <th class="by" data-s="b">Bye</th><th class="gc nos">Grade</th>
    <th class="num" data-s="ppg" title="2025 full-PPR points per game">PPG</th>
    <th class="num t" data-s="sp" title="% of 2025 games with 10+ PPR points — the floor stat that matters here">ST%</th>
    <th class="num b" data-s="bs" title="% of 2025 games under 5 PPR points">BUST</th>
    <th class="nos">Guillotine note</th><th class="act nos"></th>
  </tr></thead><tbody id="tb"></tbody></table>
  <div class="legend">
    <b style="color:var(--floor)">FLOOR</b> boring and consistent &nbsp;·&nbsp;
    <b style="color:var(--ok)">OK</b> no red flags &nbsp;·&nbsp;
    <b style="color:var(--risk)">RISK</b> boom-bust, injury, or unclear role &nbsp;·&nbsp;
    <b style="color:var(--avoid)">AVOID</b> gets you chopped &nbsp;·&nbsp;
    <b style="color:var(--cuff)">CUFF</b> handcuff / insurance<br>
    <b>ST%</b> = share of 2025 games with 10+ PPR points. In a format where one dud week ends your season,
    this is the number that matters — far more than season totals.
    <b class="flag N" style="margin-left:0">N</b> changed NFL teams for 2026, so the 2025 numbers came in a different offense.
    <b class="flag R" style="margin-left:0">R</b> no 2025 NFL production — rookie or missed the year. Treat their ranking as a projection, not evidence.
  </div>
</div>

<div class="side">
  <div class="card"><h3>Take one of these</h3><div id="sugs"></div></div>
  <div class="card"><h3>Watch out</h3><div id="warns"></div></div>
  <div class="card"><h3>Your lineup</h3><div class="slots" id="slots"></div>
    <div class="mini" id="bench"></div></div>
  <div class="card"><h3>What's left</h3><div id="scar"></div>
    <div class="mini">Startable = ranked inside the top 54 WR / 36 RB / 18 TE / 18 QB and not graded AVOID.</div></div>
</div>
</div>

<script>
let D = [];
const byName = {};
const LS = "gl-draft-2026";
let st = {};            // rank -> 'taken' | 'mine'
let hist = [];          // for undo
let fp="ALL", fg=null, qs="", hideTaken=true, sortKey="r", sortDir=1;

function save(){
  try {
    localStorage.setItem(LS, JSON.stringify({
      st, hist,
      slot: $("#slot").value,
      teams: $("#teams").value
    }));
  } catch (e) {}
}
function load(){
  try {
    const raw = localStorage.getItem(LS);
    if (!raw) return;
    const d = JSON.parse(raw);
    if (d.st && typeof d.st === "object") st = d.st;
    if (Array.isArray(d.hist)) hist = d.hist;
    if (d.slot) $("#slot").value = d.slot;
    if (d.teams) $("#teams").value = d.teams;
  } catch (e) {}
}

const $ = s => document.querySelector(s);
const teams = () => Math.max(2, +$("#teams").value || 18);
const slot  = () => Math.min(teams(), Math.max(1, +$("#slot").value || 1));
const picksMade = () => Object.keys(st).length;
const mine = () => D.filter(p => st[p.r] === "mine");

/* ---------- snake draft position ---------- */
function myPicks(){
  const t = teams(), s = slot(), out = [];
  for (let rd = 1; rd <= 18; rd++){
    const inRound = (rd % 2 === 1) ? s : (t - s + 1);
    out.push((rd - 1) * t + inRound);
  }
  return out;
}
function nextPick(){
  const made = picksMade();
  return myPicks().find(p => p > made) || null;
}

/* ---------- roster model ---------- */
function roster(){
  const m = mine();
  const cnt = {QB:0,RB:0,WR:0,TE:0};
  m.forEach(p => cnt[p.p]++);
  const need = {QB: 1-cnt.QB, RB: 2-cnt.RB, WR: 2-cnt.WR, TE: 1-cnt.TE};
  const flexUsed = Math.max(0,cnt.RB-2) + Math.max(0,cnt.WR-2) + Math.max(0,cnt.TE-1);
  return {m, cnt, need, flexOpen: flexUsed === 0 && cnt.RB>=2 && cnt.WR>=2 && cnt.TE>=1};
}
function byeCounts(){
  const b = {}; mine().forEach(p => { if(p.b) b[p.b] = (b[p.b]||0)+1; });
  return b;
}
function teamCounts(){
  const t = {}; mine().forEach(p => t[p.t] = (t[p.t]||0)+1);
  return t;
}

/* ---------- scarcity ---------- */
const STARTABLE = {WR:54, RB:36, TE:18, QB:18};
function scarcity(){
  const out = {};
  for (const pos of ["RB","WR","TE","QB"]){
    const pool = D.filter(p => p.p===pos && p.g!=="AVOID");
    const cut  = pool.slice(0, STARTABLE[pos]);
    const left = cut.filter(p => !st[p.r]).length;
    out[pos] = {left, total: cut.length};
  }
  return out;
}

/* ---------- suggestion engine ---------- */
function suggest(){
  const R = roster(), bc = byeCounts(), tc = teamCounts();
  const sc = scarcity();
  const rd = Math.floor(picksMade() / teams()) + 1;
  const filled = R.m.length;
  const gradeB = {FLOOR:45, OK:0, RISK:-35, AVOID:-140, CUFF: filled>=7 ? 40 : -25};
  const myRBteams = new Set(R.m.filter(p=>p.p==="RB").map(p=>p.t));

  const scored = D.filter(p => !st[p.r]).map(p => {
    let s = 250 - p.r;
    const pro = [], con = [];          // reasons to take him / reasons not to
    const why = pro;                   // pros are pushed first, cons appended at the end
    s += gradeB[p.g];
    if (p.g === "FLOOR") pro.push("high floor");
    if (p.g === "AVOID") con.push("graded avoid");

    // positional need
    // handcuff to a back you already own — the strongest late-round reason there is
    if (p.g === "CUFF" && p.p === "RB" && myRBteams.has(p.t)){
      s += filled >= 7 ? 130 : 60;
      pro.push("handcuffs a back you already own");
    }

    if (p.p === "QB"){
      if (R.cnt.QB === 0){ s += (rd>=8? 85 : 40); if(rd>=8) pro.push("you still have no QB"); }
      else if (R.cnt.QB >= 2) s -= 130;
      else s -= 55;
    } else if (p.p === "TE"){
      if (R.cnt.TE === 0){ s += 75; pro.push("you still have no TE"); }
      else if (R.cnt.TE >= 2) s -= 115;
      else s -= 25;
    } else {
      const need = R.need[p.p];
      if (need > 0){ s += 70; pro.push(`fills your ${p.p}${R.cnt[p.p]+1} slot`); }
      else if (R.flexOpen){ s += 35; pro.push("fills your flex"); }
      else if (R.cnt[p.p] >= 5) s -= 45;
    }

    // positional scarcity — only meaningful while some are actually left
    if (sc[p.p] && sc[p.p].left >= 1 && sc[p.p].left <= 8 && p.r <= 130){
      s += 30; pro.push(`only ${sc[p.p].left} startable ${p.p}${sc[p.p].left===1?"":"s"} left`);
    }

    // 2025 consistency
    if (p.s){
      const c = Math.max(-35, Math.min(35, (p.s.sp - 50) * 0.8));
      s += c;
      if (p.s.sp >= 75) pro.push(`10+ PPR in ${p.s.sp}% of 2025 games`);
      else if (p.s.sp <= 30) con.push(`only ${p.s.sp}% of 2025 games above 10 PPR`);
    } else { s -= 25; con.push("no 2025 data — projection only"); }

    // late-round cuff priority
    if (rd >= 13 && p.g === "CUFF") s += 35;

    // bye stacking
    if (p.b && (bc[p.b]||0) >= 4){ s -= 55; con.push(`you already have ${bc[p.b]} on the wk-${p.b} bye`); }
    // NFL team stacking
    if ((tc[p.t]||0) >= 2){ s -= 75; con.push(`you already have ${tc[p.t]} ${p.t} players`); }

    return {p, s, why: pro.concat(con)};
  });

  scored.sort((a,b) => b.s - a.s);
  return scored.slice(0, 5);
}

/* ---------- warnings ---------- */
function warnings(){
  const R = roster(), bc = byeCounts(), tc = teamCounts();
  const rd = Math.floor(picksMade() / teams()) + 1;
  const w = [];
  for (const [t,n] of Object.entries(tc))
    if (n >= 3) w.push([`<b>${n} ${t} players.</b> One bad Sunday for that offense is an elimination, not a bad week.`, false]);
  for (const [wk,n] of Object.entries(bc))
    if (n >= 4) w.push([`<b>${n} players on the Week ${wk} bye.</b> Plan FAAB for it — or draft around it now.`, true]);
  const bad = R.m.filter(p => p.g === "RISK" || p.g === "AVOID").length;
  if (R.m.length >= 6 && bad / R.m.length > 0.45)
    w.push([`<b>${bad} of your ${R.m.length} picks are RISK or AVOID.</b> This roster is built to boom and bust. Take floor with your next pick.`, true]);
  if (rd >= 9 && R.cnt.TE === 0)
    w.push([`<b>No tight end and it's round ${rd}.</b> Only ~18 are startable in an 18-team league. Do not leave this one late.`, false]);
  if (rd >= 13 && R.cnt.QB === 0)
    w.push([`<b>No quarterback and it's round ${rd}.</b> Take one now.`, false]);
  if (rd >= 14 && R.cnt.RB < 3)
    w.push([`<b>Only ${R.cnt.RB} running backs.</b> One injury and you're starting a free agent in Week 2.`, true]);
  const noData = R.m.filter(p => !p.s).length;
  if (noData >= 4)
    w.push([`<b>${noData} of your picks have no 2025 NFL production.</b> That's a lot of projection on a roster that has to survive Week 1.`, true]);
  return w;
}

/* ---------- render ---------- */
function render(){
  const q = qs.trim().toLowerCase();
  let rows = D.filter(p => {
    if (fp !== "ALL" && p.p !== fp) return false;
    if (fg && p.g !== fg) return false;
    if (hideTaken && st[p.r] === "taken") return false;
    if (q && !(p.n.toLowerCase().includes(q) || p.t.toLowerCase().includes(q))) return false;
    return true;
  });
  const k = sortKey;
  rows.sort((a,b) => {
    let av, bv;
    if (k === "r"){ av=a.r; bv=b.r; }
    else if (k === "pr"){ av=a.p+String(a.r).padStart(4,"0"); bv=b.p+String(b.r).padStart(4,"0"); }
    else if (k === "b"){ av=a.b||99; bv=b.b||99; }
    else { av = a.s ? a.s[k] : -1; bv = b.s ? b.s[k] : -1; }
    if (av < bv) return -1*sortDir; if (av > bv) return 1*sortDir; return 0;
  });

  let h = "";
  for (const p of rows){
    const s = st[p.r] || "";
    const stat = p.s;
    const fl = p.flag ? `<span class="flag ${p.flag}">${p.flag==="R"?"NO '25":"NEW TM"}</span>` : "";
    h += `<tr class="${s}" data-r="${p.r}">`
      + `<td class="rk">${p.r}</td>`
      + `<td><span class="nm">${p.n}</span><span class="tm">${p.t}</span>${fl}</td>`
      + `<td class="pr">${p.pr}</td><td class="by">${p.b||"—"}</td>`
      + `<td class="gc"><span class="g ${p.g}">${p.g}</span></td>`
      + `<td class="num${stat?"":" dim"}">${stat?stat.ppg.toFixed(1):"—"}</td>`
      + `<td class="num t${stat?"":" dim"}">${stat?stat.sp+"%":"—"}</td>`
      + `<td class="num b${stat?"":" dim"}">${stat?stat.bs+"%":"—"}</td>`
      + `<td class="nt">${p.note||""}</td>`
      + `<td class="act"><button class="star" data-mine="${p.r}" title="I drafted him">★</button></td></tr>`;
  }
  $("#tb").innerHTML = h;

  // header pills
  const made = picksMade(), t = teams();
  $("#pk").textContent = made + 1;
  $("#rd").textContent = Math.floor(made / t) + 1;
  $("#rc").textContent = mine().length;
  const np = nextPick();
  $("#nextp").innerHTML = np
    ? `your pick: <b>#${np}</b> ${np - made - 1 === 0 ? "— you're up" : `· ${np - made - 1} away`}`
    : `<b>draft complete</b>`;

  // suggestions
  $("#sugs").innerHTML = suggest().map(({p, why}) =>
    `<div class="sug" data-mine="${p.r}">
      <div class="sn">${p.n}<small>${p.pr} · ${p.t} · #${p.r}</small></div>
      <div class="sr">${why.slice(0,3).join(" · ") || "best available"}</div>
    </div>`).join("") || `<div class="ok">Nothing left.</div>`;

  // warnings
  const w = warnings();
  $("#warns").innerHTML = w.length
    ? w.map(([t2, amb]) => `<div class="warn${amb?" amb":""}">${t2}</div>`).join("")
    : `<div class="ok">Nothing wrong with this roster yet.</div>`;

  // lineup
  const R = roster();
  const pick = (pos, n) => R.m.filter(p => p.p === pos)[n];
  const cell = (lb, p) => `<div class="slot${p?"":" empty"}"><div class="lb">${lb}</div>
    <div class="vl">${p ? p.n : "—"}</div></div>`;
  const used = new Set();
  const take = (pos, n) => { const p = pick(pos, n); if (p) used.add(p.r); return p; };
  const qb = take("QB",0), rb1 = take("RB",0), rb2 = take("RB",1),
        wr1 = take("WR",0), wr2 = take("WR",1), te = take("TE",0);
  const flex = R.m.find(p => !used.has(p.r) && p.p !== "QB");
  if (flex) used.add(flex.r);
  $("#slots").innerHTML = cell("QB",qb)+cell("RB1",rb1)+cell("RB2",rb2)
    + cell("WR1",wr1)+cell("WR2",wr2)+cell("TE",te)+cell("FLEX",flex);
  const bn = R.m.filter(p => !used.has(p.r));
  $("#bench").innerHTML = bn.length
    ? `<b style="color:var(--tx2)">Bench (${bn.length}/7):</b> ${bn.map(p=>p.n).join(", ")}`
    : `<b style="color:var(--tx3)">Bench empty</b>`;

  // scarcity
  const sc = scarcity();
  $("#scar").innerHTML = ["RB","WR","TE","QB"].map(pos => {
    const {left, total} = sc[pos];
    const pct = total ? left/total*100 : 0;
    const cls = pct < 15 ? "crit" : pct < 35 ? "low" : "";
    return `<div class="scar"><span class="lb">${pos}</span>
      <span class="bar"><i class="${cls}" style="width:${pct}%"></i></span>
      <span class="vl">${left}/${total}</span></div>`;
  }).join("");
}

/* ---------- actions ---------- */
function setState(r, v){
  hist.push({...st});
  if (st[r] === v) delete st[r]; else st[r] = v;
  save();
  render();
}
$("#tb").addEventListener("click", e => {
  const b = e.target.closest("button.star");
  if (b){ setState(+b.dataset.mine, "mine"); return; }
  const tr = e.target.closest("tr"); if (!tr) return;
  setState(+tr.dataset.r, "taken");
});
$("#sugs").addEventListener("click", e => {
  const d = e.target.closest(".sug"); if (d) setState(+d.dataset.mine, "mine");
});
document.querySelectorAll("button.f").forEach(b => b.addEventListener("click", () => {
  if (b.dataset.p){ fp = b.dataset.p;
    document.querySelectorAll("button.f[data-p]").forEach(x => x.classList.toggle("on", x === b));
  } else if (b.dataset.g){ const g = b.dataset.g; fg = (fg === g) ? null : g;
    document.querySelectorAll("button.f[data-g]").forEach(x => x.classList.toggle("on", x.dataset.g === fg));
  } else { hideTaken = !hideTaken; b.classList.toggle("on", hideTaken); }
  render();
}));
document.querySelectorAll("thead th[data-s]").forEach(th => th.addEventListener("click", () => {
  const k = th.dataset.s;
  if (sortKey === k) sortDir *= -1;
  else { sortKey = k; sortDir = (k === "r" || k === "pr" || k === "b") ? 1 : -1; }
  render();
}));
$("#q").addEventListener("input", e => { qs = e.target.value; render(); });
$("#q").addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  const first = $("#tb tr"); if (!first) return;
  setState(+first.dataset.r, e.shiftKey ? "mine" : "taken");
  $("#q").value = ""; qs = ""; render();
});
$("#undo").addEventListener("click", () => { if (hist.length){ st = hist.pop(); save(); render(); } });
$("#reset").addEventListener("click", () => {
  if (picksMade() && !confirm("Clear the whole draft?")) return;
  hist.push({...st}); st = {}; save(); render();
});
["slot","teams"].forEach(id => $("#"+id).addEventListener("input", () => { save(); render(); }));

fetch("/players.json")
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(data => {
    D = data;
    D.forEach(p => byName[p.r] = p);
    load();
    render();
  })
  .catch(() => { $("#tb").innerHTML = "<tr><td colspan=\"10\">Could not load player board.</td></tr>"; });
</script></body></html>"""

open(str(ROOT / "players.json"), "w").write(DATA)
open(str(ROOT / "index.html"), "w").write(HTML)
print("built")
