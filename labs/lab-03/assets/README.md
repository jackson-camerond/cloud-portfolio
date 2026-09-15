# Lab 03, build assets

Config + migration files for **Modernizing to PaaS & Securing Secrets**. This lab
modernizes the **running Lab 02 stack live**: the SQL Server VM (`vm-db-01`) is replaced
by **Azure SQL Database**, the DB password comes off the server entirely (**Key Vault +
managed identity**, fetched into RAM at service start), and **Azure Monitor** proves the
managed database is alive. `labs/` is gitignored, none of this is published.

**The headline:** because Lab 02 put every DB value in `/etc/app.env` and ran SQL Server
(same wire protocol as Azure SQL), the app code does **not change**. The whole swap is
config: a new `app.env`, one fetch script, one systemd drop-in. Say the honest part too,
the delta isn't *zero files*, it's *zero code*: `app.py` and the pymssql driver are
untouched; what changes is environment + systemd wiring.

## Files

- `links-migration.sql`, run in the portal **Query editor** against `sqldb-app`:
  creates the least-privilege **contained user** `appuser` (reader/writer on this one
  DB), recreates `dbo.links` exactly as it was on `vm-db-01`, reseeds the `/azure` row.
  ⚠️ Replace `CHANGE_ME_APP_PASSWORD` off camera first.
- `fetch-db-pass.sh`, goes to `/usr/local/bin/fetch-db-pass.sh` on `vm-web-01`
  (chmod 700). IMDS token → Key Vault REST → writes `DB_PASS` to `/run/links/db.env`
  (tmpfs = RAM only). curl + python3 only, no SDK, no code change.
- `10-keyvault.conf`, systemd drop-in for
  `/etc/systemd/system/links.service.d/10-keyvault.conf`: `ExecStartPre` runs the fetch,
  a second stacked `EnvironmentFile` layers the RAM-only `DB_PASS` on top of
  `/etc/app.env`. The Lab 02 unit file itself is never edited.
- `app.env.lab03`, the new `/etc/app.env`: Azure SQL host + `sqldb-app` + `appuser` +
  `TDSVER=7.4`, and **no password line**. This file is the core artifact of the lab.
- `step-6-paste-blocks.sh`, the five Step 6 blocks (tee + heredoc) exactly as pasted
  into the Bastion terminal on camera. Open in VS Code during the shoot, copy one block
  at a time. Contains no secrets. The three files above are the readable canonical
  copies; **if you edit one, edit both.**

## Deploy order (matches the shoot)

0. **Lab 02 stack must be RUNNING** (`rg-lab02-cam`: `vm-web-01`, `vm-db-01`, Bastion).
   This lab modernizes it live, do not tear Lab 02 down first.
1. **Azure SQL Database**, create `sqldb-app` on new server `sql-lab03-cam` into new RG
   `rg-lab03-cam` (created inside the wizard), region **West US 2** (same as the VMs).
   **Basic / DTU / 5 DTU (~$5/mo)**, remove the free-offer banner first,
   **Workload environment = Development** (Production defaults to Hyperscale,
   $320+/mo). Networking: **Public endpoint**, **Allow Azure services = Yes**,
   **Add current client IP = Yes**. SQL auth, admin `sqladmin` (password off camera).
2. **Migrate the table**, Query editor on `sqldb-app` as `sqladmin` → paste
   `links-migration.sql` (password already substituted).
3. **Key Vault**, `kv-lab03-cam`, Standard, **RBAC** permission model, purge protection
   **disabled** (or teardown can't purge). Assign yourself **Key Vault Administrator**
   (RBAC = nobody has data-plane access by default, including the creator), wait for
   propagation, then create secret **`DbAppPassword`** = appuser's password.
4. **Managed identity**, `vm-web-01` → Identity → System assigned → **On** (Object ID
   appears). Then on the vault: IAM → add **Key Vault Secrets User** → Managed identity
   → `vm-web-01`. (Read-only on secret values, least privilege; the Administrator role
   stays with you.)
5. **Rewire `vm-web-01`** (shell via the Lab 02 **Bastion**, inbound NSG only allows 80,
   and that's a feature): install `fetch-db-pass.sh` + `10-keyvault.conf`, replace
   `/etc/app.env` with `app.env.lab03` (back up the old one first, delete the backup
   once healthy, it contains the old password), `systemctl daemon-reload && systemctl
   restart links`, then `curl -s http://127.0.0.1:8000/healthz` → `ok`.
6. **Prove it**, app works in the browser against Azure SQL; `cat /etc/app.env` shows
   no credential on the server.
7. **Decommission `vm-db-01`**, in `rg-lab02-cam` delete exactly three resources: the
   VM, its OS disk, its NIC. ⚠️ NOT the resource group, NOT `vm-web-01`. (PDF does this
   first; we swap → verify → decommission, which is the real-world order and keeps a
   rollback path until the cutover is proven.)
8. **Azure Monitor**, `sqldb-app` → Metrics → **DTU percentage**, Max, the chart shows
   the traffic you just generated.

## Cost notes

- **Azure SQL Basic (5 DTU): ~$4.99/mo ≈ 17¢/day.** LRS backup redundancy (cheapest).
  The two landmines are at create time: the **free-offer banner** (locks you out of the
  DTU tier) and **Workload environment = Production** (Hyperscale, $320+/mo).
- **Key Vault Standard: pennies**, ~$0.03 per 10k operations; this lab does a handful.
- **Azure Monitor metrics: free** (platform metrics, no Log Analytics workspace).
- **The real burner is still Lab 02's Bastion (~$0.19/hr) in `rg-lab02-cam`**, it must
  stay up through this shoot (it's the shell path to `vm-web-01`). Tear it down with the
  Lab 02 group as soon as recording wraps.

## Teardown

When recording stops (after housekeeping/rotation):

```bash
# Lab 03 resources (SQL server + DB + Key Vault). No --no-wait on purpose:
# the purge below only works once the vault is actually soft-deleted, so let
# this one block until the group is gone.
az group delete --name rg-lab03-cam --yes

# Key Vault soft-delete keeps the name reserved for 90 days after RG delete.
# Purge it so kv-lab03-cam is reusable (works because purge protection is OFF):
az keyvault purge --name kv-lab03-cam --location westus2

# Lab 02 resources (vm-web-01, Bastion, the cost landmine), when fully done:
az group delete --name rg-lab02-cam --yes --no-wait
```

- ⚠️ **Timing:** `rg-lab02-cam` hosts `vm-web-01`, this lab's app server. Delete it only
  after the Lab 03 footage is confirmed good (re-shooting a step needs the stack alive).
  Check whether the next lab builds on `vm-web-01` before deleting.
- ⚠️ **NEVER touch `rg-cloud-portfolio`**, reserved for the site (deleted 2026-07-03 for
  the recorded redo; the name comes back when the site does). Not part of any lab
  teardown, ever.

## Verify / debug

- **Web tier healthy:** on `vm-web-01`: `curl -s http://127.0.0.1:8000/healthz` → `ok`.
  From a laptop: `curl http://<web-public-ip>/healthz`.
- **Secret fetch by hand** (on `vm-web-01`): `sudo /usr/local/bin/fetch-db-pass.sh &&
  echo fetched`, errors mean identity/RBAC; success + app failing means SQL side.
- **403 from Key Vault:** RBAC propagation takes 1 to 5 min after the role assignment;
  wait, then `sudo systemctl restart links`. Confirm the assignment is on the vault:
  IAM → Role assignments → `vm-web-01` / Key Vault Secrets User.
- **IMDS returns no identity:** the System assigned toggle wasn't saved, VM → Identity
  must show an Object ID.
- **Login failed for 'appuser':** password mismatch between `links-migration.sql` and
  the `DbAppPassword` secret, they must be the same value. If auth still fails, try
  `DB_USER=appuser@sql-lab03-cam` in `/etc/app.env` (old TDS gateway routing form for
  *server* logins, `appuser` is a contained user, so this is last-ditch and likely
  not the fix).
- **Connection times out to `*.database.windows.net`:** server Networking blade →
  Public endpoint enabled + **Allow Azure services = Yes**. (Outbound from the VM is
  open by default; Azure's Redirect connection policy uses ports 11000 to 11999 outbound.)
- **TLS/handshake weirdness from pymssql:** `TDSVER=7.4` present in `/etc/app.env`; if
  needed, `sudo /opt/app/venv/bin/pip install --upgrade pymssql` (wheels bundle a
  TLS-capable FreeTDS). Still config/ops, no code change.
- **Query editor won't connect:** your client IP firewall rule is missing, it offers
  an "Allowlist IP" link right on the error; click it.
- **Service logs:** `journalctl -u links -n 50 --no-pager`, a failed `ExecStartPre`
  (fetch) is clearly labeled and the service retries (`Restart=always`).
- **Rollback (mid-shoot save):** `sudo cp /etc/app.env.lab02.bak /etc/app.env && sudo
  systemctl restart links` → app is back on `vm-db-01` as long as it still exists,
  which is exactly why decommission is the LAST infrastructure step.
