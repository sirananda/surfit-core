import json
import urllib.error
import urllib.request
from typing import Any

API_BASE_DEFAULT = "http://127.0.0.1:8010"

AGENT_NAME = "production_config_agent"
WAVE_TEMPLATE_ID = "production_config_change_v1"
POLICY_VERSION = "prod_config_policy_v1"
TARGET_PATH = "demo_artifacts/prod_config.json"


def _post_json(url: str, payload: dict[str, Any], timeout: int = 45) -> tuple[int | None, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            body = {"error": {"code": "HTTP_ERROR", "message": f"HTTP {e.code}"}}
        return e.code, body
    except Exception as e:
        return None, {"error": {"code": "REQUEST_FAILED", "message": str(e)}}


def _start_wave(api_base: str) -> dict[str, Any]:
    payload = {
        "agent_id": AGENT_NAME,
        "wave_template_id": WAVE_TEMPLATE_ID,
        "policy_version": POLICY_VERSION,
        "intent": "Demo trigger: production config mutation governance proof",
        "context_refs": {"target_path": TARGET_PATH},
    }
    code, body = _post_json(f"{api_base}/api/waves/run", payload)
    return {
        "http_code": code,
        "ok": code == 200 and str(body.get("status", "")).lower() != "failed",
        "wave_id": body.get("wave_id"),
        "wave_token": body.get("wave_token"),
        "status": body.get("status"),
        "error": body.get("error"),
        "body": body,
    }


def run_scenario(scenario: str, api_base: str = API_BASE_DEFAULT) -> dict[str, Any]:
    scenario = scenario.strip().lower()
    if scenario == "unauthorized agent":
        mutate_payload = {
            "wave_id": None,
            "wave_token": None,
            "agent_name": AGENT_NAME,
            "policy_version": POLICY_VERSION,
            "target_path": TARGET_PATH,
            "mutations": [
                {"json_path": "feature_flags.checkout_v2", "value": True},
                {"json_path": "rate_limits.requests_per_minute", "value": 0},
            ],
            "reason": "Unauthorized agent",
        }
        code, body = _post_json(f"{api_base}/ocean/mutate_config", mutate_payload)
        return {"wave": None, "mutate": {"http_code": code, "body": body}}

    wave = _start_wave(api_base)
    if not wave.get("ok"):
        return {"wave": wave, "mutate": None}

    wave_id = wave.get("wave_id")
    wave_token = wave.get("wave_token")

    target_path = TARGET_PATH
    policy_version = POLICY_VERSION
    if scenario == "path violation":
        target_path = "demo_artifacts/other.json"
    elif scenario == "policy mismatch":
        policy_version = "wrong_version"

    mutate_payload = {
        "wave_id": wave_id,
        "wave_token": wave_token,
        "agent_name": AGENT_NAME,
        "policy_version": policy_version,
        "target_path": target_path,
        "mutations": [
            {"json_path": "feature_flags.checkout_v2", "value": True},
            {"json_path": "rate_limits.requests_per_minute", "value": 0},
        ],
        "reason": scenario,
    }
    code, body = _post_json(f"{api_base}/ocean/mutate_config", mutate_payload)
    return {
        "wave": wave,
        "mutate": {
            "http_code": code,
            "body": body,
        },
    }
