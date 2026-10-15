# ecologyweb

土居秀幸（京都大学大学院情報学研究科 生物圏情報学講座）のウェブサイト。
Jimdo Free（ecologyweb.jimdofree.com）から GitHub Pages へ移行したものです。

## 仕組み

- `src/index.html` … ページの文章（Home / Research / 研究室紹介 / Members / Publications / CV）
- `src/base.css`, `src/themes/`（各案のCSSとトップページ）, `src/partials/`（研究テーマ・募集文）, `src/app.js` … デザインと動き
- `site.json` … 使うデザインテーマ（`bold` / `sidebar` / `banner`）
- `data/publications.json` … 論文リスト（自動更新される）
- `assets/img/` … 写真・ロゴ（初回実行時に Jimdo から自動でコピー）
- `scripts/build.py` … 上記を組み合わせて `_site/` を作る

GitHub Actions が **push のたび** と **毎週月曜 6:00** に動き、
論文の追加 → ビルド → 公開 まで自動で行います。

## 最初のセットアップ（1回だけ）

1. GitHub で新しいリポジトリ `hideyuki-doi.github.io`（Public）を作り、このフォルダの中身を push
2. リポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にする
3. **Actions** タブ → 「Update publications & deploy site」→ **Run workflow**
   - Jimdo の写真・ロゴが `assets/img/` に保存され、新しい論文があれば追加されます
4. 数分後、`https://hideyuki-doi.github.io/` で公開されます

独自ドメインを使う場合は、ドメイン名だけを書いた `CNAME` ファイルをリポジトリ直下に置き、
Settings → Pages の Custom domain に同じドメインを入れてください。

## デザインの切り替え

`site.json` の `"theme"` を `bold`（案A）、`sidebar`（案B）、`banner`（案C）のどれかに書き換えて push するだけで切り替わります。

## 論文の追加

- **自動**：ORCID（0000-0002-2701-3982）と Crossref を毎週確認し、
  前年以降の新しい論文を追加します。「in press」「online available」の論文は、
  巻・ページが付いた時点で自動更新されます。新しく入った論文には黄色の印が60日間付きます。
- **すぐ追加したいとき**：`data/add_dois.txt` に DOI を1行書いて push
- **追加させたくない論文**（別人の論文など）：`data/exclude_dois.txt` に DOI を書いて、
  `data/publications.json` から該当項目を削除
- **手で直したいとき**：`data/publications.json` の `html` を直接編集
  （`<strong>` が太字、`<em>` が斜体、`<sup>*</sup>` が責任著者の印）

## DOI と写真のチェック

Actions が動くたびに、全論文の DOI を Crossref で照合し（存在するか・タイトルが一致するか）、
写真の取り込み元 URL も確認します。結果は Actions の実行画面の **Summary** に出ます。
手元で確かめるときは `python scripts/check_links.py` を実行してください。

## Claude Code での編集

このフォルダで Claude Code を開き、例えば次のように頼めば編集できます。

- 「Members に D1 の〇〇さんを追加して」
- 「研究室紹介の学生構成を2026年4月現在に更新して」
- 「CV の Awards に〇〇賞を追加して」

編集したら commit して push すれば、数分でサイトに反映されます。

手元で確認する場合：

```bash
python scripts/build.py
python -m http.server -d _site 8000   # http://localhost:8000 を開く
```
