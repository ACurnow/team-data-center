# Theme 2: grid hosting capacity / 系統の受け入れ余地

This theme estimates how much additional load each candidate grid location can take within voltage, line and generator limits. The load comes from data centers and from the heat pumps of theme 1.

データセンターと（テーマ1の）ヒートポンプの負荷を、電圧・送電線・発電機の制約の中で、系統のどこにどれだけ追加できるかを見積もります。

## Planned formulation / 予定している定式化

The hosting capacity at a set of buses $B'$ is $\max \lambda$, subject to:
- the AC power-flow equations, with an added load $\lambda\,\Delta P_b$ at each $b \in B'$;
- voltage limits;
- line limits;
- generator limits.

**Convex relaxations.** Replace $W = V V^{H}$ either by $W \succeq 0$ (an SDP, with chordal decomposition to use sparsity) or by its second-order cone relaxation. The relaxation gives an upper bound on $\lambda$. When the optimal $W$ has rank one, the bound is attained and the voltages can be read back from $W$.

## Data / データ

- Open test systems (PGLib-OPF), to check the method.
- A synthetic grid for the Ishikari area built from public information: OpenStreetMap power lines and substations, and their voltage classes. Impedances and limits are marked as assumptions.
- Public data from Hokkaido Electric Power Network: available-capacity maps and hourly supply and demand.

## Open questions / 未解決の問い

- Is the relaxation exact on the Ishikari synthetic grid? If not, how far is the bound from a feasible point?
- How much more load can the grid host if data centers accept curtailment for a few hours a year?
