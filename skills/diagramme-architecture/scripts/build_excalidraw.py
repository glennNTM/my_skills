#!/usr/bin/env python3
"""Construit un fichier .excalidraw (diagramme d'architecture) à partir d'une spec JSON.

Usage :
    python build_excalidraw.py spec.json -o docs/architecture.excalidraw

Spec attendue :
{
  "title": "Mon système",                       # optionnel
  "nodes": [
    {"id": "web", "label": "Next.js App", "category": "client",
     "logo": "logos/nextjs.svg"},              # logo optionnel (svg/png/jpg/webp), chemin relatif à la spec
    ...
  ],
  "edges": [
    {"from": "web", "to": "api", "label": "REST"},
    {"from": "api", "to": "queue", "label": "event", "dashed": true},   # dashed optionnel
    ...
  ]
}

Catégories (colonnes, de gauche à droite) :
    client, gateway, service, async, datastore, external
Les arêtes touchant `async` ou `external` sont pointillées automatiquement.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
import sys
import time
from pathlib import Path

CATEGORIES = ["client", "gateway", "service", "async", "datastore", "external"]
CATEGORY_TITLES = {
    "client": "Clients",
    "gateway": "Gateway / Edge",
    "service": "Services",
    "async": "Async / Messaging",
    "datastore": "Données",
    "external": "Services externes",
}
# (fond de zone, couleur de bordure des nœuds, fond des nœuds)
PALETTE = {
    "client": ("#e7f5ff", "#1971c2", "#ffffff"),
    "gateway": ("#f3f0ff", "#6741d9", "#ffffff"),
    "service": ("#ebfbee", "#2f9e44", "#ffffff"),
    "async": ("#fff4e6", "#e8590c", "#ffffff"),
    "datastore": ("#fff9db", "#f08c00", "#ffffff"),
    "external": ("#f8f9fa", "#495057", "#ffffff"),
}

NODE_W, NODE_H = 240, 80
LOGO = 44
COL_GAP = 140
ROW_GAP = 50
ZONE_PAD = 30
ZONE_TITLE_H = 40
TOP = 80
FONT_SIZE = 18

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


def text_el(el_id: str, x: float, y: float, text: str, size: int = FONT_SIZE, **kw) -> dict:
    lines = text.split("\n")
    w = max(len(l) for l in lines) * size * 0.55
    h = len(lines) * size * 1.25
    el = base(el_id, "text", x, y, w, h)
    el.update(
        {
            "text": text,
            "originalText": text,
            "fontSize": size,
            "fontFamily": 2,  # Helvetica (lisible pour un schéma d'archi)
            "textAlign": "left",
            "verticalAlign": "top",
            "containerId": None,
            "lineHeight": 1.25,
            "autoResize": True,
        }
    )
    el.update(kw)
    return el


def load_logo(path: Path) -> tuple[str, dict] | None:
    """Retourne (fileId, entrée files) ou None si le fichier n'est pas une image valide."""
    if not path.is_file():
        print(f"[warn] logo introuvable : {path}", file=sys.stderr)
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
        print(f"[warn] {path} n'est pas une image {ext} valide — ignoré", file=sys.stderr)
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


def build(spec: dict, spec_dir: Path) -> dict:
    nodes = spec["nodes"]
    edges = spec.get("edges", [])
    ids = {n["id"] for n in nodes}
    for n in nodes:
        if n["category"] not in CATEGORIES:
            sys.exit(f"Catégorie inconnue '{n['category']}' pour le nœud '{n['id']}'. Attendu : {CATEGORIES}")
    for e in edges:
        for k in ("from", "to"):
            if e[k] not in ids:
                sys.exit(f"Arête {e} : nœud '{e[k]}' inexistant")

    cols = [c for c in CATEGORIES if any(n["category"] == c for n in nodes)]
    by_cat = {c: [n for n in nodes if n["category"] == c] for c in cols}
    max_rows = max(len(v) for v in by_cat.values())
    zone_h = ZONE_TITLE_H + ZONE_PAD * 2 + max_rows * NODE_H + (max_rows - 1) * ROW_GAP

    elements: list[dict] = []
    files: dict[str, dict] = {}
    rects: dict[str, dict] = {}
    cat_of = {n["id"]: n["category"] for n in nodes}

    if spec.get("title"):
        elements.append(text_el("title", 0, 0, spec["title"], size=32))

    zone_w = NODE_W + ZONE_PAD * 2
    for ci, cat in enumerate(cols):
        zx = ci * (zone_w + COL_GAP)
        zbg, stroke, nbg = PALETTE[cat]
        elements.append(
            base(f"zone-{cat}", "rectangle", zx, TOP, zone_w, zone_h,
                 backgroundColor=zbg, strokeColor=stroke, strokeStyle="dashed",
                 strokeWidth=1, roundness={"type": 3})
        )
        elements.append(text_el(f"zone-{cat}-title", zx + ZONE_PAD, TOP + 12, CATEGORY_TITLES[cat],
                                size=20, strokeColor=stroke))
        # centre verticalement la pile de nœuds dans la zone
        n_in = len(by_cat[cat])
        stack_h = n_in * NODE_H + (n_in - 1) * ROW_GAP
        y0 = TOP + ZONE_TITLE_H + ZONE_PAD + (zone_h - ZONE_TITLE_H - ZONE_PAD * 2 - stack_h) / 2
        for ri, n in enumerate(by_cat[cat]):
            nx, ny = zx + ZONE_PAD, y0 + ri * (NODE_H + ROW_GAP)
            gid = f"g-{n['id']}"
            rect = base(f"node-{n['id']}", "rectangle", nx, ny, NODE_W, NODE_H,
                        backgroundColor=nbg, strokeColor=stroke, roundness={"type": 3},
                        groupIds=[gid])
            rects[n["id"]] = rect
            elements.append(rect)
            text_x = nx + 16
            logo = n.get("logo")
            if logo:
                loaded = load_logo((spec_dir / logo).resolve())
                if loaded:
                    fid, entry = loaded
                    files[fid] = entry
                    elements.append(
                        base(f"logo-{n['id']}", "image", nx + 14, ny + (NODE_H - LOGO) / 2, LOGO, LOGO,
                             strokeColor="transparent", groupIds=[gid],
                             fileId=fid, status="saved", scale=[1, 1], crop=None)
                    )
                    text_x = nx + 14 + LOGO + 14
            label = n["label"]
            t = text_el(f"label-{n['id']}", text_x, 0, label, groupIds=[gid])
            t["y"] = ny + (NODE_H - t["height"]) / 2
            elements.append(t)

    for i, e in enumerate(edges):
        a, b = rects[e["from"]], rects[e["to"]]
        forward = a["x"] < b["x"]
        same_col = a["x"] == b["x"]
        if same_col:
            down = a["y"] < b["y"]
            sx = a["x"] + NODE_W / 2
            sy = a["y"] + (NODE_H if down else 0)
            ex = b["x"] + NODE_W / 2
            ey = b["y"] + (0 if down else NODE_H)
        else:
            sx = a["x"] + (NODE_W if forward else 0)
            sy = a["y"] + NODE_H / 2
            ex = b["x"] + (0 if forward else NODE_W)
            ey = b["y"] + NODE_H / 2
        dashed = e.get("dashed") or "async" in (cat_of[e["from"]], cat_of[e["to"]]) \
            or "external" in (cat_of[e["from"]], cat_of[e["to"]])
        aid = f"edge-{i}"
        arrow = base(aid, "arrow", sx, sy, abs(ex - sx), abs(ey - sy),
                     strokeStyle="dashed" if dashed else "solid", roundness={"type": 2})
        arrow.update(
            {
                "points": [[0, 0], [ex - sx, ey - sy]],
                "lastCommittedPoint": None,
                "startBinding": {"elementId": a["id"], "focus": 0, "gap": 4},
                "endBinding": {"elementId": b["id"], "focus": 0, "gap": 4},
                "startArrowhead": None,
                "endArrowhead": "arrow",
                "elbowed": False,
            }
        )
        a["boundElements"].append({"id": aid, "type": "arrow"})
        b["boundElements"].append({"id": aid, "type": "arrow"})
        elements.append(arrow)
        if e.get("label"):
            lt = text_el(f"{aid}-label", 0, 0, e["label"], size=14)
            lt.update({"containerId": aid, "textAlign": "center", "verticalAlign": "middle"})
            lt["x"] = sx + (ex - sx) / 2 - lt["width"] / 2
            lt["y"] = sy + (ey - sy) / 2 - lt["height"] / 2
            arrow["boundElements"].append({"id": lt["id"], "type": "text"})
            elements.append(lt)

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": files,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("architecture.excalidraw"))
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    doc = build(spec, args.spec.parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    n_logos = len(doc["files"])
    print(f"OK : {args.output} ({len(spec['nodes'])} nœuds, {len(spec.get('edges', []))} arêtes, {n_logos} logos)")


if __name__ == "__main__":
    main()
