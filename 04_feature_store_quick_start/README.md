# Feature Store Quick-Start

## Overview
One-click deployment of Feast backed by S3 (offline) and DynamoDB (online). This project includes Docker Compose for a local demo, Terraform for provisioning AWS resources, and a notebook that walks through ingesting and retrieving features.

## Why it matters
Feature reuse and governance are core to MLOps maturity. This quick-start lets teams evaluate Feast without weeks of infrastructure work.

## Tech Stack
* Feast 0.x
* AWS S3 (offline store) & DynamoDB (online store)
* Docker Compose for local demo / Terraform for AWS option
* Jupyter Notebook (example usage)

## Usage
```bash
# Local demo
make compose-up
jupyter lab  # open notebooks/demo.ipynb

# Provision AWS resources
make terraform-up
```

Run the ingest script to populate the online store and then fetch features:
```bash
python feature_repo/ingest.py
python feature_repo/retrieve_online.py
```

Note: The scripts can be run from any directory as they automatically resolve paths relative to their location.

Pre-commit hooks can be installed with:
```bash
make precommit-install
```

## Prerequisites
- Docker and Docker Compose for local demo
- AWS credentials configured for Terraform deployment
- Python 3.8+ for running the ingestion scripts

## Security Notes
- Database credentials can be customized via environment variables (see `.env.example`)
- S3 bucket force_destroy is disabled by default for safety
- DynamoDB table has point-in-time recovery enabled
