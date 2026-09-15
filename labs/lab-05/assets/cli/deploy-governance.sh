#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lab 05 — Governance & Hardening  ·  CLI FALLBACK (only if the portal misbehaves)
#
# The shoot is portal-first (that's the teach). This script does the same thing
# from the CLI, one guardrail per block, each block saying what it does. Run the
# blocks in order; you can stop after any block.
#
# Cost: ~$0. RBAC, Azure Policy, Budgets and Locks are all FREE. The only thing
# that could cost money is a VM — and the whole point is that the policy REFUSES
# to create the oversized one, so nothing bills.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Pin the cwd to this script's directory so the @../policies/... paths in
# Block 4 resolve no matter where the script is launched from.
cd "$(dirname "$0")"

# ── Locked values (match the shoot script) ──────────────────────────────────
RG="rg-lab05-gov-cam"
LOCATION="eastus"
TAGS="env=lab owner=cam project=lab05"
USER_UPN_PREFIX="junior-dev-cam"           # domain is appended below
USER_DISPLAY="Junior Developer"
ASSIGNMENT_NAME="Restrict-VM-Sizes"        # matches the PDF's assignment name
INITIATIVE_NAME="Lab05-Governance-Baseline"
BUDGET_NAME="Monthly-Lab-Budget"
LOCK_NAME="lab05-delete-lock"

SUB_ID="$(az account show --query id -o tsv)"
RG_SCOPE="/subscriptions/${SUB_ID}/resourceGroups/${RG}"

# ── Block 1 — the playground (the container everything lands in) ─────────────
az group create -n "$RG" -l "$LOCATION" --tags $TAGS

# ── Block 2 — RBAC: a least-privilege "junior dev" who can only LOOK ─────────
# Create the user. (Password is prompted for so it never lands in shell history.)
# NOTE (2026-07-11): Graph rejects a $filter on /domains ("Filtered searches
# against this resource are not supported"), so fetch all and filter client-side.
TENANT_DOMAIN="$(az rest --method get \
  --url 'https://graph.microsoft.com/v1.0/domains' \
  --query "value[?isDefault].id | [0]" -o tsv)"
read -rsp "Password for ${USER_UPN_PREFIX}: " JR_PW; echo
az ad user create \
  --display-name "$USER_DISPLAY" \
  --user-principal-name "${USER_UPN_PREFIX}@${TENANT_DOMAIN}" \
  --password "$JR_PW" \
  --force-change-password-next-sign-in false
unset JR_PW
# Grant Reader on the LAB RG only — view everything, change nothing.
JR_OBJ_ID="$(az ad user show --id "${USER_UPN_PREFIX}@${TENANT_DOMAIN}" --query id -o tsv)"
az role assignment create --assignee-object-id "$JR_OBJ_ID" \
  --assignee-principal-type User --role "Reader" --scope "$RG_SCOPE"

# ── Block 3 — (optional) the custom deny-public-ip policy definition ─────────
# Only if you want the "wide-open" guardrail. NOTE: the teaching file is
# ../policies/deny-public-ip.json and it's commented JSONC — Azure rejects
# comments, so strip them (or extract the policyRule block to a clean file)
# before uncommenting. Skip this block for the reliable set.
# az policy definition create --name deny-public-ip \
#   --display-name "Deny public IP on network interfaces" \
#   --mode Indexed --rules @../policies/deny-public-ip.json   # strip // comments first

# ── Block 4 — the initiative (bundle the three built-in guardrails) ──────────
az policy set-definition create --name "$INITIATIVE_NAME" \
  --display-name "Lab05 Governance Baseline" \
  --definitions @../policies/governance-initiative.definitions.json \
  --params @../policies/governance-initiative.params.json
# NOTE: the .definitions.json / .params.json are the comment-free splits of
# governance-initiative.json (the JSONC teaching copy) — they live alongside it
# in ../policies/ and are what az actually accepts. If the initiative gives you
# trouble anyway, assign the single VM-SKU built-in (the PDF baseline) — Block 5b.

# ── Block 5 — assign the initiative to the LAB RG (NOT the subscription) ─────
# Scoping to the RG is deliberate: a subscription-wide DENY would also hit the
# live site's resource group. Guardrails on the lab, live site untouched.
az policy assignment create --name "$ASSIGNMENT_NAME" \
  --display-name "Restrict VM sizes + regions + tags" \
  --policy-set-definition "$INITIATIVE_NAME" \
  --scope "$RG_SCOPE" \
  --params '{
    "allowedSKUs":      { "value": ["Standard_B1s","Standard_B1ms"] },
    "allowedLocations": { "value": ["eastus","westus2"] },
    "requiredTag":      { "value": "owner" }
  }'

# ── Block 5b — FALLBACK: single built-in policy (matches the PDF exactly) ─────
# If the initiative gives you trouble, assign just the VM-size built-in:
# az policy assignment create --name "$ASSIGNMENT_NAME" \
#   --policy "cccc23c7-8427-4f53-ad12-b6a63eb452b3" --scope "$RG_SCOPE" \
#   --params '{ "listOfAllowedSKUs": { "value": ["Standard_B1s","Standard_B1ms"] } }'

# ── Block 6 — the budget ($50) — CLI creates the BUDGET ONLY ──────────────────
# This command sets no notifications: the 80%-actual EMAIL ALERT is configured in
# the portal (RG → Budgets → Monthly-Lab-Budget → alert conditions + recipient).
# Budgets via CLI are finicky anyway; the portal is the reliable path. Best-effort:
START="$(date +%Y-%m-01)"
END="$(date -v+1y +%Y-%m-01 2>/dev/null || date -d '+1 year' +%Y-%m-01)"
az consumption budget create --budget-name "$BUDGET_NAME" \
  --amount 50 --category cost --time-grain monthly \
  --start-date "$START" --end-date "$END" \
  --resource-group "$RG" || echo "Budget via CLI failed — create it in the portal."
echo "Budget created WITHOUT alerts — add the 80% actual email alert in the portal."

# ── Block 7 — resource lock: CanNotDelete on the LAB RG ──────────────────────
az lock create --name "$LOCK_NAME" --lock-type CanNotDelete \
  --resource-group "$RG" \
  --notes "Lab 05 delete-protection demo. Remove BEFORE teardown."

echo "Governance applied to ${RG}. Policy can take 15-30 min to enforce."
