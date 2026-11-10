#!/usr/bin/env python3
"""Turn a Markdown design doc into a professional PDF (A4), via headless Chrome or Edge.

Usage:
    python build_pdf.py docs/architecture/design-doc.md [-o design-doc.pdf]
        [--lang en|fr] [--version 1.0] [--status Draft] [--date 2026-11-10] [--keep-html]

Markdown subset: # title (first H1 = document title; a following "> line" = subtitle), ## / ### / ####
headings (auto-numbered), paragraphs, - / 1. lists (one nesting level), tables, ``` code blocks,
> notes, ---, **bold**, *italic*, `code`, [links](url), and ![caption](diagram.svg) figures
(SVG inlined, other images embedded). The PDF gets a title page and a table of contents.
If no Chrome/Edge is found, the HTML is kept and the script says so. Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

LABELS = {
    "en": {"contents": "Contents", "version": "Version", "status": "Status", "date": "Date", "figure": "Figure"},
    "fr": {"contents": "Sommaire", "version": "Version", "status": "Statut", "date": "Date", "figure": "Figure"},
}

CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.55;
       color: #1f2328; margin: 0; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center;
         border-left: 6px solid #1c3d5a; padding-left: 14mm; page-break-after: always; }
.cover h1 { font-size: 28pt; line-height: 1.2; margin: 0 0 6mm; color: #1c3d5a; border: 0; }
.cover .subtitle { font-size: 13pt; color: #57606a; margin: 0 0 14mm; }
.cover table.meta { width: auto; border: 0; font-size: 10pt; }
.cover table.meta td { border: 0; padding: 1mm 8mm 1mm 0; background: none; }
.cover table.meta td:first-child { color: #57606a; }
nav.toc { page-break-after: always; }
nav.toc h2 { counter-reset: none; }
nav.toc ol { list-style: none; padding-left: 0; }
nav.toc li { margin: 1.2mm 0; }
nav.toc li.l3 { padding-left: 8mm; color: #57606a; }
nav.toc a { color: inherit; text-decoration: none; }
h2 { font-size: 16pt; color: #1c3d5a; margin: 10mm 0 3mm; padding-bottom: 1.5mm;
     border-bottom: 1px solid #d0d7de; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #1c3d5a; margin: 7mm 0 2mm; page-break-after: avoid; }
h4 { font-size: 11pt; margin: 5mm 0 1.5mm; page-break-after: avoid; }
p { margin: 0 0 3mm; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 3mm; padding-left: 7mm; }
li { margin: 0.8mm 0; }
a { color: #0b5cad; }
code { font-family: Consolas, "Cascadia Mono", Menlo, monospace; font-size: 9pt; background: #f3f5f7;
       padding: 0.3mm 1.2mm; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 4px; padding: 3mm 4mm;
      font-size: 8.8pt; line-height: 1.45; overflow: hidden; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #eef2f6; color: #1c3d5a; text-align: left; font-weight: 600; }
th, td { border: 1px solid #d0d7de; padding: 1.6mm 2.4mm; vertical-align: top; }
blockquote { margin: 0 0 3mm; padding: 2mm 4mm; border-left: 3px solid #1c3d5a; background: #f6f8fa;
             color: #3d4852; }
blockquote p:last-child { margin: 0; }
hr { border: 0; border-top: 1px solid #d0d7de; margin: 6mm 0; }
figure { margin: 4mm 0 5mm; text-align: center; page-break-inside: avoid; }
figure svg, figure img { max-width: 100%; height: auto; max-height: 200mm; }
figcaption { font-size: 9pt; color: #57606a; margin-top: 2mm; }
"""

INLINE_CODE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    codes: list[str] = []

    def keep(m: re.Match) -> str:
        codes.append(f"<code>{escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = escape(INLINE_CODE.sub(keep, text), quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{escape(m.group(2))}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def slug(text: str, used: set[str]) -> str:
    base = re.sub(r"[^\w]+", "-", text.lower()).strip("-") or "section"
    s, i = base, 2
    while s in used:
        s, i = f"{base}-{i}", i + 1
    used.add(s)
    return s


def figure(alt: str, src: str, base_dir: Path, n: int, labels: dict) -> str:
    path = (base_dir / src) if not Path(src).is_absolute() else Path(src)
    caption = f'<figcaption>{labels["figure"]} {n} — {inline(alt)}</figcaption>' if alt else ""
    if not path.is_file():
        print(f"[warn] image not found: {path}", file=sys.stderr)
        return f"<p><em>[{escape(src)}]</em></p>"
    if path.suffix.lower() == ".svg":
        svg = path.read_text(encoding="utf-8")
        svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
        return f"<figure>{svg}{caption}</figure>"
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(
        path.suffix.lower(), "application/octet-stream")
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<figure><img src="data:{mime};base64,{data}" alt="{escape(alt)}">{caption}</figure>'


def md_to_html(md: str, base_dir: Path, labels: dict) -> tuple[str, str, str, list[tuple[int, str, str]]]:
    """Return (title, subtitle, body_html, toc entries)."""
    lines = md.replace("\r\n", "\n").split("\n")
    title, subtitle = "", ""
    body: list[str] = []
    toc: list[tuple[int, str, str]] = []
    used: set[str] = set()
    n2 = n3 = fig = 0
    i = 0

    def is_table_sep(s: str) -> bool:
        return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", s))

    def cells(s: str) -> list[str]:
        s = s.strip()
        s = s[1:] if s.startswith("|") else s
        s = s[:-1] if s.endswith("|") else s
        return [c.strip() for c in s.split("|")]

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if stripped.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            body.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1 and not title:
                title = text
                if i + 2 < len(lines) and not lines[i + 1].strip() and lines[i + 2].strip().startswith(">"):
                    subtitle = lines[i + 2].strip().lstrip(">").strip()
                    i += 3
                    continue
                if i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                    subtitle = lines[i + 1].strip().lstrip(">").strip()
                    i += 2
                    continue
                i += 1
                continue
            level = max(level, 2)
            numbered = re.match(r"^\d+(\.\d+)*\.?\s", text)
            if level == 2:
                n2, n3 = n2 + 1, 0
                label = text if numbered else f"{n2}. {text}"
            elif level == 3:
                n3 += 1
                label = text if numbered else f"{n2}.{n3} {text}"
            else:
                label = text
            sid = slug(text, used)
            if level <= 3:
                toc.append((level, sid, label))
            body.append(f'<h{level} id="{sid}">{inline(label)}</h{level}>')
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            body.append("<hr>")
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if m:
            fig += 1
            body.append(figure(m.group(1), m.group(2), base_dir, fig, labels))
            i += 1
            continue
        if "|" in stripped and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            head = cells(stripped)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]))
                i += 1
            html = "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
            for r in rows:
                html += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            body.append(html + "</tbody></table>")
            continue
        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            body.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            continue
        m = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", line)
        if m:
            ordered = m.group(2)[0].isdigit()
            tag = "ol" if ordered else "ul"
            items: list[list] = []
            while i < len(lines):
                lm = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", lines[i])
                if lm and len(lm.group(1)) < 2:
                    items.append([lm.group(3), []])
                elif lm and items:
                    items[-1][1].append((lm.group(2)[0].isdigit(), lm.group(3)))
                elif lines[i].strip() and items and lines[i].startswith("  "):
                    items[-1][0] += " " + lines[i].strip()
                else:
                    break
                i += 1
            html = f"<{tag}>"
            for text, subs in items:
                html += f"<li>{inline(text)}"
                if subs:
                    st = "ol" if subs[0][0] else "ul"
                    html += f"<{st}>" + "".join(f"<li>{inline(s)}</li>" for _, s in subs) + f"</{st}>"
                html += "</li>"
            body.append(html + f"</{tag}>")
            continue
        para = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|>|\s*([-*]|\d+[.)])\s|!\[|-{3,}$)", lines[i].strip()) \
                and not ("|" in lines[i] and i + 1 < len(lines) and is_table_sep(lines[i + 1])):
            para.append(lines[i].strip())
            i += 1
        body.append(f"<p>{inline(' '.join(para))}</p>")
    return title, subtitle, "\n".join(body), toc


def build_html(md_path: Path, lang: str, version: str, status: str, date: str) -> str:
    labels = LABELS[lang]
    title, subtitle, body, toc = md_to_html(md_path.read_text(encoding="utf-8"), md_path.parent, labels)
    title = title or md_path.stem
    meta = [(labels["version"], version), (labels["status"], status), (labels["date"], date)]
    meta_html = "".join(f"<tr><td>{escape(k)}</td><td>{escape(v)}</td></tr>" for k, v in meta if v)
    cover = (f'<section class="cover"><h1>{inline(title)}</h1>'
             + (f'<p class="subtitle">{inline(subtitle)}</p>' if subtitle else "")
             + f'<table class="meta">{meta_html}</table></section>')
    toc_html = ""
    if toc:
        toc_html = (f'<nav class="toc"><h2>{labels["contents"]}</h2><ol>'
                    + "".join(f'<li class="l{lvl}"><a href="#{sid}">{inline(lbl)}</a></li>' for lvl, sid, lbl in toc)
                    + "</ol></nav>")
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{escape(title)}</title>'
            f"<style>{CSS}</style></head><body>{cover}{toc_html}<main>{body}</main></body></html>")


def find_browser() -> str | None:
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).is_file():
        return env
    for name in ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "msedge", "microsoft-edge"):
        p = shutil.which(name)
        if p:
            return p
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(str(Path(local) / "Google/Chrome/Application/chrome.exe"))
    return next((c for c in candidates if Path(c).is_file()), None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None, help="default: same name with .pdf")
    ap.add_argument("--lang", choices=sorted(LABELS), default="en")
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--status", default="")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML next to the PDF")
    args = ap.parse_args()

    out = (args.output or args.markdown.with_suffix(".pdf")).resolve()
    html_path = out.with_suffix(".html")
    html_path.write_text(build_html(args.markdown, args.lang, args.version, args.status, args.date), encoding="utf-8")

    browser = find_browser()
    if not browser:
        print(f"No Chrome/Edge found (set CHROME_PATH). HTML kept: {html_path} — print it to PDF from a browser.")
        sys.exit(2)
    with tempfile.TemporaryDirectory() as profile:
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
               f"--user-data-dir={profile}", f"--print-to-pdf={out}", html_path.as_uri()]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0 or not out.is_file():
        print(res.stderr[-2000:], file=sys.stderr)
        sys.exit(f"PDF generation failed. HTML kept: {html_path}")
    if not args.keep_html:
        html_path.unlink(missing_ok=True)
    print(f"PDF: {out}")


if __name__ == "__main__":
    main()
