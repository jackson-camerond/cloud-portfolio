#!/usr/bin/env bash
# =============================================================================
# rebuild-lab02.sh : recreate the entire Lab 02 stack from scratch in ONE
# resource group (rg-lab02-cam), so the next lab can build on top of it and the
# whole thing can be torn down with a single `az group delete`.
#
# Matches the cloud-init assets: restores vm-web-01 (app, with the password in
# /etc/app.env) and vm-db-01 (SQL Server 2022, seeded links table).
#
# Run AFTER `az login`. Safe to re-run; existing resources are skipped or
# updated. Scoped to rg-lab02-cam only.
# =============================================================================
set -euo pipefail

# ---- values (must match the cloud-init files) -------------------------------
RG="rg-lab02-cam"
LOC="westus2"
VNET="vnet-lab02"
SNET_WEB="snet-web";   CIDR_WEB="10.0.1.0/24"
SNET_DB="snet-db";     CIDR_DB="10.0.2.0/24"
SNET_BAS="AzureBastionSubnet"; CIDR_BAS="10.0.3.0/26"   # name is mandatory, /26 min
NSG_WEB="nsg-web"
NSG_DB="nsg-db"
DB_IP="10.0.2.4"                 # web cloud-init hardcodes DB_HOST=10.0.2.4
APP_PASSWORD='CHANGE_ME_AppPassw0rd!'    # PLACEHOLDER. Must equal cloud-init-db.yaml APP_PASSWORD
ADMIN="azureuser"
IMG="Ubuntu2204"                 # DB cloud-init REQUIRES 22.04 (not 20.04/24.04)
ASSETS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYDIR="$HOME/lab-keys"
KEY="$KEYDIR/vm-web-01_key"      # private key Lab 03 Bastion-connects with (.pem)

say(){ printf '\n\033[1;36m== %s\033[0m\n' "$*"; }

# ---- 0. sanity --------------------------------------------------------------
command -v az >/dev/null || { echo "az CLI not found"; exit 1; }
az account show >/dev/null 2>&1 || { echo "Not logged in. Run: az login"; exit 1; }
[ -f "$ASSETS/cloud-init-db.yaml" ]  || { echo "missing cloud-init-db.yaml";  exit 1; }
[ -f "$ASSETS/cloud-init-web.yaml" ] || { echo "missing cloud-init-web.yaml"; exit 1; }
say "Subscription: $(az account show --query name -o tsv)"

# ---- 1. SSH key (dedicated, saved where Lab 03 expects it) ------------------
mkdir -p "$KEYDIR"; chmod 700 "$KEYDIR"
if [ ! -f "$KEY" ]; then
  ssh-keygen -t rsa -b 2048 -f "$KEY" -N '' -C "vm-web-01" >/dev/null
  cp "$KEY" "$KEY.pem"; chmod 600 "$KEY" "$KEY.pem"
fi
PUBKEY="$KEY.pub"

# ---- 2. resource group ------------------------------------------------------
say "Resource group $RG ($LOC)"
az group create -n "$RG" -l "$LOC" -o none

# ---- 3. VNet + three subnets ------------------------------------------------
say "VNet + subnets (web / db / bastion)"
az network vnet create -g "$RG" -n "$VNET" --address-prefix 10.0.0.0/16 \
  --subnet-name "$SNET_WEB" --subnet-prefix "$CIDR_WEB" -o none
az network vnet subnet create -g "$RG" --vnet-name "$VNET" \
  -n "$SNET_DB" --address-prefix "$CIDR_DB" -o none
az network vnet subnet create -g "$RG" --vnet-name "$VNET" \
  -n "$SNET_BAS" --address-prefix "$CIDR_BAS" -o none

# ---- 4. DB subnet NSG: allow 1433 only from the web subnet ------------------
say "DB NSG (1433 from web subnet only) → attach to $SNET_DB"
az network nsg create -g "$RG" -n "$NSG_DB" -o none
az network nsg rule create -g "$RG" --nsg-name "$NSG_DB" -n Allow-Web-To-SQL \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "$CIDR_WEB" --destination-port-ranges 1433 -o none
az network vnet subnet update -g "$RG" --vnet-name "$VNET" -n "$SNET_DB" \
  --network-security-group "$NSG_DB" -o none

# ---- 5. vm-db-01 FIRST (private, pinned to 10.0.2.4, B2s for SQL RAM) --------
say "vm-db-01  (B2s · $IMG · private $DB_IP · SQL Server 2022)"
az vm create -g "$RG" -n vm-db-01 --image "$IMG" --size Standard_B2s \
  --vnet-name "$VNET" --subnet "$SNET_DB" --private-ip-address "$DB_IP" \
  --public-ip-address "" --nsg "" \
  --admin-username "$ADMIN" --ssh-key-values "$PUBKEY" \
  --custom-data "$ASSETS/cloud-init-db.yaml" -o none

# ---- 6. vm-web-01 (public, Bastion-only SSH via --nsg-rule NONE) ------------
# Render the web cloud-init with the matching app password injected.
RENDERED="$(mktemp -t cloudinit-web.XXXX).yaml"
sed "s/CHANGE_ME_APP_PASSWORD/${APP_PASSWORD}/" "$ASSETS/cloud-init-web.yaml" > "$RENDERED"
say "vm-web-01  (B1s · $IMG · public IP · app reads DB at $DB_IP)"
az vm create -g "$RG" -n vm-web-01 --image "$IMG" --size Standard_B1s \
  --vnet-name "$VNET" --subnet "$SNET_WEB" \
  --public-ip-address vm-web-01-pip --public-ip-sku Standard \
  --nsg "$NSG_WEB" --nsg-rule NONE \
  --admin-username "$ADMIN" --ssh-key-values "$PUBKEY" \
  --custom-data "$RENDERED" -o none
rm -f "$RENDERED"
# open only port 80 to the internet (SSH stays Bastion-only via default VnetInBound)
az network nsg rule create -g "$RG" --nsg-name "$NSG_WEB" -n Allow-HTTP \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes Internet --destination-port-ranges 80 -o none

# ---- 7. Bastion (the admin path Lab 03 uses; Basic SKU = cheapest) ----------
say "Bastion host (Basic). This one takes about 6 to 10 min"
az network public-ip create -g "$RG" -n pip-bastion \
  --sku Standard --allocation-method Static -l "$LOC" -o none
az network bastion create -g "$RG" -n bastion-lab02 \
  --public-ip-address pip-bastion --vnet-name "$VNET" --location "$LOC" \
  --sku Basic -o none

# ---- 8. report --------------------------------------------------------------
WEB_IP="$(az network public-ip show -g "$RG" -n vm-web-01-pip --query ipAddress -o tsv)"
say "DONE. Lab 02 stack is live in one group: $RG"
cat <<EOF

  Web public IP : $WEB_IP     →  http://$WEB_IP   (app UI)
  DB private IP : $DB_IP      (vm-db-01, no public IP)
  SSH key (.pem): $KEY.pem    (Bastion → vm-web-01 as '$ADMIN')
  App password  : in /etc/app.env on vm-web-01 (plaintext, by design for this lab)

  Give cloud-init ~5-8 min (SQL Server install), then verify:
      curl -s http://$WEB_IP/healthz     # expect: ok   (503 = DB not ready yet)

  LAB 03 NOTE: create the Azure SQL server + Key Vault INSIDE this same group
  ($RG), do NOT make a new rg-lab03-cam, so teardown stays one command:
      az group delete --name $RG --yes --no-wait
EOF
