"""
publications.py — read content/publications.bib for the site.

Supported extra field: status = {under review} | {accepted}
Usage: python publications.py   # print the list as the site shows it
"""

from __future__ import annotations

import pathlib
import re

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

ROOT = pathlib.Path(__file__).parent
BIB = ROOT / "content" / "publications.bib"

TYPES = {"article": "journal", "inproceedings": "conference", "incollection": "chapter",
         "inbook": "chapter", "book": "book", "proceedings": "editorship", "phdthesis": "thesis"}
TYPE_ORDER = ["journal", "conference", "chapter", "book", "editorship", "thesis", "other", "preprint"]


def _title(t: str) -> str:
    t = (t or "").replace("{", "").replace("}", "").replace("``", "“").replace("''", "”")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:-1] if t.endswith(".") else t


def _names(s: str) -> list[str]:
    out = []
    for part in re.split(r"\s+and\s+", s or ""):
        part = part.replace("{", "").replace("}", "").strip()
        if "," in part:
            last, first = [x.strip() for x in part.split(",", 1)]
            part = f"{first} {last}"
        if part:
            out.append(part)
    return out


def _year(y) -> int:
    m = re.search(r"\d{4}", str(y or ""))
    return int(m.group(0)) if m else 0


def load(path: pathlib.Path = BIB) -> list[dict]:
    if not path.exists():
        return []
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    db = bibtexparser.loads(path.read_text(encoding="utf-8"), parser=parser)
    pubs = []
    for e in db.entries:
        etype = e.get("ENTRYTYPE", "misc").lower()
        venue = e.get("journal") or e.get("booktitle") or e.get("school") or e.get("howpublished", "")
        ptype = TYPES.get(etype, "journal" if e.get("journal") else "other")
        url = e.get("url", "")
        doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", e.get("doi", "").strip(), flags=re.I)
        if "arxiv" in venue.lower():
            ptype, venue = "preprint", "arXiv"
        pubs.append({
            "type": ptype,
            "authors": _names(e.get("author", "")),
            "editors": _names(e.get("editor", "")),
            "title": _title(e.get("title", "")),
            "venue": _title(venue),
            "volume": e.get("volume", ""),
            "number": e.get("number", ""),
            "pages": e.get("pages", "").replace("--", "–"),
            "year": _year(e.get("year")),
            "doi": doi,
            "url": "" if doi or "arxiv.org" in url else url,
            "oa": "",
            "arxiv": url if "arxiv.org" in url else "",
            "status": e.get("status", "").strip().lower(),
        })
    rank = {t: n for n, t in enumerate(TYPE_ORDER)}
    pubs.sort(key=lambda p: (-p["year"], rank.get(p["type"], 99), p["title"].lower()))
    return pubs


if __name__ == "__main__":
    items = load()
    for p in items:
        print(f"{p['year']}  {p['type']:<10} {p['title'][:80]}")
    print(f"{len(items)} publications")
