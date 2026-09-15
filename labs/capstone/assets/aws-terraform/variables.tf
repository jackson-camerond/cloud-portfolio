# ============================================================================
# variables.tf, the AWS side's knobs (values live in terraform.tfvars)
# ============================================================================
# A `variable` block DECLARES an input. It doesn't set the value, that comes
# from terraform.tfvars (see terraform.tfvars.example). Keeping values out of
# the code is why the same main.tf works for anyone who changes the tfvars.

variable "aws_region" {
  description = "AWS region to deploy the source EC2 instance into. us-east-1 pairs with Azure 'East US', same coast keeps cloud-to-cloud replication fast."
  type        = string
  default     = "us-east-1"
}

variable "yourname" {
  description = "Short name, lowercase, no spaces. Makes resource names unique. This lab uses 'cam' to match the rest of the series (owner=cam)."
  type        = string
  default     = "cam"
}

variable "windows_ami" {
  description = "Optional override for the Windows Server 2022 Base AMI. Leave EMPTY (the default) to let Terraform look up the current AWS-owned image at plan time via the data.aws_ami block in main.tf, that avoids the stale/deregistered-AMI failure that hung discovery at 'collecting instance settings'. Only set this to pin a specific AMI ID."
  type        = string
  default     = ""
}

variable "instance_type" {
  description = "EC2 instance size. t3.medium (2 vCPU / 4 GB) is the practical minimum for Windows Server to run without crawling."
  type        = string
  default     = "t3.medium"
}

variable "admin_password" {
  description = "Windows Administrator password for the source EC2 instance. Set in terraform.tfvars, NEVER committed. sensitive=true keeps it out of CLI output. Rotate/tear down after the shoot."
  type        = string
  sensitive   = true
}
