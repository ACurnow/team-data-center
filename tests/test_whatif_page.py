"""The live what-if box on the Warm Ishikari page, with a stand-in for the chat endpoint.

A question goes in, the stand-in answers the two calls (which inputs to change, then the
explanation), and the page must show either the explanation or, when the explanation carries a
number the model did not compute, the numbers alone.
"""
import json
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from dcopt.common import llm
from dcopt.common.geo import missing_map_data
from dcopt.heat import v1

ROOT = Path(__file__).resolve().parents[1]
PAGE = str(ROOT / "app/pages/1_Warm_Ishikari.py")
pytestmark = pytest.mark.skipif(bool(missing_map_data()), reason="run the Ishikari data fetch first")


@pytest.fixture(autouse=True)
def own_plan_cache(monkeypatch, tmp_path):
    monkeypatch.setenv(v1.PLAN_CACHE_ENV, str(tmp_path / "plans"))
    for name in ("ORCAROUTER_API_KEY", "LLM_MODELS", "LLM_MODEL", "CARBONFORGE_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CF_API_KEY", "a-key-for-the-stand-in")
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def stand_in(explanation: str, calls: list):
    def send(url, payload, headers):
        body = json.loads(payload)
        calls.append(body)
        if "response_format" in body:                       # the first call: which inputs to change
            content = json.dumps({"changes": {"power_yen_kwh": 40, "assumed_sites": False},
                                  "new_data_center": None, "clarify": ""})
        else:                                               # the second call: the explanation
            content = explanation
        return 200, json.dumps({"choices": [{"message": {"content": content}}]}).encode(), {}
    return send


@pytest.mark.parametrize("explanation, shown_as_written", [
    ("電気料金が上がり、仮定の候補地もなくなったので、つながる需要家がなくなりました。", True),
    ("純便益は年987654百万円になります。", False),             # a number the model never computed
])
def test_a_question_changes_the_inputs_and_is_explained(monkeypatch, explanation, shown_as_written):
    calls: list = []
    monkeypatch.setattr(llm, "_http", stand_in(explanation, calls))
    at = AppTest.from_file(PAGE, default_timeout=600).run()
    assert not at.exception
    at.chat_input[0].set_value("電気料金を40円にして、仮定の候補地も除いて").run()
    assert not at.exception
    assert len(calls) == 2 and "response_format" in calls[0] and "response_format" not in calls[1]
    assert at.session_state["power_price"] == 40 and at.session_state["assumed_sites"] is False
    said = [m.value for message in at.chat_message for m in message.markdown]
    notes = [c.value for c in at.caption]
    assert any("回答したモデル：carbonforge-flash（直接接続）" in n for n in notes)
    if shown_as_written:
        assert explanation in said
    else:
        assert explanation not in said and any("数値だけを表示しています" in n for n in notes)
