"""
SURFIT V2.1 — Wave Engine API + Slack Ingestion
Run: python server.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uvicorn, sys, os, uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo, ContentMetadata

app = FastAPI(title="SurfitAI Wave Engine", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000","http://127.0.0.1:3001"], allow_methods=["*"], allow_headers=["*"])

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
# NORMALIZATION LAYER
# The seam between event sources and the wave engine.
# Today: local/mock payloads.
# Tomorrow: real Slack Events API / webhooks.
# Only this function changes when plugging in real Slack.
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

# ============================================================
# SLACK INGESTION ENDPOINT
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
    """
    Slack ingestion path.
    Normalizes Slack-style events → evaluates through wave engine → logs result.
    Future: replace payload source with real Slack Events API webhook.
    """
    eval_req = normalize_slack_event(payload.dict())
    result = engine.evaluate(eval_req)

    action_id = f"slack-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    channel = (payload.resource or {}).get("channel_name", "unknown")
    content_text = (payload.content or {}).get("text")

    record = {
        "id": action_id,
        "source": "slack_ingestion",
        "event_type": payload.event_type,
        "system": "slack",
        "action": payload.action,
        "resource": payload.resource or {},
        "context": payload.context or {},
        "content_preview": content_text[:80] if content_text else None,
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
        "proof": {
            "channel": f"#{channel}",
            "evaluated_at": now,
            "wave": result.wave_label,
            "content_preview": content_text[:40] if content_text else None,
        },
    }

    action_log.insert(0, record)
    if len(action_log) > 100:
        action_log.pop()

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
    return {"status": "ok", "engine": "surfit-v2.1", "version": "2.1.0",
            "endpoints": ["POST /api/v1/governance/evaluate", "POST /api/v1/ingest/slack", "GET /api/v1/actions"],
            "ingested_actions": len(action_log)}

if __name__ == "__main__":
    print("\n  \U0001F30A SurfitAI Wave Engine v2.1")
    print("  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    print("  API:     http://localhost:8000")
    print("  Docs:    http://localhost:8000/docs")
    print("  Ingest:  POST /api/v1/ingest/slack")
    print("  Actions: GET /api/v1/actions\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
