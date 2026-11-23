"""Robust heat network (theme 1): column-and-constraint generation over the budget Gamma.

Gamma is how many data centers may run at the low end of their IT-load range at the same time.
For Gamma = 0, 1, 2, 4 this prints the robust plan and its iterations, then compares the plans
(and the two-stage stochastic plan) by nominal value, price of robustness and worst case.

Run: uv run python experiments/heat_ccg/run.py [central|ambient]
"""
import sys
import time

from dcopt.common.geo import use_overpass_mirror
from dcopt.heat.network import (BudgetSet, Params, build_instance, ccg, default_scenarios, evaluate,
                                ishikari_sources, solve_kernel, worst_case)
from dcopt.heat.v1 import ishikari_sites

use_overpass_mirror()
mode = sys.argv[1] if len(sys.argv) > 1 else "central"
sakura, sites = ishikari_sites()
inst = build_instance(ishikari_sources(sakura), sites)
P = Params(mode=mode, time_limit=60)
M = 1e6
extra = set()
for d in range(inst.D):                                       # seed links: each data center's own plan
    one = inst.subset([d], list(range(inst.U)))
    o = solve_kernel(one, P, [BudgetSet(0).nominal(inst.sources)])
    extra |= set(one.lift([(a, b) for a, b, _, _ in o.built]))
extra = sorted(extra)
sp_plan = solve_kernel(inst, P, default_scenarios(), extra_edges=extra)   # the stochastic plan (IT x price)
nominal = BudgetSet(0).nominal(inst.sources)
plans, seed = {}, []
for G in (0, 1, 2, 4):
    t = time.perf_counter()
    out = ccg(inst, P, BudgetSet(budget=G), seed=seed, extra_edges=extra)
    seed = out["corners"][1:]
    plans[G] = out["plan"]
    pl = out["plan"]
    print(f"{mode} G={G}: robust value {out['value']/M:6.1f}M UB {out['upper']/M:6.1f}M sites {len(pl.connected)} {pl.sites_per_dc()} "
          f"km {pl.pipe_m/1000:.1f} iterations {len(out['history'])} time {time.perf_counter()-t:5.1f}s", flush=True)
    for h in out["history"]:
        print(f"    it {h['iter']}: corners {h['corners']} master {h['master']/M:6.1f}M UB {h['upper']/M:6.1f}M "
              f"LB {h['lower']/M:6.1f}M worst {h['worst']} (master {h['master_s']:.1f}s, sub {h['sub_s']:.1f}s)", flush=True)
x0 = plans[0]
nom0 = evaluate(x0, [nominal]).expected_net
print(f"\n{mode}: nominal net of x0 {nom0/M:.1f}M; columns: nominal net, PoR, worst case W(x;G) for G=1,2,4")
for name, pl in [("x0 (G=0)", x0), ("x_SP (stochastic)", sp_plan)] + [(f"x_G{G}", plans[G]) for G in (1, 2, 4)]:
    nom = evaluate(pl, [nominal]).expected_net
    ws = [worst_case(pl, BudgetSet(G)) for G in (1, 2, 4)]
    print(f"  {name:18s} nominal {nom/M:6.1f}M PoR {(nom0 - nom)/abs(nom0):6.3f} " +
          " ".join(f"W(G={G}) {v/M:6.1f}M [{k}]" for G, (v, k) in zip((1, 2, 4), ws)) +
          f" sites {len(pl.connected)} km {pl.pipe_m/1000:.1f}", flush=True)
