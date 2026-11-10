#!/usr/bin/env python3
"""Build an .excalidraw architecture diagram (and ARCHITECTURE.md) from a JSON spec.

Usage:
    python build_excalidraw.py spec.json -o docs/architecture/architecture.excalidraw [--lang en|fr] [--open]

Expected spec:
{
  "title": "My system",                          # optional
  "subtitle": "Next.js · Node · PostgreSQL",     # optional
  "nodes": [
    {"id": "web", "label": "Next.js App", "sublabel": "SSR",  # sublabel optional
     "category": "client", "logo": "logos/nextdotjs.svg"},   # logo optional (svg/png/jpg/webp), relative to the spec
    ...
  ],
  "edges": [
    {"from": "web", "to": "api", "label": "REST"},
    {"from": "api", "to": "queue", "label": "event", "dashed": true},   # dashed optional
    {"from": "bot", "to": "telegram", "label": "polling", "both": true}, # both: arrowheads on both ends
    ...
  ],
  "platform": {                                  # optional: "hosted on" frame around several categories
    "label": "Dokploy server · Docker containers",
    "logo": "logos/dokploy.svg",
    "categories": ["gateway", "service", "async", "datastore"]
  },
  "columns": [["client"], ["gateway"], ["service"], ["async", "datastore"], ["external"]],  # optional
  "decisions": ["No Nginx: Traefik + WhiteNoise are enough", ...],  # optional, copied into ARCHITECTURE.md
  "evolutions": ["PgBouncer beyond 50 active tenants", ...]         # optional, same
}

The script also writes ARCHITECTURE.md next to the spec (components, flows, decisions) for developers
and AI agents, who do not read Excalidraw JSON well. Only the generated block is replaced on re-run:
hand-written notes are kept. --doc-only updates the document without rewriting the .excalidraw.
--lang (en|fr) sets the language of zone titles, legend and ARCHITECTURE.md headings.

Categories: client, gateway, api, service, async, datastore, external.
`api` (optional) is for layers between the edge and business services: BFF, GraphQL gateway, SSR.
By default `async` and `datastore` share one column, so services reach both without crossing a column.
Edges touching `async` or `external` are dashed automatically.

Layout:
- label "Name — detail" or "Name (detail)" → name + subtitle on two lines (or use `sublabel`);
- node width computed from the longest label of the column;
- node order inside each zone chosen to minimise crossings (barycentre + search);
- orthogonal arrows: each vertical segment gets its own lane in the gap between two columns,
  attachment points are spread along the node edge, and an arrow that skips a column goes through
  a corridor above or below the zones instead of crossing them;
- edge labels on a white background, placed where they do not overlap.
"""
from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import itertools
import json
import random
import sys
import time
from pathlib import Path

CATEGORIES = ["client", "gateway", "api", "service", "async", "datastore", "external"]
DEFAULT_COLUMNS = [["client"], ["gateway"], ["api"], ["service"], ["async", "datastore"], ["external"]]
I18N = {
    "en": {
        "client": "Clients", "gateway": "Gateway / Edge", "api": "API / Presentation",
        "service": "Services", "async": "Async / Messaging", "datastore": "Data",
        "external": "External services",
        "legend_sync": "synchronous call", "legend_async": "asynchronous / external service",
        "components": "Components", "category": "Category", "component": "Component", "detail": "Detail",
        "hosting": "Hosting: **{label}** (contains: {cats}).", "flows": "Flows",
        "asynchronous": "asynchronous", "external_service": "external service",
        "dashed": "dashed: indirect or unverified",
        "decisions": "Decisions", "evolutions": "Planned evolutions",
        "diagram": "Diagram", "source": "source",
        "notes_comment": "<!-- Free hand-written notes: kept when the script is re-run. -->",
    },
    "fr": {
        "client": "Clients", "gateway": "Gateway / Edge", "api": "API / Présentation",
        "service": "Services", "async": "Async / Messaging", "datastore": "Données",
        "external": "Services externes",
        "legend_sync": "appel synchrone", "legend_async": "asynchrone / service externe",
        "components": "Briques", "category": "Catégorie", "component": "Brique", "detail": "Détail",
        "hosting": "Hébergement : **{label}** (contient : {cats}).", "flows": "Flux",
        "asynchronous": "asynchrone", "external_service": "service externe",
        "dashed": "pointillé : indirect ou non vérifié",
        "decisions": "Décisions", "evolutions": "Évolutions prévues",
        "diagram": "Diagramme", "source": "source",
        "notes_comment": "<!-- Notes libres écrites à la main : elles sont conservées quand le script est relancé. -->",
    },
}
LANG = "en"


def tr(key: str) -> str:
    """Translated string for the current --lang."""
    return I18N[LANG][key]


def cat_title(c: str) -> str:
    return I18N[LANG][c]
# (zone background, node border colour, node background)
PALETTE = {
    "client": ("#e7f5ff", "#1971c2", "#ffffff"),
    "gateway": ("#f3f0ff", "#6741d9", "#ffffff"),
    "api": ("#e3fafc", "#0c8599", "#ffffff"),
    "service": ("#ebfbee", "#2f9e44", "#ffffff"),
    "async": ("#fff4e6", "#e8590c", "#ffffff"),
    "datastore": ("#fff9db", "#f08c00", "#ffffff"),
    "external": ("#f8f9fa", "#495057", "#ffffff"),
}

# Geometry (px)
NODE_MIN_W = 210
NODE_H = 72          # node without subtitle
NODE_H_SUB = 84      # node with subtitle
LOGO = 40
PAD_X = 16
FS_LABEL = 18
FS_SUB = 13
FS_EDGE = 14
CHAR_W = 0.6         # average char width / font size (deliberately generous)
PORT_GAP = 30        # spacing between two attachment points on one edge
ROW_GAP = 44         # between two nodes of a zone
ZONE_PAD = 22
ZONE_TITLE_H = 38
ZONE_GAP = 34        # between two zones stacked in a column
GAP_MIN = 100        # minimum gap between two columns
LANE_W = 28          # spacing between two vertical lanes
LABEL_PAD = 14
CORR_OFF = 30        # distance between zones and the first corridor
CORR_SP = 34         # spacing between two corridors
FRAME_PAD = 26
FRAME_TITLE_H = 58
ARROW_GAP = 4
HEADER_H = 100

EDGE_COLOR = "#495057"
TEXT_MUTED = "#868e96"

MIME = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

NOW = int(time.time() * 1000)
_rng = random.Random(42)


def _seed() -> int:
    return _rng.randint(1, 2**31 - 1)


def tw(text: str, size: float) -> float:
    return len(text) * size * CHAR_W


def base(el_id: str, el_type: str, x: float, y: float, w: float, h: float, **kw) -> dict:
    el = {
        "id": el_id,
        "type": el_type,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": _seed(),
        "version": 1,
        "versionNonce": _seed(),
        "isDeleted": False,
        "boundElements": [],
        "updated": NOW,
        "link": None,
        "locked": False,
    }
    el.update(kw)
    return el


def text_el(el_id: str, x: float, y: float, text: str, size: float = FS_LABEL, **kw) -> dict:
    lines = text.split("\n")
    w = max(len(l) for l in lines) * size * 0.55
    h = len(lines) * size * 1.25
    el = base(el_id, "text", x, y, w, h)
    el.update(
        {
            "text": text,
            "originalText": text,
            "fontSize": size,
            "fontFamily": 2,  # Helvetica (readable for architecture diagrams)
            "textAlign": "left",
            "verticalAlign": "top",
            "containerId": None,
            "lineHeight": 1.25,
            "autoResize": True,
        }
    )
    el.update(kw)
    return el


@functools.lru_cache(maxsize=None)
def load_logo(path: Path) -> tuple[str, dict] | None:
    """Return (fileId, files entry), or None if the file is not a valid image."""
    if not path.is_file():
        print(f"[warn] logo not found: {path}", file=sys.stderr)
        return None
    data = path.read_bytes()
    ext = path.suffix.lower()
    mime = MIME.get(ext)
    head = data[:512].lstrip().lower()
    valid = (
        (mime == "image/svg+xml" and (head.startswith(b"<svg") or head.startswith(b"<?xml")) and b"<svg" in data[:4096].lower())
        or (mime == "image/png" and data.startswith(b"\x89PNG"))
        or (mime == "image/jpeg" and data.startswith(b"\xff\xd8"))
        or (mime == "image/webp" and data[8:12] == b"WEBP")
    )
    if not valid:
        print(f"[warn] {path} is not a valid {ext} image — skipped", file=sys.stderr)
        return None
    file_id = hashlib.sha1(data).hexdigest()
    entry = {
        "mimeType": mime,
        "id": file_id,
        "dataURL": f"data:{mime};base64,{base64.b64encode(data).decode()}",
        "created": NOW,
        "lastRetrieved": NOW,
    }
    return file_id, entry


def split_label(n: dict) -> tuple[str, str | None]:
    label, sub = n["label"], n.get("sublabel")
    if sub is None:
        if " — " in label:
            label, sub = label.split(" — ", 1)
        elif label.endswith(")") and " (" in label:
            i = label.rindex(" (")
            label, sub = label[:i], label[i + 2:-1]
    return label.strip(), (sub.strip() if sub else None)


# ---------------------------------------------------------------------------
# Order of vertical lanes inside a gap between columns
# ---------------------------------------------------------------------------

def _crossings(order: list[int], entries: list[dict]) -> int:
    pos = {k: i for i, k in enumerate(order)}
    n = 0
    for e in entries:
        xe = pos[e["k"]]
        for f in entries:
            if f is e:
                continue
            xf = pos[f["k"]]
            lo, hi = sorted((f["p"][0][0], f["p"][1][0]))
            for y, side in e["p"]:
                if side is None:
                    continue
                if lo < y < hi and ((side == "L" and xf < xe) or (side == "R" and xf > xe)):
                    n += 1
                # two overlapping horizontals at the same height would read as a single arrow
                for yf, sf in f["p"]:
                    if sf and abs(y - yf) < 1 and (
                        sf == side or (side == "L" and sf == "R" and xf < xe)
                        or (side == "R" and sf == "L" and xf > xe)
                    ):
                        n += 3
    return n


def order_lanes(entries: list[dict]) -> list[int]:
    keys = [e["k"] for e in entries]
    if len(keys) <= 1:
        return keys
    if len(keys) <= 7:
        return list(min(itertools.permutations(keys), key=lambda o: _crossings(list(o), entries)))
    # Beyond that: local search by swaps from a few starting orders
    best, best_c = None, None
    starts = [
        [e["k"] for e in sorted(entries, key=lambda e: e["p"][0][0])],
        [e["k"] for e in sorted(entries, key=lambda e: -e["p"][0][0])],
        [e["k"] for e in sorted(entries, key=lambda e: e["p"][1][0])],
    ]
    for order in starts:
        c = _crossings(order, entries)
        improved = True
        while improved:
            improved = False
            for i in range(len(order)):
                for j in range(i + 1, len(order)):
                    order[i], order[j] = order[j], order[i]
                    c2 = _crossings(order, entries)
                    if c2 < c:
                        c, improved = c2, True
                    else:
                        order[i], order[j] = order[j], order[i]
        if best_c is None or c < best_c:
            best, best_c = list(order), c
    return best


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def _score(R: list[dict]) -> tuple[int, int, float]:
    """(arrow crossings, arrows going back up a column, total length) — smaller = more readable."""
    upward = sum(1 for r in R if r["kind"] == "vert" and r["sa"] == "T")
    segs = []
    for r in R:
        for (x1, y1), (x2, y2) in zip(r["pts"], r["pts"][1:]):
            segs.append((r["i"], x1, y1, x2, y2))
    crossings = 0
    for i, ax1, ay1, ax2, ay2 in segs:
        if abs(ay1 - ay2) > 0.5:
            continue  # start from horizontal segments
        hx0, hx1, hy = min(ax1, ax2), max(ax1, ax2), ay1
        for j, bx1, by1, bx2, by2 in segs:
            if j == i or abs(bx1 - bx2) > 0.5:
                continue
            vy0, vy1, vx = min(by1, by2), max(by1, by2), bx1
            if hx0 + 1 < vx < hx1 - 1 and vy0 + 1 < hy < vy1 - 1:
                crossings += 1
        # overlapping horizontal segments (same height, overlapping ranges)
        for j, bx1, by1, bx2, by2 in segs:
            if j == i or abs(by1 - by2) > 0.5 or abs(by1 - hy) > 1:
                continue
            if min(hx1, max(bx1, bx2)) - max(hx0, min(bx1, bx2)) > 2:
                crossings += 3
    length = sum(abs(x2 - x1) + abs(y2 - y1) for _, x1, y1, x2, y2 in segs)
    return crossings, upward, length


def build(spec: dict, spec_dir: Path) -> dict:
    """Try the possible node orders in each zone and keep the one with the fewest crossings."""
    doc, R, zones = _build(spec, spec_dir, None)  # barycentre order
    best = (_score(R), doc)
    cats = [c for c in zones if len(zones[c]) > 1]
    n_combos = 1
    for c in cats:
        for k in range(2, len(zones[c]) + 1):
            n_combos *= k
    if 1 < n_combos <= 720:
        for combo in itertools.product(*(itertools.permutations(zones[c]) for c in cats)):
            order = dict(zones)
            order.update({c: list(p) for c, p in zip(cats, combo)})
            d, R2, _ = _build(spec, spec_dir, order)
            s = _score(R2)
            if s < best[0]:
                best = (s, d)
    elif n_combos > 720:
        # Too many combinations: optimise one zone at a time, the others fixed
        order = {c: list(v) for c, v in zones.items()}
        for _ in range(2):
            for c in cats:
                if len(order[c]) > 6:
                    continue
                for p in itertools.permutations(order[c]):
                    trial = dict(order)
                    trial[c] = list(p)
                    d, R2, _ = _build(spec, spec_dir, trial)
                    s = _score(R2)
                    if s < best[0]:
                        best, order = (s, d), trial
    return best[1]


def _build(spec: dict, spec_dir: Path, order: dict | None) -> tuple[dict, list[dict], dict]:
    nodes = spec["nodes"]
    edges = spec.get("edges", [])
    byid: dict[str, dict] = {}
    for n in nodes:
        if n["category"] not in CATEGORIES:
            sys.exit(f"Unknown category '{n['category']}' for node '{n['id']}'. Expected: {CATEGORIES}")
        if n["id"] in byid:
            sys.exit(f"Identifiant de nœud en double : '{n['id']}'")
        byid[n["id"]] = n
    for e in edges:
        for k in ("from", "to"):
            if e[k] not in byid:
                sys.exit(f"Edge {e}: node '{e[k]}' does not exist")
        if e["from"] == e["to"]:
            sys.exit(f"Edge {e}: self-loops are not supported")

    columns_spec = spec.get("columns", DEFAULT_COLUMNS)
    placed = {c for g in columns_spec for c in g}
    for n in nodes:
        if n["category"] not in placed:
            sys.exit(f"Category '{n['category']}' is not in any column of 'columns'")
    col_cats = [[c for c in g if any(n["category"] == c for n in nodes)] for g in columns_spec]
    col_cats = [g for g in col_cats if g]
    ncols = len(col_cats)
    col = {n["id"]: next(i for i, g in enumerate(col_cats) if n["category"] in g) for n in nodes}
    zones = {c: [n["id"] for n in nodes if n["category"] == c] for g in col_cats for c in g}
    if order:
        zones = {c: list(order[c]) for c in zones}

    def col_nodes(ci: int) -> list[str]:
        return [nid for c in col_cats[ci] for nid in zones[c]]

    # 1. Node order inside each zone (barycentre heuristic) ----------------------
    nbrs: dict[str, list[str]] = {nid: [] for nid in byid}
    for e in edges:
        nbrs[e["from"]].append(e["to"])
        nbrs[e["to"]].append(e["from"])
    for sweep in range(0 if order else 8):
        seq = range(ncols) if sweep % 2 == 0 else range(ncols - 1, -1, -1)
        for ci in seq:
            pos = {}
            for cj in range(ncols):
                lst = col_nodes(cj)
                for k, nid in enumerate(lst):
                    pos[nid] = (k + 0.5) / len(lst)
            for c in col_cats[ci]:
                def key(nid: str, pos=pos, ci=ci) -> float:
                    other = [pos[m] for m in nbrs[nid] if col[m] != ci]
                    return sum(other) / len(other) if other else pos[nid]
                zones[c].sort(key=key)

    # 2. Type of each edge and node sides used -----------------------------------
    R: list[dict] = []
    for i, e in enumerate(edges):
        a, b = e["from"], e["to"]
        ca, cb = col[a], col[b]
        dashed = bool(e.get("dashed")) or "async" in (byid[a]["category"], byid[b]["category"]) \
            or "external" in (byid[a]["category"], byid[b]["category"])
        r = {"i": i, "a": a, "b": b, "label": e.get("label", ""), "dashed": dashed, "straight": False,
             "both": bool(e.get("both"))}
        if ca < cb:
            r["kind"] = "fwd" if cb == ca + 1 else "corr"
            r["sa"], r["sb"] = "R", "L"
        elif ca > cb:
            r["kind"] = "bwd" if ca == cb + 1 else "corr"
            r["sa"], r["sb"] = "L", "R"
        else:
            lst = col_nodes(ca)
            ia, ib = lst.index(a), lst.index(b)
            if abs(ia - ib) == 1:
                r["kind"] = "vert"
                r["sa"], r["sb"] = ("B", "T") if ia < ib else ("T", "B")
            else:
                r["kind"] = "loop"
                r["sa"], r["sb"] = "R", "R"
        R.append(r)

    sides: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for r in R:
        sides.setdefault((r["a"], r["sa"]), []).append((r["i"], "s"))
        sides.setdefault((r["b"], r["sb"]), []).append((r["i"], "t"))

    # 3. Node sizes ---------------------------------------------------------------
    labels = {nid: split_label(n) for nid, n in byid.items()}
    logos = {nid: (load_logo((spec_dir / n["logo"]).resolve()) if n.get("logo") else None) for nid, n in byid.items()}

    def nports(nid: str, s: str) -> int:
        return len(sides.get((nid, s), []))

    h = {
        nid: max(NODE_H_SUB if labels[nid][1] else NODE_H,
                 PORT_GAP * (max(nports(nid, "L"), nports(nid, "R")) + 1))
        for nid in byid
    }

    def content_w(nid: str) -> float:
        lab, sub = labels[nid]
        text_w = max(tw(lab, FS_LABEL), tw(sub, FS_SUB) if sub else 0)
        return PAD_X + (LOGO + 12 if logos[nid] else 0) + text_w + PAD_X

    W = [max(NODE_MIN_W, max(content_w(nid) for nid in col_nodes(ci))) for ci in range(ncols)]
    ZW = [w + 2 * ZONE_PAD for w in W]

    # 4. Vertical positions (relative to the top of zones) -----------------------
    zone_rel: dict[str, tuple[float, float]] = {}
    node_rel: dict[str, float] = {}
    col_h: list[float] = []
    for ci in range(ncols):
        y = 0.0
        for c in col_cats[ci]:
            ids = zones[c]
            inner = sum(h[n] for n in ids) + ROW_GAP * (len(ids) - 1)
            zh = ZONE_TITLE_H + 2 * ZONE_PAD + inner
            zone_rel[c] = (y, zh)
            ny = y + ZONE_TITLE_H + ZONE_PAD
            for n in ids:
                node_rel[n] = ny
                ny += h[n] + ROW_GAP
            y += zh + ZONE_GAP
        col_h.append(y - ZONE_GAP)
    H = max(col_h)
    off = [(H - col_h[ci]) / 2 for ci in range(ncols)]

    def ny_rel(n: str) -> float:
        return off[col[n]] + node_rel[n]

    def ncy(n: str) -> float:
        return ny_rel(n) + h[n] / 2

    for r in R:
        if r["kind"] == "corr":
            r["corr"] = "top" if (ncy(r["a"]) + ncy(r["b"])) / 2 < H / 2 else "bot"

    def compute_ports() -> dict[tuple[int, str], float]:
        P: dict[tuple[int, str], float] = {}
        for (nid, s), lst in sides.items():
            def key(item, s=s):
                i, end = item
                r = R[i]
                other = r["b"] if end == "s" else r["a"]
                if r["kind"] == "corr":
                    return (-1e9 if r["corr"] == "top" else 1e9, i)
                if s in "LR":
                    return (ncy(other), i)
                return (0, i)
            ordered = sorted(lst, key=key)
            for k, item in enumerate(ordered):
                P[item] = (k - (len(ordered) - 1) / 2) * PORT_GAP
        return P

    def port_y(r: dict, end: str, P: dict) -> float:
        nid = r["a"] if end == "s" else r["b"]
        return ncy(nid) + P[(r["i"], end)]

    def straight_count(P: dict) -> int:
        return sum(1 for r in R if r["kind"] in ("fwd", "bwd") and abs(port_y(r, "s", P) - port_y(r, "t", P)) < 1)

    def facing_collisions(P: dict) -> int:
        """Attachment points of different arrows facing each other at the same height in one gap:
        their horizontals would continue each other and read as a single arrow."""
        by_gap: dict[int, list[tuple[int, float, str]]] = {}
        for r in R:
            ya, yb = port_y(r, "s", P), port_y(r, "t", P)
            if r["kind"] in ("fwd", "bwd") and abs(ya - yb) < 1:
                continue
            for end, nid, s, y in (("s", r["a"], r["sa"], ya), ("t", r["b"], r["sb"], yb)):
                if s == "R":
                    by_gap.setdefault(col[nid], []).append((r["i"], y, "L"))
                elif s == "L" and col[nid] > 0:
                    by_gap.setdefault(col[nid] - 1, []).append((r["i"], y, "R"))
        n = 0
        for items in by_gap.values():
            for i1, y1, s1 in items:
                for i2, y2, s2 in items:
                    if i1 < i2 and s1 != s2 and abs(y1 - y2) < PORT_GAP / 2:
                        n += 1
        return n

    # Shift shorter columns vertically to make as many arrows straight as possible
    for _ in range(3):
        for ci in range(ncols):
            slack = H - col_h[ci]
            if slack <= 0:
                continue
            P = compute_ports()
            cands = {off[ci]} | {off[ci] + k * PORT_GAP / 2 for k in (-2, -1, 1, 2)}
            for r in R:
                if r["kind"] not in ("fwd", "bwd"):
                    continue
                if col[r["a"]] == ci:
                    cands.add(off[ci] + port_y(r, "t", P) - port_y(r, "s", P))
                elif col[r["b"]] == ci:
                    cands.add(off[ci] + port_y(r, "s", P) - port_y(r, "t", P))
            best = None
            saved = off[ci]
            for c in cands:
                if c < -0.01 or c > slack + 0.01:
                    continue
                off[ci] = min(max(c, 0.0), slack)
                Pc = compute_ports()
                k = (-straight_count(Pc), facing_collisions(Pc), abs(off[ci] - slack / 2))
                if best is None or k < best[0]:
                    best = (k, off[ci])
                off[ci] = saved
            off[ci] = best[1]

    P = compute_ports()
    for r in R:
        if r["kind"] in ("fwd", "bwd") and abs(port_y(r, "s", P) - port_y(r, "t", P)) < 1:
            r["straight"] = True

    # 5. Corridors (arrows that skip at least one column) --------------------------
    corr_top = sorted([r for r in R if r["kind"] == "corr" and r["corr"] == "top"],
                      key=lambda r: (abs(col[r["a"]] - col[r["b"]]), r["i"]))
    corr_bot = sorted([r for r in R if r["kind"] == "corr" and r["corr"] == "bot"],
                      key=lambda r: (abs(col[r["a"]] - col[r["b"]]), r["i"]))
    for j, r in enumerate(corr_top):
        r["cy_rel"] = -(CORR_OFF + j * CORR_SP)
    for j, r in enumerate(corr_bot):
        r["cy_rel"] = H + CORR_OFF + j * CORR_SP

    # 6. Vertical lanes in each gap between columns --------------------------------
    # gap gi = space right of column gi (the last one hosts loops of the last column)
    gaps: dict[int, list[dict]] = {gi: [] for gi in range(ncols)}

    def add_lane(gi: int, key: tuple[int, int], p1: tuple, p2: tuple) -> None:
        gaps[gi].append({"k": key, "p": (p1, p2)})

    for r in R:
        k = r["kind"]
        ca, cb = col[r["a"]], col[r["b"]]
        ya, yb = port_y(r, "s", P), port_y(r, "t", P)
        if k == "fwd" and not r["straight"]:
            add_lane(ca, (r["i"], 0), (ya, "L"), (yb, "R"))
        elif k == "bwd" and not r["straight"]:
            add_lane(cb, (r["i"], 0), (ya, "R"), (yb, "L"))
        elif k == "loop":
            add_lane(ca, (r["i"], 0), (ya, "L"), (yb, "L"))
        elif k == "corr":
            c = r["cy_rel"]
            if ca < cb:
                add_lane(ca, (r["i"], 0), (ya, "L"), (c, None))
                add_lane(cb - 1, (r["i"], 1), (c, None), (yb, "R"))
            else:
                add_lane(ca - 1, (r["i"], 0), (ya, "R"), (c, None))
                add_lane(cb, (r["i"], 1), (c, None), (yb, "L"))

    lane_rank: dict[tuple[int, int], tuple[int, int]] = {}
    for gi, entries in gaps.items():
        for idx, key in enumerate(order_lanes(entries)):
            lane_rank[key] = (gi, idx)

    # "platform" frame
    platform = spec.get("platform")
    frame_cols: set[int] = set()
    if platform:
        cats = set(platform.get("categories", []))
        frame_cols = {ci for ci in range(ncols) if cats & set(col_cats[ci])}

    def label_box_w(text: str) -> float:
        return tw(text, FS_EDGE) + 18

    gap_label_w = {gi: 0.0 for gi in range(ncols)}
    for r in R:
        if not r["label"]:
            continue
        gi = {"fwd": col[r["a"]], "loop": col[r["a"]], "bwd": col[r["b"]]}.get(r["kind"])
        if gi is not None:
            gap_label_w[gi] = max(gap_label_w[gi], label_box_w(r["label"]))

    gap_geo = {}
    for gi in range(ncols):
        in_l = gi in frame_cols
        in_r = (gi + 1) in frame_cols if gi + 1 < ncols else False
        left_res = FRAME_PAD + 12 if in_l and not in_r else 0
        right_res = FRAME_PAD + 12 if in_r and not in_l else 0
        n = len(gaps[gi])
        label_area = gap_label_w[gi] + 2 * LABEL_PAD if gap_label_w[gi] else 0
        lanes_block = (n + 1) * LANE_W if n else 0
        total = left_res + label_area + lanes_block + right_res
        if gi < ncols - 1:
            total = max(GAP_MIN, total)
        gap_geo[gi] = {"left_res": left_res, "right_res": right_res, "label_area": label_area, "n": n, "w": total}

    # 7. Absolute positions -------------------------------------------------------
    X = [0.0]
    for ci in range(ncols - 1):
        X.append(X[ci] + ZW[ci] + gap_geo[ci]["w"])

    y_cursor = HEADER_H if (spec.get("title") or spec.get("subtitle")) else 0
    frame_top = y_cursor
    if platform:
        y_cursor += FRAME_TITLE_H
    if corr_top:
        y_cursor += CORR_OFF + (len(corr_top) - 1) * CORR_SP + 18
    zones_top = y_cursor
    zones_bottom = zones_top + H
    bottom_band = CORR_OFF + (len(corr_bot) - 1) * CORR_SP + 18 if corr_bot else 0

    def node_x(n: str) -> float:
        return X[col[n]] + ZONE_PAD

    def node_y(n: str) -> float:
        return zones_top + ny_rel(n)

    def lane_x(key: tuple[int, int]) -> float:
        gi, idx = lane_rank[key]
        g = gap_geo[gi]
        start = X[gi] + ZW[gi] + g["left_res"] + g["label_area"]
        region = g["w"] - g["left_res"] - g["label_area"] - g["right_res"]
        return start + region * (idx + 1) / (g["n"] + 1)

    def label_cx(gi: int) -> float:
        g = gap_geo[gi]
        x0 = X[gi] + ZW[gi] + g["left_res"]
        if g["n"]:
            return x0 + g["label_area"] / 2
        return x0 + (g["w"] - g["left_res"] - g["right_res"]) / 2

    def side_pt(r: dict, end: str) -> tuple[float, float]:
        nid = r["a"] if end == "s" else r["b"]
        s = r["sa"] if end == "s" else r["sb"]
        d = P[(r["i"], end)]
        x0, y0, w, hh = node_x(nid), node_y(nid), W[col[nid]], h[nid]
        if s == "R":
            return (x0 + w + ARROW_GAP, y0 + hh / 2 + d)
        if s == "L":
            return (x0 - ARROW_GAP, y0 + hh / 2 + d)
        if s == "T":
            return (x0 + w / 2 + d, y0 - ARROW_GAP)
        return (x0 + w / 2 + d, y0 + hh + ARROW_GAP)

    for r in R:
        pa, pb = side_pt(r, "s"), side_pt(r, "t")
        k = r["kind"]
        if k in ("fwd", "bwd") and r["straight"]:
            pb = (pb[0], pa[1])
            pts = [pa, pb]
        elif k in ("fwd", "bwd", "loop"):
            lx = lane_x((r["i"], 0))
            pts = [pa, (lx, pa[1]), (lx, pb[1]), pb]
        elif k == "vert":
            if abs(pa[0] - pb[0]) < 1:
                pts = [pa, (pa[0], pb[1])]
            else:
                m = (pa[1] + pb[1]) / 2
                pts = [pa, (pa[0], m), (pb[0], m), pb]
        else:  # corr
            cy = zones_top + r["cy_rel"]
            l1, l2 = lane_x((r["i"], 0)), lane_x((r["i"], 1))
            pts = [pa, (l1, pa[1]), (l1, cy), (l2, cy), (l2, pb[1]), pb]
        r["pts"] = pts

    # Edge label positions
    verticals = []  # (edge index, x, ylo, yhi)
    for r in R:
        for (x1, y1), (x2, y2) in zip(r["pts"], r["pts"][1:]):
            if abs(x1 - x2) < 0.5 and abs(y1 - y2) > 0.5:
                verticals.append((r["i"], x1, min(y1, y2), max(y1, y2)))
    for r in R:
        if not r["label"]:
            continue
        k, pts = r["kind"], r["pts"]
        if k in ("fwd", "loop"):
            r["lbl"] = (label_cx(col[r["a"]]), pts[0][1])
        elif k == "bwd":
            r["lbl"] = (label_cx(col[r["b"]]), pts[-1][1])
        elif k == "vert":
            mid = len(pts) // 2
            (x1, y1), (x2, y2) = pts[mid - 1], pts[mid]
            # next to the line (the gap between two nodes is too short to put the label on it)
            r["lbl"] = ((x1 + x2) / 2 + label_box_w(r["label"]) / 2 + 4, (y1 + y2) / 2)
        else:
            (x1, cy), (x2, _) = pts[2], pts[3]
            half = label_box_w(r["label"]) / 2 + 6
            chosen = None
            for f in (0.5, 0.38, 0.62, 0.26, 0.74, 0.15, 0.85):
                cx = x1 + (x2 - x1) * f
                if not any(i != r["i"] and lo < cy < hi and cx - half < vx < cx + half
                           for i, vx, lo, hi in verticals):
                    chosen = cx
                    break
            r["lbl"] = (chosen if chosen is not None else (x1 + x2) / 2, cy)

    # 8. Excalidraw elements -------------------------------------------------------
    elements: list[dict] = []
    files: dict[str, dict] = {}

    if spec.get("title"):
        elements.append(text_el("title", 0, 0, spec["title"], size=28))
    if spec.get("subtitle"):
        elements.append(text_el("subtitle", 0, 44, spec["subtitle"], size=16, strokeColor=TEXT_MUTED))

    max_y = zones_bottom + bottom_band
    if platform and frame_cols:
        c0, c1 = min(frame_cols), max(frame_cols)
        fx0 = X[c0] - FRAME_PAD
        fx1 = X[c1] + ZW[c1] + FRAME_PAD
        fy1 = zones_bottom + bottom_band + FRAME_PAD
        elements.append(base("platform", "rectangle", fx0, frame_top, fx1 - fx0, fy1 - frame_top,
                             strokeColor=TEXT_MUTED, strokeStyle="dashed", strokeWidth=1,
                             roundness={"type": 3}))
        tx = fx0 + 18
        if platform.get("logo"):
            loaded = load_logo((spec_dir / platform["logo"]).resolve())
            if loaded:
                fid, entry = loaded
                files[fid] = entry
                elements.append(base("platform-logo", "image", tx, frame_top + 14, 28, 28,
                                     strokeColor="transparent", fileId=fid, status="saved",
                                     scale=[1, 1], crop=None))
                tx += 38
        if platform.get("label"):
            elements.append(text_el("platform-title", tx, frame_top + 18, platform["label"], size=18,
                                    strokeColor="#495057"))
        max_y = fy1

    for ci in range(ncols):
        for c in col_cats[ci]:
            zbg, stroke, nbg = PALETTE[c]
            zy, zh = zone_rel[c]
            zx, zy = X[ci], zones_top + off[ci] + zy
            elements.append(base(f"zone-{c}", "rectangle", zx, zy, ZW[ci], zh,
                                 backgroundColor=zbg, strokeColor=stroke, strokeStyle="dashed",
                                 strokeWidth=1, roundness={"type": 3}))
            elements.append(text_el(f"zone-{c}-title", zx + ZONE_PAD, zy + 12, cat_title(c),
                                    size=18, strokeColor=stroke))

    rects: dict[str, dict] = {}
    for nid, n in byid.items():
        ci = col[nid]
        _, stroke, nbg = PALETTE[n["category"]]
        nx, ny, w, hh = node_x(nid), node_y(nid), W[ci], h[nid]
        gid = f"g-{nid}"
        rect = base(f"node-{nid}", "rectangle", nx, ny, w, hh, backgroundColor=nbg,
                    strokeColor=stroke, roundness={"type": 3}, groupIds=[gid])
        rects[nid] = rect
        elements.append(rect)
        text_x = nx + PAD_X
        if logos[nid]:
            fid, entry = logos[nid]
            files[fid] = entry
            elements.append(base(f"logo-{nid}", "image", nx + PAD_X, ny + (hh - LOGO) / 2, LOGO, LOGO,
                                 strokeColor="transparent", groupIds=[gid],
                                 fileId=fid, status="saved", scale=[1, 1], crop=None))
            text_x = nx + PAD_X + LOGO + 12
        lab, sub = labels[nid]
        lh, sh = FS_LABEL * 1.25, (FS_SUB * 1.25 + 3 if sub else 0)
        ty = ny + (hh - lh - sh) / 2
        elements.append(text_el(f"label-{nid}", text_x, ty, lab, groupIds=[gid]))
        if sub:
            elements.append(text_el(f"sublabel-{nid}", text_x, ty + lh + 3, sub, size=FS_SUB,
                                    strokeColor=TEXT_MUTED, groupIds=[gid]))

    label_elements: list[dict] = []
    for r in R:
        aid = f"edge-{r['i']}"
        gid = f"g-{aid}"
        pts = r["pts"]
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs, ys = [p[0] for p in rel], [p[1] for p in rel]
        arrow = base(aid, "arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys),
                     strokeColor=EDGE_COLOR, strokeStyle="dashed" if r["dashed"] else "solid",
                     groupIds=[gid] if r["label"] else [])
        arrow.update({
            "points": rel,
            "lastCommittedPoint": None,
            "startBinding": {"elementId": rects[r["a"]]["id"], "focus": 0, "gap": ARROW_GAP},
            "endBinding": {"elementId": rects[r["b"]]["id"], "focus": 0, "gap": ARROW_GAP},
            "startArrowhead": "arrow" if r["both"] else None,
            "endArrowhead": "arrow",
            "elbowed": False,
        })
        rects[r["a"]]["boundElements"].append({"id": aid, "type": "arrow"})
        rects[r["b"]]["boundElements"].append({"id": aid, "type": "arrow"})
        elements.append(arrow)
        if r["label"]:
            cx, cy = r["lbl"]
            bw, bh = label_box_w(r["label"]), FS_EDGE * 1.25 + 8
            box = base(f"{aid}-lblbox", "rectangle", cx - bw / 2, cy - bh / 2, bw, bh,
                       backgroundColor="#ffffff", strokeColor="transparent", strokeWidth=1,
                       roundness={"type": 3}, groupIds=[gid])
            t = text_el(f"{aid}-label", 0, 0, r["label"], size=FS_EDGE, strokeColor=EDGE_COLOR, groupIds=[gid])
            t.update({"containerId": box["id"], "textAlign": "center", "verticalAlign": "middle"})
            t["x"], t["y"] = cx - t["width"] / 2, cy - t["height"] / 2
            box["boundElements"].append({"id": t["id"], "type": "text"})
            label_elements += [box, t]
    elements += label_elements  # above arrows: the white background hides the line

    # Legend
    ly = max_y + 36
    for k, (dashed, txt) in enumerate([(False, tr("legend_sync")), (True, tr("legend_async"))]):
        lx = k * 260
        leg = base(f"legend-{k}", "arrow", lx, ly, 50, 0, strokeColor=EDGE_COLOR,
                   strokeStyle="dashed" if dashed else "solid")
        leg.update({"points": [[0, 0], [50, 0]], "lastCommittedPoint": None, "startBinding": None,
                    "endBinding": None, "startArrowhead": None, "endArrowhead": "arrow", "elbowed": False})
        elements.append(leg)
        elements.append(text_el(f"legend-{k}-text", lx + 60, ly - 9, txt, size=14, strokeColor=EDGE_COLOR))

    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": files,
    }
    return doc, R, zones


# ---------------------------------------------------------------------------
# Readable documentation (developers and AI agents): ARCHITECTURE.md
# ---------------------------------------------------------------------------

GEN_BEGIN = "<!-- BEGIN GENERATED by build_excalidraw.py from the spec: do not edit here, edit the spec and re-run -->"
GEN_END = "<!-- END GENERATED -->"
# Marker written by earlier (French) versions, still recognised so old documents keep updating.
GEN_BEGIN_LEGACY = "<!-- BEGIN GENERATED par build_excalidraw.py depuis la spec : ne pas modifier ici, modifier la spec et relancer -->"


def _rel(target: Path, base_dir: Path) -> str:
    import os
    return os.path.relpath(target.resolve(), base_dir.resolve()).replace("\\", "/")


def render_doc_block(spec: dict, doc_dir: Path, diagram: Path, spec_path: Path) -> str:
    byid = {n["id"]: n for n in spec["nodes"]}
    cat = {n["id"]: n["category"] for n in spec["nodes"]}
    out = [GEN_BEGIN, ""]
    if spec.get("subtitle"):
        out += [f"> {spec['subtitle']}", ""]
    out += [f"{tr('diagram')}: [{diagram.name}]({_rel(diagram, doc_dir)}) · {tr('source')}: "
            f"[{spec_path.name}]({_rel(spec_path, doc_dir)})", ""]

    out += [f"## {tr('components')}", "", f"| {tr('category')} | {tr('component')} | {tr('detail')} |", "|---|---|---|"]
    for c in CATEGORIES:
        for n in spec["nodes"]:
            if n["category"] == c:
                lab, sub = split_label(n)
                out.append(f"| {cat_title(c)} | **{lab}** | {sub or '—'} |")
    out.append("")
    platform = spec.get("platform")
    if platform:
        cats = ", ".join(cat_title(c) for c in platform.get("categories", []) if c in CATEGORIES)
        out += [tr("hosting").format(label=platform.get("label", ""), cats=cats), ""]

    out += [f"## {tr('flows')}", ""]
    for e in spec.get("edges", []):
        a, b = byid[e["from"]], byid[e["to"]]
        arrow = "↔" if e.get("both") else "→"
        cats = {cat[e["from"]], cat[e["to"]]}
        tags = [e["label"]] if e.get("label") else []
        if "async" in cats:
            tags.append(tr("asynchronous"))
        if "external" in cats:
            tags.append(tr("external_service"))
        if e.get("dashed") and not cats & {"async", "external"}:
            tags.append(tr("dashed"))
        out.append(f"- **{split_label(a)[0]}** {arrow} **{split_label(b)[0]}**" + (f": {' · '.join(tags)}" if tags else ""))
    out.append("")

    for key in ("decisions", "evolutions"):
        items = spec.get(key)
        if items:
            out += [f"## {tr(key)}", ""] + [f"- {x}" for x in items] + [""]
    out.append(GEN_END)
    return "\n".join(out)


def write_doc(doc_path: Path, spec: dict, diagram: Path, spec_path: Path) -> None:
    """Create or update the document. Only the generated block is replaced; hand-written notes are kept."""
    block = render_doc_block(spec, doc_path.parent, diagram, spec_path)
    if doc_path.is_file():
        text = doc_path.read_text(encoding="utf-8")
        begin = GEN_BEGIN if GEN_BEGIN in text else GEN_BEGIN_LEGACY
        if begin in text and GEN_END in text:
            head, rest = text.split(begin, 1)
            _, tail = rest.split(GEN_END, 1)
            text = head + block + tail
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
    else:
        title = spec.get("title") or "Architecture"
        text = f"# {title}\n\n{block}\n\n## Notes\n\n{tr('notes_comment')}\n"
    doc_path.write_text(text, encoding="utf-8")
    print(f"Doc: {doc_path}")


def default_doc_path(spec_path: Path) -> Path:
    stem = spec_path.stem
    if stem == "spec":
        return spec_path.parent / "ARCHITECTURE.md"
    return spec_path.parent / f"ARCHITECTURE-{stem.removeprefix('spec-')}.md"


def main() -> None:
    global LANG
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("architecture.excalidraw"))
    ap.add_argument("--lang", choices=sorted(I18N), default="en",
                    help="language of zone titles, legend and ARCHITECTURE.md headings (default: en)")
    ap.add_argument("--open", action="store_true",
                    help="open the result in VS Code (Excalidraw extension), or else the default application")
    ap.add_argument("--doc", type=Path, default=None,
                    help="path of the Markdown document (default: ARCHITECTURE.md next to the spec)")
    ap.add_argument("--no-doc", action="store_true", help="do not write the Markdown document")
    ap.add_argument("--doc-only", action="store_true",
                    help="only update the document, do not rewrite the .excalidraw (keeps manual edits)")
    args = ap.parse_args()
    LANG = args.lang
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if not args.doc_only:
        doc = build(spec, args.spec.parent)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        n_logos = len(doc["files"])
        print(f"OK: {args.output} ({len(spec['nodes'])} nodes, {len(spec.get('edges', []))} edges, {n_logos} logos)")
    if not args.no_doc:
        write_doc(args.doc or default_doc_path(args.spec), spec, args.output, args.spec)
    if args.open:
        open_file(args.output.resolve())


def open_file(path: Path) -> None:
    """Open the diagram in VS Code if possible (pomdtr.excalidraw-editor extension), else the default app."""
    import os
    import shutil
    import subprocess
    code = shutil.which("code")
    if code:
        subprocess.Popen(f'"{code}" "{path}"', shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Opened in VS Code: {path}")
    elif hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        print(f"Opened with the default application: {path}")
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, str(path)])
        print(f"Opened with {opener}: {path}")


if __name__ == "__main__":
    main()
