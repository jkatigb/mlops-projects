# OpenLineage-Powered Data & Model Lineage Graph

## Overview
Implements Marquez + Airflow OpenLineage integration to capture and visualise lineage across data preparation, model training, validation, and serving stages. The result is an interactive graph showing how each dataset version influenced specific model versions and endpoints.

## Why it matters
Auditors and SREs need to answer "who changed what, when?" quickly. This project provides provenance for both data and ML artifacts in a single UI.

## Tech Stack
* Marquez (OpenLineage backend & UI)
* Apache Airflow with `openlineage-airflow` plugin
* Example DAG (CSV → Parquet → train → push model → deploy)
* Docker-compose & Kubernetes manifests

## Task Checklist
- [ ] Docker-compose: Postgres, Marquez, Airflow web/scheduler  
- [ ] Configure `OPENLINEAGE_URL` & namespace  
- [ ] Sample DAG emitting lineage events for each task  
- [ ] Extend DAG to include Seldon/KFServing model deploy step  
- [ ] Populate UI with at least two pipeline runs  
- [ ] Documentation: how to query lineage via Marquez API  
- [ ] Makefile for `compose-up`, `dag-trigger`, `clean`  
- [ ] Architecture diagram  

## Demo
```bash
make compose-up
make dag-trigger  # triggers sample pipeline twice
open http://localhost:3000  # Marquez UI
```

Click on the model node to highlight upstream datasets and transformations.

---
*Status*: alpha 