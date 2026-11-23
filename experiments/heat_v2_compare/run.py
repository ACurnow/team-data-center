"""Warm Ishikari: model v1 against model v2 on the real Ishikari instance (printed, nothing written).

    uv run python experiments/heat_v2_compare/run.py                       # both temperature modes
    uv run python experiments/heat_v2_compare/run.py --modes central --skip-rank
    DCOPT_SOLVER=gurobi uv run python experiments/heat_v2_compare/run.py   # optional, needs gurobipy

Needs the Ishikari map data (data/cache/ishikari, from the fetch scripts); network access only when
the OpenStreetMap cache is missing. MILPs run through LP-guided kernel search (dcopt.heat.network.solve_kernel);
"gap" is the relative distance to the best bound found (LP relaxation, or the full MILP with --full).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from dcopt.common.geo import use_overpass_mirror
from dcopt.heat.v1 import Assumptions, design, ishikari_sites  # noqa: E402
from dcopt.heat.v1 import pairwise as pairwise_v1  # noqa: E402
from dcopt.heat.network import (MODES, OBJECTIVES, Params, PipeSize, Scenario, assumptions_table,  # noqa: E402
                            build_instance, candidate_edges, default_scenarios, ishikari_sources, pair_calculator,
                            pairwise, plan_for, rank_partners, robust_report, scenario_nets, solve_kernel,
                            solver_name, stochastic_report)

M = 1e6


def km(plan) -> str:
    return " ".join(f"DN{dn}:{v:.1f}" for dn, v in plan.km_by_dn().items()) or "-"


def gap(plan) -> str:
    if plan.kernel is not None:
        return f"gap {plan.kernel['gap']:.3f} (kernel {plan.kernel['links']}/{plan.kernel['of']} links)"
    return "" if plan.gap is None else f"gap {plan.gap:.3f}"


def line(tag: str, plan, own_opt=None) -> str:
    n = scenario_nets(plan, own_opt)
    reg = f" maxregret {n['max_regret'] / M:6.1f}M" if "max_regret" in n else ""
    return (f"{tag:30s} sites {len(plan.connected):2d} {plan.sites_per_dc()} km {plan.pipe_m / 1000:5.1f} [{km(plan)}]\n"
            f"{'':30s} E[net] {n['expected'] / M:6.1f}M worst {n['worst'] / M:6.1f}M{reg} per scenario "
            f"{[round(v / M, 1) for v in n['per']]} payback {plan.payback:4.1f}y time {plan.seconds:5.1f}s {gap(plan)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="ambient,central")
    ap.add_argument("--tl", type=float, default=60.0, help="time limit per MILP, seconds")
    ap.add_argument("--full", type=float, default=0.0, help="seconds for the warm-started full MILP (0: skip)")
    ap.add_argument("--skip-rank", action="store_true")
    ap.add_argument("--skip-per-dc", action="store_true")
    ap.add_argument("--skip-robust", action="store_true")
    args = ap.parse_args()

    use_overpass_mirror()                                   # the OpenStreetMap cache in data/raw
    t0 = time.perf_counter()
    sakura, sites = ishikari_sites()
    inst = build_instance(ishikari_sources(sakura), sites)
    print(f"solver {solver_name(Params())}; instance: {inst.D} data centers, {inst.U} candidate users "
          f"({time.perf_counter() - t0:.1f}s)")
    for d, src in enumerate(inst.sources):
        print(f"  [{d}] {src.key:6s} {src.name_en:45s} IT {src.it_mw} {src.status}; {src.where[1]}")

    print("\n== v1 (one data center, flat 100,000 yen/m, central heat pump COP 4, base assumptions)")
    A = Assumptions()
    d1 = design(sakura, sites, A, k=3)
    p1 = pairwise_v1(sakura, sites, A)
    print(f"v1 optimized   sites {len(d1.connected):2d} km {d1.pipe_m / 1000:5.1f} net {d1.annual_net / M:6.1f}M "
          f"payback {d1.payback_years:4.1f}y time {d1.seconds:4.1f}s")
    print(f"v1 top-5 pairs sites {len(p1.connected):2d} km {p1.pipe_m / 1000:5.1f} net {p1.annual_net / M:6.1f}M "
          f"payback {p1.payback_years:4.1f}y")

    print("\n== v2 restricted to v1 (Sakura only, one size at 100,000 yen/m, central, COP 4, no loss, 115 yen/L)")
    sak = inst.subset([1], list(range(inst.U)))
    Pv1 = Params(mode="central", cop_override=4.0, loss_override=0.0, dc_links=1, time_limit=args.tl,
                 sizes=(PipeSize(999, 10.0, 3.0, 100_000.0),))
    v1sc = [Scenario("v1", "v1", "v1", 1.0, 115.0, None, (("sakura", 10.0),))]
    print(line("v2 as v1 (direct MILP)", plan_for(sak, Pv1, v1sc, method="direct")))

    scens = default_scenarios()
    print("\nscenarios: " + "; ".join(f"{s.key} ({s.en}) p={s.prob:g}" for s in scens))
    for mode in args.modes.split(","):
        P = Params(mode=mode, time_limit=args.tl)
        print(f"\n== v2 mode {mode}: {MODES[mode][1]}")
        print(f"candidate links {len(candidate_edges(inst, P))}, sizes " + ", ".join(
            f"DN{s.dn} {s.capacity_mw(P.dT):.2f}MW {s.yen_m / 1000:.0f}k/m" for s in P.sizes))
        # each data center on its own first: its plan, the 5 best pairs, and links that seed the regional kernel
        print("  per data center on its own: optimized network vs the 5 best pairs (expected net)")
        alone, extra = {}, set()
        for d, src in enumerate(inst.sources):
            one = inst.subset([d], list(range(inst.U)))
            o = solve_kernel(one, P, scens)
            alone[d] = o
            extra |= set(one.lift([(a, b) for a, b, _, _ in o.built]))
            if args.skip_per_dc:
                continue
            pw = pairwise(inst, P, scens, d)
            print(f"   {src.key:6s} optimized sites {len(o.connected):2d} km {o.pipe_m / 1000:5.1f} "
                  f"E[net] {o.expected_net / M:6.1f}M ({o.seconds:4.1f}s, {gap(o)}) | top-5 pairs sites "
                  f"{len(pw.connected):2d} km {pw.pipe_m / 1000:5.1f} E[net] {pw.expected_net / M:6.1f}M")
        extra = sorted(extra)
        if args.skip_robust:
            rp = solve_kernel(inst, P, scens, full_time=args.full, extra_edges=extra)
            print(line(OBJECTIVES["expected"][1], rp))
        else:
            rep = robust_report(inst, P, scens, extra_edges=extra)
            rp, opt = rep["plans"]["expected"], rep["own_opt"]
            for key in ("expected", "worst", "regret"):
                tag = OBJECTIVES[key][1] + ("" if rep["found_by"][key] == key else f" [best build: {rep['found_by'][key]} solve]")
                print(line(tag, rep["plans"][key], opt))
            for sc, o, best in zip(scens, rep["own"], opt):
                print(f"  own optimum {sc.key:10s} {o.expected_net / M:6.1f}M (best known {best / M:6.1f}M) "
                      f"sites {len(o.connected):2d} time {o.seconds:5.1f}s")
            st = stochastic_report(inst, P, scens, rp=rp, own=rep["own"], extra_edges=extra)
            print(f"  VSS = RP - EEV = {st['vss'] / M:.1f}M; EVPI = WS - RP = {st['evpi'] / M:.1f}M "
                  f"(RP {rp.expected_net / M:.1f}M, EEV {st['eev'].expected_net / M:.1f}M, WS {st['ws'] / M:.1f}M)")
        if not args.skip_rank:
            print("  matchmaker in the regional plan: loss of expected net without the partner (pipes kept)")
            for d, src in enumerate(inst.sources):
                rows = rank_partners(rp, d, top=5, full_top=1 if d == 0 else 0)
                print(f"   {src.key}:")
                for r in rows:
                    loss = "" if r["loss"] is None else f"loss {r['loss'] / M:6.1f}M"
                    full = f" (re-solved {r['loss_full'] / M:6.1f}M)" if "loss_full" in r else ""
                    pair = r["pair"]
                    ps = "" if pair is None else (f" pair score {pair['score'] / M:6.1f}M DN{pair['size']} "
                                                  f"{pair['dist_m'] / 1000:.1f}km")
                    print(f"     {'plan' if r['in_plan'] else 'pair'} {r['site'].name_en[:44]:44s} "
                          f"{r['heat_mwh']:7.0f}MWh {loss}{full}{ps}")
            print("  matchmaker per data center on its own (its standalone plan)")
            for d, src in enumerate(inst.sources):
                rows = rank_partners(alone[d], 0, top=5)
                print(f"   {src.key}: " + "; ".join(
                    f"{r['site'].name_en[:28]} {'' if r['loss'] is None else round(r['loss'] / M, 1)}" for r in rows))
        if mode == args.modes.split(",")[0]:
            best = rank_partners(rp, 0, top=1, by="pair")
            if best:
                print(f"  calculator: {inst.sources[0].name_en} x {best[0]['site'].name_en}")
                for r in pair_calculator(inst, P, scens, 0, best[0]["u"]):
                    print(f"     {r['en'][:44]:44s} {str(r['value'])[:30]:>30s} {r['unit']:6s} [{r['tag']}]")
        hp = Params(mode=mode, time_limit=args.tl, hp_yen_per_mw_user=150e6, hp_yen_per_mw_central=100e6)
        print(line("with heat-pump investment", solve_kernel(inst, hp, scens)))

    print("\n== assumptions (ambient defaults)")
    for r in assumptions_table(Params()):
        print(f"  {r['en'][:40]:40s} {str(r['value'])[:60]:60s} {r['unit']:8s} {r['basis'][:110]}")
    print(f"\ntotal {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
