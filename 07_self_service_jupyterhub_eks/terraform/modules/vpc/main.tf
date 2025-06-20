variable "cidr" { default = "10.0.0.0/16" }
variable "region" { default = "us-west-2" }

provider "aws" {
  region = var.region
}

resource "aws_vpc" "this" {
  cidr_block = var.cidr
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.cidr, 8, 0)
  map_public_ip_on_launch = true
}

output "vpc_id" { value = aws_vpc.this.id }
output "public_subnet_ids" { value = [aws_subnet.public.id] }
