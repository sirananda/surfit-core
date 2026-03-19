"""
SURFIT Wave Engine — Data Models
Deterministic, explainable, configurable wave assignment.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class Handling(str, Enum):
    AUTO = "auto"
    LOG = "log"
    CHECK = "check"
    APPROVE = "approve"
    BLOCK = "block"
    DELAY = "delay"       # framework placeholder
    REROUTE = "reroute"   # framework placeholder


class DestinationClass(str, Enum):
    DM = "dm"
    SMALL_PRIVATE = "small_private_channel"
    TEAM_CHANNEL = "team_channel"
    ANNOUNCEMENT = "company_announcement"
    EXTERNAL_SHARED = "external_shared_channel"
    SENSITIVE = "sensitive_channel"
    UNKNOWN = "unknown"
    # Generic for non-Slack
    STANDARD = "standard"
    PROTECTED = "protected"
    CRITICAL = "critical"


# ============================================================
# INPUT MODELS
# ============================================================

@dataclass
class ResourceInfo:
    """Describes the target resource/destination of an action."""
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    destination_class: Optional[str] = None  # Will be resolved if not provided


@dataclass
class ContextInfo:
    """Contextual modifiers that affect risk scoring."""
    env: str = "prod"                    # prod / staging / dev
    visibility: str = "internal"          # internal / company_wide / external
    reversible: bool = True
    sensitive_data: bool = False
    financial_impact: bool = False
    deployment_stable: bool = True
    approval_required_override: bool = False
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentMetadata:
    """Optional secondary signal. NOT the primary classifier."""
    message_type: Optional[str] = None
    contains_mentions: bool = False
    contains_links: bool = False
    estimated_reach: Optional[int] = None


@dataclass
class EvaluateRequest:
    """Full input to the wave engine."""
    system: str
    action: str
    resource: Optional[ResourceInfo] = None
    context: Optional[ContextInfo] = None
    content_metadata: Optional[ContentMetadata] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None


# ============================================================
# OUTPUT MODELS
# ============================================================

@dataclass
class ContributingFactor:
    """One factor that contributed to the wave score."""
    source: str         # e.g., "system_baseline", "action_modifier", "context_modifier"
    key: str            # e.g., "slack", "post_message", "visibility=company_wide"
    modifier: int       # e.g., +1, +2, -1
    description: str    # human-readable explanation


@dataclass
class WaveResult:
    """Complete output of wave evaluation."""
    wave_score: int
    wave_label: str
    handling: str
    reasons: List[str]
    contributing_factors: List[ContributingFactor]
    destination_class_resolved: Optional[str] = None
    raw_score: Optional[int] = None  # before clamping to 1-5

    def to_dict(self) -> dict:
        return {
            "wave_score": self.wave_score,
            "wave_label": self.wave_label,
            "handling": self.handling,
            "reasons": self.reasons,
            "contributing_factors": [
                {"source": f.source, "key": f.key, "modifier": f.modifier, "description": f.description}
                for f in self.contributing_factors
            ],
            "destination_class_resolved": self.destination_class_resolved,
        }
