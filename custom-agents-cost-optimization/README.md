# Cost Optimization Custom Agents — full AWS service coverage

**187 read-only cost optimization custom agents** for
[AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/) —
one per AWS service that has meaningful cost levers, following the breadth model
of [aws-samples/sample-ai-agent-skills](https://github.com/aws-samples/sample-ai-agent-skills).

Each agent is a standalone CloudFormation stack. It detects waste from real-time
resource state plus CloudWatch metrics, then prices every finding against **what
your account was actually billed** using Cost Explorer — not public list prices.

## What each agent produces

An artifact titled:

```
<Service> Optimization Report - YYYY-MM-DD HH:MM UTC
```

The run timestamp is part of the title, so **every run is retained as its own
version** rather than overwriting the previous report.

Each report contains, in order:

1. **Disclaimer** — costs are tentative estimates, not invoice amounts.
2. **Data freshness header** — inventory timestamp, metrics window, cost window,
   and whether AWS still marks the cost data provisional.
3. **Executive summary** — billed cost observed, projected monthly/annual savings,
   split between billed-data-backed and list-price estimates.
4. **Findings table** — sorted by projected monthly savings, with the evidence,
   cost source, as-of date and a recommended (non-executed) action per finding.
5. **Reconciliation notes** — explains findings where live inventory and cost data
   disagree.
6. **Caveats** — data gaps, missing permissions, commitment-coverage uncertainty.
7. **How this report calculated cost** — a data-source table and plain-language
   explanation of what is real-time, what lags, and what is estimated.

## How costing works (and why it is more accurate)

| Data source | Used for | Freshness |
|---|---|---|
| `use_aws` — service APIs | Detecting waste: what exists, its size/type/state | **Real-time** as of the run |
| CloudWatch metrics | Proving idle / over-provisioned | **Historical window** (default 14 days) |
| Cost Explorer | Actual billed cost and savings projections | **Lags ~1 day**; provisional until the bill closes |
| Price List API | Fallback when billed data is unavailable | Current **public list price** |

Three behaviours are built into every agent to keep the numbers honest:

- **The cost window always ends yesterday.** Cost Explorer data for the current
  day is incomplete and reads near-zero, so including it would understate cost.
- **The provisional flag is surfaced.** AWS marks cost data estimated until the
  billing period closes; reports say when that applies.
- **Inventory/cost mismatches are reconciled, not hidden.** Findings are
  classified as *matched*, *too new to cost* (live resource with no cost yet — never
  reported as "$0 savings"), or *already gone* (cost with no live resource — never
  recommended for deletion).

## Safety

- Tools are limited to `use_aws` (restricted to `describe*` / `list*` / `get*`)
  and `query_cloudwatch_logs`. No agent can create, modify, stop or delete
  anything.
- All resources are treated as production. Remediation is presented as suggested
  commands for your team to review and run — never executed.
- No Savings Plans or Reserved Instance purchase recommendations; scope is
  resource-level waste and rightsizing.

## Prerequisites

1. An existing **AWS DevOps Agent Agent Space** — note its ID and Region.
2. **AWS CLI** configured with permission to create agents in that Agent Space
   (`aidevops:CreateAsset` plus trigger management).
3. For bill-accurate costing, the **Agent Space execution role** needs
   `ce:GetCostAndUsage` (plus `ce:GetCostAndUsageWithResources` and
   `ce:GetAnomalies` where used). Without it, agents fall back to list pricing and
   record the gap in their report caveats rather than failing.

## Deploying

### One agent

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-costopt-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

### Several at once

```bash
./deploy.sh --list                                    # show all 187 agent keys

./deploy.sh --agent-space-id <AGENT_SPACE_ID> \       # deploy a chosen few
  dynamodb elasticache rds-instances

./deploy.sh --agent-space-id <AGENT_SPACE_ID>         # deploy every agent

./deploy.sh --agent-space-id <AGENT_SPACE_ID> --dry-run dynamodb   # preview only
```

> **Deploying all 187 creates 187 stacks and 187 scheduled agents.** Start with
> the services you actually run, and consider `--trigger-status Inactive` on a
> first pass.

### Running alongside `custom-agents-v1/`

38 service keys exist in both catalogs. To keep them from colliding, this catalog
defaults to the stack prefix **`devops-agent-costopt-`** while `custom-agents-v1/`
uses `devops-agent-cost-`. Both can be deployed in the same Agent Space; agent
names also differ, so nothing is overwritten. Override with `--stack-prefix` if
you prefer your own convention.

## Scheduling and turning agents on or off

```bash
# install but do not run yet
--parameter-overrides AgentSpaceId=<ID> TriggerStatus=Inactive

# turn the schedule on
--parameter-overrides AgentSpaceId=<ID> TriggerStatus=Active

# daily / weekly / monthly
--parameter-overrides AgentSpaceId=<ID> ScheduleExpression="rate(1 day)"
--parameter-overrides AgentSpaceId=<ID> ScheduleExpression="rate(7 days)"
--parameter-overrides AgentSpaceId=<ID> ScheduleExpression="cron(0 8 1 * ? *)"
```

With `deploy.sh`, use `--trigger-status` and `--schedule` to apply the same
setting across a whole run.

## Parameter reference

| Parameter | Purpose | Default |
|---|---|---|
| `AgentSpaceId` | Agent Space that will own the agent. **Required.** | — |
| `ScheduleExpression` | How often the agent runs (`rate()` / `cron()`, UTC). | `rate(7 days)` |
| `TriggerStatus` | `Active` runs on schedule; `Inactive` installs without running. | `Active` |
| `CostLookbackDays` | Days of Cost Explorer history to pull, ending yesterday. | `30` |
| `LookbackDays` | Days of CloudWatch data for utilization checks. Present only on agents that analyze utilization. | `14` |

## Managing an agent

- **Update** (schedule, lookback, on/off): redeploy the same stack with new
  `--parameter-overrides`.
- **Pause**: redeploy with `TriggerStatus=Inactive`; the agent stays installed and
  can still be run on demand from the DevOps Agent web app.
- **Remove**: delete just that agent's stack.

```bash
aws cloudformation delete-stack \
  --stack-name devops-agent-costopt-dynamodb --region <REGION>
```

## Optional: attach service skills

Every service maps to its matching `<service>-troubleshooting` skill from
[aws-samples/sample-ai-agent-skills](https://github.com/aws-samples/sample-ai-agent-skills)
(recorded in `services-full.json`). Attaching one gives an agent deeper domain
context but is **not required** — the prompts work standalone.

The `skills:` line is emitted **commented out**, because a custom agent that
references a skill name not present in your Agent Space fails to create. To
enable: import the skills, set `USE_SKILLS = True` in `generate.py`, regenerate,
and redeploy.

## Coverage

Compute and containers, databases, storage and backup, networking and content
delivery, analytics and streaming, application integration, ML and AI, security,
operations and observability, media, IoT, migration and transfer, end-user
computing, and developer tools.

Services with no meaningful cost surface (for example IAM, Organizations, Control
Tower, Service Quotas, Health Dashboard, Resource Explorer) are intentionally
excluded. Run `./deploy.sh --list` for the definitive list of agent keys.
