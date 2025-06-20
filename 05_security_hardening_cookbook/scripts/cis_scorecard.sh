#!/usr/bin/env bash
# Simple wrapper around kube-bench to output summary scores

set -euo pipefail

if ! command -v kube-bench >/dev/null 2>&1; then
  echo "kube-bench not installed" >&2
  exit 1
fi

kube-bench --summary | tee /tmp/cis_report.txt

echo "\nSummary Score:"
grep -E "Total\s+pass" -A1 /tmp/cis_report.txt
