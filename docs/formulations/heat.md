# Theme 1: waste-heat network design / 排熱の導管網

The model decides which heat users to connect to which data center, along which streets and with which pipes. It maximizes the value of the heat delivered minus the annualized pipe cost.

どの施設を、どのデータセンターに、どの道路沿いに、どの太さの管でつなぐかを決めます。届けた熱の価値から導管費の年額を引いた値を最大にします。

## Prototype formulation (v1) / 試作版の定式化

**Sets.** Node $0$ is the data center. $U$ is the set of users. The candidate street links $E$ are each node's 3 nearest neighbours by road distance plus direct links from the data center, all within 8 km. The arcs $A$ are both directions of each link. The months are $T = \{1,\dots,12\}$.

**Data.**
- $\ell_e$: road length of link $e$
- $p$: pipe cost per metre
- $\mathrm{CRF}$: capital recovery factor (3 %, 30 years)
- $D_{ut}$: demand of user $u$ in month $t$
- $W_t$: recoverable waste heat in month $t$
- $\mathrm{COP}$: coefficient of performance of the heat pump
- $v$: value per MWh delivered, equal to the avoided kerosene cost minus the heat-pump electricity cost

**Variables.**
- $y_e \in \{0,1\}$: build link $e$
- $x_u \in \{0,1\}$: connect user $u$
- $g_{ua} \in [0,1]$: flow of user $u$'s commodity on arc $a$
- $s_{ut} \ge 0$: heat delivered to $u$ in month $t$

$$\max \; \sum_{u \in U}\sum_{t \in T} v\, s_{ut} \;-\; \sum_{e \in E} \mathrm{CRF}\, p\, \ell_e\, y_e$$

subject to
- **flow balance** for each user's commodity: one unit leaves node 0 and reaches $u$ when $x_u = 1$;
- $g_{u,(i,j)} + g_{u,(j,i)} \le y_e$ for each user $u$ and link $e = \{i,j\}$ (strong linking);
- $s_{ut} \le D_{ut}\, x_u$ for each user and month;
- $\sum_{u} (1 - 1/\mathrm{COP})\, s_{ut} \le W_t$ for each month (waste heat available).

This is a prize-collecting Steiner tree with monthly capacities, written in multi-commodity form, and solved with HiGHS.

**Baseline.** Score each user alone, with its own pipe from the data center, and take the best five ("top-5 pairs"). On the prototype data, the network gave 2.1 to 3.4 times the annual net benefit of the top-5 pairs across the price and pipe-cost cases tried.

## Version 2 (`dcopt.heat.network`) / 改良版

**Sets.**
- $D$: data centers — Ishikari RE DC No. 1, Sakura, KCCS ZED, and NTT-ME (planned).
- $U$: users.
- $E$: candidate links. Each user links to its nearest data center, data centers link to each other, and each node links to its nearest neighbours.
- $K$: pipe sizes DN50, 80, 100, 150, 200, 250.
- $T$: months.
- $\Omega$: scenarios, with probabilities $p_\omega$.

**First stage.**
- $y_{ek} \in \{0,1\}$: build link $e$ with size $k$.
- $x_u \in \{0,1\}$: connect user $u$.
- $z_{ud} \in \{0,1\}$: user $u$ is served by data center $d$.
- $g_{ua} \in [0,1]$: share of $u$'s commodity on arc $a$.

**Second stage.** $s_{udt\omega} \ge 0$ is the heat delivered from $d$ to $u$ in month $t$ under scenario $\omega$.

**Net benefit per scenario.**
$$\mathrm{net}_\omega = \sum v_{u\omega}\, s_{udt\omega} - \mathrm{CRF} \sum c_k \ell_e y_{ek} - \mathrm{CRF}_{hp} \sum h_u x_u$$

**Objectives.**
- Expected: $\max \sum_\omega p_\omega\, \mathrm{net}_\omega$.
- Worst case: $\max \eta$ subject to $\eta \le \mathrm{net}_\omega$ for every $\omega$.
- Minimum of the maximum regret: $\min \rho$ subject to $\rho \ge \mathrm{OPT}_\omega - \mathrm{net}_\omega$ for every $\omega$.

**Constraints.**
- Flow of $g_u$: out minus in equals $z_{ud}$ at data center $d$, $-x_u$ at the user, and $0$ elsewhere.
- One data center per user: $\sum_d z_{ud} = x_u$.
- Link by size: $g_{u,(i,j)} + g_{u,(j,i)} \le \sum_{k:\,\mathrm{cap}_k \ge q_u} y_{ek}$.
- At most one size per link: $\sum_k y_{ek} \le 1$.
- Pipe capacity: $\sum_u q_u (g_{u,(i,j)} + g_{u,(j,i)}) \le \sum_k \mathrm{cap}_k\, y_{ek}$.
- Delivery only to the assigned data center: $s_{udt\omega} \le \mathrm{cap}_{ut}\, z_{ud}$.
- Waste heat per data center: $\sum_u r_u\, s_{udt\omega} \le W_{dt\omega}$.

**Temperature modes.**
- *Ambient:* a loop at about 30 °C with ΔT 10 K and 2 % heat loss.
  - Each user has its own heat pump, with COP = 0.5 × Carnot from 25 °C, capped at 8.
  - Users that need 27 °C or less take the heat directly.
- *Central:* the network runs at 60 °C, with ΔT 30 K, COP 4.76 and 8 % heat loss.

**Robust version.**
- Uncertainty set: at most $\Gamma$ data centers run at the low end of their IT-load range.
- Solved by column-and-constraint generation:
  - the master problem is the worst-case model over the corners found so far;
  - the subproblem evaluates every corner, one LP each.
- The kerosene price stays outside the budget; its effect is shown through regret.

**Solving.**
- HiGHS is the default; Gurobi is optional (`DCOPT_SOLVER=gurobi`).
- Pipe sizing weakens the LP bound, so the full MILP does not close in 60 s.
- The default method is an LP-guided kernel search: solve the LP relaxation, then solve the MILP restricted to the links the LP uses plus each data center's own plan.
- Every plan is then re-evaluated with exact recourse.
- The gaps against HiGHS bounds are 13–21 %, so **the plans are not certified optimal**. Gurobi reaches 4.7–9 % in 60 s.

**Check against v1.** Restricted to one data center, one large pipe size at 100,000 yen/m, COP 4 and no loss, version 2 reproduces version 1 exactly: 15 sites, 16.1 km, 137.5 M yen/year.

### Results so far, heat-pump investment included / これまでの結果（ヒートポンプの設備費込み）

Four scenarios with equal weights: IT load low or high, crossed with kerosene at 115 or 156.8 yen/L. Heat pumps cost 150 M yen/MW at the users (assumption) and 100 M yen/MW centrally (Odense data). Annual net benefit, million yen. Run logs: `results/` (commit fe6fdf9 and 86ef0cf).

| Mode | Plan | Sites | Pipe km | Expected | Worst case | Max regret | Payback |
|---|---|---|---|---|---|---|---|
| ambient | stochastic | 6 | 5.0 | 85.3 | 59.9 | 17.8 | 8.7 y |
| ambient | worst case | 5 | 3.0 | 80.6 | 61.2 | 28.6 | 5.9 y |
| ambient | min-max regret | 6 | 5.0 | 85.3 | 59.9 | 17.8 | 8.7 y |
| central | stochastic | 10 | 7.5 | 62.6 | 17.9 | 14.8 | 11.9 y |
| central | worst case | 5 | 3.0 | 52.1 | 32.7 | 36.1 | 6.7 y |
| central | min-max regret | 8 | 6.3 | 62.1 | 25.0 | 8.3 | 10.8 y |

- Without heat-pump investment the stochastic plans reach 121.5 (ambient, 8 sites) and 115.8 (central, 13 sites).
- Value of the stochastic solution: 0.4 (ambient), 2.6 (central). Expected value of perfect information: 9.0 and 7.5.

**Each data center on its own: optimized network vs the top-5 pairs** (expected net)

| Data center | Ambient, optimized | Ambient, pairs | Central, optimized | Central, pairs |
|---|---|---|---|---|
| No. 1 | 84.5 | 65.3 | 62.6 | 40.4 |
| Sakura | 81.6 | 58.4 | 59.5 | 37.2 |
| ZED | 80.6 | 59.6 | 52.1 | 36.8 |
| NTT-ME (planned) | 3.8 | 0.8 | 0.0 | 0.0 |

The pair-by-pair approach reaches 63–77 % of the optimized network.

**Robust sweep over Γ** (kerosene at 115 yen/L):
- *Ambient.* The Γ = 0 plan earns 66.0 but connects one site to the planned NTT-ME center. If that center runs low or is not built, the plan falls to 33.0. The robust plan for every Γ ≥ 1 (5 sites on ZED) keeps 61.2 in every case, so the price of robustness is 7.3 %.
- *Central.* With heat-pump investment, every Γ gives the same robust plan: 5 sites on ZED, 32.7.

**What the results say.**
- Once heat pumps are paid for, the ambient loop clearly beats the central heat pump (85.3 against 62.6 expected), because the fish farm and snow melting take the heat directly.
- Waste heat is plentiful in the port area once four data centers are counted. IT-load uncertainty therefore matters mainly when a plan leans on a small or planned center.
- The kerosene price drives the plan. Regret shows its effect most clearly.

**Caveats.**
- The locations of No. 1 and ZED are approximate, and NTT-ME's is a placeholder. The robust plans pick ZED, so these locations must be checked before any conclusion is drawn. Sakura gets no partners in the regional plans.
- No. 1's top partner is the assumed fish farm, at a placeholder location.
- The model uses monthly energy only, with no hourly peaks and no storage.
- In ambient mode the largest pipe size (DN250) carries 4.6 MW; larger trunk sizes should be added.
- The peak factors, temperatures, velocities, the pipe-cost line and the heat-pump cost at the users are assumptions.

## Open questions / 未解決の問い

- What are the temperature and the recoverable share of waste heat for each cooling type in the Ishikari data centers?
- What are the heat losses and the installed cost of buried pipes in Hokkaido? What do heat pumps cost?
- Can a stronger pipe-sizing formulation (cut-set inequalities, Benders cuts) let HiGHS certify the plans?
- Can topology, temperature mode and heat-pump placement be co-optimized at street scale? We did not find this in the literature.
- How should the cost of a shared trunk be split fairly? The Shapley value on the fixed tree can be compared with the least core when each coalition's network is re-optimized, with the prize-collecting Steiner tree as the separation problem.
- Two-stage robust design under budgeted IT-load uncertainty, including planned data centers: we did not find a published network design of this kind.
