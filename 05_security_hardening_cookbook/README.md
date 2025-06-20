# Security Hardening Cookbook

## Overview
Collection of Kubernetes & CI/CD security best-practices packaged as ready-to-apply policies, scans, and pipelines. Focus areas: image hygiene, network segmentation, secrets handling, runtime security, and compliance evidence.

## Why it matters
MLOps teams face audits (HIPAA, SOC-2, ISO 27001) and production incidents caused by lax defaults (e.g., :latest images, public LoadBalancers, privileged containers). This cookbook turns security best practices into automatable guard-rails.

## Tech Stack
* OPA Gatekeeper (constraint templates with production-ready policies)
* Trivy vulnerability, secret, license & misconfiguration scanning
* Kubernetes NetworkPolicies (zero-trust networking)
* GitHub Actions security workflow with SARIF integration
* CIS Kubernetes Benchmark compliance reporting
* Pod Security Standards enforcement

## Security Policies Included

### Image Security
- **Deny Latest Tag**: Prevents use of `:latest` tag for better version control
  - Covers all workload types (Deployments, Jobs, CronJobs, Pods)
  - Checks both containers and init containers
  - Supports exemption list for system images

### Resource Management
- **Require Resource Limits**: Ensures containers have CPU/memory limits and requests
  - Prevents resource exhaustion and ensures QoS
  - Optional ephemeral-storage limits
  - Configurable exemptions for sidecars

### Network Security
- **Block Public LoadBalancers**: Requires explicit internal annotations
  - Multi-cloud support (AWS, GCP, Azure)
  - Configurable allowed namespaces
  - Prevents accidental public exposure

### Runtime Security
- **Pod Security Standards**: Enforces Kubernetes security best practices
  - Three levels: privileged, baseline, restricted
  - Prevents privilege escalation, host access
  - Controls capabilities and volume types

### Network Policies
- **Default Deny All**: Zero-trust network baseline
- **Allow Same Namespace**: Namespace isolation with DNS egress

## Quick Start
```bash
# Install Gatekeeper
kubectl apply -f manifests/gatekeeper.yaml

# Wait for Gatekeeper to be ready
kubectl wait --for=condition=Ready pod -l control-plane=controller-manager -n gatekeeper-system

# Apply security policies
kubectl apply -f policies/templates/
kubectl apply -f policies/constraints/

# Apply network policies
kubectl apply -f networkpolicies/

# Run CIS benchmark scan
bash scripts/cis_scorecard.sh
```

## Argo CD Integration
Add the policies repo as an application and set a lower `sync-wave` so Gatekeeper deploys before workloads:
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-10"  # Deploy before workloads
```
This ensures constraints are active before your deployments run.

## Policy Enforcement Modes

Each policy supports three enforcement modes:
- **deny**: Block non-compliant resources (production)
- **dryrun**: Log violations without blocking (testing)
- **warn**: Warn but allow creation (migration period)

Example migration strategy:
```yaml
# Start with dryrun
spec:
  enforcementAction: dryrun

# Monitor logs for violations
kubectl logs -n gatekeeper-system deployment/gatekeeper-audit

# Switch to warn after fixing issues
spec:
  enforcementAction: warn

# Finally enforce
spec:
  enforcementAction: deny
```

## Security Scanning Pipeline

The included GitHub Actions workflow provides comprehensive security scanning:

1. **Vulnerability Scanning**: Detects CVEs in dependencies
2. **Secret Scanning**: Prevents credential leaks
3. **License Scanning**: Ensures license compliance
4. **Misconfiguration Detection**: Catches security issues in K8s manifests
5. **SARIF Integration**: Results appear in GitHub Security tab

### Customizing Scan Severity

Adjust severity thresholds in `.github/workflows/trivy.yml`:
```yaml
severity: 'CRITICAL,HIGH'  # Add MEDIUM for stricter checks
```

## Monitoring & Alerting

### Slack Integration
Configure Slack alerts for policy violations:
```bash
# Add webhook secret
gh secret set SLACK_WEBHOOK --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Prometheus Metrics
Gatekeeper exposes metrics for monitoring:
```yaml
# Example alert rule
- alert: GatekeeperPolicyViolation
  expr: rate(gatekeeper_violation_total[5m]) > 0
  annotations:
    summary: "Gatekeeper policy violations detected"
```

## CIS Benchmark Compliance

Generate compliance reports for audits:
```bash
# Full report with JSON output
REPORT_DIR=./audit-reports bash scripts/cis_scorecard.sh

# Quick compliance check
bash scripts/cis_scorecard.sh | grep "Compliance Score"
```

The enhanced script provides:
- Compliance percentage score
- Critical failure highlighting
- JSON output for automation
- Timestamped reports for audit trails

## Production Deployment Checklist

- [ ] Start with `dryrun` mode for all policies
- [ ] Monitor violations for 1-2 weeks
- [ ] Create exemptions for legitimate use cases
- [ ] Gradually increase enforcement (`warn` → `deny`)
- [ ] Enable Prometheus metrics collection
- [ ] Configure alert notifications
- [ ] Schedule weekly CIS benchmark scans
- [ ] Document policy exemptions and compensating controls
- [ ] Train development teams on security requirements
- [ ] Integrate policy checks into CI/CD pipeline

## Troubleshooting

### Policy Not Triggering
```bash
# Check if Gatekeeper webhook is active
kubectl get validatingwebhookconfigurations | grep gatekeeper

# Verify constraint is loaded
kubectl get constraints
```

### Debugging Violations
```bash
# Check Gatekeeper controller logs
kubectl logs -n gatekeeper-system deployment/gatekeeper-controller-manager

# Test policy locally
opa test policies/templates/
```

### Performance Impact
If experiencing latency:
1. Check Gatekeeper resource limits
2. Consider using `namespaceSelector` to limit scope
3. Optimize Rego rules for efficiency

## Contributing

When adding new policies:
1. Create both template and constraint
2. Include comprehensive violation messages
3. Add parameters for flexibility
4. Document security rationale
5. Include test cases
6. Update this README

---

**Security Notice**: These policies provide defense-in-depth but are not a complete security solution. Regular security audits, penetration testing, and security training remain essential.
