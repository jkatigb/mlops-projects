# Cookiecutter ML Project (DVC + Pre-Commit)

## Overview
Opinionated template that standardises ML projects with:
* DVC for data & model versioning
* pytest for testing
* pre-commit hooks (`black`, `isort`, `flake8`, `dvc status`)
* GitHub Actions CI (unit tests, DVC pull, smoke training)

Created via `cookiecutter gh:yourname/cookiecutter-mlops` to boost onboarding speed and enforce best practices from day one.

## Why it matters
Inconsistent repo structures slow collaboration. This template bakes in sensible defaults so every new experiment starts with reproducibility and automation.

## Directory Layout
```
├── data/             # .gitignored raw data
├── dvc.lock / .yaml  # tracked datasets & models
├── src/
│   ├── __init__.py
│   └── train.py
├── tests/
└── .github/workflows/
```

## Task Checklist
- [ ] Create `cookiecutter.json` prompts (project_name, author, license, AWS profile, etc.)  
- [ ] DVC remote config (S3 or GCS)  
- [ ] Template `pyproject.toml` with dependencies  
- [ ] Pre-commit config with required hooks  
- [ ] GitHub Actions workflow: install deps → `dvc pull` → `pytest -q`  
- [ ] Example notebook & script using tracked dataset  
- [ ] Documentation site (mkdocs) optional  

## Usage
```bash
pip install cookiecutter
cookiecutter gh:yourname/cookiecutter-mlops
cd my-new-project
dvc pull
pytest
```

---
*Status*: boilerplate 