"""
SURFIT Wave Engine — Policy Configuration
Customer-editable policy that drives all wave assignment logic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os


@dataclass
class SystemConfig:
    """Base risk score for a system."""
    base_risk: int  # 1-5
    description: str = ""


@dataclass
class ActionModifier:
    """Risk modifier for a specific action type on a system."""
    modifier: int  # additive: +1, +2, -1, etc.
    default_handling: Optional[str] = None  # suggestion, can be overridden by wave thresholds
    description: str = ""


@dataclass
class ResourceGroup:
    """A group of resources (e.g., channels) sharing the same risk profile."""
    destination_class: str
    risk_modifier: int
    visibility: str = "internal"  # internal / company_wide / external
    default_handling: Optional[str] = None
    members: List[str] = field(default_factory=list)  # explicit member list
    description: str = ""


@dataclass
class ContextModifierConfig:
    """How a context field modifies risk."""
    field_name: str
    trigger_value: Any  # the value that triggers the modifier
    modifier: int
    description: str = ""


@dataclass
class HandlingThreshold:
    """Maps wave scores to handling decisions."""
    wave: int
    handling: str
    description: str = ""


@dataclass
class Override:
    """Specific override for a system+action+resource combination."""
    system: str
    action: Optional[str] = None
    resource_name: Optional[str] = None
    destination_class: Optional[str] = None
    forced_wave: Optional[int] = None
    forced_handling: Optional[str] = None
    reason: str = ""


@dataclass
class CustomerPolicy:
    """Complete customer policy configuration."""
    tenant_id: str = "default"
    
    # System baselines
    systems: Dict[str, SystemConfig] = field(default_factory=dict)
    
    # Action modifiers per system: { "slack": { "post_message": ActionModifier, ... } }
    action_modifiers: Dict[str, Dict[str, ActionModifier]] = field(default_factory=dict)
    
    # Resource groups per system: { "slack": { "announcement": ResourceGroup, ... } }
    resource_groups: Dict[str, Dict[str, ResourceGroup]] = field(default_factory=dict)
    
    # Context modifiers (global)
    context_modifiers: List[ContextModifierConfig] = field(default_factory=list)
    
    # Wave -> Handling thresholds
    handling_thresholds: List[HandlingThreshold] = field(default_factory=list)
    
    # Specific overrides
    overrides: List[Override] = field(default_factory=list)

    def get_system_baseline(self, system: str) -> int:
        cfg = self.systems.get(system)
        return cfg.base_risk if cfg else 2  # default moderate

    def get_action_modifier(self, system: str, action: str) -> Optional[ActionModifier]:
        sys_actions = self.action_modifiers.get(system, {})
        return sys_actions.get(action)

    def get_handling_for_wave(self, wave: int) -> str:
        for t in self.handling_thresholds:
            if t.wave == wave:
                return t.handling
        # Default mapping
        defaults = {1: "auto", 2: "log", 3: "check", 4: "approve", 5: "approve"}
        return defaults.get(wave, "check")

    def find_override(self, system: str, action: str, resource_name: Optional[str], dest_class: Optional[str]) -> Optional[Override]:
        for o in self.overrides:
            if o.system != system:
                continue
            if o.action and o.action != action:
                continue
            if o.resource_name and o.resource_name != resource_name:
                continue
            if o.destination_class and o.destination_class != dest_class:
                continue
            return o
        return None

    def classify_resource(self, system: str, resource_name: Optional[str]) -> Optional[ResourceGroup]:
        sys_groups = self.resource_groups.get(system, {})
        if not resource_name:
            return None
        for group_key, group in sys_groups.items():
            if resource_name in group.members:
                return group
        return None


def load_default_policy() -> CustomerPolicy:
    """Load the default policy configuration."""
    return CustomerPolicy(
        tenant_id="default",
        
        systems={
            "slack": SystemConfig(base_risk=1, description="Messaging platform"),
            "notion": SystemConfig(base_risk=2, description="Knowledge and docs platform"),
            "github": SystemConfig(base_risk=3, description="Code and deployment platform"),
            "aws": SystemConfig(base_risk=4, description="Cloud infrastructure"),
        },
        
        action_modifiers={
            "slack": {
                "post_message": ActionModifier(modifier=0, description="Standard message post"),
                "post_dm": ActionModifier(modifier=0, description="Direct message"),
                "post_announcement": ActionModifier(modifier=2, description="Company-wide announcement"),
                "update_message": ActionModifier(modifier=0, description="Edit existing message"),
                "delete_message": ActionModifier(modifier=1, description="Delete a message"),
            },
            "notion": {
                "create_page": ActionModifier(modifier=0, description="Create new page"),
                "update_page": ActionModifier(modifier=1, description="Modify existing page"),
                "update_database_entry": ActionModifier(modifier=1, description="Modify structured data"),
                "delete_page": ActionModifier(modifier=2, description="Delete a page"),
            },
            "github": {
                "create_pr": ActionModifier(modifier=0, description="Open a pull request"),
                "merge_pr": ActionModifier(modifier=2, description="Merge PR into target branch"),
                "push_branch": ActionModifier(modifier=1, description="Push to a branch"),
                "delete_branch": ActionModifier(modifier=1, description="Delete a branch"),
                "create_release": ActionModifier(modifier=2, description="Create a release"),
            },
        },
        
        resource_groups={
            "slack": {
                "dm": ResourceGroup(
                    destination_class="dm",
                    risk_modifier=0,
                    visibility="internal",
                    members=[],  # DMs classified by type, not by name
                    description="Direct messages — low visibility, low risk",
                ),
                "team_channel": ResourceGroup(
                    destination_class="team_channel",
                    risk_modifier=0,
                    visibility="internal",
                    members=["eng-platform", "ops-internal", "design-team", "backend-dev"],
                    description="Team-internal channels",
                ),
                "announcement": ResourceGroup(
                    destination_class="company_announcement",
                    risk_modifier=2,
                    visibility="company_wide",
                    members=["company-announcements", "all-hands", "leadership-updates", "exec-updates"],
                    description="Company-wide announcement channels",
                ),
                "sensitive": ResourceGroup(
                    destination_class="sensitive_channel",
                    risk_modifier=2,
                    visibility="internal",
                    members=["security-incidents", "legal-review", "hr-confidential"],
                    description="Sensitive/restricted channels",
                ),
                "external": ResourceGroup(
                    destination_class="external_shared_channel",
                    risk_modifier=3,
                    visibility="external",
                    members=[],  # External channels classified by Slack metadata
                    description="External shared channels — highest risk",
                ),
            },
            "github": {
                "main_branch": ResourceGroup(
                    destination_class="critical",
                    risk_modifier=2,
                    visibility="internal",
                    members=["main", "master", "production", "release"],
                    description="Protected branches",
                ),
                "dev_branch": ResourceGroup(
                    destination_class="standard",
                    risk_modifier=0,
                    visibility="internal",
                    members=[],
                    description="Development branches — default",
                ),
            },
            "notion": {
                "shared_database": ResourceGroup(
                    destination_class="protected",
                    risk_modifier=1,
                    visibility="company_wide",
                    members=["Sprint Tracker", "OKRs", "Hiring Pipeline", "Revenue Dashboard"],
                    description="Shared databases with structured data",
                ),
            },
        },
        
        context_modifiers=[
            ContextModifierConfig(field_name="env", trigger_value="prod", modifier=1, description="Production environment"),
            ContextModifierConfig(field_name="env", trigger_value="staging", modifier=0, description="Staging environment"),
            ContextModifierConfig(field_name="env", trigger_value="dev", modifier=-1, description="Development environment"),
            ContextModifierConfig(field_name="visibility", trigger_value="company_wide", modifier=1, description="Company-wide visibility"),
            ContextModifierConfig(field_name="visibility", trigger_value="external", modifier=2, description="External visibility"),
            ContextModifierConfig(field_name="reversible", trigger_value=False, modifier=2, description="Irreversible action"),
            ContextModifierConfig(field_name="sensitive_data", trigger_value=True, modifier=2, description="Contains sensitive data"),
            ContextModifierConfig(field_name="financial_impact", trigger_value=True, modifier=2, description="Has financial impact"),
            ContextModifierConfig(field_name="approval_required_override", trigger_value=True, modifier=99, description="Manual approval override"),
        ],
        
        handling_thresholds=[
            HandlingThreshold(wave=1, handling="auto", description="Autonomous — execute immediately"),
            HandlingThreshold(wave=2, handling="log", description="Logged — execute and record"),
            HandlingThreshold(wave=3, handling="check", description="Checked — verify before executing"),
            HandlingThreshold(wave=4, handling="approve", description="Approval — requires human sign-off"),
            HandlingThreshold(wave=5, handling="approve", description="Critical — escalated approval required"),
        ],
        
        overrides=[],
    )


def load_policy_from_json(path: str) -> CustomerPolicy:
    """Load policy from a JSON file. For customer-specific configs."""
    with open(path) as f:
        data = json.load(f)
    
    policy = load_default_policy()
    policy.tenant_id = data.get("tenant_id", "default")
    
    # Merge customer overrides into default policy
    if "systems" in data:
        for sys_key, sys_data in data["systems"].items():
            policy.systems[sys_key] = SystemConfig(**sys_data)
    
    if "resource_groups" in data:
        for sys_key, groups in data["resource_groups"].items():
            if sys_key not in policy.resource_groups:
                policy.resource_groups[sys_key] = {}
            for group_key, group_data in groups.items():
                policy.resource_groups[sys_key][group_key] = ResourceGroup(**group_data)
    
    if "overrides" in data:
        for o in data["overrides"]:
            policy.overrides.append(Override(**o))
    
    return policy
