from fastapi import FastAPI, Request, Query, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
import sqlite3
import json
import time
import os
import shutil
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
try:
    import anthropic
except ModuleNotFoundError:
    class _AnthropicStub:
        class Anthropic:  # type: ignore[no-redef]
            def __init__(self, *args, **kwargs):
                raise RuntimeError(
                    "anthropic package is not installed. Install with: python3.11 -m pip install anthropic"
                )

    anthropic = _AnthropicStub()  # type: ignore[assignment]
from pathlib import Path

try:
    from surfit_core.ocean import mutate_config as ocean_mutate_config_core
except ModuleNotFoundError:
    def ocean_mutate_config_core(*args, **kwargs):  # type: ignore[no-redef]
        return {
            "status": "REJECTED",
            "reason_code": "MUTATION_CORE_UNAVAILABLE",
            "message": "surfit_core.ocean is unavailable in this build.",
        }

from surfit.connectors.adapter_registry import (
    resolve_connector_type,
    prepare_connector_context,
    dispatch_connector_action,
)
from surfit.runtime.artifact_service import ArtifactRetrievalService, ArtifactService
from surfit.runtime.execution_gateway import ExecutionGateway
from surfit.runtime.policy_manifest_loader import PolicyManifestLoader
from surfit.runtime.policy_engine import DefaultPolicyEngine
from surfit.runtime.tenant_context import TenantContextResolver
from surfit.runtime.token_validation import TokenValidationLayer
from surfit.runtime.token_service import TokenService, TokenServiceError
from surfit.runtime.wave_lifecycle_store import WaveInsertPayload, WaveLifecycleStore
from surfit.runtime.mutation_boundary import MutationBoundaryConfig, MutationBoundaryService
from surfit.runtime.wave_service import WaveService
from surfit.runtime.wave_read_service import WaveReadService
from surfit.runtime.tenant_dashboard_access import TenantDashboardAccessService
from surfit.runtime.wave_orchestrator import (
    RuntimeGatewayOrchestratorRequest,
    WaveOrchestrator,
    WaveRunPreparationDeps,
)
from surfit.runtime.wave_application_service import (
    WaveApplicationService,
    WaveRunApplicationDeps,
    WaveRunApplicationRequest,
)
from surfit.storage.artifact_store import FileArtifactStore
from surfit.demos.handlers._common import DemoHandlerDeps, DemoHandlerError
from surfit.demos.handlers.context_router import prepare_wave_context
from surfit.demos.handlers.router import dispatch_template_handler

PROJECT_ROOT = Path(__file__).resolve().parent
RUNTIME_ARTIFACTS_ROOT = Path(os.environ.get("SURFIT_RUNTIME_ARTIFACTS_ROOT", str(PROJECT_ROOT / "artifacts")))
_RUNTIME_POLICY_MANIFEST_PATH = Path(
    os.environ.get("SURFIT_POLICY_ALLOWLISTS_PATH", str(PROJECT_ROOT / "policies" / "allowlists.json"))
)
RUNTIME_POLICY_MANIFEST_LOADER = PolicyManifestLoader(
    base_dir=_RUNTIME_POLICY_MANIFEST_PATH.parent,
    default_manifest_name=_RUNTIME_POLICY_MANIFEST_PATH.name,
)
RUNTIME_TENANT_CONTEXT = TenantContextResolver(
    artifacts_root=RUNTIME_ARTIFACTS_ROOT,
    default_tenant_id=os.environ.get("SURFIT_DEFAULT_TENANT_ID", "tenant_demo"),
)
RUNTIME_ARTIFACT_RETRIEVAL = ArtifactRetrievalService(RUNTIME_ARTIFACTS_ROOT)
RUNTIME_WAVE_READ_SERVICE = WaveReadService(RUNTIME_ARTIFACT_RETRIEVAL)
TENANT_DASHBOARD_CONFIG_PATH = Path(
    os.environ.get("SURFIT_TENANT_DASHBOARD_CONFIG_PATH", str(PROJECT_ROOT / "tenants" / "dashboard_access.json"))
)
TENANT_DASHBOARD_ACCESS_SERVICE = TenantDashboardAccessService(TENANT_DASHBOARD_CONFIG_PATH)
RUNTIME_TOKEN_VALIDATION = TokenValidationLayer()
RUNTIME_POLICY_ENGINE = DefaultPolicyEngine(RUNTIME_POLICY_MANIFEST_LOADER)
RUNTIME_WAVE_SERVICE = WaveService()
RUNTIME_WAVE_ORCHESTRATOR = WaveOrchestrator(RUNTIME_TENANT_CONTEXT)
RUNTIME_WAVE_APPLICATION_SERVICE = WaveApplicationService()
RUNTIME_WAVE_LIFECYCLE_STORE = WaveLifecycleStore(
    default_tenant_id=os.environ.get("SURFIT_DEFAULT_TENANT_ID", "tenant_demo"),
    now_iso=lambda: datetime.now(timezone.utc).isoformat(),
    sha256_text=lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest(),
    canonicalize_policy_manifest=lambda payload: json.dumps(payload, sort_keys=True, separators=(",", ":")),
)


def _resolve_db_path(project_root: Path) -> str:
    db_url = os.environ.get("SURFIT_DB_URL", "").strip()
    if db_url:
        if db_url.startswith("sqlite:///"):
            return db_url.replace("sqlite:///", "", 1)
        if db_url.startswith("sqlite://"):
            return db_url.replace("sqlite://", "", 1)
        # Postgres/other URLs are reserved for future adapter-backed DB support.
    return os.environ.get("SURFIT_DB_PATH", str(project_root / "surfit_runs.db"))


DB_PATH = _resolve_db_path(PROJECT_ROOT)
SURFIT_ENV = os.environ.get("SURFIT_ENV", "dev").strip().lower() or "dev"
MAX_RUNTIME_SECONDS = 30
WAVE_TOKEN_TTL_SECONDS = 180
WAVE_MUTATION_TOKEN_TTL_SECONDS = int(os.environ.get("SURFIT_WAVE_MUTATION_TOKEN_TTL_SECONDS", "600"))
SURFIT_TOKEN_SECRET = os.environ.get("SURFIT_TOKEN_SECRET", "surfit-local-dev-secret")
DEMO_SAFE_MODE = os.environ.get("DEMO_SAFE_MODE", "1").lower() not in {"0", "false", "off"}
OCEAN_PROXY_TIMEOUT_SECONDS = int(os.environ.get("SURFIT_PROXY_TIMEOUT_SECONDS", "5"))
OCEAN_PROXY_MAX_RESPONSE_BYTES = int(os.environ.get("SURFIT_PROXY_MAX_RESPONSE_BYTES", "1048576"))
RATE_LIMIT_WAVES_PER_MIN = int(os.environ.get("SURFIT_RATE_LIMIT_WAVES_PER_MIN", "30"))
RATE_LIMIT_PROXY_PER_MIN = int(os.environ.get("SURFIT_RATE_LIMIT_PROXY_PER_MIN", "300"))
RATE_LIMIT_EXPORT_PER_MIN = int(os.environ.get("SURFIT_RATE_LIMIT_EXPORT_PER_MIN", "20"))
TOKEN_REPLAY_MAX_USES = int(os.environ.get("SURFIT_TOKEN_REPLAY_MAX_USES", "1000"))
TOKEN_REPLAY_GRACE_SECONDS = int(os.environ.get("SURFIT_TOKEN_REPLAY_GRACE_SECONDS", "60"))
DEFAULT_TENANT_ID = os.environ.get("SURFIT_DEFAULT_TENANT_ID", "tenant_demo")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
REDIS_URL = os.environ.get("REDIS_URL", "").strip()

RUNTIME_TOKEN_SERVICE = TokenService(
    token_validation=RUNTIME_TOKEN_VALIDATION,
    wave_token_ttl_seconds=WAVE_TOKEN_TTL_SECONDS,
    sha256_text=lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest(),
)

_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_BUCKETS: dict[str, deque[float]] = defaultdict(deque)

def _load_api_key_tenant_map() -> dict[str, str]:
    raw_json = os.environ.get("SURFIT_API_KEYS_JSON", "").strip()
    if raw_json:
        try:
            payload = json.loads(raw_json)
            if isinstance(payload, dict):
                out: dict[str, str] = {}
                for key, tenant in payload.items():
                    k = str(key).strip()
                    t = str(tenant).strip()
                    if k and t:
                        out[k] = t
                if out:
                    return out
        except Exception:
            pass

    raw_csv = os.environ.get("SURFIT_API_KEYS", "").strip()
    if raw_csv:
        out = {}
        for key in raw_csv.split(","):
            k = key.strip()
            if k:
                out[k] = DEFAULT_TENANT_ID
        if out:
            return out

    if SURFIT_ENV == "prod":
        return {}

    # Local dev default keeps single-process demos working.
    return {"surfit-demo-key": DEFAULT_TENANT_ID, "surfit-other-key": "tenant_other"}


API_KEY_TENANT_MAP = _load_api_key_tenant_map()


def _is_truthy_env(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _validate_production_config() -> None:
    strict_prod = _is_truthy_env("SURFIT_REQUIRE_EXPLICIT_PROD_CONFIG", default=(SURFIT_ENV == "prod"))
    if SURFIT_ENV != "prod" or not strict_prod:
        return

    missing: list[str] = []
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not REDIS_URL:
        missing.append("REDIS_URL")
    if not os.environ.get("SURFIT_API_KEYS_JSON", "").strip() and not os.environ.get("SURFIT_API_KEYS", "").strip():
        missing.append("SURFIT_API_KEYS_JSON or SURFIT_API_KEYS")
    if not os.environ.get("SURFIT_DEFAULT_TENANT_ID", "").strip():
        missing.append("SURFIT_DEFAULT_TENANT_ID")
    if SURFIT_TOKEN_SECRET in {"", "surfit-local-dev-secret"}:
        missing.append("SURFIT_TOKEN_SECRET (must not use local default)")
    if DEFAULT_TENANT_ID == "tenant_demo":
        missing.append("SURFIT_DEFAULT_TENANT_ID must not be tenant_demo")
    if not POLICY_ALLOWLISTS_PATH.exists():
        missing.append(f"SURFIT_POLICY_ALLOWLISTS_PATH file not found: {POLICY_ALLOWLISTS_PATH}")

    if missing:
        raise RuntimeError(
            "Production configuration is incomplete. Set explicit values for: "
            + ", ".join(missing)
        )

DEFAULT_AGENT_WAVE_ALLOWLIST = {
    "openclaw_poc_agent_v1": {"sales_report_v1"},
    "openclaw_marketing_agent_v1": {"marketing_digest_v1"},  # backward compatibility
    "openclaw_market_intelligence_agent_v1": {"market_intelligence_digest_v1"},
    "production_config_agent": {"production_config_change_v1"},
    "surfit_builder_agent_v1": {"surfit_builder_brief_v1"},
    "enterprise_change_control_agent": {"ENTERPRISE_CHANGE_CONTROL_V1"},
    "enterprise_integration_governance_agent": {"ENTERPRISE_INTEGRATION_GOVERNANCE_V1"},
    "github_governance_agent": {"ENTERPRISE_GITHUB_GOVERNANCE_V1"},
    "github_multistage_governance_agent": {"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
    "openclaw_cross_agent_governance_agent": {"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
    "langgraph_cross_agent_governance_agent": {"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
    "internal_automation_cross_agent_agent": {"ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"},
}

DEFAULT_TEMPLATE_POLICY_ALLOWLIST = {
    "sales_report_v1": {"sales_report_policy_v1"},
    "marketing_digest_v1": {"marketing_digest_policy_v1", "market_intelligence_digest_policy_v1"},
    "market_intelligence_digest_v1": {"market_intelligence_digest_policy_v1"},
    "production_config_change_v1": {"prod_config_policy_v1"},
    "surfit_builder_brief_v1": {"surfit_builder_policy_v1"},
    "ENTERPRISE_CHANGE_CONTROL_V1": {"enterprise_change_control_policy_v1"},
    "ENTERPRISE_INTEGRATION_GOVERNANCE_V1": {"enterprise_integration_governance_policy_v1"},
    "ENTERPRISE_GITHUB_GOVERNANCE_V1": {"enterprise_github_governance_policy_v1"},
    "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {"enterprise_multistage_execution_governance_policy_v1"},
}

POLICY_ALLOWLISTS_PATH = Path(
    os.environ.get("SURFIT_POLICY_ALLOWLISTS_PATH", str(PROJECT_ROOT / "policies" / "allowlists.json"))
)


def _normalize_allowlist_map(raw: dict[str, Any]) -> dict[str, set[str]]:
    normalized: dict[str, set[str]] = {}
    for key, values in raw.items():
        if isinstance(values, (list, set, tuple)):
            normalized[str(key)] = {str(v) for v in values}
    return normalized


def _sorted_allowlist_map(raw: dict[str, set[str]]) -> dict[str, list[str]]:
    return {
        key: sorted(values)
        for key, values in sorted(raw.items(), key=lambda item: item[0])
    }


def _canonicalize_policy_manifest(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _default_policy_manifest_payload() -> dict[str, Any]:
    return {
        "agent_wave_allowlist": _sorted_allowlist_map(DEFAULT_AGENT_WAVE_ALLOWLIST),
        "template_policy_allowlist": _sorted_allowlist_map(DEFAULT_TEMPLATE_POLICY_ALLOWLIST),
        "http_proxy_allowlist": {
            "allowed_domains": ["localhost", "127.0.0.1", "::1"],
            "allowed_methods": ["GET"],
        },
        "template_runtime_scopes": {
            "ENTERPRISE_INTEGRATION_GOVERNANCE_V1": {
                "allowlisted_paths": ["/repo/docs/", "/repo/tests/"],
                "allowlisted_tools": [
                    "repo.file_update",
                    "deployment.approve_release",
                    "slack.channel.post_message",
                ],
            },
            "ENTERPRISE_GITHUB_GOVERNANCE_V1": {
                "allowlisted_paths": [
                    "/docs/",
                    "/agents/output/",
                    "/reports/",
                ],
                "denied_paths": [
                    "/.github/workflows/*",
                    "/infra/*",
                    "/security/*",
                    "/secrets/*",
                    "/src/*",
                    "/app/*",
                    "/backend/*",
                ],
                "allowlisted_actions": [
                    "create_branch",
                    "commit_file",
                    "open_pull_request",
                ],
                "denied_actions": [
                    "merge_pull_request",
                    "force_push",
                    "delete_branch",
                ],
                "allowlisted_repos": ["surfit-demo-repo"],
                "allowlisted_tools": [
                    "github.create_branch",
                    "github.commit_file",
                    "github.open_pull_request",
                ],
                "github_policy": {
                    "allowed_repos": ["surfit-demo-repo"],
                    "allowed_paths": ["docs/*", "agents/output/*", "reports/*"],
                    "denied_paths": [
                        ".github/workflows/*",
                        "infra/*",
                        "security/*",
                        "secrets/*",
                        "src/*",
                        "app/*",
                        "backend/*",
                    ],
                    "allowed_actions": [
                        "create_branch",
                        "commit_file",
                        "open_pull_request",
                    ],
                    "denied_actions": [
                        "merge_pull_request",
                        "force_push",
                        "delete_branch",
                    ],
                },
            },
            "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1": {
                "allowlisted_paths": [
                    "/docs/",
                    "/agents/output/",
                    "/reports/",
                ],
                "denied_paths": [
                    "/.github/workflows/*",
                    "/infra/*",
                    "/security/*",
                    "/secrets/*",
                    "/src/*",
                    "/app/*",
                    "/backend/*",
                ],
                "allowlisted_actions": [
                    "create_branch",
                    "commit_file",
                    "open_pull_request",
                    "merge_pull_request",
                ],
                "denied_actions": [
                    "force_push",
                    "delete_branch",
                ],
                "allowlisted_repos": ["surfit-demo-repo"],
                "allowlisted_tools": [
                    "github.create_branch",
                    "github.commit_file",
                    "github.open_pull_request",
                    "github.merge_pull_request",
                ],
                "github_policy": {
                    "allowed_repos": ["surfit-demo-repo"],
                    "allowed_paths": ["docs/*", "agents/output/*", "reports/*"],
                    "denied_paths": [
                        ".github/workflows/*",
                        "infra/*",
                        "security/*",
                        "secrets/*",
                        "src/*",
                        "app/*",
                        "backend/*",
                    ],
                    "allowed_actions": [
                        "create_branch",
                        "commit_file",
                        "open_pull_request",
                        "merge_pull_request",
                    ],
                    "denied_actions": [
                        "force_push",
                        "delete_branch",
                    ],
                    "require_approval_for_actions": [
                        "merge_pull_request",
                    ],
                },
            },
        },
    }


def _ensure_demo8_execution_path_primitives(payload: dict[str, Any]) -> dict[str, Any]:
    scopes = payload.get("template_runtime_scopes")
    if not isinstance(scopes, dict):
        return payload
    key = "ENTERPRISE_MULTI_STAGE_EXECUTION_GOVERNANCE_V1"
    scope = scopes.get(key)
    if not isinstance(scope, dict):
        return payload

    def _append_unique(seq: Any, value: str) -> list[str]:
        out = [str(x) for x in (seq if isinstance(seq, list) else [])]
        if value not in out:
            out.append(value)
        return out

    scope["allowlisted_tools"] = _append_unique(scope.get("allowlisted_tools"), "github.review_commit")
    scope["allowlisted_actions"] = _append_unique(scope.get("allowlisted_actions"), "review_commit")

    github_policy = scope.get("github_policy")
    if isinstance(github_policy, dict):
        github_policy["allowed_actions"] = _append_unique(github_policy.get("allowed_actions"), "review_commit")

    proxy_allowlist = payload.get("http_proxy_allowlist")
    if isinstance(proxy_allowlist, dict):
        prefixes = [str(x) for x in (proxy_allowlist.get("allowed_url_prefixes", []) if isinstance(proxy_allowlist.get("allowed_url_prefixes"), list) else [])]
        review_prefixes: list[str] = []
        for p in prefixes:
            for suffix in ("/github/create_branch", "/github/commit_file", "/github/open_pull_request", "/github/merge_pull_request"):
                if p.endswith(suffix):
                    review_prefixes.append(p[: -len(suffix)] + "/github/review_commit")
                    break
        if not review_prefixes:
            review_prefixes = ["http://127.0.0.1:8050/github/review_commit"]
        for rp in review_prefixes:
            if rp not in prefixes:
                prefixes.append(rp)
        proxy_allowlist["allowed_url_prefixes"] = prefixes

    return payload


def _load_policy_manifest_snapshot() -> dict[str, Any]:
    payload: dict[str, Any]
    version: str | None = None

    if POLICY_ALLOWLISTS_PATH.exists():
        try:
            raw = json.loads(POLICY_ALLOWLISTS_PATH.read_text(encoding="utf-8"))
            agent_map = _normalize_allowlist_map(raw.get("agent_wave_allowlist", {}))
            template_map = _normalize_allowlist_map(raw.get("template_policy_allowlist", {}))
            if agent_map and template_map:
                payload = {
                    "agent_wave_allowlist": _sorted_allowlist_map(agent_map),
                    "template_policy_allowlist": _sorted_allowlist_map(template_map),
                    "http_proxy_allowlist": raw.get("http_proxy_allowlist", _default_policy_manifest_payload()["http_proxy_allowlist"]),
                    "template_runtime_scopes": raw.get(
                        "template_runtime_scopes",
                        _default_policy_manifest_payload().get("template_runtime_scopes", {}),
                    ),
                }
                raw_version = raw.get("policy_manifest_version")
                if raw_version is not None:
                    version = str(raw_version)
            else:
                payload = _default_policy_manifest_payload()
        except Exception:
            payload = _default_policy_manifest_payload()
    else:
        payload = _default_policy_manifest_payload()

    payload = _ensure_demo8_execution_path_primitives(payload)
    canonical = _canonicalize_policy_manifest(payload)
    manifest_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    manifest_version = version or f"{POLICY_ALLOWLISTS_PATH.name}@sha256:{manifest_hash}"

    return {
        "manifest_payload": payload,
        "manifest_json": canonical,
        "manifest_hash": manifest_hash,
        "manifest_version": manifest_version,
        "agent_allowlist": _normalize_allowlist_map(payload.get("agent_wave_allowlist", {})),
        "template_policy_allowlist": _normalize_allowlist_map(payload.get("template_policy_allowlist", {})),
    }


_INITIAL_POLICY_SNAPSHOT = _load_policy_manifest_snapshot()
AGENT_WAVE_ALLOWLIST = _INITIAL_POLICY_SNAPSHOT["agent_allowlist"]
TEMPLATE_POLICY_ALLOWLIST = _INITIAL_POLICY_SNAPSHOT["template_policy_allowlist"]
MARKET_INTEL_TEMPLATES = {"marketing_digest_v1", "market_intelligence_digest_v1"}
RUNS_ROOT = Path("./runs")
PROD_CONFIG_TARGET = "demo_artifacts/prod_config.json"
PROD_CONFIG_ALLOWED_KEYS = {
    "feature_flags.checkout_v2",
    "rate_limits.requests_per_minute",
    "logging.level",
}

RUNTIME_MUTATION_BOUNDARY = MutationBoundaryService(
    MutationBoundaryConfig(
        token_secret=SURFIT_TOKEN_SECRET,
        mutation_token_ttl_seconds=WAVE_MUTATION_TOKEN_TTL_SECONDS,
        demo_safe_mode=DEMO_SAFE_MODE,
        proxy_timeout_seconds=OCEAN_PROXY_TIMEOUT_SECONDS,
        proxy_max_response_bytes=OCEAN_PROXY_MAX_RESPONSE_BYTES,
        token_replay_max_uses=TOKEN_REPLAY_MAX_USES,
        token_replay_grace_seconds=TOKEN_REPLAY_GRACE_SECONDS,
        market_intel_templates=MARKET_INTEL_TEMPLATES,
        prod_config_target=PROD_CONFIG_TARGET,
        prod_config_allowed_keys=PROD_CONFIG_ALLOWED_KEYS,
    ),
    resolve_connector_type=resolve_connector_type,
    canonicalize_policy_manifest=_canonicalize_policy_manifest,
    sha256_text=lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest(),
)

app = FastAPI(title="SurFit Runtime API", version="m13-poc")
if (PROJECT_ROOT / "surfit_console").exists():
    app.mount("/surfit-console", StaticFiles(directory=str(PROJECT_ROOT / "surfit_console"), html=True), name="surfit_console")
if (PROJECT_ROOT / "surfit_tenant_dashboard").exists():
    app.mount("/tenant-dashboard", StaticFiles(directory=str(PROJECT_ROOT / "surfit_tenant_dashboard"), html=True), name="surfit_tenant_dashboard")


class WaveRunRequest(BaseModel):
    agent_id: str | None = None
    wave_template_id: str
    policy_version: str
    intent: str
    context_refs: dict[str, Any]


class ApprovalRequest(BaseModel):
    approved_by: str
    note: str | None = None


class MutationItem(BaseModel):
    json_path: str
    value: Any


class ConfigMutateRequest(BaseModel):
    wave_id: str | None = None
    wave_token: str | None = None
    agent_name: str
    policy_version: str
    target_path: str
    mutations: list[MutationItem]
    reason: str | None = None


class OceanProxyHttpRequest(BaseModel):
    method: str
    url: str
    headers: dict[str, str] | None = None
    json_body: Any | None = None
    body: str | None = None
    wave_mutation_token: str | None = None
    governance_context: dict[str, Any] | None = None


class RuntimeGatewayRequest(BaseModel):
    wave_id: str
    wave_type: str
    system: str
    action: str
    risk_level: str
    approval_required: bool = False
    required_execution_sequence: list[str] = Field(default_factory=list)
    approval_rules: dict[str, Any] = Field(default_factory=dict)
    execution_timeout: int | None = None
    trigger_type: str = "manual"
    context: dict[str, Any] = Field(default_factory=dict)
    agent_id: str
    tenant_id: str | None = None
    orchestrator_id: str | None = None
    token_scope: list[str] = Field(default_factory=list)
    pinned_policy_manifest: list[str] = Field(default_factory=list)
    runtime_rules: list[str] = Field(default_factory=list)
    policy_manifest_hash: str | None = None
    policy_reference: str | None = None
    approval_linkage: dict[str, Any] | None = None
    execution_path_evidence: dict[str, Any] | None = None


class WaveExecutionError(Exception):
    def __init__(self, code: str, message: str, node: str):
        super().__init__(message)
        self.code = code
        self.node = node


def ensure_wave_tables(conn: sqlite3.Connection) -> None:
    RUNTIME_WAVE_LIFECYCLE_STORE.ensure_schema(conn)


@app.on_event("startup")
def initialize_runtime_schema() -> None:
    _validate_production_config()
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_wave_tables(conn)
    finally:
        conn.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_api_key(request: Request | None) -> tuple[str, str] | JSONResponse:
    # Internal direct function calls in unit tests may not provide Request.
    if request is None:
        return "__internal__", DEFAULT_TENANT_ID

    api_key = (request.headers.get("X-SURFIT-API-KEY") or "").strip()
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "API_KEY_MISSING", "message": "X-SURFIT-API-KEY header is required."}},
        )
    tenant_id = API_KEY_TENANT_MAP.get(api_key)
    if not tenant_id:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "API_KEY_INVALID", "message": "Invalid API key."}},
        )
    return api_key, tenant_id


def _authorize_wave_tenant(
    conn: sqlite3.Connection, wave_id: str, request: Request | None
) -> tuple[str, str] | JSONResponse:
    auth = _require_api_key(request)
    if isinstance(auth, JSONResponse):
        return auth
    api_key, tenant_id = auth
    wave = conn.execute("SELECT tenant_id FROM waves WHERE wave_id = ?", (wave_id,)).fetchone()
    if wave and wave[0] and str(wave[0]) != tenant_id:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "TENANT_MISMATCH", "message": "Wave belongs to a different tenant."}},
        )
    return api_key, tenant_id


def _parse_iso_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _resolve_time_window(
    since_hours: int = 24, from_ts: str | None = None, to_ts: str | None = None
) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    end_dt = _parse_iso_dt(to_ts) or now
    start_dt = _parse_iso_dt(from_ts) or (end_dt - timedelta(hours=max(1, int(since_hours))))
    return start_dt.astimezone(timezone.utc).isoformat(), end_dt.astimezone(timezone.utc).isoformat()


def _check_db_readiness() -> dict[str, Any]:
    target = DATABASE_URL or os.environ.get("SURFIT_DB_URL", "").strip()
    if target.startswith("postgresql://") or target.startswith("postgres://"):
        try:
            import psycopg
        except ModuleNotFoundError:
            return {"ready": False, "detail": "psycopg not installed"}
        try:
            with psycopg.connect(target, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return {"ready": True, "detail": "postgres ok"}
        except Exception as exc:
            return {"ready": False, "detail": f"postgres connect failed: {exc}"}

    # Default to sqlite readiness for current runtime schema.
    try:
        conn = sqlite3.connect(DB_PATH, timeout=2)
        ensure_wave_tables(conn)
        conn.close()
        return {"ready": True, "detail": "sqlite ok"}
    except Exception as exc:
        return {"ready": False, "detail": f"sqlite unavailable: {exc}"}


def _check_redis_readiness() -> dict[str, Any]:
    if not REDIS_URL:
        return {"ready": SURFIT_ENV != "prod", "detail": "REDIS_URL not set"}
    try:
        import redis
    except ModuleNotFoundError:
        return {"ready": False, "detail": "redis package not installed"}
    try:
        client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return {"ready": True, "detail": "redis ok"}
    except Exception as exc:
        return {"ready": False, "detail": f"redis ping failed: {exc}"}


def _log_api_event(
    conn: sqlite3.Connection,
    tenant_id: str,
    event_type: str,
    wave_id: str | None = None,
    reason_code: str | None = None,
    node: str | None = None,
    status: str | None = None,
) -> None:
    RUNTIME_WAVE_LIFECYCLE_STORE.log_api_event(
        conn,
        tenant_id=tenant_id,
        wave_id=wave_id,
        event_type=event_type,
        reason_code=reason_code,
        node=node,
        status=status,
    )


def _rate_limit_check(tenant_id: str, bucket: str, limit_per_min: int) -> bool:
    if limit_per_min <= 0:
        return True
    now = time.time()
    key = f"{tenant_id}:{bucket}"
    with _RATE_LIMIT_LOCK:
        q = _RATE_LIMIT_BUCKETS[key]
        while q and (now - q[0]) > 60:
            q.popleft()
        if len(q) >= limit_per_min:
            return False
        q.append(now)
        return True


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _decode_wave_mutation_token(token: str) -> tuple[dict[str, Any] | None, str | None]:
    return RUNTIME_MUTATION_BOUNDARY.decode_wave_mutation_token(token)


def _build_mutation_scope(
    wave_template_id: str,
    context_refs: dict[str, Any],
    policy_manifest_payload: dict[str, Any],
) -> dict[str, Any]:
    return RUNTIME_MUTATION_BOUNDARY.build_mutation_scope(
        wave_template_id,
        context_refs,
        policy_manifest_payload,
    )


def _mint_wave_mutation_token(
    wave_id: str,
    agent_id: str,
    policy_manifest_hash: str,
    policy_version: str,
    wave_template_id: str,
    scope: dict[str, Any],
    ttl_seconds: int = WAVE_MUTATION_TOKEN_TTL_SECONDS,
) -> tuple[str, str, str, str]:
    return RUNTIME_MUTATION_BOUNDARY.mint_wave_mutation_token(
        wave_id=wave_id,
        agent_id=agent_id,
        policy_manifest_hash=policy_manifest_hash,
        policy_version=policy_version,
        wave_template_id=wave_template_id,
        scope=scope,
        ttl_seconds=ttl_seconds,
    )


def _sha256_file(path: str) -> str | None:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _log_decision(
    conn: sqlite3.Connection,
    wave_id: str,
    decision: str,
    reason: str,
    rule: str,
    node: str,
    tenant_id: str | None = None,
) -> None:
    RUNTIME_WAVE_LIFECYCLE_STORE.log_decision(
        conn,
        wave_id=wave_id,
        decision=decision,
        reason=reason,
        rule=rule,
        node=node,
        tenant_id=tenant_id,
    )


def _fetch_decisions(conn: sqlite3.Connection, wave_id: str) -> list[dict[str, str | None]]:
    return RUNTIME_WAVE_LIFECYCLE_STORE.fetch_decisions(conn, wave_id)


def _verify_decision_chain(conn: sqlite3.Connection, wave_id: str) -> dict[str, Any]:
    return RUNTIME_WAVE_LIFECYCLE_STORE.verify_decision_chain(conn, wave_id)


def _verify_policy_manifest(policy_manifest_hash: str | None, policy_manifest_json: str | None) -> dict[str, Any]:
    return RUNTIME_WAVE_LIFECYCLE_STORE.verify_policy_manifest(policy_manifest_hash, policy_manifest_json)


def _issue_wave_token(wave_id: str, agent_id: str) -> tuple[str, str, str]:
    return RUNTIME_TOKEN_SERVICE.issue_wave_token(wave_id=wave_id, agent_id=agent_id)


def _validate_wave_token(conn: sqlite3.Connection, wave_id: str, wave_token: str, node: str = "token_validation") -> None:
    try:
        RUNTIME_TOKEN_SERVICE.validate_wave_token(
            conn,
            wave_id,
            wave_token,
            log_decision=_log_decision,
            node=node,
        )
    except TokenServiceError as e:
        raise WaveExecutionError(e.code, e.message, e.node)


def _commit_output_write(
    conn: sqlite3.Connection,
    wave_id: str,
    wave_token: str,
    workspace_dir: str,
    final_output_path: str,
    rendered_content: str,
    node: str,
) -> str:
    _validate_wave_token(conn, wave_id, wave_token, node=f"{node}.token")

    if not _is_under("./outputs", final_output_path):
        _log_decision(conn, wave_id, "DENY", "output path outside allowed prefix", "output_path_prefix", node)
        raise WaveExecutionError("PATH_VIOLATION", "Output path outside ./outputs is denied.", node)
    _log_decision(conn, wave_id, "ALLOW", "output path within allowed prefix", "output_path_prefix", node)

    workspace_output = Path(workspace_dir) / Path(final_output_path).name
    workspace_output.parent.mkdir(parents=True, exist_ok=True)
    workspace_output.write_text(rendered_content, encoding="utf-8")
    _log_decision(conn, wave_id, "ALLOW", "workspace write successful", "workspace_write", node)

    Path(final_output_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(workspace_output), final_output_path)
    _log_decision(conn, wave_id, "ALLOW", "final output committed", "commit_output", node)
    return str(workspace_output)


def _is_under(base: str, target: str) -> bool:
    base_path = Path(base).resolve()
    target_path = Path(target).resolve()
    try:
        target_path.relative_to(base_path)
        return True
    except ValueError:
        return False


def _resolve_output_path(context_refs_json: str | None) -> str | None:
    return RUNTIME_WAVE_LIFECYCLE_STORE.resolve_output_path(context_refs_json)


def _normalize_repo_relative(path_text: str) -> str:
    return str(Path(path_text).as_posix().lstrip("./"))



def _insert_wave_row(
    conn: sqlite3.Connection,
    wave_id: str,
    req: WaveRunRequest,
    tenant_id: str,
    status: str,
    workspace_dir: str | None = None,
    wave_token_hash: str | None = None,
    wave_token_expires_at: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    error_node: str | None = None,
    policy_manifest_hash: str | None = None,
    policy_manifest_version: str | None = None,
    policy_manifest_json: str | None = None,
    wave_mutation_token: str | None = None,
    wave_mutation_token_hash: str | None = None,
    wave_mutation_token_expires_at: str | None = None,
    wave_mutation_token_payload_json: str | None = None,
) -> None:
    RUNTIME_WAVE_LIFECYCLE_STORE.insert_wave(
        conn,
        WaveInsertPayload(
            wave_id=wave_id,
            tenant_id=tenant_id,
            agent_id=req.agent_id,
            wave_template_id=req.wave_template_id,
            policy_version=req.policy_version,
            intent=req.intent,
            context_refs=req.context_refs,
            status=status,
            workspace_dir=workspace_dir,
            wave_token_hash=wave_token_hash,
            wave_token_expires_at=wave_token_expires_at,
            error_code=error_code,
            error_message=error_message,
            error_node=error_node,
            policy_manifest_hash=policy_manifest_hash,
            policy_manifest_version=policy_manifest_version,
            policy_manifest_json=policy_manifest_json,
            wave_mutation_token=wave_mutation_token,
            wave_mutation_token_hash=wave_mutation_token_hash,
            wave_mutation_token_expires_at=wave_mutation_token_expires_at,
            wave_mutation_token_payload_json=wave_mutation_token_payload_json,
        ),
    )


def _record_prep_deny(
    conn: sqlite3.Connection,
    wave_id: str,
    req: WaveRunRequest,
    deny: Any,
    tenant_id: str = DEFAULT_TENANT_ID,
    policy_manifest_hash: str | None = None,
    policy_manifest_version: str | None = None,
    policy_manifest_json: str | None = None,
) -> dict[str, Any]:
    code = str(getattr(deny, "code", "WAVE_EXECUTION_ERROR"))
    message = str(getattr(deny, "message", "Wave execution failed."))
    node = str(getattr(deny, "node", "run_wave"))
    rule = str(getattr(deny, "rule", code))
    if policy_manifest_hash is None or policy_manifest_version is None or policy_manifest_json is None:
        snapshot = _load_policy_manifest_snapshot()
        policy_manifest_hash = snapshot["manifest_hash"]
        policy_manifest_version = snapshot["manifest_version"]
        policy_manifest_json = snapshot["manifest_json"]

    _insert_wave_row(
        conn=conn,
        wave_id=wave_id,
        req=req,
        tenant_id=tenant_id,
        status="failed",
        error_code=code,
        error_message=message,
        error_node=node,
        policy_manifest_hash=policy_manifest_hash,
        policy_manifest_version=policy_manifest_version,
        policy_manifest_json=policy_manifest_json,
    )
    _log_decision(conn, wave_id, "DENY", message, rule, node)
    conn.commit()
    return {
        "wave_id": wave_id,
        "tenant_id": tenant_id,
        "status": "failed",
        "error": {"code": code, "message": message, "node": node},
    }


def _persist_runtime_gateway_pending_approval(
    conn: sqlite3.Connection,
    req: RuntimeGatewayRequest,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if str(payload.get("decision") or "").upper() != "PENDING_APPROVAL":
        return payload

    tenant_id = str(req.tenant_id or DEFAULT_TENANT_ID)
    now = _now_iso()
    required_actions = req.approval_rules.get("required_for_actions") if isinstance(req.approval_rules, dict) else None
    if not isinstance(required_actions, list) or not required_actions:
        required_actions = [req.action]

    context_refs = dict(req.context) if isinstance(req.context, dict) else {}
    context_refs.setdefault("wave_type", req.wave_type)
    context_refs.setdefault("system", req.system)
    context_refs.setdefault("action", req.action)
    context_refs.setdefault("wave_template_id", context_refs.get("wave_template_id") or "runtime_gateway")
    context_refs_json = json.dumps(context_refs, sort_keys=True)

    wave_row = conn.execute(
        "SELECT wave_id FROM waves WHERE wave_id = ? LIMIT 1",
        (req.wave_id,),
    ).fetchone()
    if wave_row:
        conn.execute(
            """
            UPDATE waves
            SET status = ?, updated_at = ?, context_refs_json = ?
            WHERE wave_id = ?
            """,
            ("pending_approval", now, context_refs_json, req.wave_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO waves (
                wave_id, agent_id, wave_template_id, policy_version, intent, context_refs_json,
                status, created_at, updated_at, tenant_id,
                error_code, error_message, error_node, policy_manifest_hash, policy_manifest_version, policy_manifest_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.wave_id,
                req.agent_id,
                str(context_refs.get("wave_template_id") or "runtime_gateway"),
                str(req.policy_reference or "runtime_gateway_policy_v1"),
                f"runtime_gateway:{req.system}:{req.action}",
                context_refs_json,
                "pending_approval",
                now,
                now,
                tenant_id,
                None,
                None,
                None,
                req.policy_manifest_hash,
                None,
                None,
            ),
        )

    existing_approval = conn.execute(
        """
        SELECT approval_request_id
        FROM approval_requests
        WHERE wave_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (req.wave_id,),
    ).fetchone()

    approval_request_id = str(existing_approval[0]) if existing_approval and existing_approval[0] else f"apr_{uuid.uuid4().hex[:12]}"
    if not existing_approval:
        note_payload = {
            "tenant_id": tenant_id,
            "system": req.system,
            "action": req.action,
            "required_actions": [str(x) for x in required_actions],
        }
        RUNTIME_WAVE_LIFECYCLE_STORE.create_approval_record(
            conn,
            approval_request_id=approval_request_id,
            wave_id=req.wave_id,
            approved_by=None,
            note=json.dumps(note_payload, sort_keys=True),
            status="pending",
            target_write_path=f"{req.system}:{req.action}",
            proposed_write_hash=_sha256_text(json.dumps(note_payload, sort_keys=True)),
        )

    _log_decision(
        conn,
        req.wave_id,
        "PENDING_APPROVAL",
        str(payload.get("message") or "Action requires approval before execution."),
        str(payload.get("reason_code") or "APPROVAL_REQUIRED"),
        "runtime_gateway.evaluate",
        tenant_id=tenant_id,
    )

    approval_linkage = {
        "approval_id": approval_request_id,
        "approval_request_id": approval_request_id,
        "approval_wave_id": req.wave_id,
        "linked_wave_id": req.wave_id,
    }
    payload["approval_request_id"] = approval_request_id
    payload["approval_status"] = "pending"
    payload["approval_linkage"] = approval_linkage

    artifact = payload.get("artifact")
    if isinstance(artifact, dict):
        artifact["approval_linkage"] = approval_linkage
        artifact_path = artifact.get("artifact_path") or artifact.get("_artifact_path")
        if isinstance(artifact_path, str) and Path(artifact_path).exists():
            try:
                artifact_doc = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
                if isinstance(artifact_doc, dict):
                    artifact_doc["approval_linkage"] = approval_linkage
                    Path(artifact_path).write_text(json.dumps(artifact_doc, sort_keys=True, indent=2), encoding="utf-8")
            except Exception:
                pass

    conn.commit()
    return payload


def _write_manifest(
    conn: sqlite3.Connection,
    wave_id: str,
    workspace_dir: str,
    req: WaveRunRequest,
    output_path: str,
    extra: dict[str, Any],
) -> tuple[str, str]:
    return RUNTIME_WAVE_LIFECYCLE_STORE.write_manifest(
        conn,
        wave_id=wave_id,
        workspace_dir=workspace_dir,
        wave_template_id=req.wave_template_id,
        policy_version=req.policy_version,
        intent=req.intent,
        context_refs=req.context_refs,
        output_path=output_path,
        evidence=extra,
        agent_id=req.agent_id,
    )


@app.post("/api/waves/run")
def run_wave(req: WaveRunRequest, request: Request = None):
    auth = _require_api_key(request)
    if isinstance(auth, JSONResponse):
        return auth
    _, tenant_id = auth
    if not _rate_limit_check(tenant_id, "wave_create", RATE_LIMIT_WAVES_PER_MIN):
        conn = sqlite3.connect(DB_PATH)
        ensure_wave_tables(conn)
        try:
            _log_api_event(
                conn,
                tenant_id=tenant_id,
                event_type="rate_limit",
                reason_code="RATE_LIMIT_EXCEEDED",
                node="api.waves.run",
                status="deny",
            )
            conn.commit()
        finally:
            conn.close()
        return JSONResponse(
            status_code=429,
            content={
                "reason_code": "RATE_LIMIT_EXCEEDED",
                "message": "Tenant wave creation rate limit exceeded.",
            },
        )
    wave_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    workspace_dir = str((RUNS_ROOT / wave_id).resolve())
    try:
        result = RUNTIME_WAVE_APPLICATION_SERVICE.run_wave(
            WaveRunApplicationRequest(
                req=req,
                tenant_id=tenant_id,
                wave_id=wave_id,
                conn=conn,
                workspace_dir=workspace_dir,
                market_intel_templates=MARKET_INTEL_TEMPLATES,
                prod_config_target=PROD_CONFIG_TARGET,
                max_runtime_seconds=MAX_RUNTIME_SECONDS,
            ),
            WaveRunApplicationDeps(
                orchestrator=RUNTIME_WAVE_ORCHESTRATOR,
                build_prep_deps=lambda _conn: WaveRunPreparationDeps(
                    load_policy_snapshot=_load_policy_manifest_snapshot,
                    log_decision=lambda _wave_id, _decision, _reason, _rule, _node, _tenant_id: _log_decision(
                        _conn, _wave_id, _decision, _reason, _rule, _node, tenant_id=_tenant_id
                    ),
                    resolve_connector_type=resolve_connector_type,
                    prepare_wave_context=prepare_wave_context,
                    normalize_repo_relative=_normalize_repo_relative,
                    is_under=_is_under,
                    prepare_connector_context=prepare_connector_context,
                    issue_wave_token=_issue_wave_token,
                    build_mutation_scope=_build_mutation_scope,
                    mint_wave_mutation_token=_mint_wave_mutation_token,
                    insert_wave_row=lambda **kwargs: _insert_wave_row(conn=_conn, **kwargs),
                    mkdir=lambda path: Path(path).mkdir(parents=True, exist_ok=True),
                    commit=_conn.commit,
                ),
                build_handler_deps=lambda _conn: DemoHandlerDeps(
                    project_root=PROJECT_ROOT,
                    ocean_proxy_http=lambda proxy_req: _ocean_proxy_http_core(_conn, proxy_req),
                    commit_output_write=lambda **kwargs: _commit_output_write(conn=_conn, **kwargs),
                    log_decision=lambda _wave_id, _decision, _reason, _rule, _node: _log_decision(
                        _conn, _wave_id, _decision, _reason, _rule, _node
                    ),
                    dispatch_connector_action=lambda **kwargs: dispatch_connector_action(
                        **kwargs,
                        proxy_executor=lambda proxy_req: _ocean_proxy_http_core(_conn, proxy_req),
                    ),
                    sha256_text=_sha256_text,
                    sha256_file=_sha256_file,
                    anthropic_module=anthropic,
                ),
                dispatch_template_handler=dispatch_template_handler,
                write_manifest=lambda _conn, _wave_id, _workspace_dir, _req, _output_path, _evidence: _write_manifest(
                    _conn, _wave_id, _workspace_dir, _req, _output_path, _evidence
                ),
                update_wave_status=lambda _conn, _wave_id, _status, _error_code, _error_message, _error_node: RUNTIME_WAVE_LIFECYCLE_STORE.update_wave_status(
                    _conn,
                    wave_id=_wave_id,
                    status=_status,
                    error_code=_error_code,
                    error_message=_error_message,
                    error_node=_error_node,
                ),
                log_decision=lambda _conn, _wave_id, _decision, _reason, _rule, _node: _log_decision(
                    _conn, _wave_id, _decision, _reason, _rule, _node
                ),
                sha256_file=_sha256_file,
                record_prep_deny=lambda _conn, _wave_id, _req, _deny, _tenant_id, _snapshot: _record_prep_deny(
                    conn=_conn,
                    wave_id=_wave_id,
                    req=_req,
                    deny=_deny,
                    tenant_id=_tenant_id,
                    policy_manifest_hash=_snapshot["manifest_hash"],
                    policy_manifest_version=_snapshot["manifest_version"],
                    policy_manifest_json=_snapshot["manifest_json"],
                ),
                load_policy_snapshot=_load_policy_manifest_snapshot,
                monotonic=time.monotonic,
                wave_execution_error_type=WaveExecutionError,
            ),
        )
        if result.http_status is not None and result.http_status != 200:
            return JSONResponse(status_code=result.http_status, content=result.payload)
        return result.payload
    finally:
        conn.close()


@app.post("/api/runtime/execution-gateway/evaluate")
def evaluate_runtime_execution(req: RuntimeGatewayRequest):
    try:
        out = RUNTIME_WAVE_ORCHESTRATOR.orchestrate_runtime_gateway(
            RuntimeGatewayOrchestratorRequest(
                wave_id=req.wave_id,
                wave_type=req.wave_type,
                system=req.system,
                action=req.action,
                risk_level=req.risk_level,
                approval_required=req.approval_required,
                required_execution_sequence=list(req.required_execution_sequence),
                approval_rules=dict(req.approval_rules),
                execution_timeout=req.execution_timeout,
                trigger_type=req.trigger_type,
                context=dict(req.context),
                agent_id=req.agent_id,
                tenant_id=req.tenant_id,
                orchestrator_id=req.orchestrator_id,
                token_scope=list(req.token_scope),
                pinned_policy_manifest=list(req.pinned_policy_manifest),
                runtime_rules=list(req.runtime_rules),
                policy_manifest_hash=req.policy_manifest_hash,
                policy_reference=req.policy_reference,
                approval_linkage=req.approval_linkage,
                execution_path_evidence=req.execution_path_evidence,
            ),
            wave_service=RUNTIME_WAVE_SERVICE,
            artifact_service_factory=lambda root: ArtifactService(FileArtifactStore(root)),
            gateway_factory=lambda artifact_service: ExecutionGateway(
                policy_engine=RUNTIME_POLICY_ENGINE,
                token_validation=RUNTIME_TOKEN_VALIDATION,
                artifact_service=artifact_service,
            ),
        )
    except ValueError as e:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "INVALID_WAVE_SCHEMA", "message": str(e)}},
        )
    payload = out.payload
    if not isinstance(payload, dict):
        return payload

    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        return _persist_runtime_gateway_pending_approval(conn, req, payload)
    finally:
        conn.close()


@app.get("/api/runtime/artifacts/{artifact_id}")
def get_runtime_artifact(artifact_id: str):
    artifact = RUNTIME_ARTIFACT_RETRIEVAL.get(artifact_id)
    if artifact is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "ARTIFACT_NOT_FOUND", "message": "No artifact found for artifact_id."}},
        )
    return {
        "artifact_id": artifact.get("artifact_id"),
        "schema_version": artifact.get("schema_version"),
        "tenant_id": artifact.get("tenant_id"),
        "wave_id": artifact.get("wave_id"),
        "system": artifact.get("system"),
        "action": artifact.get("action"),
        "decision": artifact.get("decision"),
        "reason_code": artifact.get("reason_code"),
        "timestamp": artifact.get("timestamp"),
        "timestamps": artifact.get("timestamps"),
        "policy_reference": artifact.get("policy_reference"),
        "policy_manifest_hash": artifact.get("policy_manifest_hash"),
        "approval_linkage": artifact.get("approval_linkage"),
        "execution_path_evidence": artifact.get("execution_path_evidence"),
        "artifact_path": artifact.get("_artifact_path"),
    }


@app.get("/api/runtime/artifacts")
def list_runtime_artifacts(tenant_id: str | None = None, limit: int = 25):
    return {
        "tenant_id": tenant_id,
        "count": max(0, min(int(limit), 200)),
        "artifacts": RUNTIME_ARTIFACT_RETRIEVAL.list_recent(tenant_id=tenant_id, limit=max(1, min(int(limit), 200))),
    }


@app.get("/api/runtime/waves/recent")
def list_recent_runtime_waves(
    tenant_id: str = Query(..., description="Tenant scope for recent wave timeline."),
    limit: int = 20,
):
    normalized_limit = max(1, min(int(limit), 100))
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        waves = RUNTIME_WAVE_READ_SERVICE.list_recent_waves(
            conn,
            tenant_id=tenant_id,
            limit=normalized_limit,
        )
    finally:
        conn.close()
    return {
        "tenant_id": tenant_id,
        "limit": normalized_limit,
        "count": len(waves),
        "waves": waves,
    }


@app.get("/api/runtime/waves/{wave_id}/decisions")
def get_runtime_wave_decisions(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        payload = RUNTIME_WAVE_READ_SERVICE.get_wave_decisions(conn, wave_id=wave_id)
    finally:
        conn.close()
    if payload is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "WAVE_NOT_FOUND", "message": "No wave found for provided wave_id."}},
        )
    return payload


@app.get("/api/runtime/approvals/recent")
def list_recent_runtime_approvals(
    tenant_id: str = Query(..., description="Tenant scope for approvals queue."),
    limit: int = 20,
):
    normalized_limit = max(1, min(int(limit), 100))
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        approvals = RUNTIME_WAVE_READ_SERVICE.list_recent_approvals(
            conn,
            tenant_id=tenant_id,
            limit=normalized_limit,
        )
    finally:
        conn.close()
    return {
        "tenant_id": tenant_id,
        "limit": normalized_limit,
        "count": len(approvals),
        "approvals": approvals,
    }


@app.get("/api/waves/{wave_id}/status")
def wave_status(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    wave = RUNTIME_WAVE_LIFECYCLE_STORE.fetch_wave_status_row(conn, wave_id)

    conn.close()

    if not wave:
        return {
            "wave_id": wave_id,
            "status": "failed",
            "approval_request_id": None,
            "summary": {"output_path": None},
            "error": {
                "code": "WAVE_NOT_FOUND",
                "message": "No wave found for provided wave_id",
                "node": "wave_status",
            },
        }

    output_path = _resolve_output_path(wave[5])

    payload = {
        "wave_id": wave[0],
        "status": wave[1],
        "approval_request_id": None,
        "summary": {
            "output_path": output_path,
            "wave_mutation_token_expires_at": wave[6],
            "policy_manifest_hash_prefix": (wave[7] or "")[:12] if wave[7] else None,
        },
    }

    if wave[1] == "failed":
        payload["error"] = {
            "code": wave[2] or "WAVE_FAILED",
            "message": wave[3] or "Wave failed",
            "node": wave[4] or "wave_status",
        }

    return payload


@app.post("/api/approvals/{approval_request_id}")
def approve_wave(approval_request_id: str, req: ApprovalRequest):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    wave_id = RUNTIME_WAVE_LIFECYCLE_STORE.fetch_approval_wave_id(conn, approval_request_id)
    if not wave_id:
        wave_id_prefix = approval_request_id.replace("apr_", "")
        matches = RUNTIME_WAVE_LIFECYCLE_STORE.find_wave_ids_by_prefix(conn, wave_id_prefix)
        if len(matches) == 0:
            conn.close()
            return {
                "wave_id": None,
                "status": "failed",
                "approval_request_id": approval_request_id,
                "error": {
                    "code": "WAVE_NOT_FOUND",
                    "message": "No matching wave for approval_request_id prefix",
                    "node": "approve_wave",
                },
            }
        if len(matches) > 1:
            conn.close()
            return {
                "wave_id": None,
                "status": "failed",
                "approval_request_id": approval_request_id,
                "error": {
                    "code": "AMBIGUOUS_WAVE_PREFIX",
                    "message": "approval_request_id prefix maps to multiple waves",
                    "node": "approve_wave",
                },
            }

        wave_id = matches[0]
        RUNTIME_WAVE_LIFECYCLE_STORE.create_approval_record(
            conn,
            approval_request_id=approval_request_id,
            wave_id=wave_id,
            approved_by=req.approved_by,
            note=req.note,
        )
    else:
        RUNTIME_WAVE_LIFECYCLE_STORE.update_approval_record(
            conn,
            approval_request_id=approval_request_id,
            approved_by=req.approved_by,
            note=req.note,
        )

    RUNTIME_WAVE_LIFECYCLE_STORE.mark_wave_complete_if_running(conn, wave_id)

    conn.commit()
    conn.close()

    return {
        "wave_id": wave_id,
        "status": "complete",
        "approval_request_id": approval_request_id,
        "approved_by": req.approved_by,
        "note": req.note,
    }


def _ocean_proxy_http_core(
    conn: sqlite3.Connection, req: dict[str, Any], api_tenant_id: str | None = None
) -> tuple[int, dict[str, Any]]:
    return RUNTIME_MUTATION_BOUNDARY.proxy_http(
        conn,
        req,
        log_decision=_log_decision,
        api_tenant_id=api_tenant_id,
    )


@app.post("/ocean/proxy/http")
def ocean_proxy_http(req: OceanProxyHttpRequest, request: Request = None):
    auth = _require_api_key(request)
    if isinstance(auth, JSONResponse):
        return auth
    _, tenant_id = auth
    if not _rate_limit_check(tenant_id, "proxy_request", RATE_LIMIT_PROXY_PER_MIN):
        conn = sqlite3.connect(DB_PATH)
        ensure_wave_tables(conn)
        try:
            _log_api_event(
                conn,
                tenant_id=tenant_id,
                event_type="rate_limit",
                reason_code="RATE_LIMIT_EXCEEDED",
                node="ocean.proxy.http",
                status="deny",
            )
            conn.commit()
        finally:
            conn.close()
        return JSONResponse(
            status_code=429,
            content={"reason_code": "RATE_LIMIT_EXCEEDED", "message": "Tenant proxy rate limit exceeded."},
        )
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        status_code, payload = _ocean_proxy_http_core(
            conn,
            {
                "method": req.method,
                "url": req.url,
                "headers": req.headers,
                "json_body": req.json_body,
                "body": req.body,
                "wave_mutation_token": req.wave_mutation_token,
                "governance_context": req.governance_context,
            },
            api_tenant_id=tenant_id,
        )
        return JSONResponse(status_code=status_code, content=payload)
    finally:
        conn.close()


@app.post("/ocean/mutate_config")
def ocean_mutate_config(req: ConfigMutateRequest):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        return ocean_mutate_config_core(
            conn=conn,
            req={
                "wave_id": req.wave_id,
                "wave_token": req.wave_token,
                "agent_name": req.agent_name,
                "policy_version": req.policy_version,
                "target_path": req.target_path,
                "mutations": [
                    {"json_path": m.json_path, "value": m.value}
                    for m in req.mutations
                ],
                "reason": req.reason,
            },
            project_root=PROJECT_ROOT,
            prod_config_target=PROD_CONFIG_TARGET,
            prod_config_allowed_keys=PROD_CONFIG_ALLOWED_KEYS,
            log_decision=_log_decision,
            now_iso=_now_iso,
            sha256_text=_sha256_text,
            token_secret=SURFIT_TOKEN_SECRET,
        )
    finally:
        conn.close()


@app.get("/api/waves/{wave_id}/policy_manifest")
def get_policy_manifest(wave_id: str, request: Request = None):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    auth = _authorize_wave_tenant(conn, wave_id, request)
    if isinstance(auth, JSONResponse):
        conn.close()
        return auth
    row = conn.execute(
        """
        SELECT policy_manifest_hash, policy_manifest_version, policy_manifest_json
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()
    conn.close()

    if not row:
        return {"wave_id": wave_id, "status": "not_found"}

    policy_manifest_hash, policy_manifest_version, policy_manifest_json = row
    manifest_payload = None
    try:
        manifest_payload = json.loads(policy_manifest_json) if policy_manifest_json else None
    except Exception:
        manifest_payload = None

    return {
        "wave_id": wave_id,
        "policy_manifest_hash": policy_manifest_hash,
        "policy_manifest_version": policy_manifest_version,
        "policy_manifest": manifest_payload,
    }


@app.get("/api/waves/{wave_id}/token")
def get_wave_mutation_token(wave_id: str, request: Request = None):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    auth = _authorize_wave_tenant(conn, wave_id, request)
    if isinstance(auth, JSONResponse):
        conn.close()
        return auth
    row = conn.execute(
        """
        SELECT wave_mutation_token, wave_mutation_token_expires_at, policy_manifest_hash, tenant_id
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()
    conn.close()

    if not row:
        return JSONResponse(status_code=404, content={"wave_id": wave_id, "status": "not_found"})

    return {
        "wave_id": wave_id,
        "wave_mutation_token": row[0],
        "wave_mutation_token_expires_at": row[1],
        "policy_manifest_hash_prefix": (row[2] or "")[:12] if row[2] else None,
        "tenant_id": row[3],
    }


@app.get("/api/waves/{wave_id}/export")
def export_wave_bundle(wave_id: str, request: Request = None):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    auth = _authorize_wave_tenant(conn, wave_id, request)
    if isinstance(auth, JSONResponse):
        conn.close()
        return auth
    _, tenant_id = auth
    if not _rate_limit_check(tenant_id, "export_bundle", RATE_LIMIT_EXPORT_PER_MIN):
        _log_api_event(
            conn,
            tenant_id=tenant_id,
            wave_id=wave_id,
            event_type="rate_limit",
            reason_code="RATE_LIMIT_EXCEEDED",
            node="api.waves.export",
            status="deny",
        )
        conn.commit()
        conn.close()
        return JSONResponse(
            status_code=429,
            content={"reason_code": "RATE_LIMIT_EXCEEDED", "message": "Tenant export rate limit exceeded."},
        )
    wave = conn.execute(
        """
        SELECT wave_id, tenant_id, agent_id, wave_template_id, policy_version, intent, status, created_at, updated_at,
               manifest_hash, manifest_path, policy_manifest_hash, policy_manifest_version, policy_manifest_json
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()

    if not wave:
        _log_api_event(conn, tenant_id=tenant_id, wave_id=wave_id, event_type="export_bundle", status="not_found")
        conn.commit()
        conn.close()
        return JSONResponse(status_code=404, content={"wave_id": wave_id, "status": "not_found"})

    decisions = _fetch_decisions(conn, wave_id)
    decision_chain = _verify_decision_chain(conn, wave_id)
    policy_manifest_check = _verify_policy_manifest(wave[11], wave[13])
    policy_manifest_payload = policy_manifest_check.get("policy_manifest_payload")

    manifest_valid = False
    recomputed_manifest_hash = None
    execution_evidence = None
    if wave[10] and Path(wave[10]).exists():
        manifest_text = Path(wave[10]).read_text(encoding="utf-8")
        recomputed_manifest_hash = _sha256_text(manifest_text)
        manifest_valid = recomputed_manifest_hash == wave[9]
        try:
            manifest_payload = json.loads(manifest_text)
            if isinstance(manifest_payload, dict):
                maybe_evidence = manifest_payload.get("evidence")
                if isinstance(maybe_evidence, dict):
                    execution_evidence = maybe_evidence
        except Exception:
            execution_evidence = None

    integrity = {
        "manifest_hash": {
            "stored": wave[9],
            "recomputed": recomputed_manifest_hash,
            "valid": manifest_valid,
            "manifest_path": wave[10],
        },
        "decision_chain": decision_chain,
        "policy_manifest": {
            "hash": wave[11],
            "version": wave[12],
            "recomputed_hash": policy_manifest_check.get("recomputed_policy_manifest_hash"),
            "valid": bool(policy_manifest_check.get("valid")),
            "reason": policy_manifest_check.get("reason"),
        },
    }

    _log_api_event(conn, tenant_id=tenant_id, wave_id=wave_id, event_type="export_bundle", status="success")
    conn.commit()
    conn.close()

    return {
        "bundle_version": "surfit_wave_bundle_v1",
        "wave": {
            "wave_id": wave[0],
            "tenant_id": wave[1],
            "agent_id": wave[2],
            "agent_name": wave[2],
            "wave_template_id": wave[3],
            "policy_version": wave[4],
            "intent": wave[5],
            "status": wave[6],
            "created_at": wave[7],
            "updated_at": wave[8],
        },
        "policy_manifest": {
            "hash": wave[11],
            "version": wave[12],
            "manifest": policy_manifest_payload,
        },
        "decision_chain": decisions,
        "execution_evidence": execution_evidence,
        "integrity": integrity,
    }


@app.get("/api/waves/{wave_id}/audit/export")
def export_audit(wave_id: str):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)

    wave = conn.execute(
        """
        SELECT wave_id, policy_version, status, agent_id, context_refs_json, error_code, error_message, error_node,
               manifest_hash, manifest_path, workspace_dir, policy_manifest_hash, policy_manifest_version
        FROM waves
        WHERE wave_id = ?
        """,
        (wave_id,),
    ).fetchone()

    approval = conn.execute(
        """
        SELECT approved_by, approved_at, note, proposed_write_hash
        FROM approval_requests
        WHERE wave_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (wave_id,),
    ).fetchone()

    decisions = _fetch_decisions(conn, wave_id)
    conn.close()

    if not wave:
        return {
            "wave_id": wave_id,
            "integrity_status": "INVALID",
            "policy_hash": None,
            "agent_id": None,
            "output_path": None,
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "note": None,
                "proposed_write_hash": None,
            },
            "events": [],
            "llm_invocations": [],
        }

    output_path = _resolve_output_path(wave[4])
    integrity_status = "VALID" if wave[2] == "complete" else "INVALID"

    payload = {
        "wave_id": wave[0],
        "integrity_status": integrity_status,
        "policy_hash": wave[1],  # placeholder mapping for POC; replace with real hash column in full runtime API
        "agent_id": wave[3],
        "output_path": output_path,
        "approval": {
            "approved_by": approval[0] if approval else None,
            "approved_at": approval[1] if approval else None,
            "note": approval[2] if approval else None,
            "proposed_write_hash": approval[3] if approval else None,
        },
        "workspace_dir": wave[10],
        "manifest_hash": wave[8],
        "manifest_path": wave[9],
        "policy_manifest_hash": wave[11],
        "policy_manifest_version": wave[12],
        "events": decisions,
        "llm_invocations": [
            {
                "provider": "anthropic",
                "model_name": "claude",
                "model_version": "placeholder",
            }
        ],
    }

    if wave[2] == "failed":
        payload["error"] = {
            "code": wave[5] or "WAVE_FAILED",
            "message": wave[6] or "Wave failed",
            "node": wave[7] or "export_audit",
        }

    return payload


@app.get("/api/waves/{wave_id}/audit/verify")
def verify_audit(wave_id: str, request: Request = None):
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    auth = _authorize_wave_tenant(conn, wave_id, request)
    if isinstance(auth, JSONResponse):
        conn.close()
        return auth
    _, tenant_id = auth
    row = conn.execute(
        "SELECT manifest_hash, manifest_path, status, policy_manifest_hash, policy_manifest_version, policy_manifest_json FROM waves WHERE wave_id = ?",
        (wave_id,),
    ).fetchone()

    if not row:
        _log_api_event(conn, tenant_id=tenant_id, wave_id=wave_id, event_type="audit_verify", status="not_found")
        conn.commit()
        conn.close()
        return {
            "wave_id": wave_id,
            "integrity_status": "CORRUPTED",
            "details": "Wave not found.",
        }

    stored_hash, manifest_path, status, policy_manifest_hash, policy_manifest_version, policy_manifest_json = row
    if not manifest_path or not Path(manifest_path).exists():
        _log_api_event(conn, tenant_id=tenant_id, wave_id=wave_id, event_type="audit_verify", status="fail")
        conn.commit()
        conn.close()
        return {
            "wave_id": wave_id,
            "integrity_status": "CORRUPTED",
            "details": "Manifest file missing.",
        }

    manifest_text = Path(manifest_path).read_text(encoding="utf-8")
    recomputed = _sha256_text(manifest_text)
    manifest_ok = stored_hash == recomputed

    policy_manifest_ok = False
    recomputed_policy_manifest_hash = None
    if policy_manifest_hash and policy_manifest_json:
        try:
            parsed_policy_manifest = json.loads(policy_manifest_json)
            canonical_policy_manifest = _canonicalize_policy_manifest(parsed_policy_manifest)
            recomputed_policy_manifest_hash = _sha256_text(canonical_policy_manifest)
            policy_manifest_ok = recomputed_policy_manifest_hash == policy_manifest_hash
        except Exception:
            policy_manifest_ok = False

    decision_chain = _verify_decision_chain(conn, wave_id)
    chain_ok = bool(decision_chain.get("valid"))
    ok = manifest_ok and chain_ok and policy_manifest_ok

    out = {
        "wave_id": wave_id,
        "integrity_status": "VALID" if ok and status == "complete" else "CORRUPTED",
        "details": {
            "stored_manifest_hash": stored_hash,
            "recomputed_manifest_hash": recomputed,
            "manifest_path": manifest_path,
            "status": status,
            "manifest_valid": manifest_ok,
            "policy_manifest_hash": policy_manifest_hash,
            "policy_manifest_version": policy_manifest_version,
            "recomputed_policy_manifest_hash": recomputed_policy_manifest_hash,
            "policy_manifest_valid": policy_manifest_ok,
            "decision_chain": decision_chain,
        },
    }
    _log_api_event(conn, tenant_id=tenant_id, wave_id=wave_id, event_type="audit_verify", status="pass" if out["integrity_status"] == "VALID" else "fail")
    conn.commit()
    conn.close()
    return out


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "surfit-api",
        "environment": SURFIT_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/readyz")
def readyz() -> JSONResponse:
    db_status = _check_db_readiness()
    redis_status = _check_redis_readiness()
    policy_path_ok = POLICY_ALLOWLISTS_PATH.exists()

    checks = {
        "database": db_status,
        "redis": redis_status,
        "policy_manifest_path": {
            "ready": policy_path_ok,
            "detail": str(POLICY_ALLOWLISTS_PATH),
        },
    }
    all_ready = all(bool(item.get("ready")) for item in checks.values())
    status_code = 200 if all_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ready else "not_ready",
            "service": "surfit-api",
            "environment": SURFIT_ENV,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/api/metrics/summary")
def metrics_summary(
    request: Request,
    since_hours: int = 24,
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    top_n: int = 5,
):
    auth = _require_api_key(request)
    if isinstance(auth, JSONResponse):
        return auth
    _, tenant_id = auth
    start_iso, end_iso = _resolve_time_window(since_hours=since_hours, from_ts=from_ts, to_ts=to_ts)

    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        total_waves = conn.execute(
            "SELECT COUNT(*) FROM waves WHERE tenant_id = ? AND created_at BETWEEN ? AND ?",
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
        total_decisions = conn.execute(
            "SELECT COUNT(*) FROM wave_decisions WHERE tenant_id = ? AND created_at BETWEEN ? AND ?",
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
        allow_count = conn.execute(
            "SELECT COUNT(*) FROM wave_decisions WHERE tenant_id = ? AND decision = 'ALLOW' AND created_at BETWEEN ? AND ?",
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
        deny_count = conn.execute(
            "SELECT COUNT(*) FROM wave_decisions WHERE tenant_id = ? AND decision = 'DENY' AND created_at BETWEEN ? AND ?",
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]

        deny_rows = conn.execute(
            """
            SELECT rule, COUNT(*) AS n
            FROM wave_decisions
            WHERE tenant_id = ? AND decision = 'DENY' AND created_at BETWEEN ? AND ?
            GROUP BY rule
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchall()
        event_deny_rows = conn.execute(
            """
            SELECT reason_code, COUNT(*) AS n
            FROM api_events
            WHERE tenant_id = ? AND status = 'deny' AND created_at BETWEEN ? AND ?
            GROUP BY reason_code
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchall()
        deny_map: dict[str, int] = {}
        for code, n in deny_rows:
            k = str(code or "UNKNOWN")
            deny_map[k] = deny_map.get(k, 0) + int(n or 0)
        for code, n in event_deny_rows:
            k = str(code or "UNKNOWN")
            deny_map[k] = deny_map.get(k, 0) + int(n or 0)
        deny_by_reason_code = [
            {"reason_code": k, "count": v}
            for k, v in sorted(deny_map.items(), key=lambda item: item[1], reverse=True)[: max(1, int(top_n))]
        ]

        proxy_calls_total = conn.execute(
            """
            SELECT COUNT(*)
            FROM wave_decisions
            WHERE tenant_id = ? AND node = 'ocean.proxy.http' AND created_at BETWEEN ? AND ?
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
        proxy_rate_limited = conn.execute(
            """
            SELECT COUNT(*)
            FROM api_events
            WHERE tenant_id = ? AND node = 'ocean.proxy.http' AND reason_code = 'RATE_LIMIT_EXCEEDED'
              AND created_at BETWEEN ? AND ?
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
        proxy_calls_total = int(proxy_calls_total or 0) + int(proxy_rate_limited or 0)

        audit_rows = conn.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) AS pass_count,
                COUNT(*) AS total_count
            FROM api_events
            WHERE tenant_id = ? AND event_type = 'audit_verify' AND created_at BETWEEN ? AND ?
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchone()
        pass_count = int(audit_rows[0] or 0)
        audit_total = int(audit_rows[1] or 0)
        audit_verify_pass_rate = (pass_count / audit_total) if audit_total else None

        export_bundle_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM api_events
            WHERE tenant_id = ? AND event_type = 'export_bundle' AND status = 'success' AND created_at BETWEEN ? AND ?
            """,
            (tenant_id, start_iso, end_iso),
        ).fetchone()[0]
    finally:
        conn.close()

    return {
        "tenant_id": tenant_id,
        "window": {"from": start_iso, "to": end_iso, "since_hours": since_hours},
        "total_waves": total_waves,
        "total_decisions": total_decisions,
        "allow_count": allow_count,
        "deny_count": deny_count,
        "deny_by_reason_code": deny_by_reason_code,
        "proxy_calls_total": proxy_calls_total,
        "audit_verify_pass_rate": audit_verify_pass_rate,
        "export_bundle_count": export_bundle_count,
    }


@app.get("/api/metrics/waves")
def metrics_waves(
    request: Request,
    since_hours: int = 24,
    from_ts: str | None = Query(default=None, alias="from"),
    to_ts: str | None = Query(default=None, alias="to"),
    limit: int = 25,
):
    auth = _require_api_key(request)
    if isinstance(auth, JSONResponse):
        return auth
    _, tenant_id = auth
    start_iso, end_iso = _resolve_time_window(since_hours=since_hours, from_ts=from_ts, to_ts=to_ts)

    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        wave_rows = conn.execute(
            """
            SELECT wave_id, created_at, updated_at, status, policy_manifest_hash
            FROM waves
            WHERE tenant_id = ? AND created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (tenant_id, start_iso, end_iso, max(1, int(limit))),
        ).fetchall()
        waves_out: list[dict[str, Any]] = []
        for wave_id, created_at, updated_at, status, policy_manifest_hash in wave_rows:
            counts_row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN decision = 'ALLOW' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN decision = 'DENY' THEN 1 ELSE 0 END)
                FROM wave_decisions
                WHERE tenant_id = ? AND wave_id = ?
                """,
                (tenant_id, wave_id),
            ).fetchone()
            allow_count = int((counts_row[0] if counts_row else 0) or 0)
            deny_count = int((counts_row[1] if counts_row else 0) or 0)
            deny_reasons = conn.execute(
                """
                SELECT rule, COUNT(*) AS n
                FROM wave_decisions
                WHERE tenant_id = ? AND wave_id = ? AND decision = 'DENY'
                GROUP BY rule
                ORDER BY n DESC
                LIMIT 3
                """,
                (tenant_id, wave_id),
            ).fetchall()
            waves_out.append(
                {
                    "wave_id": wave_id,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "status": status,
                    "allow_count": allow_count,
                    "deny_count": deny_count,
                    "top_deny_reasons": [{"reason_code": r[0], "count": r[1]} for r in deny_reasons],
                    "policy_manifest_hash_prefix": (policy_manifest_hash or "")[:12] if policy_manifest_hash else None,
                }
            )
    finally:
        conn.close()

    return {
        "tenant_id": tenant_id,
        "window": {"from": start_iso, "to": end_iso, "since_hours": since_hours},
        "waves": waves_out,
    }

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("SURFIT_API_HOST", "127.0.0.1")
    port = int(os.environ.get("SURFIT_API_PORT", "8010"))
    uvicorn.run("api:app", host=host, port=port, reload=False)


def _resolve_tenant_dashboard_identity(
    request: Request,
    access_key: str | None,
):
    header_token = (request.headers.get("X-Surfit-Tenant-Access") or "").strip()
    query_token = (access_key or "").strip()
    token = header_token or query_token
    if not token:
        raise HTTPException(status_code=401, detail={"code": "TENANT_DASHBOARD_ACCESS_REQUIRED", "message": "Missing dashboard access key."})

    identity, reason = TENANT_DASHBOARD_ACCESS_SERVICE.resolve_identity_with_reason(token)
    if identity is None:
        if reason == "EXPIRED":
            raise HTTPException(
                status_code=403,
                detail={"code": "TENANT_DASHBOARD_ACCESS_EXPIRED", "message": "Dashboard access key has expired."},
            )
        raise HTTPException(
            status_code=403,
            detail={"code": "TENANT_DASHBOARD_ACCESS_INVALID", "message": "Invalid dashboard access key."},
        )
    return identity


@app.get("/api/tenant/dashboard/context")
def get_tenant_dashboard_context(
    request: Request,
    access_key: str | None = Query(default=None, description="Tenant dashboard access key."),
):
    identity = _resolve_tenant_dashboard_identity(request, access_key)
    return {
        "tenant_id": identity.tenant_id,
        "display_name": identity.display_name,
        "logo_url": identity.logo_url,
        "theme": identity.theme,
        "key_created_at": identity.key_created_at,
        "key_expires_at": identity.key_expires_at,
        "key_rotated_at": identity.key_rotated_at,
    }


@app.get("/api/tenant/dashboard/waves/recent")
def list_tenant_dashboard_recent_waves(
    request: Request,
    access_key: str | None = Query(default=None, description="Tenant dashboard access key."),
    limit: int = 20,
):
    identity = _resolve_tenant_dashboard_identity(request, access_key)
    normalized_limit = max(1, min(int(limit), 100))
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        waves = RUNTIME_WAVE_READ_SERVICE.list_recent_waves(
            conn,
            tenant_id=identity.tenant_id,
            limit=normalized_limit,
        )
    finally:
        conn.close()

    return {
        "tenant_id": identity.tenant_id,
        "display_name": identity.display_name,
        "logo_url": identity.logo_url,
        "theme": identity.theme,
        "limit": normalized_limit,
        "count": len(waves),
        "waves": waves,
    }


@app.get("/api/tenant/dashboard/waves/{wave_id}/decisions")
def get_tenant_dashboard_wave_decisions(
    wave_id: str,
    request: Request,
    access_key: str | None = Query(default=None, description="Tenant dashboard access key."),
):
    identity = _resolve_tenant_dashboard_identity(request, access_key)
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        payload = RUNTIME_WAVE_READ_SERVICE.get_wave_decisions(conn, wave_id=wave_id)
    finally:
        conn.close()

    if payload is None or str(payload.get("tenant_id") or "") != identity.tenant_id:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "WAVE_NOT_FOUND", "message": "No tenant-visible wave found for provided wave_id."}},
        )
    return payload


@app.get("/api/tenant/dashboard/approvals/recent")
def list_tenant_dashboard_recent_approvals(
    request: Request,
    access_key: str | None = Query(default=None, description="Tenant dashboard access key."),
    limit: int = 20,
):
    identity = _resolve_tenant_dashboard_identity(request, access_key)
    normalized_limit = max(1, min(int(limit), 100))
    conn = sqlite3.connect(DB_PATH)
    ensure_wave_tables(conn)
    try:
        approvals = RUNTIME_WAVE_READ_SERVICE.list_recent_approvals(
            conn,
            tenant_id=identity.tenant_id,
            limit=normalized_limit,
        )
    finally:
        conn.close()

    return {
        "tenant_id": identity.tenant_id,
        "display_name": identity.display_name,
        "logo_url": identity.logo_url,
        "theme": identity.theme,
        "limit": normalized_limit,
        "count": len(approvals),
        "approvals": approvals,
    }


@app.get("/api/tenant/dashboard/artifacts/{artifact_id}")
def get_tenant_dashboard_artifact(
    artifact_id: str,
    request: Request,
    access_key: str | None = Query(default=None, description="Tenant dashboard access key."),
):
    identity = _resolve_tenant_dashboard_identity(request, access_key)
    artifact = RUNTIME_ARTIFACT_RETRIEVAL.get(artifact_id)
    if artifact is None or str(artifact.get("tenant_id") or "") != identity.tenant_id:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "ARTIFACT_NOT_FOUND", "message": "No tenant-visible artifact found for artifact_id."}},
        )

    return {
        "artifact_id": artifact.get("artifact_id"),
        "schema_version": artifact.get("schema_version"),
        "tenant_id": artifact.get("tenant_id"),
        "wave_id": artifact.get("wave_id"),
        "system": artifact.get("system"),
        "action": artifact.get("action"),
        "decision": artifact.get("decision"),
        "reason_code": artifact.get("reason_code"),
        "timestamp": artifact.get("timestamp"),
        "timestamps": artifact.get("timestamps"),
        "policy_reference": artifact.get("policy_reference"),
        "policy_manifest_hash": artifact.get("policy_manifest_hash"),
        "approval_linkage": artifact.get("approval_linkage"),
        "execution_path_evidence": artifact.get("execution_path_evidence"),
        "artifact_path": artifact.get("_artifact_path"),
    }
