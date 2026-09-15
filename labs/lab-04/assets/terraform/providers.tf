# ============================================================================
# providers.tf, WHO Terraform talks to, and HOW
# ============================================================================
#
# Terraform itself doesn't know anything about Azure. It's a generic engine
# that reads .tf files and figures out what to create, change, or delete.
# The thing that actually knows how to call Azure's APIs is a PROVIDER,
# a plugin that Terraform downloads when you run `terraform init`.
#
# Division of labor:
#   Terraform reads your .tf files and builds the execution plan.
#   The provider knows the Azure REST API and makes the actual calls.
#
# Terraform is DECLARATIVE. You never write "create a VNet, then add a
# subnet", you write "a VNet and a subnet EXIST", and Terraform works out
# the steps and the order on its own.

terraform {
  # Minimum Terraform version. Locking this means the config fails fast
  # with a clear message on an old binary, instead of a weird syntax error.
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      # Where the plugin comes from: HashiCorp's public registry.
      source = "hashicorp/azurerm"

      # "~> 3.0" means "any 3.x version, but never 4.x".
      # WHY pin it: provider major versions change behavior. Pinning means
      # this config builds the same way in six months as it does today.
      # `terraform init` also writes .terraform.lock.hcl, which records the
      # EXACT version it downloaded, commit that file for the same reason.
      version = "~> 3.0"
    }
  }
}

# The provider block configures the plugin itself.
provider "azurerm" {
  # `features {}` is required by azurerm even when empty, it's where you'd
  # opt into provider-wide behaviors (e.g. "purge key vaults on destroy").
  # Empty = sensible defaults. Leaving it out is a hard error.
  features {}

  # --- HOW AUTH WORKS (nothing to configure here, that's the point) ---
  # There are no credentials in this file, on purpose. When the provider
  # needs to call Azure, it walks a chain of auth methods, and the first
  # one it finds wins. For local work that's the AZURE CLI: you run
  # `az login` once, the CLI caches a token, and Terraform quietly borrows
  # it. Same trick the portal's Cloud Shell uses, you're already logged
  # in there, so Terraform "just works".
  #
  # Which subscription does it land in? Whatever `az account show` says.
  # Check it BEFORE you apply. Switch with:
  #   az account set --subscription "<name-or-id>"
  #
  # In a pipeline (no human to run az login) you'd use a service principal
  # or managed identity via environment variables instead, the code
  # doesn't change, only the auth method behind it.
}
