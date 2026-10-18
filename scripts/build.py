#!/usr/bin/env python3
"""src/ と data/ から公開用の _site/ を作る（依存ライブラリなし）。

  python scripts/build.py                    # site.json のテーマで _site/index.html を作成
  python scripts/build.py --theme sidebar    # テーマを指定（bold / sidebar / banner）
  python scripts/build.py --preview          # 確認用の1ファイル（手元の画像を埋め込み）
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from site_images import IMAGES  # noqa: E402

SRC, OUT = ROOT / "src", ROOT / "_site"
_GF = "https://fonts.googleapis.com/css2?family="
THEMES = {
    "bold": _GF + "M+PLUS+2:wght@500;700;800&family=Noto+Sans+JP:wght@400;500;700&family=Newsreader:ital,opsz,wght@1,6..72,400&display=swap",
    "sidebar": _GF + "Noto+Serif+JP:wght@500;700&family=Noto+Sans+JP:wght@400;500;700&display=swap",
    "banner": _GF + "Albert+Sans:wght@500;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap",
}
PREVIEW = False
NEW_DAYS = 60  # 自動追加から何日間「新着」の印を付けるか


def img_src(name: str, remote: bool) -> str:
    fname, urls = IMAGES[name]
    local = ROOT / "assets" / "img" / fname
    if local.exists() and PREVIEW:
        mime = "image/png" if fname.endswith(".png") else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(local.read_bytes()).decode()
    if local.exists() and name in ("favicon", "touch-icon"):
        # ブラウザはアイコンを長く覚えているので、画像が変わったら URL も変える
        return f"assets/img/{fname}?v=" + hashlib.md5(local.read_bytes()).hexdigest()[:8]
    return f"assets/img/{fname}" if (local.exists() and (not remote or not urls)) else urls[-1]


def write_favicon_ico(png: Path, out: Path) -> None:
    """PNG を1枚だけ入れた favicon.ico を作る（/favicon.ico を直接見に来るブラウザや検索エンジン向け）。"""
    data = png.read_bytes()
    w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    header = (0).to_bytes(2, "little") + (1).to_bytes(2, "little") + (1).to_bytes(2, "little")
    entry = bytes([w % 256, h % 256, 0, 0]) + (1).to_bytes(2, "little") + (32).to_bytes(2, "little") \
        + len(data).to_bytes(4, "little") + (6 + 16).to_bytes(4, "little")
    out.write_bytes(header + entry + data)


def doi_link(doi: str) -> str:
    d = html.escape(doi)
    return f'<a href="https://doi.org/{d}">https://doi.org/{d}</a>'


def render_pub(p: dict, remote: bool, compact: bool = False) -> str:
    meta = []
    if p.get("doi"):
        meta.append(doi_link(p["doi"]))
    if p.get("url"):
        meta.append(f'<a href="{html.escape(p["url"])}">Publisher page</a>')
    notes = "".join(f"<li>{n}</li>" for n in p.get("notes", [])) if not compact else ""
    img = ""
    if p.get("image") and not compact:
        img = (f'<figure class="pub-img"><img src="{img_src(p["image"], remote)}" alt="" '
               f'loading="lazy" data-fallback></figure>')
    is_new = False
    if p.get("added"):
        is_new = (dt.date.today() - dt.date.fromisoformat(p["added"])).days <= NEW_DAYS
    cls = "pub new" if is_new else "pub"
    label = f"{p['id']}" if p["type"] == "article" else p["id"]
    return (
        f'<li class="{cls}" data-type="{p["type"]}" data-year="{p["year"]}">'
        f'<span class="pub-no" aria-hidden="true">{label}</span><div>'
        f'<p class="pub-cite">{p["html"]}</p>'
        + (f'<p class="pub-meta">{" ".join(meta)}</p>' if meta else "")
        + (f'<ul class="pub-notes">{notes}</ul>' if notes else "")
        + img
        # 「大規模データ解析の論文」などのボタン用：タグを検索語として見えない形で埋め込む
        + "".join(f'<span class="visually-hidden" aria-hidden="true"> tag-{t}</span>' for t in p.get("tags", []))
        + "</div></li>"
    )




def short_cite(p: dict) -> str:
    """Compact citation for the Research page: first author et al. (year) title. journal."""
    h = p["html"]
    m = re.search(r"\s\((\d{4})\)\s", h)
    if not m:
        return h
    plain = html.unescape(re.sub(r"<sup>.*?</sup>|<[^>]+>|[*†]", "", h[:m.start()]))
    names = [n.strip() for n in re.split(r",\s*and\s+|,\s*&\s*|\s+and\s+|\s*&\s*|,\s*", plain) if n.strip()]
    me = lambda n: f"<strong>{n}</strong>" if n == "Hideyuki Doi" else html.escape(n)
    if len(names) <= 2:
        auth = " and ".join(me(n) for n in names)
    elif len(names) == 3:
        auth = f"{me(names[0])}, {me(names[1])} and {me(names[2])}"
    elif len(names) > 1 and names[1] == "Hideyuki Doi":
        auth = f"{me(names[0])}, {me(names[1])} et al."
    else:
        auth = f"{me(names[0])} et al."
    rest = h[m.end():]
    link = f' <a class="kp-doi" href="https://doi.org/{html.escape(p["doi"])}">DOI</a>' if p.get("doi") else ""
    return f"{auth} ({m.group(1)}) {rest}{link}"


def link_cite(p: dict) -> str:
    """Key paper as a link: title (linked to the DOI), then 'Doi et al. 2019, Journal'."""
    h = p["html"]
    m = re.search(r"\s\((\d{4})\)\s", h)
    plain = html.unescape(re.sub(r"<sup>.*?</sup>|<[^>]+>|[*†]", "", h[:m.start()]))
    names = [n.strip() for n in re.split(r",\s*and\s+|,\s*&\s*|\s+and\s+|\s*&\s*|,\s*", plain) if n.strip()]
    fam = lambda n: n.split()[-1]
    who = fam(names[0]) if len(names) == 1 else (f"{fam(names[0])} &amp; {fam(names[1])}" if len(names) == 2 else f"{fam(names[0])} et al.")
    rest = h[m.end():]
    tm = re.match(r"(.*?)\.\s+<em>([^<]+)</em>", rest)
    title, journal = (tm.group(1), tm.group(2)) if tm else (rest, "")
    return (f'<a class="kp-title" href="https://doi.org/{html.escape(p["doi"])}">{title}</a>'
            f'<span class="kp-src">{who} {m.group(1)}, <em>{journal}</em></span>')


def papers_block(dois: str, by_doi: dict) -> str:
    items = []
    for d in [x.strip().lower() for x in dois.split(",") if x.strip()]:
        if d not in by_doi:
            sys.exit(f"Research page lists a DOI that is not in publications.json: {d}")
        items.append(f"<li>{link_cite(by_doi[d])}</li>")
    return '<ul class="kp-list">' + "".join(items) + "</ul>"


def main() -> None:
    global PREVIEW
    args = sys.argv[1:]
    remote = "--remote-images" in args
    PREVIEW = "--preview" in args
    cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8")) if (ROOT / "site.json").exists() else {}
    theme = args[args.index("--theme") + 1] if "--theme" in args else cfg.get("theme", "bold")
    if theme not in THEMES:
        sys.exit(f"Unknown theme {theme!r}; choose from {', '.join(THEMES)}")
    # 公開 URL（検索エンジン向けの canonical・サイトマップ用）。独自ドメインなら CNAME を優先
    if (ROOT / "CNAME").exists():
        site_url = "https://" + (ROOT / "CNAME").read_text(encoding="utf-8").strip() + "/"
    else:
        site_url = cfg.get("url", "https://hideyuki-doi.github.io/").rstrip("/") + "/"
    db = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    pubs = db["publications"]
    arts = [p for p in pubs if p["type"] == "article"]
    books = [p for p in pubs if p["type"] == "book"]
    japanese = [p for p in pubs if p["type"] == "japanese"]
    arts.sort(key=lambda p: (-p["year"], -(int(p["id"]) if p["id"].isdigit() else 0)))
    counts = Counter(p["year"] for p in arts)
    first, last = min(counts), max(max(counts), dt.date.today().year)

    groups = []
    for y in sorted(counts, reverse=True):
        items = "".join(render_pub(p, remote) for p in arts if p["year"] == y)
        groups.append(f'<section class="year-group" id="pub-{y}" data-group="{y}">'
                      f'<h3 class="year-head">{y} <span class="year-n">{counts[y]} '
                      f'paper{"s" if counts[y] != 1 else ""}</span></h3>'
                      f'<ol class="pub-list">{items}</ol></section>')

    tpl = (SRC / "index.html").read_text(encoding="utf-8")
    tpl = tpl.replace("{{HOME}}", (SRC / "themes" / f"{theme}.home.html").read_text(encoding="utf-8"))
    for _ in range(3):  # partials may contain partials (e.g. icons inside the topic list)
        tpl = re.sub(r"\{\{PART:([\w-]+)\}\}",
                     lambda m: (SRC / "partials" / f"{m.group(1)}.html").read_text(encoding="utf-8"), tpl)
    values = {
        "STYLE": (SRC / "base.css").read_text(encoding="utf-8") + "\n"
                 + (SRC / "themes" / f"{theme}.css").read_text(encoding="utf-8"),
        "THEME": theme,
        "FONTS": THEMES[theme].replace("&", "&amp;"),
        "SCRIPT": (SRC / "app.js").read_text(encoding="utf-8"),
        "PUB_COUNT": str(len(arts)),
        "BOOK_COUNT": str(len(books)),
        "FIRST_YEAR": str(first),
        "PUBLICATIONS": "\n".join(groups),
        "BOOKS": "".join(render_pub(p, remote) for p in books),
        "JAPANESE": "".join(render_pub(p, remote) for p in japanese),
        "YEAR_OPTIONS": "".join(f'<option value="pub-{y}">{y}</option>' for y in sorted(counts, reverse=True))
                        + '<option value="pub-japanese">Papers in Japanese</option>'
                        + '<option value="pub-books">Books</option>',
        "SITE_URL": site_url,
        "UPDATED": dt.date.today().strftime("%-d %B %Y"),
        "YEAR": str(dt.date.today().year),
    }
    by_doi = {p["doi"].lower(): p for p in pubs if p.get("doi")}
    tpl = re.sub(r"\{\{PAPERS:([^}]+)\}\}", lambda m: papers_block(m.group(1), by_doi), tpl)
    out = re.sub(r"\{\{IMG:([\w-]+)\}\}", lambda m: img_src(m.group(1), remote), tpl)
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_:]+\}\}", out)
    if left:
        sys.exit(f"Unfilled placeholders: {left}")

    if PREVIEW:
        out_file = ROOT / f"preview-{theme}.html"
        out_file.write_text(out, encoding="utf-8")
        print(f"Preview written: {out_file.name} ({len(out) // 1024} KB)")
        return
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "index.html").write_text(out, encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    fav = ROOT / "assets" / "img" / IMAGES["favicon"][0]
    if fav.exists():
        write_favicon_ico(fav, OUT / "favicon.ico")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site_url}sitemap.xml\n")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{site_url}</loc><lastmod>{dt.date.today().isoformat()}</lastmod></url>\n"
        "</urlset>\n", encoding="utf-8")
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    print(f"Built _site/index.html (theme: {theme}): {len(arts)} articles, {len(japanese)} in Japanese, {len(books)} books, "
          f"{len(out) // 1024} KB")


if __name__ == "__main__":
    main()
