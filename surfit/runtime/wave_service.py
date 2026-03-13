from __future__ import annotations

from typing import Any

from .models import WaveModel


class WaveService:
    VALID_RISK = {"low", "medium", "high", "critical"}

    def from_payload(self, payload: dict[str, Any]) -> WaveModel:
        wave_id = str(payload.get("wave_id", "")).strip()
        wave_type = str(payload.get("wave_type", "runtime_action")).strip()
        system = str(payload.get("system", "")).strip()
        action = str(payload.get("action", "")).strip()
        risk_level = str(payload.get("risk_level", "medium")).strip().lower()
        if not wave_id or not wave_type or not system or not action:
            raise ValueError("wave_id, wave_type, system, and action are required.")
        if risk_level not in self.VALID_RISK:
            raise ValueError(f"risk_level must be one of {sorted(self.VALID_RISK)}")

        raw_required = payload.get("required_execution_sequence", payload.get("required_sequence", []))
        required_execution_sequence = [str(x) for x in (raw_required or [])]

        raw_timeout = payload.get("execution_timeout")
        execution_timeout = int(raw_timeout) if raw_timeout is not None else None
        if execution_timeout is not None and execution_timeout <= 0:
            raise ValueError("execution_timeout must be > 0 when provided.")

        approval_required = bool(payload.get("approval_required", False))
        approval_rules = payload.get("approval_rules", {}) if isinstance(payload.get("approval_rules"), dict) else {}
        if approval_required and "required_for_actions" not in approval_rules:
            approval_rules = {**approval_rules, "required_for_actions": [action]}

        return WaveModel(
            wave_id=wave_id,
            wave_type=wave_type,
            system=system,
            action=action,
            risk_level=risk_level,
            approval_required=approval_required,
            required_execution_sequence=required_execution_sequence,
            approval_rules=approval_rules,
            execution_timeout=execution_timeout,
            trigger_type=str(payload.get("trigger_type", "manual")),
            context=payload.get("context", {}) if isinstance(payload.get("context"), dict) else {},
        )
