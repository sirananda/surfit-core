# OpenClaw x SurFit POC API Contract (M13)

## Base
`/api`

## 1) Start Wave
POST `/api/waves/run`

### Request
```json
{
  "wave_template_id": "sales_report_v1",
  "policy_version": "sales_report_policy_v1",
  "intent": "Generate weekly sales report",
  "context_refs": {
    "input_csv_path": "./data/sales.csv",
    "output_report_path": "./outputs/report.md"
  }
}

