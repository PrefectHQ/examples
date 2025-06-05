# Prefect Curriculum Overview

This directory contains a leveled learning path for Prefect, progressing from first-steps to advanced production topics.  Each phase has a companion Python module (e.g., `01_foundations.py`) and, where applicable, points to supporting example folders elsewhere in this repository.

| Phase | File | What you will learn | Relevant examples |
|-------|------|--------------------|-------------------|
| **01 – Foundations** | `01_foundations.py` | Install Prefect, define tasks vs. flows, run your first workflow locally. | `01_getting_started/*` |
| **02 – Core Concepts** | `02_core_concepts.py` | Essential SDK features: retries, async & concurrency, task-runners, on-fail/on-success hooks, transactions. | `02_sdk_concepts/*` |
| **03 – Resilience & Patterns** | `03_resilience_and_patterns.py` | Production-safe patterns: conditional logic, dynamic mapping, sub-flows, idempotency techniques. | (future examples) |
| **04 – Orchestration & Scale** | `04_orchestration_and_scale.py` | Parallelism strategies, work-pools & queues, resource limits, high-throughput task-runners. | (future examples) |
| **05 – Cloud Operations** | `05_cloud_operations.py` | Deployments, Prefect CLI vs YAML, Docker images, versioning, remote storage, Prefect Cloud specifics. | `03_cloud_concepts/*` |
| **06 – Observability & Governance** | `06_observability_and_governance.py` | Monitoring & alerting, logging best practices, audit trails, RBAC, team collaboration. | (future examples) |
| **07 – Advanced Integrations** | `07_advanced_integrations.py` | Integrations with Snowflake, dbt, Airbyte, Spark, Kubernetes, and other ecosystem tools. | (future examples) |

Feel free to add or reorder phases as the curriculum evolves. Each module can be run directly or imported into notebooks for exploration. 