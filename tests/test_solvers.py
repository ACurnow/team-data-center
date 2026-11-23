"""HiGHS and Gurobi find the same optimum on small instances (skipped without gurobipy or a licence)."""
from dataclasses import replace

import pytest

from dcopt.heat.network import Params, solve
from synthetic import SCENS, small_two_dc, tiny

gp = pytest.importorskip("gurobipy")


@pytest.fixture(scope="module", autouse=True)
def gurobi_licence():
    try:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        env.dispose()
    except Exception as exc:                                    # noqa: BLE001 - any licence problem skips
        pytest.skip(f"Gurobi licence not available: {exc}")


@pytest.mark.parametrize("make", [tiny, small_two_dc], ids=["tiny", "two_dc"])
@pytest.mark.parametrize("mode", ["ambient", "central"])
@pytest.mark.parametrize("objective", ["expected", "worst"])
def test_highs_and_gurobi_agree(make, mode, objective):
    inst = make()
    P = Params(mode=mode, mip_rel_gap=0.0, time_limit=60)
    highs = solve(inst, replace(P, solver="highs"), SCENS, objective=objective)
    gurobi = solve(inst, replace(P, solver="gurobi"), SCENS, objective=objective)
    value = (lambda p: p.expected_net) if objective == "expected" else (lambda p: float(p.net.min()))
    assert value(gurobi) == pytest.approx(value(highs), rel=1e-5, abs=1.0)
