.PHONY: all clean test compose-up compose-down terraform-init terraform-up terraform-destroy precommit-install

all: compose-up

clean: compose-down terraform-destroy

test:
	@echo "No tests configured yet"

compose-up:
	docker-compose up -d

compose-down:
	docker-compose down

terraform-init:
	@if [ ! -d terraform ]; then echo "Error: terraform directory not found"; exit 1; fi
	cd terraform && terraform init

terraform-up: terraform-init
	@if [ ! -d terraform ]; then echo "Error: terraform directory not found"; exit 1; fi
	cd terraform && terraform apply -auto-approve

terraform-destroy:
	@if [ ! -d terraform ]; then echo "Error: terraform directory not found"; exit 1; fi
	cd terraform && terraform destroy -auto-approve

precommit-install:
	pre-commit install
