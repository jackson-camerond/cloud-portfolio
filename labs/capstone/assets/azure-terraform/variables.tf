# ============================================================================
# variables.tf — the Azure side's knobs (values live in terraform.tfvars)
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
  description = "Tags stamped on every Azure resource — cost allocation + clean-up filter."
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
