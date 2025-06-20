# Cost Analysis Notes

* AWS EKS control plane costs about $73/month per cluster.
* GKE autopilot charges per vCPU/hour; a minimal cluster is roughly $0.10/hr.
* Inter-region egress is $0.02/GB on AWS and $0.05/GB on GCP.
* Crossplane itself adds no cost beyond the Kubernetes resources it manages.

