# ============================================================================
# variables.tf, the Azure side's knobs (values live in terraform.tfvars)
# ============================================================================

variable "yourname" {
  description = "Short name, lowercase, no spaces. MUST match the AWS side. This lab uses 'cam'. Note: the storage account name stmigrate<yourname> must stay <= 24 chars, lowercase alphanumeric."
  type        = string
  default     = "cam"
}

variable "location" {
  description = "Azure region for the target + staging resources. 'East US' pairs with AWS us-east-1 (same coast = fast replication). This diverges from the other labs' West US 2 on purpose."
  type        = string
  default     = "East US"
}

variable "tags" {
  description = "Tags stamped on every Azure resource, cost allocation + clean-up filter."
  type        = map(string)
  default = {
    project    = "azure-migrate-lab"
    owner      = "cam"
    managed_by = "terraform"
  }
}

# --- Appliance VM passwords: SECRETS. Set in terraform.tfvars, never commit. ---
variable "appliance_admin_password" {
  description = "Admin password for the Azure Migrate DISCOVERY appliance VM. >=12 chars, upper/lower/digit/symbol."
  type        = string
  sensitive   = true
}

variable "replication_admin_password" {
  description = "Admin password for the REPLICATION appliance VM. >=12 chars, upper/lower/digit/symbol."
  type        = string
  sensitive   = true
}

variable "admin_cidr" {
  description = "The one address range allowed to RDP (3389) to the appliance VMs and the migrated VM, normally your own public IP as a /32 (e.g. 203.0.113.10/32). No default on purpose: it has to be set, and an open /0 range is rejected."
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && !endswith(var.admin_cidr, "/0")
    error_message = "admin_cidr must be a valid CIDR such as 203.0.113.10/32, and not an open /0 range."
  }
}
