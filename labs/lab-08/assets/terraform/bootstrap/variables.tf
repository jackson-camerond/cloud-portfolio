variable "aws_region" {
  description = "Region for the whole lab. Locked to us-west-2 for this project."
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Short name used as a prefix on every resource this lab creates."
  type        = string
  default     = "lab08-cicd"
}

variable "github_org" {
  description = "GitHub org or username that owns the repo the OIDC trust policy allows."
  type        = string
}

variable "github_repo" {
  description = "Repo name (no org prefix) the OIDC trust policy allows."
  type        = string
}
