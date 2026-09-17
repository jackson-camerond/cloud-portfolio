#!/usr/bin/env bash
# Lab 07, Containerized App on Kubernetes (Azure AKS, westus2)
#
# Idempotent: every `az ... create` below is safe to re-run, Azure either
# updates the existing resource in place or no-ops if nothing changed.
# `kubectl apply` is idempotent by definition (declarative, it reconciles
# the cluster to match these files, whatever state it's currently in).
#
# What this builds:
#   Resource group -> ACR (private image store) -> build+push the image with
#   az acr build (no local Docker needed) -> AKS cluster (managed identity,
#   attached to ACR) -> Deployment + Service(LoadBalancer) + HPA -> Container
#   Insights (Log Analytics) for logs/metrics.
#
# Usage: ./deploy.sh
set -euo pipefail

# ---- locked values (match the Lab Guide) ------------------------------
RG="rg-lab07-cam"
LOCATION="westus2"
ACR_NAME="acrlab07cam"          # ACR names: lowercase alphanumeric only, no dashes
AKS_NAME="aks-lab07-cam"
AKS_VERSION="1.36.1"            # `az aks get-versions -l westus2` -- current GA
NODE_VM_SIZE="Standard_D2s_v4"
NODE_COUNT=2
NAMESPACE="aks-demo"
IMAGE_NAME="aks-demo-api"
IMAGE_TAG="v1"
TAGS="env=lab owner=cam project=lab07"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(dirname "$SCRIPT_DIR")"
APP_DIR="$ASSETS_DIR/app"
K8S_DIR="$ASSETS_DIR/k8s"

echo "==> 0/7  Resource providers (registers once per subscription, not billable)"
for ns in Microsoft.ContainerService Microsoft.ContainerRegistry; do
  state=$(az provider show -n "$ns" --query registrationState -o tsv 2>/dev/null || echo "NotRegistered")
  if [[ "$state" != "Registered" ]]; then
    echo "    registering $ns (state was: $state)..."
    az provider register --namespace "$ns" -o none
  fi
done

echo "==> 1/7  Resource group ($RG)"
az group create --name "$RG" --location "$LOCATION" --tags $TAGS -o none

echo "==> 2/7  Container registry ($ACR_NAME), a private Docker Hub for this image"
az acr create --resource-group "$RG" --name "$ACR_NAME" --sku Basic --tags $TAGS -o none

echo "==> 3/7  Build + push the image with az acr build (builds in the cloud, no local Docker needed)"
az acr build \
  --registry "$ACR_NAME" \
  --resource-group "$RG" \
  --image "${IMAGE_NAME}:${IMAGE_TAG}" \
  "$APP_DIR"

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RG" --query loginServer -o tsv)
echo "    image pushed: ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "==> 4/7  AKS cluster ($AKS_NAME), managed Kubernetes, 2x $NODE_VM_SIZE, attached to ACR"
if az aks show --resource-group "$RG" --name "$AKS_NAME" -o none 2>/dev/null; then
  echo "    cluster already exists, skipping create"
else
  az aks create \
    --resource-group "$RG" \
    --name "$AKS_NAME" \
    --location "$LOCATION" \
    --kubernetes-version "$AKS_VERSION" \
    --node-count "$NODE_COUNT" \
    --node-vm-size "$NODE_VM_SIZE" \
    --tier free \
    --enable-managed-identity \
    --attach-acr "$ACR_NAME" \
    --generate-ssh-keys \
    --tags $TAGS \
    -o none
fi

echo "==> 5/7  kubeconfig, az aks get-credentials wires kubectl to the cluster"
az aks get-credentials --resource-group "$RG" --name "$AKS_NAME" --overwrite-existing

echo "==> 6/7  Validate manifests, then apply (Deployment + Service + HPA)"
# Render the ACR login server into the Deployment (kept as a placeholder in
# git so the manifest never hardcodes a personal registry name).
RENDERED_DIR=$(mktemp -d)
trap 'rm -rf "$RENDERED_DIR"' EXIT
for f in "$K8S_DIR"/*.yaml; do
  sed "s#ACR_LOGIN_SERVER#${ACR_LOGIN_SERVER}#g" "$f" > "$RENDERED_DIR/$(basename "$f")"
done

# Client-side schema validation before anything touches the cluster.
# NOTE: `kubectl apply` (unlike `az ... -o none`) has no "none" printer --
# it only accepts go-template/json/jsonpath/kyaml/name/template/yaml. Redirect
# to /dev/null instead so this step still fails loudly on a real schema error.
kubectl apply --dry-run=client -f "$RENDERED_DIR" -o name >/dev/null

# Best-effort security/lint scan, skips quietly if the tool isn't installed
# locally (see assets/README.md for install commands). Same discipline as
# the Checkov/Trivy gate other labs run in CI.
if command -v checkov >/dev/null 2>&1; then
  echo "    checkov: scanning k8s manifests..."
  checkov -d "$K8S_DIR" --framework kubernetes --quiet || true
else
  echo "    (checkov not installed, skipping IaC scan; see assets/README.md)"
fi
if command -v trivy >/dev/null 2>&1; then
  echo "    trivy: scanning ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}..."
  trivy image --severity HIGH,CRITICAL "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}" || true
else
  echo "    (trivy not installed, skipping image scan; see assets/README.md)"
fi

kubectl apply -f "$RENDERED_DIR"

echo "==> 7/7  Container Insights, Log Analytics-backed dashboard + logs for the cluster"
az aks enable-addons --resource-group "$RG" --name "$AKS_NAME" --addons monitoring -o none 2>/dev/null \
  || echo "    (monitoring add-on already enabled, skipping)"

echo
echo "==> Waiting for the LoadBalancer's public IP (this can take 1-3 minutes)..."
for i in $(seq 1 30); do
  IP=$(kubectl get svc "$IMAGE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
  if [[ -n "$IP" ]]; then
    break
  fi
  sleep 10
done

echo
echo "===================================================================="
echo " Deploy complete."
echo "   App URL:      http://${IP:-<pending, run: kubectl get svc -n $NAMESPACE>}"
echo "   Cluster:      $AKS_NAME  (rg: $RG, region: $LOCATION)"
echo "   Registry:     $ACR_LOGIN_SERVER"
echo "   Namespace:    $NAMESPACE"
echo
echo " The HPA (2-10 replicas, 50% CPU target) is already applied and watching."
echo " Load-test it:   python3 ${SCRIPT_DIR}/../scripts/loadgen.py <that IP>"
echo " Watch it scale: kubectl get hpa -n $NAMESPACE -w"
echo "===================================================================="
