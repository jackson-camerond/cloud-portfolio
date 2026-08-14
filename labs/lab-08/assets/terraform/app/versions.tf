terraform {
  required_version = ">= 1.11.0" # use_lockfile (S3-native state locking) is GA from 1.11

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Remote state in S3 — REQUIRED because the CI pipeline applies this root on a
  # GitHub runner that starts empty every run. Local state would be invisible to
  # the runner (and two applies could clobber each other). Same bucket as
  # bootstrap, different key. use_lockfile = native S3 locking (no DynamoDB).
  backend "s3" {
    bucket       = "lab08-tfstate-350681797031"
    key          = "lab08/app.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }
}
