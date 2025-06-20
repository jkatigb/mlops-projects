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
cd feature_repo
python ingest.py
python retrieve_online.py
```

Pre-commit hooks can be installed with:
```bash
make precommit-install
```
