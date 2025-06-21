provider "aws" {
  region = var.region
}

variable "region" {
  default = "us-west-2"
}
