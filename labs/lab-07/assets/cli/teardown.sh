#!/usr/bin/env bash
# Lab 07 teardown, cost discipline: this lab's node pool + Standard Load
# Balancer bill by the hour, so tear it down the same day you record unless
# you're actively demoing it.
#
# One resource group holds everything (cluster, node pool VMs, the AKS-
# managed "MC_..." infra group, ACR, the LB) so ONE delete removes it all --
# no separate ACR/AKS deletes needed, no orphaned MC_ group left behind.
#
# Usage: ./teardown.sh
set -euo pipefail

RG="rg-lab07-cam"

echo "==> Deleting resource group $RG (this also removes the auto-created"
echo "    MC_${RG}_aks-lab07-cam_westus2 node-resource-group, the AKS cluster,"
echo "    the ACR registry, and the Load Balancer + public IP)."

if ! az group show --name "$RG" -o none 2>/dev/null; then
  echo "    $RG doesn't exist, nothing to tear down."
  exit 0
fi

az group delete --name "$RG" --yes --no-wait

echo "==> Delete requested (--no-wait). Confirm it's gone with:"
echo "      az group exists --name $RG"
echo "    Local kubeconfig context still points at the deleted cluster until"
echo "    you clean it up:"
echo "      kubectl config delete-context aks-lab07-cam"
echo "      kubectl config delete-cluster aks-lab07-cam"
