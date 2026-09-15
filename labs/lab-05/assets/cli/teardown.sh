#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lab 05 — TEARDOWN.  Order matters: the LOCK must come off FIRST, or the
# resource-group delete is itself blocked by the very lock you created.
#
# ⚠️  Deletes ONLY rg-lab05-gov-cam and the junior-dev-cam user.
# ⚠️  NEVER targets rg-cloud-portfolio. (That group was deleted ~2026-07-03 for
#     the site redo, but the guard STAYS — the rebuilt site lands in this
#     subscription too, and this script must never be able to touch it.)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

RG="rg-lab05-gov-cam"
USER_UPN_PREFIX="junior-dev-cam"
ASSIGNMENT_NAME="Restrict-VM-Sizes"
INITIATIVE_NAME="Lab05-Governance-Baseline"
LOCK_NAME="lab05-delete-lock"

# Hard guard — refuse to run against the site's group, ever (kept even though
# the group is currently deleted; it comes back with the site redo).
if [[ "$RG" == "rg-cloud-portfolio" ]]; then
  echo "REFUSING: that is the site's group."; exit 1
fi

# 1. Remove the lock FIRST (otherwise every delete below is blocked).
az lock delete --name "$LOCK_NAME" --resource-group "$RG" || true

# 2. Remove the policy assignment, then the initiative (order: assignment first).
SUB_ID="$(az account show --query id -o tsv)"
RG_SCOPE="/subscriptions/${SUB_ID}/resourceGroups/${RG}"
az policy assignment delete --name "$ASSIGNMENT_NAME" --scope "$RG_SCOPE" || true
# The portal wizard auto-generates a GUID for the initiative's NAME (only the
# display name is "Lab05 Governance Baseline"), so look it up by display name.
# This also catches the CLI-created one ($INITIATIVE_NAME has the same display name).
INIT_NAME=$(az policy set-definition list \
  --query "[?displayName=='Lab05 Governance Baseline'].name" -o tsv)
if [[ -n "$INIT_NAME" ]]; then
  while IFS= read -r name; do
    az policy set-definition delete --name "$name" || true
  done <<< "$INIT_NAME"
fi
# az policy definition delete --name deny-public-ip || true   # if you created the custom one

# 3. Delete the lab resource group (kills the RG + budget + any leftovers).
az group delete --name "$RG" --yes --no-wait

# 4. Delete the junior-dev user so the directory stays clean (PDF step).
# NOTE (2026-07-11): Graph rejects a $filter on /domains, so fetch all + filter client-side.
TENANT_DOMAIN="$(az rest --method get \
  --url 'https://graph.microsoft.com/v1.0/domains' \
  --query "value[?isDefault].id | [0]" -o tsv)"
az ad user delete --id "${USER_UPN_PREFIX}@${TENANT_DOMAIN}" || true

echo "Lab 05 torn down. Only rg-lab05-gov-cam was targeted."
