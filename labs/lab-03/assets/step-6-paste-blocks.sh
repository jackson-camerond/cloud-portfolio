# ---------------------------------------------------------------------------
# Lab 03 -- Step 6 paste blocks for the Bastion terminal on vm-web-01.
# Keep this file open in VS Code during the shoot; copy ONE block at a time.
# Each block is self-contained (tee + heredoc) and matches the shoot script
# verbatim. No secrets appear in any block -- that's the whole point.
# ---------------------------------------------------------------------------

# ============ BLOCK A -- install the Key Vault fetch script ============
sudo tee /usr/local/bin/fetch-db-pass.sh > /dev/null <<'EOF'
#!/usr/bin/env bash
# Fetch the DB password from Key Vault using this VM's managed identity.
# Runs before the app starts; writes DB_PASS to /run/links/db.env --
# tmpfs, RAM only: never on disk, gone on reboot.
set -euo pipefail

VAULT="kv-lab03-cam"
SECRET="DbAppPassword"

# 1) Ask the Instance Metadata Service for a Key Vault token.
#    169.254.169.254 is link-local: only this VM can call it. Being the
#    VM is the authentication -- no credential involved anywhere.
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
EOF
sudo chmod 700 /usr/local/bin/fetch-db-pass.sh

# ============ BLOCK B -- systemd drop-in (extends, never edits, the unit) ===
sudo mkdir -p /etc/systemd/system/links.service.d
sudo tee /etc/systemd/system/links.service.d/10-keyvault.conf > /dev/null <<'EOF'
# Fetch the DB password from Key Vault before the app starts.
# EnvironmentFile lines stack -- this one loads AFTER /etc/app.env,
# so DB_PASS arrives from RAM, not from anything on disk. The leading
# "-" tolerates a missing file: on boot it doesn't exist until
# ExecStartPre runs the fetch.
[Service]
ExecStartPre=/usr/local/bin/fetch-db-pass.sh
EnvironmentFile=-/run/links/db.env
EOF

# ============ BLOCK C -- repoint /etc/app.env at Azure SQL (no password) ====
sudo cp /etc/app.env /etc/app.env.lab02.bak
sudo tee /etc/app.env > /dev/null <<'EOF'
# Managed database. No password in this file, on purpose.
# DB_PASS is fetched from Key Vault at service start by the VM's
# managed identity and lives only in RAM.
DB_HOST=sql-lab03-cam.database.windows.net
DB_PORT=1433
DB_USER=appuser
DB_NAME=sqldb-app
TDSVER=7.4
EOF

# ============ BLOCK D -- reload, restart, verify ============================
sudo systemctl daemon-reload
sudo systemctl restart links
systemctl status links --no-pager -n 5
curl -s http://127.0.0.1:8000/healthz

# ============ BLOCK E -- only after healthz says ok =========================
# The Lab 02 backup still holds the OLD password -- it goes too.
sudo rm /etc/app.env.lab02.bak
