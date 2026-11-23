# Experiments / 実験

Each experiment gets its own folder with a config file and a script: `experiments/<name>/config.toml` and `experiments/<name>/run.py`.
The script writes to `results/<name>/<timestamp>/`, which is not committed. Save the outputs there together with the config used, the git commit, the solver name and version, and the run times.
Copy the tables and figures the team wants to keep into `docs/`.

実験ごとにフォルダを作り、設定ファイル（config.toml）と実行スクリプト（run.py）を置きます。
結果は `results/`（コミットしない）に保存します。使った設定、gitのコミット、ソルバーとそのバージョン、計算時間も一緒に残します。
残したい表や図は `docs/` にコピーします。
