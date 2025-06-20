#!/usr/bin/env bash
set -euo pipefail
AWS_CLUSTER=prod-us
GCP_CLUSTER=prod-eu

echo "Draining nodes on $AWS_CLUSTER..."
kubectl --context "$AWS_CLUSTER" drain --all --ignore-daemonsets --delete-emptydir-data

echo "Checking service availability on $GCP_CLUSTER..."
kubectl --context "$GCP_CLUSTER" rollout status deployment/inference -n inference

echo "Failover complete. Traffic should now route to $GCP_CLUSTER."

