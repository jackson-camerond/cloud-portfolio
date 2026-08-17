# Lab 08 - bootstrap root.
#
# Everything here is long-lived and rarely changes: the GitHub OIDC trust,
# the two CI roles, the ECS roles, and the ECR repo. It's applied ONCE by a
# human (deploy.sh, Step 1) and never by the pipeline itself.
#
# That split is deliberate: the GitHub Actions deploy role (below) can push
# images and update the ECS service, but it CANNOT create or edit IAM roles
# - including its own. A pipeline role that could modify its own trust
# policy would be one bad PR away from granting itself admin. Keeping this
# root out of CI's reach removes that whole class of risk.

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# 1. The GitHub OIDC identity provider - lets GitHub Actions prove who it is
#    without ever holding a long-lived AWS access key.
# ---------------------------------------------------------------------------

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]

  # No thumbprint_list: GitHub's OIDC signing certificate chains to a CA in
  # AWS's own trusted root store, so AWS verifies it directly and ignores
  # any thumbprint supplied here. (Confirmed against the current
  # hashicorp/aws provider docs for aws_iam_openid_connect_provider.)
}

# ---------------------------------------------------------------------------
# 2. The "plan" role - read-only, any branch or pull request. Used by the
#    validate job so a PR from any branch can run `terraform plan` and see
#    what would change, without being able to change anything.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "gha_plan_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # StringLike + wildcard: any branch, any PR, in this one repo.
    # Read-only permissions make that breadth safe.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "gha_plan" {
  name               = "${var.project_name}-gha-plan"
  assume_role_policy = data.aws_iam_policy_document.gha_plan_assume.json
}

resource "aws_iam_role_policy" "gha_plan" {
  name   = "${var.project_name}-gha-plan-readonly"
  role   = aws_iam_role.gha_plan.id
  policy = file("${path.module}/../policies/gha-plan-policy.json")
}

# ---------------------------------------------------------------------------
# 3. The "deploy" role - can only be assumed by a workflow run that has
#    already cleared the "production" GitHub Environment's required
#    reviewer. GitHub stamps the environment name into the OIDC token's
#    `sub` claim, and the trust policy pins on it - the approval gate is
#    enforced by AWS itself, not just by GitHub's UI.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "gha_deploy_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:environment:production"]
    }
  }
}

resource "aws_iam_role" "gha_deploy" {
  name               = "${var.project_name}-gha-deploy"
  assume_role_policy = data.aws_iam_policy_document.gha_deploy_assume.json
}

resource "aws_iam_role_policy" "gha_deploy" {
  name = "${var.project_name}-gha-deploy-app"
  role = aws_iam_role.gha_deploy.id
  policy = templatefile("${path.module}/../policies/gha-deploy-policy.json.tpl", {
    execution_role_arn = aws_iam_role.ecs_execution.arn
    task_role_arn      = aws_iam_role.ecs_task.arn
  })
}

# ---------------------------------------------------------------------------
# 4. ECS task roles - two roles, two jobs. The execution role is how ECS
#    itself pulls the image and ships logs. The task role is what the app
#    inside the container could use if it ever needs an AWS permission.
#    Today it needs none - that's the point. Adding one later means adding
#    a policy here, never touching the execution role.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project_name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
  # Intentionally no attached policy. Least privilege as a starting point,
  # not an afterthought.
}

# ---------------------------------------------------------------------------
# 5. ECR - the private registry the pipeline pushes into and ECS pulls from.
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "app" {
  name                 = "${var.project_name}-app"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  # A lab repo has no rollback traffic to protect - force_delete lets
  # teardown.sh remove it even with images still inside.
  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 10 images, expire the rest"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
