terraform {
  required_version = ">= 1.11.0" # use_lockfile (S3-native state locking) is GA from 1.11

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Remote state in S3. The bootstrap root's outputs (ECR URL + the two ECS role
  # ARNs) are read by the app root, and the app root is applied BY CI on an
  # ephemeral runner - so this state cannot live on my laptop. The bucket is
  # created once by the preflight step (aws s3api create-bucket) before this
  # runs; Terraform can't create the bucket that holds its own state.
  # use_lockfile = native S3 locking, so there's no separate DynamoDB table.
  backend "s3" {
    bucket       = "lab08-tfstate-350681797031"
    key          = "lab08/bootstrap.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }
}
