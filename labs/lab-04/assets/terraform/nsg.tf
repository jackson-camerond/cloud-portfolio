# ============================================================================
# nsg.tf — network security group + attach it to the subnet
# ============================================================================
#
# This file is the "add a resource to a LIVE environment" act. Terraform
# reads EVERY .tf file in the folder as one configuration — file names are
# purely for humans. Drop this file in next to the others, run plan, and
# Terraform compares the new full picture against the state file, sees the
# RG / VNet / subnet already exist and are unchanged, and plans ONLY the
# two new resources below. It never rebuilds what it already has — that's
# the whole superpower of state + plan.
#
# (For the shoot: this file is parked one directory up as ../nsg.tf.later
# before recording — out of the folder Terraform reads AND out of the VS Code
# file tree — and moved back on camera.)

# ---------------------------------------------------------------------------
# 4. Network security group — the firewall rule set
# ---------------------------------------------------------------------------
# An NSG is a stateful firewall: a list of allow/deny rules evaluated by
# priority (lowest number wins), with a built-in DenyAllInBound at the
# bottom catching whatever no rule allowed. "Stateful" = it tracks
# connections, so an allowed request's reply is allowed back automatically.
resource "azurerm_network_security_group" "nsg" {
  name                = var.nsg_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  # The assignment ships this NSG empty. Leveling it up: an empty firewall
  # attached to nothing proves nothing, so this one carries a real rule and
  # gets attached to the subnet below.
  #
  # Rules can be written inline like this, or as separate
  # azurerm_network_security_rule resources (better when many rules or many
  # NSGs). Inline is easier to read for one rule, so inline it is.
  security_rule {
    name                       = "Allow-HTTP-Inbound"
    priority                   = 100 # lowest number = evaluated first
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"  # source port is random client-side — always *
    destination_port_range     = "80" # the one door we open
    source_address_prefix      = "*"  # a web tier faces the internet
    destination_address_prefix = "*"
    description                = "Web traffic in on 80; everything else falls through to the default deny."
  }

  # The Lab 02 pattern, as code, for reference — a DB-tier NSG would scope
  # its one rule to the web subnet only. Same shape, tighter source:
  #   destination_port_range = "1433"
  #   source_address_prefix  = "10.0.1.0/24"

  tags = var.tags
}

# ---------------------------------------------------------------------------
# 5. Attach the NSG to the subnet
# ---------------------------------------------------------------------------
# In the portal this is a dropdown on the subnet. In Terraform the
# attachment is its OWN resource — which is honest: the link between two
# things is itself a piece of infrastructure you can create and destroy.
resource "azurerm_subnet_network_security_group_association" "subnet_nsg" {
  subnet_id                 = azurerm_subnet.subnet.id
  network_security_group_id = azurerm_network_security_group.nsg.id

  # No depends_on needed here — and that's worth understanding. The two
  # references above already tell Terraform "the subnet and the NSG must
  # exist before this link can". That's an IMPLICIT dependency, and it
  # covers ~95% of cases.
  #
  # `depends_on = [ ... ]` is the EXPLICIT version, for the rare case where
  # resource A must wait on resource B but never references any of B's
  # values (e.g. an app deployment that needs a role assignment to finish
  # propagating first). Rule of thumb: let references do the ordering;
  # reach for depends_on only when there's a real ordering need the
  # references can't express.
}

# This output lives here rather than in outputs.tf on purpose: it reads the
# NSG resource above, so it has to enter and leave the configuration together
# with this file (the shoot parks this file pre-record — see the note at the
# top). An output referencing a resource that isn't declared fails validate.
output "nsg_name" {
  description = "The firewall attached to the subnet."
  value       = azurerm_network_security_group.nsg.name
}
