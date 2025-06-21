#!/bin/bash
# Local testing script for SOC-2 evidence collector

set -e

echo "SOC-2 Evidence Collector - Local Test"
echo "====================================="

# Check dependencies
echo "Checking dependencies..."
python3 --version
pip3 show boto3 >/dev/null 2>&1 || { echo "boto3 not installed. Run: pip install -r requirements.txt"; exit 1; }

# Create test data
echo "Creating test data..."
echo "dummy terraform plan content" > plan.tfplan

# Set test environment variables
export RUN_ID="test-run-$(date +%s)"
export KMS_KEY_ID="${KMS_KEY_ID:-test-key-id}"
export S3_BUCKET="${S3_BUCKET:-test-bucket}"
export TERRAFORM_PLAN_PATH="plan.tfplan"
export IMAGE_DIGEST="sha256:abc123def456"

echo "Test configuration:"
echo "  RUN_ID: $RUN_ID"
echo "  KMS_KEY_ID: $KMS_KEY_ID"
echo "  S3_BUCKET: $S3_BUCKET"
echo ""

# Run in dry-run mode (will fail at AWS calls without credentials)
echo "Running evidence collector (dry-run)..."
python3 collect_evidence.py 2>&1 | head -20 || true

echo ""
echo "Test completed. In production, this would:"
echo "1. Sign the evidence with KMS"
echo "2. Upload to S3 bucket"
echo "3. Send SNS notification"

# Cleanup
rm -f plan.tfplan