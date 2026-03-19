# SurfitAI — Wave Engine v1.0

## Backend Design Summary

The wave engine implements deterministic, explainable, configurable wave assignment using the formula:

```
WAVE = BASE SYSTEM RISK + ACTION TYPE MODIFIER + DESTINATION MODIFIER + CONTEXT MODIFIERS
```

Every evaluation produces a complete explanation trail. No opaque AI reasoning. No semantic NLP on content. Every decision is inspectable and debuggable.

## Architecture

```
surfit-wave-engine/
├── surfit_wave/
│   ├── __init__.py        # Package exports
│   ├── models.py          # Data models (input/output)
│   ├── policy.py          # Customer policy config + defaults
│   ├── classifier.py      # Destination classifier (grouped channels)
│   ├── engine.py          # Core wave engine (deterministic evaluation)
│   └── api.py             # FastAPI endpoints + request/response schemas
├── config/
│   └── acme_policy.json   # Example customer policy override
├── tests/
│   └── test_wave_engine.py  # Full test suite (9 scenarios)
└── README.md
```

## Data Model

### Systems (base risk scores)
| System | Base Risk | Description |
|--------|-----------|-------------|
| slack | 1 | Messaging platform |
| notion | 2 | Knowledge and docs |
| github | 3 | Code and deployment |
| aws | 4 | Cloud infrastructure |

### Action Modifiers
| System | Action | Modifier | Description |
|--------|--------|----------|-------------|
| slack | post_message | +0 | Standard message |
| slack | post_announcement | +2 | Company-wide announcement |
| slack | delete_message | +1 | Delete a message |
| notion | update_database_entry | +1 | Modify structured data |
| notion | delete_page | +2 | Delete a page |
| github | create_pr | +0 | Open PR |
| github | merge_pr | +2 | Merge PR |
| github | create_release | +2 | Create release |

### Destination Classes (Slack)
| Class | Risk Modifier | Visibility | Examples |
|-------|---------------|------------|----------|
| dm | +0 | internal | Any DM (detected by channel ID) |
| team_channel | +0 | internal | eng-platform, ops-internal |
| company_announcement | +2 | company_wide | company-announcements, all-hands |
| sensitive_channel | +2 | internal | security-incidents, legal-review |
| external_shared_channel | +3 | external | External/partner channels |

### Context Modifiers
| Field | Trigger Value | Modifier | Description |
|-------|---------------|----------|-------------|
| env | prod | +1 | Production environment |
| env | dev | -1 | Development environment |
| visibility | company_wide | +1 | Company-wide reach |
| visibility | external | +2 | External visibility |
| reversible | false | +2 | Irreversible action |
| sensitive_data | true | +2 | Contains sensitive data |
| financial_impact | true | +2 | Financial impact |

### Wave → Handling
| Wave | Handling | Description |
|------|---------|-------------|
| 1 | auto | Autonomous — execute immediately |
| 2 | log | Logged — execute and record |
| 3 | check | Checked — verify before executing |
| 4 | approve | Approval — requires human sign-off |
| 5 | approve | Critical — escalated approval |

## API Request/Response

### POST /api/v1/governance/evaluate

**Request:**
```json
{
  "system": "slack",
  "action": "post_announcement",
  "resource": {
    "resource_id": "C04ABCDEF",
    "resource_name": "company-announcements",
    "destination_class": null
  },
  "context": {
    "env": "prod",
    "visibility": "company_wide",
    "reversible": true,
    "sensitive_data": false
  },
  "agent_id": "agent-001",
  "tenant_id": "acme-corp"
}
```

**Response:**
```json
{
  "wave_score": 5,
  "wave_label": "Wave 5",
  "handling": "approve",
  "destination_class_resolved": "company_announcement",
  "reasons": [
    "System baseline: slack=1",
    "Action modifier: post_announcement=+2",
    "Destination: company_announcement=+2",
    "Context: env=prod => +1",
    "Context: visibility=company_wide => +1",
    "Final: Wave 5 => approve"
  ],
  "contributing_factors": [
    {"source": "system_baseline", "key": "slack", "modifier": 1, "description": "..."},
    {"source": "action_modifier", "key": "slack/post_announcement", "modifier": 2, "description": "..."},
    {"source": "destination_modifier", "key": "slack/company_announcement", "modifier": 2, "description": "..."},
    {"source": "context_modifier", "key": "env=prod", "modifier": 1, "description": "..."},
    {"source": "context_modifier", "key": "visibility=company_wide", "modifier": 1, "description": "..."}
  ]
}
```

## Example Walkthroughs

### A. Slack DM → Wave 2 (log)
```
slack(1) + post_dm(0) + dm_dest(0) + prod(+1) = 2 → log
```

### B. Slack Announcement → Wave 5 (approve)
```
slack(1) + post_announcement(+2) + announcement_dest(+2) + prod(+1) + company_wide(+1) = 7 → clamped to 5 → approve
```

### C. Notion DB Update → Wave 5 (approve)
```
notion(2) + update_database_entry(+1) + protected_dest(+1) + prod(+1) = 5 → approve
```

### D. GitHub Create PR → Wave 4 (approve)
```
github(3) + create_pr(0) + standard(0) + prod(+1) = 4 → approve
```

### E. GitHub Merge PR (main, irreversible) → Wave 5 (approve)
```
github(3) + merge_pr(+2) + critical_dest(+2) + prod(+1) + irreversible(+2) = 10 → clamped to 5 → approve
```

## Running

```bash
# Run tests
python tests/test_wave_engine.py

# Run API (requires: pip install fastapi uvicorn)
python -c "from surfit_wave.api import create_app; import uvicorn; uvicorn.run(create_app(), host='0.0.0.0', port=8000)"
```

## Customer Configuration

Customers define their own policy by providing a JSON file with:
- Custom resource groups (which channels belong to which class)
- Overrides (force specific wave/handling for certain actions)
- See `config/acme_policy.json` for an example.

## Assumptions

1. Content semantic analysis is intentionally NOT part of v1. Destination class + action type + context is sufficient.
2. Slack DMs are detected by channel ID prefix (D for DM, G for group DM). This matches Slack's API behavior.
3. Unknown systems default to base_risk=2. Unknown actions get +0 modifier.
4. Wave scores clamp to 1-5. Raw scores are preserved for debugging.
5. The `approval_required_override` context flag forces Wave 5 regardless of other factors.
6. `delay` and `reroute` handling types exist in the model but are no-ops for v1.
