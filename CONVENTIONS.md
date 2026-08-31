# Shared conventions for the AWS Cost Optimizer agent catalog

Every agent in this catalog is a single-purpose AWS DevOps Agent **custom agent**, deployed
as its own CloudFormation stack so customers can pick and choose. All templates follow the
same shape so they are predictable to review and deploy.

## Resource model

Each template creates:

- One `AWS::DevOpsAgent::Asset` with `AssetType: custom_agent` — the agent itself
  (name, tools, and the system prompt embedded as an `AGENT.md` file).
- One `AWS::DevOpsAgent::Trigger` with `Type: TIME_BASED` — the recurring schedule that
  runs the agent. Its `Action.task.agent` references the agent via `custom:<AssetId>`
  using `Fn::GetAtt` so CloudFormation wires and orders the two resources.

## Shared parameters

| Parameter | Purpose | Default |
|---|---|---|
| `AgentSpaceId` | The Agent Space that owns the agent. Required. | — |
| `ScheduleExpression` | EventBridge `rate()` / `cron()` expression for the recurring run. | `rate(7 days)` |
| `TriggerStatus` | `Active` runs on schedule; `Inactive` deploys the agent without auto-running. | `Active` |

Deploying with `TriggerStatus=Inactive` lets a customer install an agent and run it
on demand from the web app before committing to a schedule.

## Tools (read-only)

Every agent is granted only read-only tools, consistent with the "observe and recommend,
never change" posture:

- `use_aws` — run read-only AWS CLI calls (`describe*`, `list*`, `get*`).
- `query_cloudwatch_logs` — read CloudWatch data for utilization / idle evidence.

No agent is granted a tool that can mutate AWS state. Remediation is emitted as
text ("suggested manual actions — not executed") for the customer to run themselves.

## System prompt structure

Each `AGENT.md` follows the same four sections:

1. **Goal** — the one category this agent covers, in a sentence.
2. **Approach** — the specific read-only calls to make, and the evidence to capture.
3. **Constraints** — read-only only, always-assume-production, continue-on-error,
   record account ID + region on every finding, and the exclusion of Savings Plans /
   Reserved Instance recommendations (this catalog is resource-level waste only).
4. **Output** — a single artifact with an executive summary, a findings table sorted by
   estimated monthly savings, and a caveats section.

## Naming

- Agent `name` metadata: `cost-<category>` (lowercase, hyphens, <=64 chars),
  e.g. `cost-unattached-ebs-volumes`.
- Template file: `<category>.yaml`, e.g. `unattached-ebs-volumes.yaml`.
- Stack name (suggested): `devops-agent-cost-<category>`.

## Prerequisites

- An existing Agent Space (with at least one connected integration) — pass its ID as
  `AgentSpaceId`.
- IAM permissions in the `aidevops:` namespace (at least `aidevops:CreateAsset` and
  the trigger-management actions) for whoever runs the deploy.
- Deploy in an AWS Region where AWS DevOps Agent is available.
