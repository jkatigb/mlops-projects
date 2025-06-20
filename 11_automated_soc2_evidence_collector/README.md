# Automated SOC-2 Evidence Collector for ML Pipelines

## Overview
GitHub Action that captures cryptographic proofs of each ML pipeline run (MLflow metadata, pipeline DAG hash, Terraform plan, container digest) and stores signed JSON artefacts in an S3 "audit-evidence" bucket.

## Why it matters
Compliance teams waste days screenshotting logs. Automating evidence collection turns weeks of audit prep into minutes and eliminates human error.

## Tech Stack
* GitHub Actions
* MLflow REST API
* AWS S3 (versioned bucket)
* Python script to generate & sign evidence JSON (AWS KMS)

## Task Checklist
- [ ] Define Action workflow triggered on successful `train-and-deploy` pipeline  
- [ ] Step: pull MLflow run details via API (run-id from artifact)  
- [ ] Compute SHA256 of Git commit & DAG YAML  
- [ ] Terraform `plan -out=plan.tfplan` → binary hashed  
- [ ] Package evidence into JSON schema `{timestamp, commit, run_id, terraform_hash, image_digest}`  
- [ ] Sign JSON with KMS key & upload to S3  
- [ ] Optional: SNS notification to compliance channel  
- [ ] README instructions for auditors to verify signature  

## Usage
Evidence automatically lands under `s3://audit-evidence/<date>/<run-id>.json.sig`. Auditors can verify with:
```bash
aws kms verify --key-id <key> --message fileb://evidence.json --signature fileb://evidence.sig --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256
```

---
*Status*: proposal 