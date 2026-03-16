from typing import Any, Dict
from .auth import load_auth
from .github_client import GitHubClient

def _client() -> GitHubClient:
    auth = load_auth()
    return GitHubClient(token=auth.token)

def propose_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["owner", "repo", "pull_number", "action"]
    missing = [k for k in required if k not in payload]
    if missing:
        return {"ok": False, "error": f"missing fields: {', '.join(missing)}"}

    if payload["action"] != "merge_pull_request":
        return {"ok": False, "error": "unsupported action"}

    client = _client()
    pr = client.get_pull(payload["owner"], payload["repo"], int(payload["pull_number"]))
    return {
        "ok": True,
        "action": "merge_pull_request",
        "owner": payload["owner"],
        "repo": payload["repo"],
        "pull_number": int(payload["pull_number"]),
        "pull_state": pr.get("state"),
        "mergeable": pr.get("mergeable"),
        "head_sha": (pr.get("head") or {}).get("sha"),
        "base_ref": (pr.get("base") or {}).get("ref"),
    }

def execute_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("action") != "merge_pull_request":
        return {"ok": False, "error": "unsupported action"}

    client = _client()
    result = client.merge_pull(
        payload["owner"],
        payload["repo"],
        int(payload["pull_number"]),
        payload.get("commit_title"),
    )
    return {"ok": True, "result": result}

def fetch_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = _client()
    pr = client.get_pull(payload["owner"], payload["repo"], int(payload["pull_number"]))
    return {"ok": True, "pull": pr}
