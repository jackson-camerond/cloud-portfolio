output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecr_repository_name" {
  value = aws_ecr_repository.app.name
}

output "ecs_execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}

output "gha_plan_role_arn" {
  description = "Put this in the repo variable AWS_PLAN_ROLE_ARN."
  value       = aws_iam_role.gha_plan.arn
}

output "gha_deploy_role_arn" {
  description = "Put this in the repo variable AWS_DEPLOY_ROLE_ARN."
  value       = aws_iam_role.gha_deploy.arn
}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}
