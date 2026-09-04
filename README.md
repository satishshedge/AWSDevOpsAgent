# AWS DevOps Agent — Cost Optimization Custom Agents

Ready-to-deploy **cost optimization custom agents** for
[AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/).

Each agent is a standalone CloudFormation stack that installs one read-only
agent into your Agent Space. The agent inspects your AWS resources on a schedule
and produces a cost optimization report ranked by estimated savings. Agents
observe and recommend — they never change, stop, or delete anything.

## Repository contents

| Folder | What it is | Best for |
|---|---|---|
| [`custom-agent-cloudformation-stacks/`](custom-agent-cloudformation-stacks/) | **187 deployment-only CloudFormation stacks**, plus the manifest and batch deployment helper. | Creating complete agents with tools and schedules through IaC. |
| [`custom-agent-prompts/`](custom-agent-prompts/) | **187 GitHub-importable Markdown prompts**, one per service. | Creating an agent interactively from the DevOps Agent web app. |
| [`custom-agents-v1/`](custom-agents-v1/) | Earlier 54-agent catalog using list-price oriented prompts. | Existing v1 users and backward compatibility. |
| [`custom-agents-cost-optimization/`](custom-agents-cost-optimization/) | Full 187-service Cost Explorer catalog source. | Catalog source and advanced maintenance. |

## Choose an end-user option

### Option 1: deploy a CloudFormation stack

Use [`custom-agent-cloudformation-stacks/`](custom-agent-cloudformation-stacks/)
when you want the complete agent, tool selection, and schedule created in one
CloudFormation deployment.

```bash
git clone https://github.com/satishshedge/AWSDevOpsAgent
cd AWSDevOpsAgent/custom-agent-cloudformation-stacks

# See the available service keys
./deploy.sh --list

# Deploy one agent
aws cloudformation deploy \
  --template-file ec2-instances.yaml \
  --stack-name devops-agent-costopt-ec2-instances \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

### Option 2: import a GitHub prompt

Use [`custom-agent-prompts/`](custom-agent-prompts/) when you want to create an
agent from the DevOps Agent web app. For example, import:

```text
https://raw.githubusercontent.com/satishshedge/AWSDevOpsAgent/main/custom-agent-prompts/ec2-instances.md
```

After import, use the agent's Chat experience to attach `use_aws` and
`query_cloudwatch_logs`. The prompt catalog README has the full import and tool
selection instructions.

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
