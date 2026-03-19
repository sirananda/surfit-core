"""
SURFIT V2.2 — Wave Engine API + Real Slack Integration
Run: python server.py
Env vars: SLACK_SIGNING_SECRET, SLACK_BOT_TOKEN (optional)
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uvicorn, sys, os, uuid, hashlib, hmac, time, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo, ContentMetadata

# ── Config ──
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

app = FastAPI(title="SurfitAI Wave Engine", version="2.2.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000","http://127.0.0.1:3001"],
    allow_methods=["*"], allow_headers=["*"])

engine = WaveEngine()
action_log: List[dict] = []

# ── Shared Models ──
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
# SLACK SIGNATURE VERIFICATION
# ============================================================

def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Verify that the request actually came from Slack."""
    if not SLACK_SIGNING_SECRET:
        return True  # Skip verification if no secret configured (dev mode)
    if abs(time.time() - float(timestamp)) > 300:
        return False  # Request too old
    base = f"v0:{timestamp}:{body.decode('utf-8')}"
    expected = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ============================================================
# NORMALIZATION LAYER
# Now handles BOTH local mock payloads AND real Slack events.
# ============================================================

def normalize_slack_event(payload: dict) -> EvaluateRequest:
    """
    Normalize a Slack-style event into a Surfit EvaluateRequest.
    Handles local mock format (resource/context dicts) as before.
    """
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
    """
    Convert a real Slack slash command payload into our internal format.
    Slack sends: channel_id, channel_name, text, user_id, user_name, command, etc.
    We convert to the same shape normalize_slack_event() expects.
    """
    channel_name = form_data.get("channel_name", "unknown")
    channel_id = form_data.get("channel_id", "")
    text = form_data.get("text", "")
    user_name = form_data.get("user_name", "unknown")

    # Determine action from command text or default
    action = "post_message"
    if text.lower().startswith("announce"):
        action = "post_announcement"

    # Determine visibility from channel characteristics
    visibility = "internal"
    announcement_channels = ["company-announcements", "all-hands", "general", "leadership-updates"]
    if channel_name in announcement_channels:
        visibility = "company_wide"

    return {
        "action": action,
        "resource": {
            "channel_id": channel_id,
            "channel_name": channel_name,
        },
        "context": {
            "env": "prod",
            "visibility": visibility,
            "reversible": True,
        },
        "content": {
            "text": text or f"Action from {user_name} in #{channel_name}",
        },
        "agent_id": f"slack-user-{form_data.get('user_id', 'unknown')}",
        "slack_metadata": {
            "user_id": form_data.get("user_id"),
            "user_name": user_name,
            "team_id": form_data.get("team_id"),
            "command": form_data.get("command"),
            "response_url": form_data.get("response_url"),
        },
    }


def normalize_real_slack_event(event_data: dict) -> dict:
    """
    Convert a real Slack Events API message event into our internal format.
    Slack sends: type, channel, text, user, ts, etc.
    """
    return {
        "action": "post_message",
        "resource": {
            "channel_id": event_data.get("channel", ""),
            "channel_name": event_data.get("channel", ""),  # Will be resolved by classifier
        },
        "context": {
            "env": "prod",
            "visibility": "internal",
            "reversible": True,
        },
        "content": {
            "text": event_data.get("text", ""),
        },
        "agent_id": f"slack-user-{event_data.get('user', 'unknown')}",
    }


def log_action(result, channel, content_text, source="slack_ingestion", slack_metadata=None):
    """Create and log an action record."""
    action_id = f"slack-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "id": action_id,
        "source": source,
        "system": "slack",
        "action": result.reasons[0].split("=")[0].replace("System baseline: ", "") if result.reasons else "post_message",
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
        "status": "pending_approval" if result.handling == "approve" else "completed",
        "decided_by": None if result.handling == "approve" else "system",
        "content_preview": content_text[:80] if content_text else None,
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
# REAL SLACK SLASH COMMAND ENDPOINT
# ============================================================

@app.post("/api/v1/slack/command")
async def slack_command(request: Request):
    """
    Receives real Slack slash commands.
    Usage in Slack: /surfit [message or action description]
    """
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")

    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    # Parse form-encoded body from Slack
    form_data = {}
    for pair in body.decode("utf-8").split("&"):
        if "=" in pair:
            key, val = pair.split("=", 1)
            from urllib.parse import unquote_plus
            form_data[key] = unquote_plus(val)

    # Normalize to Surfit format
    normalized = normalize_real_slack_command(form_data)

    # Evaluate through wave engine
    eval_req = normalize_slack_event(normalized)
    result = engine.evaluate(eval_req)

    # Log
    channel = form_data.get("channel_name", "unknown")
    content_text = form_data.get("text", "")
    record = log_action(result, channel, content_text, source="real_slack", slack_metadata=normalized.get("slack_metadata"))

    # Respond to Slack with the wave result
    wave_emoji = {1: "\u2705", 2: "\U0001F4DD", 3: "\U0001F50D", 4: "\u26A0\uFE0F", 5: "\U0001F6D1"}
    handling_text = {
        "auto": "Allowed \u2014 executing autonomously",
        "log": "Allowed \u2014 logged for review",
        "check": "Held \u2014 requires verification",
        "approve": "Held \u2014 requires approval before execution",
        "block": "Blocked \u2014 action denied",
    }

    emoji = wave_emoji.get(result.wave_score, "\U0001F30A")
    handle = handling_text.get(result.handling, result.handling)

    slack_response = {
        "response_type": "ephemeral",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Surfit \u2014 {result.wave_label}*\n*Decision:* {handle}\n*Channel:* #{channel}\n*Action:* {content_text or 'post_message'}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": " | ".join(result.reasons[-3:])}
                ]
            }
        ]
    }

    return JSONResponse(slack_response)


# ============================================================
# REAL SLACK EVENTS API ENDPOINT
# ============================================================

@app.post("/api/v1/slack/events")
async def slack_events(request: Request):
    """
    Receives real Slack Events API webhooks.
    Handles url_verification challenge and message events.
    """
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
    signature = request.headers.get("X-Slack-Signature", "")

    if SLACK_SIGNING_SECRET and not verify_slack_signature(body, timestamp, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    data = json.loads(body)

    # Handle Slack URL verification challenge
    if data.get("type") == "url_verification":
        return JSONResponse({"challenge": data.get("challenge")})

    # Handle message events
    if data.get("type") == "event_callback":
        event = data.get("event", {})

        # Skip bot messages to avoid loops
        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return JSONResponse({"ok": True})

        if event.get("type") == "message":
            normalized = normalize_real_slack_event(event)
            eval_req = normalize_slack_event(normalized)
            result = engine.evaluate(eval_req)

            channel = event.get("channel", "unknown")
            content_text = event.get("text", "")
            log_action(result, channel, content_text, source="real_slack_event")

    return JSONResponse({"ok": True})


# ============================================================
# LOCAL SLACK INGESTION (unchanged from V2.1)
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
    """Local/simulated Slack ingestion (dashboard simulate buttons)."""
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
# ACTION LOG + HEALTH
# ============================================================

@app.get("/api/v1/actions")
def get_actions():
    return {"actions": action_log}

@app.get("/api/v1/health")
def health():
    slack_configured = bool(SLACK_SIGNING_SECRET)
    return {
        "status": "ok", "engine": "surfit-v2.2", "version": "2.2.0",
        "slack_configured": slack_configured,
        "endpoints": [
            "POST /api/v1/governance/evaluate",
            "POST /api/v1/ingest/slack",
            "POST /api/v1/slack/command",
            "POST /api/v1/slack/events",
            "GET /api/v1/actions",
        ],
        "ingested_actions": len(action_log),
    }

if __name__ == "__main__":
    slack_status = "configured" if SLACK_SIGNING_SECRET else "not configured (set SLACK_SIGNING_SECRET)"
    print(f"\n  \U0001F30A SurfitAI Wave Engine v2.2")
    print(f"  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print(f"  API:      http://localhost:8000")
    print(f"  Docs:     http://localhost:8000/docs")
    print(f"  Slack:    {slack_status}")
    print(f"  Command:  POST /api/v1/slack/command")
    print(f"  Events:   POST /api/v1/slack/events")
    print(f"  Ingest:   POST /api/v1/ingest/slack")
    print(f"  Actions:  GET /api/v1/actions\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
