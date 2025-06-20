compose-up:
docker-compose up -d

compose-down:
docker-compose down

terraform-init:
cd terraform && terraform init

terraform-up: terraform-init
cd terraform && terraform apply -auto-approve

terraform-destroy:
cd terraform && terraform destroy -auto-approve

precommit-install:
pre-commit install
