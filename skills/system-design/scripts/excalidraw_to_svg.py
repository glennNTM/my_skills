#!/usr/bin/env python3
"""Render an .excalidraw file (as produced by build_excalidraw.py, manual edits included) to a static SVG.

Usage:
    python excalidraw_to_svg.py docs/architecture/architecture.excalidraw [-o out.svg] [--no-logos] [--no-header]

Supports the element types the diagram uses: rectangle, text, arrow/line, image.
--no-logos drops technology logos (used for the design-doc PDF) and shifts node labels
to where the logo was, so nodes stay balanced. --no-header drops the diagram title and subtitle
(the design doc already has them).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

PAD = 24
FONT = "Helvetica, Arial, 'Segoe UI', sans-serif"


def _color(c: str | None, default: str = "none") -> str:
    return default if not c or c == "transparent" else c


def _dash(el: dict) -> str:
    style = el.get("strokeStyle")
    if style == "dashed":
        return ' stroke-dasharray="8 6"'
    if style == "dotted":
        return ' stroke-dasharray="2 4"'
    return ""


def _bounds(elements: list[dict]) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for el in elements:
        if el["type"] in ("arrow", "line"):
            for px, py in el.get("points", []):
                xs.append(el["x"] + px)
                ys.append(el["y"] + py)
        else:
            xs += [el["x"], el["x"] + el.get("width", 0)]
            ys += [el["y"], el["y"] + el.get("height", 0)]
    return min(xs), min(ys), max(xs), max(ys)


def _arrowhead(tip: tuple[float, float], prev: tuple[float, float], color: str, width: float) -> str:
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    size = 10 + width * 2
    left = (tip[0] - size * math.cos(ang - math.pi / 7), tip[1] - size * math.sin(ang - math.pi / 7))
    right = (tip[0] - size * math.cos(ang + math.pi / 7), tip[1] - size * math.sin(ang + math.pi / 7))
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (tip, left, right))
    return f'<polygon points="{pts}" fill="{color}" stroke="none"/>'


def render(doc: dict, no_logos: bool = False, no_header: bool = False) -> str:
    elements = [e for e in doc.get("elements", []) if not e.get("isDeleted")]
    if no_header:
        elements = [e for e in elements if e.get("id") not in ("title", "subtitle")]
    files = doc.get("files", {})

    # With --no-logos, move the labels of a node to the logo's place (same group as the image).
    shift: dict[str, float] = {}
    if no_logos:
        for img in (e for e in elements if e["type"] == "image"):
            for gid in img.get("groupIds", []):
                shift[gid] = max(shift.get(gid, 0), img["width"] + 8)
        elements = [e for e in elements if e["type"] != "image"]

    x0, y0, x1, y1 = _bounds(elements)
    w, h = x1 - x0 + 2 * PAD, y1 - y0 + 2 * PAD
    ox, oy = PAD - x0, PAD - y0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
           f'width="{w:.0f}" height="{h:.0f}" font-family="{FONT}">',
           f'<rect x="0" y="0" width="{w:.0f}" height="{h:.0f}" fill="#ffffff"/>']

    for el in elements:
        t = el["type"]
        x, y = el["x"] + ox, el["y"] + oy
        opacity = el.get("opacity", 100) / 100
        op = f' opacity="{opacity:.2f}"' if opacity < 1 else ""
        stroke = _color(el.get("strokeColor"), "#1e1e1e")
        sw = el.get("strokeWidth", 1)
        if t in ("rectangle", "ellipse", "diamond"):
            fill = _color(el.get("backgroundColor"))
            if t == "ellipse":
                out.append(f'<ellipse cx="{x + el["width"] / 2:.1f}" cy="{y + el["height"] / 2:.1f}" '
                           f'rx="{el["width"] / 2:.1f}" ry="{el["height"] / 2:.1f}" fill="{fill}" '
                           f'stroke="{stroke}" stroke-width="{sw}"{_dash(el)}{op}/>')
            else:
                r = 8 if el.get("roundness") else 0
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{el["width"]:.1f}" height="{el["height"]:.1f}" '
                           f'rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{_dash(el)}{op}/>')
        elif t == "text":
            dx = next((shift[g] for g in el.get("groupIds", []) if g in shift), 0)
            size = el.get("fontSize", 16)
            lh = size * el.get("lineHeight", 1.25)
            align = el.get("textAlign", "left")
            anchor = {"left": "start", "center": "middle", "right": "end"}.get(align, "start")
            tx = x - dx + {"left": 0, "center": el.get("width", 0) / 2, "right": el.get("width", 0)}.get(align, 0)
            lines = str(el.get("text", "")).split("\n")
            spans = "".join(
                f'<tspan x="{tx:.1f}" y="{y + i * lh + size * 0.9:.1f}">{escape(line)}</tspan>'
                for i, line in enumerate(lines))
            out.append(f'<text font-size="{size}" fill="{stroke}" text-anchor="{anchor}"{op}>{spans}</text>')
        elif t in ("arrow", "line"):
            pts = [(x + px, y + py) for px, py in el.get("points", [])]
            if len(pts) < 2:
                continue
            poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
            out.append(f'<polyline points="{poly}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
                       f'stroke-linejoin="round"{_dash(el)}{op}/>')
            if t == "arrow":
                if el.get("endArrowhead"):
                    out.append(_arrowhead(pts[-1], pts[-2], stroke, sw))
                if el.get("startArrowhead"):
                    out.append(_arrowhead(pts[0], pts[1], stroke, sw))
        elif t == "image":
            f = files.get(el.get("fileId", ""))
            if f:
                out.append(f'<image x="{x:.1f}" y="{y:.1f}" width="{el["width"]:.1f}" height="{el["height"]:.1f}" '
                           f'href="{f["dataURL"]}" preserveAspectRatio="xMidYMid meet"/>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None, help="default: same name with .svg")
    ap.add_argument("--no-logos", action="store_true", help="drop technology logos (design-doc PDF)")
    ap.add_argument("--no-header", action="store_true", help="drop the diagram title and subtitle")
    args = ap.parse_args()
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    if not doc.get("elements"):
        sys.exit(f"{args.input}: no elements")
    out = args.output or args.input.with_suffix(".svg")
    out.write_text(render(doc, args.no_logos, args.no_header), encoding="utf-8")
    print(f"SVG: {out}")


if __name__ == "__main__":
    main()
