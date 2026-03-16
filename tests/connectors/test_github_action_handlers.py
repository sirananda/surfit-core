from connectors.github.action_handlers import propose_action

def test_propose_action_requires_fields():
    out = propose_action({})
    assert out["ok"] is False
    assert "missing fields" in out["error"]
