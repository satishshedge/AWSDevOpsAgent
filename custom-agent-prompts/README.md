# AWS DevOps Agent cost-optimization prompts

This folder contains **187 GitHub-importable Markdown system prompts**, one per
AWS service with meaningful cost-optimization levers.

Use this option when you prefer to create an agent from the AWS DevOps Agent web
app rather than deploy a CloudFormation stack. Each `.md` file is the complete
system prompt for one service-specific cost optimization agent.

> Choose **one creation approach per service**: import a prompt from this folder
> or deploy that service's stack from `../custom-agent-cloudformation-stacks/`.
> Both approaches use the same `cost-<service>` agent naming convention, so
> creating both in the same Agent Space would create a duplicate-name conflict.

## Import a prompt from GitHub

1. Open the AWS DevOps Agent web app and select your **Agent Space**.
2. Go to **Agents** → **Custom Agents** → **Create agent** → **Import**.
3. Give the agent a lowercase, hyphenated name. Use `cost-<service-key>`, for
   example `cost-ec2-instances`.
4. Paste the raw GitHub URL for the service prompt. For example:

   ```text
   https://raw.githubusercontent.com/satishshedge/AWSDevOpsAgent/main/custom-agent-prompts/ec2-instances.md
   ```

5. Choose **Import agent**.
6. Use the agent's **Chat** experience to add its tools (required; see below).

The prompt import supplies the system prompt only. The web app keeps the source
link and lets you sync updates from GitHub later.

## Required tool selection

After importing, ask Chat to attach these read-only tools to the agent:

```text
Add the use_aws and query_cloudwatch_logs tools to my cost-ec2-instances agent.
```

Every prompt expects these tools:

| Tool | Why it is needed |
|---|---|
| `use_aws` | Reads current service configuration/state and Cost Explorer data. The prompt permits only `describe*`, `list*`, and `get*` operations. |
| `query_cloudwatch_logs` | Reads CloudWatch utilization/activity evidence to prove a resource is idle or over-provisioned. |

The Agent Space execution role also needs Cost Explorer read permissions
(`ce:GetCostAndUsage`, `ce:GetCostAndUsageWithResources`, and `ce:GetAnomalies`
where applicable). If it lacks those permissions, the prompt requires a clearly
labeled Price List fallback instead of failing.

## Prompt defaults

CloudFormation templates normally substitute deployment parameters into their
prompts. A GitHub prompt import has no CloudFormation parameter resolver, so the
Markdown prompts use the equivalent defaults directly:

| Setting | Default in imported prompts |
|---|---|
| CloudWatch utilization lookback | 14 days (services that use utilization metrics) |
| Cost Explorer history | 30 days, ending yesterday |
| Scheduled trigger | None — configure scheduling in the web app if desired |

You can fork this repository and change a prompt before importing it if your
organization needs a different default. The prompts explicitly state the actual
window used in each generated report.

## What the reports do

Every imported prompt creates a report named:

```text
<Service> Optimization Report - YYYY-MM-DD HH:MM UTC
```

The timestamp prevents later runs from replacing earlier artifacts. Each report:

- starts with a disclaimer that savings are tentative estimates, not billed
  invoice amounts;
- uses real-time AWS API configuration/state to find waste;
- uses CloudWatch metrics as historical utilization evidence where relevant;
- uses Cost Explorer billed data through **yesterday** (never the incomplete
  current day) and states whether AWS marks it provisional;
- reconciles live inventory against T-1 cost data as *matched*, *too new to
  cost*, or *already gone*;
- falls back to public Price List pricing only when billed data is unavailable;
- ends with a plain-language "How this report calculated cost" table describing
  every source and its freshness.

All prompts are read-only. They never modify, stop, or delete AWS resources, and
they exclude Savings Plans and Reserved Instance purchase recommendations.

## Service files

Each filename is the service key used by both the prompt import and CloudFormation
catalogs. Examples:

| Service | Prompt file |
|---|---|
| EC2 | [`ec2-instances.md`](ec2-instances.md) |
| EKS | [`eks-clusters.md`](eks-clusters.md) |
| DynamoDB | [`dynamodb.md`](dynamodb.md) |
| RDS | [`rds-instances.md`](rds-instances.md) |
| S3 | [`s3-storage.md`](s3-storage.md) |
| CloudWatch Logs | [`cloudwatch-logs.md`](cloudwatch-logs.md) |

Browse this folder for all 187 prompts. Coverage spans compute and containers,
storage, databases, networking, analytics, application integration, ML/AI,
security, observability, media, IoT, migration, end-user computing, and
developer tools.
