"""
SURFIT V2 — Wave Engine API Server
Run: python server.py
Serves on http://localhost:8000
CORS enabled for localhost:3000 (dashboard)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import sys
import os

# Add wave engine to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from surfit_wave.engine import WaveEngine
from surfit_wave.models import EvaluateRequest, ResourceInfo, ContextInfo, ContentMetadata

app = FastAPI(title="SurfitAI Wave Engine", version="2.0.0")

# CORS for dashboard at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = WaveEngine()


# ── Request Models ──

class ResourceIn(BaseModel):
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    channel_name: Optional[str] = None  # alias for resource_name (Slack)
    repo: Optional[str] = None          # alias for resource_name (GitHub)
    database: Optional[str] = None      # alias for resource_name (Notion)
    destination_class: Optional[str] = None

class ContextIn(BaseModel):
    env: str = "prod"
    visibility: str = "internal"
    reversible: bool = True
    sensitive_data: bool = False
    financial_impact: bool = False
    deployment_stable: bool = True
    approval_required_override: bool = False

class EvalIn(BaseModel):
    system: str
    action: str
    resource: Optional[ResourceIn] = None
    context: Optional[ContextIn] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None


# ── Endpoints ──

@app.post("/api/v1/governance/evaluate")
def evaluate(req: EvalIn):
    # Resolve resource_name from aliases
    resource_name = None
    resource_id = None
    dest_class = None

    if req.resource:
        resource_name = (
            req.resource.resource_name or
            req.resource.channel_name or
            req.resource.repo or
            req.resource.database
        )
        resource_id = req.resource.resource_id
        dest_class = req.resource.destination_class

    eval_req = EvaluateRequest(
        system=req.system,
        action=req.action,
        resource=ResourceInfo(
            resource_id=resource_id,
            resource_name=resource_name,
            destination_class=dest_class,
        ) if req.resource else None,
        context=ContextInfo(
            env=req.context.env if req.context else "prod",
            visibility=req.context.visibility if req.context else "internal",
            reversible=req.context.reversible if req.context else True,
            sensitive_data=req.context.sensitive_data if req.context else False,
            financial_impact=req.context.financial_impact if req.context else False,
            deployment_stable=req.context.deployment_stable if req.context else True,
            approval_required_override=req.context.approval_required_override if req.context else False,
        ) if req.context else None,
        agent_id=req.agent_id,
        tenant_id=req.tenant_id,
    )

    result = engine.evaluate(eval_req)
    return result.to_dict()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "engine": "surfit-wave-engine-v2", "version": "2.0.0"}


if __name__ == "__main__":
    print("\n  🌊 SurfitAI Wave Engine v2.0")
    print("  ───────────────────────────")
    print("  API:  http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("  Health: http://localhost:8000/api/v1/health\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
