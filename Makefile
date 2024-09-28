.PHONY: help
help:
	@echo "Available commands:"
	@echo "  validate-dags   - Validate .YAML files that describe Airflow DAGs by running the validator script"
	@echo "  setup-dev       - Set up the development environment by installing required Python packages"
	@echo "  lint            - Run the Black linter with a line length of 120"
	@echo "  test            - Run unit tests with pytest"
	@echo "  deploy          - Deploy the application (aliases: up)"

.PHONY: validate-dags
validate-dags:
	python3 airflow/scripts/validator/validate_dags.py

.PHONY: setup-dev
setup-dev:
	pip install -r environment/dev-requirements.txt
	pip install -r environment/requirements.txt

.PHONY: lint
lint:
	black . --line-length 120


.PHONY: test
test:
		echo "Running tests"; \
		cd airflow && PYTHONPATH=$$PYTHONPATH:$$PWD/dags AIRFLOW_HOME="." python3 -m pytest -vv

.PHONY: deploy up
deploy: up  
up:
	docker compose down && docker compose build && docker compose up -d
	docker exec -u root -ti clinical_trials-airflow-scheduler-1 chmod -R 777 /opt/airflow/
	

