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
  description = "Windows Administrator password for the source EC2 instance. Set in terraform.tfvars, NEVER committed. sensitive=true keeps it out of CLI output. Rotate it or tear the lab down the same day."
  type        = string
  sensitive   = true
}

variable "admin_cidr" {
  description = "The one address range allowed to RDP (3389) to the source EC2 instance, normally your own public IP as a /32 (e.g. 203.0.113.10/32). No default on purpose: it has to be set, and 0.0.0.0/0 is rejected."
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && !endswith(var.admin_cidr, "/0")
    error_message = "admin_cidr must be a valid CIDR such as 203.0.113.10/32, and not an open /0 range."
  }
}
