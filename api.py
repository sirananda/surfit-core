from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uuid

app = FastAPI(title="SurFit Runtime API", version="m13-poc")


class WaveRunRequest(BaseModel):
    wave_template_id: str
    policy_version: str
    intent: str
    context_refs: dict[str, Any]


class ApprovalRequest(BaseModel):
    approved_by: str
    note: str | None = None


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest):
    wave_id = str(uuid.uuid4())
    return {
        "wave_id": wave_id,
        "status": "running",
    }

@app.get("/api/waves/{wave_id}/status")
def wave_status(wave_id: str):
    return {
        "wave_id": wave_id,
        "status": "needs_approval",
        "approval_request_id": f"apr_{wave_id[:8]}",
        "summary": {"output_path": "./outputs/report.md"},
    }

@app.post("/api/approvals/{approval_request_id}")
def approve_wave(approval_request_id: str, req: ApprovalRequest):
    wave_id = approval_request_id.replace("apr_", "")
    return {
        "wave_id": wave_id,
        "status": "complete",
        "approval_request_id": approval_request_id,
        "approved_by": req.approved_by,
        "note": req.note,
    }

@app.get("/api/waves/{wave_id}/audit/export")
def export_audit(wave_id: str):
    return {
        "wave_id": wave_id,
        "integrity_status": "VALID",
        "policy_hash": "demo_policy_hash_placeholder",
        "approval": {
            "approved_by": "andreas@surfit.ai",
            "approved_at": "2026-02-23T00:00:00Z",
            "note": "POC approval",
            "proposed_write_hash": "demo_proposed_write_hash_placeholder",
        },
        "events": [
            {"node": "load_csv", "status": "ok"},
            {"node": "compute_metrics", "status": "ok"},
            {"node": "llm_summary", "status": "ok"},
            {"node": "propose_write_report", "status": "ok"},
            {"node": "approval_gate", "status": "approved"},
            {"node": "commit_write_report", "status": "ok"},
        ],
        "llm_invocations": [
            {
                "provider": "anthropic",
                "model_name": "claude",
                "model_version": "placeholder",
            }
        ],
    }

