# Cost Optimization Custom Agents — full AWS service coverage

> **Status: in development.** This folder is where the next-generation cost
> optimization agent catalog is being built. For the current, working catalog see
> [`../custom-agents-v1/`](../custom-agents-v1/).

## Goal

Provide a cost optimization custom agent for **every AWS service that has
meaningful cost levers** — following the breadth model of
[aws-samples/sample-ai-agent-skills](https://github.com/aws-samples/sample-ai-agent-skills),
which publishes a per-service skill for 200+ AWS services.

The existing `custom-agents-v1/` catalog covers 54 agents (10 cross-service
resource-level checks + 44 per-service). This folder expands that to full
service coverage.

## How this differs from `custom-agents-v1/`

| | `custom-agents-v1/` | this folder |
|---|---|---|
| Coverage | 54 agents (curated high-value services) | Every AWS service with cost levers |
| Costing source | Public list pricing (Price List API) | Cost Explorer (bill-accurate) with Price List fallback |
| Cost data caveats | Estimates labeled as estimates | Explicit disclaimer, data-freshness header, provisional-data flag |
| Report versioning | Static artifact title | Artifact title includes run timestamp, so each run is retained |
| Methodology | Noted in caveats | Dedicated "How this report calculated cost" section with a data-source/freshness table |

## Planned agent design

Every agent in this folder follows the same contract as v1 — one
CloudFormation stack per agent, deployed independently — plus these
improvements:

- **Read-only.** Tools limited to `use_aws` (only `describe*` / `list*` / `get*`)
  and `query_cloudwatch_logs`. No agent can modify, stop, or delete a resource.
- **Detection from real-time state + historical utilization.** Service APIs for
  configuration/state, CloudWatch metrics over a configurable lookback window to
  prove idleness rather than guess it.
- **Bill-accurate costing.** Cost Explorer for actual billed amounts, with the
  cost window ending yesterday (the current day is excluded because its data is
  incomplete), the AWS `Estimated` provisional flag surfaced, and public list
  pricing used only as a labeled fallback.
- **Mismatch reconciliation.** Real-time inventory and T-1 cost data can
  legitimately disagree; findings are classified as *matched*, *too new to cost*,
  or *already gone* rather than reported as contradictions or false zeros.
- **Transparent methodology.** Each report opens with a tentative-cost disclaimer
  and a data-freshness header, and closes with a plain-language explanation of
  every data source used and how fresh it is.
- **Scope.** Resource-level waste and rightsizing only. No Savings Plans or
  Reserved Instance purchase recommendations.

## Prerequisites (same as v1)

1. An existing **AWS DevOps Agent Agent Space** — its ID is passed to every
   deploy.
2. **AWS CLI** configured with permission to create agents in that Agent Space
   (`aidevops:CreateAsset` plus trigger management).
3. For Cost Explorer costing, the Agent Space execution role also needs
   `ce:GetCostAndUsage` (and `ce:GetCostAndUsageWithResources` /
   `ce:GetAnomalies` where used). Without it, agents fall back to list pricing
   and note the gap in their report caveats.

## Contents

Templates will be added here as services are covered. Until then, use
[`../custom-agents-v1/`](../custom-agents-v1/).
