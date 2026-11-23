# Contributing / 開発のルール

## Workflow / 進め方

- Work on a branch and open a pull request. Another member reviews it before it is merged into `main`.
  ブランチで作業し、プルリクエストを出します。別のメンバーが確認してから `main` に入れます。
- Keep `uv run pytest` passing. CI runs it on every push.
  `uv run pytest` が通る状態を保ちます。CIがpushのたびに実行します。
- Write code, comments and commit messages in English. Text shown to users is in Japanese and English.
  コード・コメント・コミットメッセージは英語で書きます。画面に出す文章は日英併記にします。

## Numbers and sources / 数字と出典

- Every parameter has a source (URL), or it is marked as an assumption with a one-line reason. Record it in `docs/data-sources.md`.
  すべてのパラメータに出典（URL）を付けるか、理由を1行添えて仮定と明記します。`docs/data-sources.md` に記録します。
- Add a paper to `docs/references.bib` only after checking that it exists, by opening its DOI or publisher page.
  文献は、DOIや出版社のページで実在を確かめてから `docs/references.bib` に加えます。

## Data and licenses / データとライセンス

- The repository is under the MIT license. Commit only data that may be shared under MIT, such as our own compilations of facts with their sources.
  リポジトリはMITライセンスです。MITで公開してよいデータ（出典付きで自分たちがまとめた事実など）だけをコミットします。
- Scripts download OpenStreetMap (ODbL) and other licensed data into `data/raw/` and `data/cache/`, which git ignores. Any output that shows OSM data credits "© OpenStreetMap contributors".
  OpenStreetMap（ODbL）などはスクリプトで `data/raw/` と `data/cache/` に取得し、gitには入れません。OSMのデータを表示するときは「© OpenStreetMap contributors」と明記します。
- Never commit solver license files, API keys or `.env` files.
  ソルバーのライセンスファイル、APIキー、`.env` はコミットしません。

## Solvers / ソルバー

- The defaults are open source: HiGHS for MILP/LP, and Clarabel or SCS for conic problems. A commercial solver may be offered as an option, but code must never require one.
  既定はオープンソース（MILP/LPはHiGHS、錐計画はClarabelかSCS）です。商用ソルバーは選べるようにしてもよいですが、必須にはしません。

## Experiments / 実験

- An experiment is a config file plus a script in `experiments/`. Its outputs go to `results/`, which is not committed. Save them together with the git commit, the solver and its version, and the run time.
  実験は `experiments/` の設定ファイルとスクリプトで再現できるようにします。結果は `results/`（コミットしない）に、gitのコミット、ソルバーとそのバージョン、計算時間と一緒に保存します。
