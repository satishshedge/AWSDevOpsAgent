# AWS DevOps Agent cost-optimization CloudFormation stacks

This folder contains **187 deployable CloudFormation templates**, one per AWS
service with meaningful cost-optimization levers.

Use this option when you want AWS CloudFormation to create the complete custom
agent for you: its name, read-only tool selection, system prompt, and optional
scheduled trigger.

## What a stack creates

Each `<service>.yaml` stack creates:

- An `AWS::DevOpsAgent::Asset` custom agent with the service-specific cost
  optimization prompt.
- A `TIME_BASED` `AWS::DevOpsAgent::Trigger` that can run the agent on a
  schedule.

Every agent is read-only. It uses `use_aws` for `describe*` / `list*` / `get*`
operations and `query_cloudwatch_logs` for utilization evidence. It never
changes, stops, or deletes AWS resources.

The generated reports use real-time resource state, CloudWatch utilization,
Cost Explorer billed-cost data through yesterday, and Price List fallback where
billed data cannot be attributed. Each report explains its sources, freshness,
and limitations.

## Prerequisites

1. An existing **AWS DevOps Agent Agent Space**. Note its ID and AWS Region.
2. The AWS CLI configured with permission to create the agent in that Agent
   Space (`aidevops:CreateAsset` and trigger-management permissions).
3. For Cost Explorer based costing, the Agent Space execution role needs:
   - `ce:GetCostAndUsage`
   - `ce:GetCostAndUsageWithResources` where resource-level data is needed
   - `ce:GetAnomalies` where anomaly context is needed

Without Cost Explorer access, an agent continues with a clearly labeled public
Price List estimate and records the access gap in its report.

## Deploy one service

From this folder, deploy the template for the service you use:

```bash
aws cloudformation deploy \
  --template-file ec2-instances.yaml \
  --stack-name devops-agent-costopt-ec2-instances \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

After CloudFormation reports `CREATE_COMPLETE`, open the agent in the AWS
DevOps Agent web app. Its report artifact title includes the UTC run timestamp,
so each run is retained separately.

## Deploy multiple services

`deploy.sh` reads `agents.manifest` and creates one stack per selected service.

```bash
# List all service keys
./deploy.sh --list

# Preview commands only
./deploy.sh --agent-space-id <AGENT_SPACE_ID> --region <REGION> --dry-run \
  ec2-instances dynamodb rds-instances

# Deploy a chosen set
./deploy.sh --agent-space-id <AGENT_SPACE_ID> --region <REGION> \
  ec2-instances dynamodb rds-instances

# Deploy every agent in this folder
./deploy.sh --agent-space-id <AGENT_SPACE_ID> --region <REGION>
```

> Deploying all templates creates 187 CloudFormation stacks and 187 scheduled
> custom agents. Start with services you actively use.

## Schedule and trigger controls

Each stack accepts these parameters:

| Parameter | Purpose | Default |
|---|---|---|
| `AgentSpaceId` | Agent Space that owns the custom agent. Required. | — |
| `ScheduleExpression` | EventBridge `rate()` or `cron()` schedule. | `rate(7 days)` |
| `TriggerStatus` | `Active` runs on schedule; `Inactive` installs without auto-running. | `Active` |
| `CostLookbackDays` | Cost Explorer history ending yesterday. | `30` |
| `LookbackDays` | CloudWatch utilization window. Only metric-based services expose it. | `14` |

Install an agent but keep its trigger off:

```bash
aws cloudformation deploy \
  --template-file ec2-instances.yaml \
  --stack-name devops-agent-costopt-ec2-instances \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> TriggerStatus=Inactive \
  --region <REGION>
```

Schedule an active agent every day, week, or calendar month:

```bash
# Every day
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="rate(1 day)"

# Every week
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="rate(7 days)"

# 08:00 UTC on the first day of every month
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="cron(0 8 1 * ? *)"
```

## Stack naming

The deployment helper defaults to the `devops-agent-costopt-` prefix. This is
intentionally different from the `custom-agents-v1/` catalog's prefix, so both
catalogs can be deployed into the same Agent Space without overwriting each
other.

## Manage a deployed agent

- Update a schedule or parameter by redeploying the same stack name.
- Pause a scheduled agent by redeploying with `TriggerStatus=Inactive`.
- Remove one agent without touching others:

```bash
aws cloudformation delete-stack \
  --stack-name devops-agent-costopt-ec2-instances \
  --region <REGION>
```

## Services

Run `./deploy.sh --list` for the definitive service-key list. Coverage spans
compute and containers, storage, databases, networking, analytics, application
integration, ML/AI, security, observability, media, IoT, migration, end-user
computing, and developer tools.
