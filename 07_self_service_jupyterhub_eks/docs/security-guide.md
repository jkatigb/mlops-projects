# Security Guide for JupyterHub on EKS

This guide covers security best practices and configurations for JupyterHub deployment.

## Authentication & Authorization

### GitHub OAuth Setup
1. Create GitHub OAuth App:
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - Application name: `JupyterHub Production`
   - Homepage URL: `https://your-domain.com`
   - Authorization callback URL: `https://your-domain.com/hub/oauth_callback`

2. Configure allowed organizations:
   ```yaml
   hub:
     config:
       GitHubOAuthenticator:
         allowed_organizations:
           - "your-org-name"
         team_whitelist:
           - "your-org-name:data-science"
   ```

### Admin Users
Define admin users in Helm values:
```yaml
hub:
  config:
    JupyterHub:
      admin_users:
        - "github-username-1"
        - "github-username-2"
```

## Network Security

### 1. Network Policies
Network policies restrict pod-to-pod communication:
```yaml
# Applied automatically via Helm chart
networkPolicy:
  enabled: true
```

### 2. Security Groups
- Load balancer: Restricts inbound to HTTPS (443)
- Nodes: Private subnet communication only
- Control plane: Restricted to node communication

### 3. Private Endpoints
VPC endpoints reduce internet exposure:
- S3 endpoint for user storage
- ECR endpoint for container images

## Data Security

### 1. Encryption at Rest
- **S3**: AES-256 encryption enabled
- **EBS**: Encrypted volumes for user storage
- **Secrets**: KMS encryption for Kubernetes secrets

### 2. Encryption in Transit
- **HTTPS**: Enable with cert-manager
- **Internal**: TLS between components

### 3. User Isolation
Each user's data is isolated:
```bash
/home/jovyan/          # User home directory
/home/jovyan/s3/       # S3 mount point
```

## IAM Security

### 1. IRSA (IAM Roles for Service Accounts)
Each component has minimal permissions:
- Hub: Read secrets, manage pods
- User pods: S3 access to user directory only

### 2. S3 Bucket Policies
Users can only access their own directories:
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::bucket/home/${aws:username}/*"
}
```

## Secrets Management

### 1. JupyterHub Secrets
Stored in AWS Secrets Manager:
```bash
aws secretsmanager get-secret-value --secret-id jupyterhub-token
```

### 2. Kubernetes Secrets
Encrypted at rest in etcd:
```bash
kubectl get secret -n jupyterhub jupyterhub-secret -o yaml
```

## Security Monitoring

### 1. Audit Logs
Enable EKS audit logging:
```hcl
cluster_enabled_log_types = ["api", "audit", "authenticator"]
```

### 2. CloudWatch Alarms
Set up alarms for:
- Failed authentication attempts
- Unusual S3 access patterns
- Node security group changes

### 3. AWS GuardDuty
Enable for threat detection:
```bash
aws guardduty create-detector --enable
```

## Compliance

### 1. Pod Security Standards
Enforce security policies:
```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### 2. Image Scanning
Scan container images for vulnerabilities:
```bash
# Using ECR scanning
aws ecr put-image-scanning-configuration \
  --repository-name jupyterhub \
  --image-scanning-configuration scanOnPush=true
```

### 3. CIS Benchmarks
Run CIS Kubernetes Benchmark:
```bash
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-eks.yaml
```

## Incident Response

### 1. Suspicious Activity
If suspicious activity is detected:
1. Identify affected users
2. Revoke user tokens
3. Review audit logs
4. Update security groups if needed

### 2. Data Breach
In case of potential data breach:
1. Isolate affected nodes
2. Snapshot EBS volumes for forensics
3. Rotate all secrets
4. Notify security team

### 3. Emergency Shutdown
To quickly shut down JupyterHub:
```bash
# Scale down all user pods
kubectl scale deployment -n jupyterhub hub --replicas=0

# Deny all network traffic
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: jupyterhub
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
```

## Security Checklist

- [ ] GitHub OAuth configured with organization restrictions
- [ ] Admin users defined
- [ ] HTTPS enabled with valid certificates
- [ ] Network policies enabled
- [ ] S3 bucket encryption enabled
- [ ] IAM roles follow least privilege
- [ ] Audit logging enabled
- [ ] Monitoring alerts configured
- [ ] Image scanning enabled
- [ ] Regular security updates applied