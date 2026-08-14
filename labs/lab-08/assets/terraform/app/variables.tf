variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "project_name" {
  type    = string
  default = "lab08-cicd"
}

variable "container_port" {
  description = "Port the app listens on inside the container."
  type        = number
  default     = 8080
}

variable "image_tag" {
  description = <<-EOT
    Tag of the image in ECR to run. deploy.sh passes "bootstrap" for the
    first-ever apply (before any pipeline has pushed a real build); the
    GitHub Actions deploy job passes the git SHA + run number on every
    merge to main after that.
  EOT
  type        = string
  default     = "bootstrap"
}

variable "desired_count" {
  description = "How many Fargate tasks the service keeps running."
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Fargate task-level CPU units (256 = 0.25 vCPU -- cheapest valid Fargate size)."
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Fargate task-level memory in MiB (512 is the minimum paired with 256 CPU units)."
  type        = string
  default     = "512"
}
