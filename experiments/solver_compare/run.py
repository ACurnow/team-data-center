"""HiGHS and Gurobi on the full theme-1 MILP (all candidate links, no kernel search).

For each network-temperature mode this solves the expected-value model of model v2 from a cold start with
each solver and time limit. It prints the plan value, the solver's bound and the gap. It also prints the
plan from the default LP-guided kernel search (HiGHS), so its distance from the best bound can be read off.

Run: uv sync --extra gurobi && uv run python experiments/solver_compare/run.py [--limits 60,300]
Gurobi is optional and needs its own licence; HiGHS alone runs with --solvers highs.
"""
from __future__ import annotations

import argparse
from dataclasses import replace

from dcopt.common.geo import use_overpass_mirror
from dcopt.heat.network import Params, build_instance, default_scenarios, ishikari_sources, solve, solve_kernel
from dcopt.heat.v1 import ishikari_sites

M = 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limits", default="60,300", help="time limits in seconds, comma separated")
    ap.add_argument("--modes", default="ambient,central")
    ap.add_argument("--solvers", default="highs,gurobi")
    ap.add_argument("--dc-links", type=int, default=1,
                    help="direct candidate links from each user to its nearest data centers (4: to every data center)")
    args = ap.parse_args()
    use_overpass_mirror()
    sakura, sites = ishikari_sites()
    inst = build_instance(ishikari_sources(sakura), sites)
    scens = default_scenarios()
    print(f"instance: {inst.D} data centers, {inst.U} users, {len(scens)} scenarios, dc_links {args.dc_links}")
    best_bound: dict[str, float] = {}
    for mode in args.modes.split(","):
        P = Params(mode=mode, dc_links=args.dc_links)
        kern = solve_kernel(inst, P, scens)
        print(f"\n== {mode}: kernel search (HiGHS) value {kern.expected_net / M:.2f}M, "
              f"LP bound {kern.kernel['bound'] / M:.2f}M, {kern.seconds:.1f}s, {len(kern.connected)} sites")
        for solver in args.solvers.split(","):
            for tl in [float(x) for x in args.limits.split(",")]:
                Ps = replace(P, solver=solver, time_limit=tl, mip_rel_gap=1e-4)
                plan = solve(inst, Ps, scens)
                value, bound = plan.expected_net, plan.dual_bound
                best_bound[mode] = min(best_bound.get(mode, float("inf")), bound)
                print(f"   {solver:6s} limit {tl:5.0f}s: value {value / M:7.2f}M  bound {bound / M:7.2f}M  "
                      f"gap {(bound - value) / abs(bound):6.2%}  time {plan.seconds:6.1f}s  "
                      f"sites {len(plan.connected):2d}  status {plan.status}")
        b = best_bound[mode]
        print(f"   kernel plan vs best bound {b / M:.2f}M: within {(b - kern.expected_net) / abs(b):.2%}")


if __name__ == "__main__":
    main()
