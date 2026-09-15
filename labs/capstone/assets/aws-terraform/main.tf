# ============================================================================
# main.tf, the AWS SOURCE environment we are going to migrate FROM
# ============================================================================
#
# The shape of every resource block is always the same:
#   resource "<type>" "<local-name>" { ...settings... }
#   <type>       = what to build (aws_vpc = an AWS VPC).
#   <local-name> = the code-side handle other blocks reference. NOT the AWS name.
#
# Block ORDER doesn't matter. Terraform reads the references between blocks,
# builds a dependency graph, and works out the create/destroy order itself.
#
# What this file builds (10 resources): a VPC + internet gateway + route table
# + public subnet + a security group, an IAM role/user for Azure Migrate to
# read the account, and ONE Windows Server 2022 EC2 instance that boots up
# running the link-shortener app. That EC2 instance is the "workload" we lift
# and shift to Azure.

# ---------------------------------------------------------------------------
# 1. VPC, the private network boundary (AWS's version of an Azure VNet)
# ---------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16" # 65,536 addresses. Roomy on purpose; standard size.

  # DNS hostnames let Azure Migrate identify and reach the instance during
  # discovery. Turn both on.
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "vpc-migrate-${var.yourname}"
    project = "azure-migrate-lab"
  }
}

# ---------------------------------------------------------------------------
# 2. Internet gateway, the VPC's door to the public internet
# ---------------------------------------------------------------------------
# Without this the EC2 instance can't call AWS APIs and Azure Migrate's
# appliance (over in Azure) can't reach it. The gateway itself is free.
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "igw-migrate-${var.yourname}"
  }
}

# ---------------------------------------------------------------------------
# 3. Route table + association, send internet-bound traffic to the gateway
# ---------------------------------------------------------------------------
# The 0.0.0.0/0 route ("everything not local") points at the internet gateway.
# Associating it with the subnet is what makes that subnet PUBLIC.
resource "aws_route_table" "main" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = {
    Name = "rt-migrate-${var.yourname}"
  }
}

resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true # the instance gets a public IP automatically
  tags = {
    Name = "snet-migrate-${var.yourname}"
  }
}

resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.main.id
}

# ---------------------------------------------------------------------------
# 4. Security group, a stateful firewall on the instance (AWS's version of an NSG)
# ---------------------------------------------------------------------------
# NOTE, the name canNOT start with "sg-": AWS reserves that prefix for
# system-generated IDs. We use "migrate-source-sg-...".
#
# LAB-ONLY exposure. Everything here is open to 0.0.0.0/0 because it's a
# short-lived lab that gets torn down the same day. In production you scope
# every one of these to specific IPs. Say that on camera.
resource "aws_security_group" "source_vm" {
  name        = "migrate-source-sg-${var.yourname}"
  description = "Allow app (80), Azure Migrate (443/5985), and RDP (3389)"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP for the link-shortener app (the workload being migrated)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS for Azure Migrate appliance communication"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "WinRM (HTTP) so Azure Migrate can do OS-level discovery over 5985"
    from_port   = 5985
    to_port     = 5985
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "RDP for admin access (LAB ONLY - restrict to your IP in prod)"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound (AWS API calls + Azure Migrate)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "migrate-source-sg-${var.yourname}"
  }
}

# ---------------------------------------------------------------------------
# 5. IAM for Azure Migrate, least-privilege read access into this AWS account
# ---------------------------------------------------------------------------
# Azure Migrate needs to READ EC2 metadata and snapshot the disk to replicate
# it. This role/policy defines exactly what it may do and nothing more:
# describe-only calls plus Create/DeleteSnapshot (it takes a temp snapshot,
# copies the data, deletes it).
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "migrate_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeInstances",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeVolumes",
      "ec2:DescribeSnapshots",
      "ec2:DescribeImages",
      "ec2:DescribeRegions",
      "ec2:CreateSnapshot",
      "ec2:DeleteSnapshot",
      "ec2:DescribeTags",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "migrate_role" {
  name               = "role-azure-migrate-${var.yourname}"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags = {
    project = "azure-migrate-lab"
  }
}

resource "aws_iam_policy" "migrate_policy" {
  name   = "policy-azure-migrate-${var.yourname}"
  policy = data.aws_iam_policy_document.migrate_permissions.json
}

resource "aws_iam_role_policy_attachment" "migrate_attach" {
  role       = aws_iam_role.migrate_role.name
  policy_arn = aws_iam_policy.migrate_policy.arn
}

resource "aws_iam_instance_profile" "migrate_profile" {
  name = "profile-azure-migrate-${var.yourname}"
  role = aws_iam_role.migrate_role.name
}

# Azure Migrate can't assume a role across clouds, it authenticates to AWS
# with a STATIC access key + secret. This dedicated user holds ONLY the policy
# above. Its key/secret get pasted into the Migrate appliance in the portal.
# THOSE VALUES ARE SECRETS, read them off-camera (see outputs.tf), never show
# them on screen, and this user is deleted with `terraform destroy`.
resource "aws_iam_user" "migrate_user" {
  name = "svc-azure-migrate-${var.yourname}"
  tags = {
    project = "azure-migrate-lab"
  }
}

resource "aws_iam_user_policy_attachment" "migrate_user_policy" {
  user       = aws_iam_user.migrate_user.name
  policy_arn = aws_iam_policy.migrate_policy.arn
}

resource "aws_iam_access_key" "migrate_user_key" {
  user = aws_iam_user.migrate_user.name
}

# ---------------------------------------------------------------------------
# 6. The source EC2 instance, Windows Server 2022 running the link-shortener
# ---------------------------------------------------------------------------
# This is the machine we migrate. The PDF migrates a BARE Windows box; we put
# the link-shortener app + a seeded SQLite database on it via user_data so the
# cutover proves something real: the SAME app and the SAME data land in Azure.
# The migration mechanism (block-level disk replication) doesn't care what's on
# the disk, whatever's there comes across byte-for-byte.
# Look the AMI up at plan time instead of pinning an ID. A hardcoded AMI goes
# stale, AWS deregisters old Windows images every few months, and a
# deregistered ID makes Azure Migrate's discovery hang at "collecting instance
# settings" (the exact failure from the first take). most_recent=true always
# resolves to the current AWS-owned Windows Server 2022 Base image for the
# region, so the lab never rots. Set var.windows_ami to override if you ever
# need a specific pinned image.
data "aws_ami" "windows_2022" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Full-Base-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "source_vm" {
  ami                    = var.windows_ami != "" ? var.windows_ami : data.aws_ami.windows_2022.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.source_vm.id]
  iam_instance_profile   = aws_iam_instance_profile.migrate_profile.name

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
    encrypted   = false
  }

  # user_data is a PowerShell script that runs ONCE on first boot. It sets the
  # Administrator password and installs + starts the app. templatefile() reads
  # bootstrap.ps1.tftpl and fills in ${admin_password} at plan time.
  user_data = templatefile("${path.module}/bootstrap.ps1.tftpl", {
    admin_password = var.admin_password
  })

  # Azure Migrate reads volume tags during discovery to map disks to instances.
  volume_tags = {
    Name    = "vol-migrate-source-${var.yourname}"
    project = "azure-migrate-lab"
  }

  tags = {
    Name    = "ec2-migrate-source-${var.yourname}"
    project = "azure-migrate-lab"
  }
}
