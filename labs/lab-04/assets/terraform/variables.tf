# ============================================================================
# variables.tf — the knobs (every value you might want to change, in one place)
# ============================================================================
#
# A VARIABLE is an input to the configuration. Instead of hardcoding
# "East US" in five places, you declare it once here and reference it as
# var.location everywhere else. Change it once, everything follows.
#
# Where do values come from? In priority order (last one wins):
#   1. The `default` written here
#   2. A terraform.tfvars file in this folder (auto-loaded)
#   3. -var flags on the command line
#
# Every variable here has a default, so the lab runs with ZERO extra setup:
# init / plan / apply and go. terraform.tfvars.example shows how you'd
# override them.
#
# NOTE ON SECRETS: this lab creates only network resources, so there are no
# passwords here. When a lab DOES need one, the rule is: declare it as a
# variable with `sensitive = true` (so plan/apply output hides it), give it
# a CHANGE_ME placeholder, put the real value only in the gitignored
# terraform.tfvars — and rotate it after the recording, always.

variable "resource_group_name" {
  description = "Name of the resource group everything in this lab lives in (and dies with)."
  type        = string
  default     = "rg-lab04-tf-cam"
}

variable "location" {
  description = "Azure region for every resource. One variable = the whole lab moves regions with a one-line change."
  type        = string
  default     = "East US"
}

variable "vnet_name" {
  description = "Name of the virtual network."
  type        = string
  default     = "vnet-terraform"
}

variable "vnet_address_space" {
  description = "The VNet's private address space. /16 = about 65k addresses to carve subnets from."
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_name" {
  description = "Name of the subnet."
  type        = string
  default     = "snet-backend"
}

variable "subnet_prefix" {
  description = "The subnet's slice of the VNet address space. Must sit inside vnet_address_space."
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "nsg_name" {
  description = "Name of the network security group attached to the subnet."
  type        = string
  default     = "nsg-web"
}

variable "tags" {
  description = "Tags stamped on every resource — lets you filter, cost-track, and bulk-delete the lab as one set."
  type        = map(string)
  default = {
    env     = "lab"
    owner   = "cam"
    project = "lab04"
  }
}
