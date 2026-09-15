# ============================================================================
# providers.tf, WHO Terraform talks to on the Azure side, and HOW
# ============================================================================
# This is the Azure half. `azurerm` is the plugin that calls the Azure APIs;
# `null` is a tiny helper provider we use to DOCUMENT one manual step (the
# Azure Migrate project, which the azurerm provider can't create).
#
#   Terraform = the brain · Provider = the hands
#   Declarative: you declare what EXISTS; Terraform derives the order.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # any 3.x, never 4.x
    }
    # The null provider does nothing real, null_resource is a placeholder we
    # use to write a note in code about a step done by hand in the portal.
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  # Required even when empty, it's where provider-wide behaviors live.
  features {}

  # --- HOW AUTH WORKS (nothing hardcoded, that's the point) ---
  # No credentials here. Run `az login` ONCE (off camera), the CLI caches a
  # token, and Terraform borrows it. It lands in whatever `az account show`
  # says, check that BEFORE apply, switch with:
  #   az account set --subscription "<name-or-id>"
}
