compose-up:
	docker-compose -f docker-compose.yml up -d

compose-down:
	docker-compose -f docker-compose.yml down -v

clean: compose-down

# Trigger DAG twice to populate lineage graph
dag-trigger:
	docker-compose -f docker-compose.yml exec airflow-webserver airflow dags trigger ml_lineage
	@echo "Waiting 30 seconds before second trigger..."
	@sleep 30
	docker-compose -f docker-compose.yml exec airflow-webserver airflow dags trigger ml_lineage

# Create default Airflow user
init-airflow:
	docker-compose -f docker-compose.yml exec airflow-webserver airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com \
		--password admin

# View logs
logs:
	docker-compose -f docker-compose.yml logs -f

# Check status of all services
status:
	docker-compose -f docker-compose.yml ps
