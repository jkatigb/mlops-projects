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
- [x] Define Action workflow triggered on successful `train-and-deploy` pipeline
- [x] Step: pull MLflow run details via API (run-id from artifact)
- [x] Compute SHA256 of Git commit & DAG YAML
- [x] Terraform `plan -out=plan.tfplan` → binary hashed
- [x] Package evidence into JSON schema `{timestamp, commit, run_id, terraform_hash, image_digest}`
- [x] Sign JSON with KMS key & upload to S3
- [x] Optional: SNS notification to compliance channel
- [x] README instructions for auditors to verify signature

## Usage
Evidence lands under `s3://audit-evidence/<date>/<run-id>.json` with a matching `.sig` file. Auditors can verify signatures using the AWS CLI:
```bash
aws s3 cp s3://audit-evidence/<date>/<run-id>.json evidence.json
aws s3 cp s3://audit-evidence/<date>/<run-id>.sig evidence.sig
aws kms verify \
  --key-id <key-id> \
  --message fileb://evidence.json \
  --signature fileb://evidence.sig \
  --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256
```
The command returns a `SignatureValid: True` field when the evidence JSON matches the signature.

---
*Status*: implemented
