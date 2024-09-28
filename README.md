# Airflow - clinical trial data ingestion 

This project uses Airflow that orchestrates pipeline to ingest, normalize and process data from the [ClinicalTrials.gov](https://clinicaltrials.gov/) API. 

Data ingestion is done through dlt into duckdb, whereas DBT takes care of the SQL transformations, and a standalone python function standardizes disease names with the aid of OpenAI API.

The graph representation of the DAG is then: 

![alt text](docs/dag.png)

## Key features:
### Dynamic DAGs
This deployment implements an abstraction on top of Airflow, enabling complex DAGs to be created with simple yaml statements:

```YAML
schedule_interval: '0 0 * * *'
start_date: '2024-07-01'

groups:
  respiratory-conditions:
    - task_id: 'clinical-trials-gov-influenza'
      kind: 'dlt-ingestion-pipeline'
      api_parameters: "{'query.cond': 'INFLUENZA'}"
    
    - task_id: 'clinical-trials-gov-covid'
      kind: 'dlt-ingestion-pipeline'
      api_parameters: "{'query.cond': 'COVID'}"

  endocrinal-conditions:
    - task_id: 'clinical-trials-gov-diabetes'
      kind: 'dlt-ingestion-pipeline'
      api_parameters: "{'query.cond': 'DIABETES'}"

    - task_id: 'clinical-trials-gov-menopause'
      kind: 'dlt-ingestion-pipeline'
      api_parameters: "{'query.cond': 'MENOPAUSE'}"
  
  transformation:
    - task_id: 'clinical-trials-gov-dbt'
      kind: 'dbt-transformation'
      models: 'all'
      dependencies:
        - clinical-trials-gov-influenza
        - clinical-trials-gov-covid
        - clinical-trials-gov-diabetes
        - clinical-trials-gov-menopause
  
    - task_id: 'clinical-trials-gov-openai-standardize-conditions'
      kind: 'llm-processing'
      source_table: 'dim_conditions'
      source_schema: 'clinical_trials_preprocessed'
      target_table: 'dim_conditions_processed'
      target_schema: 'clinical_trials_processed'
      dependencies:
        - 'clinical-trials-gov-dbt'
```
This yaml creates the DAG in the first image.


## Code
All python code is stored under [airflow/dags/dag_creation_engine](https://github.com/gabryuri/clinical_trials/tree/main/airflow/dags/dag_creation_engine) and the scripts `dag_factory.py` and `task_factory.py` are responsible for translating YAML configuration files into DAGs.

The code may be tested through `make test`. 


## Data Modelling and results
The tables created by dbt can be seen under the schema clinical_trials_preprocessed and clinical_trials_processed. The table that received the LLM standardization can be seen below: 

![alt text](docs/dbeaver_print.png)

## Next steps:
It is important to note that this is not a production environment but a simple example of how one could be built. Many aspects would need to change, including:

- Better testing in both dbt and airflow dag_factory and task_factory, as well as the validate
- running dbt models separately instead of a `dbt run` command
  - This could be done using the dbt manifest.json that has the solved dependencies between models, making each one a task
- Decoupling Airflow Scheduling with the actual execution environment
  - Kubernetes or ECS operators would be a good choice instead of PythonOperator
- Using another database (here, DuckDB is used only for practice purposes)
- Improving the flexibility of the .yaml templates by adding more parameters
- The LLM API code is ad-hoc and should be refactored into something generic that can be used for other purposes.


## Other
### Makefile
This project implements some helpful commands in its makefile. Testing, linting, deploying and validating dag yamls are some of the commands.

### Environment variables
In order to run this application properly, a `docker.env` file must be created on the root of this folder with the content: 


**please note the OpenAI api key**
```
DUCKDB_PATH=db/duckdb.db
_AIRFLOW_WWW_USER_PASSWORD=admin
_AIRFLOW_WWW_USER_USERNAME=admin
AIRFLOW__WEBSERVER__SECRET_KEY=test123
PROGRESS=log
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
DBT_PROFILES_DIR=/opt/airflow/dbt
OPENAI_API_KEY=<your_key>
```

