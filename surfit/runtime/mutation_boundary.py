from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import base64
import fnmatch
import hashlib
import hmac
import ipaddress
import json
import socket
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable


@dataclass(frozen=True)
class MutationBoundaryConfig:
    token_secret: str
    mutation_token_ttl_seconds: int = 600
    demo_safe_mode: bool = True
    proxy_timeout_seconds: int = 5
    proxy_max_response_bytes: int = 1_048_576
    token_replay_max_uses: int = 1000
    token_replay_grace_seconds: int = 60
    market_intel_templates: set[str] = field(default_factory=set)
    prod_config_target: str = "demo_artifacts/prod_config.json"
    prod_config_allowed_keys: set[str] = field(default_factory=set)


class MutationBoundaryService:
    def __init__(
        self,
        config: MutationBoundaryConfig,
        *,
        resolve_connector_type: Callable[[str], str | None],
        canonicalize_policy_manifest: Callable[[dict[str, Any]], str],
        sha256_text: Callable[[str], str] | None = None,
    ):
        self.config = config
        self.resolve_connector_type = resolve_connector_type
        self.canonicalize_policy_manifest = canonicalize_policy_manifest
        self.sha256_text = sha256_text or (lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest())
        self._token_replay_lock = threading.Lock()
        self._token_replay_state: dict[str, dict[str, int]] = {}

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        pad = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode((data + pad).encode("utf-8"))

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def decode_wave_mutation_token(self, token: str) -> tuple[dict[str, Any] | None, str | None]:
        try:
            parts = token.split(".")
            if len(parts) != 3 or parts[0] != "swt1":
                return None, "TOKEN_INVALID_SIGNATURE"
            payload_b64, sig_b64 = parts[1], parts[2]
            expected = hmac.new(
                self.config.token_secret.encode("utf-8"),
                payload_b64.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            found = self._b64url_decode(sig_b64)
            if not hmac.compare_digest(expected, found):
                return None, "TOKEN_INVALID_SIGNATURE"
            payload = json.loads(self._b64url_decode(payload_b64).decode("utf-8"))
            if not isinstance(payload, dict):
                return None, "TOKEN_INVALID_SIGNATURE"
            return payload, None
        except Exception:
            return None, "TOKEN_INVALID_SIGNATURE"

    def build_mutation_scope(
        self,
        wave_template_id: str,
        context_refs: dict[str, Any],
        policy_manifest_payload: dict[str, Any],
    ) -> dict[str, Any]:
        http_allow = policy_manifest_payload.get("http_proxy_allowlist", {}) if isinstance(policy_manifest_payload, dict) else {}
        template_scopes = policy_manifest_payload.get("template_runtime_scopes", {}) if isinstance(policy_manifest_payload, dict) else {}
        allowed_domains = [str(x) for x in (http_allow.get("allowed_domains", []) or [])]
        allowed_methods = [str(x).upper() for x in (http_allow.get("allowed_methods", ["GET"]) or ["GET"])]
        url_prefixes = [str(x) for x in (http_allow.get("allowed_url_prefixes", []) or [])]
        allowed_private_hosts = [str(x).lower() for x in (http_allow.get("allowed_private_hosts", []) or [])]

        if wave_template_id in self.config.market_intel_templates:
            for url_value in context_refs.get("sources", []) or []:
                try:
                    host = (urllib.parse.urlparse(str(url_value)).hostname or "").lower()
                    if host and host not in allowed_domains:
                        allowed_domains.append(host)
                    if str(url_value) not in url_prefixes:
                        url_prefixes.append(str(url_value))
                except Exception:
                    continue

        if wave_template_id == "ENTERPRISE_CHANGE_CONTROL_V1":
            repo_base_url = str(context_refs.get("repo_base_url", "")).strip()
            allowed_action = str(context_refs.get("allowed_action", "pull_request")).strip() or "pull_request"
            try:
                host = (urllib.parse.urlparse(repo_base_url).hostname or "").lower()
                if host and host not in allowed_domains:
                    allowed_domains.append(host)
            except Exception:
                pass
            allowed_prefix = str(context_refs.get("allowed_enterprise_prefix", "")).strip()
            if not allowed_prefix and repo_base_url:
                allowed_prefix = f"{repo_base_url.rstrip('/')}/repo/{allowed_action}"
            if allowed_prefix and allowed_prefix not in url_prefixes:
                url_prefixes.append(allowed_prefix)
            if "POST" not in allowed_methods:
                allowed_methods.append("POST")

        if wave_template_id == "ENTERPRISE_INTEGRATION_GOVERNANCE_V1":
            integration_base_url = str(context_refs.get("integration_base_url", "http://127.0.0.1:8040")).strip()
            try:
                host = (urllib.parse.urlparse(integration_base_url).hostname or "").lower()
                if host and host not in allowed_domains:
                    allowed_domains.append(host)
            except Exception:
                pass
            required_prefixes = [
                f"{integration_base_url.rstrip('/')}/repo/file_update",
                f"{integration_base_url.rstrip('/')}/aws/iam/modify_policy",
                f"{integration_base_url.rstrip('/')}/slack/channel/post_message",
            ]
            for prefix in required_prefixes:
                if prefix not in url_prefixes:
                    url_prefixes.append(prefix)
            for method_name in ("POST", "PUT"):
                if method_name not in allowed_methods:
                    allowed_methods.append(method_name)

        connector_type = self.resolve_connector_type(wave_template_id)
        if connector_type is not None:
            connector_base_url = str(
                context_refs.get("connector_base_url", context_refs.get("github_base_url", "http://127.0.0.1:8050"))
            ).strip()
            try:
                host = (urllib.parse.urlparse(connector_base_url).hostname or "").lower()
                if host and host not in allowed_domains:
                    allowed_domains.append(host)
            except Exception:
                pass
            required_prefixes = [str(x) for x in (context_refs.get("allowed_connector_prefixes", []) or [])]
            for prefix in required_prefixes:
                if prefix not in url_prefixes:
                    url_prefixes.append(prefix)
            if "POST" not in allowed_methods:
                allowed_methods.append("POST")

        if wave_template_id == "production_config_change_v1":
            return {
                "allowlisted_paths": [self.config.prod_config_target],
                "allowlisted_keys": sorted(self.config.prod_config_allowed_keys),
                "allowlisted_tools": ["ocean.mutate_config"],
                "mutation_types": ["config_mutation"],
                "http_proxy": {
                    "allowed_domains": allowed_domains,
                    "allowed_methods": allowed_methods,
                    "allowed_url_prefixes": url_prefixes,
                    "allowed_private_hosts": allowed_private_hosts,
                },
            }

        if wave_template_id == "ENTERPRISE_CHANGE_CONTROL_V1":
            return {
                "allowlisted_paths": [],
                "allowlisted_keys": [],
                "allowlisted_tools": ["ocean.proxy.http"],
                "mutation_types": ["repo_change_control"],
                "http_proxy": {
                    "allowed_domains": allowed_domains,
                    "allowed_methods": allowed_methods,
                    "allowed_url_prefixes": url_prefixes,
                    "allowed_private_hosts": allowed_private_hosts,
                },
            }

        if wave_template_id == "ENTERPRISE_INTEGRATION_GOVERNANCE_V1":
            template_scope = template_scopes.get("ENTERPRISE_INTEGRATION_GOVERNANCE_V1", {}) if isinstance(template_scopes, dict) else {}
            scope_paths = [str(x) for x in (template_scope.get("allowlisted_paths", []) or ["/repo/docs/", "/repo/tests/"])]
            scope_tools = [
                str(x)
                for x in (
                    template_scope.get("allowlisted_tools", [])
                    or ["repo.file_update", "deployment.approve_release", "slack.channel.post_message"]
                )
            ]
            return {
                "allowlisted_paths": scope_paths,
                "allowlisted_keys": [],
                "allowlisted_tools": scope_tools,
                "mutation_types": ["enterprise_integration_action"],
                "http_proxy": {
                    "allowed_domains": allowed_domains,
                    "allowed_methods": allowed_methods,
                    "allowed_url_prefixes": url_prefixes,
                    "allowed_private_hosts": allowed_private_hosts,
                },
            }

        if connector_type is not None:
            template_scope = template_scopes.get(wave_template_id, {}) if isinstance(template_scopes, dict) else {}
            scope_paths = [str(x) for x in (template_scope.get("allowlisted_paths", []) or ["/docs/", "/agents/output/", "/reports/"])]
            scope_tools = [str(x) for x in (template_scope.get("allowlisted_tools", []) or [])]
            scope_actions = [
                str(x)
                for x in (
                    template_scope.get("allowlisted_actions", [])
                    or ["create_branch", "commit_file", "open_pull_request"]
                )
            ]
            scope_repos = [str(x) for x in (template_scope.get("allowlisted_repos", []) or ["surfit-demo-repo"])]
            return {
                "allowlisted_paths": scope_paths,
                "allowlisted_keys": [],
                "allowlisted_tools": scope_tools,
                "allowlisted_actions": scope_actions,
                "allowlisted_repos": scope_repos,
                "mutation_types": [f"{connector_type}_workflow"],
                "http_proxy": {
                    "allowed_domains": allowed_domains,
                    "allowed_methods": allowed_methods,
                    "allowed_url_prefixes": url_prefixes,
                    "allowed_private_hosts": allowed_private_hosts,
                },
            }

        return {
            "allowlisted_paths": [],
            "allowlisted_keys": [],
            "allowlisted_tools": [],
            "mutation_types": [],
            "http_proxy": {
                "allowed_domains": allowed_domains,
                "allowed_methods": allowed_methods,
                "allowed_url_prefixes": url_prefixes,
                "allowed_private_hosts": allowed_private_hosts,
            },
        }

    def mint_wave_mutation_token(
        self,
        *,
        wave_id: str,
        agent_id: str,
        policy_manifest_hash: str,
        policy_version: str,
        wave_template_id: str,
        scope: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> tuple[str, str, str, str]:
        expires_epoch = int(time.time()) + int(ttl_seconds if ttl_seconds is not None else self.config.mutation_token_ttl_seconds)
        payload = {
            "v": 1,
            "wave_id": wave_id,
            "agent_id": agent_id,
            "policy_manifest_hash": policy_manifest_hash,
            "policy_version": policy_version,
            "wave_template_id": wave_template_id,
            "scope": scope,
            "exp": expires_epoch,
        }
        payload_json = self.canonicalize_policy_manifest(payload)
        payload_b64 = self._b64url_encode(payload_json.encode("utf-8"))
        sig = hmac.new(self.config.token_secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        token = f"swt1.{payload_b64}.{self._b64url_encode(sig)}"
        token_hash = self.sha256_text(token)
        expires_iso = datetime.fromtimestamp(expires_epoch, tz=timezone.utc).isoformat()
        return token, token_hash, expires_iso, payload_json

    def _token_replay_decision(self, token: str, exp_epoch: int, now_epoch: int) -> str | None:
        token_id = self.sha256_text(token)
        with self._token_replay_lock:
            state = self._token_replay_state.get(token_id)
            if state is None:
                self._token_replay_state[token_id] = {"count": 1, "exp": exp_epoch}
                return None
            state["count"] = int(state.get("count", 0)) + 1
            if state["count"] > self.config.token_replay_max_uses:
                return "TOKEN_REPLAY_DETECTED"
            if now_epoch > (int(state.get("exp", exp_epoch)) + self.config.token_replay_grace_seconds):
                return "TOKEN_REPLAY_DETECTED"
            return None

    @staticmethod
    def _sanitize_url(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        except Exception:
            return url

    @staticmethod
    def _host_resolves_private(host: str) -> bool:
        try:
            infos = socket.getaddrinfo(host, None)
        except Exception:
            return True
        for info in infos:
            ip_text = info[4][0]
            try:
                ip = ipaddress.ip_address(ip_text)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return True
            except Exception:
                return True
        return False

    def proxy_http(
        self,
        conn: sqlite3.Connection,
        req: dict[str, Any],
        *,
        log_decision: Callable[[sqlite3.Connection, str, str, str, str, str], None],
        api_tenant_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        token = req.get("wave_mutation_token")
        method = str(req.get("method", "GET")).upper()
        url = str(req.get("url", "")).strip()
        sanitized_url = self._sanitize_url(url)

        def deny(reason_code: str, message: str, wave_id: str | None = None) -> tuple[int, dict[str, Any]]:
            if wave_id:
                log_decision(conn, wave_id, "DENY", f"{message} ({method} {sanitized_url})", reason_code, "ocean.proxy.http")
                conn.commit()
            return 403, {
                "status": "REJECTED",
                "reason_code": reason_code,
                "message": message,
                "url": sanitized_url,
                "method": method,
            }

        if not token:
            return deny("TOKEN_MISSING", "wave_mutation_token is required.")

        token_payload, token_error = self.decode_wave_mutation_token(str(token))
        if token_error or not token_payload:
            return deny("TOKEN_INVALID_SIGNATURE", "Mutation token signature is invalid.")

        wave_id = str(token_payload.get("wave_id", ""))
        if not wave_id:
            return deny("TOKEN_INVALID_SIGNATURE", "Mutation token missing wave scope.")

        wave = conn.execute(
            """
            SELECT wave_id, policy_manifest_hash, policy_manifest_json, tenant_id
            FROM waves
            WHERE wave_id = ?
            """,
            (wave_id,),
        ).fetchone()
        if not wave:
            return deny("TOKEN_INVALID_SIGNATURE", "Wave not found for token scope.", wave_id)

        exp = int(token_payload.get("exp", 0))
        now_epoch = int(time.time())
        replay_decision = self._token_replay_decision(str(token), exp_epoch=exp, now_epoch=now_epoch)
        if replay_decision:
            return deny("TOKEN_REPLAY_DETECTED", "Mutation token replay threshold exceeded.", wave_id)
        if exp <= now_epoch:
            return deny("TOKEN_EXPIRED", "Mutation token expired.", wave_id)

        if token_payload.get("policy_manifest_hash") != wave[1]:
            return deny("POLICY_HASH_MISMATCH", "Token policy hash does not match wave pinned policy.", wave_id)
        if api_tenant_id and wave[3] and str(wave[3]) != api_tenant_id:
            return deny("TENANT_MISMATCH", "API key tenant does not match token wave tenant.", wave_id)

        scope = token_payload.get("scope") or {}
        proxy_scope = scope.get("http_proxy") or {}
        scope_tools = {str(t) for t in (scope.get("allowlisted_tools", []) or [])}
        scope_paths = [str(p) for p in (scope.get("allowlisted_paths", []) or [])]
        manifest_proxy_allowlist: dict[str, Any] = {}
        manifest_runtime_scope: dict[str, Any] = {}

        if wave[2]:
            try:
                manifest_payload = json.loads(wave[2])
                if isinstance(manifest_payload, dict):
                    maybe_proxy = manifest_payload.get("http_proxy_allowlist")
                    if isinstance(maybe_proxy, dict):
                        manifest_proxy_allowlist = maybe_proxy
                    template_scopes = manifest_payload.get("template_runtime_scopes")
                    if isinstance(template_scopes, dict):
                        candidate_scope = template_scopes.get(str(token_payload.get("wave_template_id", "")))
                        if isinstance(candidate_scope, dict):
                            manifest_runtime_scope = candidate_scope
            except Exception:
                manifest_proxy_allowlist = {}

        allowed_methods = {str(m).upper() for m in (proxy_scope.get("allowed_methods", []) or [])}
        allowed_domains = {str(d).lower() for d in (proxy_scope.get("allowed_domains", []) or [])}
        allowed_prefixes = [str(p) for p in (proxy_scope.get("allowed_url_prefixes", []) or [])]

        manifest_methods = {str(m).upper() for m in (manifest_proxy_allowlist.get("allowed_methods", []) or [])}
        manifest_domains = {str(d).lower() for d in (manifest_proxy_allowlist.get("allowed_domains", []) or [])}
        manifest_prefixes = [str(p) for p in (manifest_proxy_allowlist.get("allowed_url_prefixes", []) or [])]

        if manifest_methods:
            allowed_methods &= manifest_methods
        if manifest_domains:
            allowed_domains &= manifest_domains
        # Global manifest proxy prefixes can carry unrelated template defaults.
        # Only intersect prefixes when a template-specific runtime scope is present.
        if manifest_prefixes and manifest_runtime_scope:
            if allowed_prefixes:
                allowed_prefixes = [
                    prefix
                    for prefix in allowed_prefixes
                    if any(prefix.startswith(mp) or mp.startswith(prefix) for mp in manifest_prefixes)
                ]
            else:
                allowed_prefixes = manifest_prefixes

        if method not in allowed_methods:
            return deny("SCOPE_VIOLATION", "HTTP method not allowed by token+policy scope.", wave_id)

        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        scheme = (parsed.scheme or "").lower()
        if scheme not in {"http", "https"} or not host:
            return deny("SCOPE_VIOLATION", "URL scheme/host is invalid for proxy.", wave_id)

        if host not in allowed_domains:
            return deny("SCOPE_VIOLATION", "Domain not allowlisted by token+policy scope.", wave_id)

        if allowed_prefixes and not any(url.startswith(prefix) for prefix in allowed_prefixes):
            return deny("SCOPE_VIOLATION", "URL not allowed by token+policy prefix scope.", wave_id)

        governance_context = req.get("governance_context") or {}
        requested_tool = str(governance_context.get("tool", "")).strip()
        requested_path = str(governance_context.get("target_path", "")).strip()
        requested_repo = str(governance_context.get("requested_repo", "")).strip()
        requested_action = str(governance_context.get("requested_action", "")).strip()

        manifest_tools = (
            {str(t) for t in (manifest_runtime_scope.get("allowlisted_tools", []) or [])}
            if isinstance(manifest_runtime_scope, dict)
            else set()
        )
        manifest_paths = (
            [str(p) for p in (manifest_runtime_scope.get("allowlisted_paths", []) or [])]
            if isinstance(manifest_runtime_scope, dict)
            else []
        )
        manifest_denied_paths = (
            [str(p) for p in (manifest_runtime_scope.get("denied_paths", []) or [])]
            if isinstance(manifest_runtime_scope, dict)
            else []
        )
        manifest_actions = (
            {str(a) for a in (manifest_runtime_scope.get("allowlisted_actions", []) or [])}
            if isinstance(manifest_runtime_scope, dict)
            else set()
        )
        manifest_denied_actions = (
            {str(a) for a in (manifest_runtime_scope.get("denied_actions", []) or [])}
            if isinstance(manifest_runtime_scope, dict)
            else set()
        )
        manifest_repos = (
            {str(r) for r in (manifest_runtime_scope.get("allowlisted_repos", []) or [])}
            if isinstance(manifest_runtime_scope, dict)
            else set()
        )

        token_actions = {str(a) for a in (scope.get("allowlisted_actions", []) or [])}
        effective_actions = set(token_actions) if token_actions else set()
        if manifest_actions:
            if effective_actions:
                effective_actions &= manifest_actions
            else:
                effective_actions = set(manifest_actions)

        if requested_action and requested_action in manifest_denied_actions:
            return deny("ACTION_NOT_ALLOWED", "Requested action is denied by pinned policy scope.", wave_id)
        if requested_action and effective_actions and requested_action not in effective_actions:
            return deny("ACTION_NOT_ALLOWED", "Requested action is not allowed by token+policy scope.", wave_id)

        token_repos = {str(r) for r in (scope.get("allowlisted_repos", []) or [])}
        effective_repos = set(token_repos) if token_repos else set()
        if manifest_repos:
            if effective_repos:
                effective_repos &= manifest_repos
            else:
                effective_repos = set(manifest_repos)
        if requested_repo and effective_repos and requested_repo not in effective_repos:
            return deny("REPO_NOT_ALLOWED", "Requested repo is not allowed by token+policy scope.", wave_id)

        effective_tools = set(scope_tools)
        if manifest_tools:
            effective_tools &= manifest_tools
        if requested_tool and effective_tools and requested_tool not in effective_tools:
            return deny("TOOL_NOT_ALLOWED", "Requested tool is not allowed by token+policy scope.", wave_id)

        effective_paths = list(scope_paths)
        if manifest_paths:
            if effective_paths:
                effective_paths = [
                    p for p in effective_paths if any(p.startswith(mp) or mp.startswith(p) for mp in manifest_paths)
                ]
            else:
                effective_paths = list(manifest_paths)

        if requested_path and manifest_denied_paths:
            normalized_path = requested_path.lstrip("/")
            for denied_pattern in manifest_denied_paths:
                raw_pattern = str(denied_pattern).lstrip("/")
                if not raw_pattern:
                    continue
                if fnmatch.fnmatch(normalized_path, raw_pattern):
                    return deny("PATH_NOT_ALLOWED", "Requested path is denied by pinned policy scope.", wave_id)

        if requested_path and effective_paths and not any(requested_path.startswith(prefix) for prefix in effective_paths):
            return deny("PATH_NOT_ALLOWED", "Requested path is not allowed by token+policy scope.", wave_id)

        explicit_private_allow = {
            str(x).lower() for x in (manifest_proxy_allowlist.get("allowed_private_hosts", []) or [])
        }
        if self.config.demo_safe_mode:
            safe_hosts = {"localhost", "127.0.0.1", "::1"} | allowed_domains | explicit_private_allow
            if host not in safe_hosts:
                return deny("SCOPE_VIOLATION", "DEMO_SAFE_MODE blocks non-localhost target.", wave_id)
            if (
                host not in {"localhost", "127.0.0.1", "::1"}
                and host not in explicit_private_allow
                and self._host_resolves_private(host)
            ):
                return deny(
                    "SCOPE_VIOLATION",
                    "DEMO_SAFE_MODE blocks private/reserved host resolution.",
                    wave_id,
                )

        headers = dict(req.get("headers") or {})
        data: bytes | None = None
        if req.get("json_body") is not None:
            data = json.dumps(req.get("json_body")).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif req.get("body") is not None:
            data = str(req.get("body")).encode("utf-8")

        try:
            proxy_req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(proxy_req, timeout=self.config.proxy_timeout_seconds) as resp:
                raw = resp.read(self.config.proxy_max_response_bytes + 1)
                if len(raw) > self.config.proxy_max_response_bytes:
                    return deny("RESPONSE_TOO_LARGE", "Proxy response exceeds max allowed bytes.", wave_id)
                body_text = raw.decode("utf-8", errors="replace")
                selected_headers = {
                    "content-type": resp.headers.get("Content-Type"),
                    "content-length": resp.headers.get("Content-Length"),
                }
                log_decision(conn, wave_id, "ALLOW", f"{method} {sanitized_url}", "http_proxy_allow", "ocean.proxy.http")
                conn.commit()
                return 200, {
                    "status": "ALLOWED",
                    "reason_code": "OK",
                    "wave_id": wave_id,
                    "url": sanitized_url,
                    "method": method,
                    "status_code": resp.status,
                    "headers": selected_headers,
                    "body": body_text,
                    "truncated": False,
                }
        except urllib.error.HTTPError as exc:
            log_decision(
                conn,
                wave_id,
                "DENY",
                f"{method} {sanitized_url} -> HTTP {exc.code}",
                "http_proxy_target_error",
                "ocean.proxy.http",
            )
            conn.commit()
            return 403, {
                "status": "REJECTED",
                "reason_code": "TARGET_HTTP_ERROR",
                "message": f"Target responded with HTTP {exc.code}",
                "url": sanitized_url,
                "method": method,
            }
        except Exception as exc:
            log_decision(
                conn,
                wave_id,
                "DENY",
                f"{method} {sanitized_url} -> {exc}",
                "http_proxy_transport_error",
                "ocean.proxy.http",
            )
            conn.commit()
            return 403, {
                "status": "REJECTED",
                "reason_code": "TARGET_HTTP_ERROR",
                "message": f"Proxy transport error: {exc}",
                "url": sanitized_url,
                "method": method,
            }
