# AWS DevOps Agent — Cost Optimization Custom Agents

Ready-to-deploy **cost optimization custom agents** for
[AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/).

Each agent is a standalone CloudFormation stack that installs one read-only
agent into your Agent Space. The agent inspects your AWS resources on a schedule
and produces a cost optimization report ranked by estimated savings. Agents
observe and recommend — they never change, stop, or delete anything.

## Repository contents

| Folder | What it is | Status |
|---|---|---|
| [`custom-agents-v1/`](custom-agents-v1/) | The current catalog — **54 agents** (10 cross-service resource-level checks + 44 per-service). Deployable today. | ✅ Ready to use |
| [`custom-agents-cost-optimization/`](custom-agents-cost-optimization/) | Next-generation catalog expanding to **full AWS service coverage**, with Cost Explorer based (bill-accurate) costing. | 🚧 In development |

**Start here:** [`custom-agents-v1/`](custom-agents-v1/) — see its
[README](custom-agents-v1/README.md) for the agent list, deployment commands,
and scheduling options.

## Quick start

```bash
git clone https://github.com/satishshedge/AWSDevOpsAgent
cd AWSDevOpsAgent/custom-agents-v1

# See the available agents
./deploy.sh --list

# Deploy one agent
aws cloudformation deploy \
  --template-file unattached-ebs-volumes.yaml \
  --stack-name devops-agent-cost-unattached-ebs-volumes \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

Full deployment, scheduling, and management instructions are in the
[`custom-agents-v1/` README](custom-agents-v1/README.md).

## Prerequisites

1. An existing **AWS DevOps Agent Agent Space** (note its ID and Region).
2. **AWS CLI** configured with permission to create agents in that Agent Space
   (`aidevops:CreateAsset` plus trigger management).

## What the agents cover

**Resource-level (cross-service waste):** unattached EBS volumes, idle Elastic
IPs, aged/orphaned snapshots, idle EC2, unused load balancers, idle RDS,
orphaned resources (NAT gateways, ENIs, AMIs, empty ASGs), Compute Optimizer
rightsizing, S3 storage optimization, serverless over-provisioning.

**Per-service:** EKS, ECS/Fargate, Auto Scaling, Elastic Beanstalk, Batch,
Lightsail, Aurora, RDS (MySQL/PostgreSQL/MariaDB/Oracle/SQL Server), DynamoDB,
ElastiCache, MemoryDB, Redshift, DocumentDB, Neptune, Keyspaces, Timestream,
EFS, FSx, Backup, Storage Gateway, CloudFront, Route 53, Global Accelerator,
Transit Gateway, VPC endpoints, Direct Connect/VPN, EMR, Glue, Athena, Kinesis,
MSK, OpenSearch, MWAA, API Gateway, Step Functions, SQS/SNS, AppSync, SageMaker,
Bedrock, CloudWatch Logs.

## Safety

Every agent is read-only by design:

- Tools are limited to `use_aws` (restricted to `describe*` / `list*` / `get*`)
  and `query_cloudwatch_logs`.
- All resources are treated as production. Findings are reported with the
  evidence behind them; remediation is presented as suggested commands for your
  team to review and run, never executed.
- Reports exclude Savings Plans and Reserved Instance purchase recommendations —
  scope is resource-level waste and rightsizing.

Cost figures are estimates for prioritization, not billed invoice amounts.
