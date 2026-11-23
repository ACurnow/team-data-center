# Team Data Center

Optimization for data centers in Ishikari, Hokkaido. The work asks three questions: where should the waste heat go, how much new load can the power grid host, and where should the next data center be built?

石狩（北海道）のデータセンターの最適化です。排熱をどこへ届けるか、電力系統が新しい負荷をどれだけ受け入れられるか、次のデータセンターをどこに建てるか、の3つを扱います。

The work started at Hack × Hokkaido Build Week 2026 (Sapporo, November 2026). We plan to continue it as a research project.
Hack × Hokkaido Build Week 2026（2026年11月、札幌）で始め、その後も研究として続ける予定です。

## Themes / テーマ

| | Theme | テーマ | Model |
|---|---|---|---|
| 1 | **Waste-heat networks.** Which users (greenhouses, fish farms, snow melting, baths) connect to which data center, with which pipes | **排熱の導管網。** どの施設（温室・陸上養殖・融雪・浴場）を、どのデータセンターに、どの太さの管でつなぐか | Network-design MILP with monthly heat balances; stochastic and robust versions |
| 2 | **Grid hosting capacity.** How much data-center and heat-pump load each grid location can take | **系統の受け入れ余地。** データセンターとヒートポンプの負荷を、系統のどこにどれだけ受け入れられるか | AC optimal power flow with convex (SDP/SOCP) relaxations |
| 3 | **Siting.** Where the next data center should go, given heat users, grid capacity, renewables, fiber and land | **立地。** 熱の使い手、系統の余地、再エネ、通信、土地から、次のデータセンターの場所を選ぶ | Facility-location MILP using the results of themes 1 and 2 |

## Layout / 構成

```
src/dcopt/heat      theme 1
src/dcopt/grid      theme 2
src/dcopt/siting    theme 3
src/dcopt/common    shared code: road network, data, solvers, uncertainty
app/                the demo app
experiments/        reproducible experiments (config + script; results are not committed)
docs/               model formulations, data sources, literature
data/curated/       small tables we compiled ourselves, each value with its source
```

## Quick start / 使い方

```bash
uv sync
uv run pytest
```

## Solvers and data / ソルバーとデータ

- **Solvers / ソルバー**
  - The defaults are open source: HiGHS for MILP/LP, and Clarabel or SCS for conic problems (`uv sync --extra conic`). Gurobi is an option (`uv sync --extra gurobi`), never a requirement. Solver license files are never committed.
  - 既定はオープンソースのソルバーです（MILP/LPはHiGHS、錐計画はClarabelかSCS）。Gurobiは任意で、なくても動きます。ライセンスファイルはコミットしません。
- **Numbers / 数字**
  - Every number has a source or is marked as an assumption. See [docs/data-sources.md](docs/data-sources.md).
  - すべての数字に出典を付けるか、仮定と明記します。
- **Downloaded data / 取得するデータ**
  - Scripts download OpenStreetMap data (© OpenStreetMap contributors, ODbL) and other licensed data into `data/raw/` and `data/cache/`. These folders are not committed.
  - OpenStreetMap（ODbL）など、ライセンスの異なるデータはスクリプトで取得し、リポジトリには入れません。

## Team / メンバー

Adam Curnow, Junko, Lia Vergou, Noriyuki Sugita, Paul Binder, Seiko Yamaguchi, Thomas Braam

## License / ライセンス

The code is under the MIT license ([LICENSE](LICENSE)). Data from other sources keeps its own license. To cite this work, see [CITATION.cff](CITATION.cff).
コードはMITライセンスです。外部のデータは、それぞれのライセンスに従います。
