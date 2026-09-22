# Lab 02 - Deploy Flow (cheat sheet)

> On-camera reference. Pair with `architecture.png`. Build **DB first**, then web.
> 🔒 Set the two passwords before pasting any cloud-init (same value, both files).

---

## The flow, in order

```
① VNet + 2 subnets   ② NAT GW on snet-db   ③ vm-db-01 (DB)          ④ vm-web-01 (web)       ⑤ NSG lockdown     ⑥ prove it
   10.0.0.0/16           outbound-only        D2as_v7 · Ubuntu 22.04   D2as_v7 · public IP     DB:1433 from web   shorten → click
   snet-web 10.0.1.0/24  internet for           · no PIP                cloud-init-web          only              → redirect
   snet-db  10.0.2.0/24  cloud-init
```

| # | Step | Do | Watch out |
|---|------|----|-----------|
| 1 | **Network** | VNet `10.0.0.0/16`; `snet-web` `10.0.1.0/24`, `snet-db` `10.0.2.0/24` | - |
| 2 | **NAT Gateway on snet-db** | `natgw-lab02` + `pip-natgw`, attach to `snet-db` | snet-db has no public IP and this sub's subnets get no default outbound access - skip this and cloud-init's SQL Server install hangs on `curl (28)` |
| 3 | **DB VM first** | `vm-db-01`, **Ubuntu 22.04 LTS**, **Standard_D2as_v7**, **no public IP**, paste `cloud-init-db.yaml` | Ubuntu 20.04 image is gone from westus2 (404) - must be 22.04, matching the cloud-init's apt repo. B1s (1 GB) → SQL install **fails** either way; B2s and D2s_v3 were also unavailable in this subscription. Confirm private IP = **10.0.2.4** |
| 4 | **Web VM** | `vm-web-01`, Ubuntu 22.04, D2as_v7, **public IP**, paste `cloud-init-web.yaml` | If DB IP ≠ 10.0.2.4, fix `DB_HOST` first |
| 5 | **NSG lockdown** | DB NSG: allow `10.0.1.0/24 → 1433`, **deny the rest** | Tightens the PDF's `*` source |
| 6 | **Prove it** | Browse web public IP → shorten a URL → click short link → redirect | That redirect = web reading the **private** DB live |

🔒 **Verify live before recording:** VM SKU capacity can vanish for a subscription/region with
no notice - check `az vm list-skus --location westus2 --size Standard_D2as_v7 --all` for a
`Location`-type restriction. `Standard_B1s`, `Standard_B2s`, and `Standard_D2s_v3` were all
unavailable as of 2026-07-18; `Standard_D2as_v7` is the size both VMs actually use.

---

## Request path (say it out loud)

```
browser → Public IP → NSG :80 → vm-web-01 (nginx → gunicorn → Flask)
        → NSG :1433 → vm-db-01 (SQL Server, appdb.dbo.links) → 302 redirect
```

## NSG rules that matter

| NSG | Allow | Source | Port |
|-----|-------|--------|------|
| web | HTTP  | Internet (`*`) | 80 |
| db  | SQL   | `10.0.1.0/24` (web subnet only) | 1433 |
| db  | **deny** | everything else | 1433 |

## Verify / debug (paste-ready)

```bash
curl http://<web-public-ip>/healthz        # ok=200 reaches DB · db-unreachable=503
nc -vz <db-private-ip> 1433                 # from laptop → NO route (proves private)
                                            # from web VM via Bastion → connects
# DB cloud-init finished? on vm-db-01:  cat /var/log/db-setup.done
# cloud-init logs (either VM):           /var/log/cloud-init-output.log
```

## Say-on-camera beats (the receipts)

- **Right-sizing:** "DB is D2as_v7 - SQL Server needs ≥2 GB; B1s would fail." 
- **Least privilege:** "`appuser` is datareader/datawriter only - never sysadmin."
- **Private by design:** "DB has no public IP; 1433 is open *only* to the web subnet."
- **Plaintext secret (acknowledge):** "Password's in cloud-init for now - rotating before publish. Getting it off the box is the whole pitch for the hardened build." → 🔒 **rotate before publish**

## Cleanup (when recording stops)

```bash
az group delete --name rg-lab02-cam --yes --no-wait   # kills VMs, Bastion ($$$), everything
```
⚠️ **Only** `rg-lab02-cam`. Never touch `rg-cloud-portfolio` (live site + résumé).
