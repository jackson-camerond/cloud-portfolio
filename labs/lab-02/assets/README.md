# Lab 02 build assets

Provisioning and application source for a secure two-tier build on Azure. The service is
a small link shortener: a stateless web tier that reads and writes a database sitting on
a private subnet with no public IP and no route from the internet.

**This lab is as much Linux administration as it is Azure networking.** Nothing here is
portal magic. Both VMs are Ubuntu, administered the standard way: packages installed and
services wired by cloud-init, the app run as a systemd unit, nginx as the reverse proxy,
environment config in `/etc/app.env`, and debugging done by reading logs
(`/var/log/cloud-init-output.log`, `journalctl -u`, nginx logs) over Bastion SSH.

## Files

- `cloud-init-db.yaml` : vm-db-01. SQL Server 2022 Express, a least-privilege `appuser`
  login, and a seeded `dbo.links` table.
- `cloud-init-web.yaml` : vm-web-01. nginx in front of gunicorn in front of a Flask link
  shortener, with the app embedded in the file.
- `app/app.py`, `app/templates/index.html` : a readable copy of the same application.
  **This source is embedded into `cloud-init-web.yaml`**, so if you edit one, edit both.
- `rebuild-lab02.sh` : rebuilds the whole environment from the CLI in one pass.
- `diagram/` : architecture diagram and the deploy flow.

## Deploy order

1. Create the VNet and the two subnets.
2. **vm-db-01 first.** Paste `cloud-init-db.yaml` as Custom data. **Size Standard_B2s.**
   SQL Server needs at least 2 GB of RAM; B1s has 1 GB and the install fails. No public
   IP. Confirm its private IP is `10.0.2.4`, and if it is not, update `DB_HOST` in the
   web cloud-init to match.
3. **vm-web-01.** Paste `cloud-init-web.yaml`. Standard_B1s, public IP, NSG allowing 80.
4. NSG on the database subnet: allow `10.0.1.0/24` to `1433`, deny everything else.
5. Browse the web VM's public IP, shorten a URL, then click the short link. The redirect
   is the web tier reading a row out of the database on the private subnet.

## Before you deploy: set the passwords

Three placeholders must be replaced before this will run. Set the SAME value in both
places marked `APP_PASSWORD` / `DB_PASS`:

- `cloud-init-db.yaml` : `APP_PASSWORD`
- `cloud-init-web.yaml` : `DB_PASS` in `/etc/app.env`
- `cloud-init-db.yaml` : `SA_PASSWORD` is provisioning-time only and the app never uses
  it. It can be a different value.

SQL Server runs with `CHECK_POLICY=ON`, so each password needs upper case, lower case,
a digit and a symbol.

> **These sit in plaintext in cloud-init, and that is the point of this build.**
> A password on the box is the weakness this architecture still has after the network is
> locked down. Removing it entirely, with a managed identity and a secrets manager, is
> the subject of the next lab. Do not reuse these files as-is for anything real.

## Cleanup

Delete the lab's resource group and nothing else:

```
az group delete --name rg-lab02-cam --yes --no-wait
```

That removes every resource the lab created in one action: VMs, disks, NICs, NSGs, the
VNet, and **Bastion**, which is the expensive one to leave running. Deleting a resource
group cannot affect resources in any other group, so scope your teardown to the lab
group and check the name before you confirm.

## Verify and debug

- **Web tier up:** `curl http://<web-public-ip>/healthz` returns `ok` with a 200.
  A `db-unreachable` 503 means the web tier cannot reach port 1433 on the database.
  Check the NSG rule, and check that `cloud-init-db.yaml` finished by looking for
  `/var/log/db-setup.done` on vm-db-01 over Bastion.
- **cloud-init logs** on each VM: `/var/log/cloud-init-output.log`.
- **Prove the database is private:** from your own machine, `nc -vz <db-private-ip> 1433`
  hangs with no route. From the web VM over Bastion, the same command connects.
