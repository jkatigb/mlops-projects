# Feature Store Quick-Start

## Overview
One-click deployment of Feast backed by S3 (offline) & DynamoDB (online) with a demo notebook that registers, materialises, and retrieves features at low latency.

## Why it matters
Feature reuse and governance are core to MLOps maturity. This quick-start lets teams evaluate Feast without weeks of infra work.

## Tech Stack
* Feast 0.x
* AWS S3 (offline store) & DynamoDB (online store)
* Docker-compose for local demo / Terraform for AWS option
* Jupyter Notebook (example usage)

## Task Checklist
- [ ] Docker-compose: `feast-core`, `redis`, `postgres` for local quick spin-up  
- [ ] Terraform module to create S3 bucket + DynamoDB table  
- [ ] Feast `feature_repo/` with example `driver_stats` dataset  
- [ ] Notebook: ingest batch data → materialise → online retrieval  
- [ ] `make apply` script wiring AWS creds & Feast config  
- [ ] Pre-commit hooks: `black`, `flake8`, `isort`, `nbstripout`  
- [ ] README demo GIF  

## Usage
```bash
# Local
make compose-up
jupyter lab  # open notebook

# AWS
make terraform-up
python scripts/ingest.py
python scripts/retrieve.py  # latency <10ms
```

---
*Status*: draft 