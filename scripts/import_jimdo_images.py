#!/usr/bin/env python3
"""Jimdo サイトの写真・ロゴを assets/img/ にダウンロードする（既にあるファイルは飛ばす）。"""
import sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from site_images import IMAGES

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)
for name, (fname, urls) in IMAGES.items():
    dest = OUT / fname
    if dest.exists() and dest.stat().st_size > 0:
        continue
    if not urls:
        continue
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ecologyweb migration)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 500 or not (data[:3] == b"\xff\xd8\xff" or data[:4] == b"\x89PNG"):
                raise ValueError("not an image")
            dest.write_bytes(data)
            print(f"saved {fname} ({len(data) // 1024} KB)")
            break
        except Exception as e:  # noqa: BLE001
            print(f"  {name}: {url} failed ({e})")
    else:
        print(f"::warning::could not download {name}; the site will link to Jimdo's copy for now")
