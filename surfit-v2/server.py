"""
SURFIT V2.3 — Wave Engine + Execution Gate
Surfit now CONTROLS execution, not just evaluates.
- auto/log → actually posts message to Slack
- check/approve → holds for approval, does NOT post
- block → blocks, does NOT post
- dashboard approve → triggers real Slack post

Run: python server.py
Env: SLACK_SIGNING_SECRET, SLACK_BOT_TOKEN
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uvicorn, sys, os, uuid, hashlib, hmac, time, json
from urllib.parse import unquote_plus

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo, ContentMetadata

# ── Config ──
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

app = FastAPI(title="SurfitAI Wave Engine", version="2.3.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000","http://127.0.0.1:3001"],
    allow_methods=["*"], allow_headers=["*"])

engine = WaveEngine()
action_log: List[dict] = []
pending_actions: List[dict] = []


# ============================================================
# SLACK WEB API — Post messages to Slack
# ============================================================

def slack_post_message(channel_id: str, text: str, surfit_prefix: bool = True) -> dict:
    """Actually post a message to a Slack channel using the Bot Token."""
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "no_bot_token", "note": "Set SLACK_BOT_TOKEN to enable real posting"}

    import urllib.request
    post_text = f"[Surfit] {text}" if surfit_prefix else text
    payload = json.dumps({"channel": channel_id, "text": post_text}).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================
# SHARED MODELS
# ============================================================

class ResourceIn(BaseModel):
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    repo: Optional[str] = None
    database: Optional[str] = None
    destination_class: Optional[str] = None

class ContextIn(BaseModel):
    env: str = "prod"
    visibility: str = "internal"
    reversible: bool = True
    sensitive_data: bool = False
    financial_impact: bool = False
    deployment_stable: bool = True
    approval_required_override: bool = False


# ============================================================
# SIGNATURE VERIFICATION
# ============================================================

def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    if not SLACK_SIGNING_SECRET:
        return True
    if abs(time.time() - float(timestamp)) > 300:
        return False
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ============================================================
# NORMALIZATION LAYER
# ============================================================

def normalize_slack_event(payload: dict) -> EvaluateRequest:
    resource = payload.get("resource", {})
    context = payload.get("context", {})
    return EvaluateRequest(
        system="slack",
        action=payload.get("action", "post_message"),
        resource=ResourceInfo(
            resource_id=resource.get("channel_id"),
            resource_name=resource.get("channel_name") or resource.get("channel_id"),
            destination_class=resource.get("destination_class"),
        ),
        context=ContextInfo(
            env=context.get("env", "prod"),
            visibility=context.get("visibility", "internal"),
            reversible=context.get("reversible", True),
            sensitive_data=context.get("sensitive_data", False),
            financial_impact=context.get("financial_impact", False),
            approval_required_override=context.get("approval_required_override", False),
        ),
        content_metadata=ContentMetadata(
            message_type=payload.get("content_metadata", {}).get("message_type"),
        ) if payload.get("content_metadata") else None,
        agent_id=payload.get("agent_id"),
        tenant_id=payload.get("tenant_id"),
    )


def normalize_real_slack_command(form_data: dict) -> dict:
    channel_name = form_data.get("channel_name", "unknown")
    channel_id = form_data.get("channel_id", "")
    text = form_data.get("text", "")
    user_name = form_data.get("user_name", "unknown")

    action = "post_message"
    if text.lower().startswith("announce"):
        action = "post_announcement"

    visibility = "internal"
    announcement_channels = ["company-announcements", "all-hands", "general", "leadership-updates"]
    if channel_name in announcement_channels:
        visibility = "company_wide"

    return {
        "action": action,
        "resource": {"channel_id": channel_id, "channel_name": channel_name},
        "context": {"env": "prod", "visibility": visibility, "reversible": True},
        "content": {"text": text or f"Action from {user_name} in #{channel_name}"},
        "agent_id": f"slack-user-{form_data.get('user_id', 'unknown')}",
        "slack_metadata": {
            "user_id": form_data.get("user_id"),
            "user_name": user_name,
            "team_id": form_data.get("team_id"),
            "command": form_data.get("command"),
            "channel_id": channel_id,
            "channel_name": channel_name,
            "response_url": form_data.get("response_url"),
        },
    }


# ============================================================
# ACTION LOGGING
# ============================================================

def log_action(result, channel, content_text, source="slack_ingestion", slack_metadata=None, channel_id=None):
    action_id = f"slack-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": action_id,
        "source": source,
        "system": "slack",
        "action": "post_message",
        "timestamp": now,
        "wave_score": result.wave_score,
        "wave_label": result.wave_label,
        "handling": result.handling,
        "destination_class": result.destination_class_resolved,
        "reasons": result.reasons,
        "contributing_factors": [
            {"source": f.source, "key": f.key, "modifier": f.modifier, "description": f.description}
            for f in result.contributing_factors
        ],
        "status": "pending_approval" if result.handling in ("approve", "check") else "completed",
        "decided_by": None if result.handling in ("approve", "check") else "system",
        "content_preview": content_text[:80] if content_text else None,
        "channel_id": channel_id,
        "channel_name": channel,
        "content_text": content_text,
        "proof": {
            "channel": f"#{channel}",
            "evaluated_at": now,
            "wave": result.wave_label,
            "content_preview": content_text[:40] if content_text else None,
            "source": source,
        },
    }
    if slack_metadata:
        record["slack_metadata"] = slack_metadata
        record["proof"]["user"] = slack_metadata.get("user_name")

    action_log.insert(0, record)
    if len(action_log) > 100:
        action_log.pop()

    return record


# ============================================================
# SLACK SLASH COMMAND — WITH EXECUTION GATE
# ============================================================

@app.post("/api/v1/slack/command")
async def slack_command(request: Request):
    """
    V2.3 Execution Gate:
    - auto/log → actually post the message to Slack
    - check/approve → hold for approval, do NOT post
    - block → deny, do NOT post
    """
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")

    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    form_data = {}
    for pair in body.decode("utf-8").split("&"):
        if "=" in pair:
            key, val = pair.split("=", 1)
            form_data[key] = unquote_plus(val)

    normalized = normalize_real_slack_command(form_data)
    eval_req = normalize_slack_event(normalized)
    result = engine.evaluate(eval_req)

    channel_name = form_data.get("channel_name", "unknown")
    channel_id = form_data.get("channel_id", "")
    content_text = form_data.get("text", "")
    user_name = form_data.get("user_name", "unknown")

    record = log_action(result, channel_name, content_text,
                        source="real_slack", slack_metadata=normalized.get("slack_metadata"),
                        channel_id=channel_id)

    # ── EXECUTION GATE ──

    if result.handling in ("auto", "log"):
        # EXECUTE: Actually post the message to Slack
        post_result = slack_post_message(channel_id, content_text)
        executed = post_result.get("ok", False)
        record["status"] = "executed" if executed else "execution_failed"
        record["decided_by"] = "surfit_auto"
        record["proof"]["executed"] = executed
        record["proof"]["slack_ts"] = post_result.get("ts")

        emoji = "\u2705"
        decision_text = f"*Allowed and executed* ({result.wave_label})"
        if not executed:
            emoji = "\u26A0\uFE0F"
            decision_text = f"*Allowed but execution failed* ({post_result.get('error', 'unknown')})"
            if not SLACK_BOT_TOKEN:
                decision_text = f"*Allowed* ({result.wave_label}) \u2014 Set SLACK_BOT_TOKEN to enable auto-posting"

    elif result.handling in ("check", "approve"):
        # HOLD: Do NOT post. Add to pending queue.
        pending_record = {
            "id": record["id"],
            "channel_id": channel_id,
            "channel_name": channel_name,
            "content_text": content_text,
            "user_name": user_name,
            "wave_score": result.wave_score,
            "wave_label": result.wave_label,
            "handling": result.handling,
            "reasons": result.reasons,
            "contributing_factors": record["contributing_factors"],
            "timestamp": record["timestamp"],
            "status": "pending",
        }
        pending_actions.insert(0, pending_record)
        record["status"] = "pending_approval"

        emoji = "\u26A0\uFE0F" if result.handling == "approve" else "\U0001F50D"
        decision_text = f"*Held for approval* ({result.wave_label})\nMessage will NOT be posted until approved in the Surfit dashboard."

    else:
        # BLOCK
        record["status"] = "blocked"
        record["decided_by"] = "surfit_block"
        emoji = "\U0001F6D1"
        decision_text = f"*Blocked* ({result.wave_label})\nThis action has been denied by Surfit policy."

    slack_response = {
        "response_type": "ephemeral",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Surfit* \u2014 {decision_text}\n*Channel:* #{channel_name}\n*Message:* {content_text[:100]}"
                }
            },
        ]
    }

    return JSONResponse(slack_response)


# ============================================================
# PENDING ACTIONS + APPROVE ENDPOINT
# ============================================================

@app.get("/api/v1/pending")
def get_pending():
    """Return pending actions awaiting approval."""
    return {"pending": [p for p in pending_actions if p["status"] == "pending"]}


@app.post("/api/v1/pending/{action_id}/approve")
def approve_action(action_id: str):
    """
    Approve a pending action.
    This triggers the REAL Slack post.
    """
    target = None
    for p in pending_actions:
        if p["id"] == action_id and p["status"] == "pending":
            target = p
            break

    if not target:
        return JSONResponse({"error": "Action not found or already resolved"}, status_code=404)

    # Execute the held message
    post_result = slack_post_message(target["channel_id"], target["content_text"])
    executed = post_result.get("ok", False)

    target["status"] = "approved_executed" if executed else "approved_failed"
    now = datetime.now(timezone.utc).isoformat()

    # Update action log
    for a in action_log:
        if a["id"] == action_id:
            a["status"] = "approved"
            a["decided_by"] = "operator"
            a["proof"]["approved_at"] = now
            a["proof"]["executed"] = executed
            a["proof"]["slack_ts"] = post_result.get("ts")
            break

    return {
        "id": action_id,
        "status": target["status"],
        "executed": executed,
        "slack_result": {"ok": post_result.get("ok"), "ts": post_result.get("ts"), "error": post_result.get("error")},
        "approved_at": now,
    }


@app.post("/api/v1/pending/{action_id}/reject")
def reject_action(action_id: str):
    """Reject a pending action. Message is never posted."""
    for p in pending_actions:
        if p["id"] == action_id and p["status"] == "pending":
            p["status"] = "rejected"
            for a in action_log:
                if a["id"] == action_id:
                    a["status"] = "rejected"
                    a["decided_by"] = "operator"
                    break
            return {"id": action_id, "status": "rejected"}
    return JSONResponse({"error": "Action not found or already resolved"}, status_code=404)


# ============================================================
# SLACK EVENTS API (unchanged)
# ============================================================

@app.post("/api/v1/slack/events")
async def slack_events(request: Request):
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")

    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    data = json.loads(body)
    if data.get("type") == "url_verification":
        return JSONResponse({"challenge": data.get("challenge")})

    if data.get("type") == "event_callback":
        event = data.get("event", {})
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return JSONResponse({"ok": True})
        if event.get("type") == "message":
            normalized = {
                "action": "post_message",
                "resource": {"channel_id": event.get("channel", ""), "channel_name": event.get("channel", "")},
                "context": {"env": "prod", "visibility": "internal", "reversible": True},
                "content": {"text": event.get("text", "")},
                "agent_id": f"slack-user-{event.get('user', 'unknown')}",
            }
            eval_req = normalize_slack_event(normalized)
            result = engine.evaluate(eval_req)
            log_action(result, event.get("channel", "unknown"), event.get("text", ""), source="real_slack_event")

    return JSONResponse({"ok": True})


# ============================================================
# LOCAL SLACK INGESTION (dashboard simulate buttons)
# ============================================================

class SlackIngestPayload(BaseModel):
    event_type: str = "message_attempt"
    system: str = "slack"
    action: str = "post_message"
    resource: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    content_metadata: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None

@app.post("/api/v1/ingest/slack")
def ingest_slack(payload: SlackIngestPayload):
    eval_req = normalize_slack_event(payload.dict())
    result = engine.evaluate(eval_req)
    channel = (payload.resource or {}).get("channel_name", "unknown")
    content_text = (payload.content or {}).get("text")
    record = log_action(result, channel, content_text, source="simulated")
    record["action"] = payload.action
    record["resource"] = payload.resource or {}
    record["context"] = payload.context or {}
    return record


# ============================================================
# GENERIC EVALUATE ENDPOINT
# ============================================================

class EvalIn(BaseModel):
    system: str
    action: str
    resource: Optional[ResourceIn] = None
    context: Optional[ContextIn] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None

@app.post("/api/v1/governance/evaluate")
def evaluate(req: EvalIn):
    resource_name = None
    resource_id = None
    dest_class = None
    if req.resource:
        resource_name = req.resource.resource_name or req.resource.channel_name or req.resource.repo or req.resource.database
        resource_id = req.resource.resource_id or req.resource.channel_id
        dest_class = req.resource.destination_class

    eval_req = EvaluateRequest(
        system=req.system, action=req.action,
        resource=ResourceInfo(resource_id=resource_id, resource_name=resource_name, destination_class=dest_class) if req.resource else None,
        context=ContextInfo(
            env=req.context.env if req.context else "prod",
            visibility=req.context.visibility if req.context else "internal",
            reversible=req.context.reversible if req.context else True,
            sensitive_data=req.context.sensitive_data if req.context else False,
            financial_impact=req.context.financial_impact if req.context else False,
            deployment_stable=req.context.deployment_stable if req.context else True,
            approval_required_override=req.context.approval_required_override if req.context else False,
        ) if req.context else None,
        agent_id=req.agent_id, tenant_id=req.tenant_id,
    )
    result = engine.evaluate(eval_req)
    return result.to_dict()


# ============================================================
# ACTION LOG + PENDING + HEALTH
# ============================================================

@app.get("/api/v1/actions")
def get_actions():
    return {"actions": action_log}

@app.get("/api/v1/health")
def health():
    return {
        "status": "ok", "engine": "surfit-v2.3", "version": "2.3.0",
        "slack_configured": bool(SLACK_SIGNING_SECRET),
        "slack_bot_token": bool(SLACK_BOT_TOKEN),
        "execution_gate": True,
        "pending_actions": len([p for p in pending_actions if p["status"] == "pending"]),
        "endpoints": [
            "POST /api/v1/governance/evaluate",
            "POST /api/v1/ingest/slack",
            "POST /api/v1/slack/command",
            "POST /api/v1/slack/events",
            "GET  /api/v1/pending",
            "POST /api/v1/pending/{id}/approve",
            "POST /api/v1/pending/{id}/reject",
            "GET  /api/v1/actions",
        ],
        "ingested_actions": len(action_log),
    }

if __name__ == "__main__":
    slack_status = "configured" if SLACK_SIGNING_SECRET else "NOT configured (set SLACK_SIGNING_SECRET)"
    bot_status = "configured" if SLACK_BOT_TOKEN else "NOT configured (set SLACK_BOT_TOKEN for auto-posting)"
    print(f"\n  \U0001F30A SurfitAI Wave Engine v2.3 \u2014 Execution Gate")
    print(f"  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print(f"  API:       http://localhost:8000")
    print(f"  Docs:      http://localhost:8000/docs")
    print(f"  Slack:     {slack_status}")
    print(f"  Bot Token: {bot_status}")
    print(f"  Command:   POST /api/v1/slack/command")
    print(f"  Pending:   GET  /api/v1/pending")
    print(f"  Approve:   POST /api/v1/pending/{{id}}/approve")
    print(f"  Reject:    POST /api/v1/pending/{{id}}/reject\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
