# ============================================================================
# outputs.tf, what Terraform reports back when it's done
# ============================================================================
#
# An OUTPUT is a value Terraform prints at the end of `apply` (and any time
# you run `terraform output`). Two reasons they exist:
#
#   1. For humans, surface the handful of values you actually need after a
#      deploy (an IP to browse to, a hostname to point DNS at) instead of
#      digging through the portal.
#   2. For other code, outputs are how one Terraform configuration hands
#      values to another (or to a CI pipeline). They're the public API of
#      this folder.
#
# This lab is pure networking, no VM, so no public IP to print. These
# outputs prove the build and hand back the IDs that a follow-on config
# (say, one that adds the Lab 02 VMs) would consume.

output "resource_group_name" {
  description = "The lab's resource group, the one thing to check in the portal, and the blast radius of terraform destroy."
  value       = azurerm_resource_group.rg.name
}

output "vnet_id" {
  description = "Full Azure resource ID of the VNet, what a later config would reference to place VMs into this network."
  value       = azurerm_virtual_network.vnet.id
}

output "subnet_id" {
  description = "Resource ID of the subnet, a VM's NIC would attach here."
  value       = azurerm_subnet.subnet.id
}

# The NSG's output lives in nsg.tf, next to the resource it reads, that file
# is staged in and out during the shoot, and the output has to appear and
# disappear with it or validate breaks while the file is parked.

# If an output were ever secret (a generated password, a connection
# string), you'd add `sensitive = true`, Terraform then masks it in the
# terminal. It is STILL plaintext inside terraform.tfstate, which is one
# more reason state never gets committed.
