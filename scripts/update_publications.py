#!/usr/bin/env python3
"""新しい論文を ORCID と Crossref から探して data/publications.json に追加する。

GitHub Actions から毎週自動で実行される（手動実行も可）。
- ORCID の業績リストと、Crossref に ORCID 付きで登録された論文を照合
- まだ載っていない論文（DOI またはタイトルで判定）だけを追加
- data/add_dois.txt に書いた DOI は年・種類に関係なく追加
- data/exclude_dois.txt に書いた DOI は追加しない
- 「in press」「online available」の論文に巻・ページが付いたら自動で更新
ネットワークエラーが起きてもサイトのビルドは止めない（警告を出して終了）。
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "publications.json"
ADD_FILE = ROOT / "data" / "add_dois.txt"
EXCLUDE_FILE = ROOT / "data" / "exclude_dois.txt"

THIS_YEAR = dt.date.today().year
SINCE_YEAR = int(os.environ.get("PUB_SINCE_YEAR", THIS_YEAR - 1))
MY_FAMILY = "doi"
MY_GIVEN = ("hideyuki", "h.", "h")
# プレプリント・データセットなど、論文リストに載せないDOI
EXCLUDED_PREFIXES = (
    "10.1101/", "10.21203/", "10.5281/", "10.22541/", "10.32942/", "10.31219/",
    "10.3897/arphapreprints", "10.20944/", "10.2139/ssrn", "10.6084/", "10.5061/",
)
PENDING = re.compile(r"\s*\b(in press|online available)\b\.?\s*$", re.I)
UA = "ecologyweb-publication-updater/1.0"
MAILTO = os.environ.get("CROSSREF_MAILTO", "")


# ---------- network ----------
def get_json(url: str, headers: dict | None = None, tries: int = 3):
    h = {"User-Agent": UA + (f" (mailto:{MAILTO})" if MAILTO else "")}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            print(f"  retry {url}: {e}", file=sys.stderr)
            time.sleep(2 * (i + 1))


def orcid_dois(orcid: str) -> set[str]:
    data = get_json(f"https://pub.orcid.org/v3.0/{orcid}/works", {"Accept": "application/json"})
    out = set()
    for g in data.get("group", []):
        ws = (g.get("work-summary") or [{}])[0]
        if ws.get("type") not in (None, "journal-article"):
            continue
        y = ((ws.get("publication-date") or {}).get("year") or {}).get("value")
        if y and int(y) < SINCE_YEAR:
            continue
        for x in (g.get("external-ids") or {}).get("external-id", []):
            if x.get("external-id-type") == "doi" and x.get("external-id-value"):
                out.add(norm_doi(x["external-id-value"]))
    return out


def crossref_dois(orcid: str) -> set[str]:
    q = urllib.parse.urlencode({
        "filter": f"orcid:{orcid},from-pub-date:{SINCE_YEAR}-01-01,type:journal-article",
        "rows": 200, "select": "DOI",
    })
    data = get_json(f"https://api.crossref.org/works?{q}")
    return {norm_doi(i["DOI"]) for i in data["message"]["items"]}


def crossref_work(doi: str) -> dict:
    return get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]


# ---------- helpers ----------
def norm_doi(d: str) -> str:
    d = d.strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", d)
    return d.rstrip(".")


def norm_text(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def read_list(p: Path) -> list[str]:
    if not p.exists():
        return []
    return [norm_doi(l.split("#")[0]) for l in p.read_text(encoding="utf-8").splitlines()
            if l.split("#")[0].strip()]


def clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    t = re.sub(r"<(/?)i>", r"<\1em>", t)
    keep = re.compile(r"</?(em|sub|sup)>")
    parts, out, last = [], [], 0
    for m in keep.finditer(t):
        parts.append((t[last:m.start()], m.group(0)))
        last = m.end()
    parts.append((t[last:], ""))
    for text, tag in parts:
        out.append(html.escape(re.sub(r"<[^>]+>", "", text), quote=False) + tag)
    return "".join(out).rstrip(".")


def is_me(a: dict, orcid: str) -> bool:
    if orcid and orcid in (a.get("ORCID") or ""):
        return True
    fam, giv = (a.get("family") or "").lower(), (a.get("given") or "").lower()
    return fam == MY_FAMILY and giv.startswith(MY_GIVEN)


def fmt_authors(authors: list[dict], orcid: str) -> str:
    names = []
    for a in authors:
        n = " ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "")
        n = html.escape(n, quote=False)
        names.append(f"<strong>{n}</strong>" if is_me(a, orcid) else n)
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + ", and " + names[-1]


def year_of(w: dict) -> int:
    for k in ("published-print", "published-online", "issued", "created"):
        dp = (w.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            return int(dp[0][0])
    return THIS_YEAR


def vol_pages(w: dict) -> str:
    vol = w.get("volume")
    if not vol:
        return ""
    pg = w.get("page") or w.get("article-number") or ""
    return f"{vol}:{pg}" if pg else vol


def make_entry(w: dict, new_id: int, orcid: str) -> dict:
    y = year_of(w)
    title = clean_title((w.get("title") or ["(untitled)"])[0])
    journal = html.escape((w.get("container-title") or [""])[0], quote=False)
    vp = vol_pages(w)
    tail = f"<em>{journal}</em> {vp}." if vp else f"<em>{journal}</em> online available."
    cite = f"{fmt_authors(w.get('author', []), orcid)} ({y}) {title}. {tail}"
    return {"id": str(new_id), "year": y, "type": "article", "html": cite,
            "doi": norm_doi(w["DOI"]), "source": "auto", "added": dt.date.today().isoformat()}


def sort_key(e: dict):
    num = int(e["id"]) if e["id"].isdigit() else -1
    order = {"article": 0, "japanese": 1, "book": 2}.get(e["type"], 3)
    return (order, -e["year"], -num)


# ---------- main ----------
def main() -> int:
    db = json.loads(DATA.read_text(encoding="utf-8"))
    pubs = db["publications"]
    orcid = db.get("orcid", "")
    have_doi = {norm_doi(p["doi"]) for p in pubs if p.get("doi")}
    have_title = {p["id"]: norm_text(p["html"]) for p in pubs}
    exclude = set(read_list(EXCLUDE_FILE))
    manual = read_list(ADD_FILE)
    added, updated = [], []

    candidates: set[str] = set(manual)
    for name, fn in (("ORCID", orcid_dois), ("Crossref", crossref_dois)):
        try:
            found = fn(orcid)
            print(f"{name}: {len(found)} DOI(s) since {SINCE_YEAR}")
            candidates |= found
        except Exception as e:  # noqa: BLE001
            print(f"::warning::{name} lookup failed: {e}")

    next_id = max(int(p["id"]) for p in pubs if p["id"].isdigit()) + 1
    for doi in sorted(candidates):
        if doi in have_doi or doi in exclude or doi.startswith(EXCLUDED_PREFIXES):
            continue
        try:
            w = crossref_work(doi)
        except Exception as e:  # noqa: BLE001
            print(f"::warning::Crossref lookup failed for {doi}: {e}")
            continue
        if doi not in manual and w.get("type") != "journal-article":
            continue
        t = norm_text((w.get("title") or [""])[0])
        match = next((p for p in pubs if t and len(t) > 20 and t in have_title[p["id"]]), None)
        if match:  # 既に載っている論文（DOI未登録の in press など）に DOI と巻号を付ける
            match["doi"] = doi
            vp = vol_pages(w)
            if vp and PENDING.search(match["html"]):
                match["html"] = PENDING.sub(f" {vp}.", match["html"])
            updated.append(match)
        else:
            e = make_entry(w, next_id, orcid)
            next_id += 1
            pubs.append(e)
            added.append(e)
        have_doi.add(doi)

    # DOI はあるが巻号がまだの論文を更新
    for p in pubs:
        if p.get("doi") and p["year"] >= SINCE_YEAR and PENDING.search(p["html"]) and p not in updated:
            try:
                vp = vol_pages(crossref_work(p["doi"]))
            except Exception:  # noqa: BLE001
                continue
            if vp:
                p["html"] = PENDING.sub(f" {vp}.", p["html"])
                updated.append(p)

    pubs.sort(key=sort_key)
    DATA.write_text(json.dumps(db, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lines = [f"Added {len(added)}, updated {len(updated)} publication(s)."]
    lines += [f"- added: {re.sub('<[^>]+>', '', e['html'])[:160]}" for e in added]
    lines += [f"- updated: {re.sub('<[^>]+>', '', e['html'])[:160]}" for e in updated]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Publications\n" + "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
