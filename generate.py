#!/usr/bin/env python3
"""
Generate one CloudFormation template per service-specific cost-optimization
custom agent, from services.json.

Each generated template matches the shape of the hand-written resource-level
templates in this same cost-agents/ folder:
  - Parameters: AgentSpaceId, ScheduleExpression, TriggerStatus
                (+ LookbackDays when the service uses utilization metrics)
  - AWS::DevOpsAgent::Asset (custom_agent) with read-only tools use_aws +
    query_cloudwatch_logs and an embedded AGENT.md system prompt
  - AWS::DevOpsAgent::Trigger (TIME_BASED) referencing the agent
  - Outputs: AgentAssetId, AgentArn

Skills: the matching <service>-troubleshooting skill is emitted only when
USE_SKILLS is true AND the skill has been imported into your Agent Space
(a skill referenced by name that does not exist makes CreateAsset fail).
By default it is written as a commented hint so deploys work out of the box.

Usage:
  python3 generate.py            # write templates + manifest
  python3 generate.py --check    # write to a temp check, print summary only

Output: <service>.yaml files in this directory, and agents.manifest.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "services.json")

# Set True only after importing the matching skills into your Agent Space.
USE_SKILLS = False

PROMPT_INDENT = " " * 12  # AGENT.md ContentText body indent (matches hand-written)


def block(text, indent):
    """Indent every line of text by `indent` spaces (blank lines stay blank)."""
    out = []
    for line in text.split("\n"):
        out.append(indent + line if line.strip() else "")
    return "\n".join(out)


def build_prompt(svc):
    lb = svc.get("lookback", False)
    window = " over the last ${LookbackDays} days" if lb else ""
    approach_lines = "\n".join(f"{i+1}. {step}" for i, step in enumerate(svc["approach"]))

    constraints = [
        "- Read-only only: run only `describe*`, `list*`, `get*`. Never create,",
        "  modify, delete, stop, resize, or otherwise mutate anything.",
        "- Always assume production. Report the evidence behind each finding and",
        "  never assume a resource is safe to change or remove.",
        "- Record account ID and region on every finding.",
        "- Continue on errors: note missing-permission failures in Caveats and",
        "  keep scanning.",
        "- Do NOT include Savings Plans or Reserved Instance purchase",
        "  recommendations; this agent covers resource-level waste and rightsizing.",
    ]

    prompt = f"""You are the {svc['title']} agent. You observe and recommend; you
never change anything.

## Goal
{svc['goal']}

## Approach
Enumerate opted-in regions with `ec2 describe-regions` unless the user
narrows scope, then scan each region and account. Read utilization from
CloudWatch{window} where relevant. For every finding capture the resource
identifier, region, account ID, the supporting evidence, and an estimated
monthly (and annual) saving, querying `pricing get-products` when a precise
figure is needed and labeling estimates.

{approach_lines}

Savings levers to look for: {svc['levers']}.

## Constraints
{chr(10).join(constraints)}

## Output
Produce a single artifact titled "{svc['title']} Report" with:
1. Executive summary — total estimated monthly and annual savings, count of
   findings, accounts and regions scanned{', lookback window used' if lb else ''}.
2. Findings table sorted by estimated monthly savings (highest first):
   resource ID, region, account ID, evidence, estimated monthly savings,
   estimated annual savings, and a short recommended (non-executed) action.
3. Suggested manual actions — optional, clearly labeled "suggested manual
   actions — not executed". Text only.
4. Caveats — data gaps, missing permissions, estimation assumptions."""
    return prompt


def build_template(svc):
    lb = svc.get("lookback", False)
    # ContentText uses !Sub only when we must interpolate ${LookbackDays}.
    content_key = "!Sub |" if lb else "|"

    params = [
        "  AgentSpaceId:",
        "    Type: String",
        "    Description: The ID of the Agent Space that will own this custom agent.",
        "  ScheduleExpression:",
        "    Type: String",
        "    Default: rate(7 days)",
        "    Description: EventBridge rate() or cron() expression for the recurring run.",
        "  TriggerStatus:",
        "    Type: String",
        "    Default: Active",
        "    AllowedValues: [Active, Inactive]",
        "    Description: Set Inactive to deploy the agent without running it on a schedule.",
    ]
    if lb:
        params += [
            "  LookbackDays:",
            "    Type: String",
            '    Default: "14"',
            "    Description: Utilization lookback window in days for CloudWatch metrics.",
        ]

    # Metadata block: name, tools, optional skills.
    meta = [
        "      Metadata:",
        f"        name: {svc['agent']}",
        "        tools:",
        "          - use_aws",
        "          - query_cloudwatch_logs",
    ]
    if USE_SKILLS:
        meta += ["        skills:", f"          - {svc['skill']}"]
    else:
        meta += [
            f"        # skills:   # import '{svc['skill']}' into the Agent Space first, then enable",
            f"        #   - {svc['skill']}",
        ]

    prompt_body = block(build_prompt(svc), PROMPT_INDENT)

    tpl = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: >-
  AWS DevOps Agent custom agent (read-only) that generates {svc['title']}
  recommendations. Deployed as its own stack so it can be picked independently
  from the service cost-optimizer catalog.

Parameters:
{chr(10).join(params)}

Resources:
  Agent:
    Type: AWS::DevOpsAgent::Asset
    Properties:
      AgentSpaceId: !Ref AgentSpaceId
      AssetType: custom_agent
{chr(10).join(meta)}
      Files:
        - Path: AGENT.md
          ContentText: {content_key}
{prompt_body}

  Schedule:
    Type: AWS::DevOpsAgent::Trigger
    Properties:
      AgentSpaceId: !Ref AgentSpaceId
      Type: TIME_BASED
      Condition:
        Schedule:
          Expression: !Ref ScheduleExpression
      Action:
        actionType: create:task
        task:
          agent: !Sub
            - custom:${{AssetId}}
            - AssetId: !GetAtt Agent.AssetId
      Status: !Ref TriggerStatus

Outputs:
  AgentAssetId:
    Description: The asset ID of the deployed custom agent.
    Value: !GetAtt Agent.AssetId
  AgentArn:
    Description: The ARN of the deployed custom agent.
    Value: !GetAtt Agent.Arn
"""
    return tpl


# Hand-written resource-level agents that live in this catalog but are NOT
# generated from services.json. Listed here so the manifest covers the whole
# catalog. Each has a matching <key>.yaml already present in this folder.
RESOURCE_LEVEL_KEYS = [
    "unattached-ebs-volumes",
    "unassociated-elastic-ips",
    "old-ebs-snapshots",
    "idle-ec2-instances",
    "unused-load-balancers",
    "idle-rds-instances",
    "orphaned-resources",
    "rightsizing-compute-optimizer",
    "s3-storage-optimization",
    "serverless-overprovisioning",
]


def main():
    check = "--check" in sys.argv
    spec = json.load(open(SPEC))
    services = spec["services"]

    manifest_lines = [
        "# Cost optimization agent catalog manifest",
        "# One line per agent: <stack-suffix>=<template-file>",
        "# Comment out any agent you do not want deploy.sh to deploy by default.",
        "",
        "# --- Resource-level agents (cross-service waste; hand-written templates) ---",
    ]
    for key in RESOURCE_LEVEL_KEYS:
        path = os.path.join(HERE, f"{key}.yaml")
        if not os.path.exists(path):
            print(f"WARNING: resource-level template missing: {key}.yaml")
        manifest_lines.append(f"{key}={key}.yaml")

    manifest_lines += [
        "",
        "# --- Per-service agents (generated from services.json) ---",
    ]

    written = 0
    for svc in services:
        tpl = build_template(svc)
        path = os.path.join(HERE, f"{svc['key']}.yaml")
        if not check:
            with open(path, "w") as f:
                f.write(tpl)
        manifest_lines.append(f"{svc['key']}={svc['key']}.yaml")
        written += 1

    if not check:
        with open(os.path.join(HERE, "agents.manifest"), "w") as f:
            f.write("\n".join(manifest_lines) + "\n")

    print(f"{'(check) ' if check else ''}generated {written} service templates"
          f" (+ {len(RESOURCE_LEVEL_KEYS)} resource-level in manifest)"
          f"{'; wrote agents.manifest' if not check else ''}; USE_SKILLS={USE_SKILLS}")


if __name__ == "__main__":
    main()
