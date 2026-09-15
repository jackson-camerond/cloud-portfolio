# ============================================================================
# providers.tf — WHO Terraform talks to on the AWS side, and HOW
# ============================================================================
#
# This is the AWS half of the migration. Terraform itself is a generic engine;
# the plugin that actually knows how to call the AWS APIs is the `aws`
# PROVIDER — the exact counterpart of `azurerm` on the Azure side. `terraform
# init` downloads it.
#
#   Terraform = the brain (reads .tf files, builds the plan)
#   Provider  = the hands (knows the AWS API, makes the real calls)
#
# Terraform is DECLARATIVE: you don't script "make a VPC, then a subnet." You
# declare that a VPC and a subnet EXIST, and Terraform works out the order from
# the references between blocks.

terraform {
  # Fail fast on an old binary with a clear message instead of a weird error.
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      # HashiCorp's public registry.
      source = "hashicorp/aws"

      # "~> 5.0" = any 5.x, never 6.x. Pinning means this config builds the
      # same way in six months. `init` also writes .terraform.lock.hcl with the
      # EXACT version — commit that file.
      version = "~> 5.0"
    }
  }
}

# The provider block configures the plugin itself.
provider "aws" {
  # Region comes from a variable so it can change without touching main.tf.
  region = var.aws_region

  # --- HOW AUTH WORKS (nothing hardcoded here — on purpose) ---
  # No keys in this file. The provider walks a chain of auth methods and the
  # first it finds wins. For local work that's the shared credentials file the
  # AWS CLI writes: you run `aws configure` ONCE (off camera), the CLI caches
  # your Access Key ID + Secret, and Terraform quietly borrows them.
  #
  # NEVER put an access key in a .tf or .tfvars file. `aws configure` off
  # camera, confirm with `aws sts get-caller-identity`, then apply.
}
