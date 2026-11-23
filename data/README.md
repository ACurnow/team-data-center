# Data / データ

- `curated/` holds small tables we compiled ourselves from public sources. Every row names its source. They are shared under the repository's MIT license.
  `curated/`：公開情報から自分たちでまとめた小さな表です。各行に出典を書き、MITライセンスで公開します。
- `raw/` and `cache/` hold data downloaded by scripts, such as OpenStreetMap (© OpenStreetMap contributors, ODbL 1.0). They are not in git. Rebuild them with the scripts; do not commit them.
  `raw/` と `cache/`：スクリプトで取得するデータ（OpenStreetMapなど、ODbL 1.0）です。gitには入れず、スクリプトで作り直します。

When coordinates come from a licensed source, they are not stored in `curated/`. The scripts look them up at build time.
ライセンス付きの出典から得た座標は `curated/` に保存しません。スクリプトが実行時に取得します。
