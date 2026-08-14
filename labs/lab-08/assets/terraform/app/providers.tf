provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project = var.project_name
      env     = "lab"
      owner   = "cam"
      lab     = "lab-08"
    }
  }
}
