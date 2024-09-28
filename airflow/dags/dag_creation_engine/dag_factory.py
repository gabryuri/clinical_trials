import os
import yaml
import traceback
import logging
from datetime import datetime

from airflow import DAG

from dag_creation_engine.task_factory import create_tasks


logging.basicConfig(format="[%(levelname)s] %(asctime)s : %(message)s", level=logging.INFO, force=True)


def create_dag(logging, dag_id, schedule_interval, start_date, task_configs):
    logging.info(f"creating DAG: {dag_id}")
    try:
        with DAG(dag_id, start_date=start_date, schedule=schedule_interval, catchup=False) as dag:
            logging.info(f"task configs: {task_configs}")
            tasks = create_tasks(dag=dag, dag_yaml=task_configs)
            return dag
    except Exception as e:
        logging.info("DAG Creation failed with message:")
        traceback.print_exc()
        return None


def import_dag_yamls(YAML_FOLDER):
    for yaml_file in os.listdir(YAML_FOLDER):
        print("YAML FILES: ", yaml_file)
        if yaml_file.endswith(".yaml"):
            with open(os.path.join(YAML_FOLDER, yaml_file), "r") as f:
                dag_yaml = yaml.safe_load(f)
                dag_id = yaml_file.split(".")[0]
                start_date = datetime.strptime(dag_yaml["start_date"], "%Y-%m-%d")
                schedule_interval = dag_yaml["schedule_interval"]
                task_configs = dag_yaml["groups"]
                globals()[dag_id] = create_dag(
                    logging=logging,
                    dag_id=dag_id,
                    schedule_interval=schedule_interval,
                    start_date=start_date,
                    task_configs=task_configs,
                )


import_dag_yamls("dags/")
