# ============================================================================
# network.tf, the Azure landing zone: staging + target networks
# ============================================================================
# TWO resource groups, on purpose:
#   * rg-migrate-source-<name>  = the STAGING area. The appliances, cache
#     storage, Log Analytics, and Recovery Services Vault live here, all the
#     scaffolding of the migration. It also holds the VNet the migrated VM
#     lands in.
#   * rg-migrate-target-<name>  = where the MIGRATED VM is created at cutover.
#     Keeping it separate means you can nuke all the migration scaffolding
#     without touching the VM you just migrated.
#
# References between blocks (azurerm_resource_group.source.name, etc.) are what
# tell Terraform the create/destroy order, nobody writes the ordering.

# ---------------------------------------------------------------------------
# Staging resource group + the VNet the migrated VM will land in
# ---------------------------------------------------------------------------
resource "azurerm_resource_group" "source" {
  name     = "rg-migrate-source-${var.yourname}"
  location = var.location
  tags     = var.tags
}

# 10.1.0.0/16 is DELIBERATELY different from the AWS VPC's 10.0.0.0/16, so if
# you ever peer or VPN the two clouds together, the address ranges don't clash.
resource "azurerm_virtual_network" "main" {
  name                = "vnet-migrate-${var.yourname}"
  location            = azurerm_resource_group.source.location
  resource_group_name = azurerm_resource_group.source.name
  address_space       = ["10.1.0.0/16"]
  tags                = var.tags
}

resource "azurerm_subnet" "main" {
  name                 = "snet-migrate"
  resource_group_name  = azurerm_resource_group.source.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.1.0/24"]
}

# ---------------------------------------------------------------------------
# Target resource group, the migrated VM's home
# ---------------------------------------------------------------------------
resource "azurerm_resource_group" "target" {
  name     = "rg-migrate-target-${var.yourname}"
  location = var.location
  tags     = var.tags
}

# NSG that gets attached to the migrated VM after cutover. It opens RDP (3389)
# so you can log in AND port 80 so the link-shortener is reachable in Azure,
# that's the money-shot browse. (The PDF opens only 3389; we add 80 so the app
# is visible.)
resource "azurerm_network_security_group" "target_vm" {
  name                = "nsg-migrate-target-${var.yourname}"
  location            = var.location
  resource_group_name = azurerm_resource_group.target.name

  security_rule {
    name                       = "allow-rdp"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-http"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}
