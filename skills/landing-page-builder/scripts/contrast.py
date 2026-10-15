#!/usr/bin/env python3
"""Calcule le ratio de contraste WCAG 2.x entre deux couleurs.

Usage :
    python contrast.py "#ffffff" "#1a1a1a"          # une paire
    python contrast.py --pairs "#fff:#111" "#0a5:#fff" ...   # plusieurs paires fond:texte

Formats acceptés : #rgb, #rrggbb (le # est optionnel).
Sortie : ratio, et verdict pour texte normal (4.5), grand texte (3.0) et
éléments d'interface (3.0). Code retour 1 si une paire échoue au texte normal.
"""
import sys


def parse(color: str) -> tuple[int, int, int]:
    c = color.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"couleur invalide : {color!r}")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def luminance(rgb: tuple[int, int, int]) -> float:
    def lin(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: str, b: str) -> float:
    la, lb = luminance(parse(a)), luminance(parse(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def report(a: str, b: str) -> bool:
    r = ratio(a, b)
    ok = lambda t: "OK  " if r >= t else "FAIL"
    print(
        f"{a} / {b} : {r:.2f}:1  "
        f"texte normal(4.5) {ok(4.5)}  grand texte(3) {ok(3.0)}  UI(3) {ok(3.0)}"
    )
    return r >= 4.5


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "--pairs":
        results = [report(*p.split(":", 1)) for p in argv[1:]]
        return 0 if all(results) else 1
    if len(argv) == 2:
        return 0 if report(argv[0], argv[1]) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
