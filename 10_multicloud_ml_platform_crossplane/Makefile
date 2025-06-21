.PHONY: help crossplane-up crossplane-down deploy-clusters check-clusters failover clean

KUBECTL := kubectl
CROSSPLANE_VERSION := v1.15.0
TIMEOUT := 600s

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-requirements: ## Check if required tools are installed
	@which kubectl >/dev/null || (echo "kubectl not found. Please install kubectl" && exit 1)
	@which helm >/dev/null || (echo "helm not found. Please install helm" && exit 1)
	@echo "✓ All requirements met"

crossplane-up: check-requirements ## Install Crossplane and providers
	@echo "Installing Crossplane..."
	$(KUBECTL) apply -f bootstrap/crossplane-install.yaml
	@echo "Waiting for Crossplane to be ready..."
	$(KUBECTL) wait --for=condition=complete job/install-crossplane -n crossplane-system --timeout=$(TIMEOUT)
	@echo "Installing providers..."
	$(KUBECTL) apply -f bootstrap/provider-aws.yaml
	$(KUBECTL) apply -f bootstrap/provider-gcp.yaml
	@echo "Waiting for providers to be healthy..."
	$(KUBECTL) wait --for=condition=healthy provider/crossplane-provider-aws --timeout=$(TIMEOUT)
	$(KUBECTL) wait --for=condition=healthy provider/crossplane-provider-gcp --timeout=$(TIMEOUT)
	@echo "✓ Crossplane is ready!"

deploy-clusters: ## Deploy production clusters
	@echo "Creating cluster XRD..."
	$(KUBECTL) apply -f clusters/xcluster-definition.yaml
	@echo "Creating cluster claims..."
	$(KUBECTL) apply -f clusters/prod-us.yaml
	$(KUBECTL) apply -f clusters/prod-eu.yaml
	@echo "✓ Cluster deployments initiated"

check-clusters: ## Check cluster status
	@echo "Cluster Status:"
	@$(KUBECTL) get clusters -o wide
	@echo ""
	@echo "Crossplane Resources:"
	@$(KUBECTL) get crossplane -A

deploy-apps: ## Deploy applications via ArgoCD
	@echo "Deploying ApplicationSet..."
	$(KUBECTL) apply -f argocd/appset-inference.yaml
	@echo "✓ Application deployment initiated"

failover: ## Execute failover from AWS to GCP
	@echo "Starting failover procedure..."
	@./failover.sh

test-endpoints: ## Test inference endpoints
	@echo "Testing endpoints..."
	@for cluster in prod-us prod-eu; do \
		echo "Testing $$cluster..."; \
		endpoint=$$($(KUBECTL) --context $$cluster get svc inference -n inference -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending"); \
		if [ "$$endpoint" != "pending" ]; then \
			curl -s -o /dev/null -w "$$cluster: %{http_code}\n" http://$$endpoint/health || echo "$$cluster: failed"; \
		else \
			echo "$$cluster: endpoint pending"; \
		fi \
	done

crossplane-down: ## Uninstall Crossplane and all resources
	@echo "⚠️  This will delete all Crossplane resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(KUBECTL) delete clusters --all; \
		$(KUBECTL) delete providers --all; \
		helm uninstall crossplane -n crossplane-system || true; \
		$(KUBECTL) delete namespace crossplane-system; \
	fi

clean: ## Clean up temporary files
	@find . -name "*.tmp" -delete
	@find . -name "*.bak" -delete
	@echo "✓ Cleanup complete"