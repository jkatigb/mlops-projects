# MLOps Projects

This repository collects a series of small MLOps prototypes and templates. Each folder is a standalone subproject demonstrating specific MLOps patterns, tools, and best practices. 

## Overview

See the table below for a short description and current status. Click on any project name to view its README for full details.

| Project | Purpose | Status |
|---|---|---|
| [01_gitops_first_ml_pipeline_template](01_gitops_first_ml_pipeline_template/README.md) | End-to-end reference implementation that provisions cloud infrastructure and automates the entire ML lifecycle using GitOps principles. | scaffold only – PRs welcome! |
| [02_model_drift_performance_dashboard](02_model_drift_performance_dashboard/README.md) | Proof-of-concept service that detects model drift and latency anomalies in real time. | planning |
| [03_cost_aware_gpu_auto_scaler_poc](03_cost_aware_gpu_auto_scaler_poc/README.md) | Demonstrates dynamic provisioning of spot GPU nodes only when ML workloads need them, terminating when idle. | not started |
| [04_feature_store_quick_start](04_feature_store_quick_start/README.md) | One-click deployment of Feast backed by S3 and DynamoDB with a demo notebook for low-latency feature retrieval. | draft |
| [05_security_hardening_cookbook](05_security_hardening_cookbook/README.md) | Collection of Kubernetes & CI/CD security best-practices packaged as ready-to-apply policies, scans, and pipelines. | concept |
| [06_cookiecutter_ml_project_dvc_precommit](06_cookiecutter_ml_project_dvc_precommit/README.md) | Opinionated template standardising ML projects with DVC, pytest, and pre-commit hooks. | boilerplate |
| [07_self_service_jupyterhub_eks](07_self_service_jupyterhub_eks/README.md) | Deploys JupyterHub on AWS EKS with per-user IAM roles and idle-cull automation. | skeleton |
| [08_openlineage_lineage_graph](08_openlineage_lineage_graph/README.md) | Captures and visualises lineage across data preparation, training, validation, and serving stages using OpenLineage. | alpha |
| [09_canary_ab_model_releases_istio](09_canary_ab_model_releases_istio/README.md) | Shows progressive delivery of ML models with Istio traffic splitting and automated rollback. | planning |
| [10_multicloud_ml_platform_crossplane](10_multicloud_ml_platform_crossplane/README.md) | Provisions AWS and GCP clusters via Crossplane and syncs the same Argo CD app to both for portable GitOps. | idea |
| [11_automated_soc2_evidence_collector](11_automated_soc2_evidence_collector/README.md) | GitHub Action that stores cryptographic proofs of each ML pipeline run in an S3 "audit-evidence" bucket. | proposal |
| [12_realtime_feature_pipeline_kafka_flink_feast](12_realtime_feature_pipeline_kafka_flink_feast/README.md) | Streams sensor data through Kafka and Flink into Feast for sub-10 ms feature retrieval. | design |
| [13_reusable_helm_chart_model_serving](13_reusable_helm_chart_model_serving/README.md) | Opinionated Helm chart wrapping KFServing/Seldon with best-practice defaults. | N/A |
| [14_chaos_engineering_suite_ml_pipelines](14_chaos_engineering_suite_ml_pipelines/README.md) | Injects failures into ML pipelines using LitmusChaos to validate auto-healing and rollback mechanisms. | plan |
| [15_opentelemetry_tracing_ml_inference](15_opentelemetry_tracing_ml_inference/README.md) | Adds end-to-end distributed tracing of an ML inference request using OpenTelemetry. | ready |

## Contributing

Each project follows a similar structure:
- `README.md` - Project overview, architecture, and usage instructions
- Implementation files (Docker, Terraform, Python, etc.)
- Example configurations and test scripts

Feel free to open issues or submit PRs to improve existing projects or suggest new MLOps patterns to demonstrate.

## License

See individual project directories for specific licenses. Most code is provided as examples and templates for educational purposes.
