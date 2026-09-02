#!/usr/bin/env bash
#
# Deploy selected AWS Cost Optimizer custom agents to an AWS DevOps Agent
# Agent Space, one CloudFormation stack per agent.
#
# Each agent is independent: deploy any subset, redeploy to update, and delete
# a single stack to remove just that agent.
#
# USAGE
#   ./deploy.sh --agent-space-id <ID> [options] [agent ...]
#
# ARGUMENTS
#   agent ...   One or more agent keys (the left-hand side in agents.manifest,
#               e.g. old-ebs-snapshots). If omitted, every non-commented agent
#               in agents.manifest is deployed.
#
# OPTIONS
#   --agent-space-id <ID>   (required) Target Agent Space ID.
#   --region <REGION>       AWS region. Defaults to $AWS_REGION or us-east-1.
#   --schedule <EXPR>       Trigger schedule, e.g. "rate(7 days)" or
#                           "cron(0 8 ? * MON *)". Passed to every stack.
#   --trigger-status <S>    Active | Inactive. Deploy without auto-running by
#                           passing Inactive. Default: template default (Active).
#   --stack-prefix <P>      Stack name prefix. Default: devops-agent-costopt-.
#                           (Distinct from the custom-agents-v1 prefix so both
#                           catalogs can be deployed side by side.)
#   --list                  List available agent keys and exit.
#   --dry-run               Print the deploy commands without running them.
#   -h, --help              Show this help.
#
# EXAMPLES
#   # Deploy only the three EBS/EIP agents, inactive so they don't auto-run yet
#   ./deploy.sh --agent-space-id 8f61...757c --trigger-status Inactive \
#     unattached-ebs-volumes unassociated-elastic-ips old-ebs-snapshots
#
#   # Deploy every agent in the manifest on a Monday-morning schedule
#   ./deploy.sh --agent-space-id 8f61...757c --schedule "cron(0 8 ? * MON *)"
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/agents.manifest"

AGENT_SPACE_ID=""
REGION="${AWS_REGION:-us-east-1}"
SCHEDULE=""
TRIGGER_STATUS=""
STACK_PREFIX="devops-agent-costopt-"
DRY_RUN="false"
LIST_ONLY="false"
SELECTED=()

die() { echo "error: $*" >&2; exit 1; }

# --- parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent-space-id) AGENT_SPACE_ID="${2:-}"; shift 2 ;;
    --region)         REGION="${2:-}"; shift 2 ;;
    --schedule)       SCHEDULE="${2:-}"; shift 2 ;;
    --trigger-status) TRIGGER_STATUS="${2:-}"; shift 2 ;;
    --stack-prefix)   STACK_PREFIX="${2:-}"; shift 2 ;;
    --list)           LIST_ONLY="true"; shift ;;
    --dry-run)        DRY_RUN="true"; shift ;;
    -h|--help)        sed -n '2,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)               die "unknown option: $1" ;;
    *)                SELECTED+=("$1"); shift ;;
  esac
done

[[ -f "$MANIFEST" ]] || die "manifest not found: $MANIFEST"

# --- load manifest into parallel arrays (bash 3.2 compatible, no assoc arrays) ---
KEYS=()
TEMPLATES=()
while IFS= read -r line; do
  line="${line%%#*}"                      # strip comments
  line="$(echo "$line" | tr -d '[:space:]')"
  [[ -z "$line" ]] && continue
  KEYS+=("${line%%=*}")
  TEMPLATES+=("${line##*=}")
done < "$MANIFEST"

template_for() {
  local want="$1" i
  for i in "${!KEYS[@]}"; do
    [[ "${KEYS[$i]}" == "$want" ]] && { echo "${TEMPLATES[$i]}"; return 0; }
  done
  return 1
}

if [[ "$LIST_ONLY" == "true" ]]; then
  echo "Available agents:"
  for k in "${KEYS[@]}"; do echo "  - $k"; done
  exit 0
fi

[[ -n "$AGENT_SPACE_ID" ]] || die "--agent-space-id is required (see --help)"

# Default selection = every agent in the manifest
if [[ ${#SELECTED[@]} -eq 0 ]]; then
  SELECTED=("${KEYS[@]}")
fi

echo "Region:       $REGION"
echo "Agent Space:  $AGENT_SPACE_ID"
echo "Agents:       ${SELECTED[*]}"
echo

for key in "${SELECTED[@]}"; do
  template="$(template_for "$key")" || die "unknown agent '$key' (try --list)"
  template_path="${SCRIPT_DIR}/${template}"
  [[ -f "$template_path" ]] || die "template not found: $template_path"

  stack="${STACK_PREFIX}${key}"

  # Build parameter overrides. Only pass optional params when the caller set
  # them, so each template keeps its own defaults otherwise.
  params=("AgentSpaceId=${AGENT_SPACE_ID}")
  [[ -n "$SCHEDULE" ]]       && params+=("ScheduleExpression=${SCHEDULE}")
  [[ -n "$TRIGGER_STATUS" ]] && params+=("TriggerStatus=${TRIGGER_STATUS}")

  cmd=(aws cloudformation deploy
        --template-file "$template_path"
        --stack-name "$stack"
        --region "$REGION"
        --no-fail-on-empty-changeset
        --parameter-overrides "${params[@]}")

  echo ">> ${key}  (stack: ${stack})"
  if [[ "$DRY_RUN" == "true" ]]; then
    printf '   '; printf '%q ' "${cmd[@]}"; echo
  else
    "${cmd[@]}"
  fi
  echo
done

echo "Done."
