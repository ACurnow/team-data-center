# Theme 3: data-center siting / 次のデータセンターの立地

This theme chooses where the next data center(s) in Hokkaido should go, from a set of candidate sites. It weighs:
- the value of the waste heat (theme 1);
- the grid's hosting capacity (theme 2);
- renewable supply;
- fiber and latency;
- land;
- hazards.

熱の使い道（テーマ1）、系統の受け入れ余地（テーマ2）、再エネ、通信と遅延、土地、災害リスクから、次のデータセンターの候補地を選びます。

## Planned formulation / 予定している定式化

- **Sites.** $J$ is the set of candidate sites. $z_j \in \{0,1\}$ opens site $j$.
- **Load.** The IT load at site $j$ is $L_j \le H_j$, where $H_j$ is the hosting capacity from theme 2.
- **Heat value.** $h_j(L_j)$ is the value of the site's waste heat from theme 1, piecewise linear in the load.
- **Costs.** Land, grid connection and fiber.
- **Limits.** Hazards and latency enter as constraints.
- **Objective.** Total net value.
- **Uncertainty.** Future demand and prices are modelled as scenarios or as an uncertainty set.

## Open questions / 未解決の問い

- Which criteria change the ranking of sites, and by how much?
- How robust is the choice when future data-center demand is uncertain?
