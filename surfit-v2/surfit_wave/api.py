"""
SURFIT Wave Engine — API Layer
RESTful endpoints for wave evaluation.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


# ============================================================
# API REQUEST / RESPONSE SHAPES
# ============================================================

# REQUEST (matches directive Section 9)
EVALUATE_REQUEST_SCHEMA = {
    "system": "slack",                          # required
    "action": "post_message",                   # required
    "resource": {                               # optional
        "resource_id": "C04ABCDEF",
        "resource_name": "company-announcements",
        "destination_class": None,              # auto-resolved if not provided
    },
    "context": {                                # optional, defaults applied
        "env": "prod",
        "visibility": "company_wide",
        "reversible": True,
        "sensitive_data": False,
        "financial_impact": False,
        "deployment_stable": True,
        "approval_required_override": False,
    },
    "content_metadata": {                       # optional, secondary signal
        "message_type": "deployment_update",
        "contains_mentions": False,
        "contains_links": False,
        "estimated_reach": None,
    },
    "agent_id": "agent-openclaw-001",           # optional
    "tenant_id": "acme-corp",                   # optional
}

# RESPONSE
EVALUATE_RESPONSE_SCHEMA = {
    "wave_score": 4,
    "wave_label": "Wave 4",
    "handling": "approve",
    "destination_class_resolved": "company_announcement",
    "reasons": [
        "System baseline: slack=1",
        "Action modifier: post_announcement=+2",
        "Destination: company_announcement=+2 (Company-wide announcement channels)",
        "Context: visibility=company_wide => +1 (Company-wide visibility)",
        "Final: Wave 4 => approve",
    ],
    "contributing_factors": [
        {"source": "system_baseline", "key": "slack", "modifier": 1, "description": "System baseline: slack=1"},
        {"source": "action_modifier", "key": "slack/post_announcement", "modifier": 2, "description": "Action modifier: post_announcement=+2"},
        {"source": "destination_modifier", "key": "slack/company_announcement", "modifier": 2, "description": "Destination: company_announcement=+2"},
        {"source": "context_modifier", "key": "visibility=company_wide", "modifier": 1, "description": "Context: visibility=company_wide => +1"},
    ],
}


def create_app():
    """
    Create a FastAPI app with wave evaluation endpoints.
    Import this and run with uvicorn when ready to serve.
    """
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn")
        return None

    from .engine import WaveEngine
    from .models import EvaluateRequest, ResourceInfo, ContextInfo, ContentMetadata

    app = FastAPI(title="SurfitAI Wave Engine", version="1.0.0")
    engine = WaveEngine()

    class ResourceIn(BaseModel):
        resource_id: Optional[str] = None
        resource_name: Optional[str] = None
        destination_class: Optional[str] = None

    class ContextIn(BaseModel):
        env: str = "prod"
        visibility: str = "internal"
        reversible: bool = True
        sensitive_data: bool = False
        financial_impact: bool = False
        deployment_stable: bool = True
        approval_required_override: bool = False

    class ContentIn(BaseModel):
        message_type: Optional[str] = None
        contains_mentions: bool = False
        contains_links: bool = False
        estimated_reach: Optional[int] = None

    class EvalIn(BaseModel):
        system: str
        action: str
        resource: Optional[ResourceIn] = None
        context: Optional[ContextIn] = None
        content_metadata: Optional[ContentIn] = None
        agent_id: Optional[str] = None
        tenant_id: Optional[str] = None

    @app.post("/api/v1/governance/evaluate")
    def evaluate(req: EvalIn):
        eval_req = EvaluateRequest(
            system=req.system,
            action=req.action,
            resource=ResourceInfo(
                resource_id=req.resource.resource_id if req.resource else None,
                resource_name=req.resource.resource_name if req.resource else None,
                destination_class=req.resource.destination_class if req.resource else None,
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
            content_metadata=ContentMetadata(
                message_type=req.content_metadata.message_type if req.content_metadata else None,
            ) if req.content_metadata else None,
            agent_id=req.agent_id,
            tenant_id=req.tenant_id,
        )
        result = engine.evaluate(eval_req)
        return result.to_dict()

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "engine": "wave-engine-v1"}

    return app
