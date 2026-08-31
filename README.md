# AWS Cost Optimization Agents for AWS DevOps Agent

A library of ready-to-deploy **cost optimization custom agents** for
[AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/).
Each agent is packaged as its own CloudFormation stack, so you can pick exactly
the agents you want, deploy them into your Agent Space, and have them
continuously surface where you're wasting money on AWS.

## What these stacks are

Each stack installs one **custom agent** into your AWS DevOps Agent Agent Space.
A custom agent is a specialized, autonomous agent with a focused job — here,
finding cost savings for one area of AWS. Every agent in this library:

- is **read-only** — it inspects your resources (`describe` / `list` / `get`)
  and reads CloudWatch metrics, and it **never changes, stops, or deletes
  anything**;
- produces a **cost optimization report** as a DevOps Agent artifact, with
  findings ranked by estimated monthly (and annual) savings and a recommended
  (non-executed) action for each;
- runs **on a schedule you choose**, so savings opportunities show up on their
  own instead of waiting for a manual review.

## Why they're useful in AWS DevOps Agent

AWS DevOps Agent already knows your accounts, resources, and telemetry. These
stacks turn that into an ongoing cost practice:

- **Continuous, hands-off cost review.** Scheduled agents re-scan on their own,
  so waste (idle instances, unattached volumes, over-provisioned databases,
  orphaned resources) is caught as it appears.
- **Focused, per-area agents.** Instead of one giant report, each agent covers a
  single service or resource type, so the output is specific and actionable and
  you deploy only what's relevant to your stack.
- **Safe by design.** Every agent is read-only and treats all resources as
  production, so you can run them broadly without risk. Remediation is presented
  as suggested commands for your team to review and run.
- **Prioritized by savings.** Reports lead with the highest-impact opportunities
  so you act on the biggest wins first.

## What's in the library

All agent templates live at the root of this repository and fall into two
groups. Deploy any of them, mix and match freely.

### Resource-level agents — cross-service waste (10 agents)

Cross-service checks for the most common sources of waste:

| Agent | Finds |
|---|---|
| `unattached-ebs-volumes` | EBS volumes not attached to anything |
| `unassociated-elastic-ips` | Elastic IPs that are idle or unassociated |
| `old-ebs-snapshots` | Aged / orphaned EBS snapshots |
| `idle-ec2-instances` | Long-stopped or low-utilization EC2 |
| `unused-load-balancers` | ALB/NLB/CLB with no targets or traffic |
| `idle-rds-instances` | RDS databases with little/no activity |
| `orphaned-resources` | Unused NAT gateways, ENIs, AMIs, empty ASGs |
| `rightsizing-compute-optimizer` | Over-provisioned EC2/EBS/ASG (Compute Optimizer) |
| `s3-storage-optimization` | Missing lifecycle rules, cold data, incomplete uploads |
| `serverless-overprovisioning` | Idle/over-provisioned Lambda & DynamoDB |

### Per-service agents — per-service deep dives (44 agents)

One cost agent per AWS service with meaningful cost levers, across compute &
containers (EKS, ECS/Fargate, Auto Scaling, Elastic Beanstalk, Batch,
Lightsail), databases (Aurora, RDS MySQL/PostgreSQL/MariaDB/Oracle/SQL Server,
DynamoDB, ElastiCache, MemoryDB, Redshift, DocumentDB, Neptune, Keyspaces,
Timestream), storage (EFS, FSx, Backup, Storage Gateway), networking
(CloudFront, Route 53, Global Accelerator, Transit Gateway, VPC endpoints,
Direct Connect/VPN), analytics (EMR, Glue, Athena, Kinesis, MSK, OpenSearch,
MWAA), app & integration (API Gateway, Step Functions, SQS/SNS, AppSync), ML
(SageMaker, Bedrock), and CloudWatch Logs.

To see every deployable agent key, run `./deploy.sh --list` from the root of
this repository.

## Before you start

You need:

1. An existing **AWS DevOps Agent Agent Space** — you'll pass its ID to every
   deploy. Note the Agent Space ID and the AWS Region it's in.
2. **AWS CLI** installed and configured with permission to create the agent
   (the `aidevops:CreateAsset` action and trigger management) in that Agent
   Space.

## Deploying an individual agent

Every agent is a standalone CloudFormation stack. Deploy just the one you want
by pointing at its template and passing your Agent Space ID:

```bash
aws cloudformation deploy \
  --template-file unattached-ebs-volumes.yaml \
  --stack-name devops-agent-cost-unattached-ebs-volumes \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

A per-service agent deploys exactly the same way — just point at its template:

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-cost-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

When the stack finishes, the agent appears in your Agent Space and its outputs
include the agent's asset ID and ARN.

### Deploying several at once

The catalog includes a helper script to deploy a chosen set:

```bash
./deploy.sh --list                                  # show available agent keys

./deploy.sh --agent-space-id <AGENT_SPACE_ID> \     # deploy a chosen few
  unattached-ebs-volumes old-ebs-snapshots idle-ec2-instances

./deploy.sh --agent-space-id <AGENT_SPACE_ID>       # deploy every agent
```

## Turning the schedule on or off

Each agent runs on a schedule via a trigger. Control it with the
`TriggerStatus` parameter — no template editing required.

**Deploy an agent but keep it off** (install now, run manually later from the
DevOps Agent web app, or turn on when ready):

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-cost-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> TriggerStatus=Inactive \
  --region <REGION>
```

**Turn the schedule on** (or back on) — redeploy the same stack with
`TriggerStatus=Active`:

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-cost-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> TriggerStatus=Active \
  --region <REGION>
```

With the `deploy.sh` helper, add `--trigger-status Inactive` (or `Active`) to
apply it to everything in the run.

## Choosing how often an agent runs

Set the `ScheduleExpression` parameter to any EventBridge `rate()` or `cron()`
expression. All times are UTC.

**Every day** (once every 24 hours):

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-cost-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="rate(1 day)" \
  --region <REGION>
```

**Every week**:

```bash
aws cloudformation deploy \
  --template-file dynamodb.yaml \
  --stack-name devops-agent-cost-dynamodb \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="rate(7 days)" \
  --region <REGION>
```

**Once a month** — either a 30-day rate, or a fixed calendar day with `cron()`:

```bash
# every 30 days
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="rate(30 days)"

# 08:00 UTC on the 1st of each month
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="cron(0 8 1 * ? *)"
```

**A specific day and time each week** — e.g. Mondays at 08:00 UTC:

```bash
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> ScheduleExpression="cron(0 8 ? * MON *)"
```

You can combine parameters, for example deploy on a monthly schedule but keep it
off until you're ready:

```bash
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
                      ScheduleExpression="rate(30 days)" \
                      TriggerStatus=Inactive
```

Some agents that analyze utilization also accept a `LookbackDays` parameter (how
many days of CloudWatch data to consider, default `14`):

```bash
--parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> LookbackDays=30
```

## Using the agents

Once deployed and `Active`, an agent runs on its schedule and writes its cost
optimization report as an artifact in your Agent Space — open the agent in the
DevOps Agent web app to read the latest report. You can also open any deployed
agent there and **run it on demand** at any time, regardless of its schedule.

## Managing an agent

- **Update** (change schedule, lookback, or on/off): redeploy the same stack
  with new `--parameter-overrides`.
- **Pause**: redeploy with `TriggerStatus=Inactive` — the agent stays installed
  and can still be run manually.
- **Remove**: delete just that agent's stack; the others are untouched.

```bash
aws cloudformation delete-stack \
  --stack-name devops-agent-cost-dynamodb --region <REGION>
```

## Parameter reference

| Parameter | Purpose | Default |
|---|---|---|
| `AgentSpaceId` | The Agent Space that will own the agent. **Required.** | — |
| `ScheduleExpression` | How often the agent runs (`rate()` / `cron()`, UTC). | `rate(7 days)` |
| `TriggerStatus` | `Active` runs on schedule; `Inactive` installs without auto-running. | `Active` |
| `LookbackDays` | Days of CloudWatch data for utilization checks (agents that use metrics). | `14` |
