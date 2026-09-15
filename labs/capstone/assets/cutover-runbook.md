# Cutover Runbook — AWS EC2 → Azure (Azure Migrate lift-and-shift)

The rehearsed, ordered sequence for moving the link-shortener workload from an
AWS EC2 Windows Server to Azure with zero data loss. Terraform builds the
scaffolding; the migration itself (discovery → assess → replicate → test →
cutover) is driven in the Azure portal because the appliances need interactive
config. This runbook is the checklist behind the shoot script.

> **Golden rule of a cutover: never flip until you've rehearsed.** The test
> migration (Part 6A) is that rehearsal — a throwaway copy booted in an
> isolated network. Only after it boots clean do you do the real cutover.

---

## 0. Pre-cutover state (must all be true)

- [ ] AWS side applied — EC2 up, app answering at `http://<ec2_public_ip>`.
- [ ] Azure landing zone applied — both RGs, VNet, storage, Log Analytics, RSV.
- [ ] Azure Migrate project created in the portal.
- [ ] Discovery appliance deployed + registered; EC2 discovered.
- [ ] Assessment run — status **Ready for Azure**, size recommendation noted.
- [ ] Replication appliance deployed + registered with the vault.
- [ ] Replication enabled; machine status is **Protected** (initial sync done).

## 1. The zero-data-loss proof (do this BEFORE cutover)

While replication is live, add a NEW short link in the source app
(`http://<ec2_public_ip>` → shorten a URL). That write lands in the SQLite file
on the EC2 disk, replication picks up the delta, and after cutover the same new
link must appear in Azure. Note the code it generates.

## 2. Test migration (the rehearsal — Part 6A)

1. Azure Migrate → Replicating machines → the EC2 instance → **Test migration**.
2. Target VNet: `vnet-migrate-<name>`.
3. When the test VM appears in the target RG, RDP in (public IP + original
   `admin_password`), confirm Windows boots and the desktop/hostname match.
4. **Clean up test migration** (deletes the throwaway copy).

## 3. Cutover (Part 6B — the real flip)

1. Replicating machines → the EC2 instance → **Migrate**.
2. **Shut down machines before migration:** No for the lab. (In production:
   Yes — shutting the source prevents "split-brain," where both copies take
   writes and data diverges.)
3. **Migrate.** Azure builds the target VM from the latest synced disk (~5-10 min).

## 4. DNS / URL flip + validate (Part 6C)

The migrated VM gets a NEW Azure public IP — cloud-to-cloud, the address always
changes. That's the flip.

1. Attach a public IP + confirm `nsg-migrate-target-<name>` is on the NIC (opens
   3389 + 80). See CLI in README.
2. Browse `http://<new-azure-public-ip>` → the SAME link-shortener, the SAME
   seeded links, AND the new link you added in step 1 above. **Zero data loss.**
3. RDP in (Administrator + original `admin_password`); confirm hostname + OS
   version match the source EC2 instance.

**On DNS / TTL (say it, even though the lab uses raw IPs):** in the real world
the app has a domain, not an IP. Before a cutover you lower that record's TTL
(say to 60s) a day ahead, so when you repoint it to the new IP the world picks
it up in a minute instead of caching the old address for hours. Low TTL first,
flip second, raise TTL back after.

## 5. Decommission the source + tear down BOTH clouds (same day)

Order matters — stop replication before destroying, or you get dependency errors.

1. Azure Migrate → Replicating machines → the machine → **Stop replication**.
2. `cd aws-terraform && terraform destroy` — the source is gone; workload lives
   in Azure now.
3. Delete the two appliance VMs (part of the Azure destroy below).
4. `cd azure-terraform && terraform destroy` — kills the staging RG, both
   appliances, storage, Log Analytics, and the vault.
5. `az group delete --name rg-migrate-target-<name> --yes` — the migrated VM
   was created BY Azure Migrate, not Terraform, so its RG is deleted by hand.

> If `terraform destroy` fails on the Recovery Services Vault with "vault is not
> empty": portal → the vault → **Backup items** / **Replication items** → delete
> all items → retry destroy.
