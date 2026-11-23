"""Model v2 (dcopt.heat.network) on a tiny synthetic instance: no map data needed."""
import math

import numpy as np
import pytest

from dcopt.heat.v1 import Assumptions, Site
from dcopt.heat.network import (BudgetSet, Instance, ccg, Params, Scenario, Source, duration_energy, evaluate,
                            pair_calculator, pairwise, rank_partners, robust_report, solve, solve_kernel,
                            stochastic_report)


def tiny(road_factor: float = 1.3) -> Instance:
    """Two data centers 2 km apart and five users around them (metres on a plane)."""
    pts_src = [(0, 0), (2000, 0)]
    users = [("gh", "greenhouse", (600, 500), 2500.0), ("fish", "aquaculture", (1200, -700), 1800.0),
             ("school", "school", (-800, 300), 300.0), ("snow", "snow", (2500, 600), 400.0),
             ("hosp", "hospital", (3000, -400), 1500.0)]
    sources = [Source("a", "DC A", "DC A", 0, 0, {"low": 0.3, "high": 0.6}, "operating", ("", ""), "test"),
               Source("b", "DC B", "DC B", 0, 0, {"low": 0.1, "high": 0.4}, "operating", ("", ""), "test")]
    sites = [Site(k, k, k, kind, 0.0, 0.0, mwh, "test") for k, kind, _, mwh in users]
    pts = pts_src + [p for _, _, p, _ in users]
    n = len(pts)
    dist = np.array([[road_factor * math.dist(pts[i], pts[j]) for j in range(n)] for i in range(n)])
    return Instance(sources, sites, dist, road=False)


SCENS = [Scenario("lo", "低", "low", 0.5, 115.0, "low"), Scenario("hi", "高", "high", 0.5, 156.8, "high")]
P0 = Params(mip_rel_gap=0.0, time_limit=60, k=3, dc_links=2)


def built_ok(plan, tol=1e-6):
    inst, P = plan.inst, plan.P
    nE = len(plan.E)
    yk = plan.y.max(axis=1)
    # heat only on built links, and each built link carries its users' peak within its size
    assert np.all(plan.g[:, :nE] + plan.g[:, nE:] <= yk[None, :] + tol)
    for e in range(nE):
        if yk[e] > 0.5:
            k = int(np.argmax(plan.y[e]))
            load = float(plan.ud.q @ (plan.g[:, e] + plan.g[:, e + nE]))
            assert load <= P.sizes[k].capacity_mw(P.dT) + tol
    # waste heat per data center, month and scenario
    assert np.all(plan.waste_used() <= plan.W + 1e-6)
    # exactly one data center per connected user, none for the others
    for u in range(inst.U):
        from_dc = plan.s[u].sum(axis=(1, 2))
        if plan.x[u] > 0.5:
            assert plan.assign[u] >= 0
            others = [d for d in range(inst.D) if d != plan.assign[u]]
            assert from_dc[others].sum() <= 1e-6
        else:
            assert from_dc.sum() <= 1e-6


@pytest.mark.parametrize("mode", ["ambient", "central"])
def test_caps_capacity_and_single_source(mode):
    plan = solve(tiny(), Params(mode=mode, mip_rel_gap=0.0), SCENS)
    assert plan.connected, "something should connect on this instance"
    built_ok(plan)
    # the build is shared, only deliveries differ: more waste heat (scenario hi) never delivers less
    assert plan.delivered[1] >= plan.delivered[0] - 1e-6


def test_pipe_capacity_limits_connections():
    inst = tiny()
    only_small = Params(mip_rel_gap=0.0, sizes=Params().sizes[:1])          # DN50 only
    plan = solve(inst, only_small, SCENS)
    cap = only_small.sizes[0].capacity_mw(only_small.dT)
    assert all(plan.ud.q[u] <= cap + 1e-9 for u in plan.connected)
    full = solve(inst, P0, SCENS)
    assert full.expected_net >= plan.expected_net - 1e-6


def test_scenario_coupling_order():
    rep = stochastic_report(tiny(), P0, SCENS, method="direct")
    # wait-and-see >= recourse plan >= plan built for the mean scenario
    assert rep["ws"] >= rep["rp"].expected_net - 1e-3
    assert rep["rp"].expected_net >= rep["eev"].expected_net - 1e-3
    assert rep["vss"] >= -1e-3 and rep["evpi"] >= -1e-3


def test_robust_objectives_do_their_job():
    rep = robust_report(tiny(), P0, SCENS, method="direct")
    nets = rep["nets"]
    tol = 1e-3 * max(1.0, abs(nets["expected"]["expected"]))
    assert nets["worst"]["worst"] >= nets["expected"]["worst"] - tol
    assert nets["regret"]["max_regret"] <= nets["expected"]["max_regret"] + tol
    assert nets["expected"]["expected"] >= max(nets["worst"]["expected"], nets["regret"]["expected"]) - tol
    for key in ("expected", "worst", "regret"):
        built_ok(rep["plans"][key])
    # the epigraph variable matches what the solved plan achieves
    sw, sr = rep["solved"]["worst"], rep["solved"]["regret"]
    assert abs(sw.bound - float(sw.net.min())) <= tol
    assert abs(sr.bound - float(max(np.asarray(sr.own_opt) - sr.net))) <= tol


def test_temperature_modes():
    amb, cen = Params(mode="ambient"), Params(mode="central")
    for kind in ("aquaculture", "snow"):
        k = amb.per_kind(kind)
        assert k["cop"] is None and k["elec"] == 0.0 and abs(k["r"] - (1 + amb.loss)) < 1e-12
    assert abs(amb.cop("greenhouse") - 0.5 * 318.15 / 20) < 1e-9
    assert abs(cen.cop("greenhouse") - 0.5 * 333.15 / 35) < 1e-9
    assert cen.cop("aquaculture") == cen.cop("onsen")


def test_matches_v1_numbers_when_restricted():
    P = Params(mode="central", cop_override=4.0, loss_override=0.0)
    A = Assumptions()
    k = P.per_kind("greenhouse")
    assert abs(k["r"] - 0.75) < 1e-12
    v = P.fuel_yen_per_mwh(115.0) - P.power_yen_kwh * 1000 * k["elec"]
    assert abs(v - A.value_yen_per_mwh) < 1e-6
    assert abs(P.crf - A.crf) < 1e-12


def test_duration_energy():
    m, h = 2.0, 744
    assert abs(duration_energy(m, h, 2.5, 2.5 * m) - m * h) < 1e-9
    half = duration_energy(m, h, 2.5, 1.25 * m)
    assert 0.8 * m * h < half < m * h
    assert duration_energy(m, h, 1.0, 1.0 * m) == m * h


def test_pairwise_rank_and_calculator():
    inst = tiny()
    pw = pairwise(inst, P0, SCENS, d=0, top=3)
    assert pw.inst.D == 1 and pw.inst.U <= 3
    assert all(a == 0 for a, _, _, _ in pw.built)
    plan = solve(inst, P0, SCENS)
    rows = rank_partners(plan, 0, top=5, full_top=1, method="direct")
    assert len(rows) <= 5
    for r in rows:
        if r["in_plan"]:
            assert r["loss"] >= -1e-3
    pairs = rank_partners(plan, 0, top=5, by="pair")
    assert all(not r["in_plan"] for r in pairs)
    calc = pair_calculator(inst, P0, SCENS, 0, 0)
    assert calc and all(r["tag"] in ("source", "assumption", "calculated") for r in calc)
    assert {r["key"] for r in calc} >= {"dist", "size", "capex", "saving", "co2", "payback"}


def test_evaluate_keeps_the_build():
    plan = solve(tiny(), P0, SCENS)
    again = evaluate(plan)
    assert np.array_equal(again.y, plan.y) and np.array_equal(again.x, plan.x)
    assert abs(again.expected_net - plan.expected_net) <= 1e-3 * max(1.0, abs(plan.expected_net))


def test_budget_vertices():
    inst = tiny()
    vs = BudgetSet(budget=1).vertices(inst.sources)
    assert len(vs) == inst.D
    for v in vs:
        lows = [s.key for s in inst.sources if v.it_load(s) == s.it_mw["low"]]
        assert len(lows) == 1


def test_formulations_agree():
    inst = tiny()
    for mode in ("ambient", "central"):
        a = solve(inst, Params(mode=mode, mip_rel_gap=0.0, formulation="aggregated"), SCENS)
        e = solve(inst, Params(mode=mode, mip_rel_gap=0.0, formulation="extended"), SCENS)
        assert abs(a.expected_net - e.expected_net) <= 1e-3 * max(1.0, abs(a.expected_net))
        built_ok(e)


@pytest.mark.parametrize("objective", ["expected", "worst"])
def test_kernel_search_is_feasible_and_bounded(objective):
    inst = tiny()
    direct = solve(inst, P0, SCENS, objective=objective)
    for full in (0.0, 30.0):
        k = solve_kernel(inst, P0, SCENS, objective=objective, full_time=full)
        built_ok(k)
        score = k.expected_net if objective == "expected" else float(k.net.min())
        best = direct.expected_net if objective == "expected" else float(direct.net.min())
        assert score <= best + 1e-3 * max(1.0, abs(best))           # a heuristic plan, never above the optimum
        assert k.kernel["bound"] >= score - 1e-3 * max(1.0, abs(score))
    assert score >= best - 1e-3 * max(1.0, abs(best))               # with the warm-started full solve: optimal here


def test_ccg_matches_max_min_over_all_corners():
    inst = tiny()
    uset = BudgetSet(budget=1)
    out = ccg(inst, P0, uset, method="direct")
    corners = [Scenario(v.key, v.ja, v.en, 1.0 / inst.D, v.kerosene_yen_l, None, v.it_mw)
               for v in uset.vertices(inst.sources)]
    direct = solve(inst, P0, corners, objective="worst")
    best = float(direct.net.min())
    assert abs(out["value"] - best) <= 1e-3 * max(1.0, abs(best))
    assert out["history"][-1]["worst"] in [c.key for c in out["corners"]]


def test_pairwise_with_no_profitable_pair_builds_nothing():
    from dcopt.heat.network import pairwise
    # central mode: every user needs the central heat pump, which is priced so that no pair pays back
    P = Params(mode="central", mip_rel_gap=0.0, hp_yen_per_mw_central=1e12)
    plan = pairwise(tiny(), P, SCENS, 0)
    assert not plan.connected and plan.pipe_m == 0
