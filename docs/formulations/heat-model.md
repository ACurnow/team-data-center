# Theme 1: the waste-heat network model, in full

This page states the model in `src/dcopt/heat/network.py` (version 2) completely: every set, coefficient, variable, constraint and objective, how each coefficient is computed, and worked numbers. Results are in [heat.md](heat.md). Reference numbers in square brackets point to the list in the [README](../README.md#references).

**In one sentence.** Choose which streets get a pipe and of which size, which users connect and to which data center, and how much heat each user receives each month, so that the value of the kerosene replaced, minus heat-pump electricity and the annualized cost of pipes and heat pumps, is as large as possible: in expectation over scenarios, in the worst scenario, or with the smallest regret.

**Structure.** It is a mixed-integer linear program:
- a prize-collecting Steiner network [23, 24] in strong multi-commodity form, with discrete pipe sizes and several sources;
- twelve monthly heat balances per scenario;
- a first stage (the network) and a second stage (monthly deliveries), which makes it a two-stage stochastic program, or a two-stage robust program with a budgeted uncertainty set [31, 32, 34].

## 1. Sets and indices

| Symbol | Meaning |
|---|---|
| $\mathcal D$ | data centers (heat sources): Ishikari RE DC No. 1, Sakura, KCCS ZED, NTT-ME (planned) |
| $\mathcal U$ | heat users (candidate sites) |
| $\mathcal N = \mathcal D \cup \mathcal U$ | nodes; $n(u)$ is user $u$'s node |
| $\mathcal E$ | candidate links $e=\{i,j\}$ between nodes, each a shortest road path |
| $\mathcal A$ | arcs: both directions $(i,j)$ and $(j,i)$ of every link |
| $\delta^+(i), \delta^-(i)$ | arcs leaving and entering node $i$ |
| $\mathcal K$ | pipe sizes DN50, DN80, DN100, DN150, DN200, DN250 |
| $\mathcal T = \{1,\dots,12\}$ | months |
| $\Omega$ | scenarios $\omega$ with probabilities $p_\omega$ |

**Candidate links.** Each node is linked to its $k=3$ nearest nodes by road distance. Each user is also linked to its nearest data center, and the data centers are linked to each other. Links longer than 8 km are dropped. With 4 data centers and 50 users this gives about 120 links.

## 2. Coefficients and how they are computed

### 2.1 Monthly demand

Each user $u$ of kind $\kappa(u)$ has an annual heat demand $A_u$ (MWh/yr): a default per kind, or floor area × intensity for greenhouses (0.40 MWh/m²/yr) and snow-melting areas (0.12 MWh/m²/yr). All of these are assumptions; see [data-sources.md](../data-sources.md).

The annual demand is spread over the months by a profile $\pi_{\kappa t}$ built from the JMA climate normals for Sapporo, 1991–2020 [12]:

$$D_{ut} = A_u\,\pi_{\kappa(u),t}, \qquad \sum_t \pi_{\kappa t} = 1 .$$

With mean temperature $\bar\theta_t$, $\mathrm{days}_t$ days in the month and base temperature $T_b$, heating degree-days are

$$\mathrm{HDD}_t(T_b) = \mathrm{days}_t\,\max(0,\;T_b - \bar\theta_t).$$

| Profile | $\pi_t$ proportional to | Used for |
|---|---|---|
| building | $\mathrm{HDD}_t(18\,^\circ\mathrm C)$ | hospitals, public buildings |
| greenhouse | $\mathrm{HDD}_t(15\,^\circ\mathrm C)$ | greenhouses |
| school | $\mathrm{HDD}_t(18)$, with August × 0.3 | schools |
| pool | $\tfrac12\,\mathrm{days}_t/365 + \tfrac12\,\mathrm{HDD}_t(18)/\sum\mathrm{HDD}(18)$ | pools, baths, hotels |
| snow | monthly snowfall | snow melting |
| flat | $\mathrm{days}_t$ | fish farm, factory |

The month has $h_t = 24\,\mathrm{days}_t$ hours, and the mean load is $\mu_{ut} = D_{ut}/h_t$ (MW).

### 2.2 Design peak and what a connection can deliver

**Design peak.** The design peak is the mean load of the heaviest month times a peak factor $f_\kappa$ (an assumption per kind: greenhouses 2.5, snow 3.0, buildings 1.8–2.0, pools, baths and hotels 1.4, fish farm and factory 1.2):

$$P_u = f_{\kappa(u)}\,\max_t \mu_{ut}.$$

**Sizing.** Pipes and heat pumps are sized for $c_u = \alpha P_u$, a share $\alpha$ of the peak ($\alpha=1$ by default). The existing boiler covers anything above $c_u$.

**Energy deliverable in a month.** Within a month, the hourly load is taken as spread evenly between $\mu(1-b)$ and $\mu(1+b)$, where $b=\min(f-1,1)$. Write $\ell o = \mu(1-b)$ and $hi = \mu(1+b)$. A connection of size $c$ then delivers the expected value of $\min(L, c)$ over the month:

$$\bar s_{ut} = h_t \cdot \begin{cases}
\mu_{ut} & c_u \ge hi \\
c_u & c_u \le \ell o \\
\dfrac{(c_u^2-\ell o^2)/2 + c_u\,(hi-c_u)}{hi-\ell o} & \text{otherwise.}
\end{cases}$$

**Example: a pool in January.**
- Demand: $A=800$ MWh/yr and $\pi_{\text{Jan}}=0.139$, so $D=111$ MWh and $\mu = 111/744 = 0.149$ MW.
- Spread: $f=1.4$ gives $b=0.4$, $\ell o = 0.089$ MW and $hi = P = 0.209$ MW.
- With $\alpha=1$ the connection delivers all 111 MWh.
- With $\alpha=0.7$ ($c=0.146$ MW) it still delivers $\bar s = 744 \times 0.1326 = 98.6$ MWh, or 89 % of January's demand, from a connection 30 % smaller.

### 2.3 Temperatures, heat pumps and what each MWh costs the network

**Heat-pump COP.** The COP is a fraction $\eta=0.5$ of the Carnot value, capped at 8. Temperatures are in °C and the lift is at least 1 K:

$$\mathrm{COP}(\theta_h,\theta_c) = \min\Big\{8,\; \eta\,\frac{\theta_h+273.15}{\max(\theta_h-\theta_c,\,1)}\Big\}.$$

**Two network designs (modes).**
- **Ambient loop.** The loop runs at $\theta_{net}=30$ °C, and each user has its own heat pump. The heat pump lifts from $\theta_{net} - 5$ K $=25$ °C to the user's supply temperature $\theta_u$:
  - greenhouses, schools and public buildings: 45 °C;
  - pools: 40 °C;
  - baths, hospitals, hotels and factories: 60 °C.
  
  A user that needs at most $\theta_{net} - 3$ K $= 27$ °C takes the heat directly: the fish farm (22 °C) and snow melting (25 °C).
- **Central heat pump.** A heat pump at the data center lifts 25 °C to 60 °C for everyone, so $\mathrm{COP} = 0.5 \times 333.15/35 = 4.76$.

Examples in ambient mode: 45 °C gives $0.5\times318.15/20 = 7.95$; 40 °C gives 10.4, capped at 8; 60 °C gives 4.76.

**Coefficients per MWh delivered to user $u$.** These are the electricity $e_u$, the waste heat drawn $r_u$, and the share of the delivered heat that travels through the pipes $\sigma_u$. The network heat loss is $\lambda$ = 2 % (ambient) or 8 % (central).

| Mode and user | $e_u$ (MWh el.) | $r_u$ (MWh waste heat) | $\sigma_u$ (network share) |
|---|---|---|---|
| ambient, heat pump at the user | $1/\mathrm{COP}_u$ | $(1-1/\mathrm{COP}_u)(1+\lambda)$ | $1-1/\mathrm{COP}_u$ |
| ambient, direct use | $0$ | $1+\lambda$ | $1$ |
| central | $(1+\lambda)/\mathrm{COP}$ | $(1+\lambda)(1-1/\mathrm{COP})$ | $1$ |

In ambient mode the pipes carry only the low-temperature part of the heat; the user's heat pump adds the electricity on site.

### 2.4 Value of a delivered MWh

Each MWh delivered replaces kerosene burned in a boiler with efficiency $\eta_b = 0.85$. Kerosene's lower heating value is 9.7 kWh/L, so one MWh replaces $1000/(9.7 \times 0.85) = 121.3$ L. With the kerosene price $p^{ker}_\omega$ (yen/L) and the electricity price $p^{el} = 25$ yen/kWh:

$$v_{u\omega} = \frac{1000\,p^{ker}_\omega}{9.7\,\eta_b} - 1000\,p^{el}\,e_u \qquad \text{(yen/MWh)}.$$

| Kerosene price | Replaced fuel per MWh | Value, direct use ($e_u=0$) | Value with a COP 8 heat pump ($e_u=0.125$) |
|---|---|---|---|
| 115 yen/L (conservative bulk price, an assumption) | 13,948 yen | 13,948 yen/MWh | 10,823 yen/MWh |
| 156.8 yen/L (survey of 16 Nov 2026 [11]) | 19,018 yen | 19,018 yen/MWh | 15,893 yen/MWh |

**CO₂ avoided.** It is $2.49/(9.7 \times 0.85) = 0.302$ t per MWh. Heat-pump electricity from the grid (0.55 t/MWh) is subtracted in ambient mode; the central heat pump runs on the data center's renewable power.

### 2.5 Pipes

A pipe of size $k$ is a pre-insulated twin pipe with inner diameter $d_k$ (JIS G 3452) and a design velocity $w_k$ (1.0 m/s at DN50, rising to 2.2 m/s at DN250; an assumption). Its capacity at a supply–return difference $\Delta T$ (10 K ambient, 30 K central) is

$$\bar Q_k = \rho\, w_k\, \frac{\pi d_k^2}{4}\, c_p\, \Delta T \,/\, 1000 \quad \text{(MW)}, \qquad \rho = 990\ \mathrm{kg/m^3},\; c_p = 4.18\ \mathrm{kJ/(kg\,K)}.$$

For example, DN150 has $d=0.1552$ m and $w=1.8$ m/s, so it carries 33.7 kg/s. That is $\bar Q = 1.41$ MW at 10 K and 4.23 MW at 30 K.

Installed cost per metre of route follows a straight line through the 2019 quotes for small networks [15], plus 33 % overhead (an assumption):

$$c_k = 1.33\,\Big(40{,}000 + (\mathrm{DN}_k - 25)\,\frac{210{,}000}{225}\Big)\ \text{yen/m}.$$

DN150 costs 208,367 yen/m. DN80 costs 121,473 yen/m and carries 0.25 MW (ambient), while DN250 costs 332,500 yen/m and carries 4.62 MW. Per MW carried, the large pipe is about 7 times cheaper.

**Pipe load of a user.** At peak, user $u$ puts this load on every pipe along its path:

$$q_u = c_u\,\sigma_u\,(1+\lambda) = \alpha P_u\,\sigma_u\,(1+\lambda) \quad \text{(MW)}.$$

### 2.6 Heat pumps, annuities and waste heat

**Heat-pump investment.** The investment for user $u$ is $H_u = c_u \cdot h^{user}$ when the user has its own heat pump (ambient) and $H_u = c_u \cdot h^{central}$ in central mode:
- $h^{user} = 150$ M yen/MW, an assumption for small heat pumps;
- $h^{central} = 100$ M yen/MW, from Odense, where two ammonia heat pumps cost about €0.65 M per MW of heat [16].

**Annuities.** Costs are annualized with the capital recovery factor $\mathrm{CRF}(r,n) = r(1+r)^n/((1+r)^n-1)$ at $r = 3$ %:
- pipes over 30 years: $\mathrm{CRF}_p = 0.0510$;
- heat pumps over 20 years: $\mathrm{CRF}_{hp} = 0.0672$.

**Waste heat.** Data center $d$ in scenario $\omega$ has IT load $L_{d\omega}$ (MW). With a recoverable share $\rho^{rec} = 0.6$ (an assumption), its recoverable waste heat is

$$W_{dt\omega} = L_{d\omega}\, h_t\, \rho^{rec}\quad \text{(MWh)}.$$

At 10 MW in January this is $10 \times 744 \times 0.6 = 4{,}464$ MWh.

## 3. Decision variables

| Variable | Domain | Stage | Meaning |
|---|---|---|---|
| $y_{ek}$ | $\{0,1\}$ | 1 | build link $e$ with pipe size $k$ |
| $x_u$ | $\{0,1\}$ | 1 | connect user $u$ |
| $z_{ud}$ | $\{0,1\}$ | 1 | user $u$ is served by data center $d$ |
| $g_{ua}$ | $[0,1]$ | 1 | share of user $u$'s commodity on arc $a$ (its path from its data center) |
| $s_{udt\omega}$ | $\ge 0$ | 2 | MWh delivered from $d$ to $u$ in month $t$ under scenario $\omega$ |

## 4. Constraints

**(C1) Flow of each user's commodity.** One unit leaves the chosen data center and arrives at the user:

$$\sum_{a\in\delta^+(i)} g_{ua} - \sum_{a\in\delta^-(i)} g_{ua} =
\begin{cases} z_{ud} & i = d \in \mathcal D\\ -x_u & i = n(u)\\ 0 & \text{otherwise}\end{cases}
\qquad \forall u,\ i.$$

**(C2) One data center per user.** A connected user is served by exactly one data center; a user that is not connected by none:

$$\sum_{d} z_{ud} = x_u \qquad \forall u.$$

**(C3) At most one pipe size per link.**

$$\sum_{k} y_{ek} \le 1 \qquad \forall e.$$

**(C4) Heat runs only on built pipes that are big enough.** User $u$'s commodity may use link $e$ only if a pipe is built there that could carry $u$'s load on its own:

$$g_{u,(i,j)} + g_{u,(j,i)} \le \sum_{k:\ \bar Q_k \ge q_u} y_{ek} \qquad \forall u,\ e=\{i,j\}.$$

This per-commodity linking is what makes the formulation strong. Its LP relaxation is much tighter than one aggregated flow per arc with a big-M link, the form most district-heating MILPs use [25, 26]. Restricting the sum to sizes that fit $q_u$ is valid and tightens it further.

**(C5) Pipe capacity.** The peak loads of all users whose paths use a link must fit the size built:

$$\sum_{u} q_u\,\big(g_{u,(i,j)} + g_{u,(j,i)}\big) \le \sum_{k} \bar Q_k\, y_{ek} \qquad \forall e.$$

**(C6) Deliveries only to connected users, from their own data center, within what the connection can deliver.**

$$s_{udt\omega} \le \bar s_{ut}\, z_{ud} \qquad \forall u,d,t,\omega.$$

**(C7) Waste heat available at each data center, each month, in each scenario.**

$$\sum_{u} r_u\, s_{udt\omega} \le W_{dt\omega} \qquad \forall d,t,\omega.$$

## 5. Objectives

The annual net benefit of a plan in scenario $\omega$ is

$$N_\omega = \underbrace{\sum_{u,d,t} v_{u\omega}\, s_{udt\omega}}_{\text{kerosene replaced minus electricity}}
\;-\; \underbrace{\mathrm{CRF}_p \sum_{e,k} c_k\, \ell_e\, y_{ek}}_{\text{pipes}}
\;-\; \underbrace{\mathrm{CRF}_{hp} \sum_u H_u\, x_u}_{\text{heat pumps}} .$$

Three objectives are offered. Each is a MILP over (C1)–(C7). For the robust ones a small $\epsilon\,\mathbb E[N]$ ($\epsilon = 10^{-4}$) breaks ties in favor of the better expected value.

| Name | Problem | When to use it |
|---|---|---|
| Expected (stochastic) | $\max\ \sum_\omega p_\omega N_\omega$ | scenarios with credible probabilities |
| Worst case (max-min) | $\max\ \eta \ \ \text{s.t.}\ \ \eta \le N_\omega\ \ \forall\omega$ | protect the weakest scenario |
| Min-max regret | $\min\ \rho \ \ \text{s.t.}\ \ \rho \ge N^\star_\omega - N_\omega\ \ \forall\omega$ | no probabilities; compare each scenario with its own best plan $N^\star_\omega$ [36] |

**Scenarios.** The default set has four scenarios with equal weight: the IT load at every data center is low or high, crossed with kerosene at 115 or 156.8 yen/L.

**Two-stage structure.** $y, x, z, g$ are fixed before the uncertainty resolves. The deliveries $s$ adapt to each scenario.

## 6. Robust design with a budgeted uncertainty set

The IT loads of the data centers are not published; only rough ranges $[L^{lo}_d, L^{hi}_d]$ are known. Following Bertsimas and Sim [31], the uncertainty set lets at most $\Gamma$ data centers sit at their low value at once:

$$\mathcal L(\Gamma) = \big\{L:\ L_d \in \{L^{lo}_d, L^{hi}_d\},\ \ |\{d: L_d = L^{lo}_d\}| \le \Gamma\big\}.$$

$\Gamma = 0$ is the nominal plan. $\Gamma = |\mathcal D|$ protects against all data centers at their low value at once.

The two-stage adjustable robust problem [32, 34] is

$$\max_{(y,x,z,g)\,\in\,\mathcal X}\ \ \min_{L\,\in\,\mathcal L(\Gamma)}\ \ \max_{s\,\in\,\mathcal S(y,x,z;\,L)}\ N(y,x,s),$$

where $\mathcal X$ is (C1)–(C5) and $\mathcal S$ is (C6)–(C7) with $W_{dt} = L_d h_t \rho^{rec}$.

**Why only vertices matter.** $L$ enters only the right-hand side of (C7). More waste heat can never lower the best delivery value. The worst case therefore puts exactly $\min(\Gamma, |\mathcal D|)$ data centers at their low value, and there are $\binom{|\mathcal D|}{\Gamma}$ such corners.

**Column-and-constraint generation** [33]:
1. **Master.** Maximize $\eta$ over the first-stage variables, subject to $\eta \le N(y,x,s^c)$ and $s^c \in \mathcal S(y,x,z;L^c)$ for every corner $c$ found so far. Each corner adds its own copy of the monthly deliveries (new columns) and one epigraph row (a new constraint). The solver's bound on $\eta$ is an upper bound UB on the robust value.
2. **Subproblem.** For the master's network, evaluate every corner. Each evaluation is one LP over $s$. The worst value is a lower bound LB, and the worst corner joins the master.
3. **Stop** when $\mathrm{UB}-\mathrm{LB} \le 0.5\,\%$ of UB, or when the worst corner is already in the master. Runs for larger $\Gamma$ start from the corners found at smaller $\Gamma$, because $\mathcal L(\Gamma-1)\subseteq\mathcal L(\Gamma)$.

**Price of robustness.** For the plan $x^\Gamma$ built for budget $\Gamma$ and the nominal plan $x^0$:

$$\mathrm{PoR}(\Gamma) = \frac{N^{nom}(x^0)-N^{nom}(x^\Gamma)}{N^{nom}(x^0)}.$$

**Kerosene stays outside the budget.** In a max-min model of savings, the worst kerosene price is always the lowest one, so the price would never act as a real adversary. Its uncertainty is shown through regret instead.

## 7. How it is solved

**Solver.** HiGHS (open source) solves the problem through highspy. Gurobi can be used when installed (`DCOPT_SOLVER=gurobi`). The real instance has about 18,000 variables (about 900 binary) and 15,000 rows.

**The difficulty.** Discrete pipe sizes weaken the LP bound, and the full MILP does not close in 60 s.

**The default method is an LP-guided kernel search:**
1. Solve the LP relaxation on all candidate links. Its value bounds the optimum.
2. Keep the links the LP uses (its $y$ above $10^{-6}$), plus the links of each data center's own plan (seeds).
3. Solve the MILP on those links only.
4. Optionally, solve the full MILP warm-started from that plan.
5. Re-evaluate every plan with exact recourse.

The gap to the LP bound is reported, and was 13–21 % in our runs. **The plans are therefore not certified optimal.** A stronger formulation (cut-set inequalities, Benders cuts) is an open research question.

## 8. Checks

**Against version 1.** Restrict version 2 to one data center, one very large pipe size at 100,000 yen/m, a central COP of 4, no loss and kerosene at 115 yen/L. It then reproduces version 1 exactly: 15 sites, 16.1 km and 137.5 M yen/yr.

**Unit tests** (`tests/test_heatnet.py`) on a synthetic instance check:
- the per-data-center waste-heat limits;
- pipe capacity;
- that each user is served by one data center;
- the coupling between scenarios;
- that each robust objective does best on its own criterion;
- that C&CG matches the max-min over all corners;
- that the formulas match version 1.

## 9. The pair-by-pair baseline

The idea starter asks for five ranked partners per data center. Our baseline is the following.
1. **Score each user alone.** User $u$ gets its own pipe from data center $d$: the smallest size $k$ with $\bar Q_k \ge q_u$, along the road distance $\ell_{du}$. It also gets all of $d$'s waste heat. Its score is
   $$\text{score}_{du} = \sum_t v_u \min\!\big(\bar s_{ut},\, W_{dt}/r_u\big) - \mathrm{CRF}_p\, c_k\, \ell_{du} - \mathrm{CRF}_{hp}\, H_u .$$
2. **Pick the five best** users with a positive score.
3. **Build the five pipes** and evaluate them together with the same delivery LP.

The shared network beats this baseline because it avoids duplicated pipes, lets small users join through short branches, and uses larger, cheaper-per-MW trunks.

## 10. A worked pair: data center No. 1 and the fish farm (ambient loop)

| Item | Value | How |
|---|---|---|
| Road distance | 2,483 m | OpenStreetMap shortest path |
| Demand | 5,000 MWh/yr, flat | assumed site and demand |
| Design peak $P$ | 0.68 MW | $1.2 \times 5{,}000/8{,}760$ |
| Supply temperature | 22 °C, so direct use | below 27 °C |
| Pipe | DN150 (1.41 MW) | smallest size with $\bar Q_k \ge q_u$ (DN100 carries only 0.54 MW) |
| Pipe investment | 517 M yen | $2{,}483 \times 208{,}367$ |
| Heat-pump investment | 0 | direct use |
| Saving per year | 69.7 M yen (115 yen/L) to 95.1 M yen (156.8 yen/L); expected 82.4 M yen | $5{,}000 \times v$ |
| CO₂ avoided | 1,510 t/yr | $5{,}000 \times 0.302$ |
| Simple payback | 6.3 years | $517 / 82.4$ |

## 11. Limitations

- **Monthly energy balances.** The model has no hourly operation, no storage and no pumping energy. Peaks enter only through $P_u$, $\alpha$ and the duration curve.
- **Heat loss.** Losses are a flat share $\lambda$. A length-, size- and temperature-dependent loss, fixed per built pipe, is the next step.
- **Positions.** Two data-center positions are approximate and one is a placeholder. Several users are assumed sites.
- **Assumed parameters.** The peak factors, supply temperatures, velocities, the pipe-cost line and the heat-pump cost at the users are assumptions to be checked with experts and data.
