# ============================================================================
# outputs.tf — the values you need AFTER apply (some feed Part 3 in the portal)
# ============================================================================
# `terraform output <name>` prints one. Secrets are marked sensitive so they
# don't splash across the terminal — pull them with `terraform output -raw`
# OFF CAMERA when you paste them into the Azure Migrate appliance.

output "ec2_public_ip" {
  description = "Public IP of the source EC2 instance — browse http://<this> to see the app, and RDP to it."
  value       = aws_instance.source_vm.public_ip
}

output "ec2_private_ip" {
  description = "Private IP of the source EC2 instance."
  value       = aws_instance.source_vm.private_ip
}

output "ec2_instance_id" {
  description = "AWS instance ID — handy when confirming discovery in Azure Migrate."
  value       = aws_instance.source_vm.id
}

output "app_url" {
  description = "The link-shortener on the SOURCE cloud. This is what should look identical after cutover in Azure."
  value       = "http://${aws_instance.source_vm.public_ip}"
}

# --- SECRETS: read these OFF CAMERA, paste into the Migrate appliance ---
output "migrate_access_key_id" {
  description = "AWS access key ID for the Azure Migrate service account. OFF-CAMERA."
  value       = aws_iam_access_key.migrate_user_key.id
  sensitive   = true
}

output "migrate_secret_access_key" {
  description = "AWS secret access key for the Azure Migrate service account. OFF-CAMERA — terraform output -raw."
  value       = aws_iam_access_key.migrate_user_key.secret
  sensitive   = true
}

output "aws_region" {
  value = var.aws_region
}
