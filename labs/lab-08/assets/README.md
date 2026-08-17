# Lab 08 assets - End-to-End CI/CD Pipeline

What's here, one command to stand it up, one to tear it down.

```
assets/
  app/                     the app the pipeline ships (stdlib-only Python + Dockerfile)
  terraform/
    bootstrap/             OIDC provider, IAM roles, ECR repo - applied by a human, once
    app/                   ALB, ECS cluster/service, security groups - applied by CI, every merge
    policies/               the two IAM policy JSON docs the bootstrap roles use
  .github/
    workflows/ci-cd.yml     the pipeline (copy to .github/workflows/ at the repo root)
    dependabot.yml           keeps the pipeline's own pinned Actions current (copy to .github/)
  cli/
    deploy.sh               one-time bootstrap (idempotent)
    teardown.sh              tears everything down (idempotent)
```

## Deploy

```bash
cd labs/lab-08/assets/cli
GITHUB_ORG=your-gh-username GITHUB_REPO=your-repo-name ./deploy.sh
```

This builds the *first* version of everything by hand: the OIDC trust, the
two CI roles, the ECR repo, a seed image, and the ECS Fargate service behind
an ALB. Everything after this first run ships through `ci-cd.yml` instead.
Re-running `deploy.sh` is safe - Terraform only changes what drifted.

Then, once (from the repo root, with the `gh` CLI):

```bash
gh variable set AWS_REGION          --body us-west-2
gh variable set AWS_PLAN_ROLE_ARN   --body "$(terraform -chdir=terraform/bootstrap output -raw gha_plan_role_arn)"
gh variable set AWS_DEPLOY_ROLE_ARN --body "$(terraform -chdir=terraform/bootstrap output -raw gha_deploy_role_arn)"
gh variable set ECR_REPOSITORY      --body "$(terraform -chdir=terraform/bootstrap output -raw ecr_repository_name)"
```

And create a **`production`** GitHub Environment (Settings -> Environments)
with at least one required reviewer. The deploy role's trust policy only
accepts a token whose `sub` claim reads
`repo:<org>/<repo>:environment:production` - without that environment
existing and being approved, AWS refuses the role, full stop.

## Teardown

```bash
cd labs/lab-08/assets/cli
./teardown.sh
```

Destroys the app stack, then the bootstrap stack. Confirms empty in the
script's last line.

## Design decisions worth saying out loud

**Two Terraform roots, not one, and CI only ever touches the second one.**
`bootstrap/` holds the OIDC provider and both GitHub Actions IAM roles;
`app/` holds the ALB, the ECS service, and the security groups. The deploy
role's permissions (`terraform/policies/gha-deploy-policy.json.tpl`) can
create and update everything in `app/` but hold **zero** `iam:*` actions
beyond a `PassRole` scoped to exactly two ARNs. A pipeline role that could
edit IAM roles - including its own trust policy - is one merged PR away
from granting itself admin. Splitting the roots removes that failure mode
by construction instead of relying on a reviewer to catch it in every PR.

**No NAT Gateway.** The Fargate tasks run in the account's default public
subnets with `assign_public_ip = true`, so they reach the ECR API and
CloudWatch Logs directly over their own public IP. A NAT Gateway is the
"correct" production answer for private subnets, but it bills by the hour
whether the lab is being watched or not - for a $1-2/day lab, that's the
wrong trade. The task's security group only allows port 443 out, so the
convenience doesn't turn into an open egress hole.

**Checkov runs as a hard gate (`soft_fail: false`), with 13 named skips.**
Every skip below is a real, verified finding from running Checkov against
this exact code - not a guess. They fall into three groups:

| Group | IDs skipped | Why | Production fix |
|---|---|---|---|
| No HTTPS in this lab | `CKV_AWS_2`, `CKV_AWS_103`, `CKV_AWS_378`, `CKV2_AWS_20`, `CKV2_AWS_28`, `CKV_AWS_260` | No domain name, no ACM cert budgeted for a lab | ACM cert + HTTPS listener + HTTP->HTTPS redirect + WAF |
| Cost-bounded choices | `CKV_AWS_150`, `CKV_AWS_91`, `CKV_AWS_65`, `CKV_AWS_333`, `CKV_AWS_338` | Deletion protection off (so `teardown.sh` actually works), no S3 access-log bucket, Container Insights off (that's Lab 10's job), task gets a public IP instead of a NAT Gateway, 7-day log retention instead of a year | Turn each on; they cost real money or storage to run continuously |
| Default AWS-managed encryption | `CKV_AWS_158`, `CKV_AWS_136` | AES-256 at rest is already on (CloudWatch Logs and ECR both encrypt by default); a customer-managed KMS key adds cost and rotation overhead a lab doesn't need | Point the log group and the ECR repo's `encryption_configuration` at a CMK |

Everything **not** on that list fails the build. Two real fixes came out of
running the scanner rather than skipping around it: the ALB's
`drop_invalid_header_fields` (free, no tradeoff, just wasn't on by default)
and both security groups' egress rules, which were `0.0.0.0/0` on all ports
until Checkov's `CKV_AWS_382` called it out - now the ALB can only reach
the app tier's one port, and the app tier can only leave on 443.

**Trivy scans the built image before it's ever pushed.** `exit-code: 1`
with `severity: CRITICAL,HIGH` means a vulnerable base image fails the PR,
not the deploy. The Dockerfile also runs the app as a non-root user --
one of the first things a container scanner flags, fixed at the source.

**ECR tags are `IMMUTABLE`.** Once an image is pushed under a tag, that tag
can never be overwritten - a real defense against a tag-substitution
supply-chain attack. The tradeoff: a workflow *re-run* on the same commit
can't reuse the same tag, so the deploy job tags images
`${{ github.sha }}-${{ github.run_number }}`, which is unique even across
re-runs of the same commit.

**Every third-party GitHub Action is pinned to a commit SHA, not a version
tag.** A tag like `@v12` is just a pointer - whoever controls the repo can
move it. That stopped being a hypothetical in March 2026, when
`aquasecurity/trivy-action` - one of the two scanners this pipeline runs on
every pull request - had its own release tags force-pushed to a malicious
commit in a real supply-chain compromise. A commit SHA can't be silently
repointed the same way. `.github/dependabot.yml` is what keeps a SHA pin
from going stale: it opens a pull request to bump each pin to the latest
release, and that PR still has to clear `terraform-plan`, Checkov, and Trivy
like any other change before it merges.

**Remote state lives in S3** (`lab08-tfstate-350681797031`), using Terraform's
native S3 lockfile, no DynamoDB. It's required, not optional: CI applies the
app root on an ephemeral runner, so the state can't be a local file. Reusable
modules + multi-environment remote state are Lab 11's whole subject ("Reusable
Terraform Modules"), which builds on top of this.
