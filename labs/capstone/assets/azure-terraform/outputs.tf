# ============================================================================
# outputs.tf, values you read after apply (feed the portal steps in Part 3-6)
# ============================================================================
# NOTE: the appliance public-IP outputs live in the appliances-*.tf.later
# files, so they only appear once you've renamed those files in.

output "source_resource_group" {
  value = azurerm_resource_group.source.name
}

output "target_resource_group" {
  value = azurerm_resource_group.target.name
}

output "vnet_name" {
  value = azurerm_virtual_network.main.name
}

output "target_subnet_id" {
  description = "Paste into Azure Migrate replication settings when prompted for the target subnet."
  value       = azurerm_subnet.main.id
}

output "replication_storage_account" {
  value = azurerm_storage_account.replication_cache.name
}

output "recovery_services_vault" {
  value = azurerm_recovery_services_vault.main.name
}

output "target_nsg_name" {
  description = "Attach this NSG to the migrated VM's NIC after cutover (opens 3389 + 80)."
  value       = azurerm_network_security_group.target_vm.name
}

output "migrate_project_name" {
  value = "migrate-project-${var.yourname} (create manually in portal)"
}
