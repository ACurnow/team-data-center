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

## Next version (v2), in progress / 改良版（作業中）

- **Several data centers.** Each user is served by one of them, and each center has its own monthly limit on waste heat.
- **Discrete pipe sizes,** each with a capacity and a cost per metre.
- **Network temperature.** Compare two designs:
  - a loop at about 30 °C with heat pumps at the users, and direct use where the user's temperature allows;
  - a central heat pump that raises the network to 60 °C.
- **Uncertainty.** The IT loads are not published, and the kerosene price varies. Two versions handle this:
  - a two-stage stochastic version: pipes are fixed first, and the monthly operation adapts to each scenario;
  - robust versions: the worst case, the minimum of the maximum regret, and a budgeted uncertainty set solved by column-and-constraint generation.

## Open questions / 未解決の問い

- What are the temperature and the recoverable share of waste heat for each cooling type in the Ishikari data centers?
- What are the heat losses and the installed cost of buried pipes in Hokkaido?
- How should the cost of a shared trunk be split fairly among users (a cooperative game: core, Shapley value)?
