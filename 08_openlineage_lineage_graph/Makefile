compose-up:
	docker-compose -f docker-compose.yml up -d

compose-down:
	docker-compose -f docker-compose.yml down -v

clean: compose-down

# Trigger DAG twice to populate lineage graph
dag-trigger:
	docker-compose -f docker-compose.yml exec airflow-webserver airflow dags trigger ml_lineage || true
	docker-compose -f docker-compose.yml exec airflow-webserver airflow dags trigger ml_lineage || true
