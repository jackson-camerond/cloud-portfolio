#!/usr/bin/env bash
# Lab 08 - tear down everything this lab created. Cost discipline: run this
# the same day you record unless you're actively iterating on the pipeline.
#
# Order matters: the app root (ALB, ECS service/cluster, security groups)
# comes down first, THEN the bootstrap root (ECR, IAM roles, OIDC provider).
# The app root's task definition references the bootstrap root's IAM role
# ARNs by value, not by a live Terraform dependency across states, so this
# ordering isn't strictly required by Terraform - but it matches how you'd
# tear down a real two-tier stack, cheapest and most-detachable pieces last.
#
# Idempotent: safe to re-run if it's interrupted partway through.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$HERE/../terraform"

# State lives in S3 now, so we can't key off a local .terraform dir - CI may
# have applied the app root, leaving NO local state on this machine while the
# ALB + Fargate service bill in the background. Instead we `init` against the
# remote backend (which pulls the real state) and destroy from that. If the
# state bucket itself is gone, nothing was ever deployed.
STATE_BUCKET="lab08-tfstate-350681797031"

if aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
  echo "==> [1/3] terraform destroy - app (ALB + ECS Fargate service)"
  terraform -chdir="$TF_DIR/app" init -input=false -reconfigure >/dev/null
  terraform -chdir="$TF_DIR/app" destroy -auto-approve

  echo "==> [2/3] terraform destroy - bootstrap (OIDC + IAM + ECR)"
  terraform -chdir="$TF_DIR/bootstrap" init -input=false -reconfigure >/dev/null
  terraform -chdir="$TF_DIR/bootstrap" destroy -auto-approve

  echo "==> [3/3] removing state bucket s3://${STATE_BUCKET}"
  aws s3 rb "s3://${STATE_BUCKET}" --force
else
  echo "    state bucket absent - nothing was deployed, nothing to destroy"
fi

echo "==> Done. Confirm zero cost:"
echo "  aws ecs list-clusters --region us-west-2"
echo "  aws elbv2 describe-load-balancers --region us-west-2"
echo "  aws ecr describe-repositories --region us-west-2"
echo "(all three should come back empty of anything named lab08-cicd-*)"
