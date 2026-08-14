# Reuses the account's default VPC -- a dedicated hub-spoke network is
# Lab 14's job, not this one. Two of its default public subnets, in two
# different AZs, are enough for an ALB (which requires >= 2 AZs) and for
# Fargate tasks that get a public IP directly -- no NAT Gateway, which would
# otherwise be the single biggest line item on this lab's bill.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

locals {
  # First two default subnets, in two different AZs -- what the ALB needs
  # and all the app tier needs.
  subnet_ids = slice(sort(data.aws_subnets.default.ids), 0, 2)
}

# The bootstrap root's state -- read-only from here. This app root never
# creates or edits IAM; it only reads the two role ARNs and the ECR repo
# bootstrap already made.
data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  # Reads bootstrap's state from S3 (not a local file), so the CI runner — which
  # never has the bootstrap state on disk — can still resolve the ECR URL and
  # the two ECS role ARNs bootstrap produced.
  config = {
    bucket = "lab08-tfstate-350681797031"
    key    = "lab08/bootstrap.tfstate"
    region = "us-west-2"
  }
}
