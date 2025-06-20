#!/bin/bash
# Install LitmusChaos using Helm into the 'chaos' namespace
set -euo pipefail

helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
helm repo update
helm install litmus litmuschaos/litmus --namespace chaos --create-namespace
