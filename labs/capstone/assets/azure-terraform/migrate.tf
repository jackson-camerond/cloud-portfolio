# ============================================================================
# migrate.tf, the Azure Migrate scaffolding (cache, logs, vault, project)
# ============================================================================
# These are the moving parts Azure Migrate uses under the hood. None of them is
# the "migration tool" you click, they're the plumbing it runs on.

# ---------------------------------------------------------------------------
# Storage account, the replication CACHE
# ---------------------------------------------------------------------------
# During replication, disk data from the EC2 instance is written here first,
# then committed to the target managed disk. It's a buffer that absorbs the
# continuous delta syncs. It's temporary staging, so LRS (cheapest) is fine,
# lose it mid-replication and you just restart. Standard + StorageV2 are
# REQUIRED by Azure Migrate; other values fail replication setup.
resource "azurerm_storage_account" "replication_cache" {
  name                     = "stmigrate${var.yourname}" # <=24 chars, lowercase alnum, globally unique
  resource_group_name      = azurerm_resource_group.source.name
  location                 = azurerm_resource_group.source.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  min_tls_version          = "TLS1_2"
  tags                     = var.tags
}

# ---------------------------------------------------------------------------
# Log Analytics workspace, where discovery data + dependency maps land
# ---------------------------------------------------------------------------
# When you view discovered machines and their properties in the Migrate portal,
# that data is read from this workspace.
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-migrate-${var.yourname}"
  location            = azurerm_resource_group.source.location
  resource_group_name = azurerm_resource_group.source.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# ---------------------------------------------------------------------------
# Recovery Services Vault, orchestrates the replication (Azure Site Recovery)
# ---------------------------------------------------------------------------
# Agentless replication runs on Azure Site Recovery under the hood, and Site
# Recovery keeps its config/policies/state in this vault.
#   soft_delete_enabled = false  -> lets `terraform destroy` delete it cleanly
#                                   at end of lab (leave it ON in production).
#   cross_region_restore = false -> this is a migration, not a DR/backup setup.
resource "azurerm_recovery_services_vault" "main" {
  name                         = "rsv-migrate-${var.yourname}"
  location                     = azurerm_resource_group.source.location
  resource_group_name          = azurerm_resource_group.source.name
  sku                          = "Standard"
  soft_delete_enabled          = false
  cross_region_restore_enabled = false
  tags                         = var.tags
}

# ---------------------------------------------------------------------------
# Azure Migrate project, created BY HAND in the portal (documented here)
# ---------------------------------------------------------------------------
# The azurerm provider has NO resource type for an Azure Migrate project, so it
# can't be built in Terraform. This null_resource is a placeholder that records
# the manual steps and anchors the dependency chain. Do this in the portal
# after `terraform apply`:
#   1. Search "Azure Migrate" in the portal
#   2. Click "Create project"
#   3. Resource group: rg-migrate-source-<name>
#   4. Project name: migrate-project-<name>
#   5. Geography: United States
#   6. Click Create
resource "null_resource" "migrate_project_reminder" {
  triggers = {
    resource_group = azurerm_resource_group.source.name
  }
}
