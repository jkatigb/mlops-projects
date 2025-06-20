variable "name" {}
variable "cidr_block" {}
variable "public_subnets" { type = list(string) }
variable "azs" { type = list(string) }
