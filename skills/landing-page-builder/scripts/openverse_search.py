#!/usr/bin/env python3
"""Recherche d'images libres de droit via l'API publique Openverse (sans clé).

Usage :
    python openverse_search.py "small business owner laptop"
    python openverse_search.py "conference stage" --n 8 --orientation wide
    python openverse_search.py "mountain lake" --cc0        # CC0 / domaine public uniquement
    python openverse_search.py "office plants" --json       # sortie JSON brute

Filtre par défaut : usage commercial ET modification autorisés (exclut NC et ND).
Orientation : wide (paysage), tall (portrait), square.
Sortie : pour chaque résultat, dimensions, licence, attribution requise ou non,
auteur, page source, URL du fichier et ligne d'attribution prête à l'emploi.
Vérifie toujours la licence sur la page source avant d'utiliser l'image.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

API = "https://api.openverse.org/v1/images/"
NO_ATTRIBUTION = {"cc0", "pdm"}


def search(query: str, n: int, orientation: str | None, cc0: bool) -> list[dict]:
    params = {"q": query, "page_size": str(n), "mature": "false"}
    if cc0:
        params["license"] = "cc0,pdm"
    else:
        params["license_type"] = "commercial,modification"
    if orientation:
        params["aspect_ratio"] = orientation
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "landing-page-builder/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp).get("results", [])


def main() -> int:
    p = argparse.ArgumentParser(description="Recherche d'images libres via Openverse.")
    p.add_argument("query")
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--orientation", choices=["wide", "tall", "square"])
    p.add_argument("--cc0", action="store_true", help="CC0 / domaine public uniquement")
    p.add_argument("--json", action="store_true", help="sortie JSON brute")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):  # console Windows en cp1252
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        results = search(a.query, a.n, a.orientation, a.cc0)
    except Exception as e:  # réseau, quota anonyme, API indisponible
        print(f"Erreur Openverse : {e}", file=sys.stderr)
        return 2

    if a.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
        return 0
    if not results:
        print("Aucun résultat.")
        return 0

    for i, r in enumerate(results, 1):
        lic = (r.get("license") or "").lower()
        version = r.get("license_version") or ""
        required = "non" if lic in NO_ATTRIBUTION else "OUI"
        print(f"[{i}] {r.get('title') or '(sans titre)'}")
        print(f"    {r.get('width')}x{r.get('height')} — licence {lic.upper()} {version} — attribution requise : {required}")
        print(f"    auteur  : {r.get('creator') or '?'} {r.get('creator_url') or ''}".rstrip())
        print(f"    source  : {r.get('foreign_landing_url')} ({r.get('source')})")
        print(f"    fichier : {r.get('url')}")
        print(f"    licence : {r.get('license_url')}")
        if r.get("attribution"):
            print(f"    crédit  : {r['attribution']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
