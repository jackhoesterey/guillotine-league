/* Live Sleeper brief / gameday for the static site.
 * Ports src/core/faab.py and src/core/survival.py. Does not fetch /players/nfl (~5–14MB).
 * Never auto-submits a bid. Missing scores/inactives stay UNVERIFIED.
 */
(function (global) {
  "use strict";

  var API = "https://api.sleeper.app/v1";
  var SPEND_CURVE = [
    [1, 4, 850, "Survive — cheap patches only"],
    [5, 9, 650, "Navigate — spend on chaos/bye weeks, not between them"],
    [10, 13, 300, "Pivot — prices collapse; buy the roster that wins"],
    [14, 17, 0, "Empty the tank — leftover dollars are wasted"]
  ];
  var DEFAULT_BIDS = [25, 44, 77, 121, 153, 201];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  function isoNow() {
    return new Date().toISOString();
  }

  function asInt(v, fallback) {
    var n = parseInt(v, 10);
    return Number.isFinite(n) ? n : fallback;
  }

  function median(nums) {
    if (!nums.length) return null;
    var s = nums.slice().sort(function (a, b) { return a - b; });
    var mid = Math.floor(s.length / 2);
    if (s.length % 2) return s[mid];
    return (s[mid - 1] + s[mid]) / 2;
  }

  async function getJson(url) {
    var r = await fetch(url);
    if (!r.ok) throw new Error(url + " HTTP " + r.status);
    return r.json();
  }

  async function sleeper(path) {
    var fetchedAt = isoNow();
    try {
      var r = await fetch(API + path);
      if (!r.ok) {
        return { ok: false, data: null, fetchedAt: fetchedAt, status: "UNVERIFIED — " + path + ": HTTP " + r.status };
      }
      return { ok: true, data: await r.json(), fetchedAt: fetchedAt, status: "ok" };
    } catch (e) {
      return { ok: false, data: null, fetchedAt: fetchedAt, status: "UNVERIFIED — " + path + ": " + (e.message || e) };
    }
  }

  function remainingForRoster(roster, budget) {
    var used = (roster.settings || {}).waiver_budget_used;
    if (used == null) return budget;
    var usedI = asInt(used, null);
    if (usedI == null) return budget;
    return budget - usedI;
  }

  function remainingMap(rosters, budget) {
    var out = {};
    (rosters || []).forEach(function (r) {
      var rid = asInt(r.roster_id, null);
      if (rid == null) return;
      out[rid] = remainingForRoster(r, budget);
    });
    return out;
  }

  function landscape(remaining, myRosterId, bids) {
    bids = bids || DEFAULT_BIDS;
    var rivals = [];
    Object.keys(remaining).forEach(function (k) {
      if (asInt(k, 0) !== myRosterId) rivals.push(remaining[k]);
    });
    var mine = remaining[myRosterId];
    if (!rivals.length) {
      return {
        my_remaining: mine,
        rivals_alive: 0,
        max_rival: null,
        median_rival: null,
        bids: [],
        status: "UNVERIFIED — no rival budgets"
      };
    }
    var rows = bids.map(function (x) {
      var can = rivals.filter(function (r) { return r > x; }).length;
      return {
        bid: x,
        can_outbid_me: can,
        rivals_alive: rivals.length,
        blurb: "Bid $" + x + " and " + can + " of " + rivals.length + " surviving teams can outbid you."
      };
    });
    var broke = Object.keys(remaining).map(asInt).filter(function (rid) {
      return rid !== myRosterId && remaining[rid] < 50;
    }).sort(function (a, b) { return a - b; });
    return {
      my_remaining: mine,
      rivals_alive: rivals.length,
      max_rival: Math.max.apply(null, rivals),
      median_rival: median(rivals),
      broke: broke,
      bids: rows,
      status: "ok"
    };
  }

  function curveTarget(week) {
    for (var i = 0; i < SPEND_CURVE.length; i++) {
      var row = SPEND_CURVE[i];
      if (week >= row[0] && week <= row[1]) {
        return { week: week, remaining_target: row[2], note: row[3] };
      }
    }
    return { week: week, remaining_target: null, note: "UNVERIFIED — week out of 1–17" };
  }

  function curveVerdict(week, myRemaining, preseason) {
    if (preseason) {
      return {
        week: week,
        remaining_target: null,
        note: "Spend curve starts Week 1",
        verdict: "UNVERIFIED — preseason (league has not started)",
        my_remaining: myRemaining
      };
    }
    var t = curveTarget(week);
    if (myRemaining == null || t.remaining_target == null) {
      t.verdict = "UNVERIFIED";
      t.my_remaining = myRemaining;
      return t;
    }
    var target = t.remaining_target;
    if (myRemaining > target + 150 && week >= 10) {
      t.verdict = "hoarding — the bar is rising and unspent FAAB dies with you";
    } else if (myRemaining < target - 200 && week <= 9) {
      t.verdict = "overspending — you are burning capital in the weeks you were likely to survive anyway";
    } else {
      t.verdict = "on curve";
    }
    t.my_remaining = myRemaining;
    t.delta_vs_target = myRemaining - target;
    return t;
  }

  function winningBidsFromTransactions(transactions) {
    var out = [];
    (transactions || []).forEach(function (tx) {
      var settings = tx.settings || {};
      var bid = settings.waiver_bid;
      var adds = tx.adds || {};
      if (bid == null && !(adds && Object.keys(adds).length)) {
        (tx.waiver_budget || []).forEach(function (move) {
          out.push({
            kind: "trade_faab",
            amount: move.amount,
            sender: move.sender,
            receiver: move.receiver,
            transaction_id: tx.transaction_id,
            status: tx.status,
            week: tx.leg || tx.week
          });
        });
        return;
      }
      if (bid == null) return;
      var playerIds = adds && typeof adds === "object" ? Object.keys(adds) : [];
      out.push({
        kind: "waiver",
        amount: bid,
        player_ids: playerIds,
        roster_id: (tx.roster_ids && tx.roster_ids[0]) || null,
        transaction_id: tx.transaction_id,
        status: tx.status,
        week: tx.leg || tx.week
      });
    });
    return out;
  }

  function priceCurve(bids) {
    var won = (bids || []).filter(function (b) {
      return b.kind === "waiver" && b.amount != null && (b.status == null || b.status === "complete");
    });
    if (!won.length) {
      return { n: 0, median: null, max: null, status: "UNVERIFIED — no winning bids logged yet" };
    }
    var amounts = won.map(function (b) { return asInt(b.amount, 0); }).sort(function (a, b) { return a - b; });
    return {
      n: amounts.length,
      median: median(amounts),
      max: amounts[amounts.length - 1],
      p90: amounts[Math.floor(0.9 * (amounts.length - 1))],
      status: "ok",
      amounts: amounts
    };
  }

  function matchupPoints(m) {
    if (!m || m.points == null) return null;
    var n = Number(m.points);
    return Number.isFinite(n) ? n : null;
  }

  function scoresFromMatchups(matchups) {
    var rows = [];
    var skipped = [];
    (matchups || []).forEach(function (m) {
      var rid = asInt(m.roster_id, null);
      if (rid == null) return;
      var pts = matchupPoints(m);
      if (pts == null) {
        skipped.push(rid);
        return;
      }
      rows.push({ roster_id: rid, points: pts });
    });
    if (!rows.length) {
      return {
        chop_line: null,
        n: 0,
        scores: [],
        skipped: skipped,
        status: "UNVERIFIED — no usable matchup points"
      };
    }
    var anyPositive = rows.some(function (r) { return r.points > 0; });
    if (!anyPositive) {
      return {
        chop_line: null,
        n: rows.length,
        scores: rows,
        skipped: skipped,
        status: "UNVERIFIED — all matchup points are 0 (week not scored yet)"
      };
    }
    var chop = Math.min.apply(null, rows.map(function (r) { return r.points; }));
    return {
      chop_line: chop,
      n: rows.length,
      scores: rows.slice().sort(function (a, b) { return a.points - b.points; }),
      skipped: skipped,
      status: "ok",
      assumption: "all-matchups-with-points"
    };
  }

  function margin(myPoints, chopLine) {
    if (myPoints == null || chopLine == null) {
      return { margin: null, status: "UNVERIFIED — missing score or chop line" };
    }
    var m = myPoints - chopLine;
    var danger = m <= 0 ? "dead" : m < 8 ? "critical" : m < 15 ? "danger" : m < 25 ? "watch" : "safe";
    return { margin: m, my_points: myPoints, chop_line: chopLine, danger: danger, status: "ok" };
  }

  function findMyMatchup(matchups, rosterId) {
    rosterId = asInt(rosterId, null);
    if (rosterId == null) return null;
    for (var i = 0; i < (matchups || []).length; i++) {
      if (asInt(matchups[i].roster_id, 0) === rosterId) return matchups[i];
    }
    return null;
  }

  function usersById(users) {
    var out = {};
    (users || []).forEach(function (u) { out[String(u.user_id)] = u; });
    return out;
  }

  function displayName(roster, byUser) {
    var u = byUser[String(roster.owner_id || "")];
    if (!u) return "UNVERIFIED — no owner";
    return (u.metadata && u.metadata.team_name) || u.display_name || String(u.user_id);
  }

  function resolveMe(cfg, users, rosters) {
    var userId = cfg.user_id || "";
    if (!userId && cfg.username) {
      var want = String(cfg.username).toLowerCase();
      (users || []).forEach(function (u) {
        if ((u.display_name || "").toLowerCase() === want || String(u.user_id) === String(cfg.username)) {
          userId = String(u.user_id || "");
        }
      });
    }
    var rosterId = cfg.my_roster_id != null ? asInt(cfg.my_roster_id, null) : null;
    if (rosterId == null && userId) {
      (rosters || []).forEach(function (r) {
        if (String(r.owner_id) === String(userId)) rosterId = asInt(r.roster_id, null);
      });
    }
    return { user_id: userId, roster_id: rosterId };
  }

  function lookupPlayer(sid, xw, boardBySid) {
    sid = String(sid || "");
    if (!sid || sid === "0") return { sleeper_id: sid, name: null, empty: true };
    var board = (boardBySid || {})[sid] || null;
    var rank = ((xw || {}).by_sleeper_id || {})[sid];
    var rec = rank != null ? (((xw || {}).by_rank || {})[String(rank)] || {}) : {};
    return {
      sleeper_id: sid,
      rank: rank,
      name: (board && board.n) || rec.board_name || rec.full_name || null,
      pos: (board && board.p) || rec.position || null,
      team: (board && board.t) || rec.team || null,
      grade: board && board.g,
      empty: false
    };
  }

  function playerLabel(p) {
    if (!p || p.empty) return "—";
    return p.name || ("UNVERIFIED — Sleeper #" + p.sleeper_id);
  }

  function isPreseason(state, league) {
    var st = (state || {}).season_type;
    var ls = (league || {}).status;
    return st === "pre" || ls === "pre_draft" || ls === "drafting";
  }

  function weekLabel(state, league) {
    var week = asInt((state || {}).display_week || (state || {}).week, null);
    var status = (league || {}).status || "unknown";
    if (isPreseason(state, league)) {
      return { week: week, title: "Preseason", sub: (league && league.name ? league.name + " · " : "") + status + (week != null ? " · NFL week " + week : "") };
    }
    return { week: week, title: "Week " + (week != null ? week : "?"), sub: ((league && league.name) || "") + " · " + status };
  }

  async function loadLive() {
    var cfg;
    try {
      cfg = await getJson("/league.json");
    } catch (e) {
      throw new Error("UNVERIFIED — no league.json (" + e.message + ")");
    }
    if (!cfg || !cfg.league_id) throw new Error("UNVERIFIED — league.json is missing league_id");
    var budget = asInt(cfg.faab_budget, 1000);
    var lid = encodeURIComponent(cfg.league_id);

    var packed = await Promise.all([
      sleeper("/state/nfl"),
      sleeper("/league/" + lid),
      sleeper("/league/" + lid + "/rosters"),
      sleeper("/league/" + lid + "/users"),
      getJson("/crosswalk.json").catch(function () { return null; })
    ]);
    var stateR = packed[0], leagueR = packed[1], rosR = packed[2], usrR = packed[3], xw = packed[4];
    var state = stateR.ok ? stateR.data : {};
    var league = leagueR.ok ? leagueR.data : {};
    var rosters = rosR.ok ? rosR.data : [];
    var users = usrR.ok ? usrR.data : [];
    var week = asInt(state.display_week || state.week, null);
    var extra = await Promise.all([
      week != null ? sleeper("/league/" + lid + "/matchups/" + week) : Promise.resolve({ ok: false, data: [], status: "UNVERIFIED — no week", fetchedAt: isoNow() }),
      week != null ? sleeper("/league/" + lid + "/transactions/" + week) : Promise.resolve({ ok: false, data: [], status: "UNVERIFIED — no week", fetchedAt: isoNow() }),
      sleeper("/players/nfl/trending/add?lookback_hours=24&limit=25")
    ]);
    var muR = extra[0], txR = extra[1], trendR = extra[2];
    var me = resolveMe(cfg, users, rosters);
    return {
      cfg: cfg,
      budget: budget,
      state: state,
      league: league,
      rosters: rosters,
      users: users,
      matchups: muR.ok ? muR.data : [],
      transactions: txR.ok ? txR.data : [],
      trending: trendR.ok ? trendR.data : [],
      xw: xw || {},
      me: me,
      week: week,
      preseason: isPreseason(state, league),
      fetched: {
        state: stateR,
        league: leagueR,
        rosters: rosR,
        users: usrR,
        matchups: muR,
        transactions: txR,
        trending: trendR
      },
      builtAt: isoNow()
    };
  }

  function money(n) {
    if (n == null) return "—";
    return "$" + n;
  }

  function statusClass(st) {
    return String(st || "").indexOf("UNVERIFIED") === 0 ? "unv" : "ok";
  }

  function renderBrief(el, live) {
    var label = weekLabel(live.state, live.league);
    var byUser = usersById(live.users);
    var rem = remainingMap(live.rosters, live.budget);
    var myRid = live.me.roster_id;
    var land = myRid != null ? landscape(rem, myRid) : { status: "UNVERIFIED — could not resolve your roster_id", bids: [] };
    var verdict = curveVerdict(live.week || 0, myRid != null ? rem[myRid] : null, live.preseason);
    var chop = scoresFromMatchups(live.matchups);
    var mineMu = myRid != null ? findMyMatchup(live.matchups, myRid) : null;
    var meMargin = margin(matchupPoints(mineMu), chop.chop_line);
    var bids = winningBidsFromTransactions(live.transactions);
    var curve = priceCurve(bids);
    var xw = live.xw || {};

    var faabRows = (live.rosters || []).slice().sort(function (a, b) {
      return remainingForRoster(a, live.budget) - remainingForRoster(b, live.budget);
    }).map(function (r) {
      var rid = asInt(r.roster_id, 0);
      var mine = rid === myRid ? " class=\"mine\"" : "";
      return "<tr" + mine + "><td>" + esc(displayName(r, byUser)) + "</td><td>" + rid + "</td><td>" + esc(money(rem[rid])) + "</td></tr>";
    }).join("");

    var bidBlurbs = (land.bids || []).map(function (b) {
      return "<li>" + esc(b.blurb) + "</li>";
    }).join("") || "<li class=\"unv\">UNVERIFIED — no bid landscape</li>";

    var chopRows = (chop.scores || []).slice(0, 8).map(function (s) {
      var r = (live.rosters || []).filter(function (x) { return asInt(x.roster_id, 0) === s.roster_id; })[0];
      var name = r ? displayName(r, byUser) : ("roster " + s.roster_id);
      var mine = s.roster_id === myRid ? " class=\"mine\"" : "";
      return "<tr" + mine + "><td>" + esc(name) + "</td><td>" + esc(s.points) + "</td></tr>";
    }).join("");

    var trendRows = (live.trending || []).slice(0, 25).map(function (row) {
      var p = lookupPlayer(row.player_id, xw, {});
      return "<tr><td>" + esc(playerLabel(p)) + "</td><td>" + esc(p.pos || "") + " " + esc(p.team || "") + "</td><td>" + esc(row.count) + "</td></tr>";
    }).join("") || "<tr><td colspan=\"3\" class=\"unv\">UNVERIFIED — no trending adds</td></tr>";

    var seasonNote = live.preseason
      ? "<p class=\"banner\">Draft has not started. FAAB remaining is live from Sleeper. Chop line and waiver bids stay <b>UNVERIFIED</b> until Week 1 scores exist.</p>"
      : "";

    var fetchFail = [];
    ["state", "league", "rosters", "users"].forEach(function (k) {
      if (!live.fetched[k].ok) fetchFail.push(live.fetched[k].status);
    });
    var failHtml = fetchFail.length ? "<p class=\"unv\">" + esc(fetchFail.join(" · ")) + "</p>" : "";

    el.innerHTML =
      "<h1>" + esc(label.title) + "</h1>" +
      "<p class=\"muted\">" + esc(label.sub) + " · live from Sleeper " + esc(live.builtAt) +
      (myRid != null ? " · your roster " + myRid : "") + "</p>" +
      seasonNote + failHtml +
      "<div class=\"card\"><h2>FAAB</h2>" +
        "<p class=\"" + statusClass(land.status) + "\">" + esc(land.status === "ok" ? "Live remaining budgets" : land.status) + "</p>" +
        "<p>You have <b>" + esc(money(land.my_remaining)) + "</b> of " + esc(money(live.budget)) +
        ". Rival max " + esc(money(land.max_rival)) + " · median " + esc(money(land.median_rival)) + ".</p>" +
        "<p class=\"" + statusClass(verdict.verdict) + "\">Spend curve: " + esc(verdict.verdict) +
        (verdict.note ? " — " + esc(verdict.note) : "") + "</p>" +
        "<p class=\"muted\">waiver_budget_used treated as dollars until confirmed against a known bid.</p>" +
        "<ul>" + bidBlurbs + "</ul>" +
        "<table><thead><tr><th>Manager</th><th>Roster</th><th>Remaining</th></tr></thead><tbody>" + faabRows + "</tbody></table>" +
      "</div>" +
      "<div class=\"card\"><h2>Chop line</h2>" +
        "<p class=\"" + statusClass(chop.status) + "\">" + esc(chop.status) + "</p>" +
        (chop.chop_line != null ? "<p>Chop line <b>" + esc(chop.chop_line) + "</b> · your margin: " + esc(meMargin.margin != null ? meMargin.margin.toFixed(1) + " (" + meMargin.danger + ")" : meMargin.status) + "</p>" : "") +
        "<p class=\"muted\">Eliminated-roster scoring is unverified. Chop uses every matchup that has points — we do not drop anyone.</p>" +
        (chopRows ? "<table><thead><tr><th>Lowest scores</th><th>Pts</th></tr></thead><tbody>" + chopRows + "</tbody></table>" : "") +
      "</div>" +
      "<div class=\"card\"><h2>Bids</h2>" +
        "<p class=\"" + statusClass(curve.status) + "\">" + esc(curve.status) + "</p>" +
        (curve.n ? "<p>" + curve.n + " completed waiver bids · median " + esc(money(curve.median)) + " · max " + esc(money(curve.max)) + "</p>" : "") +
        "<p class=\"muted\">This page never submits a bid.</p>" +
      "</div>" +
      "<div class=\"card\"><h2>Trending adds (24h)</h2>" +
        "<p class=\"" + statusClass(live.fetched.trending.status) + "\">" + esc(live.fetched.trending.status) + "</p>" +
        "<table><thead><tr><th>Player</th><th>Pos</th><th>Adds</th></tr></thead><tbody>" + trendRows + "</tbody></table>" +
        "<p class=\"muted\">Names come from the draft-board crosswalk. Players not on the 220-name board show as UNVERIFIED Sleeper ids.</p>" +
      "</div>";
  }

  async function renderGameday(el, live) {
    var label = weekLabel(live.state, live.league);
    var myRid = live.me.roster_id;
    var myRoster = null;
    (live.rosters || []).forEach(function (r) {
      if (asInt(r.roster_id, 0) === myRid) myRoster = r;
    });
    var rem = remainingMap(live.rosters, live.budget);
    var xw = live.xw || {};
    var boardBySid = {};
    try {
      var board = await getJson("/players.json");
      (board || []).forEach(function (p) {
        if (p && p.sid) boardBySid[String(p.sid)] = p;
      });
    } catch (e) { /* names still resolve from crosswalk */ }

    var slots = ((live.league || {}).roster_positions || ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]).filter(function (s) {
      return s && s !== "BN";
    });
    var starterIds = (myRoster && myRoster.starters) || [];
    var rows = starterIds.map(function (sid, i) {
      var p = lookupPlayer(sid, xw, boardBySid);
      var slot = slots[i] || ("BN" + i);
      var name = playerLabel(p);
      var unver = !p.name && !p.empty;
      return "<tr><td>" + esc(slot) + "</td><td>" + esc(name) + "</td><td>" + esc(p.pos || "") + " " + esc(p.team || "") +
        "</td><td style=\"font-weight:600;color:" + (unver || p.empty ? "#f85149" : "#e8eaef") + "\">" +
        (p.empty ? "—" : "UNVERIFIED") + "</td><td>—</td><td>" +
        (p.empty ? "empty slot" : "no game-day inactive list") + "</td></tr>";
    }).join("");

    var emptyRoster = !myRoster || !(myRoster.players || []).length;
    var banner = "UNVERIFIED — game-day inactives: ESPN scoreboard/summary/injuries have no inactive list (checked 2026-08-19). Check Sleeper/NFL app 90 minutes before kickoff.";
    if (live.preseason) banner = "UNVERIFIED — league is " + ((live.league || {}).status || "preseason") + ". No Sunday starters yet. " + banner;
    if (!myRoster) banner = "UNVERIFIED — could not resolve your roster. " + banner;

    el.innerHTML =
      "<p>Look with your eyes. This is a checklist, not a decision. Game-day inactives are not automated.</p>" +
      "<p class=\"unv\">" + esc(banner) + "</p>" +
      "<p class=\"muted\">" + esc(label.title) + " · " + esc(label.sub) + " · live from Sleeper " + esc(live.builtAt) +
      (myRid != null ? " · FAAB remaining " + money(rem[myRid]) : "") + "</p>" +
      (emptyRoster ? "<p class=\"muted\">Your Sleeper roster is empty until the draft.</p>" : "") +
      "<table><thead><tr><th>Slot</th><th>Player</th><th>Pos</th><th>Designation</th><th>Kickoff</th><th>Source</th></tr></thead>" +
      "<tbody>" + (rows || "<tr><td colspan=\"6\">UNVERIFIED — no starters</td></tr>") + "</tbody></table>" +
      "<h3>Depth-chart moves</h3>" +
      "<p class=\"muted\">UNVERIFIED in the browser — nflverse depth diffs need <code>python3 src/jobs/gameday_check.py</code> locally. This page does not download Sleeper’s full /players/nfl dump.</p>";
  }

  function fail(el, err) {
    el.innerHTML = "<p class=\"unv\">" + esc(err && err.message ? err.message : err) + "</p>";
  }

  async function bootBrief(el) {
    try {
      var live = await loadLive();
      renderBrief(el, live);
    } catch (e) {
      fail(el, e);
    }
  }

  async function bootGameday(el) {
    try {
      var live = await loadLive();
      await renderGameday(el, live);
    } catch (e) {
      fail(el, e);
    }
  }

  global.GuillotineLive = {
    loadLive: loadLive,
    bootBrief: bootBrief,
    bootGameday: bootGameday,
    remainingMap: remainingMap,
    landscape: landscape,
    curveVerdict: curveVerdict,
    scoresFromMatchups: scoresFromMatchups,
    priceCurve: priceCurve,
    winningBidsFromTransactions: winningBidsFromTransactions
  };
})(typeof window !== "undefined" ? window : globalThis);
