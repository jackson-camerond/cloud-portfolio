resource "aws_ecs_cluster" "app" {
  name = "${var.project_name}-cluster"

  # Container Insights costs a little extra CloudWatch ingestion - Lab 10
  # ("Observability & Alerting") is where that gets turned on deliberately.
  # Off here keeps this lab's bill to the ALB + Fargate line items only.
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 7 # short retention - this is a lab, not an audit trail
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = data.terraform_remote_state.bootstrap.outputs.ecs_execution_role_arn
  task_role_arn            = data.terraform_remote_state.bootstrap.outputs.ecs_task_role_arn

  runtime_platform {
    cpu_architecture        = "ARM64" # Graviton - cheaper than x86, and it
    operating_system_family = "LINUX" # matches the arm64 Mac building the image, so no cross-compile flag needed.
  }

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = "${data.terraform_remote_state.bootstrap.outputs.ecr_repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "APP_VERSION", value = var.image_tag },
        { name = "PORT", value = tostring(var.container_port) }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-svc"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.subnet_ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = true # no NAT Gateway in this lab - see network.tf
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = var.container_port
  }

  # Every new task definition revision (a new image tag from the pipeline)
  # rolls out here automatically - this IS the "update ECS service" step.
  depends_on = [aws_lb_listener.http]
}
