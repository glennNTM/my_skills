#!/usr/bin/env python3
"""Vérifie la lisibilité d'un .excalidraw généré par build_excalidraw.py, sans navigateur.

Usage :
    python check_layout.py docs/architecture/architecture.excalidraw [autre.excalidraw ...]

Compte, pour chaque fichier :
- les croisements entre flèches (segment horizontal × segment vertical) ;
- les superpositions (deux flèches sur le même trait : on croirait une seule flèche) ;
- les étiquettes de flèches qui se chevauchent, ou qui recouvrent un nœud ;
- les flèches qui traversent un nœud.

Repères : 0 superposition, 0 étiquette masquée, 0 flèche à travers un nœud sont attendus.
Quelques croisements (≤ 5) sont acceptables quand des flèches sautent des colonnes.
Code de sortie 1 si l'un des trois critères « attendus » n'est pas respecté.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    segs = []
    for el in d["elements"]:
        if el["type"] == "arrow" and el["id"].startswith("edge-"):
            pts = [(el["x"] + p[0], el["y"] + p[1]) for p in el["points"]]
            segs += [(el["id"], a, b) for a, b in zip(pts, pts[1:])]
    cross = overlap = 0
    for i, (ei, (x1, y1), (x2, y2)) in enumerate(segs):
        for ej, (u1, v1), (u2, v2) in segs[i + 1:]:
            if ei == ej:
                continue
            h1, h2 = abs(y1 - y2) < .5, abs(v1 - v2) < .5
            if h1 and h2 and abs(y1 - v1) < 1 and min(max(x1, x2), max(u1, u2)) - max(min(x1, x2), min(u1, u2)) > 2:
                overlap += 1
            if not h1 and not h2 and abs(x1 - u1) < 1 and min(max(y1, y2), max(v1, v2)) - max(min(y1, y2), min(v1, v2)) > 2:
                overlap += 1
            if h1 != h2:
                (hx1, hy, hx2), (vx, vy1, vy2) = ((x1, y1, x2), (u1, v1, v2)) if h1 else ((u1, v1, u2), (x1, y1, y2))
                if min(hx1, hx2) + 1 < vx < max(hx1, hx2) - 1 and min(vy1, vy2) + 1 < hy < max(vy1, vy2) - 1:
                    cross += 1
    boxes = [e for e in d["elements"] if e["id"].endswith("-lblbox")]
    nodes = [e for e in d["elements"] if e["id"].startswith("node-")]

    def ov(a, b):
        return a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"] \
            and a["y"] < b["y"] + b["height"] and b["y"] < a["y"] + a["height"]

    through = sum(
        1 for _, (x1, y1), (x2, y2) in segs for n in nodes
        if min(x1, x2) < n["x"] + n["width"] - 2 and max(x1, x2) > n["x"] + 2
        and min(y1, y2) < n["y"] + n["height"] - 2 and max(y1, y2) > n["y"] + 2
    )
    return {
        "croisements": cross,
        "superpositions": overlap,
        "étiquettes qui se chevauchent": sum(1 for i, a in enumerate(boxes) for b in boxes[i + 1:] if ov(a, b)),
        "étiquettes sur un nœud": sum(1 for a in boxes for b in nodes if ov(a, b)),
        "flèches à travers un nœud": through,
    }


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    bad = False
    for arg in sys.argv[1:]:
        r = check(Path(arg))
        ok = (r["superpositions"] == 0 and r["étiquettes qui se chevauchent"] == 0
              and r["étiquettes sur un nœud"] == 0 and r["flèches à travers un nœud"] == 0)
        bad |= not ok
        print(f"{'OK ' if ok else 'KO '} {arg} : " + " · ".join(f"{k} {v}" for k, v in r.items()))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
