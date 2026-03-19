"""
SURFIT Wave Engine — Core Evaluator
WAVE = BASE SYSTEM RISK + ACTION TYPE MODIFIER + DESTINATION MODIFIER + CONTEXT MODIFIERS
Deterministic. Explainable. Configurable.
"""

from typing import Optional
from .models import (
    EvaluateRequest, WaveResult, ContributingFactor,
    ResourceInfo, ContextInfo
)
from .policy import CustomerPolicy, load_default_policy
from .classifier import DestinationClassifier


class WaveEngine:
    """
    Core wave assignment engine.
    
    Every evaluation produces:
    - A wave score (1-5)
    - A handling decision (auto/log/check/approve/block)
    - A complete list of reasons explaining the decision
    - Every contributing factor with its modifier value
    """

    def __init__(self, policy: Optional[CustomerPolicy] = None):
        self.policy = policy or load_default_policy()
        self.classifier = DestinationClassifier(self.policy)

    def evaluate(self, request: EvaluateRequest) -> WaveResult:
        """
        Evaluate an action request and assign a wave.
        
        Logic:
        1. Check for forced overrides
        2. Start with system baseline
        3. Add action type modifier
        4. Classify destination, add destination modifier
        5. Apply context modifiers
        6. Clamp to 1-5
        7. Map to handling decision
        8. Return full explanation
        """
        factors = []
        reasons = []
        
        system = request.system.lower()
        action = request.action.lower()
        resource = request.resource or ResourceInfo()
        context = request.context or ContextInfo()

        # ── Step 0: Check overrides ──
        dest_class, dest_group = self.classifier.classify(system, resource)
        override = self.policy.find_override(
            system, action,
            resource.resource_name,
            dest_class
        )
        
        if override:
            if override.forced_wave is not None and override.forced_handling is not None:
                wave = override.forced_wave
                handling = override.forced_handling
                reason = f"Override applied: {override.reason}" if override.reason else "Explicit override"
                return WaveResult(
                    wave_score=wave,
                    wave_label=f"Wave {wave}",
                    handling=handling,
                    reasons=[reason],
                    contributing_factors=[
                        ContributingFactor("override", f"{system}/{action}", wave, reason)
                    ],
                    destination_class_resolved=dest_class,
                )

        # ── Step 1: System baseline ──
        baseline = self.policy.get_system_baseline(system)
        factors.append(ContributingFactor(
            source="system_baseline",
            key=system,
            modifier=baseline,
            description=f"System baseline: {system}={baseline}"
        ))
        reasons.append(f"System baseline: {system}={baseline}")
        score = baseline

        # ── Step 2: Action type modifier ──
        action_mod = self.policy.get_action_modifier(system, action)
        if action_mod:
            factors.append(ContributingFactor(
                source="action_modifier",
                key=f"{system}/{action}",
                modifier=action_mod.modifier,
                description=f"Action modifier: {action}={action_mod.modifier:+d} ({action_mod.description})"
            ))
            reasons.append(f"Action modifier: {action}={action_mod.modifier:+d}")
            score += action_mod.modifier
        else:
            reasons.append(f"Action modifier: {action}=+0 (no specific modifier)")

        # ── Step 3: Destination classification ──
        if dest_group:
            factors.append(ContributingFactor(
                source="destination_modifier",
                key=f"{system}/{dest_class}",
                modifier=dest_group.risk_modifier,
                description=f"Destination: {dest_class}={dest_group.risk_modifier:+d} ({dest_group.description})"
            ))
            reasons.append(f"Destination: {dest_class}={dest_group.risk_modifier:+d}")
            score += dest_group.risk_modifier
        elif dest_class:
            reasons.append(f"Destination: {dest_class}=+0 (no group config)")

        # ── Step 4: Context modifiers ──
        for cm in self.policy.context_modifiers:
            ctx_value = self._get_context_value(context, cm.field_name)
            if ctx_value is not None and ctx_value == cm.trigger_value:
                # Special case: approval_required_override forces wave 5
                if cm.modifier >= 99:
                    score = 99  # will clamp to 5
                    factors.append(ContributingFactor(
                        source="context_modifier",
                        key=f"{cm.field_name}={cm.trigger_value}",
                        modifier=cm.modifier,
                        description=f"Context override: {cm.description}"
                    ))
                    reasons.append(f"Context override: {cm.description}")
                else:
                    factors.append(ContributingFactor(
                        source="context_modifier",
                        key=f"{cm.field_name}={cm.trigger_value}",
                        modifier=cm.modifier,
                        description=f"Context: {cm.field_name}={cm.trigger_value} => {cm.modifier:+d} ({cm.description})"
                    ))
                    reasons.append(f"Context: {cm.field_name}={cm.trigger_value} => {cm.modifier:+d}")
                    score += cm.modifier

        # ── Step 5: Clamp to 1-5 ──
        raw_score = score
        score = max(1, min(5, score))

        # ── Step 6: Determine handling ──
        handling = self.policy.get_handling_for_wave(score)

        # If action modifier suggested specific handling, note it
        if action_mod and action_mod.default_handling:
            reasons.append(f"Action suggests: {action_mod.default_handling} (wave threshold takes precedence)")

        reasons.append(f"Final: Wave {score} => {handling}")

        return WaveResult(
            wave_score=score,
            wave_label=f"Wave {score}",
            handling=handling,
            reasons=reasons,
            contributing_factors=factors,
            destination_class_resolved=dest_class,
            raw_score=raw_score,
        )

    def _get_context_value(self, context: ContextInfo, field_name: str):
        """Extract a value from context by field name."""
        if hasattr(context, field_name):
            return getattr(context, field_name)
        return context.custom.get(field_name)
