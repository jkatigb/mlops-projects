.PHONY: deploy destroy

deploy:
cd terraform && terraform init && terraform apply -auto-approve
helm upgrade --install argocd argo/argo-cd -f helm/argo-cd/values.yaml --namespace argocd --create-namespace
helm upgrade --install mlflow ./helm/mlflow --namespace mlflow --create-namespace
helm upgrade --install monitoring ./helm/prometheus-grafana --namespace monitoring --create-namespace
helm upgrade --install karpenter ./helm/karpenter --namespace karpenter --create-namespace

destroy:
cd terraform && terraform destroy -auto-approve
