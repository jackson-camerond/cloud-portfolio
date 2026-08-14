# The ALB and app security groups reference each other (ALB's egress points
# at the app SG; the app's ingress points at the ALB SG). Two groups that
# point at each other can't both carry inline rule blocks -- Terraform can't
# tell which one to create first, and errors with "Cycle: aws_security_group
# .app, aws_security_group.alb". Standalone aws_vpc_security_group_*_rule
# resources break that cycle: both empty groups get created first, then the
# cross-referencing rules attach afterward.

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb"
  description = "Internet to ALB. Port 80 only -- this lab has no domain/cert, so HTTPS is the noted production upgrade."
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_security_group" "app" {
  name        = "${var.project_name}-app"
  description = "ALB to Fargate task, container port only. Nothing else on the internet can reach the task directly."
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "alb_http_in" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from anywhere"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "alb_to_app" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to the app tier, container port only"
  from_port                    = var.container_port
  to_port                      = var.container_port
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.app.id
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  description                  = "App port from the ALB only"
  from_port                    = var.container_port
  to_port                      = var.container_port
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.alb.id
}

# 443 only: the task has a public IP (no NAT Gateway in this lab -- see
# network.tf) and uses it to reach the ECR API and CloudWatch Logs, both
# HTTPS-only endpoints. Nothing this app does needs any other port out.
resource "aws_vpc_security_group_egress_rule" "app_https_out" {
  security_group_id = aws_security_group.app.id
  description       = "HTTPS out to ECR / CloudWatch Logs"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}
