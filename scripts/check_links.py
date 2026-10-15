#!/usr/bin/env python3
"""全論文の DOI と、Jimdo から取り込む写真の URL を実際にネットで確認する。

  python scripts/check_links.py

- DOI：Crossref に問い合わせ、登録されているか、タイトルがリストと一致するかを確認
  （Crossref にない DOI は doi.org で存在だけ確認）
- 写真：site_images.py の各 URL が画像を返すかを確認
結果は画面と（GitHub Actions では）ジョブの Summary に出る。サイトの公開は止めない。
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from site_images import IMAGES  # noqa: E402

UA = "ecologyweb-link-checker/1.0" + (f" (mailto:{os.environ['CROSSREF_MAILTO']})"
                                      if os.environ.get("CROSSREF_MAILTO") else "")


def get(url: str, accept: str = "application/json", tries: int = 3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410) or i == tries - 1:
                return e.code, "", b""
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                return 0, str(e), b""


def norm(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def check_doi(p: dict) -> tuple[str, str, str]:
    doi = p["doi"]
    code, _, body = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if code == 200:
        title = (json.loads(body)["message"].get("title") or [""])[0]
        t = norm(title)
        if t and (t in norm(p["html"]) or t[:40] in norm(p["html"])):
            return "OK", p["id"], doi
        return "TITLE MISMATCH", p["id"], f"{doi} -> Crossref title: {re.sub('<[^>]+>', '', title)[:120]}"
    # Crossref 以外（JaLC など）に登録された DOI は doi.org で存在確認
    code2, _, body2 = get("https://doi.org/api/handles/" + urllib.parse.quote(doi))
    if code2 == 200 and json.loads(body2).get("responseCode") == 1:
        return "OK (not in Crossref)", p["id"], doi
    return "NOT FOUND", p["id"], f"{doi} (Crossref {code}, doi.org {code2})"


def check_image(item) -> list[tuple[str, str, str]]:
    name, (_, urls) = item
    out = []
    for u in urls:
        code, ctype, body = get(u, accept="image/*")
        ok = code == 200 and ctype.startswith("image/") and len(body) > 500
        out.append(("OK" if ok else "FAILED", name, f"{len(body) // 1024} KB" if ok else f"HTTP {code} {ctype}"))
    return out


def main() -> int:
    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))["publications"]
    with_doi = [p for p in pubs if p.get("doi")]
    with ThreadPoolExecutor(8) as ex:
        dres = list(ex.map(check_doi, with_doi))
        ires = [r for rs in ex.map(check_image, IMAGES.items()) for r in rs]

    lines = ["### DOI check",
             f"{sum(r[0].startswith('OK') for r in dres)} / {len(dres)} DOIs OK "
             f"({len(pubs) - len(with_doi)} entries have no DOI)"]
    lines += [f"- **{s}** No. {i}: {d}" for s, i, d in dres if not s.startswith("OK")]
    lines += ["", "### Image check"]
    for name, (fname, urls) in IMAGES.items():
        if not urls:  # リポジトリにだけ置いている画像は、ファイルがあるかだけ確認
            ok = (ROOT / "assets" / "img" / fname).exists()
            lines.append(f"- {'OK' if ok else 'MISSING'} {name}: local file assets/img/{fname}")
            continue
        rs = [r for r in ires if r[1] == name]
        best = "OK" if any(r[0] == "OK" for r in rs) else "FAILED"
        lines.append(f"- {best} {name}: " + ", ".join(r[2] for r in rs))
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
