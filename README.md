# AWS DevOps Agent Cost Optimization Custom Agents

Ready-to-use, **read-only** cost optimization custom agents for
[AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/).

Each agent inspects AWS resource configuration and CloudWatch utilization,
produces prioritized cost optimization findings, and never changes, stops, or
deletes AWS resources.

## Choose how to create an agent

### Option 1: Deploy with CloudFormation

Use [`custom-agent-cloudformation-stacks/`](custom-agent-cloudformation-stacks/)
when you want the full custom agent, its tools, and an optional scheduled trigger
created through Infrastructure as Code.

This folder includes **187 service-specific CloudFormation stacks**, a batch
deployment helper, and complete deployment/scheduling instructions.

```bash
git clone https://github.com/satishshedge/AWSDevOpsAgent
cd AWSDevOpsAgent/custom-agent-cloudformation-stacks

# List available service keys
./deploy.sh --list

# Deploy one agent
aws cloudformation deploy \
  --template-file ec2-instances.yaml \
  --stack-name devops-agent-costopt-ec2-instances \
  --parameter-overrides AgentSpaceId=<AGENT_SPACE_ID> \
  --region <REGION>
```

See the [CloudFormation stack README](custom-agent-cloudformation-stacks/README.md)
for multi-service deployment, trigger controls, scheduling, and cleanup.

### Option 2: Import a GitHub Markdown prompt

Use [`custom-agent-prompts/`](custom-agent-prompts/) when you prefer to create
an agent interactively in the AWS DevOps Agent web app.

This folder includes **187 service-specific Markdown prompts**. For example,
use this GitHub URL in **Agents → Custom Agents → Create agent → Import**:

```text
https://github.com/satishshedge/AWSDevOpsAgent/blob/main/custom-agent-prompts/ec2-instances.md
```

After importing, add the required read-only tools through the agent Chat
experience:

```text
Add the use_aws and query_cloudwatch_logs tools to my cost-ec2-instances agent.
```

See the [prompt import README](custom-agent-prompts/README.md) for the full
import flow, required permissions, defaults, and report behavior.

## What the reports provide

Every agent creates a timestamped optimization report such as:

```text
EC2 Optimization Report - YYYY-MM-DD HH:MM UTC
```

The timestamp means multiple runs are retained as separate artifacts. Reports
include:

- a clear disclaimer that savings are estimates, not invoice amounts;
- real-time resource configuration/state evidence;
- CloudWatch utilization/activity evidence;
- Cost Explorer cost data ending yesterday, with provisional-data status;
- reconciliation for resources that are too new to cost or already removed;
- a plain-language data-source and freshness explanation.

## Prerequisites

1. An existing **AWS DevOps Agent Agent Space**.
2. AWS CLI permissions to create custom-agent assets and triggers when using
   CloudFormation.
3. For bill-accurate Cost Explorer cost calculations, the Agent Space execution
   role needs Cost Explorer read permissions. Agents fall back to public Price
   List estimates and report the limitation when those permissions are absent.

## Safety

All agents are designed to be read-only:

- `use_aws` is limited by the prompts to `describe*`, `list*`, and `get*`
  operations.
- `query_cloudwatch_logs` is used for utilization/activity evidence.
- Agents recommend manual actions but never execute remediation.
- Savings Plans and Reserved Instance purchase recommendations are outside the
  scope of these agents.
