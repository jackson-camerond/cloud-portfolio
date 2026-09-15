# ============================================================================
# network.tf — the core resources: resource group, VNet, subnet
# ============================================================================
#
# A RESOURCE block is the heart of Terraform. The shape is always:
#
#   resource "<type>" "<local-name>" { ...settings... }
#
#   <type>       = what to build (azurerm_resource_group = an Azure RG).
#                  The azurerm_ prefix tells you which provider owns it.
#   <local-name> = what THIS config calls it ("rg"). It is NOT the Azure
#                  name — it's a code-side handle other blocks use to
#                  reference this one. The Azure name is the `name` argument.
#
# Order of blocks in the file does NOT matter. Terraform builds a
# dependency graph from the REFERENCES between blocks and works out the
# creation order itself. Watch for that below.

# ---------------------------------------------------------------------------
# 1. Resource group — the container everything lives in
# ---------------------------------------------------------------------------
# Same reason as always: one group = one lab = one clean teardown. Delete
# the group (or `terraform destroy`) and everything in it dies together.
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name # <- value comes from variables.tf
  location = var.location
  tags     = var.tags
}

# ---------------------------------------------------------------------------
# 2. Virtual network — the private address space
# ---------------------------------------------------------------------------
resource "azurerm_virtual_network" "vnet" {
  name          = var.vnet_name
  address_space = var.vnet_address_space

  # THESE TWO LINES ARE THE MAGIC. They don't hardcode "East US" or the RG
  # name — they REFERENCE the resource group block above by its handle:
  # "the rg resource's location", "the rg resource's name".
  #
  # That reference does two jobs at once:
  #   1. Keeps values in sync — rename the RG, the VNet follows.
  #   2. Creates an IMPLICIT DEPENDENCY — Terraform sees the VNet needs a
  #      value from the RG, so it knows the RG must be created FIRST.
  #      Nobody writes the ordering; the references ARE the ordering.
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = var.tags
}

# ---------------------------------------------------------------------------
# 3. Subnet — a slice of the VNet
# ---------------------------------------------------------------------------
# 10.0.1.0/24 is carved out of the VNet's 10.0.0.0/16. A VNet can hold many
# subnets — each one is a separate network segment, and (from Lab 02) a
# subnet is what you attach firewall rules to. That's why subnets exist.
resource "azurerm_subnet" "subnet" {
  name                 = var.subnet_name
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name # <- depends on the VNet
  address_prefixes     = var.subnet_prefix
}

# So the graph Terraform derives, without being told:
#   resource group  ->  virtual network  ->  subnet
# On `apply` they create in that order; on `destroy` it reverses the arrows
# and deletes subnet -> vnet -> rg. Same graph, walked backwards.
