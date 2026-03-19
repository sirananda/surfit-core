"""
SURFIT Wave Engine — Destination Classifier
Resolves resource names/IDs into destination classes without requiring
per-channel hardcoding.
"""

from typing import Optional, Tuple
from .models import ResourceInfo
from .policy import CustomerPolicy, ResourceGroup


class DestinationClassifier:
    """
    Classifies destinations into groups using:
    1. Explicit customer config lists (highest priority)
    2. Metadata hints (channel type, member count)
    3. Fallback heuristics (name patterns)
    """

    def __init__(self, policy: CustomerPolicy):
        self.policy = policy

    def classify(self, system: str, resource: Optional[ResourceInfo]) -> Tuple[Optional[str], Optional[ResourceGroup]]:
        """
        Classify a resource into a destination class.
        Returns (destination_class, matching_resource_group) or (None, None).
        """
        if not resource:
            return None, None

        resource_name = resource.resource_name or ""

        # 1. Check if destination_class was explicitly provided
        if resource.destination_class:
            group = self._find_group_by_class(system, resource.destination_class)
            return resource.destination_class, group

        # 2. Check explicit customer config lists
        group = self.policy.classify_resource(system, resource_name)
        if group:
            return group.destination_class, group

        # 3. System-specific heuristics
        if system == "slack":
            return self._classify_slack(resource)
        elif system == "github":
            return self._classify_github(resource)
        elif system == "notion":
            return self._classify_notion(resource)

        # 4. Fallback
        return "unknown", None

    def _classify_slack(self, resource: ResourceInfo) -> Tuple[str, Optional[ResourceGroup]]:
        """Slack-specific classification heuristics."""
        name = (resource.resource_name or "").lower()
        rid = (resource.resource_id or "").upper()

        # DM detection: Slack DM channel IDs start with 'D'
        if rid.startswith("D"):
            return "dm", self._find_group_by_class("slack", "dm")

        # Group DM: starts with 'G' in Slack
        if rid.startswith("G"):
            return "small_private_channel", self._find_group_by_class("slack", "small_private_channel")

        # Name-based heuristics for channels not in explicit lists
        announcement_keywords = ["announcement", "all-hands", "company-", "exec-", "leadership"]
        for kw in announcement_keywords:
            if kw in name:
                return "company_announcement", self._find_group_by_class("slack", "company_announcement")

        external_keywords = ["external", "shared-", "partner-", "client-"]
        for kw in external_keywords:
            if kw in name:
                return "external_shared_channel", self._find_group_by_class("slack", "external_shared_channel")

        sensitive_keywords = ["security", "legal", "hr-", "confidential", "incident"]
        for kw in sensitive_keywords:
            if kw in name:
                return "sensitive_channel", self._find_group_by_class("slack", "sensitive_channel")

        # Default: team channel
        return "team_channel", self._find_group_by_class("slack", "team_channel")

    def _classify_github(self, resource: ResourceInfo) -> Tuple[str, Optional[ResourceGroup]]:
        """GitHub-specific classification."""
        name = (resource.resource_name or "").lower()

        protected = ["main", "master", "production", "release", "prod"]
        if name in protected:
            return "critical", self._find_group_by_class("github", "critical")

        return "standard", self._find_group_by_class("github", "standard")

    def _classify_notion(self, resource: ResourceInfo) -> Tuple[str, Optional[ResourceGroup]]:
        """Notion-specific classification."""
        name = resource.resource_name or ""

        group = self.policy.classify_resource("notion", name)
        if group:
            return group.destination_class, group

        return "standard", None

    def _find_group_by_class(self, system: str, dest_class: str) -> Optional[ResourceGroup]:
        """Find a resource group by its destination class."""
        sys_groups = self.policy.resource_groups.get(system, {})
        for group in sys_groups.values():
            if group.destination_class == dest_class:
                return group
        return None
