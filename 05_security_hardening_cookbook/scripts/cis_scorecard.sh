#!/usr/bin/env bash
# CIS Kubernetes Benchmark scorecard generator
# Generates compliance reports for security audits

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORT_DIR="${REPORT_DIR:-./security-reports}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/cis_scorecard_${TIMESTAMP}.txt"
JSON_REPORT="${REPORT_DIR}/cis_scorecard_${TIMESTAMP}.json"

# Ensure report directory exists
mkdir -p "${REPORT_DIR}"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")
            echo -e "${BLUE}[INFO]${NC} ${message}"
            ;;
        "success")
            echo -e "${GREEN}[SUCCESS]${NC} ${message}"
            ;;
        "warning")
            echo -e "${YELLOW}[WARNING]${NC} ${message}"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} ${message}"
            ;;
    esac
}

# Check prerequisites
print_status "info" "Checking prerequisites..."

if ! command -v kube-bench >/dev/null 2>&1; then
    print_status "error" "kube-bench not installed"
    print_status "info" "Install with: go install github.com/aquasecurity/kube-bench@latest"
    exit 1
fi

if ! kubectl cluster-info >/dev/null 2>&1; then
    print_status "error" "kubectl not configured or cluster not accessible"
    exit 1
fi

# Detect Kubernetes version and node type
K8S_VERSION=$(kubectl version --short 2>/dev/null | grep Server | awk '{print $3}')
NODE_TYPE="worker" # Default to worker, can be overridden

print_status "info" "Kubernetes version: ${K8S_VERSION}"
print_status "info" "Starting CIS benchmark scan..."

# Run kube-bench with appropriate parameters
{
    echo "==================================================================="
    echo "CIS Kubernetes Benchmark Security Scorecard"
    echo "==================================================================="
    echo "Generated: $(date)"
    echo "Cluster: $(kubectl config current-context)"
    echo "Kubernetes Version: ${K8S_VERSION}"
    echo "==================================================================="
    echo ""
    
    # Run kube-bench with JSON output for parsing
    kube-bench --json > "${JSON_REPORT}" 2>/dev/null || true
    
    # Run kube-bench with summary for human-readable output
    kube-bench --outputfile /dev/stdout 2>/dev/null || {
        print_status "warning" "Running kube-bench with default configuration"
        kube-bench run --targets node --outputfile /dev/stdout 2>/dev/null
    }
    
} | tee "${REPORT_FILE}"

# Extract and display summary
echo "" | tee -a "${REPORT_FILE}"
echo "==================================================================="  | tee -a "${REPORT_FILE}"
echo "EXECUTIVE SUMMARY" | tee -a "${REPORT_FILE}"
echo "==================================================================="  | tee -a "${REPORT_FILE}"

# Parse JSON report for summary if available
if [ -f "${JSON_REPORT}" ] && command -v jq >/dev/null 2>&1; then
    TOTAL_PASS=$(jq -r '.Totals.total_pass // 0' "${JSON_REPORT}")
    TOTAL_FAIL=$(jq -r '.Totals.total_fail // 0' "${JSON_REPORT}")
    TOTAL_WARN=$(jq -r '.Totals.total_warn // 0' "${JSON_REPORT}")
    TOTAL_INFO=$(jq -r '.Totals.total_info // 0' "${JSON_REPORT}")
    
    TOTAL_CHECKS=$((TOTAL_PASS + TOTAL_FAIL + TOTAL_WARN + TOTAL_INFO))
    if [ $TOTAL_CHECKS -gt 0 ]; then
        COMPLIANCE_SCORE=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_PASS / $TOTAL_CHECKS) * 100}")
    else
        COMPLIANCE_SCORE="0.0"
    fi
    
    {
        echo ""
        echo "Total Checks: ${TOTAL_CHECKS}"
        echo -e "${GREEN}Passed: ${TOTAL_PASS}${NC}"
        echo -e "${RED}Failed: ${TOTAL_FAIL}${NC}"
        echo -e "${YELLOW}Warnings: ${TOTAL_WARN}${NC}"
        echo -e "${BLUE}Info: ${TOTAL_INFO}${NC}"
        echo ""
        echo "Compliance Score: ${COMPLIANCE_SCORE}%"
        
        # Determine compliance status
        if (( $(echo "$COMPLIANCE_SCORE >= 90" | bc -l) )); then
            echo -e "${GREEN}Status: COMPLIANT${NC}"
        elif (( $(echo "$COMPLIANCE_SCORE >= 70" | bc -l) )); then
            echo -e "${YELLOW}Status: PARTIALLY COMPLIANT${NC}"
        else
            echo -e "${RED}Status: NON-COMPLIANT${NC}"
        fi
    } | tee -a "${REPORT_FILE}"
    
    # Critical failures section
    echo "" | tee -a "${REPORT_FILE}"
    echo "==================================================================="  | tee -a "${REPORT_FILE}"
    echo "CRITICAL FAILURES REQUIRING IMMEDIATE ATTENTION" | tee -a "${REPORT_FILE}"
    echo "==================================================================="  | tee -a "${REPORT_FILE}"
    
    jq -r '.Controls[].checks[]? | select(.state == "FAIL" and .scored == true) | "- [\(.id)] \(.text)"' "${JSON_REPORT}" 2>/dev/null | head -10 | tee -a "${REPORT_FILE}"
    
else
    # Fallback to grep-based parsing
    print_status "warning" "jq not found, using basic parsing"
    grep -E "== Summary|PASS:|FAIL:|WARN:|INFO:" "${REPORT_FILE}" | tail -10
fi

# Generate recommendations
{
    echo ""
    echo "==================================================================="
    echo "RECOMMENDATIONS"
    echo "==================================================================="
    echo "1. Address all FAILED checks immediately"
    echo "2. Review WARNING items and create remediation plan"
    echo "3. Document any compensating controls for failed checks"
    echo "4. Schedule regular CIS benchmark scans (weekly recommended)"
    echo "5. Integrate CIS checks into CI/CD pipeline"
} | tee -a "${REPORT_FILE}"

# File locations
echo "" | tee -a "${REPORT_FILE}"
echo "==================================================================="  | tee -a "${REPORT_FILE}"
echo "REPORT FILES" | tee -a "${REPORT_FILE}"
echo "==================================================================="  | tee -a "${REPORT_FILE}"
echo "Full Report: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "JSON Report: ${JSON_REPORT}" | tee -a "${REPORT_FILE}"

print_status "success" "CIS scorecard generated successfully"
print_status "info" "Reports saved to ${REPORT_DIR}/"

# Exit with appropriate code
if [ "${TOTAL_FAIL:-0}" -gt 0 ]; then
    exit 1
fi
