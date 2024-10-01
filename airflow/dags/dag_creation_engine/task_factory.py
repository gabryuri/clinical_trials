import os
import json
import logging

from airflow.utils.task_group import TaskGroup
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator

from dag_creation_engine.dlt.ingestor import load_clinical_trials
from dag_creation_engine.openai.llm_process import process_disease_info

logger = logging.getLogger(__name__)

HOME = os.environ["AIRFLOW_HOME"]
dbt_path = os.path.join(HOME, "dbt")


def create_tasks(dag, dag_yaml):
    logger.info(f"DAG YAML: {dag_yaml}")
    tasks = {}
    for task_group in dag_yaml:
        with TaskGroup(group_id=f"{task_group}", dag=dag) as task:
            for task_cfg in dag_yaml.get(task_group):
                task_id = task_cfg["task_id"]
                kind = task_cfg["kind"]

                if kind == "dlt-ingestion-pipeline":

                    task = PythonOperator(
                        task_id=task_id,
                        python_callable=load_clinical_trials,
                        op_kwargs={"params": task_cfg.get("api_parameters"), "pipeline": task_group},
                        dag=dag,
                    )

                elif kind == "dbt-transformation":

                    task = BashOperator(
                        task_id=task_id,
                        bash_command=f"cd {dbt_path}" + f" && dbt run",
                    )

                elif kind == "llm-processing":
                    task = PythonOperator(
                        task_id=task_id,
                        python_callable=process_disease_info,
                        op_kwargs={
                            "source_table": task_cfg.get("source_table"),
                            "source_schema": task_cfg.get("source_schema"),
                            "target_table": task_cfg.get("target_table"),
                            "target_schema": task_cfg.get("target_schema"),
                        },
                        dag=dag,
                    )
                else:
                    raise ValueError(f"Unsupported operator: {kind}")
                tasks[task_id] = task

    for task_group in dag_yaml:
        for task_cfg in dag_yaml.get(task_group):
            task_id = task_cfg["task_id"]
            logger.info(f"upstreams to cfg {task_cfg}")
            upstreams = task_cfg.get("dependencies", [])
            for upstream in upstreams:
                tasks[task_id].set_upstream(tasks[upstream])
