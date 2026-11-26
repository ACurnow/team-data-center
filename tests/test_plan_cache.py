"""The disk cache of solved Warm Ishikari plans (dcopt.heat.v1.cached_design), on a synthetic
instance: no map data and no solver needed."""
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
from synthetic import tiny

from dcopt.heat import v1
from dcopt.heat.v1 import Assumptions, Design, Site, cached_design, plan_key

ROOT = Path(__file__).resolve().parents[1]
DC = Site("dc", "DC", "DC", "dc", 141.3, 43.2, 0.0, "test", node=0)
SITES = [replace(s, node=i + 1) for i, s in enumerate(tiny().users)]
KINDS = {"greenhouse", "aquaculture", "school"}


def fake_design(calls):
    """Stands in for the MILP: records each call and returns a small, deterministic plan."""
    def run(dc, sites, A, k=4, kinds=None, links=None, time_limit=30.0):
        calls.append((A, k, frozenset(kinds or ()), time_limit))
        users = [s for s in sites if kinds is None or s.kind in kinds]
        served = np.array([[s.annual_mwh / 12] * 12 for s in users])
        d = Design(users, [(0, 1, 850.0)], {(0, 1): float(served.sum())}, served,
                   served.sum(axis=0) * (1 - 1 / A.cop), A.waste_heat_mwh(), A, "Optimal", 1.25)
        d.gap = 0.004
        return d
    return run


def test_plan_key_is_stable_and_tracks_every_input(monkeypatch):
    A = Assumptions()
    key = plan_key(DC, SITES, A, 3, KINDS, 60)
    assert key == plan_key(DC, list(SITES), Assumptions(), 3, {"school", "aquaculture", "greenhouse"}, 60.0)
    assert key != plan_key(DC, SITES, replace(A, kerosene_yen_l=120.0), 3, KINDS, 60)
    assert key != plan_key(DC, SITES, replace(A, carbon_yen_t=500.0), 3, KINDS, 60)
    assert key != plan_key(DC, SITES, A, 4, KINDS, 60)
    assert key != plan_key(DC, SITES, A, 3, KINDS | {"snow"}, 60)
    assert key != plan_key(DC, SITES, A, 3, None, 60)
    assert key != plan_key(DC, SITES, A, 3, KINDS, 30)
    assert key != plan_key(DC, SITES[:-1], A, 3, KINDS, 60)
    assert key != plan_key(DC, [replace(SITES[0], annual_mwh=1.0)] + SITES[1:], A, 3, KINDS, 60)
    monkeypatch.setattr(v1, "code_version", lambda: "another-version")
    assert key != plan_key(DC, SITES, A, 3, KINDS, 60)


def test_plan_key_is_the_same_in_a_fresh_interpreter():
    """No per-process hash randomization: a restarted app must find the plans it saved."""
    code = ("import sys; sys.path.insert(0, 'tests'); from test_plan_cache import DC, SITES, KINDS; "
            "from dcopt.heat.v1 import Assumptions, plan_key; "
            "print(plan_key(DC, SITES, Assumptions(), 3, KINDS, 60))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == plan_key(DC, SITES, Assumptions(), 3, KINDS, 60)


def test_cached_design_round_trips_through_disk(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(v1, "design", fake_design(calls))
    A = Assumptions()
    first, hit = cached_design(DC, SITES, A, k=3, kinds=KINDS, time_limit=60, cache_dir=tmp_path)
    assert not hit and len(calls) == 1
    assert len(list(tmp_path.glob("*.pkl"))) == 1 and not list(tmp_path.glob("*.tmp"))

    again, hit = cached_design(DC, SITES, A, k=3, kinds=KINDS, time_limit=60, cache_dir=tmp_path)
    assert hit and len(calls) == 1                                     # no second solve
    assert again.A == first.A and again.edges == first.edges and again.status == first.status
    assert [s.key for s in again.sites] == [s.key for s in first.sites]
    np.testing.assert_array_equal(again.served, first.served)
    assert again.annual_net == first.annual_net
    assert again.seconds == first.seconds and again.gap == first.gap

    _, hit = cached_design(DC, SITES, replace(A, power_yen_kwh=30.0), k=3, kinds=KINDS, time_limit=60,
                           cache_dir=tmp_path)
    assert not hit and len(calls) == 2                                 # new settings, new solve


def test_cached_design_uses_the_env_folder_and_survives_a_broken_file(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(v1, "design", fake_design(calls))
    monkeypatch.setenv(v1.PLAN_CACHE_ENV, str(tmp_path))
    A = Assumptions()
    (tmp_path / f"{plan_key(DC, SITES, A, 3, KINDS, 60)}.pkl").write_bytes(b"not a pickle")
    d, hit = cached_design(DC, SITES, A, k=3, kinds=KINDS, time_limit=60)
    assert not hit and len(calls) == 1 and d.gap == 0.004
    _, hit = cached_design(DC, SITES, A, k=3, kinds=KINDS, time_limit=60)
    assert hit and len(calls) == 1


def test_default_cache_folder_is_git_ignored(monkeypatch):
    monkeypatch.delenv(v1.PLAN_CACHE_ENV, raising=False)
    rel = v1.plan_cache_dir().relative_to(ROOT)
    assert rel.parts[:2] == ("data", "cache")
    out = subprocess.run(["git", "check-ignore", "-q", str(rel / "plan.pkl")], cwd=ROOT, check=False)
    assert out.returncode == 0
