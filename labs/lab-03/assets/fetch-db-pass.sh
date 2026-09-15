#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Lab 03 -- fetch the DB password from Key Vault with the VM's managed identity.
#
# Installed at /usr/local/bin/fetch-db-pass.sh on vm-web-01 (chmod 700).
# Runs as ExecStartPre for links.service (see 10-keyvault.conf). Writes
# DB_PASS to /run/links/db.env -- /run is tmpfs, so the password exists in
# RAM only: never on disk, never in a disk image or backup, gone on reboot.
#
# No credential appears anywhere in this file. The IMDS endpoint
# (169.254.169.254) is link-local -- only this VM can reach it -- and the
# token it hands back is Azure vouching "this request is vm-web-01."
# Key Vault then checks RBAC (Key Vault Secrets User) before answering.
#
# Uses only curl + python3 (both already on the VM) -- no SDK, no agent.
# ---------------------------------------------------------------------------
set -euo pipefail

VAULT="kv-lab03-cam"       # Key Vault name (locked values table)
SECRET="DbAppPassword"     # secret name in the vault

# 1) Ask the Azure Instance Metadata Service for a Key Vault-scoped token.
TOKEN=$(curl -sf -H Metadata:true \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fvault.azure.net" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2) Trade the token for the secret value, over TLS.
VALUE=$(curl -sf -H "Authorization: Bearer ${TOKEN}" \
  "https://${VAULT}.vault.azure.net/secrets/${SECRET}?api-version=7.4" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["value"])')

# 3) Write it where only root can read it, in RAM.
install -d -m 700 /run/links
umask 077
printf 'DB_PASS=%s\n' "${VALUE}" > /run/links/db.env
