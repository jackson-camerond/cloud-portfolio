#!/usr/bin/env bash
# Lab 08 -- End-to-End CI/CD Pipeline -- one-time bootstrap.
#
# This script does the thing a pipeline can never do for itself: it stands
# up the very first version of everything, by hand, once. After this runs,
# every future change ships through GitHub Actions -- this script is not
# part of the pipeline, it's what makes the pipeline possible.
#
# Idempotent: safe to re-run. Terraform only changes what drifted; the
# image push is skipped if the "bootstrap" tag already exists in ECR.
#
# Usage:
#   GITHUB_ORG=your-gh-username GITHUB_REPO=your-repo-name ./deploy.sh
# (Only required the first time -- after that, org/repo are cached in
#  terraform/bootstrap/terraform.tfvars and every re-run reuses them.)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$HERE/../terraform"
AWS_REGION="${AWS_REGION:-us-west-2}"

echo "==> Lab 08 deploy -- region ${AWS_REGION}"

# ---------------------------------------------------------------------------
# 0. Pin down GitHub org/repo -- written once, reused on every re-run.
# ---------------------------------------------------------------------------
TFVARS="$TF_DIR/bootstrap/terraform.tfvars"

if [[ -f "$TFVARS" ]]; then
  echo "==> Reusing existing $TFVARS"
else
  : "${GITHUB_ORG:?Set GITHUB_ORG (e.g. your GitHub username) on first run}"
  : "${GITHUB_REPO:?Set GITHUB_REPO (e.g. cloud-portfolio) on first run}"
  cat > "$TFVARS" <<EOF
github_org  = "${GITHUB_ORG}"
github_repo = "${GITHUB_REPO}"
aws_region  = "${AWS_REGION}"
EOF
  echo "==> Wrote $TFVARS"
fi

# ---------------------------------------------------------------------------
# 0.5 State backend bucket -- "who bootstraps the bootstrapper."
# ---------------------------------------------------------------------------
# Both Terraform roots keep their state in this S3 bucket (see versions.tf).
# The app root is applied by CI on an ephemeral runner, so its state CANNOT be
# a local file -- the runner starts empty every run. But Terraform can't create
# the bucket that holds its own state, so we make it here, once, with one CLI
# call. Idempotent: the create is a no-op if the bucket already exists.
STATE_BUCKET="lab08-tfstate-350681797031"
echo "==> [0.5] ensuring state bucket s3://${STATE_BUCKET}"
if ! aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$AWS_REGION" \
    --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
  # Deliberately NOT versioned: this is a same-day lab, and a versioned bucket
  # can't be emptied by `aws s3 rb --force` (it leaves old versions + delete
  # markers), which would make teardown fail. Non-versioned = clean teardown.
  echo "    created"
else
  echo "    already exists"
fi

# ---------------------------------------------------------------------------
# 1. Bootstrap root -- OIDC provider, gha-plan / gha-deploy roles, ECS
#    execution/task roles, ECR repo. Applied by YOU, never by CI.
# ---------------------------------------------------------------------------
echo "==> [1/4] terraform apply -- bootstrap (OIDC + IAM + ECR)"
terraform -chdir="$TF_DIR/bootstrap" init -input=false -upgrade=false
terraform -chdir="$TF_DIR/bootstrap" apply -auto-approve

ECR_URL=$(terraform -chdir="$TF_DIR/bootstrap" output -raw ecr_repository_url)
ECR_NAME=$(terraform -chdir="$TF_DIR/bootstrap" output -raw ecr_repository_name)
PLAN_ROLE_ARN=$(terraform -chdir="$TF_DIR/bootstrap" output -raw gha_plan_role_arn)
DEPLOY_ROLE_ARN=$(terraform -chdir="$TF_DIR/bootstrap" output -raw gha_deploy_role_arn)

# ---------------------------------------------------------------------------
# 2. Seed ECR with a first image so the ECS service has something to run.
#    Skipped if it's already there -- the repo is IMMUTABLE-tagged, so a
#    second push of the same tag would fail, not just be a no-op.
# ---------------------------------------------------------------------------
echo "==> [2/4] seed image (tag: bootstrap)"
if aws ecr describe-images --region "$AWS_REGION" --repository-name "$ECR_NAME" \
     --image-ids imageTag=bootstrap >/dev/null 2>&1; then
  echo "    bootstrap tag already in ECR -- skipping build+push"
else
  aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "${ECR_URL%%/*}"
  docker build --platform linux/arm64 -t "${ECR_URL}:bootstrap" "$HERE/../app"
  docker push "${ECR_URL}:bootstrap"
fi

# ---------------------------------------------------------------------------
# 3. App root -- cluster, ALB, security groups, task definition, service.
#    This is the exact `terraform apply` the GitHub Actions deploy job runs
#    on every future merge -- you're just running it by hand this one time.
# ---------------------------------------------------------------------------
echo "==> [3/4] terraform apply -- app (ALB + ECS Fargate service)"
terraform -chdir="$TF_DIR/app" init -input=false -upgrade=false
terraform -chdir="$TF_DIR/app" apply -auto-approve -var="image_tag=bootstrap"

APP_URL=$(terraform -chdir="$TF_DIR/app" output -raw app_url)

# ---------------------------------------------------------------------------
# 4. What to paste into the GitHub repo's settings.
# ---------------------------------------------------------------------------
echo "==> [4/4] done"
echo ""
echo "App URL (may take ~60s for the target group to go healthy):"
echo "  ${APP_URL}"
echo ""
echo "Repo variables to set (Settings > Secrets and variables > Actions > Variables) --"
echo "or with the gh CLI from the repo root:"
echo ""
echo "  gh variable set AWS_REGION        --body '${AWS_REGION}'"
echo "  gh variable set AWS_PLAN_ROLE_ARN --body '${PLAN_ROLE_ARN}'"
echo "  gh variable set AWS_DEPLOY_ROLE_ARN --body '${DEPLOY_ROLE_ARN}'"
echo "  gh variable set ECR_REPOSITORY    --body '${ECR_NAME}'"
echo ""
echo "Also create a 'production' GitHub Environment with a required reviewer"
echo "(Settings > Environments > New environment) -- the deploy role's trust"
echo "policy only accepts tokens minted for a job that ran under that exact"
echo "environment name."
