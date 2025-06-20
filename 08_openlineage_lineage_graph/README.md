# OpenLineage-Powered Data & Model Lineage Graph

## Overview
Implements Marquez with Airflow and the OpenLineage plugin to capture lineage across data prep, training and serving stages. The UI lets you trace which dataset versions produced a given model version and when it was deployed.

## Why it matters
Auditors and SREs can quickly answer *who changed what, when?* by inspecting lineage for both data and ML artifacts in a single place.

## Tech Stack
* Marquez (OpenLineage backend and UI)
* Apache Airflow with `openlineage-airflow` plugin
* Example DAG: CSV → transform → train → deploy via Seldon/KFServing
* Docker Compose

## Task Checklist
- [x] Docker-compose: Postgres, Marquez, Airflow web/scheduler
- [x] Configure `OPENLINEAGE_URL` & namespace
- [x] Sample DAG emitting lineage events for each task
- [x] Extend DAG to include Seldon/KFServing model deploy step
- [ ] Populate UI with at least two pipeline runs
- [x] Documentation: how to query lineage via Marquez API
- [x] Makefile for `compose-up`, `dag-trigger`, `clean`
- [x] Architecture diagram

## Demo
```bash
make compose-up
make dag-trigger  # triggers sample pipeline twice
open http://localhost:3000  # Marquez UI
```

Click on the model node to highlight upstream datasets and transformations.

### Query lineage via Marquez API
```bash
# list runs for the ml_lineage job
curl -s http://localhost:5000/api/v1/namespaces/demo/jobs/ml_lineage/runs | jq
```
The API returns run IDs which can be expanded for detailed inputs and outputs.

### Architecture
See `architecture.mmd` for a simple Mermaid diagram of Airflow emitting events to Marquez.

---
*Status*: alpha
