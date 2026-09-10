# Lab 02: Deploy Flow (cheat sheet)

> Quick reference. Pair with `architecture.png`. Build **DB first**, then web.
> 🔒 Set the two passwords before pasting any cloud-init (same value, both files).

---

## The flow, in order

```
① VNet + 2 subnets   ②  vm-db-01 (DB)   ③  vm-web-01 (web)   ④  NSG lockdown   ⑤  prove it
   10.0.0.0/16          B2s · no PIP        B1s · public IP      DB:1433 from web    shorten → click
   snet-web 10.0.1.0/24                      cloud-init-web        only               → redirect
   snet-db  10.0.2.0/24
```

| # | Step | Do | Watch out |
|---|------|----|-----------|
| 1 | **Network** | VNet `10.0.0.0/16`; `snet-web` `10.0.1.0/24`, `snet-db` `10.0.2.0/24` | n/a |
| 2 | **DB VM first** | `vm-db-01`, **Standard_B2s**, **no public IP**, paste `cloud-init-db.yaml` | B1s (1 GB) → SQL install **fails**. Confirm private IP = **10.0.2.4** |
| 3 | **Web VM** | `vm-web-01`, B1s, **public IP**, paste `cloud-init-web.yaml` | If DB IP ≠ 10.0.2.4, fix `DB_HOST` first |
| 4 | **NSG lockdown** | DB NSG: allow `10.0.1.0/24 → 1433`, **deny the rest** | Tightens the PDF's `*` source |
| 5 | **Prove it** | Browse web public IP → shorten a URL → click short link → redirect | That redirect = web reading the **private** DB live |

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

## Cleanup

```bash
az group delete --name rg-lab02-cam --yes --no-wait   # kills VMs, Bastion ($$$), everything
```
⚠️ **Only** `rg-lab02-cam`. Never touch `rg-cloud-portfolio` (live site + résumé).
